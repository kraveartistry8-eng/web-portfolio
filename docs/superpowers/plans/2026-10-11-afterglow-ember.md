# Afterglow Ember Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved ember as one engine behind every page of the Afterglow brand guide, with a new Ember page (direction A′, page 12, deep violet). The Shopify homepage (Task 5) is deferred.

**Architecture:**
- **Pure maths:** `brand/ember/ember-math.js` holds everything testable without a GPU: the fall, field sizing, decay, the stop timing (coast, cut, cap, ripple fade) and the light curves.
- **Engine:** `brand/ember/ember-engine.js` is the `EmberEngine` class, in `StylizedShadowEngine`'s shape on Three.js 0.160.0. It runs three passes per frame: heat, age, display.
- **One bundle:** esbuild turns both into a single classic-script file, `brand/ember/ember.bundle.js`, which exposes `window.EmberEngine`. The bundle opens over `file://` (the guide) and loads as a Shopify asset later.
- **Ground:** each host passes a `groundAt(t)` callback that colours the document from top (t = 0) to bottom (t = 1). The engine bakes it into a 1 × 2048 lookup texture.

**Tech Stack:** JavaScript (ES modules, bundled to an IIFE), Three.js 0.160.0, esbuild via `npx`, `node --test`, Python 3 with Playwright. Browser tests run headless on the real GPU, launched with `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`. They never run headed, because a headed window picks up Aaron's real mouse.

**Spec:** `docs/superpowers/specs/2026-10-11-afterglow-ember-design.md`
**Reference build:** `docs/superpowers/specs/2026-10-11-afterglow-ember-reference.html`, approved v23. Port behaviour from it. Where the reference and the spec differ, the spec wins.
**Page mockup:** `docs/superpowers/specs/2026-10-11-afterglow-ember-page-reference.html` (A′ on deep violet), built by `docs/superpowers/specs/2026-10-11-afterglow-ember-page-build.py`. Port its markup and CSS for the Ember page.

## Global Constraints

- **Three.js:** exactly `three@0.160.0`, vendored into the bundle. No CDN at runtime.
- **Fall stops:**
  - #D8B260 at 0
  - #BC6F4C at 0.30
  - #893A50 at 0.60
  - #341D5E at 0.84
  - #080808 at 0.95–0.972
  - #BF15B7 at 0.994–1
- **Field:** heat and age fields at a quarter of the viewport's CSS size on each axis, minimum 360 × 225. Half-float targets, falling back to 8-bit with a 4-tap bilinear sample in the shader. In the 8-bit fallback, age is stored over 0–2 s. Canvas DPR is capped at 2. The body edge, the cut and the cel bands are anti-aliased over at least 1 px with `fwidth`.
- **Stop:** a stop is 34 ms without movement (pointer, or scroll on touch). T = 0.25 + 0.75 × c0, where c0 = min(0.58, stroke age). The head coasts to zero at T, and the cut meets it at T. Nothing pauses, and the field clears 60 ms after T.
- **Must not (spec §2.9):**
  - shadows
  - frosted grain, or ripple away from the head
  - paper grain or a halo
  - a round head
  - a frozen or separately fading head
  - a hold after a stop
  - a pop or a jump
  - a dark, print-like pattern
  - a full-card wash
  - a page that needs the ember to render
- **First paint:** the page is complete without the engine. Hosts make their grounds transparent only after the engine calls `onFirstFrame`.
- **Print:** no canvas is printed, and every sheet prints on its own CSS ground.
- **Canvas behaviour:**
  - The canvas never takes pointer events and never causes horizontal scroll.
  - Rendering pauses while `document.hidden`.
  - Rendering idles once the field is empty, and resumes on the next movement.
- **Voice rules** for any new guide copy: complete sentences, no em-dashes, none of the banned words (luxury, premium, elevated, indulge, shop now, discover).
- **Imagery:** the Ember page uses `brand/moodboard-media/R6euaYP.jpg`, which appears nowhere else in the guide. It is never brightened.
- **Commits:** only when Aaron says to. Each task's commit step is staged and ready, but waits for his go.

## Review Focus

