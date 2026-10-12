"""Uninstall UI, polling and failure handling against disposable Flask state."""
import logging
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.remote_registry import RemoteRegistry
from services.package_catalog import PackageCatalog

logging.getLogger('werkzeug').setLevel(logging.ERROR)
with tempfile.TemporaryDirectory(prefix='fjordhub-uninstall-browser-') as data:
    os.environ.update(DATA_DIR=data,APPS_DIR=str(Path(data)/'apps'),FJORDHUB_SRC_DIR='',
                      FJORDHUB_MEMORY_RECONCILE='0',SECRET_KEY='synthetic-browser-key')
    with patch.object(RemoteRegistry,'_start_background_refresh'), \
         patch.object(PackageCatalog,'_start_background_refresh'), \
         patch('docker.from_env',side_effect=RuntimeError('Docker disabled')), \
         patch('requests.sessions.Session.request',side_effect=RuntimeError('External requests disabled')):
        import app as hub
        hub._auth.create_user('admin','test-password',role='admin')
        (Path(data)/'.git').mkdir()
        definition={'id':'demo','name':'Demo','default_port':1234,'setup_steps':[], 'compose_dir':data}
        hub._get_apps=lambda:[definition];hub._get_app=lambda _:definition
        hub._with_compose_dir=lambda a,_:a
        runtime={'state':'running','uptime':'test'}
        hub.docker_mgr.get_status=lambda _:dict(runtime)
        hub._update_manager.get_status=lambda a,**kwargs:{'state':'up_to_date'}
        hub._install_state.register('demo',data)
        hub._auth.save_hub_key('demo','fixture-key')
        entered=threading.Event();release=threading.Event()
        def remove(*args,**kwargs):
            entered.set()
            assert release.wait(5)
            runtime['state']='not_installed'
        hub.remove_runtime=remove
        server=make_server('127.0.0.1',0,hub.app,threaded=True)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page()
                page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base+'/') else r.abort())
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base+'/login')
                page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill('test-password')
                page.locator('button[type=submit]').click()
                card=page.locator('.app-card[data-app-id=demo]')
                expect(card.locator('.btn-toggle')).to_have_text('Stop')
                page.once('dialog',lambda d:d.accept())
                page.evaluate("() => { void confirmUninstall(document.querySelector('.app-card[data-app-id=demo]')); }")
                expect(card.locator('.btn-toggle')).to_be_disabled()
                assert entered.wait(2)
                page.evaluate("() => { applyStatus(document.querySelector('.app-card[data-app-id=demo]'),{state:'running'}); applyUpdateStatus(document.querySelector('.app-card[data-app-id=demo]'),{state:'up_to_date'}); }")
                expect(card.locator('.btn-toggle')).to_be_disabled()
                release.set()
                expect(card.locator('.btn-toggle')).to_have_text('Installer')
                expect(card.locator('.btn-link-hub')).not_to_be_visible()
                assert not hub._auth.get_hub_key('demo') and hub._install_state.get('demo')=={}
                page.reload()
                expect(card.locator('.btn-toggle')).to_have_text('Installer')
                expect(card.locator('.btn-link-hub')).not_to_be_visible()
                card.locator('.btn-toggle').click()
                expect(page).to_have_url(base+'/apps/demo/wizard')
                # A failed removal must keep the running card, registration and key.
                runtime['state']='running';hub._install_state.register('demo',data)
                hub._auth.save_hub_key('demo','fixture-key')
                hub.remove_runtime=Mock(side_effect=RuntimeError('Fixture cleanup failed'))
                page.goto(base+'/');expect(card.locator('.btn-toggle')).to_have_text('Stop')
                page.once('dialog',lambda d:d.accept())
                page.evaluate("() => { void confirmUninstall(document.querySelector('.app-card[data-app-id=demo]')); }")
                expect(card.locator('.btn-toggle')).to_be_enabled()
                assert hub._auth.verify_hub_key('demo','fixture-key')
                assert hub._install_state.get_install_dir('demo')==data
                assert not errors,errors
                browser.close()
        finally:
            release.set();server.shutdown()
print('PASS: polling cannot enable actions during uninstall; success shows Installer; failure preserves registration and key')
