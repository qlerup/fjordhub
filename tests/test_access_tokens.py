import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import app as fjordhub
from services.auth import AuthService
from services.install_state import InstallState


class AccessTokenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.auth = AuthService(root / 'hub.db')
        self.admin = self.auth.create_user('admin', 'password', role='admin')
        self.user = self.auth.create_user('reader', 'password')
        self.patches = [
            patch.object(fjordhub, '_auth', self.auth),
            patch.object(fjordhub, '_install_state', InstallState(root)),
            patch.object(fjordhub, '_get_apps', return_value=[{
                'id': 'demo', 'name': 'Demo', 'description': 'An app',
                'secret': 'never expose', 'setup_steps': [{'password': 'secret'}],
            }]),
        ]
        for patcher in self.patches:
            patcher.start()
        self.client = fjordhub.app.test_client()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp.cleanup()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
            session['access_token_csrf'] = 'csrf-test'

    def create(self, **overrides):
        return self.client.post('/settings/access-tokens',
                                headers={'X-CSRF-Token': 'csrf-test'},
                                json={'name': 'Other app', 'days': 90, **overrides})

    def test_create_read_and_revoke(self):
        self.login(self.admin)
        response = self.create()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        token = response.json['token']
        with closing(self.auth._conn()) as conn:
            row = dict(conn.execute('SELECT * FROM access_tokens').fetchone())
        self.assertNotIn(token, str(row))
        self.assertEqual(len(row['token_hash']), 64)
        page = self.client.get('/settings?section=tokens')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(token.encode(), page.data)
        external = fjordhub.app.test_client()
        headers = {'Authorization': 'Bearer ' + token}
        response = external.get('/api/integrations/v1/apps', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'items': [
            {'id': 'demo', 'name': 'Demo', 'description': 'An app'}]})
        self.assertIsNotNone(self.auth.list_access_tokens()[0]['last_used_at'])
        self.assertEqual(external.get('/api/resources', headers=headers).status_code, 401)
        self.assertEqual(external.get('/api/hub/apps/users?app_id=demo', headers={
            'X-Hub-Key': token}).status_code, 401)
        self.assertEqual(external.post('/api/integrations/v1/apps', headers=headers).status_code, 401)
        response = self.client.post(f"/settings/access-tokens/{row['id']}/revoke",
                                    headers={'X-CSRF-Token': 'csrf-test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(external.get('/api/integrations/v1/apps', headers=headers).status_code, 401)

    def test_permissions_csrf_and_validation(self):
        self.assertEqual(self.create().status_code, 302)
        self.login(self.user)
        self.assertEqual(self.create().status_code, 403)
        self.login(self.admin)
        self.assertEqual(self.client.post('/settings/access-tokens', json={}).status_code, 403)
        for invalid in ({'name': ''}, {'name': 'a' * 81}, {'days': 0}, {'days': '90'}):
            self.assertEqual(self.create(**invalid).status_code, 400)
        self.assertEqual(self.auth.list_access_tokens(), [])
        self.assertEqual(self.client.get('/api/integrations/v1/apps').status_code, 401)
        self.assertEqual(self.client.get('/api/integrations/v1/apps?token=invalid').status_code, 401)

    def test_lan_and_pve_clients_with_direct_and_proxied_requests(self):
        token = self.auth.create_access_token('PVE app', self.admin)
        headers = {'Authorization': 'Bearer ' + token}
        for address in ('127.0.0.1', '192.168.1.42', '10.10.0.5', '172.18.0.3',
                        '::1', 'fd12::42', '::ffff:192.168.1.42'):
            with self.subTest(address=address):
                response = self.client.get('/api/integrations/v1/apps', headers=headers,
                                           environ_overrides={'REMOTE_ADDR': address})
                self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/integrations/v1/apps', headers={
            **headers, 'X-Forwarded-For': '192.168.1.42, 172.18.0.2',
            'X-Real-IP': '192.168.1.42',
        }, environ_overrides={'REMOTE_ADDR': '172.18.0.3'})
        self.assertEqual(response.status_code, 200)

    def test_public_clients_and_spoofed_or_invalid_proxy_headers_are_denied(self):
        token = self.auth.create_access_token('Local only', self.admin)
        headers = {'Authorization': 'Bearer ' + token}
        cases = [
            ('8.8.8.8', {}),
            ('2606:4700::1111', {}),
            ('::ffff:8.8.8.8', {}),
            ('8.8.8.8', {'X-Forwarded-For': '192.168.1.42'}),
            ('172.18.0.2', {'X-Forwarded-For': '8.8.8.8'}),
            ('172.18.0.2', {'X-Forwarded-For': '192.168.1.42, 8.8.8.8'}),
            ('172.18.0.2', {'X-Real-IP': '8.8.8.8'}),
            ('172.18.0.2', {'X-Forwarded-For': ''}),
            ('172.18.0.2', {'X-Forwarded-For': 'unknown'}),
            ('172.18.0.2', {'Forwarded': 'for=8.8.8.8'}),
            ('', {}),
            ('100.64.0.1', {}),
        ]
        for address, forwarded in cases:
            with self.subTest(address=address, forwarded=forwarded):
                response = self.client.get('/api/integrations/v1/apps',
                    headers={**headers, **forwarded}, environ_overrides={'REMOTE_ADDR': address})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertIsNone(self.auth.list_access_tokens()[0]['last_used_at'])

    def test_expiry_owner_removal_and_persistence(self):
        token = self.auth.create_access_token('External', self.admin)
        reopened = AuthService(self.auth._db_path)
        self.assertTrue(reopened.authenticate_access_token(token))
        self.assertFalse(reopened.authenticate_access_token(token + 'x'))
        with closing(self.auth._conn()) as conn:
            conn.execute("UPDATE access_tokens SET expires_at='2000-01-01T00:00:00+00:00'")
            conn.commit()
        self.assertFalse(reopened.authenticate_access_token(token))
        token = self.auth.create_access_token('New', self.admin)
        with closing(self.auth._conn()) as conn:
            conn.execute("UPDATE users SET role='user' WHERE id=?", (self.admin,))
            conn.commit()
        self.assertFalse(reopened.authenticate_access_token(token))
        self.auth.delete_user(self.admin)
        self.assertFalse(reopened.authenticate_access_token(token))


if __name__ == '__main__':
    unittest.main()