1. **A stop mid-curve.** The cut follows the curved path back without re-ageing older trail, and no piece breaks off. Test: `test_stop_on_curve` (Task 2).
2. **Resize while a trail is on screen.** The fields reallocate, the trail clears without errors, and the next movement draws normally. Test: `test_resize_reallocates_field` (Task 2).
3. **A tab hidden mid-stop, then shown again.** On return there is no burst. `dt` is clamped to 0.1 s and the stop completes or clears. Test: `test_hidden_tab_pauses` (Task 2).
4. **Document height changes after load** (late images or fonts). The ground lookup re-bakes so colours stay aligned. Test: `test_ground_rebakes_on_height_change` (Task 2).
5. **WebGL context lost.** The engine disposes itself and the guide restores its CSS grounds. Test: `test_context_lost_restores_ground` (Task 3).

---

### Task 1: The ember maths

**Files:**
- Create: `brand/ember/ember-math.js`
- Create: `brand/ember/ember-math.test.mjs`

**Interfaces:**
- Produces, all named exports:
  - `FALL: Array<[number, string]>`
  - `fallAt(t: number) -> [r, g, b]`, 0–255
  - `fieldSize(cssW: number, cssH: number) -> [w, h]`
  - `decay(perFrame: number, dt: number) -> number`, the value `perFrame ** (dt * 60)`
  - `hot(rgb: [r, g, b], heat: number) -> [r, g, b]`, spec §2.4
  - `stopTime(c0: number) -> number`, the value 0.25 + 0.75 × min(0.58, c0)
  - `coastSpeed(v0: number, t: number, T: number) -> number`, px per frame: `min(v0, 8) × max(0, 1 − t ÷ T)`
  - `cutAge(c0: number, t: number, T: number) -> number`, the value `c0 − t − (c0 ÷ T²) × t²`
  - `capOffset(d: number, speed: number) -> number`, the value `min(0.3, d² ÷ (2 × 0.07 × speed))`
  - `rippleFade(t: number, T: number) -> number`, the value `(1 − min(1, t ÷ T))²`
  - `encodeAge(sec: number) -> number` and `decodeAge(v: number) -> number`, the 8-bit 0–2 s mapping
  - `lightTarget(heat: number, distPx: number) -> number`
  - `easeLight(current: number, target: number) -> number`
  - `emberColour(rgb: [r, g, b]) -> [r, g, b]`, the card and text light colour: luma plus chroma ×2.2, plus 40, clamped

- [ ] **Step 1: Write the failing tests** (`node:test`, `assert`)

```js
test('fallAt hits each stop', () => { assert.deepEqual(fallAt(0), [216,178,96]); assert.deepEqual(fallAt(.6), [137,58,80]); assert.deepEqual(fallAt(.96), [8,8,8]); assert.deepEqual(fallAt(1), [191,21,183]); });
test('fallAt clamps', () => { assert.deepEqual(fallAt(-1), fallAt(0)); assert.deepEqual(fallAt(2), fallAt(1)); });
test('fieldSize is a quarter, at least 360x225', () => { assert.deepEqual(fieldSize(1440,900), [360,225]); assert.deepEqual(fieldSize(1920,1080), [480,270]); assert.deepEqual(fieldSize(390,844), [360,225]); });
test('decay is per second, not per frame', () => { assert.ok(Math.abs(decay(.955, 1/60) - .955) < 1e-9); assert.ok(Math.abs(decay(.955, 1/30) - .955**2) < 1e-9); });
test('stopTime', () => { assert.ok(Math.abs(stopTime(.58) - .685) < 1e-9); assert.ok(Math.abs(stopTime(2) - .685) < 1e-9); assert.ok(Math.abs(stopTime(.2) - .4) < 1e-9); });
test('the cut meets the head at T', () => { const T = stopTime(.58); assert.ok(Math.abs(cutAge(.58, 0, T) - .58) < 1e-9); assert.ok(Math.abs(cutAge(.58, T, T) + T) < 1e-9); });
test('the cut never pauses', () => { const T = stopTime(.58); let prev = Infinity; for (let i = 0; i <= 60; i++) { const c = cutAge(.58, T*i/60, T); assert.ok(c < prev); prev = c; } });
test('the head coasts to zero at T', () => { assert.equal(coastSpeed(20, 0, .685), 8); assert.ok(coastSpeed(4, .3, .685) > 0); assert.equal(coastSpeed(4, .685, .685), 0); });
test('capOffset caps at 0.3', () => { assert.equal(capOffset(0, 1), 0); assert.equal(capOffset(1, .01), .3); });
test('rippleFade', () => { assert.equal(rippleFade(0, .7), 1); assert.equal(rippleFade(.7, .7), 0); assert.ok(Math.abs(rippleFade(.35, .7) - .25) < 1e-9); });
test('8-bit age round-trips to within 8 ms', () => { for (const s of [0, .3, .685, 1, 1.99]) assert.ok(Math.abs(decodeAge(encodeAge(s)) - s) < .008); assert.equal(encodeAge(5), 1); });
test('hot keeps the tail at head intensity', () => { assert.deepEqual(hot([154,76,79], .2), hot([154,76,79], .75)); });
test('lightTarget', () => { assert.equal(lightTarget(1, 0), 1); assert.ok(Math.abs(lightTarget(1, 140) - .65) < 1e-9); assert.equal(lightTarget(0, 0), 0); });
test('easeLight moves 12% of the way', () => { assert.ok(Math.abs(easeLight(0, 1) - .12) < 1e-9); });
```

