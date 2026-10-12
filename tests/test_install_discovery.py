from unittest.mock import patch

import pytest

import app as hub
from services.install_state import InstallState


@pytest.mark.parametrize('runtime', ['running', 'exited', 'paused', 'restarting', 'created',
                                    'not_installed', 'unknown', 'error'])
def test_checkout_discovery_requires_a_container(tmp_path, runtime):
    checkout = tmp_path / 'fjordseed'
    (checkout / '.git').mkdir(parents=True)
    state = InstallState(tmp_path)
    definition = {'id': 'fjordseed', 'compose_dir': str(checkout)}
    with patch.object(hub, '_install_state', state), \
         patch.object(hub.docker_mgr, 'get_status', return_value={'state': runtime}):
        hub._ensure_install_state_for_existing_app(definition)
    assert bool(state.get_install_dir('fjordseed')) == (runtime in {
        'running', 'exited', 'paused', 'restarting', 'created'})


@pytest.mark.parametrize('previous_registration', [False, True])
def test_missing_container_stays_available_with_preserved_checkout(tmp_path, previous_registration):
    checkout = tmp_path / 'fjordseed'
    (checkout / '.git').mkdir(parents=True)
    state = InstallState(tmp_path)
    if previous_registration:
        # Older versions rediscovered the checkout after successful removal.
        state.register('fjordseed', str(checkout))
    definition = {'id': 'fjordseed', 'compose_dir': str(checkout), 'default_port': 8080}
    with patch.object(hub, '_install_state', state), \
         patch.object(hub, '_get_apps', return_value=[definition]), \
         patch.object(hub.docker_mgr, 'get_status', return_value={'state': 'not_installed'}):
        with hub.app.test_request_context('/api/apps-status'):
            for _ in range(2):
                assert hub.api_apps_status().json['fjordseed']['state'] == 'not_installed'
    assert (checkout / '.git').is_dir()
    if not previous_registration:
        assert state.get('fjordseed') == {}


def test_deleted_app_cannot_be_updated_even_with_stale_registration_and_cache(tmp_path):
    from services.update_manager import UpdateManager
    state=InstallState(tmp_path)
    state.register('fjordseed',str(tmp_path))
    manager=UpdateManager(state,runtime_exists=hub._update_manager._runtime_exists)
    definition={'id':'fjordseed','container_name':'fjordseed'}
    manager._set_cache('fjordseed',{'state':'update_available','update_available':True})
    with patch.object(hub.docker_mgr,'get_status',return_value={'state':'not_installed'}), \
         patch.object(manager,'_git_info') as git, \
         patch('services.update_manager.threading.Thread') as thread:
        assert manager.get_status(definition)['state']=='not_installed'
        assert manager.check_now(definition)['update_available'] is False
        assert manager.start_update(definition)[1]==404
        assert manager.start_all_updates([definition])[0]['queued']==[]
        # Even a stale batch result must be rejected under the operation lock.
        with patch.object(manager,'get_status',return_value={'update_available':True}):
            assert manager.start_all_updates([definition])[0]['queued']==[]
        git.assert_not_called()
        thread.assert_not_called()
    assert not manager._reservations


def test_stopped_installed_app_still_has_updates(tmp_path):
    from services.update_manager import UpdateManager
    state=InstallState(tmp_path)
    state.register('fjordseed',str(tmp_path))
    manager=UpdateManager(state,runtime_exists=hub._update_manager._runtime_exists)
    with patch.object(hub.docker_mgr,'get_status',return_value={'state':'exited'}), \
         patch.object(manager,'_git_info',return_value={'state':'update_available','update_available':True}):
        assert manager.get_status({'id':'fjordseed'})['update_available']
