import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.auth import AuthService
from services.install_state import InstallState
from services.update_manager import UpdateManager


def test_existing_installation_keeps_directory_url_and_state(tmp_path):
    state = {'fjordshare': {'install_dir': '/apps/fjordshare', 'state': 'installed', 'external_url': 'https://models.example'}}
    (tmp_path / 'install_state.json').write_text(json.dumps(state))
    store = InstallState(tmp_path)
    assert store.get_install_dir('fjord3d') == '/apps/fjordshare'
    assert store.get_external_url('fjord3d') == 'https://models.example'
    assert store.get('fjordshare') == store.get('fjord3d')
    store.register('fjord3d', '/apps/fjordshare')
    store.set_external_url('fjord3d', 'https://models-new.example')
    saved = json.loads((tmp_path / 'install_state.json').read_text())
    assert 'fjordshare' not in saved
    assert saved['fjord3d']['install_dir'] == '/apps/fjordshare'


def test_existing_sso_keys_and_grants_migrate_without_losing_access(tmp_path):
    auth = AuthService(tmp_path / 'auth.db')
    uid = auth.create_user('Model user', 'test-long-password-123', role='user')
    auth.save_hub_key('fjordshare', 'existing-key')
    auth.set_user_app_access(uid, 'fjordshare', 'admin')
    # Seed the layout of an old installation, bypassing normalized write APIs.
    with auth._conn() as conn:
        conn.execute("UPDATE app_hub_keys SET app_id='fjordshare'")
        conn.execute("UPDATE user_app_access SET app_id='fjordshare'")
    auth = AuthService(tmp_path / 'auth.db')
    assert auth.verify_hub_key('fjord3d', 'existing-key')
    assert auth.verify_hub_key('fjordshare', 'existing-key')
    assert auth.get_user_app_role(uid, 'fjord3d') == 'admin'
    assert auth.get_user_app_access(uid)[0]['app_id'] == 'fjord3d'
    assert AuthService(tmp_path / 'auth.db').verify_hub_key('fjord3d', 'existing-key')


def test_container_rename_preserves_actual_nas_mounts_and_secrets(tmp_path):
    (tmp_path / '.env').write_text('FJORDHUB_API_KEY=existing-secret\nDATA_DIR=/wrong/default\n')
    manager = UpdateManager(InstallState(tmp_path))
    container = {'Config': {'Labels': {'com.docker.compose.service': 'fjordshare'}}, 'Mounts': [
        {'Type': 'bind', 'Destination': target, 'Source': source}
        for target, source in [('/data', '/srv/models-db'), ('/uploads', '/mnt/nas/3d originals'), ('/thumbs', '/srv/3d-thumbs')]]}
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps([container]), stderr='')
    with patch.object(manager, '_run', return_value=result):
        assert manager._capture_legacy_3d(tmp_path)
    updated = (tmp_path / '.env').read_text()
    assert 'FJORDHUB_API_KEY=existing-secret' in updated
    assert 'DATA_DIR="/srv/models-db"' in updated
    assert 'UPLOADS_HOST_DIR="/mnt/nas/3d originals"' in updated
    assert 'FJORDHUB_APP_ID="fjord3d"' in updated
    assert (tmp_path / '.env.before-fjord3d').read_text().startswith('FJORDHUB_API_KEY=existing-secret')


def test_unverified_data_mounts_stop_migration(tmp_path):
    manager = UpdateManager(InstallState(tmp_path))
    row = {'Config': {'Labels': {'com.docker.compose.service': 'fjordshare'}}, 'Mounts': []}
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps([row]), stderr='')
    with patch.object(manager, '_run', return_value=result), pytest.raises(RuntimeError, match='datastier'):
        manager._capture_legacy_3d(tmp_path)
    assert not (tmp_path / '.env').exists()


@pytest.mark.parametrize('app_id,container_name,folder', [
    ('fjord3d', 'fjordshare', 'fjordshare'), ('fjordparcel', 'fjordparcel', 'fjordparcel')])
def test_unregistered_running_apps_discovered_through_hub_mount(tmp_path, app_id, container_name, folder):
    import app as hub
    checkout = tmp_path / 'hub' / 'apps' / folder
    (checkout / '.git').mkdir(parents=True)
    container = SimpleNamespace(attrs={'Config': {'Labels': {
        'com.docker.compose.project.working_dir': '/host/hub/apps/' + folder}}})
    hub_container = SimpleNamespace(attrs={'Mounts': [{
        'Type': 'bind', 'Source': '/host/hub', 'Destination': str(tmp_path / 'hub')}]})
    def get(name):
        if name == container_name:
            return container
        if name == 'fjordhub':
            return hub_container
        raise hub.docker.errors.NotFound('not found')
    client = SimpleNamespace(containers=SimpleNamespace(get=get))
    state_dir = tmp_path / 'state'
    state_dir.mkdir()
    state = InstallState(state_dir)
    definition = {'id': app_id, 'container_name': app_id, 'legacy_container_names': ['fjordshare'] if app_id == 'fjord3d' else []}
    with patch.object(hub.docker_mgr, 'client', client), patch.object(hub, '_install_state', state), patch.object(hub, 'APPS_BASE', tmp_path / 'missing'):
        hub._ensure_install_state_for_existing_app(definition)
    assert state.get_install_dir(app_id) == str(checkout)


@pytest.mark.parametrize('startup_fails', [False, True])
def test_rename_builds_before_stopping_and_restores_old_container_on_failure(tmp_path, startup_fails):
    manager = UpdateManager(InstallState(tmp_path))
    calls = []
    def logged(app_id, args, **kwargs):
        calls.append(args)
        return 1 if startup_fails and args[:3] == ['docker', 'compose', 'up'] else 0
    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout='', stderr='')
    info = {'ok': True, 'dirty': False, 'update_available': True, 'current_rev': 'old', 'remote_rev': 'new', 'branch': 'main'}
    with patch.object(manager, '_git_info', return_value=info), patch.object(manager, '_capture_legacy_3d', return_value={'legacy': True}), \
         patch.object(manager, '_changed_paths', return_value=['docker-compose.yml']), patch.object(manager, '_compose_build_services_for_changes', return_value=['fjord3d']), \
         patch.object(manager, '_run_logged', side_effect=logged), patch.object(manager, '_run', side_effect=run), \
         patch.object(manager, '_complete_legacy_3d') as complete:
        manager._run_update({'id': 'fjord3d', 'name': 'Fjord3D'}, tmp_path)
    assert calls.index(['docker', 'compose', 'build']) < calls.index(['docker', 'stop', 'fjordshare'])
    if startup_fails:
        assert ['docker', 'start', 'fjordshare'] in calls
        assert not complete.called
        assert manager._jobs['fjord3d']['state'] == 'failed'
    else:
        complete.assert_called_once_with(tmp_path)
        assert ['docker', 'start', 'fjordshare'] not in calls
        assert manager._jobs['fjord3d']['state'] == 'up_to_date'
