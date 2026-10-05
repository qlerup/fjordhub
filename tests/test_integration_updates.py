import unittest
from contextlib import closing
from unittest.mock import patch

import app as hub
from services.auth import AuthService
import test_access_tokens as fixtures


class IntegrationUpdateTests(unittest.TestCase):
    setUp = fixtures.AccessTokenTests.setUp
    tearDown = fixtures.AccessTokenTests.tearDown
    login = fixtures.AccessTokenTests.login
    create = fixtures.AccessTokenTests.create

    def install(self, app_id='fjordflix'):
        hub._install_state.register(app_id, str(self.auth._db_path.parent))

    def headers(self, token):
        return {'Authorization': 'Bearer ' + token}

    def test_selection_persistence_edit_delete_and_legacy(self):
        self.install(); self.login(self.admin)
        with patch.object(hub, 'FJORDHUB_UPDATER_URL', 'http://updater'):
            result = self.create(update_apps=['fjordflix', 'fjordhub'])
        self.assertEqual(result.status_code, 201)
        token = result.json['token']
        reopened = AuthService(self.auth._db_path)
        grant = reopened.access_token_grant(token)
        self.assertEqual(grant['update_apps'], ['fjordflix', 'fjordhub'])
        self.assertEqual(grant['apps'], [])
        legacy = reopened.create_access_token('Legacy', self.admin)
        self.assertEqual(reopened.access_token_grant(legacy)['update_apps'], [])
        # Older clients editing data scopes do not silently erase update scopes.
        reopened.update_access_token_apps(grant['id'], [])
        self.assertEqual(reopened.access_token_grant(token)['update_apps'], grant['update_apps'])
        result = self.client.post(f"/settings/access-tokens/{grant['id']}/apps",
                                  headers={'X-CSRF-Token': 'csrf-test'},
                                  json={'apps': [], 'update_apps': []})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(reopened.access_token_grant(token)['update_apps'], [])
        reopened.revoke_access_token(grant['id'])
        reopened.delete_access_token(grant['id'])
        with closing(reopened._conn()) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM access_token_updates WHERE token_id=?', (grant['id'],)).fetchone()[0], 0)

    def test_selection_validation_and_management_auth(self):
        self.login(self.admin)
        for values in (['fjordflix'], ['unknown'], '../fjordflix', [True]):
            self.assertEqual(self.create(update_apps=values).status_code, 400)
        self.install()
        self.assertEqual(self.create(update_apps=['fjordflix']).status_code, 201)
        self.login(self.user)
        self.assertEqual(self.create(update_apps=['fjordflix']).status_code, 403)

    def test_old_database_migration_does_not_grant_updates(self):
        token = self.auth.create_access_token('Old data token', self.admin, apps=['fjordflix'])
        with closing(self.auth._conn()) as conn:
            conn.execute('DROP TABLE access_token_updates')
            conn.commit()
        migrated = AuthService(self.auth._db_path)
        self.assertEqual(migrated.access_token_grant(token)['apps'], ['fjordflix'])
        self.assertEqual(migrated.access_token_grant(token)['update_apps'], [])

    def test_bearer_lan_scope_and_revocation(self):
        self.install()
        token = self.auth.create_access_token('Updates', self.admin, update_apps=['fjordflix'])
        data_only = self.auth.create_access_token('Data', self.admin, apps=['fjordflix'])
        url = '/api/integrations/v1/updates/fjordflix/start'
        with patch.object(hub._update_manager, 'start_update') as start:
            self.assertEqual(self.client.post(url).status_code, 401)
            self.assertEqual(self.client.post(url, headers=self.headers(data_only)).status_code, 403)
            self.assertEqual(self.client.post(url.replace('fjordflix', 'fjordlens'), headers=self.headers(token)).status_code, 403)
            self.assertEqual(self.client.post(url, headers=self.headers(token), environ_overrides={'REMOTE_ADDR': '8.8.8.8'}).status_code, 403)
            self.auth.revoke_access_token(self.auth.access_token_grant(token)['id'])
            self.assertEqual(self.client.post(url, headers=self.headers(token)).status_code, 401)
            expired = self.auth.create_access_token('Expired', self.admin, update_apps=['fjordflix'])
            with closing(self.auth._conn()) as conn:
                conn.execute("UPDATE access_tokens SET expires_at='2000-01-01' WHERE name='Expired'")
                conn.commit()
            self.assertEqual(self.client.post(url, headers=self.headers(expired)).status_code, 401)
            start.assert_not_called()

    def test_status_check_start_and_no_sensitive_fields(self):
        self.install()
        token = self.auth.create_access_token('Updates', self.admin, update_apps=['fjordflix'])
        headers = self.headers(token)
        status = {'ok': True, 'state': 'update_available', 'update_available': True,
                  'log': ['secret'], 'dirty_lines': ['/private'], 'current_rev': 'old', 'remote_rev': 'new'}
        with patch.object(hub._update_manager, 'get_status', return_value=status), \
             patch.object(hub._update_manager, 'check_now', return_value=status) as check, \
             patch.object(hub._update_manager, 'start_update', return_value=({'ok': True, 'running': True, 'state': 'updating'}, 202)) as start:
            result = self.client.get('/api/integrations/v1/updates', headers=headers)
            self.assertEqual(set(result.json['updates']), {'fjordflix'})
            self.assertNotIn('secret', result.get_data(as_text=True))
            self.assertNotIn('/private', result.get_data(as_text=True))
            self.assertEqual(result.headers['Cache-Control'], 'no-store')
            result = self.client.post('/api/integrations/v1/updates/fjordflix/check', headers=headers)
            self.assertTrue(result.json['update_available']); check.assert_called_once()
            self.assertEqual(self.client.get('/api/integrations/v1/updates/fjordflix/start', headers=headers).status_code, 400)
            result = self.client.post('/api/integrations/v1/updates/fjordflix/start', headers=headers)
            self.assertEqual(result.status_code, 202); start.assert_called_once()
            with patch.object(hub.app_storage, 'busy', return_value=True):
                self.assertEqual(self.client.post('/api/integrations/v1/updates/fjordflix/start', headers=headers).status_code, 409)
            self.assertEqual(start.call_count, 1)
            with patch.object(hub._install_state, 'get_install_dir', return_value=None):
                self.assertEqual(self.client.post('/api/integrations/v1/updates/fjordflix/start', headers=headers).status_code, 404)

    def test_hub_proxy_and_storage_guard(self):
        token = self.auth.create_access_token('Hub', self.admin, update_apps=['fjordhub'])
        headers = self.headers(token)
        with patch.object(hub, 'FJORDHUB_UPDATER_URL', 'http://updater'), \
             patch.object(hub, '_hub_update_proxy', return_value=({'ok': True, 'state': 'updating', 'running': True}, 202)) as proxy:
            result = self.client.post('/api/integrations/v1/updates/fjordhub/start', headers=headers)
            self.assertEqual(result.status_code, 202)
            self.assertEqual(proxy.call_args.args, ('/start',))
            self.assertEqual(proxy.call_args.kwargs['payload'], {})
            with patch.object(hub._install_state, 'has_storage_jobs', return_value=True):
                self.assertEqual(self.client.post('/api/integrations/v1/updates/fjordhub/start', headers=headers).status_code, 409)
            self.assertEqual(proxy.call_count, 1)

    def test_resources_include_selected_updates(self):
        token = self.auth.create_access_token('Updates', self.admin, update_apps=['fjordhub'])
        with patch.object(hub.resource_monitor, 'collect', return_value={'ok': True}), \
             patch.object(hub, '_integration_update_status', return_value=({'ok': True, 'update_available': True}, 200)):
            result = self.client.get('/api/integrations/v1/resources', headers=self.headers(token))
            self.assertTrue(result.json['updates']['fjordhub']['update_available'])


if __name__ == '__main__':
    unittest.main()