- [ ] **Step 2: Run them and confirm they fail.** `node --test brand/ember/` should FAIL, because the module isn't found.
- [ ] **Step 3: Implement the exports** with the formulas given in the Interfaces block. `lightTarget` is `min(1, 1.3 × heat ÷ (1 + (d ÷ 140)²))`.
- [ ] **Step 4: Run them and confirm they pass.** `node --test brand/ember/` should PASS, 14 of 14.
- [ ] **Step 5: Commit.** `feat(ember): pure maths for the ember and its stop`

### Task 2: EmberEngine and its bundle

**Files:**
- Create: `brand/ember/ember-engine.js`
- Create: `brand/ember/build.sh`
- Create: `brand/ember/harness.html`
- Create: `tools/test_ember.py`
- Generated (committed): `brand/ember/ember.bundle.js`

**Interfaces:**
- Consumes: Task 1's exports.
- Produces:
  - `new EmberEngine(container: HTMLElement, options)`. Options:
    - `groundAt(t)` returns `[r, g, b]`. Default `fallAt`.
    - `lit: string`, a CSS selector list.
    - `onFirstFrame(): void`
    - `onLost(): void`
  - Methods:
    - `.dispose()`
    - `.rebakeGround()`
  - Read-only for tests:
    - `.fieldW`, `.fieldH`
    - `.renderer`
    - `.paused: boolean`, true while hidden
    - `.idle: boolean`, true once the field is empty
    - `.phase`, one of `'idle' | 'moving' | 'stopping'`
    - `.stopT` (s)
    - `.stopElapsed` (s)
    - `.head: {x, y}` in CSS px
    - `.cutHead: {x, y}`, the screen point the cut has reached (for tests)
  - The bundle sets `window.EmberEngine` and `window.EmberMath`.
- On every element matched by `lit`, the engine sets these CSS variables. Hosts style them.

| Variable | Value |
|---|---|
| `--li` | 0–1 |
| `--px`, `--py` | Ember position relative to the element, in px |
| `--rr` | `156 + 156 × heat` px |
| `--tx`, `--ty` | Text-shadow offset, 1.5 px toward the ember |
| `--ec` | `"r,g,b"` |

