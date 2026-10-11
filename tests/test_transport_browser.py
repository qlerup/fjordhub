"""Real browser cookie/redirect behavior against disposable local HTTP/TLS servers."""
from threading import Thread
from urllib.parse import urlsplit
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright
import requests
from werkzeug.serving import WSGIRequestHandler, make_server

import app as hub
from services.auth import AuthService
from services.install_state import InstallState
from services.transport_security import TransportPolicy


class QuietHandler(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


def test_browser_public_https_and_independent_lan_http(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / 'auth.db')
    auth.create_user('browser-transport', 'synthetic-password', role='user')
    monkeypatch.setattr(hub, '_auth', auth)
    monkeypatch.setattr(hub, '_install_state', InstallState(tmp_path))
    http = make_server('127.0.0.1', 0, hub.app, threaded=True, request_handler=QuietHandler)
    tls = make_server('127.0.0.1', 0, hub.app, threaded=True, request_handler=QuietHandler, ssl_context='adhoc')
    public = f'https://hub.example.test:{tls.server_port}'
    insecure_public = f'http://hub.example.test:{http.server_port}'
    lan = f'http://127.0.0.1:{http.server_port}'
    monkeypatch.setitem(hub.app.config, 'FJORDHUB_TRANSPORT_POLICY', TransportPolicy.from_config(public))
    threads = [Thread(target=server.serve_forever, daemon=True) for server in (http, tls)]
    for thread in threads:
        thread.start()
    try:
        with patch.object(requests.Session, 'request', side_effect=RuntimeError('No outbound network in test')):
            with sync_playwright() as pw:
                browser = pw.chromium.launch(args=['--host-resolver-rules=MAP hub.example.test 127.0.0.1', '--no-proxy-server'])
                # Certificate verification bypass is confined to these disposable local servers.
                context = browser.new_context(ignore_https_errors=True)
                unexpected = []
                def boundary(route):
                    if urlsplit(route.request.url).hostname in ('hub.example.test', '127.0.0.1'):
                        route.continue_()
                    else:
                        unexpected.append(route.request.url)
                        route.abort()
                context.route('**/*', boundary)
                page = context.new_page()
                http_cookies = []
                def observe(request):
                    if request.url.startswith(insecure_public + '/'):
                        http_cookies.append(request.all_headers().get('cookie', ''))
                page.on('request', observe)
                page.goto(insecure_public + '/login', wait_until='domcontentloaded')
                expect(page).to_have_url(public + '/login')
                page.locator('[name=username]').fill('browser-transport')
                page.locator('[name=password]').fill('synthetic-password')
                # Preserve a real safe return path through the normal form.
                page.locator('form').evaluate("form => form.action='/login?next=/profile'")
                page.locator('button[type=submit]').click()
                expect(page).to_have_url(public + '/profile')
                cookie = next(c for c in context.cookies() if c['name'] == '__Host-fjordhub_session')
                assert cookie['secure'] and cookie['httpOnly'] and cookie['sameSite'] == 'Lax'
                page.goto(insecure_public + '/profile', wait_until='domcontentloaded')
                expect(page).to_have_url(public + '/profile')
                assert http_cookies and all('__Host-fjordhub_session=' not in c for c in http_cookies)

                page.goto(lan + '/profile', wait_until='domcontentloaded')
                assert page.url.startswith(lan + '/login')
                page.locator('[name=username]').fill('browser-transport')
                page.locator('[name=password]').fill('synthetic-password')
                page.locator('button[type=submit]').click()
                expect(page).to_have_url(lan + '/profile')
                lan_cookie = next(c for c in context.cookies() if c['name'] == 'fjordhub_session')
                assert not lan_cookie['secure']
                page.goto(public + '/profile', wait_until='domcontentloaded')
                expect(page).to_have_url(public + '/profile')
                assert not unexpected
                browser.close()
    finally:
        for server in (http, tls):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=5)
