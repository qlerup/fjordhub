from unittest.mock import patch
import unittest
import json
from unittest.mock import MagicMock

import test_access_tokens as fixtures
import app as hub
from services.auth import AuthService
from services import app_integration


class AppIntegrationTests(unittest.TestCase):
    setUp = fixtures.AccessTokenTests.setUp
    tearDown = fixtures.AccessTokenTests.tearDown
    login = fixtures.AccessTokenTests.login
    create = fixtures.AccessTokenTests.create
    def installed(self):
        self.root = self.auth._db_path.parent
        self.root.joinpath('.env').write_text('FJORDHUB_API_KEY=internal-secret\nAPP_PORT=8097\n', encoding='utf-8')
        hub._install_state.register('fjordflix', str(self.root))
        self.auth.save_hub_key('fjordflix', 'internal-secret')

    def test_scopes_persist_edit_and_revoke(self):
        self.installed(); self.login(self.admin)
        response = self.create(apps=['fjordflix'])
        self.assertEqual(response.status_code, 201)
        token = response.json['token']
        reopened = AuthService(self.auth._db_path)
        grant = reopened.access_token_grant(token)
        self.assertEqual(grant['apps'], ['fjordflix'])
        self.assertEqual(reopened.list_access_tokens()[0]['apps'], ['fjordflix'])
        response = self.client.post(f"/settings/access-tokens/{grant['id']}/apps", json={'apps': []}, headers={'X-CSRF-Token': 'csrf-test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reopened.access_token_grant(token)['apps'], [])
        self.auth.revoke_access_token(grant['id'])
        self.assertIsNone(reopened.access_token_grant(token))

    def test_validate_scopes_management(self):
        self.login(self.admin)
        for apps in (['unknown'], ['fjordflix'], 'fjordflix', [False], {}):
            self.assertEqual(self.create(apps=apps).status_code, 400)
        self.installed()
        token = self.auth.create_access_token('data', self.admin)
        token_id = self.auth.access_token_grant(token)['id']
        endpoint = f'/settings/access-tokens/{token_id}/apps'
        self.assertEqual(self.client.post(endpoint, json={'apps': ['fjordflix']}).status_code, 403)
        self.login(self.user)
        self.assertEqual(self.client.post(endpoint, json={'apps': ['fjordflix']}, headers={'X-CSRF-Token':'csrf-test'}).status_code, 403)

    def test_resources_include_only_opted_in_data_and_fail_independently(self):
        self.installed()
        token = self.auth.create_access_token('data', self.admin, apps=['fjordflix'])
        data = {'ok': True, 'items': [{'id': 'a'*32, 'title': 'Film'}],
                'streams': [{'id':'playback', 'movie_id':'b'*32, 'user':'Anna'}]}
        with patch.object(hub.resource_monitor, 'collect', return_value={'ok':True}), \
             patch.object(hub.app_integration, 'fetch', return_value=data) as fetch:
            response = self.client.get('/api/integrations/v1/resources', headers={'Authorization':'Bearer '+token})
            self.assertEqual(response.status_code, 200)
            self.assertIn('/app-data/fjordflix/posters/' + 'a'*32, response.json['app_data']['fjordflix']['items'][0]['poster_url'])
            self.assertIn('/posters/' + 'b'*32, response.json['app_data']['fjordflix']['streams'][0]['poster_url'])
            self.assertNotIn('internal-secret', response.get_data(as_text=True))
            fetch.assert_called_once()
        with patch.object(hub.resource_monitor, 'collect', return_value={'ok':True}), \
             patch.object(hub.app_integration, 'fetch', side_effect=app_integration.AppDataError('Unavailable')):
            response = self.client.get('/api/integrations/v1/resources', headers={'Authorization':'Bearer '+token})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json['app_data']['fjordflix']['ok'])

    def test_data_and_posters_require_token_scope_and_lan(self):
        self.installed()
        scoped = self.auth.create_access_token('data', self.admin, apps=['fjordflix'])
        unscoped = self.auth.create_access_token('resources', self.admin)
        for endpoint in ('/api/integrations/v1/app-data/fjordflix',
                         '/api/integrations/v1/app-data/fjordflix/posters/' + 'a'*32):
            with patch.object(hub.app_integration, 'fetch') as fetch:
                self.assertEqual(self.client.get(endpoint).status_code, 401)
                self.assertEqual(self.client.get(endpoint, headers={'Authorization':'Bearer '+unscoped}).status_code, 403)
                self.assertEqual(self.client.get(endpoint, headers={'Authorization':'Bearer '+scoped}, environ_base={'REMOTE_ADDR':'8.8.8.8'}).status_code, 403)
                fetch.assert_not_called()
        endpoint = '/api/integrations/v1/app-data/fjordflix/posters/' + 'a'*32
        with patch.object(hub.app_integration, 'fetch', return_value=b'jpeg'):
            response = self.client.get(endpoint, headers={'Authorization':'Bearer '+scoped})
            self.assertEqual(response.data, b'jpeg')
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.auth.update_access_token_apps(self.auth.access_token_grant(scoped)['id'], [])
        self.assertEqual(self.client.get(endpoint, headers={'Authorization':'Bearer '+scoped}).status_code, 403)


class AppDataFetchTests(unittest.TestCase):
    def response(self, status=200, content=None, content_type='application/json'):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = status
        response.headers = {'Content-Type': content_type}
        response.iter_content.return_value = [content or json.dumps({
            'ok': True, 'items': [{'id':'a'*32, 'title':'Film', 'path':'/private'}],
            'streams': [], 'secret':'hidden'}).encode()]
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = response
        return client

    def test_projection_auth_timeout_and_no_redirects(self):
        client = self.response()
        with patch.object(app_integration.requests, 'Session', return_value=client):
            data = app_integration.fetch('http://local:8097', 'internal-secret')
        self.assertNotIn('path', str(data))
        self.assertNotIn('hidden', str(data))
        self.assertFalse(client.trust_env)
        kwargs = client.get.call_args.kwargs
        self.assertFalse(kwargs['allow_redirects'])
        self.assertEqual(kwargs['timeout'], (2, 5))
        self.assertEqual(kwargs['headers'], {'X-Hub-Key':'internal-secret'})

    def test_unavailable_redirect_malformed_oversize_and_missing_poster(self):
        for client in (self.response(status=302), self.response(status=404),
                       self.response(content=b'not-json'),
                       self.response(content=b'x' * (app_integration.MAX_JSON_BYTES+1))):
            with patch.object(app_integration.requests, 'Session', return_value=client):
                with self.assertRaises(app_integration.AppDataError):
                    app_integration.fetch('http://local', 'key')
        with patch.object(app_integration.requests, 'Session') as session:
            with self.assertRaises(app_integration.AppDataError) as exc:
                app_integration.fetch('http://local', 'key', '../secret')
            self.assertEqual(exc.exception.status, 404)
            session.assert_not_called()
        with patch.object(app_integration.requests, 'Session', return_value=self.response(content_type='text/html')):
            with self.assertRaises(app_integration.AppDataError):
                app_integration.fetch('http://local', 'key', 'a'*32)