- [ ] **Step 1: Write the harness and the failing checks.**
  - **`harness.html`:** a 500vh page with nine `.card` elements and text. It loads `ember.bundle.js` with a classic `<script>`. It runs `new EmberEngine(el, {lit: '.card, h1, h2, .copy', onFirstFrame: () => document.documentElement.classList.add('ember-on')})`. Its lit-element CSS is ported from reference v23 (the 2 px rim, the inner wash and the 24 px outer glow).
  - **`tools/test_ember.py`:** like `check_b1.py`, it prints one line per failure and exits 1. Viewports are 1440 × 900, 768 × 1024 and 390 × 844. It checks:
    1. The canvas exists, and has `pointer-events: none`.
    2. There is no horizontal scroll.
    3. There are no console errors.
    4. At 1440, `fieldW, fieldH == 360, 225`.
    5. After a 40-step sweep, the canvas under the sweep differs from the ground there by at least 40 in some channel.
    6. `test_stop_frame_by_frame` (spec §5): sweep at a fixed speed, stop, and sample `phase`, `head`, `cutHead` and `stopElapsed` every frame.
       - `phase` becomes `'stopping'` within 34 ms ± one frame.
       - `head` moves every frame until `stopElapsed ≥ stopT`.
       - `cutHead` advances every frame.
       - The distance between `head` and `cutHead` is under 2 px at T.
       - `idle` is true by T + 60 ms plus one frame.
    7. `test_stop_on_curve`: run a semicircular sweep, then stop. The check in 6 still holds. Screenshot the canvas every frame of the stop. No lit pixel (more than 40 from the ground) appears at a point the cut has already passed.
    8. With `--force-prefers-reduced-motion`, two screenshots 500 ms apart match after a sweep.
    9. `test_touch_scroll_stop`: in a mobile context with `hasTouch`, scrolling with the wheel sets `phase` to `'moving'`, and ending the scroll moves it to `'stopping'` and then `'idle'`.
    10. `test_idle_stops_rendering`: once `idle` is true, `renderer.info.render.frame` holds still for 500 ms. The next pointer move advances it.
    11. With JavaScript disabled, the harness `<main>` is visible and `ember-on` is absent.
    12. `test_resize_reallocates_field`: resizing 1440 → 1920 gives a field of 480 × 270 with no error.
    13. `test_hidden_tab_pauses`: a `visibilitychange` event with `hidden` sets `.paused`. Showing the tab clears it, and the first frame back uses `dt ≤ 0.1`.
    14. `test_ground_rebakes_on_height_change`: appending 1000 px to the body calls `rebakeGround` within 1 s.
    15. `test_dpr_cap`: at `deviceScaleFactor: 3`, the canvas width is 2 × innerWidth.
    16. `test_card_rim_lit`: moving near a card's corner raises its `--li` above 0.5 within 400 ms.
    17. `test_8bit_fallback`: forcing the fallback (option `forceByteTargets: true`) still passes check 6.
- [ ] **Step 2: Run it and confirm it fails.** `python3 tools/test_ember.py` should FAIL, because the bundle is missing.
- [ ] **Step 3: Implement `EmberEngine` in `ember-engine.js`.**
  - **Structure:** keep `StylizedShadowEngine`'s method names (`init`, `setupListeners`, `onWindowResize`, `animate`, `dispose`, `getFragmentShader`).
  - **Port from v23:**
    - the heat pass: head and tail layers with segment splats and the decays in spec §2.2, held during a stop and cleared after it
    - the age pass: r is seconds since passed, interpolated along each segment; g is distance from the centre line; b is speed. It is written within dot(d, d) < 0.0066, and only ahead of the segment start.
    - the stop: detection after 34 ms; T from `stopTime`; the head coasts with `coastSpeed` along its last direction, still writing heat and age; the cut from `cutAge`, with the cap from `capOffset` and the needle as in v23
    - the display pass:
      - the lava-lamp surface (§2.5)
      - the silhouette from screen distance
      - the marker outline capped at 5 px
      - cel bands anti-aliased with `fwidth`
      - the ripple at the head, faded with `rippleFade` (§2.6)
      - lit elements (§2.7), using `lightTarget`, `easeLight` and `emberColour`
  - **New relative to v23:**
    - the ground comes from a 1 × 2048 `DataTexture` baked from `groundAt`
    - `rebakeGround` runs on a `ResizeObserver` height change
    - the fields are sized by `fieldSize` and reallocated on resize
    - an 8-bit fallback uses `encodeAge` and a 4-tap bilinear sample
    - DPR capped at 2
    - `visibilitychange` pause
    - idle once the field is empty
    - on touch (`pointer: coarse`), scroll speed drives heat and the end of scrolling triggers the stop
    - `webglcontextlost` calls `onLost` and then `dispose`
    - creation is wrapped in try/catch, so with no WebGL nothing is appended and `onLost` is called
- [ ] **Step 4: Bundle it.** `build.sh` runs `npx --yes esbuild@0.24.0 brand/ember/ember-engine.js --bundle --format=iife --global-name=EmberBundle --minify --outfile=brand/ember/ember.bundle.js`, with `three` resolved from `npm i --no-save three@0.160.0` in a temp directory. It should print the bundle size, under 200 KB compressed.
- [ ] **Step 5: Run the checks and confirm they pass.** `node --test brand/ember/ && python3 tools/test_ember.py` should print `PASS`.
- [ ] **Step 6: Commit.** `feat(ember): EmberEngine on Three.js, bundled for file:// and Shopify`

