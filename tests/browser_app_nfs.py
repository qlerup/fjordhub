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
    for width, privileged in ((1280, True), (390, True), (1280, False), (390, False)):
        mount = {'mounted':False, 'error':'Mount mangler i LXC. <img data-error-marker> Kontrollér LXC-ID.'}
        verify_status = 200
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
            elif path == '/api/lxc-type': route.fulfill(json={'privileged':privileged,'vmid':'1000'})
            elif path == '/api/list-nfs-exports': route.fulfill(json={'exports':['/volume1/media']})
            elif path == '/api/verify-nfs-mount': route.fulfill(status=verify_status,json=mount)
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
        expect(page.locator('#nfs-mount-status')).to_contain_text('Kontrollér LXC-ID')
        assert page.locator('[data-error-marker]').count() == 0
        if privileged:
            expect(page.locator('#nfs-auto-btn')).to_be_visible()
            page.locator('#nfs-auto-btn').click()
        else:
            code = page.locator('#nfs-code-block').text_content()
            assert 'ctid=\'1000\'' in code
            assert 'pct shutdown "$ctid" --timeout 60' in code
            assert 'pct start "$ctid"' in code
            assert 'pct reboot' not in code
            verify_status = 503
            page.evaluate("startMountPolling('/mnt/fjordseed')")
            expect(page.locator('#nfs-mount-status')).to_contain_text('HTTP 503')
            expect(page.locator('#nfs-done-btn')).to_be_disabled()
            verify_status = 200
            mount = {'mounted':True,'fstype':'nfs'}
            page.evaluate("startMountPolling('/mnt/fjordseed')")
        expect(page.locator('#nfs-done-btn')).to_be_enabled()
        expect(page.locator('#nfs-mount-status')).to_contain_text('NFS mount bekræftet')
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
