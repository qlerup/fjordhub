from unittest.mock import MagicMock

import pytest

import app as hub
from services.auth import AuthService
from services.install_state import InstallState
from services.password_reset import PasswordResetService


@pytest.fixture
def client(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / 'hub.db')
    mail = PasswordResetService(tmp_path / 'hub.db', 'isolated-test-secret', auth)
    monkeypatch.setattr(hub, '_auth', auth)
    monkeypatch.setattr(hub, '_password_reset', mail)
    monkeypatch.setattr(hub, '_install_state', InstallState(tmp_path))
    monkeypatch.setattr(mail, '_smtp', MagicMock())
    monkeypatch.setattr(mail, 'send_test_email', MagicMock())
    return hub.app.test_client()


def create(client):
    response = client.post('/setup', data=dict(username='owner', email='owner@example.com',
        password='temporary-pass-73', password2='temporary-pass-73'))
    assert response.status_code == 302
    assert response.location.endswith('/setup/preferences')
    assert client.get(response.location).status_code == 200
    with client.session_transaction() as session:
        return session['onboarding_csrf']


def test_create_then_skip_persists_without_mail_changes(client):
    token = create(client)
    assert client.get('/').location.endswith('/setup/preferences')
    response = client.post('/setup/preferences', data={'action': 'skip', 'csrf_token': token})
    assert response.status_code == 302 and not response.location.endswith('/setup/preferences')
    assert not hub._auth.onboarding_pending(1)
    assert hub._password_reset.mail_settings() is None
    hub._password_reset._smtp.assert_not_called()
    hub._password_reset.send_test_email.assert_not_called()
    assert not AuthService(hub._auth._db_path).onboarding_pending(1)
    assert client.get('/setup/preferences').status_code == 302


def test_test_and_save_uses_shared_mail_settings(client):
    token = create(client)
    data = dict(smtp_user='resend', smtp_password='private-test-key', smtp_host='smtp.resend.com',
                smtp_port='465', smtp_from='noreply@example.com')
    assert client.post('/settings/mail/test', json={**data, 'test_to': 'owner@example.com'}).json['ok']
    hub._password_reset.send_test_email.assert_called_once()
    response = client.post('/setup/preferences', data={**data, 'action': 'save', 'enabled': '1', 'csrf_token': token})
    assert response.status_code == 302
    assert hub._password_reset.mail_settings()['user'] == 'resend'
    assert hub._password_reset.is_enabled()
    assert not hub._auth.onboarding_pending(1)
    page = client.get('/settings').get_data(as_text=True)
    assert 'resend' in page and 'private-test-key' not in page
    assert page.count('id="mail-settings-form"') == 1


def test_failure_keeps_setup_open_and_allows_skip(client):
    token = create(client)
    hub._password_reset._smtp.side_effect = RuntimeError('sensitive upstream failure')
    response = client.post('/setup/preferences', data=dict(action='save', csrf_token=token,
        smtp_user='user', smtp_password='private-test-key', smtp_from='a@example.com'))
    assert response.status_code == 400
    assert b'sensitive upstream failure' not in response.data and b'private-test-key' not in response.data
    assert hub._auth.onboarding_pending(1)
    assert hub._password_reset.mail_settings() is None
    assert client.post('/setup/preferences', data=dict(action='skip', csrf_token=token)).status_code == 302


def test_resume_after_new_login(client):
    create(client)
    fresh = hub.app.test_client()
    assert fresh.get('/setup/preferences').status_code == 302
    response = fresh.post('/login', data={'username': 'owner', 'password': 'temporary-pass-73'})
    assert response.location.endswith('/setup/preferences')


def test_existing_users_and_new_regular_accounts_are_not_enrolled(client):
    for name, role in [('old-admin', 'admin'), ('reader', 'user')]:
        uid = hub._auth.create_user(name, 'temporary-pass', role=role)
        assert not hub._auth.onboarding_pending(uid)
        with client.session_transaction() as session:
            session['_user_id'] = str(uid)
            session['_fresh'] = True
        assert client.get('/setup/preferences').status_code == (302 if role == 'admin' else 403)


def test_csrf_and_repeated_first_setup(client):
    create(client)
    assert client.post('/setup/preferences', data={'action': 'skip'}).status_code == 403
    assert hub._auth.onboarding_pending(1)
    with pytest.raises(ValueError, match='allerede opsat'):
        hub._auth.create_user('attacker', 'temporary-pass', role='admin', first_setup=True)
    assert hub._auth.users_count() == 1
