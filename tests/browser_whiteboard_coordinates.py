"""Real rendered pixels must stay under the pointer at every display scale."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
package = root / 'packages_src' / 'notepad'
html = ('<!doctype html><meta charset="utf-8"><style>' +
        (root / 'static/styles.css').read_text(encoding='utf-8') +
        (package / 'styles.css').read_text(encoding='utf-8') +
        '</style><main class="page-content"><div class="builtin-app" data-package="notepad">' +
        (package / 'body.html').read_text(encoding='utf-8') + '</div></main><script>' +
        (package / 'app.js').read_text(encoding='utf-8') + '</script>')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for ratio in (1, 1.25, 1.5, 2):
        context = browser.new_context(viewport={'width': round(3840/ratio), 'height': round(2160/ratio)},
                                      device_scale_factor=ratio)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('http://whiteboard.test/', lambda route: route.fulfill(body=html, content_type='text/html'))
        page.goto('http://whiteboard.test/')
        page.wait_for_function('document.getElementById("wbCanvas").width > 300')

        def draw_at_pointer(fraction):
            page.wait_for_function('''() => {
                const c=document.getElementById('wbCanvas'), r=document.getElementById('wbStage').getBoundingClientRect();
                return Math.abs(c.width-r.width*devicePixelRatio)<=.5 && Math.abs(c.height-r.height*devicePixelRatio)<=.5;
            }''')
            bounds = page.locator('#wbStage').bounding_box()
            x, y = bounds['x'] + bounds['width']*fraction, bounds['y'] + bounds['height']*.55
            page.mouse.click(x, y)
            alpha = page.evaluate('''([x,y]) => {
                const canvas=document.getElementById('wbCanvas'), r=canvas.getBoundingClientRect();
                const px=Math.floor((x-r.left)*canvas.width/r.width), py=Math.floor((y-r.top)*canvas.height/r.height);
                return canvas.getContext('2d').getImageData(px,py,1,1).data[3];
            }''', [x,y])
            assert alpha > 200, f'DPR {ratio}: no stroke under pointer ({x}, {y}); alpha={alpha}'
            page.locator('[data-tool="eraser"]').click()
            page.mouse.move(x,y)
            cursor = page.locator('.wb-eraser-cursor').bounding_box()
            assert abs(cursor['x']+cursor['width']/2-x)<1
            assert abs(cursor['y']+cursor['height']/2-y)<1
            page.mouse.click(x,y)
            page.locator('[data-tool="pen"]').click()

        draw_at_pointer(.35)
        page.mouse.wheel(0, -400)
        page.locator('[data-tool="hand"]').click()
        bounds = page.locator('#wbStage').bounding_box()
        page.mouse.move(bounds['x']+300, bounds['y']+200)
        page.mouse.down()
        page.mouse.move(bounds['x']+410, bounds['y']+260, steps=5)
        page.mouse.up()
        page.locator('[data-tool="pen"]').click()
        draw_at_pointer(.65)
        page.set_viewport_size({'width': 1280, 'height': 900})
        page.wait_for_function('document.getElementById("wbStage").clientWidth < 1280')
        draw_at_pointer(.45)
        if ratio == 1:
            cdp = context.new_cdp_session(page)
            cdp.send('Emulation.setDeviceMetricsOverride', {
                'width':1280, 'height':900, 'deviceScaleFactor':2, 'mobile':False})
            page.wait_for_function('''() => {
                const s=document.getElementById('wbStage'), c=document.getElementById('wbCanvas');
                return Math.abs(c.width-s.getBoundingClientRect().width*2)<1;
            }''')
            draw_at_pointer(.75)
        assert not errors, errors
        context.close()
    browser.close()
print('PASS: 4K at 100/125/150/200 percent, drawing, eraser cursor, zoom, pan and resize')