### Task 3: The ember in the brand guide, with option 1 wiring

**Files:**
- Modify: `tools/density_b_family.py`. The B1 branch and `POLISH_CSS` are touched. The script is inlined, so the deck stays a single file.
- Modify: `tools/check_b1.py`
- Generated: `brand/2026-10-10-density-b1-column.html`

**Interfaces:**
- Consumes: `brand/ember/ember.bundle.js`, read and inlined.
- Consumes the `EmberEngine` options from Task 2.
- Produces: `guideGroundAt(t)` in the deck.
  - It walks `.sheet` elements and any nested `[data-ground]` element and, for the innermost one (smallest height) containing document y = t × scrollHeight, interpolates the two hex stops of its inline `linear-gradient(180deg, A, B)` ground.
  - Sheets without a parsable gradient use #080808. The voice sheet's magenta end is parsed as its last stop.

- [ ] **Step 1: Add the failing checks to `check_b1.py`.**
  - There is one `<canvas>` under `#ember`.
  - `ember-on` is on `<html>` after load.
  - With `ember-on` set, every `.sheet` except the cover computes `background-color: rgba(0, 0, 0, 0)` and `background-image: none`.
  - `test_context_lost_restores_ground`: calling `renderer.forceContextLoss()` removes `ember-on`, and sheet 2's background image becomes a gradient again.
  - With JavaScript disabled, the existing desktop height and overflow checks still pass, and the sheets keep their grounds.
  - `test_print_grounds`: emulating print media with `ember-on` set, `#ember` is not displayed and sheet 2 shows its gradient.
- [ ] **Step 2: Run it and confirm it fails.** `python3 tools/density_b_family.py && python3 tools/check_b1.py` should FAIL on the ember lines.
- [ ] **Step 3: Implement.**
  - Inline the bundle and an `#ember` fixed container behind the sheets.
  - Add `.ember-on .sheet:not(.bcover){background:transparent!important}`. The cover keeps its photo, so the ember shows from sheet 2 on.
  - Add a print rule: hide `#ember` and restore each sheet's gradient.
  - Lit selector: `.panel, .wtile, .pcard, .plabel, .pposter, h2.t, .lead, .stagename, .adbig, .vbig`. Lit-element CSS is as in the harness.
  - Engine options: `groundAt: guideGroundAt`, `onFirstFrame` adds `ember-on`, and `onLost` removes it.
- [ ] **Step 4: Run the checks and confirm they pass.** `python3 tools/density_b_family.py && python3 tools/check_b1.py` should print `PASS`.
- [ ] **Step 5: Commit.** `feat(guide): the ember behind every sheet`

### Task 4: The Ember page and the rule changes

**Files:**
- Modify: `tools/density_b_family.py`. Add an `ember_page(pg, style, ink)` builder, the page's CSS in `POLISH_CSS`, the R6euaYP image, and `n_fall` 12 → 13.
- Modify: `tools/check_b1.py`, for the sheet count and the per-sheet expectations
- Generated: `brand/2026-10-10-density-b1-column.html`

