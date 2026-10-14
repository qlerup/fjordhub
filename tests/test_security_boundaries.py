"""Defensive full-route regressions, using only synthetic identities and sinks."""
from unittest.mock import Mock

import pytest
from flask.testing import FlaskClient

import app as hub
from services.auth import AuthService
from services.install_state import InstallState
from services.password_reset import PasswordResetService
from services.install_validation import validate_install_values


@pytest.fixture
def security(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / 'hub.db')
    auth.create_user('admin', 'test-password', role='admin', email='admin@example.test')
    auth.create_user('reader', 'test-password', email='reader@example.test')
    monkeypatch.setattr(hub, '_auth', auth)
    monkeypatch.setattr(hub, '_install_state', InstallState(tmp_path))
    monkeypatch.setattr(hub, '_get_apps', lambda: [])
    monkeypatch.setattr(hub.app, 'test_client_class', FlaskClient)
    return auth


def token(client):
    with client.session_transaction() as state:
        return state['hub_csrf']


def login(name='admin'):
    client = hub.app.test_client()
    assert client.get('/login').status_code == 200
    assert client.post('/login', data={'username': name, 'password': 'test-password',
                                     'csrf_token': token(client)}).status_code == 302
    return client


def test_admin_can_require_email_on_existing_session_and_member_app_can_complete_it(security):
    reader = login('reader')
    admin = login()
    uid = security.get_by_username('reader').id
    version = security.get_by_id(uid).session_version
    data = {'username':'reader', 'email':'reader@example.test', 'role':'user',
            'require_email_update':'1', 'csrf_token':token(admin)}
    assert admin.post(f'/users/{uid}/edit', data=data).status_code == 302
    assert security.get_by_id(uid).email_required
    assert security.get_by_id(uid).session_version == version
    assert reader.get('/').location.endswith('/profile')
    assert reader.get('/profile').status_code == 200
    assert reader.get('/api/auth/access').json['email_required'] is True
    security.set_user_app_access(uid, 'fjordflix')
    security.save_hub_key('fjordflix', 'test-key')
    security.save_hub_key('fjordlens', 'lens-key')
    path = f'/api/hub/apps/users/{uid}/email'
    client = hub.app.test_client()
    assert client.post(path,json={'app_id':'fjordflix','email':'new@example.test'}).status_code == 400
    assert client.post(path,json={'app_id':'fjordlens','email':'new@example.test'},headers={'X-Hub-Key':'lens-key'}).status_code == 403
    for email in ('invalid', 'admin@example.test'):
        result = client.post(path,json={'app_id':'fjordflix','email':email},headers={'X-Hub-Key':'test-key'})
        assert result.status_code == 200 and result.json['accepted'] is False
        assert security.get_by_id(uid).email_required
    result = client.post(path,json={'app_id':'fjordflix','email':'new@example.test'},headers={'X-Hub-Key':'test-key'})
    assert result.status_code == 200 and result.json['accepted'] is True
    assert security.get_by_id(uid).email == 'new@example.test'
    assert not security.get_by_id(uid).email_required
    assert reader.get('/').status_code == 200
    assert reader.get('/api/auth/access').json['authenticated'] is True
    # The dedicated endpoint cannot change email again after completion.
    client.post(path,json={'app_id':'fjordflix','email':'overwrite@example.test'},headers={'X-Hub-Key':'test-key'})
    assert security.get_by_id(uid).email == 'new@example.test'
    assert reader.post(f'/users/{uid}/edit', data={**data, 'csrf_token':token(reader)}).status_code == 403


