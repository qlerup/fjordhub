"""Isolated Chromium regression for the same-origin CSRF fetch wrapper.

Run: python tests/browser_csrf.py
All navigation and fetch results are synthetic; no server is contacted.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright


script = (Path(__file__).resolve().parents[1] / 'static/csrf.js').read_text(encoding='utf-8')
token = 'synthetic-session-csrf-token'
origin = 'https://fjordhub.test'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    navigations = []

    def intercept(route):
        navigations.append(route.request.url)
        if route.request.url == origin + '/fixture':
            route.fulfill(content_type='text/html', body=f'<meta name="csrf-token" content="{token}">')
        else:
            route.abort()

    page.route('**/*', intercept)
    page.goto(origin + '/fixture')
    page.evaluate('''() => {
      window.calls = [];
      window.fetch = async (input, init) => {
        // Native Request normalization verifies the wrapper's effective request,
        // including headers/body inherited from Request objects or overridden by init.
        const request = new Request(input, init);
        calls.push({url: request.url, method: request.method,
          headers: Object.fromEntries(request.headers), body: await request.text(),
          credentials: request.credentials, redirect: request.redirect});
        return new Response('{"ok":true}', {headers: {'Content-Type': 'application/json'}});
      };
    }''')
    page.add_script_tag(content=script)

    result = page.evaluate('''async () => {
      const headers = {'Content-Type': 'application/json', 'X-Existing': 'kept'};
      const init = {method: 'post', headers, body: '{"value":1}', credentials: 'include', redirect: 'manual'};
      const response = await fetch('/api/example', init);
      return {data: await response.json(), initUnchanged: !('X-CSRF-Token' in headers) && init.headers === headers};
    }''')
    assert result == {'data': {'ok': True}, 'initUnchanged': True}
    call = page.evaluate('calls.at(-1)')
    assert call['headers']['x-csrf-token'] == token
    assert call['headers']['x-existing'] == 'kept'
    assert call['headers']['content-type'] == 'application/json'
    assert call['body'] == '{"value":1}'
    assert call['credentials'] == 'include'
    assert call['redirect'] == 'manual'

    page.evaluate('''async () => {
      const request = new Request(location.origin + '/api/example', {
        method: 'POST', headers: new Headers({'Content-Type': 'text/plain', 'X-Existing': 'request-header'}),
        body: 'original request body', credentials: 'omit'});
      await fetch(request);
      window.originalToken = request.headers.get('X-CSRF-Token');
    }''')
    call = page.evaluate('calls.at(-1)')
    assert call['headers']['x-csrf-token'] == token
    assert call['headers']['x-existing'] == 'request-header'
    assert call['headers']['content-type'] == 'text/plain'
    assert call['body'] == 'original request body'
    assert call['credentials'] == 'omit'
    assert page.evaluate('originalToken') is None

    # Explicit headers and bodies passed with a Request retain native override semantics.
    page.evaluate('''async () => {
      const request = new Request(location.origin + '/api/example', {
        method: 'POST', headers: {'X-Old': 'replaced'}, body: 'old body'});
      await fetch(request, {method: 'PATCH', headers: [['X-New', 'new header']], body: 'new body'});
    }''')
    call = page.evaluate('calls.at(-1)')
    assert call['method'] == 'PATCH'
    assert call['body'] == 'new body'
    assert call['headers']['x-new'] == 'new header'
    assert 'x-old' not in call['headers']
    assert call['headers']['x-csrf-token'] == token

    for request_object in (False, True):
        page.evaluate('''async useRequest => {
          const init = {method: 'POST', headers: {'x-CsRf-ToKeN': 'explicit-token'}, body: 'body'};
          await (useRequest ? fetch(new Request(location.origin + '/api/example', init)) : fetch('/api/example', init));
        }''', request_object)
        assert page.evaluate("calls.at(-1).headers['x-csrf-token']") == 'explicit-token'

    for method in ('GET', 'HEAD', 'OPTIONS'):
        for request_object in (False, True):
            page.evaluate('''async ({method, useRequest}) => {
              await (useRequest ? fetch(new Request(location.origin + '/api/example', {method})) : fetch('/api/example', {method}));
            }''', {'method': method, 'useRequest': request_object})
            assert 'x-csrf-token' not in page.evaluate('calls.at(-1).headers')

    for url in ('https://other.test/api/example', 'https://fjordhub.test:8443/api/example',
                'http://fjordhub.test/api/example', '//other.test/api/example'):
        for request_object in (False, True):
            page.evaluate('''async ({url, useRequest}) => {
              const init = {method: 'POST', headers: {'X-Existing': 'external'}, body: 'external body'};
              await (useRequest ? fetch(new Request(new URL(url, location.href), init)) : fetch(url, init));
            }''', {'url': url, 'useRequest': request_object})
            call = page.evaluate('calls.at(-1)')
            assert 'x-csrf-token' not in call['headers']
            assert call['headers']['x-existing'] == 'external'
            assert call['body'] == 'external body'

    # Init method overrides the Request method for token selection too.
    page.evaluate('''async () => {
      await fetch(new Request(location.origin + '/api/example'), {method: 'DELETE'});
    }''')
    assert page.evaluate("calls.at(-1).headers['x-csrf-token']") == token

    page.evaluate('''() => {
      document.querySelector('meta[name="csrf-token"]').remove();
      window.fetch = async () => 'unwrapped';
      window.fetchBefore = window.fetch;
    }''')
    page.add_script_tag(content=script)
    assert page.evaluate('fetch === fetchBefore')
    assert navigations == [origin + '/fixture'], navigations
    browser.close()
print('PASS: CSRF token scope, Request/string inputs, existing headers/body, explicit tokens and safe methods.')
