"""Self-contained first-run browser check; no live email or user data is used."""
import os
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
workspace = tempfile.TemporaryDirectory(prefix='fjordhub-onboarding-browser-')
os.environ['DATA_DIR'] = workspace.name
os.environ['SECRET_KEY'] = 'isolated-browser-test-secret'

import app as hub
hub.HostStorage.inventory = lambda self: {"available": False, "pools": []}

server = make_server('127.0.0.1', 0, hub.app, threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}'
out = Path(__file__).resolve().parents[1] / 'test-results'
out.mkdir(exist_ok=True)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1050})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base + '/setup')
        for field, value in {'username': 'UI Admin', 'email': 'qa@example.com',
                             'password': 'Temporary-onboarding-73!', 'password2': 'Temporary-onboarding-73!'}.items():
            page.locator('#' + field).fill(value)
        page.locator('button[type=submit]').click()
        expect(page).to_have_url(base + '/setup/preferences')
        expect(page.get_by_role('heading', name='Gør FjordHub klar')).to_be_visible()
        page.screenshot(path=str(out / 'onboarding-choice.png'))
        page.locator('summary').click()
        for field, value in {'smtp_from': 'noreply@example.com', 'smtp_user': 'resend',
                             'smtp_password': 'qa-placeholder', 'smtp_host': 'smtp.resend.com'}.items():
            page.locator('#' + field).fill(value)
        page.screenshot(path=str(out / 'onboarding-desktop.png'), full_page=True)
        for width in (320, 760, 390):
            page.set_viewport_size({'width': width, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        page.screenshot(path=str(out / 'onboarding-mobile.png'), full_page=True)
        page.get_by_role('button', name='Test og gem', exact=True).click()
        expect(page.get_by_role('dialog')).to_be_visible()
        page.keyboard.press('Escape')
        expect(page.get_by_role('dialog')).not_to_be_visible()
        page.get_by_role('button', name='Test og gem', exact=True).click()
        page.locator('#mail-test-to').fill('qa@example.com')
        page.route('**/settings/mail/test', lambda route: route.fulfill(
            status=400, json={'ok': False, 'error': 'Testforbindelsen fejlede'}))
        page.locator('#mail-test-send').click()
        expect(page.locator('#mail-test-error')).to_have_text('Testforbindelsen fejlede')
        expect(page.locator('#mail-test-confirm')).not_to_be_visible()
        page.unroute('**/settings/mail/test')
        page.route('**/settings/mail/test', lambda route: route.fulfill(json={'ok': True}))
        page.locator('#mail-test-send').click()
        expect(page.locator('#mail-test-confirm')).to_be_visible()
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Spring over').click()
        expect(page.get_by_role('heading', name='Lageradgang til dine apps')).to_be_visible()
        page.screenshot(path=str(out / 'storage-onboarding-mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.reload()
        expect(page.get_by_role('heading', name='Lageradgang til dine apps')).to_be_visible()
        page.get_by_role('button', name='Spring over', exact=True).click()
        expect(page).not_to_have_url(base + '/setup/preferences')
        page.goto(base + '/setup/preferences')
        expect(page).not_to_have_url(base + '/setup/preferences')
        page.goto(base + '/settings')
        expect(page.locator('#mail-settings-form')).to_be_visible()
        # Both screens use the same native test dialog and form behavior.
        for field, value in {'smtp_from': 'noreply@example.com', 'smtp_user': 'resend',
                             'smtp_password': 'qa-placeholder'}.items():
            page.locator('#' + field).fill(value)
        page.get_by_role('button', name='Test og gem', exact=True).click()
        expect(page.get_by_role('dialog')).to_be_visible()
        page.keyboard.press('Escape')
        assert not errors, errors
        browser.close()
    print('PASS: registration, optional guide, desktop/mobile, mocked mail test, keyboard, saved skip, existing settings')
finally:
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    workspace.cleanup()
