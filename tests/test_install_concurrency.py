import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from services.installer import Installer
from services.install_state import InstallState


def test_concurrent_requests_start_one_worker_and_keep_credentials_and_log(tmp_path):
    state = InstallState(tmp_path)
    installer = Installer(state)
    entered, finish, done = threading.Event(), threading.Event(), threading.Event()
    prepare = Mock()
    barrier = threading.Barrier(8)

    def worker(*args):
        state.append_log('fjordflix', 'first worker')
        entered.set()
        assert finish.wait(5)
        state.set_installed('fjordflix')

    original = installer._run_reserved

    def tracked(*args):
        try:
            original(*args)
        finally:
            done.set()

    def submit():
        barrier.wait(timeout=5)
        return installer.start_install({'id': 'fjordflix'}, {}, before_start=prepare)

    with patch.object(installer, '_run', side_effect=worker) as run, \
         patch.object(installer, '_run_reserved', side_effect=tracked):
        try:
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: submit(), range(8)))
            assert entered.wait(2)
            assert results.count(True) == 1
            assert results.count(False) == 7
            prepare.assert_called_once()
            run.assert_called_once()
            assert state.get('fjordflix')['log'] == ['first worker']
            assert state.get('fjordflix')['state'] == 'installing'
        finally:
            finish.set()
            assert done.wait(3)
    assert state.get('fjordflix')['state'] == 'installed'
    assert not installer._active_installs


def test_other_apps_can_start_while_one_install_is_active(tmp_path):
    installer = Installer(InstallState(tmp_path))
    with patch('services.installer.threading.Thread') as thread:
        assert installer.start_install({'id': 'fjordflix'}, {})
        assert installer.start_install({'id': 'fjordlens'}, {})
        assert not installer.start_install({'id': 'fjordflix'}, {})
        assert thread.call_count == 2


@pytest.mark.parametrize('failure', ['prepare', 'thread'])
def test_failed_launch_releases_reservation_for_retry(tmp_path, failure):
    state = InstallState(tmp_path)
    installer = Installer(state)
    prepare = Mock(side_effect=RuntimeError('launch failed') if failure == 'prepare' else None)
    with patch('services.installer.threading.Thread') as thread:
        if failure == 'thread':
            thread.return_value.start.side_effect = RuntimeError('launch failed')
        with pytest.raises(RuntimeError, match='launch failed'):
            installer.start_install({'id': 'fjordflix'}, {}, before_start=prepare)
        assert not installer._active_installs
        assert state.get('fjordflix')['state'] == 'failed'
        thread.return_value.start.side_effect = None
        assert installer.start_install({'id': 'fjordflix'}, {})


def test_worker_failure_releases_reservation(tmp_path):
    installer = Installer(InstallState(tmp_path))
    installer._active_installs.add('fjordflix')
    with patch.object(installer, '_run', side_effect=RuntimeError('failed')):
        with pytest.raises(RuntimeError):
            installer._run_reserved({'id': 'fjordflix'}, {}, tmp_path, None)
    assert not installer._active_installs


def test_success_clears_old_failure(tmp_path):
    state = InstallState(tmp_path)
    state.set_failed('fjordflix', 'previous attempt failed')
    state.set_installed('fjordflix')
    assert state.get('fjordflix')['error'] is None


def test_duplicate_http_request_keeps_hub_key_and_running_log(tmp_path):
    import app as hub
    from services.auth import AuthService

    state = InstallState(tmp_path)
    auth = AuthService(tmp_path / 'auth.db')
    auth.create_user('install-admin', 'test-password', role='admin')
    installer = Installer(state)
    definition = {'id': 'fjordflix', 'name': 'FjordFlix', 'setup_steps': []}
    with patch.object(hub, '_auth', auth), patch.object(hub, '_install_state', state), \
         patch.object(hub, '_installer', installer), \
         patch.object(hub, '_get_app', return_value=definition), \
         patch.object(hub, 'media_gateway') as gateway, \
         patch('services.installer.threading.Thread') as thread:
        with hub.app.test_client() as client:
            client.post('/login', data={'username': 'install-admin', 'password': 'test-password'})
            payload = {'env': {}, 'media_gateway': {
                'domain': 'media.example.com', 'web_url': 'film.example.com', 'mode': 'managed',
            }}
            assert client.post('/apps/fjordflix/install', json=payload).status_code == 200
            original_key = auth.get_hub_key('fjordflix')
            assert original_key
            worker_values = thread.call_args.kwargs['args'][1]
            assert auth.verify_hub_key('fjordflix', worker_values['FJORDHUB_API_KEY'])
            state.append_log('fjordflix', 'Docker build in progress')
            response = client.post('/apps/fjordflix/install', json=payload)
            assert response.json['already_running'] is True
            assert auth.get_hub_key('fjordflix') == original_key
            assert state.get('fjordflix')['log'] == ['Docker build in progress']
            assert thread.call_count == 1
            gateway.save.assert_called_once()
