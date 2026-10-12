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
