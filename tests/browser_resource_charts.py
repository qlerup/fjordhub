"""Exercise real resource view switching and polling with synthetic measurements."""
import json
from pathlib import Path
from types import SimpleNamespace

from conftest import hub
from flask import render_template
from playwright.sync_api import sync_playwright, expect

with hub.app.test_request_context('/resources'):
    html=render_template('resources.html',current_user=SimpleNamespace(
        is_admin=True,is_authenticated=True,username='Preview'),active_page='resources')
sample={'ok':True,'generated_at':'2026-10-12T12:00:00Z',
        'hub':{'net_rx':1000000,'net_tx':2000000,'cpu_capacity_percent':10,'memory_percent':20},
        'system':{'available':True,'cpu_capacity_percent':25,'memory_percent':30}}
requests=[]
root=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    def route(request):
        url=request.request.url
        if url.endswith('/api/resources'):
            requests.append(url);request.fulfill(json=sample)
        elif url.endswith('/resources'):
            request.fulfill(content_type='text/html',body=html)
        elif '/static/styles.css' in url:
            request.fulfill(content_type='text/css',body=(root/'static/styles.css').read_text(encoding='utf-8'))
        else:request.fulfill(status=204)
    page.route('**/*',route)
    page.goto('http://fixture.test/resources')
    page.wait_for_function('() => chartHistories.lxc.length === 1')
    page.evaluate('clearInterval(resourceTimer)')
    baseline=page.evaluate('JSON.stringify(chartHistories)')
    for _ in range(4):
        page.locator('[data-resource-view=docker]').click()
        expect(page.locator('#resource-scope-title')).to_have_text('Docker-containere')
        page.locator('[data-resource-view=lxc]').click()
        expect(page.locator('#resource-scope-title')).to_have_text('LXC fra Proxmox')
    assert page.evaluate('JSON.stringify(chartHistories)')==baseline
    assert len(requests)==1
    sample.update(generated_at='2026-10-12T12:00:07Z')
    sample['hub'].update(net_rx=1007000,net_tx=2014000)
    page.evaluate('() => Promise.all([refreshResources(),refreshResources()])')
    assert len(requests)==2
    histories=page.evaluate('chartHistories')
    for points in histories.values():
        assert len(points)==2
        assert points[0]['netIn']==points[0]['netOut']==0
        assert points[1]['netIn']==1000 and points[1]['netOut']==2000
    page.evaluate('() => refreshResources()')
    assert page.evaluate('chartHistories.lxc.length')==2
    sample['generated_at']='2026-10-12T11:59:00Z'
    page.evaluate('() => refreshResources()')
    assert page.evaluate('chartHistories.lxc.length')==2
    sample.update(generated_at='2026-10-12T12:00:14Z')
    sample['hub'].update(net_rx=0,net_tx=0)
    page.evaluate('() => refreshResources()')
    assert page.evaluate('chartHistories.docker.at(-1).netIn')==0
    assert not errors,errors
    browser.close()
print('PASS: view changes do not sample; real polls advance both histories; rates, deduplication and request overlap verified')
