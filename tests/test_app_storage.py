import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from services.app_storage import AppStorage, host_path, patched_env
from services.install_state import InstallState
from services.storage_copy import transfer, cleanup, MANIFEST
from services.storage_browser import browse, probe, checked


class StorageBrowserTests(unittest.TestCase):
    def test_browse_only_directories_and_reports_free_space(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'mnt/disk/movies').mkdir(parents=True)
            (root / 'mnt/disk/private.txt').write_text('not listed')
            self.assertEqual(browse(root, '')['directories'], [{'name':'/mnt', 'path':'/mnt'}])
            result = browse(root, '/mnt/disk')
            self.assertEqual(result['directories'], [{'name':'movies','path':'/mnt/disk/movies'}])
            self.assertEqual(result['parent'], '/mnt')
            self.assertGreater(result['free_bytes'], 0)
            self.assertEqual(browse(root, '/mnt')['parent'], '')

    def test_new_nested_folder_is_scoped_to_existing_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'mnt/disk').mkdir(parents=True)
            self.assertEqual(probe(root, '/mnt/disk/new/films'), {'ancestor':'/mnt/disk','relative':'new/films'})
            self.assertFalse((root / 'mnt/disk/new').exists())
            for path in ('/etc', '/mnt/../../etc', '/mnt2/files', '/proc', '/srv/new'):
                with self.subTest(path=path), self.assertRaises(ValueError): probe(root, path)

    def test_ensure_destination_only_mounts_existing_parent_for_creation(self):
        service = AppStorage(MagicMock(), MagicMock())
        service.folders = MagicMock(side_effect=[{'ancestor':'/mnt/disk','relative':'new/films'}, {'created':True}])
        service.ensure_destination('/mnt/disk/new/films')
        self.assertEqual([c.args for c in service.folders.call_args_list], [
            ('probe','/mnt/disk/new/films'), ('create','new/films','/mnt/disk')])


