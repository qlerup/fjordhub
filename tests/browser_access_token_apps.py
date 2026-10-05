"""Exercise token app selection against isolated Flask state in Chromium."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
import app as hub
from services.auth import AuthService
from services.install_state import InstallState


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    auth = AuthService(root / 'auth.db')
    admin = auth.create_user('Token Admin', 'Temporary-token-test-73!', role='admin')
    state = InstallState(root)
    state.register('fjordflix', str(root))
    client = hub.app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(admin)
        session['_fresh'] = True
    with patch.object(hub, '_auth', auth), patch.object(hub, '_install_state', state), sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1280, 'height':960})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def route(route):
            req = route.request
            parsed = urlsplit(req.url)
            if parsed.hostname != 'hub.test':
                route.abort(); return
            response = client.open(parsed.path + ('?' + parsed.query if parsed.query else ''),
                method=req.method, data=req.post_data, headers=req.headers)
            route.fulfill(status=response.status_code, body=response.data,
                          headers={k:v for k,v in response.headers if k.lower() != 'content-length'})
        page.route('**/*', route)
        page.goto('http://hub.test/settings?section=tokens')
        page.locator('#token-name').fill('Min anden app æøå')
        page.locator('#access-token-form input[name="apps"]').check()
        page.locator('#access-token-form button[type="submit"]').click()
        expect(page.locator('#token-created')).to_be_visible()
        assert auth.list_access_tokens()[0]['apps'] == ['fjordflix']
        assert page.locator('#token-secret').input_value().startswith('fh_at_')
        page.goto('http://hub.test/settings?section=tokens')
        page.get_by_text('Rediger adgang til appdata', exact=True).click()
        page.locator('.token-app-form input[name="apps"]').uncheck()
        page.locator('.token-app-form button[type="submit"]').click()
        expect(page.get_by_text('Ekstra appdata: Ingen — kun Docker-forbrug', exact=True)).to_be_visible()
        assert auth.list_access_tokens()[0]['apps'] == []
        page.set_viewport_size({'width':390, 'height':844})
        page.goto('http://hub.test/settings?section=tokens')
        page.screenshot(path=str(Path(__file__).parents[2] / '.codex-investigation/token-apps-mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), page.evaluate("Array.from(document.querySelectorAll('*')).filter(x=>x.getBoundingClientRect().right>window.innerWidth).map(x=>[x.tagName,x.className,x.getBoundingClientRect().right]).slice(0,20)")
        page.set_viewport_size({'width':1280, 'height':960})
        page.screenshot(path=str(Path(__file__).parents[2] / '.codex-investigation/token-apps-desktop.png'), full_page=True)
        page.on('dialog', lambda dialog: dialog.accept())
        action = page.locator('.token-action')
        expect(action).to_have_text('Tilbagekald')
        action.click()
        expect(action).to_have_text('Slet')
        expect(action).to_have_class('btn btn-open token-action token-action-delete')
        assert auth.list_access_tokens()[0]['revoked_at']
        expect(page.locator('.token-app-form')).to_have_count(0)
        page.reload()
        expect(action).to_have_text('Slet')
        action.click()
        expect(page.locator('.token-row')).to_have_count(0)
        expect(page.locator('#token-list-empty')).to_be_visible()
        assert auth.list_access_tokens() == []
        page.reload()
        expect(page.locator('.token-row')).to_have_count(0)
        expect(page.locator('#token-list-empty')).to_be_visible()
        assert not errors, errors
        browser.close()
print('Token creation, app scopes, revoke/delete, reload persistence and mobile layout passed.')