**Interfaces:**
- Consumes: Task 3's deck.
- Produces: 15 sheets, with 13 on the fall. Pages 01–11 are unchanged: the cover, five system pages, art direction 07, and the stages 08–11. Ember is page 12, on fall slice 11 of 13 (#321C5B → #1D1231). Use and misuse becomes 13, Digital and print 14, and Voice 15.

- [ ] **Step 1: Add the failing checks.**
  - The sheet count is 15.
  - Sheet 12 has an h2 of `The ember`, and its inline ground is `linear-gradient(180deg,#321C5B,#1D1231)`.
  - These strings exist verbatim:
    - "Move, and it lights. Stop, and in 0.7 seconds it goes out."
    - "#321C5B → #5304E4"
    - "Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render."
    - "The light only brightens where the ember is."
    - "Hover, focus and active states still deepen and never lighten."
    - "The ember is the one exception"
  - The old rule text "No state change brightens." is gone.
  - "page 03" and "page 07" still appear.
  - R6euaYP appears once in the deck.
  - At 1440, every desktop sheet is 820 tall. At 390, there's no overflow. On sheet 12 at 390, the label line's three parts are stacked: their tops strictly increase.
- [ ] **Step 2: Run it and confirm it fails.** `python3 tools/check_b1.py` should FAIL.
- [ ] **Step 3: Implement.**
  - **The Ember page (spec §4.1):** port A′ from the page mockup, with its copy as written in §4.1:
    - the title column: title, two leads, the photograph, the Never line
    - the field: the wordmark, and the label line at its foot
  - **Lit selector:** add `.fwm2` and `.tri span` to the guide's lit selector.
  - **Responsive:** follow the table in §4.1, with the guide's 992 and 576 breakpoints.
  - **The rule changes in spec §4:**
    - page 06's one rule
    - the art direction mention
    - the Digital and print hover note
    - a chroma line on page 03
  - **Housekeeping:** update the CSS comments that name pages 12 and 13 to the new numbers.
- [ ] **Step 4: Run the checks and confirm they pass.** `python3 tools/density_b_family.py && python3 tools/check_b1.py` should print `PASS`. Screenshot sheets 3, 6, 12 and 14 at 1440 and 390, and look at them.
- [ ] **Step 5: Commit.** `feat(guide): the Ember page and the rule that makes room for it`

### Task 5: The ember on the Shopify homepage (deferred; not in today's scope)

**Files:**
- Create: `afterglow/snippets/ember.liquid`
- Create: `afterglow/assets/ember.bundle.js`, a copy of the Task 2 output, written by `build.sh`
- Modify: `afterglow/layout/theme.liquid`, adding `{% render 'ember' %}` before `</body>`
- Modify: `afterglow/snippets/css-variables.liquid`, adding `--fall` to `:root` and setting `body` to `background: #080808 var(--fall) no-repeat; background-size: 100% 100%; min-height: 100%`

**Interfaces:**
- Consumes: `window.EmberEngine` with default `groundAt` (`fallAt`).
- Lit selector: `.product-card, h1, h2, .rte p, .price`. Lit-element CSS is as in the harness, inside the snippet's `{% style %}`.

- [ ] **Step 1: Add a failing check.** `tools/test_ember.py --theme` renders `afterglow/snippets/ember.liquid` with its Liquid tags stripped inside the harness, and asserts:
  - the loader injects the bundle only after the `load` event, so it never sits in the critical path
  - `ember-on` is set after the first frame
  - `body` keeps its fall ground until then
- [ ] **Step 2: Run it and confirm it fails.** `python3 tools/test_ember.py --theme` should FAIL.
- [ ] **Step 3: Implement the snippet.**
  - **Container:** `<div id="ember" aria-hidden="true">` with `position: fixed`, `inset: 0`, `z-index: 0` and `pointer-events: none`.
  - **Stacking:** `main` and the header and footer containers get `position: relative; z-index: 1`.
  - **Deferred loader:**
    - on `load`, it checks `!!document.createElement('canvas').getContext('webgl2')`
    - if that passes, it appends `<script src="{{ 'ember.bundle.js' | asset_url }}" defer>`
    - on that script's load, it starts the engine
  - **Ground:** `onFirstFrame` sets `ember-on`, which makes the body background transparent. `onLost` removes it.
- [ ] **Step 4: Verify.**
  - `python3 tools/test_ember.py --theme` should PASS.
  - `shopify theme check --path afterglow` should report 0 errors.
- [ ] **Step 5: Commit.** `feat(theme): the ember behind the homepage`

### Task 6: Prove it

- [ ] **Automated checks.** Run `node --test brand/ember/ && python3 tools/test_ember.py && python3 tools/check_b1.py`. Every one should print PASS.
- [ ] **Pixelation check (spec §2.8).** Screenshot the harness at 1440 and 1920 with `deviceScaleFactor: 2`, and at 390 with `deviceScaleFactor: 3`, mid-sweep. Crop the head, the tail tip, the outline, the cut and the cel bands, including the last frames of a stop, and look for stair-steps. If any appear, fix them before handing over.
- [ ] **Blind check.** Have a cold critic compare the built page 12 with the pinned Bob Beauté and Frame.io captures, with labels stripped. Report the verdict as it comes back.
- [ ] **Hand over.** Open the deck and the harness for Aaron to judge the look and timing on his GPU. The ember's mid-motion fins are a known open item, set aside by Aaron.
- [ ] **Shopify push.** Pushing the theme to the store needs Aaron's go. It's an action on his account.
