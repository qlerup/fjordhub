import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import app as hub
import test_access_tokens as fixtures
from services.install_state import InstallState
from services.update_manager import UpdateManager


class UpdateAllTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = InstallState(Path(self.temp.name))
        self.manager = UpdateManager(self.state)
        self.apps = [{'id': name} for name in ('fjordhub', 'one', 'two', 'current', 'busy', 'dirty', 'missing')]
        for app in self.apps[:-1]:
            self.state.register(app['id'], self.temp.name)

    def status(self, app):
        name = app['id']
        return {'update_available': name != 'current', 'running': name == 'busy', 'dirty': name == 'dirty'}

    def test_only_eligible_apps_reserved_and_processed_even_after_failure(self):
        with patch.object(self.manager, 'get_status', side_effect=self.status), \
             patch('services.update_manager.threading.Thread') as thread:
            result, code = self.manager.start_all_updates(self.apps)
            self.assertEqual(code, 202)
            self.assertEqual(result['queued'], ['one', 'two'])
            self.assertEqual(result['skipped'], ['dirty'])
            self.assertTrue(self.manager.is_running('two'))
            snapshot = self.manager.get_batch_status()
            self.assertTrue(snapshot['running'])
            self.assertEqual([item['id'] for item in snapshot['items']], ['one', 'two'])
            self.manager._append_job_log('one', 'Building image')
            self.assertEqual(snapshot['items'][0]['log'], [])
            self.assertEqual(self.manager.get_batch_status()['items'][0]['log'], ['Building image'])
            self.assertEqual(self.manager.start_update({'id': 'two'})[1], 409)
            self.assertEqual(self.manager.start_all_updates(self.apps)[1], 409)
            target, args = thread.call_args.kwargs['target'], thread.call_args.kwargs['args']
        visited = []
        def update(app, directory):
            visited.append(app['id'])
            self.assertEqual(self.manager._jobs[app['id']]['state'], 'updating')
            if app['id'] == 'one':
                raise RuntimeError('Fixture build failed')
            self.manager._set_job(app['id'], {'running': False, 'state': 'up_to_date'})
        with patch.object(self.manager, '_run_update', side_effect=update):
            target(*args)
        self.assertCountEqual(visited, ['one', 'two'])
        self.assertFalse(self.manager.is_running('one'))
        self.assertFalse(self.manager._batch_lock.locked())
        self.assertFalse(self.manager.get_batch_status()['running'])
        self.assertEqual(self.manager.get_batch_status()['items'][0]['state'], 'failed')

    def test_empty_batch_releases_lock_without_worker(self):
        with patch.object(self.manager, 'get_status', return_value={'update_available': False}), \
             patch('services.update_manager.threading.Thread') as thread:
            self.assertEqual(self.manager.start_all_updates(self.apps), ({'ok': True, 'queued': [], 'skipped': []}, 200))
            thread.assert_not_called()
            self.assertFalse(self.manager._batch_lock.locked())

    def test_two_concurrent_updates_and_next_starts_when_one_fails(self):
        names = ['one', 'two', 'three', 'four']
        started = {name: threading.Event() for name in names}
        release = {name: threading.Event() for name in names}
        lock = threading.Lock()
        counts = {'active': 0, 'peak': 0}
        queued = [({'id': name}, Path(self.temp.name)) for name in names]
        for name in names:
            self.manager._set_job(name, {'state': 'queued', 'running': True})
        def update(app, directory):
            name = app['id']
            with lock:
                counts['active'] += 1
                counts['peak'] = max(counts['peak'], counts['active'])
            started[name].set()
            try:
                if not release[name].wait(5):
                    raise RuntimeError('Test worker timed out')
                if name == 'one':
                    raise RuntimeError('Fixture build failed')
                self.manager._set_job(name, {'running': False, 'state': 'up_to_date'})
            finally:
                with lock:
                    counts['active'] -= 1
        self.manager._batch_lock.acquire()
        with patch.object(self.manager, '_run_update', side_effect=update):
            worker = threading.Thread(target=self.manager._run_all_updates, args=(queued,))
            worker.start()
            try:
                self.assertTrue(started['one'].wait(2))
                self.assertTrue(started['two'].wait(2))
                self.assertFalse(started['three'].is_set())
                self.assertFalse(started['four'].is_set())
                release['one'].set()
                self.assertTrue(started['three'].wait(2))
                self.assertTrue(self.manager.is_running('two'))
                self.assertFalse(started['four'].is_set())
            finally:
                for event in release.values():
                    event.set()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(counts['peak'], 2)
        self.assertTrue(all(event.is_set() for event in started.values()))
        self.assertFalse(self.manager._batch_lock.locked())
        self.assertEqual(self.manager._jobs['one']['state'], 'failed')


class UpdateAllRouteTests(unittest.TestCase):
    setUp = fixtures.AccessTokenTests.setUp
    tearDown = fixtures.AccessTokenTests.tearDown
    login = fixtures.AccessTokenTests.login

    def test_batch_status_requires_admin_and_never_checks_git(self):
        with patch.object(hub._update_manager, 'get_status') as git_status:
            self.assertEqual(self.client.get('/api/apps-updates/batch').status_code, 401)
            self.login(self.user)
            self.assertEqual(self.client.get('/api/apps-updates/batch').status_code, 403)
            self.login(self.admin)
            response = self.client.get('/api/apps-updates/batch')
            self.assertEqual(response.status_code, 200)
            self.assertIn('items', response.json)
            git_status.assert_not_called()

    def test_only_admin_can_start_queue(self):
        with patch.object(hub._update_manager, 'start_all_updates', return_value=({'ok': True, 'queued': ['fjordlens']}, 202)) as start:
            self.assertEqual(self.client.post('/api/apps-updates/start-all').status_code, 401)
            self.login(self.user)
            self.assertEqual(self.client.post('/api/apps-updates/start-all').status_code, 403)
            start.assert_not_called()
            self.login(self.admin)
            response = self.client.post('/api/apps-updates/start-all')
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json['queued'], ['fjordlens'])
            start.assert_called_once()