@pytest.mark.parametrize('path,method,endpoint', [
    ('/apps/demo/install', 'POST', 'install_app'),
    ('/apps/demo/start', 'POST', 'start_app'),
    ('/apps/demo/stop', 'POST', 'stop_app'),
    ('/apps/demo/update/check', 'POST', 'check_app_update'),
    ('/apps/demo/update/start', 'POST', 'start_app_update'),
    ('/apps/demo/uninstall', 'POST', 'uninstall_app'),
    ('/apps/demo/wizard', 'GET', 'install_wizard'),
    ('/apps/demo/install/status', 'GET', 'install_status'),
    ('/api/mount-nfs', 'POST', 'api_mount_nfs'),
    ('/api/mkdir', 'POST', 'api_mkdir'),
    ('/api/list-nfs-exports?host=example.test', 'GET', 'api_list_nfs_exports'),
    ('/api/gpu-preflight', 'POST', 'api_gpu_preflight'),
    ('/api/gpu-setup', 'POST', 'api_gpu_setup'),
    ('/api/docker-cleanup', 'POST', 'api_docker_cleanup'),
    ('/api/registry/refresh', 'POST', 'api_registry_refresh'),
    ('/api/hub/self/update/start', 'POST', 'api_hub_self_update_start'),
])
def test_admin_gate_precedes_operation(security, monkeypatch, path, method, endpoint):
    operation = Mock(return_value=('', 204))
    monkeypatch.setitem(hub.app.view_functions, endpoint, operation)
    anonymous = hub.app.test_client()
    assert anonymous.open(path, method=method).status_code in (302, 401)
    ordinary = login('reader')
    assert ordinary.open(path, method=method, headers={'X-CSRF-Token': token(ordinary)}).status_code == 403
    operation.assert_not_called()
    admin = login()
    assert admin.open(path, method=method, headers={'X-CSRF-Token': token(admin)}).status_code == 204
    operation.assert_called_once()


def test_sensitive_form_requires_session_bound_csrf(security):
    client = login()
    data = {'username': 'new-reader', 'password': 'test-password', 'email': 'new@example.test', 'role': 'user'}
    assert client.post('/users/create', data=data).status_code == 403
    other = login()
    assert client.post('/users/create', data={**data, 'csrf_token': token(other)}).status_code == 403
    assert security.get_by_username('new-reader') is None
    assert client.post('/users/create', data={**data, 'csrf_token': token(client)}).status_code == 302
    assert security.get_by_username('new-reader') is not None


def test_public_login_and_json_mutations_are_protected(security, monkeypatch):
    client = hub.app.test_client()
    assert client.post('/login', data={'username':'admin','password':'test-password'}).status_code == 403
    client = login()
    sink = Mock(return_value=(True, 'started'))
    monkeypatch.setattr(hub, '_get_app', lambda _: {'id':'demo'})
    monkeypatch.setattr(hub.docker_mgr, 'start', sink)
    monkeypatch.setattr(hub, '_with_compose_dir', lambda definition, _: definition)
    assert client.post('/apps/demo/start', json={}).status_code == 403
    sink.assert_not_called()
    assert client.post('/apps/demo/start', json={}, headers={'X-CSRF-Token':token(client)}).status_code == 200
    sink.assert_called_once()


@pytest.mark.parametrize('endpoint', ['/api/hub/user-sync', '/api/hub/apps/users'])
def test_app_identity_cannot_change_unlinked_or_linked_profile(security, endpoint):
    security.save_hub_key('demo', 'synthetic-app-key')
    client = hub.app.test_client()
    headers = {'X-Hub-Key':'synthetic-app-key'}
    data = {'app_id':'demo', 'username':'admin', 'email':'changed@example.test', 'role':'user'}
    assert client.post(endpoint, json=data, headers=headers).status_code == 400
    assert security.get_by_username('admin').email == 'admin@example.test'
    assert security.get_user_app_role(1, 'demo') is None
    security.set_user_app_access(1, 'demo', 'user')
    assert client.post(endpoint, json=data, headers=headers).status_code in (200, 201)
    assert security.get_by_username('admin').email == 'admin@example.test'
    data.update(username='new-app-user', email='new-app@example.test', password='test-password')
    assert client.post(endpoint, json=data, headers=headers).status_code in (200, 201)
    assert security.get_by_username('new-app-user').role == 'user'


def test_password_change_revokes_other_session_and_retains_current(security):
    current, other = login(), login()
    assert current.post('/profile', data={'current_password':'test-password',
        'new_password':'new-test-password','new_password2':'new-test-password',
        'csrf_token':token(current)}).status_code == 302
    assert current.get('/users').status_code == 200
    assert other.get('/users').status_code == 302
    assert security.check_password('admin','test-password') is None


