from datetime import datetime, timezone

import pytest
from flask_login.utils import encode_cookie

import app as hub
from services.auth import AuthService
from services.install_state import InstallState


@pytest.fixture
def client(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / 'hub.db')
    auth.create_user('demo', 'test-password', role='admin')
    monkeypatch.setattr(hub, '_auth', auth)
    monkeypatch.setattr(hub, '_install_state', InstallState(tmp_path))
    return hub.app.test_client()


def login(client):
    return client.post('/login', data={'username': 'demo', 'password': 'test-password'})


def test_restart_and_fixed_expiry(client, monkeypatch):
    assert login(client).status_code == 302
    name = hub.app.config['SESSION_COOKIE_NAME']
    cookie = client.get_cookie(name)
    remaining = cookie.expires - datetime.now(timezone.utc)
    assert abs(remaining.total_seconds() - 30 * 86400) < 5
    browser = hub.app.test_client()
    browser.set_cookie(name, cookie.value)
    assert browser.get('/login').location == '/'
    with browser.session_transaction() as session:
        deadline = session['login_expires_at']
        assert session.permanent
    monkeypatch.setattr(hub.time, 'time', lambda: deadline - 60)
    with browser.session_transaction() as session:
        session['preference'] = 'changed'
    response = browser.get('/login')
    assert response.location == '/'
    assert 'Set-Cookie' not in response.headers
    monkeypatch.setattr(hub.time, 'time', lambda: deadline)
    assert browser.get('/login').status_code == 200
    assert browser.get('/api/users').status_code == 401


def test_logout(client):
    login(client)
    assert client.post('/logout').location == '/login'
    assert client.get('/login').status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' not in session
        assert 'login_expires_at' not in session
        assert not session.permanent


def test_legacy_remember_cookie_cannot_restore_login(client):
    with hub.app.app_context():
        token = encode_cookie('1')
    client.set_cookie('remember_token', token)
    assert client.get('/login').status_code == 200
    assert client.get_cookie('remember_token') is None
    assert login(client).status_code == 302
    assert client.get_cookie('remember_token') is None


def test_wrong_password_does_not_persist(client):
    client.post('/login', data={'username': 'demo', 'password': 'wrong'})
    with client.session_transaction() as session:
        assert 'login_expires_at' not in session
        assert '_user_id' not in session