class StorageCopyTests(unittest.TestCase):
    def test_move_removes_originals_after_verified_copy_even_if_app_updates_database(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            (source / 'nested').mkdir(parents=True); target.mkdir()
            (source / 'nested/movie').write_bytes(b'film')
            (source / 'database').write_bytes(b'database')
            copied = transfer(source, target, prepare_move=True)
            (target / 'database').write_bytes(b'updated by app')
            cleanup(source, target, copied['manifest_sha256'])
            self.assertFalse(any(source.iterdir()))
            self.assertEqual((target / 'nested/movie').read_bytes(), b'film')
            self.assertEqual((target / 'database').read_bytes(), b'updated by app')
            self.assertFalse((target / MANIFEST).exists())

    def test_move_preserves_originals_when_source_or_manifest_or_destination_changes(self):
        for change in ('modified', 'added', 'missing_target', 'manifest'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                source, target = Path(folder) / 'old', Path(folder) / 'new'
                source.mkdir(); target.mkdir()
                (source / 'movie').write_bytes(b'film')
                copied = transfer(source, target, prepare_move=True)
                if change == 'modified': (source / 'movie').write_bytes(b'new film')
                if change == 'added': (source / 'extra').write_bytes(b'extra')
                if change == 'missing_target': (target / 'movie').unlink()
                if change == 'manifest': (target / MANIFEST).write_text('{}')
                with self.assertRaises((ValueError, OSError)):
                    cleanup(source, target, copied['manifest_sha256'])
                self.assertTrue((source / 'movie').exists())

    def test_move_symlinks_preserves_external_target(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            source.mkdir(); target.mkdir()
            outside = Path(folder) / 'keep'; outside.write_text('keep')
            try:
                (source / 'link').symlink_to(outside)
            except OSError:
                self.skipTest('Symlink creation requires Windows developer mode')
            copied = transfer(source, target, prepare_move=True)
            cleanup(source, target, copied['manifest_sha256'])
            self.assertEqual(outside.read_text(), 'keep')
            self.assertTrue((target / 'link').is_symlink())

    def test_copy_verifies_contents_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            (source / 'nested').mkdir(parents=True); target.mkdir()
            (source / 'nested' / 'movie.mkv').write_bytes(b'video-data' * 1000)
            (source / 'hub.db').write_bytes(b'database')
            before = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob('*') if p.is_file()}
            check = transfer(source, target, True)
            self.assertFalse(any(target.iterdir()))
            result = transfer(source, target)
            self.assertEqual(check['bytes'], result['bytes'])
            for relative, content in before.items():
                self.assertEqual((source / relative).read_bytes(), content)
                self.assertEqual((target / relative).read_bytes(), content)

    def test_destination_contents_and_same_or_nested_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            source.mkdir(); target.mkdir()
            (target / 'keep').write_text('keep')
            with self.assertRaises(ValueError): transfer(source, target)
            self.assertEqual((target / 'keep').read_text(), 'keep')
            with self.assertRaises(ValueError): transfer(source, source)
            nested = source / 'nested'; nested.mkdir()
            with self.assertRaises(ValueError): transfer(source, nested)

    def test_invalid_paths_and_env_injection_are_rejected(self):
        for path in ('/', '/etc/passwd', '/mnt/../etc', '/mnt/a\nSECRET=x', '/mnt/$HOME', '/var/lib/docker/data', '/mnt/a:b'):
            with self.subTest(path=path), self.assertRaises(ValueError): host_path(path)
        self.assertEqual(host_path('/mnt/storage/my movies'), '/mnt/storage/my movies')
        original = 'SECRET=a$b\nCOMPOSE_FILE=a.yml:b.yml\nDATA_DIR=/data\nUPLOADS_HOST_DIR=/old\n'
        updated = patched_env(original, 'UPLOADS_HOST_DIR', '/mnt/new')
        self.assertIn('SECRET=a$b\nCOMPOSE_FILE=a.yml:b.yml\nDATA_DIR=/data\n', updated)
        self.assertIn("UPLOADS_HOST_DIR='/mnt/new'", updated)


class StorageTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = self.root / '.env'
        self.original = 'SECRET=unchanged\nCOMPOSE_FILE=base.yml:gpu.yml\nUPLOADS_HOST_DIR=/old/files\n'
        self.env.write_text(self.original)
        self.state = InstallState(self.root)
        self.state.register('demo', str(self.root))
        self.manager = MagicMock()
        container = MagicMock()
        container.labels = {'com.docker.compose.service':'app', 'com.docker.compose.project':'demo'}
        container.status = 'running'
        container.attrs = {'Mounts':[{'Type':'bind','Source':'/old/files','Destination':'/media'}]}
        self.manager.client.containers.list.return_value = [container]
        self.service = AppStorage(self.manager, self.state)
        self.app = {'id':'demo','setup_steps':[{'fields':[{'key':'UPLOADS_HOST_DIR','type':'path','label':'Film'}]}]}
        self.service.save('demo', id='test', running=True)
        self.service.active.add('demo')
        self.service.configuration = lambda directory, extra=None: {'name':'demo','services':{
            'app':{'image':'app:test','volumes':[{'type':'bind','source':(extra or {}).get('UPLOADS_HOST_DIR','/old/files'),'target':'/media'}]}}}
        self.service.helper = MagicMock(return_value={'bytes':123, 'manifest_sha256':'seal'})
        self.service.ensure_destination = MagicMock()
        self.service.compose = MagicMock(return_value='')

    def tearDown(self):
        self.temp.cleanup()

    def test_success_stops_then_copies_and_preserves_other_configuration(self):
        events = []
        self.service.helper.side_effect = lambda a,b,mode: events.append(mode)
        self.service.compose.side_effect = lambda directory,args,**kw: events.append(args[0])
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.assertEqual(events, ['check','stop','copy','up'])
        self.assertIn("UPLOADS_HOST_DIR='/new/files'", self.env.read_text())
        self.assertIn('COMPOSE_FILE=base.yml:gpu.yml', self.env.read_text())
        self.assertEqual((self.root / 'storage-backups/demo/test.env').read_text(), self.original)
        self.assertFalse(self.service.job('demo')['running'])
        self.assertEqual(self.service.job('demo')['error'], '')

    def test_copy_failure_keeps_env_and_restarts_old_configuration(self):
        self.service.helper.side_effect = [{}, RuntimeError('Copy failed')]
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.assertEqual(self.env.read_text(), self.original)
        self.assertEqual([call.args[1][0] for call in self.service.compose.call_args_list], ['stop','up'])
        self.assertIn('Copy failed', self.service.job('demo')['error'])

    def test_directory_creation_failure_does_not_stop_app(self):
        self.service.ensure_destination.side_effect = ValueError('Folder unavailable')
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.service.compose.assert_not_called()
        self.service.helper.assert_not_called()
        self.assertEqual(self.env.read_text(), self.original)

    def test_move_cleanup_only_after_activation(self):
        events = []
        def helper(a, b, mode, *args):
            events.append(mode)
            return {'manifest_sha256': 'seal'}
        self.service.helper.side_effect = helper
        self.service.compose.side_effect = lambda directory,args,**kw: events.append(args[0])
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files', 'move')
        self.assertEqual(events, ['check', 'stop', 'prepare-move', 'up', 'cleanup'])
        self.assertEqual(self.service.job('demo')['phase'], 'complete')

    def test_failed_activation_never_deletes_originals(self):
        self.service.compose.side_effect = ['', RuntimeError('Start failed'), '']
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files', 'move')
        self.assertEqual(self.env.read_text(), self.original)
        self.assertEqual([c.args[2] for c in self.service.helper.call_args_list], ['check', 'prepare-move'])

    def test_cleanup_failure_keeps_new_configuration_without_rollback(self):
        self.service.helper.side_effect = [{}, {'manifest_sha256': 'seal'}, RuntimeError('Cleanup failed')]
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files', 'move')
        self.assertIn("UPLOADS_HOST_DIR='/new/files'", self.env.read_text())
        self.assertEqual(self.service.compose.call_count, 2)
        self.assertEqual(self.service.job('demo')['phase'], 'cleanup_incomplete')
        self.assertFalse(self.service.job('demo')['running'])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            self.service.start(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files', 'delete')

    def test_start_failure_rolls_back_configuration(self):
        self.service.compose.side_effect = ['', RuntimeError('Start failed'), '']
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.assertEqual(self.env.read_text(), self.original)
        self.assertEqual(self.service.compose.call_count, 3)
        self.assertIn('Start failed', self.service.job('demo')['error'])

    def test_concurrent_env_edit_is_not_overwritten_or_started(self):
        def helper(a,b,mode):
            if mode == 'copy': self.env.write_text('Changed externally')
        self.service.helper.side_effect = helper
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.assertEqual(self.env.read_text(), 'Changed externally')
        self.assertEqual(self.service.compose.call_count, 1)
        self.assertIn('forbliver stoppet', self.service.job('demo')['error'])

    def test_stale_location_does_not_stop_app(self):
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/stale/files')
        self.service.compose.assert_not_called()
        self.service.helper.assert_not_called()
        self.assertEqual(self.env.read_text(), self.original)

    def test_stopped_app_stays_stopped(self):
        self.manager.client.containers.list.return_value[0].status = 'exited'
        self.service.run(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')
        self.assertEqual([call.args[1][0] for call in self.service.compose.call_args_list], ['stop'])

    def test_interrupted_job_is_visible_and_blocks_another_move(self):
        self.service.active.clear()
        self.assertTrue(self.service.job('demo')['interrupted'])
        with self.assertRaises(ValueError): self.service.start(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')

    def test_two_apps_cannot_copy_into_the_same_destination(self):
        self.service.save('demo', running=False)
        self.state.set_storage_job('other', {'running':True, 'source':'/other/files', 'destination':'/new/files'})
        with self.assertRaisesRegex(ValueError, 'anden flytning'):
            self.service.start(self.app, 'UPLOADS_HOST_DIR', '/new/files', '/old/files')


class StorageEndpointTests(unittest.TestCase):
    def setUp(self):
        import app as hub
        from services.auth import AuthService
        self.hub = hub
        self.temp = tempfile.TemporaryDirectory()
        self.auth = AuthService(Path(self.temp.name) / 'auth.db')
        self.admin = self.auth.create_user('admin', 'test-password', role='admin')
        self.user = self.auth.create_user('viewer', 'test-password')
        self.storage = MagicMock()
        self.storage.busy.return_value = False
        self.storage.job.return_value = {'running':True}
        self.storage.describe.return_value = {'fields':[{'key':'DATA_DIR','path':'/old/data'}], 'job':{}}
        self.updates = MagicMock(); self.updates.is_running.return_value = False
        self.state = MagicMock(); self.state.get.return_value = {'state':'installed'}
        self.patches = [patch.object(hub, '_auth', self.auth), patch.object(hub, 'app_storage', self.storage),
                        patch.object(hub, '_update_manager', self.updates), patch.object(hub, '_install_state', self.state),
                        patch.object(hub, '_get_app', return_value={'id':'demo'})]
        for item in self.patches: item.start()
        self.client = hub.app.test_client()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def login(self, uid):
        with self.client.session_transaction() as session:
            session['_user_id'], session['_fresh'] = str(uid), True

    def test_only_admin_can_read_or_change_paths(self):
        self.login(self.user)
        self.assertEqual(self.client.get('/api/apps/demo/storage').status_code, 403)
        self.assertEqual(self.client.get('/api/apps/demo/storage?folders=1').status_code, 403)
        self.assertEqual(self.client.post('/api/apps/demo/storage', json={}).status_code, 403)
        self.storage.start.assert_not_called()
        self.login(self.admin)
        self.assertEqual(self.client.get('/api/apps/demo/storage').status_code, 200)
        response = self.client.post('/api/apps/demo/storage', json={'key':'DATA_DIR','source':'/old/data','destination':'/new/data'})
        self.assertEqual(response.status_code, 202)
        self.storage.start.assert_called_once_with({'id':'demo'}, 'DATA_DIR', '/new/data', '/old/data', 'copy')
        response = self.client.post('/api/apps/demo/storage', json={'key':'DATA_DIR','source':'/old/data','destination':'/new/data','mode':'move'})
        self.assertEqual(response.status_code, 202)
        self.storage.start.assert_called_with({'id':'demo'}, 'DATA_DIR', '/new/data', '/old/data', 'move')

    def test_admin_browses_host_folders_and_receives_validation_errors(self):
        self.login(self.admin)
        self.storage.folders.return_value = {'path':'/mnt','parent':'','directories':[]}
        response = self.client.get('/api/apps/demo/storage?folders=1&path=/mnt')
        self.assertEqual(response.status_code, 200)
        self.storage.folders.assert_called_once_with('browse', '/mnt')
        self.storage.folders.side_effect = ValueError('Invalid path')
        self.assertEqual(self.client.get('/api/apps/demo/storage?folders=1&path=/etc').status_code, 400)

    def test_storage_and_update_jobs_cannot_overlap(self):
        self.login(self.admin)
        self.updates.is_running.return_value = True
        self.assertEqual(self.client.post('/api/apps/demo/storage', json={}).status_code, 409)
        self.storage.start.assert_not_called()
        self.storage.busy.return_value = True
        self.assertEqual(self.client.post('/apps/demo/update/start').status_code, 409)
        self.updates.start_update.assert_not_called()
        with patch.object(self.hub.docker_mgr, 'start') as start:
            self.assertEqual(self.client.post('/apps/demo/start').status_code, 409)
            start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
