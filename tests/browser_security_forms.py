"""Browser login, form and fetch regression against disposable local Flask state."""
import logging
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.remote_registry import RemoteRegistry
from services.package_catalog import PackageCatalog

logging.getLogger('werkzeug').setLevel(logging.ERROR)
with tempfile.TemporaryDirectory(prefix='fjordhub-browser-security-') as data:
    os.environ.update(DATA_DIR=data, APPS_DIR=str(Path(data)/'apps'), FJORDHUB_SRC_DIR='',
                      FJORDHUB_MEMORY_RECONCILE='0', SECRET_KEY='synthetic-browser-key')
    with patch.object(RemoteRegistry,'_start_background_refresh'), \
         patch.object(PackageCatalog,'_start_background_refresh'), \
         patch('docker.from_env', side_effect=RuntimeError('Docker disabled')), \
         patch('requests.sessions.Session.request',side_effect=RuntimeError('External requests disabled')):
        import app as hub
        hub._auth.create_user('admin','test-password',role='admin',email='admin@example.test')
        reader_id=hub._auth.create_user('reader','test-password',email='reader@example.test')
        hub._auth.set_user_app_access(reader_id,'demo','user')
        definition={'id':'demo','name':'Demo','default_port':1234,'setup_steps':[]}
        hub._get_apps=lambda: [definition]
        hub._with_compose_dir=lambda a, _: a
        hub.docker_mgr.get_status=lambda a: {'state':'running','uptime':'test'}
        hub._update_manager.get_status=lambda a, **kwargs: {'state':'up_to_date'}
        started=Mock(return_value=(True,'started'))
        hub.docker_mgr.start=started
        hub._get_app=lambda _: definition
        server=make_server('127.0.0.1',0,hub.app,threaded=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page()
                page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base+'/') else r.abort())
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                def login(name):
                    page.goto(base+'/login')
                    page.locator('input[name=username]').fill(name)
                    page.locator('input[name=password]').fill('test-password')
                    page.locator('button[type=submit]').click()
                    expect(page).to_have_url(base+'/')
                login('admin')
                expect(page.locator('.btn-toggle')).to_have_count(1)
                page.goto(base+'/profile')
                page.locator('#profile-first-name').fill('Updated')
                page.get_by_role('button',name='Gem oplysninger').click()
                expect(page.locator('#profile-first-name')).to_have_value('Updated')
                assert hub._auth.get_by_username('admin').first_name=='Updated'
                code=page.evaluate("async()=> (await fetch('/apps/demo/start',{method:'POST'})).status")
                assert code==200
                started.assert_called_once()
                page.locator('form[action="/logout"] button').click()
                expect(page).to_have_url(base+'/login')
                login('reader')
                expect(page.locator('.btn-toggle')).to_have_count(0)
                expect(page.locator('.btn-delete')).to_have_count(0)
                expect(page.locator('.btn-link-hub')).to_have_count(0)
                expect(page.locator('.app-card .btn-open').first).to_be_visible()
                assert page.evaluate("async()=> (await fetch('/apps/demo/start',{method:'POST'})).status")==403
                started.assert_called_once()
                assert not errors, errors
                browser.close()
            print('PASS: actual login/profile/logout forms, authenticated fetch, admin controls and ordinary-user denial.')
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
