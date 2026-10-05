# FjordHub artwork

`icon-master.png` is the standalone image generated with the built-in image generation tool from the approved nine-app reference. It is not a crop of the reference sheet.

All exported app icons, logos, favicons and platform assets are listed in `exports.json`. Existing public filenames are retained for compatibility; their artwork is replaced. SVG files are layout wrappers embedding the new raster illustration, not editable vector originals.

Rebuild with `python scripts/build_brand.py` (Pillow and Playwright Chromium required). The exporter preserves the entire illustration and transparency, resizes platform icons, and lays out the app name for wordmarks. Maskable exports include safe padding on an opaque background. No application theme is changed.

Generation prompt: Regenerate only the FjordHub icon from the user's approved nine-app sheet as a standalone square. Preserve its motif, palette, composition and dimensional shading. No text, grain, wear, outside shadow or white border; transparent rounded corners. Do not crop the sheet.
