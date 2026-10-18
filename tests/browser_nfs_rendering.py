"""Isolated SEC-006 browser regression; all API responses are synthetic.

Run: python tests/browser_nfs_rendering.py
Requires Playwright with Chromium installed. Never contacts an NFS server.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright


script = (Path(__file__).resolve().parents[1] / 'static/nfs-helper.js').read_text(encoding='utf-8')
html = '''
<input id="nfs-server-ip" value="192.0.2.1">
<select id="nfs-export-select"></select>
<input id="nfs-mount-root" value="/mnt/nas">
<input id="nfs-subdir" value="uploads">
<input id="nfs-options" value="vers=3,resvport,_netdev,nofail">
<input id="nfs-vmid" value="100">
<input type="radio" name="nfs-setup-type" value="proxmox" checked>
<input type="radio" name="nfs-setup-type" value="wsl2">
<button id="nfs-fetch-btn"></button><div id="nfs-fetch-result"></div>
<div id="nfs-code-block"></div><div id="nfs-mount-status"></div>
<button id="nfs-done-btn"></button><button id="nfs-copy-btn"></button>
'''

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    # A network request is a harness failure, not a real service dependency.
    requests = []
    page.route('**/*', lambda route: (requests.append(route.request.url), route.abort()))
    page.set_content(html)
    page.add_script_tag(content=script)
    page.evaluate('''() => {
      window.calls = [];
      window.reply = {};
      window.fetch = async (url, options) => {
        calls.push({url, options});
        if (window.fetchError) throw new Error(window.fetchError);
        return {json: async () => reply};
      };
      // Rendering is under test; mount polling cannot run jobs or timers.
      startMountPolling = () => {};
      _copyText = text => { window.copied = text; };
    }''')
    special = '/exports/Photos & "family" <b data-nfs-marker>literal</b>'
    active = '/exports/<img data-nfs-marker src=x onerror="window.nfsMarker=true">'
    for export in ('/exports/photos', special, active):
        page.evaluate('(value) => { reply = {exports: [value]}; }', export)
        page.evaluate('fetchNfsExports()')
        option = page.locator('#nfs-export-select option').nth(1)
        assert option.text_content() == export
        assert option.get_attribute('value') == export
        page.select_option('#nfs-export-select', export)
        for mode in ('wsl2', 'proxmox', 'unknown'):
            page.evaluate('''mode => {
              document.querySelector(`input[value="${mode === 'wsl2' ? 'wsl2' : 'proxmox'}"]`).checked = true;
              _nfsLxcPrivileged = mode === 'proxmox' ? false : null;
              renderNfsCommands();
            }''', mode)
            code = page.locator('#nfs-code-block .nfs-code-block')
            assert export in code.text_content()
            assert code.locator('.nfs-code-comment').count() > 0
            page.locator('#nfs-code-block .btn-nfs-copy-section').click()
            assert page.evaluate('copied') == code.text_content()
            page.evaluate('copyNfsCommands()')
            assert export in page.evaluate('copied')
            assert page.locator('[data-nfs-marker]').count() == 0
            assert page.evaluate('window.nfsMarker === undefined')

    # All editable preview fields also stay text, including comments and VMID.
    for field in ('nfs-server-ip', 'nfs-mount-root', 'nfs-subdir', 'nfs-options', 'nfs-vmid'):
        previous = page.locator('#' + field).input_value()
        page.locator('#' + field).fill(special)
        page.evaluate('_nfsLxcPrivileged = false; renderNfsCommands()')
        assert special in page.locator('#nfs-code-block .nfs-code-block').text_content()
        assert page.locator('[data-nfs-marker]').count() == 0
        page.locator('#' + field).fill(previous)

    for error in (special, active):
        page.evaluate('(error) => { reply = {error}; }', error)
        page.evaluate('fetchNfsExports()')
        assert page.locator('#nfs-fetch-result').text_content() == '✗ ' + error
        assert page.locator('#nfs-export-select').is_disabled()
        page.evaluate('(error) => { window.fetchError = error; }', error)
        page.evaluate('fetchNfsExports()')
        assert page.locator('#nfs-fetch-result').text_content() == '✗ Fejl: ' + error
        page.evaluate('window.fetchError = null')
        assert page.locator('[data-nfs-marker]').count() == 0

    # Automatic mount success and failure use the actual asynchronous callback.
    page.evaluate('reply = {exports: ["/exports/photos"]}')
    page.evaluate('fetchNfsExports()')
    page.select_option('#nfs-export-select', '/exports/photos')
    page.evaluate('_nfsLxcPrivileged = true; renderNfsCommands()')
    for ok in (False, True):
        page.evaluate('(data) => { reply = data; }', {'ok': ok, 'error': active, 'path': special})
        page.evaluate('autoMountNfs()')
        status = page.locator('#nfs-auto-status')
        assert status.text_content() == ('✓ Mountet — ' + special if ok else '✗ ' + active)
        assert page.locator('[data-nfs-marker]').count() == 0
        assert page.evaluate('window.nfsMarker === undefined')
    assert page.locator('#nfs-done-btn').is_enabled()
    assert not requests, requests
    browser.close()
print('PASS: NFS exports, preview modes, clipboard text, fields, errors and mount results render inertly.')
