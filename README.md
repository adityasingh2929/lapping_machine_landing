# Micro MLP 42 — client showcase

A responsive static landing page with the saved machine in interactive 3D, camera presets, component views and nameplate specifications.

## Preview

Run `npm ci`, then `npm run dev`. Open http://127.0.0.1:4173/.
The publishable website is entirely in `docs/`; no server or build step is required for hosting.

## GitHub Pages

Publish the `master` branch, `/docs` folder. Public URL:
https://adityasingh2929.github.io/lapping_machine_landing/

## Refresh the model

The website has two independent machines. Export `saved_one.blend` with `--python site_tools/export_web.py` for the original (`micro-mlp42.glb`). Export `lapping_machine_blockout.blend` with `--python site_tools/export_web.py -- --blue` for the blue machine (`micro-blue.glb`). Exporting never saves changes to either source. The exporter resolves modifiers and packs nameplate textures into Draco-compressed GLBs; accompanying source JSON records the Blender source hash. Use `site_tools/render_machine_poster.py` with the same source and optional `-- --blue` to refresh each poster. Delete `docs/assets/plate-*-color.png` and `plate-*-metal.png` before exporting if the shared nameplate artwork has changed; otherwise the baked artwork is reused. The blue machine can be linked directly using `?machine=blue`.

The website uses model-viewer 4.3.1 (Apache 2.0, license in `docs/assets/`). Update the local runtime from `node_modules/@google/model-viewer/dist/model-viewer.min.js` after changing dependencies. Google Fonts and the model-viewer Draco decoder are fetched from their public providers. Business details and electrical specifications come from the supplied nameplate; no unverified production tolerances are stated.

Original Blender assets, generation scripts and historical previews remain in the working folder; this initial website commit includes only files needed to serve and reproduce the web export.
