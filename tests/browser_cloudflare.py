"""Cloudflare settings UI with isolated login and synthetic provider responses."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
from conftest import hub
from services.auth import AuthService
from services.install_state import InstallState
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory() as folder:
    auth=AuthService(Path(folder)/'auth.db')
    uid=auth.create_user('Cloudflare UI','Synthetic-password-73!',role='admin',email='admin@example.com')
    client=hub.app.test_client()
    with client.session_transaction() as session:
        session['_user_id']=auth.get_by_id(uid).get_id();session['_fresh']=True
    with patch.object(hub,'_auth',auth),patch.object(hub,'_install_state',InstallState(Path(folder))),sync_playwright() as pw:
        browser=pw.chromium.launch()
        for width in (1440,390):
            page=browser.new_page(viewport={'width':width,'height':1100})
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            state={'ok':True,'enabled':True,'domains':[]}
            records=[]
            def route(route):
                request=route.request;url=urlsplit(request.url)
                if url.hostname!='hub.test':route.abort();return
                path=url.path
                if path.startswith('/api/cloudflare/'):
                    payload=json.loads(request.post_data or '{}')
                    if path.endswith('/settings'):
                        if request.method=='POST':state['enabled']=payload['enabled']
                        route.fulfill(json=state);return
                    if path.endswith('/domains'):
                        if payload['token'] not in ('synthetic-test-token','multi-zone-token'):
                            route.fulfill(status=400,json={'ok':False,'error':'Kontrollér API-tokenets rettigheder.'});return
                        if payload['token']=='multi-zone-token' and not payload.get('name'):
                            route.fulfill(json={**state,'selection_required':True,'choices':['example.com','other.dk']});return
                        name=payload.get('name','example.com')
                        assert name in ('example.com','other.dk')
                        existing=next((d for d in state['domains'] if d['name']==name),None)
                        if existing:existing['label']=payload['label']
                        else:state['domains'].append({'id':len(state['domains'])+1,'name':name,'label':payload['label']})
                        route.fulfill(json={**state,'connected_domain':name});return
                    if '/records' in path:
                        if request.method=='POST':records.append({**payload,'id':'record-1'})
                        if request.method=='PATCH':records[0].update(payload)
                        if request.method=='DELETE':records.clear()
                        route.fulfill(json={'ok':True});return
                    route.fulfill(json={'ok':True,'records':records,'tunnels':[],'warnings':[]});return
                if path.startswith('/api/'):
                    route.fulfill(json={});return
                response=client.get(path+('?' + url.query if url.query else ''))
                route.fulfill(status=response.status_code,body=response.data,headers={'Content-Type':response.content_type})
            page.route('**/*',route)
            page.goto('http://hub.test/settings/cloudflare')
            expect(page.locator('#cf-content')).to_be_visible()
            expect(page.locator('.cf-guide')).to_have_attribute('open','')
            expect(page.locator('#cf-empty')).to_be_visible()
            assert page.locator('.cf-permissions tbody tr').count()==2
            assert page.locator('a[href="https://dash.cloudflare.com/profile/api-tokens"]').count()==1
            for link in page.locator('.cf-page a[target="_blank"]').all():
                assert 'noopener' in link.get_attribute('rel')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            output=Path(__file__).resolve().parents[1]/'test-results';output.mkdir(exist_ok=True)
            page.screenshot(path=str(output/f'cloudflare-empty-{width}.png'),full_page=True)
            expect(page.locator('#cf-zone-choice')).to_be_hidden()
            page.locator('#cf-token-label').fill('Privat')
            page.locator('#cf-token').fill('invalid-synthetic-token')
            page.locator('#cf-connect button[type=submit]').click()
            expect(page.locator('#cf-status')).to_have_attribute('data-error','true')
            expect(page.locator('#cf-empty')).to_be_visible()
            page.locator('#cf-token').fill('synthetic-test-token')
            page.locator('#cf-connect button[type=submit]').click()
            expect(page.locator('#cf-overview')).to_be_visible()
            expect(page.locator('#cf-token')).to_have_value('')
            expect(page.locator('#cf-domains')).to_have_value('1')
            expect(page.locator('#cf-domains option:checked')).to_have_text('Privat · example.com')
            expect(page.locator('#cf-token-label')).to_have_value('')
            expect(page.locator('#cf-zone-choice')).to_be_hidden()
            page.locator('#cf-new').click()
            page.locator('#cf-record-name').fill('media.example.com')
            page.locator('#cf-value').fill('192.0.2.10')
            page.locator('#cf-record-form button[type=submit]').click()
            expect(page.locator('#cf-records')).to_contain_text('media.example.com')
            page.locator('#cf-records').get_by_role('button',name='Rediger',exact=True).click()
            page.locator('#cf-value').fill('192.0.2.11')
            page.locator('#cf-record-form button[type=submit]').click()
            expect(page.locator('#cf-records')).to_contain_text('192.0.2.11')
            page.screenshot(path=str(output/f'cloudflare-connected-{width}.png'),full_page=True)
            page.on('dialog',lambda dialog:dialog.accept())
            page.locator('#cf-records').get_by_role('button',name='Slet',exact=True).click()
            expect(page.locator('#cf-records')).not_to_contain_text('media.example.com')
            page.locator('#cf-token-label').fill('Arbejde')
            page.locator('#cf-token').fill('multi-zone-token')
            page.locator('#cf-connect button[type=submit]').click()
            expect(page.locator('#cf-zone-choice')).to_be_visible()
            page.locator('#cf-name').select_option('other.dk')
            page.locator('#cf-connect button[type=submit]').click()
            expect(page.locator('#cf-zone-choice')).to_be_hidden()
            expect(page.locator('#cf-domains option:checked')).to_have_text('Arbejde · other.dk')
            assert page.locator('#cf-domains option').count()==2
            expect(page.locator('#cf-token')).to_have_value('')
            page.locator('#cf-enabled').uncheck()
            expect(page.locator('#cf-content')).to_be_hidden()
            page.locator('#cf-enabled').check()
            expect(page.locator('#cf-content')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
            print('PASS Cloudflare: desktop/mobile layout, links, token connection, create/edit/delete subdomain and enable toggle',width)
            page.close()
        browser.close()
