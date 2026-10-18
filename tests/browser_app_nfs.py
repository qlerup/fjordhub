"""Real dashboard/wizard UI with synthetic NAS responses; never mounts a drive."""
import json
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlsplit
import conftest
import app as hub
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'app_registry/fjordseed.json').read_text(encoding='utf-8'))
with hub.app.test_request_context('/'), patch.object(hub, 'current_user', Mock(is_admin=True, is_authenticated=True, username='test')):
    html = hub.render_template('dashboard.html', apps=[manifest], reg_status={}, active_page='apps')
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for width in (1280, 390):
        page = browser.new_page(viewport={'width':width,'height':900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def route(route):
            path = urlsplit(route.request.url).path
            if path == '/':
                route.fulfill(body=html, content_type='text/html')
            elif path.startswith('/static/'):
                file = root / path.lstrip('/')
                route.fulfill(body=file.read_bytes(), content_type='text/css' if file.suffix=='.css' else 'application/javascript' if file.suffix=='.js' else 'image/svg+xml') if file.exists() else route.abort()
            elif path == '/api/lxc-type': route.fulfill(json={'privileged':True})
            elif path == '/api/list-nfs-exports': route.fulfill(json={'exports':['/volume1/media']})
            elif path == '/api/verify-nfs-mount': route.fulfill(json={'mounted':False})
            elif path == '/api/mount-nfs': route.fulfill(json={'ok':True,'path':'/mnt/fjordseed'})
            elif path.endswith('/settings'): route.fulfill(json={'ok':True})
            else: route.fulfill(json={})
        page.route('**/*',route)
        page.goto('http://hub.test/')
        page.evaluate("openAppSettings(document.querySelector('[data-app-id=fjordseed]'))")
        page.locator('#app-nfs-add').click()
        expect(page.locator('#nfs-modal')).to_be_visible()
        expect(page.locator('#nfs-field-label')).to_have_text('FjordSeed')
        page.locator('#nfs-server-ip').fill('192.0.2.1')
        page.locator('#nfs-fetch-btn').click()
        expect(page.locator('#nfs-export-select')).to_be_enabled()
        page.locator('#nfs-export-select').select_option('/volume1/media')
        expect(page.locator('#nfs-auto-btn')).to_be_visible()
        page.locator('#nfs-auto-btn').click()
        expect(page.locator('#nfs-done-btn')).to_be_enabled()
        page.locator('#nfs-done-btn').click()
        expect(page.locator('#nfs-modal')).to_be_hidden()
        expect(page.locator('#app-nfs-result')).to_contain_text('/mnt/fjordseed')
        page.locator('#app-nfs-add').click()
        page.keyboard.press('Escape')
        expect(page.locator('#nfs-modal')).to_be_hidden()
        assert page.locator('#app-settings-modal').evaluate("e=>e.classList.contains('is-open')")
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        page.close()
    browser.close()
print('PASS: NFS settings button, modal, connect, mount, result and Escape at desktop/mobile sizes.')