def test_public_reset_revokes_existing_browser(security, monkeypatch):
    service = PasswordResetService(security._db_path, hub.app.secret_key, security)
    service.set_enabled(True)
    sent = []
    monkeypatch.setattr(service, '_send_code', lambda email, code, **kwargs: sent.append(code))
    monkeypatch.setattr(hub, '_password_reset', service)
    old = login('reader')
    challenge = service.request('reader@example.test')
    reset_token = service.verify(challenge, sent[0])
    reset = hub.app.test_client()
    assert reset.get('/glemt-adgangskode').status_code == 200
    result = reset.post('/glemt-adgangskode', data={'step':'password','challenge_id':challenge,
        'reset_token':reset_token,'password':'new-test-password','password2':'new-test-password',
        'csrf_token':token(reset)})
    assert result.status_code == 200
    assert security.check_password('reader','new-test-password')
    assert old.get('/profile').status_code == 302


@pytest.mark.parametrize('values', [{'COMPOSE_FILE':'other.yml'}, {'PATH':'custom'}, {'UPLOADS_HOST_DIR':'/etc'},
    {'UPLOADS_HOST_DIR':'/'}, {'UPLOADS_HOST_DIR':'/mnt/../etc'}, {'UPLOADS_HOST_DIR':'C:\\'},
    {'UPLOADS_HOST_DIR':'/srv/data:ro'}, {'UPLOADS_HOST_DIR':'//etc/fjord/data'},
    {'APP_PORT':'8080\nUNEXPECTED=1'}])
def test_install_rejects_unapproved_values_before_side_effects(security, monkeypatch, values):
    definition={'id':'demo','setup_steps':[{'fields':[{'key':'UPLOADS_HOST_DIR','type':'path'},
        {'key':'APP_PORT','type':'number'}]}]}
    monkeypatch.setattr(hub, '_get_app', lambda _: definition)
    start = Mock()
    monkeypatch.setattr(hub._installer, 'start_install', start)
    client=login()
    result=client.post('/apps/demo/install',json={'env':values},headers={'X-CSRF-Token':token(client)})
    assert result.status_code == 400
    start.assert_not_called()
    assert security.get_hub_key('demo') is None


def test_all_catalog_defaults_remain_valid():
    import json
    from pathlib import Path
    for path in (Path(__file__).parents[1] / 'app_registry').glob('*.json'):
        definition=json.loads(path.read_text(encoding='utf-8'))
        supplied={f['key']:str(f.get('default','')) for step in definition.get('setup_steps',[])
                  for f in step.get('fields',[])}
        assert validate_install_values(definition,supplied)==supplied


def test_updater_proxy_sends_auth_without_redirects(security, monkeypatch):
    monkeypatch.setattr(hub,'FJORDHUB_UPDATER_URL','http://updater.invalid:8090')
    monkeypatch.setattr(hub,'load_updater_token',lambda _: 'synthetic-control-token')
    response=Mock(status_code=200)
    response.json.return_value={'ok':True}
    for method in ('get','post'):
        request_mock=Mock(return_value=response)
        monkeypatch.setattr(hub.requests,method,request_mock)
        assert hub._hub_update_proxy('/status',method=method.upper())[1]==200
        assert request_mock.call_args.kwargs['headers']=={'Authorization':'Bearer synthetic-control-token'}
        assert request_mock.call_args.kwargs['allow_redirects'] is False


@pytest.mark.parametrize('revoke', ['password', 'membership', 'delete'])
def test_sso_rechecks_identity_and_current_access(security, revoke):
    security.save_hub_key('demo','synthetic-app-key')
    security.set_user_app_access(2,'demo','user')
    client=login('reader')
    first=client.get('/api/hub/sso-token?app_id=demo').json['token']
    headers={'X-Hub-Key':'synthetic-app-key'}
    verifier=hub.app.test_client()
    assert verifier.get('/api/hub/sso-verify',query_string={'app_id':'demo','token':first},headers=headers).status_code==200
    pending=client.get('/api/hub/sso-token?app_id=demo').json['token']
    if revoke=='password':
        security.change_password(2,'new-test-password')
    elif revoke=='membership':
        security.remove_user_app_access(2,'demo')
    else:
        security.delete_user(2)
    assert verifier.get('/api/hub/sso-verify',query_string={'app_id':'demo','token':pending},headers=headers).status_code==401
