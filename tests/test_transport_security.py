"""Public HTTPS routing and cookie isolation alongside legitimate LAN HTTP use."""
import re

import pytest
from flask.testing import FlaskClient

import app as hub
from services.auth import AuthService
from services.install_state import InstallState
from services.transport_security import TransportPolicy


@pytest.fixture
def transport_client(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / 'auth.db')
    auth.create_user('transport-user', 'synthetic-password', role='user')
    monkeypatch.setattr(hub, '_auth', auth)
    monkeypatch.setattr(hub, '_install_state', InstallState(tmp_path))
    monkeypatch.setitem(hub.app.config, 'FJORDHUB_TRANSPORT_POLICY', TransportPolicy())
    return FlaskClient(hub.app)


def policy(monkeypatch, public='https://hub.example.test', proxies=''):
    monkeypatch.setitem(hub.app.config, 'FJORDHUB_TRANSPORT_POLICY',
                        TransportPolicy.from_config(public, proxies))


def login(client, origin, **kwargs):
    form = client.get('/login', base_url=origin, **kwargs)
    assert form.status_code == 200
    csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', form.get_data(as_text=True)).group(1)
    response = client.post('/login?next=/profile', base_url=origin, data={
        'csrf_token': csrf, 'username': 'transport-user', 'password': 'synthetic-password'}, **kwargs)
    assert response.status_code == 302
    assert response.headers['Location'] == '/profile'
    assert client.get('/profile', base_url=origin, **kwargs).status_code == 200
    return response


def test_default_http_installation_can_log_in_and_out(transport_client):
    client = transport_client
    result = login(client, 'http://192.168.1.110:8888')
    cookie = next(c for c in result.headers.getlist('Set-Cookie') if c.startswith('fjordhub_session='))
    assert 'Secure' not in cookie
    assert 'Strict-Transport-Security' not in result.headers
    with client.session_transaction(base_url='http://192.168.1.110:8888') as session:
        csrf = session['hub_csrf']
    assert client.post('/logout', base_url='http://192.168.1.110:8888',
                       data={'csrf_token': csrf}).status_code == 302
    assert client.get('/profile', base_url='http://192.168.1.110:8888').status_code == 302


def test_public_redirect_keeps_path_query_and_never_reaches_login(transport_client, monkeypatch):
    policy(monkeypatch)
    monkeypatch.setattr(hub._auth, 'check_password', lambda *args: pytest.fail('HTTP must not process credentials'))
    response = transport_client.get('/login?next=%2Fprofile&view=blue', base_url='http://hub.example.test')
    assert response.status_code == 308
    assert response.headers['Location'] == 'https://hub.example.test/login?next=%2Fprofile&view=blue'
    response = transport_client.post('/login', base_url='http://hub.example.test',
                                     data={'username': 'transport-user', 'password': 'synthetic-password'})
    assert response.status_code == 308
    assert response.headers['Location'] == 'https://hub.example.test/login'
    assert not response.headers.getlist('Set-Cookie')


def test_https_domain_and_lan_have_independent_working_logins(transport_client, monkeypatch):
    policy(monkeypatch)
    client = transport_client
    result = login(client, 'https://hub.example.test')
    cookie = next(c for c in result.headers.getlist('Set-Cookie') if c.startswith('__Host-fjordhub_session='))
    assert '; Secure;' in cookie and '; HttpOnly;' in cookie and 'SameSite=Lax' in cookie
    assert 'Path=/' in cookie and 'Domain=' not in cookie
    assert result.headers['Strict-Transport-Security'] == 'max-age=31536000'
    assert client.get('/profile', base_url='http://192.168.1.110:8888').status_code == 302
    lan = login(client, 'http://192.168.1.110:8888')
    assert 'Strict-Transport-Security' not in lan.headers
    assert any(c.startswith('fjordhub_session=') and 'Secure' not in c for c in lan.headers.getlist('Set-Cookie'))
    assert client.get('/profile', base_url='https://hub.example.test').status_code == 200
    assert client.get('/api/health', base_url='http://127.0.0.1:8080').status_code == 200


def test_enabling_public_https_does_not_accept_legacy_insecure_session(transport_client, monkeypatch):
    client = transport_client
    login(client, 'http://hub.example.test')
    policy(monkeypatch)
    result = client.get('/profile', base_url='https://hub.example.test')
    assert result.status_code == 302 and result.location.startswith('/login')
    assert any(c.startswith('fjordhub_session=;') and 'Max-Age=0' in c for c in result.headers.getlist('Set-Cookie'))
    login(client, 'https://hub.example.test')


