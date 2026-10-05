import unittest
from contextlib import closing
from unittest.mock import patch

import app as hub
import test_access_tokens as fixtures
from services.auth import AuthService


class AppInfoTests(unittest.TestCase):
    setUp = fixtures.AccessTokenTests.setUp
    tearDown = fixtures.AccessTokenTests.tearDown
    login = fixtures.AccessTokenTests.login
    create = fixtures.AccessTokenTests.create

    def install(self):
        root = self.auth._db_path.parent
        (root/'.env').write_text('APP_PORT=18097\nPRIVATE_PASSWORD=do-not-share\n')
        hub._install_state.register('fjordflix', str(root))

    def test_metadata_only_current_port_icon_and_no_update_permission(self):
        self.install(); self.login(self.admin)
        result = self.create(metadata_apps=['fjordflix', 'fjordhub'])
        self.assertEqual(result.status_code, 201)
        token = result.json['token']; headers = {'Authorization': 'Bearer '+token}
        external = hub.app.test_client()
        with patch.object(hub, '_host_lan_ip', return_value='192.168.1.110'):
            result = external.get('/api/integrations/v1/app-info', headers=headers)
        self.assertEqual(result.status_code, 200)
        apps = result.json['app_info']
        self.assertEqual(set(apps), {'fjordflix', 'fjordhub'})
        self.assertEqual(apps['fjordflix']['port'], 18097)
        self.assertTrue(apps['fjordflix']['icon_url'].startswith('https://'))
        self.assertEqual(apps['fjordflix']['permissions'], {'app_data': False, 'updates': False})
        self.assertEqual(apps['fjordhub']['port'], hub.APP_PORT)
        self.assertIn('192.168.1.110', apps['fjordhub']['icon_url'])
        path = apps['fjordhub']['icon_url'].split('/static/',1)[1].split('?')[0]
        self.assertTrue((hub.Path(hub.app.static_folder)/path).is_file())
        self.assertNotIn('do-not-share', result.get_data(as_text=True))
        self.assertEqual(result.headers['Cache-Control'], 'no-store')
        self.assertEqual(external.post('/api/integrations/v1/updates/fjordflix/start', headers=headers).status_code, 403)
        self.assertEqual(external.get('/api/integrations/v1/app-data/fjordflix', headers=headers).status_code, 403)
        (self.auth._db_path.parent/'.env').write_text('APP_PORT=28097\n')
        self.assertEqual(external.get('/api/integrations/v1/app-info', headers=headers).json['app_info']['fjordflix']['port'], 28097)

    def test_app_selection_union_resources_and_unselected_not_exposed(self):
        self.install()
        token = self.auth.create_access_token('Data', self.admin, apps=['fjordflix'], metadata_apps=['fjordhub'])
        headers = {'Authorization': 'Bearer '+token}
        with patch.object(hub.resource_monitor, 'collect', return_value={'ok':True}), \
             patch.object(hub, '_integration_app_payload', return_value={'ok':True}):
            result = self.client.get('/api/integrations/v1/resources', headers=headers)
        self.assertEqual(set(result.json['app_info']), {'fjordflix', 'fjordhub'})
        self.assertTrue(result.json['app_info']['fjordflix']['permissions']['app_data'])
        token = self.auth.create_access_token('Update', self.admin, update_apps=['fjordflix'])
        result = self.client.get('/api/integrations/v1/app-info', headers={'Authorization':'Bearer '+token})
        self.assertEqual(set(result.json['app_info']), {'fjordflix'})
        self.assertTrue(result.json['app_info']['fjordflix']['permissions']['updates'])

    def test_persist_edit_remove_revoke_delete_and_old_client(self):
        self.install(); self.login(self.admin)
        token = self.auth.create_access_token('Info', self.admin, metadata_apps=['fjordflix'])
        reopened = AuthService(self.auth._db_path)
        grant = reopened.access_token_grant(token)
        self.assertEqual(grant['metadata_apps'], ['fjordflix'])
        reopened.update_access_token_apps(grant['id'], [])
        self.assertEqual(reopened.access_token_grant(token)['metadata_apps'], ['fjordflix'])
        endpoint = f"/settings/access-tokens/{grant['id']}/apps"
        result = self.client.post(endpoint, json={'apps': [], 'metadata_apps': []}, headers={'X-CSRF-Token':'csrf-test'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(reopened.access_token_grant(token)['metadata_apps'], [])
        reopened.update_access_token_apps(grant['id'], [], metadata_apps=['fjordflix'])
        reopened.revoke_access_token(grant['id'])
        self.assertEqual(self.client.get('/api/integrations/v1/app-info', headers={'Authorization':'Bearer '+token}).status_code, 401)
        self.assertTrue(reopened.delete_access_token(grant['id']))
        with closing(reopened._conn()) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM access_token_metadata').fetchone()[0],0)

    def test_validation_lan_and_migration(self):
        self.login(self.admin)
        for selected in (['unknown'], ['fjordflix'], ['/etc/passwd'], 'fjordhub'):
            self.assertEqual(self.create(metadata_apps=selected).status_code,400)
        token = self.auth.create_access_token('Old', self.admin)
        with closing(self.auth._conn()) as conn:
            conn.execute('DROP TABLE access_token_metadata'); conn.commit()
        reopened = AuthService(self.auth._db_path)
        self.assertEqual(reopened.access_token_grant(token)['metadata_apps'], [])
        self.assertEqual(self.client.get('/api/integrations/v1/app-info').status_code,401)
        self.assertEqual(self.client.get('/api/integrations/v1/app-info', headers={'Authorization':'Bearer '+token}, environ_overrides={'REMOTE_ADDR':'8.8.8.8'}).status_code,403)
        self.assertEqual(self.client.get('/api/integrations/v1/app-info', headers={'Authorization':'Bearer '+token}).json['app_info'],{})


if __name__ == '__main__':
    unittest.main()
