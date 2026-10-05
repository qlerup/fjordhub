"""All app-card local links use SSO while keeping the local destination."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
import app as hub
from services.auth import AuthService
from services.install_state import InstallState


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    auth = AuthService(root / 'auth.db')
    uid = auth.create_user('Local Link Admin', 'Temporary-local-link-73!', role='admin')
    state = InstallState(root)
    app_ids = ('fjordlens', 'fjordshare', 'fjordparcel', 'orbitmap',
               'urban-explorer', 'fjordflix', 'fjordbudget', 'fjordvpn')
    apps = [json.loads((Path(__file__).parents[1] / 'app_registry' / f'{app_id}.json').read_text(encoding='utf-8')) for app_id in app_ids]
    statuses = {}
    for i, app_def in enumerate(apps):
        app_id = app_def['id']
        directory = root / app_id
        directory.mkdir()
        port = 12000 + i
        (directory / '.env').write_text(f'APP_PORT={port}\n', encoding='utf-8')
        state.register(app_id, str(directory))
        state.set_external_url(app_id, f'https://{app_id}.example.test')
        auth.save_hub_key(app_id, 'test-key-' + app_id)
        statuses[app_id] = {'state':'running', 'external_url':state.get_external_url(app_id),
                           'fallback_url': f'http://10.10.0.50:{port}'}
    client = hub.app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(uid)
        session['_fresh'] = True
    with patch.object(hub, '_auth', auth), patch.object(hub, '_install_state', state), \
         patch.object(hub, '_get_apps', return_value=apps), \
         patch.dict(os.environ, {'HOST_LAN_IP':'10.10.0.50'}), sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        errors, requests, destinations = [], [], []
        def route(route):
            req = route.request
            parsed = urlsplit(req.url)
            if parsed.path == '/hub-login':
                if parsed.hostname == '10.10.0.50':
                    app_id = app_ids[parsed.port - 12000]
                else:
                    app_id = parsed.hostname.split('.')[0]
                token = parse_qs(parsed.query)['token'][0]
                result = client.get('/api/hub/sso-verify', query_string={'app_id':app_id, 'token':token},
                                    headers={'X-Hub-Key':'test-key-' + app_id})
                assert result.status_code == 200 and result.json['id'] == uid
                destinations.append((app_id, parsed.scheme, parsed.hostname, parsed.port))
                route.fulfill(content_type='text/html', body='<h1>Logged in via FjordHub</h1>')
                return
            if parsed.hostname != 'hub.test':
                route.abort(); return
            if parsed.path == '/api/apps-status':
                route.fulfill(json=statuses); return
            if parsed.path in ('/api/apps-updates', '/api/health'):
                route.fulfill(json={}); return
            if parsed.path.endswith('/sso-url'):
                requests.append((parsed.path, parsed.query))
            response = client.open(parsed.path + ('?' + parsed.query if parsed.query else ''),
                                   method=req.method, data=req.post_data, headers=req.headers)
            route.fulfill(status=response.status_code, body=response.data,
                          headers={'Content-Type':response.content_type})
        context.route('**/*', route)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://hub.test/')
        for i, app_id in enumerate(app_ids):
            with context.expect_page() as opened:
                page.locator(f'#card-{app_id} .card-local-address svg').click()
            popup = opened.value
            expect(popup.get_by_role('heading')).to_have_text('Logged in via FjordHub')
            assert requests[-1] == (f'/apps/{app_id}/sso-url', 'target=local')
            assert destinations[-1] == (app_id, 'http', '10.10.0.50', 12000+i)
            popup.close()
        with context.expect_page() as opened:
            page.locator('#card-fjordlens .btn-open').click()
        popup = opened.value
        expect(popup.get_by_role('heading')).to_have_text('Logged in via FjordHub')
        assert requests[-1] == ('/apps/fjordlens/sso-url', '')
        assert destinations[-1] == ('fjordlens', 'https', 'fjordlens.example.test', None)
        assert not errors, errors
        browser.close()
print('Local SSO for all eight apps and normal public Open destination passed.')