def test_public_login_sso_internal_verification_and_logout(transport_client, monkeypatch):
    policy(monkeypatch)
    monkeypatch.setattr(hub, '_sso_tokens', {})
    user = hub._auth.get_by_username('transport-user')
    hub._auth.save_hub_key('fjordlens', 'synthetic-app-key')
    hub._auth.set_user_app_access(user.id, 'fjordlens', 'user')
    client = transport_client
    login(client, 'https://hub.example.test')
    issued = client.get('/api/hub/sso-token?app_id=fjordlens', base_url='https://hub.example.test')
    assert issued.status_code == 200 and issued.json['ok']
    machine = FlaskClient(hub.app)
    verified = machine.get('/api/hub/sso-verify', base_url='http://192.168.1.110:8888',
        query_string={'app_id': 'fjordlens', 'token': issued.json['token']},
        headers={'X-Hub-Key': 'synthetic-app-key'})
    assert verified.status_code == 200 and verified.json['username'] == 'transport-user'
    with client.session_transaction(base_url='https://hub.example.test') as session:
        csrf = session['hub_csrf']
    assert client.post('/logout', base_url='https://hub.example.test', data={'csrf_token': csrf}).status_code == 302
    assert client.get('/profile', base_url='https://hub.example.test').status_code == 302


def test_only_explicit_last_hop_proxy_can_report_https(transport_client, monkeypatch):
    policy(monkeypatch, proxies='10.42.0.2/32')
    client = transport_client
    for peer, forwarded in [('10.42.0.3', 'https'), ('10.42.0.2', 'http'), ('10.42.0.2', 'https,http')]:
        response = client.get('/login', base_url='http://hub.example.test',
                              environ_overrides={'REMOTE_ADDR': peer}, headers={'X-Forwarded-Proto': forwarded})
        assert response.status_code == 308
    response = login(client, 'http://hub.example.test', environ_overrides={'REMOTE_ADDR': '10.42.0.2'},
                     headers={'X-Forwarded-Proto': 'https'})
    assert 'Strict-Transport-Security' in response.headers
    assert any(c.startswith('__Host-fjordhub_session=') and '; Secure;' in c for c in response.headers.getlist('Set-Cookie'))


def test_untrusted_forwarding_host_cannot_control_redirect(transport_client, monkeypatch):
    policy(monkeypatch)
    response = transport_client.get('/login?next=//attacker.invalid', base_url='http://hub.example.test',
        headers={'X-Forwarded-Host': 'attacker.invalid', 'X-Forwarded-Proto': 'https',
                 'Forwarded': 'proto=https;host=attacker.invalid', 'CF-Visitor': '{"scheme":"https"}'})
    assert response.status_code == 308
    assert response.location == 'https://hub.example.test/login?next=//attacker.invalid'


def test_custom_public_port_and_other_hosts(transport_client, monkeypatch):
    policy(monkeypatch, public='https://hub.example.test:8443')
    assert transport_client.get('/login', base_url='http://hub.example.test:8888').location == 'https://hub.example.test:8443/login'
    assert transport_client.get('/login', base_url='https://hub.example.test:8443').status_code == 200
    other = transport_client.get('/login', base_url='http://other.internal:8888')
    assert other.status_code == 200 and 'Strict-Transport-Security' not in other.headers


def test_public_cookie_cannot_inherit_domain_or_path_overrides(transport_client, monkeypatch):
    policy(monkeypatch)
    monkeypatch.setitem(hub.app.config, 'SESSION_COOKIE_DOMAIN', '.example.test')
    monkeypatch.setitem(hub.app.config, 'SESSION_COOKIE_PATH', '/custom')
    response = transport_client.get('/login', base_url='https://hub.example.test')
    cookie = next(c for c in response.headers.getlist('Set-Cookie') if c.startswith('__Host-fjordhub_session='))
    assert 'Domain=' not in cookie and 'Path=/;' in cookie and '/custom' not in cookie


@pytest.mark.parametrize('value', ['http://hub.example.test', '//hub.example.test',
    'https://user@hub.example.test', 'https://hub.example.test/path', 'https://hub.example.test?q=1',
    'https://hub.example.test#part', 'https://hub.example.test\\evil', 'https://hub.example.test\n.evil',
    'https://hub.example.test:0', 'https://hub.example.test:bad', 'https://*.example.test'])
def test_invalid_public_origin_fails_configuration(value):
    with pytest.raises(ValueError, match='FJORDHUB_PUBLIC_URL'):
        TransportPolicy.from_config(value)


def test_proxy_hostnames_are_not_silently_trusted():
    with pytest.raises(ValueError):
        TransportPolicy.from_config('https://hub.example.test', 'proxy.example.test')


def test_public_origin_normalization():
    assert TransportPolicy.from_config('https://HUB.EXAMPLE.TEST:443/').public_url == 'https://hub.example.test'
    assert TransportPolicy.from_config('https://[::1]:8443').public_url == 'https://[::1]:8443'
