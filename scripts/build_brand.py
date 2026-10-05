"""Export the approved standalone artwork (never crop or redraw it).

Development dependencies: Pillow and Playwright Chromium.
Run from any directory: python scripts/build_brand.py
"""
from pathlib import Path
import base64
import io
import json
from html import escape

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'branding/exports.json').read_text(encoding='utf-8'))


def destination(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Brand export must remain inside the repository')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def export():
    master = Image.open(ROOT / 'branding/icon-master.png').convert('RGBA')
    # Keep the complete generated illustration, including its alpha channel.
    embedded = io.BytesIO()
    master.resize((512, 512), Image.Resampling.LANCZOS).save(embedded, format='PNG')
    uri = 'data:image/png;base64,' + base64.b64encode(embedded.getvalue()).decode('ascii')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        for item in CONFIG['exports']:
            path = destination(item['path'])
            width, height = item['size']
            kind = item.get('kind', 'icon')
            bg = item.get('background')
            ink = item.get('ink', '#edf3f7')
            if kind == 'icon' and path.suffix.lower() != '.svg':
                fraction = item.get('scale', 1)
                side = max(1, round(min(width, height) * fraction))
                icon = master.resize((side, side), Image.Resampling.LANCZOS)
                result = Image.new('RGBA', (width, height), bg or (0, 0, 0, 0))
                result.alpha_composite(icon, ((width-side)//2, (height-side)//2))
                if bg:
                    result = result.convert('RGB')
                if path.suffix.lower() == '.ico':
                    result.save(path, sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
                elif path.suffix.lower() == '.icns':
                    result.save(path, format='ICNS')
                else:
                    result.save(path, optimize=True)
                continue
            if kind == 'horizontal':
                side = height * .88
                x, y = 0, (height-side)/2
                tx = side + height*.13
                font = min(height*.42, (width-tx)*1.6/len(CONFIG['name']))
                text = f'<text x="{tx}" y="{height*.53}" dominant-baseline="middle" font-size="{font}" fill="{ink}">{escape(CONFIG["name"])}</text>'
            elif kind in ('stacked', 'social'):
                side = min(height*.68, width*.7)
                x, y = (width-side)/2, height*.035
                font = min(height*.13, width*1.55/len(CONFIG['name']))
                text = f'<text x="{width/2}" y="{height*.9}" text-anchor="middle" font-size="{font}" fill="{ink}">{escape(CONFIG["name"])}</text>'
            else:
                side = min(width, height) * item.get('scale', 1)
                x, y = (width-side)/2, (height-side)/2
                text = ''
            backdrop = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ''
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(CONFIG["name"])}">'
                   f'{backdrop}<image x="{x}" y="{y}" width="{side}" height="{side}" href="{uri}"/>'
                   f'<g font-family="Arial,sans-serif" font-weight="700">{text}</g></svg>')
            if path.suffix.lower() == '.svg':
                path.write_text(svg, encoding='utf-8')
            else:
                page.set_viewport_size({'width': width, 'height': height})
                page.set_content('<html><body style="margin:0;background:transparent">' + svg + '</body></html>')
                page.locator('svg image').evaluate('(el) => new Promise((resolve, reject) => {const i = new Image(); i.onload = resolve; i.onerror = reject; i.src = el.getAttribute("href");})')
                page.screenshot(path=str(path), omit_background=not bg)
        browser.close()
    print(f'{CONFIG["name"]}: exported {len(CONFIG["exports"])} assets')


if __name__ == '__main__':
    export()
