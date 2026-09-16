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

    def test_create_and_revoke(self):
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
        self.assertTrue(self.auth.authenticate_access_token(token))
        self.assertIsNotNone(self.auth.list_access_tokens()[0]['last_used_at'])
        self.assertEqual(external.get('/api/resources', headers=headers).status_code, 401)
        self.assertEqual(external.get('/api/hub/apps/users?app_id=demo', headers={
            'X-Hub-Key': token}).status_code, 401)
        self.assertEqual(external.post('/api/integrations/v1/apps', headers=headers).status_code, 401)
        response = self.client.post(f"/settings/access-tokens/{row['id']}/revoke",
                                    headers={'X-CSRF-Token': 'csrf-test'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.auth.authenticate_access_token(token))

    def test_catalog_endpoint_removed(self):
        self.assertNotIn('/api/integrations/v1/apps',
                         {rule.rule for rule in fjordhub.app.url_map.iter_rules()})
        token = self.auth.create_access_token('Unused', self.admin)
        for user in (None, self.admin):
            if user:
                self.login(user)
            response = self.client.get('/api/integrations/v1/apps',
                headers={'Authorization': 'Bearer ' + token})
            self.assertIn(response.status_code, (401, 404))
        self.assertIsNone(self.auth.list_access_tokens()[0]['last_used_at'])
        page = self.client.get('/settings?section=tokens').get_data(as_text=True)
        self.assertNotIn('/api/integrations/v1/apps', page)
        self.assertIn('/api/integrations/v1/resources', page)

    def test_resource_read_projection(self):
        token = self.auth.create_access_token('Monitor', self.admin, days=0)
        container = {'id': 'container-id', 'name': 'demo', 'status': 'running',
                     'cpu_percent': 12.5, 'memory_usage': 1024, 'memory_limit': 4096,
                     'net_rx': 100, 'net_tx': 200, 'block_read': 300, 'block_write': 400,
                     'environment': 'secret', 'mounts': ['/private'], 'error': None}
        group = {'id': 'demo', 'name': 'Demo', 'container_count': 1, 'running_count': 1,
                 'cpu_percent': 12.5, 'memory_usage': 1024, 'net_rx': 100,
                 'containers': [container], 'icon_url': 'private', 'description': 'hidden'}
        snapshot = {'ok': True, 'generated_at': '2026-09-16T12:00:00+00:00',
                    'capacity': {'cpus': 4, 'memory_total': 4096, 'secret': 'private'},
                    'hub': group, 'core': group, 'apps': [group],
                    'system': {'secret': 'private'}, 'overhead': {'secret': 'private'}}
        with patch.object(fjordhub, '_apps_with_install_dirs', return_value=['apps']) as apps, \
                patch.object(fjordhub.resource_monitor, 'collect', return_value=snapshot) as collect:
            response = self.client.get('/api/integrations/v1/resources',
                headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        collect.assert_called_once_with(['apps'])
        apps.assert_called_once()
        self.assertEqual(set(response.json), {'ok', 'generated_at', 'capacity', 'hub', 'core', 'apps', 'hub_url'})
        self.assertEqual(response.json['apps'][0]['cpu_percent'], 12.5)
        self.assertEqual(response.json['apps'][0]['containers'][0]['block_write'], 400)
        for hidden in ('secret', 'private', 'environment', 'mounts', 'icon_url', 'description'):
            self.assertNotIn(hidden, response.get_data(as_text=True))
        self.assertIsNotNone(self.auth.list_access_tokens()[0]['last_used_at'])

    def test_resource_access_requires_valid_token_and_lan(self):
        token = self.auth.create_access_token('Monitor', self.admin)
        headers = {'Authorization': 'Bearer ' + token}
        endpoint = '/api/integrations/v1/resources'
        self.login(self.admin)
        with patch.object(fjordhub.resource_monitor, 'collect') as collect:
            for supplied in ({}, {'Authorization': 'Bearer invalid'},
                             {'Authorization': 'Basic ' + token}):
                response = self.client.get(endpoint, headers=supplied)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers['WWW-Authenticate'], 'Bearer')
            self.assertEqual(self.client.get(endpoint + '?token=' + token).status_code, 401)
            for address, extra in [('8.8.8.8', {}), ('172.18.0.2', {'X-Forwarded-For': '8.8.8.8'}),
                                   ('127.0.0.1', {'X-Forwarded-For': 'unknown'}),
                                   ('127.0.0.1', {'Forwarded': 'for=192.168.1.2'})]:
                response = self.client.get(endpoint, headers={**headers, **extra},
                    environ_overrides={'REMOTE_ADDR': address})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertEqual(self.client.post(endpoint, headers=headers).status_code, 405)
            self.auth.revoke_access_token(self.auth.list_access_tokens()[0]['id'])
            self.assertEqual(self.client.get(endpoint, headers=headers).status_code, 401)
            expired = self.auth.create_access_token('Expired', self.admin)
            with closing(self.auth._conn()) as conn:
                conn.execute("UPDATE access_tokens SET expires_at='2000-01-01'")
                conn.commit()
            self.assertEqual(self.client.get(endpoint, headers={
                'Authorization': 'Bearer ' + expired}).status_code, 401)
            collect.assert_not_called()

    def test_resource_failures_hide_internal_details(self):
        token = self.auth.create_access_token('Monitor', self.admin)
        with patch.object(fjordhub, '_apps_with_install_dirs', return_value=[]), \
                patch.object(fjordhub.resource_monitor, 'collect', return_value={
                    'ok': False, 'error': 'secret Docker connection string'}) as collect:
            response = self.client.get('/api/integrations/v1/resources',
                headers={'Authorization': 'Bearer ' + token})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('secret', response.get_data(as_text=True))
            collect.side_effect = RuntimeError('secret connection')
            with patch.object(fjordhub.app.logger, 'exception'):
                response = self.client.get('/api/integrations/v1/resources',
                    headers={'Authorization': 'Bearer ' + token})
            self.assertEqual(response.status_code, 503)
            self.assertFalse(response.json['ok'])
            self.assertEqual(response.json['error'], 'Docker metrics unavailable')
            self.assertIn('hub_url', response.json)

    def test_resource_hub_url_uses_lan_ip_and_published_port(self):
        token = self.auth.create_access_token('Open hub', self.admin)
        with patch.object(fjordhub, '_apps_with_install_dirs', return_value=[]), \
                patch.object(fjordhub.resource_monitor, 'collect', return_value={'ok': True}), \
                patch.object(fjordhub, 'APP_PORT', 8091):
            for address, expected in [
                ('192.168.1.10', 'http://192.168.1.10:8091/'),
                ('fd12::42', 'http://[fd12::42]:8091/'),
                ('', 'http://hub.local:8888/'),
            ]:
                with self.subTest(address=address), patch.object(fjordhub, '_host_lan_ip', return_value=address):
                    response = self.client.get('/api/integrations/v1/resources',
                        base_url='http://hub.local:8888',
                        headers={'Authorization': 'Bearer ' + token})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json['hub_url'], expected)
                    self.assertNotIn(token, response.json['hub_url'])

    def test_permissions_csrf_and_validation(self):
        self.assertEqual(self.create().status_code, 302)
        self.login(self.user)
        self.assertEqual(self.create().status_code, 403)
        self.login(self.admin)
        self.assertEqual(self.client.post('/settings/access-tokens', json={}).status_code, 403)
        for invalid in ({'name': ''}, {'name': 'a' * 81}, {'days': -1}, {'days': 1},
                        {'days': '90'}, {'days': None}, {'days': False}):
            self.assertEqual(self.create(**invalid).status_code, 400)
        self.assertEqual(self.auth.list_access_tokens(), [])

    def test_no_expiry_persists_and_can_be_revoked(self):
        self.login(self.admin)
        response = self.create(days=0)
        self.assertEqual(response.status_code, 201)
        token = response.json['token']
        reopened = AuthService(self.auth._db_path)
        row = reopened.list_access_tokens()[0]
        self.assertEqual(row['expires_at'], '')
        self.assertEqual(row['status'], 'Aktivt')
        page = self.client.get('/settings?section=tokens')
        self.assertEqual(page.status_code, 200)
        self.assertIn('· Udløber aldrig', page.get_data(as_text=True))
        from datetime import datetime, timezone
        with patch('services.auth.datetime') as clock:
            clock.now.return_value = datetime(2200, 1, 1, tzinfo=timezone.utc)
            self.assertTrue(reopened.authenticate_access_token(token))
            self.assertEqual(reopened.list_access_tokens()[0]['status'], 'Aktivt')
        external = fjordhub.app.test_client()
        headers = {'Authorization': 'Bearer ' + token}
        self.assertTrue(reopened.authenticate_access_token(token))
        response = self.client.post(f"/settings/access-tokens/{row['id']}/revoke",
                                    headers={'X-CSRF-Token': 'csrf-test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reopened.list_access_tokens()[0]['status'], 'Tilbagekaldt')
        self.assertFalse(self.auth.authenticate_access_token(token))

    def test_no_expiry_still_requires_active_admin_owner(self):
        token = self.auth.create_access_token('Permanent', self.admin, days=0)
        for role, password_change in [('user', 0), ('admin', 1), ('admin', 0)]:
            with self.subTest(role=role, password_change=password_change):
                with closing(self.auth._conn()) as conn:
                    conn.execute('UPDATE users SET role=?, must_change_password=? WHERE id=?',
                                 (role, password_change, self.admin))
                    conn.commit()
                active = role == 'admin' and not password_change
                self.assertEqual(self.auth.authenticate_access_token(token), active)
                self.assertEqual(self.auth.list_access_tokens()[0]['status'], 'Aktivt' if active else 'Inaktiv')
        self.auth.delete_user(self.admin)
        self.assertFalse(self.auth.authenticate_access_token(token))

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
