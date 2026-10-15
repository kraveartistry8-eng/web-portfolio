# Ember v23, frozen

Saved 12 Oct 2026 at Aaron's request, to reuse elsewhere as is. Nothing here changes when the Afterglow ember changes.

- `ember-v23.html`: the approved reference page, self-contained. It loads Three.js 0.160.0 from unpkg as a module, so open it over a local server (`python3 -m http.server`), not as a file.
- `ember-engine.js`, `ember-math.js`: the engine as committed (HEAD 4c88531). Its colour pushes the page's chroma up (`1 + 3.4 × heat`) and runs toward white heat.
- `ember.bundle.js`: the same engine and Three.js as one classic script that sets `window.EmberEngine`. It opens over file://.
