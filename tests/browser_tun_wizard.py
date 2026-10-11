"""Verify the TUN step and copy button, including ordinary HTTP fallback."""
import json
import logging
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock,patch

from playwright.sync_api import sync_playwright,expect
from werkzeug.serving import make_server

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from services.remote_registry import RemoteRegistry
from services.package_catalog import PackageCatalog
from services import vpn_setup

logging.getLogger('werkzeug').setLevel(logging.ERROR)
with tempfile.TemporaryDirectory(prefix='fjordhub-tun-wizard-') as data:
    os.environ.update(DATA_DIR=data,APPS_DIR=str(Path(data)/'apps'),FJORDHUB_SRC_DIR='',
        FJORDHUB_MEMORY_RECONCILE='0',SECRET_KEY='synthetic-browser-key')
    with patch.object(RemoteRegistry,'_start_background_refresh'),patch.object(PackageCatalog,'_start_background_refresh'), \
         patch('docker.from_env',side_effect=RuntimeError('Docker disabled')), \
         patch('requests.sessions.Session.request',side_effect=RuntimeError('Network disabled')):
        import app as hub
        hub._auth.create_user('admin','test-password',role='admin')
        definition=json.loads((root/'app_registry/fjordvpn.json').read_text(encoding='utf-8'))
        hub._get_app=lambda _:definition;hub._get_apps=lambda:[definition]
        client=Mock();client.containers.get.return_value.attrs={'Id':'a'*64}
        with patch.object(vpn_setup.docker,'from_env',return_value=client),patch.dict(os.environ,HOSTNAME='test-hub'):
            info=vpn_setup.wizard_setup()
        hub.docker_mgr.get_status=lambda _:{'state':'not_installed'}
        server=make_server('127.0.0.1',0,hub.app,threaded=True)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            initial={'proxmox':'unconfigured','docker':'connected','tun':'unavailable','ready':False,'message':'Kør opsætningen.'}
            with patch.object(vpn_setup,'wizard_setup',return_value=info), \
                 patch.object(vpn_setup,'cached_check_vpn_tun',return_value=initial) as checker,sync_playwright() as pw:
                browser=pw.chromium.launch()
                context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'])
                page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base+'/') else r.abort())
                page.goto(base+'/login');page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill('test-password')
                page.locator('button[type=submit]').click()
                page.goto(base+'/apps/fjordvpn/wizard');page.locator('#btn-next').click()
                expect(page.locator('#panel-1 h2')).to_have_text('TUN netværksopsætning')
                expect(page.locator('#tun-proxmox-status')).to_have_text('Ikke sat op')
                page.locator('#tun-copy-btn').click()
                expect(page.locator('#tun-copy-btn')).to_contain_text('Kopieret')
                assert page.evaluate('() => navigator.clipboard.readText()').replace('\r\n','\n')==info['command']
                (root/'test-results').mkdir(exist_ok=True)
                page.screenshot(path=str(root/'test-results/tun-wizard-1440.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(root/'test-results/tun-wizard-390.png'),full_page=True)
                page.evaluate("() => { Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true}); const original=document.execCommand.bind(document); document.execCommand=(command)=>{window.fallbackCopy=document.querySelector('textarea').value; return original(command);}; }")
                page.locator('#tun-copy-btn').click()
                assert page.evaluate('window.fallbackCopy')==info['command']
                checker.return_value={'proxmox':'connected','docker':'connected','tun':'ready','ready':True,'message':'TUN er klar.'}
                page.locator('#tun-check-btn').click()
                expect(page.locator('#tun-proxmox-status')).to_have_text('Forbundet')
                expect(page.locator('#tun-device-status')).to_have_text('TUN er klar')
                page.locator('#btn-next').click()
                expect(page.locator('#panel-2 h2')).to_have_text('Web og lokalnet')
                assert not errors,errors
                browser.close()
        finally:server.shutdown()
print('PASS: TUN step, exact clipboard command, HTTP fallback, desktop/mobile and next step')
