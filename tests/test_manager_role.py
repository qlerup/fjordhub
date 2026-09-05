import tempfile
import unittest
from pathlib import Path

from services.auth import AuthService
from services.install_state import InstallState
import app as fjordhub


class ManagerRoleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.auth = AuthService(Path(self.tempdir.name) / 'hub.db')

    def tearDown(self):
        self.tempdir.cleanup()

    def test_hub_grant_is_preserved_in_login_and_user_list(self):
        uid = self.auth.create_user('manager', 'test-password')
        self.auth.set_user_app_access(uid, 'fjordlens', 'manager')
        self.assertEqual(self.auth.get_user_app_role(uid, 'fjordlens'), 'manager')
        user = self.auth.authenticate_app_user('fjordlens', 'manager', 'test-password')
        self.assertEqual(user['role'], 'manager')
        self.assertEqual(user['hub_role'], 'user')
        self.assertEqual(self.auth.list_app_users('fjordlens')[0]['role'], 'manager')
        self.assertFalse(self.auth.get_by_id(uid).is_admin)

    def test_app_created_manager_remains_an_ordinary_hub_user(self):
        user = self.auth.create_or_grant_app_user('fjordlens', 'new-manager', 'test-password', 'manager')
        self.assertEqual((user['role'], user['hub_role']), ('manager', 'user'))
        self.assertEqual(self.auth.get_user_app_access(user['id'])[0]['role'], 'manager')
        updated = self.auth.update_app_user_role(user['id'], 'fjordlens', 'user')
        self.assertEqual(updated['role'], 'user')
        updated = self.auth.update_app_user_role(user['id'], 'fjordlens', 'manager')
        self.assertEqual(updated['role'], 'manager')

    def test_manager_is_not_a_hub_admin_role_or_a_role_for_other_apps(self):
        with self.assertRaises(ValueError):
            self.auth.create_user('invalid', 'test-password', role='manager')
        uid = self.auth.create_user('user', 'test-password')
        self.auth.set_user_app_access(uid, 'fjordshare', 'manager')
        self.assertEqual(self.auth.get_user_app_role(uid, 'fjordshare'), 'user')
        with self.assertRaises(ValueError):
            self.auth.update_app_user_role(uid, 'fjordshare', 'manager')


class ManagerEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.previous_auth, self.previous_state = fjordhub._auth, fjordhub._install_state
        fjordhub._auth = AuthService(root / 'hub.db')
        fjordhub._install_state = InstallState(root)
        fjordhub._auth.create_user('admin', 'test-password', role='admin')
        fjordhub._auth.save_hub_key('fjordlens', 'test-key')
        self.headers = {'X-Hub-Key': 'test-key'}
        self.client = fjordhub.app.test_client()

    def tearDown(self):
        fjordhub._sso_tokens.clear()
        fjordhub._auth, fjordhub._install_state = self.previous_auth, self.previous_state
        self.tempdir.cleanup()

    def test_app_api_create_update_list_and_legacy_sync_preserve_manager(self):
        response = self.client.post('/api/hub/apps/users', headers=self.headers,
                                    json={'app_id': 'fjordlens', 'username': 'app-user', 'password': 'test-password', 'role': 'manager'})
        self.assertEqual(response.status_code, 201, response.json)
        uid = response.json['user']['id']
        self.assertEqual(response.json['user']['role'], 'manager')
        for role in ('user', 'manager'):
            response = self.client.patch(f'/api/hub/apps/users/{uid}', headers=self.headers, json={'app_id': 'fjordlens', 'role': role})
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json['user']['role'], role)
        response = self.client.get('/api/hub/apps/users?app_id=fjordlens', headers=self.headers)
        self.assertEqual(response.json['items'][0]['role'], 'manager')
        response = self.client.post('/api/hub/user-sync', headers=self.headers,
                                    json={'app_id': 'fjordlens', 'username': 'app-user', 'role': 'manager'})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json['user']['role'], 'manager')

    def test_sso_keeps_manager_app_role_and_user_hub_role(self):
        uid = fjordhub._auth.create_user('manager', 'test-password')
        fjordhub._auth.set_user_app_access(uid, 'fjordlens', 'manager')
        with self.client.session_transaction() as session:
            session['_user_id'], session['_fresh'] = str(uid), True
        response = self.client.get('/api/hub/sso-token?app_id=fjordlens')
        self.assertEqual(response.status_code, 200, response.json)
        token = response.json['token']
        response = self.client.get(f'/api/hub/sso-verify?app_id=fjordlens&token={token}', headers=self.headers)
        self.assertEqual((response.json['role'], response.json['hub_role']), ('manager', 'user'))

    def test_hub_user_forms_accept_the_manager_app_role(self):
        with self.client.session_transaction() as session:
            session['_user_id'], session['_fresh'] = '1', True
        data = dict(username='form-user', password='test-password', email='manager@example.com', role='user',
                    app_access='fjordlens', app_role_fjordlens='manager')
        response = self.client.post('/users/create', data=data)
        self.assertEqual(response.status_code, 302)
        user = fjordhub._auth.get_by_username('form-user')
        self.assertIsNotNone(user)
        self.assertEqual(fjordhub._auth.get_user_app_role(user.id, 'fjordlens'), 'manager')
        for role in ('user', 'manager'):
            data['app_role_fjordlens'] = role
            response = self.client.post(f'/users/{user.id}/edit', data=data)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(fjordhub._auth.get_user_app_role(user.id, 'fjordlens'), role)


if __name__ == '__main__':
    unittest.main()
