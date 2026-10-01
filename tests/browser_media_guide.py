"""Browser UI checks using isolated Flask state and mocked Docker jobs."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
import app as hub
from services.auth import AuthService
from services.install_state import InstallState

with tempfile.TemporaryDirectory() as tmp:
    auth=AuthService(Path(tmp)/'auth.db')
    auth.create_user('Guide Admin','Temporary-guide-73!',role='admin')
    state=InstallState(Path(tmp));state.set_external_url('fjordflix','https://film.example.com')
    manifest=json.loads((Path(__file__).parents[1]/'app_registry/fjordflix.json').read_text(encoding='utf-8'))
    gateway=MagicMock();gateway.status.return_value={}
    client=hub.app.test_client()
    with patch.object(hub,'_auth',auth),patch.object(hub,'_install_state',state),patch.object(hub,'media_gateway',gateway),patch.object(hub,'_get_apps',return_value=[manifest]),patch.object(hub,'_nfs_runtime_info',return_value={}),sync_playwright() as pw:
        client.post('/login',data={'username':'Guide Admin','password':'Temporary-guide-73!'})
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1280,'height':960})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def route(request):
            parsed=urlsplit(request.request.url)
            if parsed.hostname!='hub.test':
                request.abort();return
            if parsed.path in ('/api/apps-status','/api/apps-updates','/api/health'):
                request.fulfill(json={});return
            response=client.open(parsed.path+('?' + parsed.query if parsed.query else ''),method=request.request.method,data=request.request.post_data,content_type=request.request.headers.get('content-type'))
            request.fulfill(status=response.status_code,body=response.data,headers={'Content-Type':response.content_type})
        page.route('**/*',route)
        page.goto('http://hub.test/apps/fjordflix/wizard')
        # Choose the actual dynamic step by its rendered pill index.
        index=page.locator('.step-pill').filter(has_text='Adgang og Cloudflare').get_attribute('data-step')
        page.evaluate('(n)=>showPanel(Number(n))',index)
        expect(page.locator('#media-guide-details')).to_be_hidden()
        page.locator('#media-use-tunnel').select_option('yes')
        expect(page.locator('#media-guide-details')).to_be_visible()
        expect(page.locator('#media-guide-start')).to_be_hidden()
        assert page.locator('#media-guide').text_content().find('DNS only')>=0
        assert page.locator('[data-media-step]:visible').count()==1
        page.locator('[data-media-next="2"]').click()
        expect(page.locator('[data-media-step="2"]')).to_contain_text('Opret DNS i Cloudflare')
        page.locator('#media-use-tunnel').select_option('no')
        assert page.evaluate('validateMediaGuide()')
        gateway.start.assert_not_called()
        page.goto('http://hub.test/')
        assert '?v=' in page.locator('script[src*="app.js"]').get_attribute('src')
        gateway.status.return_value={'domain':'media.gleruphub.dk','mode':'managed'}
        page.evaluate("openAppSettings(document.querySelector('[data-app-id=fjordflix]'))")
        expect(page.locator('#media-dns-name')).to_have_text('media.gleruphub.dk')
        gateway.status.return_value={}
        expect(page.locator('#media-guide-web')).to_have_value('https://film.example.com')
        page.locator('#media-use-tunnel').select_option('yes')
        page.locator('[data-media-next="2"]').click()
        page.locator('#media-guide-domain').fill('media.example.com')
        expect(page.locator('#media-dns-name')).to_have_text('media.example.com')
        page.locator('#media-guide-domain').fill('https://video.home.example.co.uk/')
        expect(page.locator('#media-dns-name')).to_have_text('video.home.example.co.uk')
        expect(page.locator('#media-dns-target')).to_contain_text('video.home.example.co.uk')
        page.locator('#media-guide-domain').fill('')
        expect(page.locator('#media-dns-name')).to_have_text('—')
        page.locator('#media-guide-domain').fill('media.example.com')
        page.locator('[data-media-next="3"]').click()
        expect(page.locator('[data-media-step="3"]')).to_be_visible()
        expect(page.locator('[data-media-step="3"]')).to_contain_text('Åbn forbindelsen i routeren')
        page.locator('[data-media-next="4"]').click()
        expect(page.locator('[data-media-step="4"]')).to_be_visible()
        expect(page.locator('#media-guide-confirm')).to_have_value('https://media.example.com')
        expect(page.locator('#media-guide-web')).to_have_value('https://film.example.com')
        page.locator('[data-media-back="3"]').click()
        expect(page.locator('[data-media-step="3"]')).to_be_visible()
        out=Path(__file__).parents[1]/'test-results';out.mkdir(exist_ok=True)
        page.screenshot(path=str(out/'media-guide-dns.png'))
        page.locator('[data-media-next="4"]').click()
        page.locator('[data-media-next="5"]').click()
        expect(page.locator('#media-guide-ready')).not_to_be_checked()
        page.once('dialog',lambda dialog:dialog.accept())
        page.locator('#media-guide-start').click()
        gateway.start.assert_not_called()
        page.locator('#media-guide-ready').check()
        page.locator('#media-guide-start').click()
        page.wait_for_timeout(300)
        gateway.start.assert_called_once()
        out=Path(__file__).parents[1]/'test-results';out.mkdir(exist_ok=True)
        page.screenshot(path=str(out/'media-guide.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'media-guide-mobile.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        gateway.status.return_value={'active':True,'running':False,'phase':'Direkte video er aktiveret.'}
        page.evaluate('loadMediaGuide()')
        expect(page.locator('#media-guide-start')).to_be_disabled()
        expect(page.locator('#media-guide-done')).to_be_visible()
        # An unsuccessful retry must remain actionable even if an earlier setup was active.
        gateway.status.return_value={'active':True,'running':False,'error':'HTTPS-test fejlede'}
        page.evaluate('loadMediaGuide()')
        expect(page.locator('#media-guide-start')).to_be_enabled()
        expect(page.locator('#media-guide-done')).to_be_hidden()
        # New VPN path has its own instructions and carries the port to the API.
        gateway.status.return_value={}
        page.set_viewport_size({'width':1280,'height':960})
        page.evaluate('showMediaStep(1,false)')
        page.locator('#media-guide-route').select_option('proton')
        expect(page.locator('#media-guide-status')).not_to_have_class('app-settings-status ok')
        page.locator('[data-media-next="2"]').click()
        expect(page.locator('#media-dns-ip-help')).to_contain_text('Proton')
        page.locator('[data-media-next="3"]').click()
        expect(page.locator('#media-router-instructions')).to_be_hidden()
        expect(page.locator('#media-proton-instructions')).to_be_visible()
        page.locator('#media-guide-port').fill('57369')
        page.locator('[data-media-next="4"]').click()
        expect(page.locator('#media-guide-confirm')).to_have_value('https://media.example.com:57369')
        page.locator('[data-media-next="5"]').click()
        expect(page.locator('#media-router-mode')).to_be_hidden()
        expect(page.locator('#media-url-preview')).to_have_text('https://media.example.com:57369')
        expect(page.locator('#media-guide-ready')).not_to_be_checked()
        expect(page.locator('#media-ready-label')).to_contain_text('HTTPS-certifikat')
        previous_calls=gateway.start.call_count
        page.once('dialog',lambda dialog:dialog.accept())
        page.locator('#media-guide-start').click()
        assert gateway.start.call_count==previous_calls
        page.locator('#media-guide-ready').check()
        page.locator('#media-guide-start').click()
        page.wait_for_function('!document.getElementById("media-guide-start").disabled')
        assert gateway.start.call_args.args[-1]=='proton'
        assert gateway.start.call_args.kwargs['port']=='57369'
        page.screenshot(path=str(out/'media-guide-proton.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'media-guide-proton-mobile.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        gateway.status.return_value={'active':True,'running':False}
        page.evaluate('loadMediaGuide()')
        page.locator('#media-guide-done').click()
        expect(page.locator('#app-settings-modal')).not_to_have_class('modal-overlay is-open')
        assert not errors,errors
        print('PASS: installer yes/no, detailed DNS/port guide, settings prefill, setup API, mobile width, no JS errors.')
        browser.close()
