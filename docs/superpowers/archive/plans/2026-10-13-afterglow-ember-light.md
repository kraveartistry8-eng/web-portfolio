# Afterglow Ember Light Revision: Implementation Plan

> **Abandoned, 13 Oct 2026.** Aaron: the build "looks and behaves nothing like what we prototyped". The hour-lite guide was reverted to v23. Why it failed: the prototype's look comes from light multiplied by the page's own pixels across the whole trail, but this design split it into a faint WebGL ground plus per-element CSS gradients at the cursor only, so surfaces never carried the trail. The prototype's numbers were carried into that different model, a brightness cap the prototype never had was added and bent the look, and no blind side-by-side against the prototype was run before building. The feature-design workflow is being rerun from Step 1. This file is a record, not a spec to build from. The code is archived outside the repo.


> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v23 "cartoon" ember with a short warm light that cools down the fall as it fades. It shows on surfaces (type, photograph edges, boxes) and only faintly on the ground, and its head glides to rest after a stop.

**Isolation (Aaron, 13 Oct): the older builds must not change.** The light revision is a new, separate engine in `brand/ember/light/`, with its own maths, tests, build script and bundle. Only `build_lite()` (the hour-lite guide, `brand/2026-10-12-guide-hour-lite.html`) swaps it in, replacing the v23 bundle and CSS in its own output. `brand/ember/*` (the current engine and bundle), `brand/ember/v23/`, `tools/density_b_family.py`, `tools/check_b1.py` and every older guide file stay byte-for-byte as they are.

**Architecture:** WebGL stays (Three.js 0.160.0, the same `EmberEngine` shape and guide wiring). The heat field and its sim pass are removed. The existing **age field** already records, per texel, the seconds since the light passed, the distance from the path and the speed, so it becomes the one field. The display shader draws the ground plus the faint light from it analytically. Surfaces are lit in CSS, from per-element variables that `lightElements()` writes, because the canvas sits behind the HTML.

**Tech Stack:** Three.js 0.160.0 bundled with esbuild (`brand/ember/build.sh`), GLSL ES 1.0, `node --test` for the maths, and Python 3 plus Playwright for the guide build and checks.

**Spec:** [docs/superpowers/specs/2026-10-13-afterglow-ember-light-design.md](../specs/2026-10-13-afterglow-ember-light-design.md). **Reference prototype:** `brand/ember-directions/a2-family.html`, button `c3`. Serve it with `python3 -m http.server 8765` from the repo root.

**No commits.** Aaron commits only when he says. Every "Checkpoint" step below means stop and show the state; it does not mean `git commit`.

---

## File map

| File | Responsibility | Change |
|---|---|---|
| `brand/ember/light/ember-light-math.js` | Pure maths: radius, strength, colour, glide, element light, size scale | Create |
| `brand/ember/light/ember-light-math.test.mjs` | Tests for the maths | Create |
| `brand/ember/light/ember-light.js` | The engine: input, glide, age pass, display shader, element light | Create (full file in Task 3) |
| `brand/ember/light/build.sh` | Bundles the engine and Three.js 0.160.0 into `ember-light.bundle.js` | Create |
| `brand/ember/light/ember-light.bundle.js` | Built output; sets `window.EmberEngine` | Built |
| `tools/afterglow_specimen.py` | `build_lite()`: swaps the v23 bundle and CSS for the light ones; light CSS, `COPY` edits | Modify |
| `tools/check_ember_light.py` | Browser checks of the light revision on the hour-lite guide | Create |
| `brand/ember/*.js`, `brand/ember/harness.html`, `tools/density_b_family.py`, `tools/check_b1.py`, older guide HTML | The current v23 engine and older builds | **Untouched** (Task 1 baseline, Task 8 proof) |
| `brand/ember/v23/` | Frozen v23 | **Untouched** |

---

## Chunk 1: The maths (TDD)

### Task 1: Baseline the files that must not change

**Files:** read only

- [ ] **Step 1:** Record checksums of everything the older builds use or produce:

```bash
shasum brand/ember/*.js brand/ember/*.mjs brand/ember/*.sh brand/ember/harness.html tools/density_b_family.py tools/check_b1.py \
  brand/2026-10-10-density-b1-column.html brand/2026-10-11-guide-the-hour.html $(find brand/ember/v23 -type f) > "$TMPDIR/ember-baseline.sha"
wc -l "$TMPDIR/ember-baseline.sha"
```

Expected: one line per file. Task 8 checks them again. No step in this plan edits any of these files. If a step seems to need to, **stop and ask**.

### Task 2: New maths functions

**Files:**
- Create: `brand/ember/light/ember-light-math.js` (start from a copy of `brand/ember/ember-math.js`; the original is not edited)
- Create: `brand/ember/light/ember-light-math.test.mjs`

- [ ] **Step 0: Copy the maths.** Run `mkdir -p brand/ember/light && cp brand/ember/ember-math.js brand/ember/light/ember-light-math.js`.

- [ ] **Step 1: Write the test file** `brand/ember/light/ember-light-math.test.mjs` with the following. It keeps the tests for functions that stay (`fallAt`, `fieldSize`, the 8-bit age codec and `easeLight`) and adds the new ones. Expected values come from the prototype's code and from spec §3.

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fallAt, fieldSize, encodeAge, decodeAge, easeLight, STAGES,
         touchRadius, touchStrength, profile, freshColour, cooledColour,
         glideStart, glideSpeed, glideDistance, lightTarget } from './ember-light-math.js';

const near = (a, b, tol = 1e-9) => Math.abs(a - b) <= tol;

test('fallAt hits each stop', () => { assert.deepEqual(fallAt(0), [216,178,96]); assert.deepEqual(fallAt(.6), [137,58,80]); assert.deepEqual(fallAt(.96), [8,8,8]); assert.deepEqual(fallAt(1), [191,21,183]); });
test('fallAt clamps', () => { assert.deepEqual(fallAt(-1), fallAt(0)); assert.deepEqual(fallAt(2), fallAt(1)); });
test('fieldSize is a quarter, at least 360x225 (225x360 in portrait)', () => { assert.deepEqual(fieldSize(1440,900), [360,225]); assert.deepEqual(fieldSize(1920,1080), [480,270]); assert.deepEqual(fieldSize(390,844), [225,360]); });
test('8-bit age round-trips to within 8 ms', () => { for (const s of [0, .3, .9, 1.99]) assert.ok(Math.abs(decodeAge(encodeAge(s)) - s) < .008); assert.equal(encodeAge(5), 1); });
test('easeLight moves 12% of the way', () => { assert.ok(near(easeLight(0, 1), .12)); });

// §3.1 a touch of light
test('touchRadius: 52 + 40 x speed, speed capped at 1.5, growing to 1.25x over its life', () => {
  assert.equal(touchRadius(0), 52); assert.equal(touchRadius(1.5), 112); assert.equal(touchRadius(5), 112);
  assert.equal(touchRadius(0, 1), 65); assert.equal(touchRadius(1.5, 1), 140); assert.equal(touchRadius(-1), 52);
});
test('touchStrength: 0.42 x (1 - age)^1.3, nothing at the end of its life', () => {
  assert.ok(near(touchStrength(0), .42)); assert.equal(touchStrength(1), 0); assert.equal(touchStrength(2), 0);
  assert.ok(near(touchStrength(.5), .42 * .5 ** 1.3)); assert.ok(near(touchStrength(.5, 1), .5 ** 1.3));
});
test('profile: 1 at the centre, 0.4 at half the radius, 0 at the radius', () => {
  assert.equal(profile(0), 1); assert.ok(near(profile(.5), .4)); assert.equal(profile(1), 0); assert.equal(profile(2), 0); assert.ok(near(profile(.25), .7));
});

// §3.3 colour
test('freshColour: 35% toward gold, chroma x1.5, lifted on dark grounds only', () => {
  assert.deepEqual(freshColour([137,58,80]), [218,111,87]);    // rose ground (dark): #DA6F57
  assert.deepEqual(freshColour([216,178,96]), [234,177,54]);   // gold ground (light, luma > 140): not lifted
  assert.deepEqual(freshColour([52,29,94]), [140,93,116]);     // deep violet ground
});
test('cooledColour: fresh at 0, deep violet at the end, fully cooled by 1/1.4 of its life', () => {
  const f = freshColour([137,58,80]);
  assert.deepEqual(cooledColour(f, 0), f);
  assert.deepEqual(cooledColour(f, 1), STAGES[3]);
  const a = 1 / 1.4, k = a * 3 - 2, want = STAGES[2].map((v, i) => Math.round(v + (STAGES[3][i] - v) * k));
  assert.deepEqual(cooledColour(f, a), want);
});

// §3.2 the glide
test('glideStart: no glide under 0.02 px/ms, capped at 0.6', () => { assert.equal(glideStart(.01), 0); assert.equal(glideStart(.3), .3); assert.equal(glideStart(2), .6); });
test('glideSpeed falls to zero at T with no step: each drop smaller than the last', () => {
  assert.equal(glideSpeed(.6, 0), .6); assert.equal(glideSpeed(.6, .32), 0); assert.equal(glideSpeed(.6, 1), 0);
  let prev = glideSpeed(.6, 0), lastDrop = Infinity;
  for (let i = 1; i <= 20; i++) { const v = glideSpeed(.6, .32 * i / 20), drop = prev - v; assert.ok(drop > 0 && drop < lastDrop + 1e-12); lastDrop = drop; prev = v; }
});
test('glideDistance: v0 x T / 3 at rest, about 64 px at the cap', () => {
  assert.equal(glideDistance(.6, 0), 0); assert.ok(near(glideDistance(.6, .32), 64, 1e-9)); assert.ok(near(glideDistance(.6, 5), 64, 1e-9));
});

// §3.4 element light
test('lightTarget: the profile over twice a still touch radius', () => {
  assert.equal(lightTarget(0), 1); assert.ok(near(lightTarget(52), .4)); assert.equal(lightTarget(104), 0); assert.ok(lightTarget(104, 1.5) > 0);
});
```

- [ ] **Step 2: Run the tests to watch them fail.** Run `node --test brand/ember/light/ember-light-math.test.mjs`. Expected: FAIL, because the import of `touchRadius` (and the other new names) fails.

- [ ] **Step 3: Edit `brand/ember/light/ember-light-math.js`** (the copy). Keep `FALL`, `rgb`, `luma`, `clamp255`, `fallAt`, `fieldSize`, `encodeAge`, `decodeAge` and `easeLight` as they are. **Delete** `decay`, `hot`, `stopTime`, `coastSpeed`, `cutAge`, `capOffset`, `rippleFade`, the old `lightTarget`, `emberColour`, and the whole OKLab block (`toLin`, `toSrgb`, `toLab`, `fromLab`, `oklch`, `lift`, `emberColourMatched`). Update the header comment to name the new spec. Then append:

```js
// ---- the light revision (spec 2026-10-13-afterglow-ember-light-design.md) ----
export const STAGES = [[216,178,96], [188,111,76], [137,58,80], [52,29,94]];   // gold, after gold, rose, deep violet
const GOLD = STAGES[0], clamp01 = v => Math.min(1, Math.max(0, v));
const mixc = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

// §3.1: a touch's radius in px, from the speed it was laid at (px per ms) and its age (0 to 1 over its life)
export const touchRadius = (speed, age = 0) => (52 + 40 * Math.min(1.5, Math.max(0, speed))) * (1 + .25 * clamp01(age));
// §3.1: its strength; pass 1 as strength for the bare fade curve
export const touchStrength = (age, strength = .42) => age >= 1 ? 0 : strength * (1 - Math.max(0, age)) ** 1.3;
// §3.1: radial, 1 at the centre, 0.4 at half the radius, 0 at the radius (x is distance over radius)
export const profile = x => x <= 0 ? 1 : x < .5 ? 1 - 1.2 * x : x < 1 ? .4 * (1 - (x - .5) * 2) : 0;

// §3.3: the fresh colour: 35% toward gold, chroma x1.5, and on dark grounds (luma 140 or under) x1.1 + 8
export function freshColour(c) {
  let m = mixc(c, GOLD, .35); const l = luma(m); m = m.map(v => l + (v - l) * 1.5);
  if (luma(c) <= 140) m = m.map(v => v * 1.1 + 8);
  return m.map(v => Math.round(clamp255(v)));
}
// §3.3: down the fall in equal thirds of its life, fully cooled by 1/1.4 of it
export function cooledColour(fresh, age) {
  const a = clamp01(age), k = Math.min(2.999, a * 3), j = Math.floor(k);
  return mixc(fresh, mixc(STAGES[j], STAGES[j + 1], k - j), Math.min(1, 1.4 * a)).map(v => Math.round(clamp255(v)));
}

// §3.2: the glide. Speeds in px per ms, times in seconds.
export const glideStart = (v, max = .6) => v < .02 ? 0 : Math.min(max, v);
export const glideSpeed = (v0, t, T = .32) => t >= T ? 0 : v0 * (1 - Math.max(0, t) / T) ** 2;
export const glideDistance = (v0, t, T = .32) => v0 * 1000 * T / 3 * (1 - (1 - Math.min(1, Math.max(0, t) / T)) ** 3);

// §3.4: how strongly an element is lit, from its distance to the light; it reaches twice a still touch's radius
export const lightTarget = (distPx, speed = 0) => profile(distPx / (2 * touchRadius(speed)));
```

- [ ] **Step 4: Run the tests to watch them pass.** Run `node --test brand/ember/light/ember-light-math.test.mjs`. Expected: every test passes, 0 fail.

- [ ] **Step 5: Checkpoint.** Show the test output. No commit.

---

## Chunk 2: The engine

### Task 3: The light engine

**Files:**
- Create: `brand/ember/light/ember-light.js`
- Create: `brand/ember/light/build.sh`

The shape stays as it was: constructor, init, setupListeners, makeTargets, onWindowResize, rebakeGround, groundRGB, collectLit, wake, tick, animate, lightElements, lose, dispose and getFragmentShader. The bodies change.

- [ ] **Step 1: Write `brand/ember/light/ember-light.js`** with exactly this content:

```js
import {
  WebGLRenderer, Scene, OrthographicCamera, Mesh, PlaneGeometry, ShaderMaterial, Vector2,
  WebGLRenderTarget, DataTexture, HalfFloatType, UnsignedByteType, LinearFilter, NearestFilter, RGBAFormat, Color,
} from "three";
import * as EmberMath from "./ember-light-math.js";
import { fallAt, fieldSize, touchRadius, touchStrength, freshColour, cooledColour, glideStart, glideDistance, lightTarget, easeLight } from "./ember-light-math.js";

const GROUND_N = 2048;
const REACH_PX = 140;   // the widest a touch grows: (52 + 40 x 1.5) x 1.25 (spec §3.1)

/**
 * EmberEngine, light revision: a short warm light that cools down the fall as it fades, shown on surfaces (CSS, from
 * the variables lightElements writes) and faintly on the ground (this canvas). The head glides to rest after a stop.
 * Spec: docs/superpowers/specs/2026-10-13-afterglow-ember-light-design.md. v23 is frozen in brand/ember/v23/.
 */
export class EmberEngine {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      groundAt: fallAt,        // the page's colour from top (0) to bottom (1)
      lit: "",                 // what catches the light
      photos: "",              // which of those are photographs: lit only at the edge facing the light (§3.4)
      onFirstFrame: () => {},
      onLost: () => {},
      onFrame: null,
      forceByteTargets: false,
      stopDetect: .034,        // seconds without movement that count as a stop
      glideMax: .6,            // px per ms: the fastest a glide starts
      glideTime: .32,          // seconds to come to rest
      life: .9,                // seconds a touch of light lasts
      strength: .42,           // a touch's strength when fresh
      groundGain: .06,         // the ground's share of the light (spec §3.4: tuned by eye)
      ...options,
    };
    this.onFrame = this.options.onFrame;
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.coarse = matchMedia("(pointer: coarse)").matches;
    this.phase = "idle"; this.idle = true; this.paused = false; this.glide = null; this.lastWrite = -1e9;
    this.raf = 0; this.dirty = true; this.drawn = false; this.disposed = false;
    try {
      this.init();
    } catch (err) {
      // no WebGL, or the engine throws: nothing is added and the page is unchanged
      console.warn("ember: not started", err);
      this.failed = true;
      if (this.renderer) { this.renderer.domElement.remove(); this.renderer.dispose(); }
      this.options.onLost();
    }
  }

  init() {
    this.W = this.container.clientWidth || innerWidth; this.H = this.container.clientHeight || innerHeight;
    const cv = document.createElement("canvas"), attrs = { antialias: false, alpha: false, depth: false, stencil: false, powerPreference: "low-power" };
    const gl = cv.getContext("webgl2", attrs) || cv.getContext("webgl", attrs);
    if (!gl) throw new Error("no WebGL");
    this.renderer = new WebGLRenderer({ canvas: cv, context: gl });
    const caps = this.renderer.capabilities, ext = this.renderer.extensions;
    this.byteTargets = this.options.forceByteTargets ||
      !(caps.isWebGL2 ? (ext.has("EXT_color_buffer_float") || ext.has("EXT_color_buffer_half_float"))
                      : (ext.has("OES_texture_half_float") && ext.has("OES_texture_half_float_linear") && ext.has("EXT_color_buffer_half_float")));
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(this.W, this.H, false);
    cv.style.cssText = "display:block;width:100%;height:100%;pointer-events:none";
    cv.setAttribute("aria-hidden", "true");
    this.scene = new Scene();
    this.camera = new OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.E = { x: this.W / 2, y: this.H * .6, vx: 0, vy: 0, moved: 0, stepped: false, lastMove: -1e9, known: false };

    const vs = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position, 1.0); }`;
    const geo = new PlaneGeometry(2, 2), pre = this.byteTargets ? "#define BYTE_AGE 1\n" : "";
    this.ageSim = new ShaderMaterial({
      uniforms: { uAge: { value: null }, uPos: { value: new Vector2() }, uPrev: { value: new Vector2() }, uAmt: { value: 0 },
                  uAsp: { value: 1 }, uDt: { value: 0 }, uReach: { value: .02 }, uFieldSize: { value: new Vector2(1, 1) } },
      vertexShader: vs, fragmentShader: pre + AGE_GLSL + AGE_SIM_GLSL });
    const o = this.options;
    this.material = new ShaderMaterial({
      uniforms: { uAge: { value: null }, uGround: { value: null }, uScroll: { value: 0 }, uVh: { value: this.H }, uDoc: { value: 1 },
                  uAsp: { value: 1 }, uH: { value: this.H }, uLife: { value: o.life }, uStrength: { value: o.strength },
                  uGain: { value: o.groundGain }, uReduced: { value: 0 }, uHead: { value: new Vector2(.5, .5) },
                  uFieldSize: { value: new Vector2(1, 1) } },
      vertexShader: vs, fragmentShader: pre + this.getFragmentShader() });
    this.ageScene = new Scene(); this.ageScene.add(new Mesh(geo, this.ageSim));
    this.scene.add(new Mesh(geo, this.material));
    this.makeTargets();
    this.rebakeGround();
    this.collectLit();
    this.container.appendChild(cv);
    this.setupListeners();
    this.wake();
  }

  setupListeners() {
    const E = this.E, on = (t, ev, fn, o = { passive: true }) => { t.addEventListener(ev, fn, o); this.off.push(() => t.removeEventListener(ev, fn, o)); };
    this.off = [];
    let lx = null, ly = null, ls = scrollY;
    const moveTo = (x, y) => {
      if (lx !== null) E.moved += Math.hypot(x - lx, y - ly);
      lx = E.x = x; ly = E.y = y; E.known = true; if (this.reduced) this.dirty = true; this.wake();
    };
    on(window, "resize", () => this.onWindowResize());
    on(window, "pointermove", e => { if (e.pointerType !== "touch") moveTo(e.clientX, e.clientY); });
    // touch (§3.6): the light follows the finger while it moves, and stands at the touch point while the page scrolls
    on(window, "touchstart", e => { const t = e.touches[0]; if (t) { lx = E.x = t.clientX; ly = E.y = t.clientY; E.known = true; } });
    on(window, "touchmove", e => { const t = e.touches[0]; if (t) moveTo(t.clientX, t.clientY); });
    on(window, "scroll", () => {
      const d = scrollY - ls; ls = scrollY;
      if (this.coarse) { E.moved += Math.abs(d) * .8; E.known = true; }
      this.dirty = true; this.wake();
    });
    on(document, "visibilitychange", () => {
      this.paused = document.hidden;
      if (this.paused) { cancelAnimationFrame(this.raf); this.raf = 0; } else { this.dirty = true; this.wake(); }
    });
    if (window.ResizeObserver) {
      let h = document.documentElement.scrollHeight;
      this.ro = new ResizeObserver(() => { const n = document.documentElement.scrollHeight; if (n !== h) { h = n; this.rebakeGround(); this.collectLit(); } });
      this.ro.observe(document.body); this.ro.observe(document.documentElement);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { if (!this.disposed) this.collectLit(); });
    this.renderer.domElement.addEventListener("webglcontextlost", e => { e.preventDefault(); this.lose(); }, false);
  }

  // the age field (the one field): a quarter of the viewport on each axis, at least 360 x 225 (v23 spec §2.8)
  makeTargets() {
    [this.agA, this.agB].forEach(t => t && t.dispose());
    const [W, H] = fieldSize(this.W, this.H), byte = this.byteTargets;
    this.fieldW = W; this.fieldH = H;
    const rt = () => new WebGLRenderTarget(W, H, { type: byte ? UnsignedByteType : HalfFloatType, format: RGBAFormat,
      minFilter: byte ? NearestFilter : LinearFilter, magFilter: byte ? NearestFilter : LinearFilter, depthBuffer: false, stencilBuffer: false });
    this.agA = rt(); this.agB = rt();
    const r = this.renderer;
    r.setClearColor(new Color(1, 1, 1), 1);           // age starts old: past the light's life, so nothing shows
    [this.agA, this.agB].forEach(t => { r.setRenderTarget(t); r.clear(); });
    r.setRenderTarget(null); r.setClearColor(0x080808, 1);
    this.material.uniforms.uFieldSize.value.set(W, H); this.ageSim.uniforms.uFieldSize.value.set(W, H);
    this.ageSim.uniforms.uReach.value = (REACH_PX / this.H) ** 2;
  }

  onWindowResize() {
    this.W = this.container.clientWidth || innerWidth; this.H = this.container.clientHeight || innerHeight;
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(this.W, this.H, false);
    const [fw, fh] = fieldSize(this.W, this.H);
    if (fw !== this.fieldW || fh !== this.fieldH) this.makeTargets();
    this.ageSim.uniforms.uReach.value = (REACH_PX / this.H) ** 2;
    clearTimeout(this.rebakeT); this.rebakeT = setTimeout(() => { this.rebakeGround(); this.collectLit(); }, 100);
    this.dirty = true; this.wake();
  }

  rebakeGround() {
    const px = new Uint8Array(GROUND_N * 4), at = this.options.groundAt;
    for (let i = 0; i < GROUND_N; i++) { const c = at((i + .5) / GROUND_N); px.set([Math.round(c[0]), Math.round(c[1]), Math.round(c[2]), 255], i * 4); }
    this.groundPx = px;
    if (this.groundTex) this.groundTex.dispose();
    this.groundTex = new DataTexture(px, 1, GROUND_N, RGBAFormat);
    this.groundTex.magFilter = this.groundTex.minFilter = LinearFilter;
    this.groundTex.needsUpdate = true;
    this.material.uniforms.uGround.value = this.groundTex;
    this.dirty = true; this.wake();
  }

  groundRGB(y) {
    const t = (scrollY + y) / document.documentElement.scrollHeight, i = Math.max(0, Math.min(GROUND_N - 1, Math.floor(t * GROUND_N))) * 4;
    return [this.groundPx[i], this.groundPx[i + 1], this.groundPx[i + 2]];
  }

  // what catches the light, where each piece sits, and each text's own colour (kept so unlit text is unchanged).
  // Reads first, then writes, so collecting costs one layout.
  collectLit() {
    const o = this.options;
    this.lit = o.lit ? [...document.querySelectorAll(o.lit)] : [];
    const sx = scrollX, sy = scrollY;
    const read = this.lit.map(el => ({ r: el.getBoundingClientRect(), c: el.hasAttribute("data-lit") ? null : getComputedStyle(el).color }));
    this.litBoxes = read.map(({ r }) => ({ l: r.left + sx, t: r.top + sy, r: r.right + sx, b: r.bottom + sy, w: r.width, h: r.height }));
    this.lit.forEach((el, i) => {
      el._li = el._li || 0; el._photo = !!(o.photos && el.matches(o.photos));
      if (read[i].c) el.style.setProperty("--tc", read[i].c);
    });
  }

  wake() { if (!this.raf && !this.paused && !this.disposed && !this.failed) this.raf = requestAnimationFrame(t => this.tick(t)); }

  tick() {
    this.raf = 0;
    if (this.paused || this.disposed) return;
    if (this.animate()) this.wake();
  }

  // one frame: input and the glide, the age pass, the display pass, the element light. Returns whether to go on.
  animate() {
    const E = this.E, o = this.options, now = performance.now();
    const dt = Math.min(.1, (now - (this.lastT || now)) / 1000) || 1 / 60; this.lastT = now;
    const stepped = E.moved > 0; if (E.moved > 2) E.lastMove = now; E.moved = 0;
    const since = (now - E.lastMove) / 1000, moving = !this.reduced && since < o.stopDetect;
    if (E.cx === undefined) { E.cx = E.x; E.cy = E.y; }
    let fromX = E.cx, fromY = E.cy, write = 0, start = false;

    if (this.reduced) {
      // one still, faint light at the pointer: no trail, no cooling, no glide (§3.6)
      E.cx = E.x; E.cy = E.y; this.phase = "idle";
    } else if (moving) {
      if (this.phase === "moving") {
        // velocity in px per ms, smoothed by half, only from frames where the pointer moved (§3.2)
        if (stepped) { const ms = dt * 1000; E.vx = E.vx * .5 + (E.x - E.cx) / ms * .5; E.vy = E.vy * .5 + (E.y - E.cy) / ms * .5; }
      } else {
        // a new stroke, or a glide interrupted: the light carries on from the pointer, never drawn from where it rested
        start = true; fromX = E.x; fromY = E.y; E.vx = E.vy = 0;
      }
      E.cx = E.x; E.cy = E.y; this.phase = "moving"; this.glide = null; write = 1;
    } else if (this.phase === "moving" || this.phase === "gliding") {
      // the glide (§3.2): on along the last direction, slowing smoothly to rest over glideTime
      if (!this.glide && this.phase === "moving") {
        const v = Math.hypot(E.vx, E.vy), v0 = glideStart(v, o.glideMax);
        this.glide = v0 ? { x: E.cx, y: E.cy, ux: E.vx / v, uy: E.vy / v, v0, t0: now } : null;
      }
      if (this.glide) {
        const G = this.glide, t = (now - G.t0) / 1000, d = glideDistance(G.v0, t, o.glideTime);
        E.cx = G.x + G.ux * d; E.cy = G.y + G.uy * d; write = 1;
        this.phase = t < o.glideTime ? "gliding" : "fading";
      } else this.phase = "fading";
    } else if (this.phase === "fading" && (now - this.lastWrite) / 1000 > o.life) {
      this.phase = "idle";
    }
    if (write) this.lastWrite = now;

    const field = this.phase !== "idle" || (this.reduced && E.known);
    const drew = field || this.dirty || !this.drawn;
    if (drew) {
      const r = this.renderer, asp = this.W / this.H, ag = this.ageSim.uniforms;
      ag.uAge.value = this.agA.texture; ag.uAsp.value = asp; ag.uDt.value = dt;
      ag.uPrev.value.set(fromX / this.W, 1 - fromY / this.H); ag.uPos.value.set(E.cx / this.W, 1 - E.cy / this.H);
      // a zero-length segment writes age over a whole disc; only a stroke's first point may do that
      const segPx = Math.hypot(E.cx - fromX, E.cy - fromY);
      ag.uAmt.value = segPx < .1 && !start ? 0 : write;
      r.setRenderTarget(this.agB); r.render(this.ageScene, this.camera); [this.agA, this.agB] = [this.agB, this.agA];
      const u = this.material.uniforms;
      u.uAge.value = this.agA.texture; u.uScroll.value = scrollY; u.uVh.value = this.H; u.uH.value = this.H;
      u.uDoc.value = document.documentElement.scrollHeight; u.uAsp.value = asp;
      u.uReduced.value = this.reduced && E.known ? 1 : 0; u.uHead.value.set(E.cx / this.W, 1 - E.cy / this.H);
      r.setRenderTarget(null); r.render(this.scene, this.camera);
      this.dirty = false;
      if (!this.drawn) { this.drawn = true; this.options.onFirstFrame(); }
    }
    this.idle = this.phase === "idle";
    const lights = this.lightElements(now);
    if (this.onFrame) this.onFrame(this, drew);
    return !this.idle || lights;
  }

  // light on surfaces (§3.4): an element near the light eases up to it and takes the fresh colour; once the light
  // leaves, it fades along the touch's life and its colour cools down the fall. All reads come before all writes.
  lightElements(now) {
    if (!this.lit.length) return false;
    const t0 = performance.now(), E = this.E, o = this.options, X = E.cx, Y = E.cy, sx = scrollX, sy = scrollY;
    const live = this.phase === "moving" || this.phase === "gliding" || (this.reduced && E.known);
    const speed = Math.min(1.5, Math.hypot(E.vx, E.vy)), fresh = freshColour(this.groundRGB(Y)), R = 2 * touchRadius(speed);
    let active = false;
    for (let i = 0; i < this.lit.length; i++) {
      const el = this.lit[i], B = this.litBoxes[i], s = el.style;
      const r = { left: B.l - sx, top: B.t - sy, right: B.r - sx, bottom: B.b - sy, width: B.w, height: B.h };
      const off = () => { if (el._li) { el._li = 0; el._t = 0; s.setProperty("--li", "0"); el.removeAttribute("data-lit"); } };
      if (r.bottom < -200 || r.top > this.H + 200 || !r.width) { off(); continue; }
      const nx = Math.max(r.left, Math.min(X, r.right)), ny = Math.max(r.top, Math.min(Y, r.bottom));
      const target = live ? lightTarget(Math.hypot(X - nx, Y - ny), speed) * (this.reduced ? .4 : 1) : 0;
      let li = el._li || 0, c;
      if (target > .002 && target >= li) { li = easeLight(li, target); el._t = now; el._peak = li; el._c = fresh; c = fresh; }
      else if (this.reduced) { li = easeLight(li, target); c = el._c || fresh; }
      else {
        const age = el._t ? (now - el._t) / 1000 / o.life : 1;
        li = (el._peak || 0) * touchStrength(age, 1); c = cooledColour(el._c || fresh, age);
      }
      if (li < .002) { off(); continue; }
      active = true; el._li = li;
      s.setProperty("--li", li.toFixed(3)); s.setProperty("--ec", c.join(","));
      s.setProperty("--px", (X - r.left).toFixed(0) + "px"); s.setProperty("--py", (Y - r.top).toFixed(0) + "px");
      s.setProperty("--rr", R.toFixed(0) + "px");
      if (el._photo) {
        // the edge facing the light: the nearest point on the photograph's nearest side
        let ex = nx - r.left, ey = ny - r.top; const m = Math.min(ex, r.width - ex, ey, r.height - ey);
        if (m === ex) ex = 0; else if (m === r.width - ex) ex = r.width; else if (m === ey) ey = 0; else ey = r.height;
        s.setProperty("--ex", ex.toFixed(0) + "px"); s.setProperty("--ey", ey.toFixed(0) + "px");
        s.setProperty("--band", (.18 * Math.min(r.width, r.height)).toFixed(0) + "px");
      }
      if (!el.hasAttribute("data-lit")) el.setAttribute("data-lit", "");
    }
    this.lightMs = performance.now() - t0;
    return active;
  }

  lose() {
    if (this.disposed) return;
    this.options.onLost();
    this.dispose();
  }

  dispose() {
    this.disposed = true;
    cancelAnimationFrame(this.raf); this.raf = 0; clearTimeout(this.rebakeT);
    (this.off || []).forEach(f => f()); if (this.ro) this.ro.disconnect();
    [this.agA, this.agB, this.groundTex].forEach(t => t && t.dispose());
    (this.lit || []).forEach(el => { ["--li", "--px", "--py", "--rr", "--ec", "--ex", "--ey", "--band", "--tc"].forEach(k => el.style.removeProperty(k)); el.removeAttribute("data-lit"); });
    if (this.renderer) { this.renderer.dispose(); this.renderer.domElement.remove(); }
    if (this.scene) this.scene.clear();
  }

  getFragmentShader() { return AGE_GLSL + DISPLAY_GLSL; }
}

// the age field: r is seconds since the light passed (0-2 s packed into r and g on 8-bit targets), b the distance
// from the path's centre line (screen-height units), a the speed when written (screen heights per second)
const AGE_GLSL = `
  uniform vec2 uFieldSize;
  #ifdef BYTE_AGE
  vec3 unpackAge(vec4 t){ return vec3((t.r * 255. * 256. + t.g * 255.) / 65535. * 2., t.b * .4, t.a * 8.); }
  vec4 packAge(vec3 a){ float v = floor(clamp(a.x / 2., 0., 1.) * 65535. + .5);
    return vec4(floor(v / 256.) / 255., mod(v, 256.) / 255., clamp(a.y / .4, 0., 1.), clamp(a.z / 8., 0., 1.)); }
  vec3 ageTexel(sampler2D t, vec2 uv){ return unpackAge(texture2D(t, uv)); }
  vec3 ageAt(sampler2D t, vec2 uv){
    vec2 st = uv * uFieldSize - .5, i = floor(st), f = st - i, px = 1. / uFieldSize;
    vec2 b = (i + .5) * px;
    return mix(mix(ageTexel(t, b), ageTexel(t, b + vec2(px.x, 0.)), f.x),
               mix(ageTexel(t, b + vec2(0., px.y)), ageTexel(t, b + px), f.x), f.y); }
  #else
  vec3 unpackAge(vec4 t){ return t.rgb; }
  vec4 packAge(vec3 a){ return vec4(min(a.x, 30.), a.y, a.z, 1.); }
  vec3 ageTexel(sampler2D t, vec2 uv){ return texture2D(t, uv).rgb; }
  vec3 ageAt(sampler2D t, vec2 uv){ return texture2D(t, uv).rgb; }
  #endif
`;

// age runs smoothly down each frame's segment, written out to the widest a touch can grow (uReach), and only ahead
// of the segment's start, so a path that curves back never re-ages older light
const AGE_SIM_GLSL = `
  uniform sampler2D uAge; uniform vec2 uPos, uPrev; uniform float uAmt, uAsp, uDt, uReach; varying vec2 vUv;
  void main(){ vec3 A = ageTexel(uAge, vUv); float a = A.x + uDt;
    vec2 pa = uPrev, pb = uPos, p = vUv; pa.x *= uAsp; pb.x *= uAsp; p.x *= uAsp; vec2 ab = pb - pa; float len = length(ab);
    float kr = dot(p - pa, ab) / max(len * len, 1e-8), k = clamp(kr, 0., 1.); vec2 d = p - (pa + ab * k);
    if (uAmt > .02 && dot(d, d) < uReach && (kr > 0. || len < 1e-4)) { float na = uDt * (1. - k);
      if (na <= a) { a = na; A.y = length(d); A.z = len / max(uDt, 1e-3); } }
    gl_FragColor = packAge(vec3(a, A.y, A.z)); }`;

// the ground, and the light on it at groundGain of its strength: screened on dark grounds, soft light on light ones;
// never past gold's lightness (OKLab L 0.781) unless the ground was already there
const DISPLAY_GLSL = `
  uniform sampler2D uAge, uGround; uniform float uScroll, uVh, uDoc, uAsp, uH, uLife, uStrength, uGain, uReduced; uniform vec2 uHead; varying vec2 vUv;
  const vec3 S0 = vec3(216., 178., 96.) / 255., S1 = vec3(188., 111., 76.) / 255., S2 = vec3(137., 58., 80.) / 255., S3 = vec3(52., 29., 94.) / 255.;
  float luma(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
  float profile(float x){ return x < .5 ? 1. - 1.2 * max(x, 0.) : max(0., .4 * (1. - (x - .5) * 2.)); }
  vec3 fresh(vec3 b){ vec3 m = mix(b, S0, .35); float l = luma(m); m = l + (m - l) * 1.5;
    if (luma(b) <= 140. / 255.) m = m * 1.1 + 8. / 255.; return clamp(m, 0., 1.); }
  vec3 cooled(vec3 f, float a){ float k = min(2.999, a * 3.);
    vec3 c = k < 1. ? mix(S0, S1, k) : k < 2. ? mix(S1, S2, k - 1.) : mix(S2, S3, k - 2.);
    return mix(f, c, min(1., 1.4 * a)); }
  vec3 lin(vec3 c){ return mix(c / 12.92, pow((c + .055) / 1.055, vec3(2.4)), step(.04045, c)); }
  vec3 gam(vec3 c){ c = max(c, 0.); return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
  vec3 toLab(vec3 c){ vec3 r = lin(c);
    vec3 m = pow(max(vec3(dot(r, vec3(.4122214708, .5363325363, .0514459929)), dot(r, vec3(.2119034982, .6806995451, .1073969566)),
                         dot(r, vec3(.0883024619, .2817188376, .6299787005))), 0.), vec3(1. / 3.));
    return vec3(dot(m, vec3(.2104542553, .793617785, -.0040720468)), dot(m, vec3(1.9779984951, -2.428592205, .4505937099)), dot(m, vec3(.0259040371, .7827717662, -.808675766))); }
  vec3 labLin(vec3 q){ vec3 m = vec3(q.x + .3963377774 * q.y + .2158037573 * q.z, q.x - .1055613458 * q.y - .0638541728 * q.z, q.x - .0894841775 * q.y - 1.291485548 * q.z); m = m * m * m;
    return vec3(dot(m, vec3(4.0767416621, -3.3077115913, .2309699292)), dot(m, vec3(-1.2684380046, 2.6097574011, -.3413193965)), dot(m, vec3(-.0041960863, -.7034186147, 1.707614701))); }
  void main(){
    vec3 base = texture2D(uGround, vec2(.5, clamp((uScroll + (1. - vUv.y) * uVh) / uDoc, 0., 1.))).rgb;
    vec3 lc = fresh(base); float I = 0.;
    if (uReduced > .5) { vec2 d = vUv - uHead; d.x *= uAsp; I = .4 * uStrength * profile(length(d) * uH / 52.); }
    else { vec3 A = ageAt(uAge, vUv); float a = A.x / uLife;
      if (a < 1.) { float spd = clamp(A.z * uH / 1000., 0., 1.5), R = (52. + 40. * spd) * (1. + .25 * a);
        I = uStrength * pow(1. - a, 1.3) * profile(A.y * uH / R); lc = cooled(lc, a); } }
    float g = clamp(I * uGain, 0., 1.);
    vec3 scr = 1. - (1. - base) * (1. - lc);
    vec3 soft = mix(2. * base * lc + base * base * (1. - 2. * lc), sqrt(base) * (2. * lc - 1.) + 2. * base * (1. - lc), step(.5, lc));
    vec3 col = mix(base, luma(base) > 140. / 255. ? soft : scr, g);
    vec3 q = toLab(col); float cap = max(toLab(base).x, .781);
    if (q.x > cap) col = gam(clamp(labLin(vec3(cap, q.yz)), 0., 1.));
    gl_FragColor = vec4(clamp(col, 0., 1.), 1.); }`;

if (typeof window !== "undefined") { window.EmberEngine = EmberEngine; window.EmberMath = EmberMath; }
```

- [ ] **Step 2: Check that nothing from v23 is left.** Run `grep -nE "decay|stopTime|coastSpeed|cutAge|rippleFade|emberColour|chroma|coastMax|uField|rtA|SIM_GLSL" brand/ember/light/ember-light.js`. Expected: no output.

- [ ] **Step 3: Write `brand/ember/light/build.sh`.** Copy `brand/ember/build.sh` to the new path (don't edit the original), then change it so it bundles `brand/ember/light/ember-light.js` to `brand/ember/light/ember-light.bundle.js` with `--global-name=EmberLightBundle`, and prints `ember-light.bundle.js: ...`. It uses the same cached Three.js 0.160.0 folder.

- [ ] **Step 4: Build the bundle.** Run `sh brand/ember/light/build.sh`. Expected: a line `ember-light.bundle.js: N bytes, M bytes gzipped`, with N a little smaller than `brand/ember/ember.bundle.js` (the heat pass and the v23 maths are gone). If esbuild reports an import error, fix the import list at the top of the engine.

- [ ] **Step 5: Run the maths tests again.** Run `node --test brand/ember/light/ember-light-math.test.mjs`. Expected: every test passes.

- [ ] **Step 6: Checkpoint.** No commit.

### Task 3b: Responsive (spec §3.8). Do Step 8 as part of Task 4, where `LIGHT_CSS` is written.

**Files:** Modify: `brand/ember/light/ember-light-math.js`, `brand/ember/light/ember-light-math.test.mjs`, `brand/ember/light/ember-light.js`, `tools/afterglow_specimen.py`

- [ ] **Step 1: Write the failing tests.** Append to `ember-light-math.test.mjs` (and add `sizeScale` to its import list):

```js
test('sizeScale: 1 on desktop, 0.85 on tablets, 0.75 on phones', () => {
  assert.equal(sizeScale(1440), 1); assert.equal(sizeScale(993), 1); assert.equal(sizeScale(992), .85); assert.equal(sizeScale(577), .85);
  assert.equal(sizeScale(576), .75); assert.equal(sizeScale(390), .75);
});
test('touchRadius and lightTarget take the scale', () => {
  assert.equal(touchRadius(0, 0, .75), 39); assert.equal(touchRadius(1.5, 0, .75), 84); assert.equal(touchRadius(1.5, 1, .75), 105);
  assert.ok(near(lightTarget(39, 0, .75), .4));
});
```

- [ ] **Step 2: Run `node --test brand/ember/light/ember-light-math.test.mjs`.** Expected: FAIL, because `sizeScale` is not exported.

- [ ] **Step 3: Implement in `ember-light-math.js`.** Add `export const sizeScale = w => w >= 993 ? 1 : w >= 577 ? .85 : .75;`. Give `touchRadius` a third parameter, `scale = 1`, that multiplies the whole result. Give `lightTarget` a third parameter, `scale = 1`, passed through to `touchRadius`.

- [ ] **Step 4: Run the tests.** Expected: every test passes.

- [ ] **Step 5: Wire the scale into the engine.**
  1. Import `sizeScale`. In `init` and `onWindowResize`, after `this.W` is set, set `this.scale = sizeScale(this.W)` and the display uniform `uScale` to it. Add `uScale: { value: 1 }` to the display material's uniforms.
  2. The age field's write reach becomes `(REACH_PX * this.scale / this.H) ** 2` in both places it is set.
  3. The glide cap becomes `o.glideMax * this.scale` where `glideStart` is called.
  4. In `lightElements`, pass `this.scale` to both `touchRadius(speed)` and `lightTarget(...)`.
  5. In `DISPLAY_GLSL`, declare `uScale` with the other floats and multiply `R` by it. In the reduced-motion branch, the `52.` becomes `52. * uScale`.
- [ ] **Step 6: Pixel ratio.** Wherever `Math.min(devicePixelRatio, 2)` appears (in `init` and `onWindowResize`), the cap becomes 1.5 when `this.coarse` is true. `this.coarse` is set in the constructor before `init` runs.
- [ ] **Step 7: Early out.** In `DISPLAY_GLSL` `main`, right after `I` is computed, return the ground where there is no light: if `I` is at or below 0.0001, write `base` and return. The colour, blend and ceiling maths then run only where light falls.
- [ ] **Step 8: Viewport height.** In `LIGHT_CSS` (Task 4, `tools/afterglow_specimen.py`), the `#ember` rule changes from filling the viewport to the top-left at full width and the large viewport height: 100vh first as a fallback, then 100lvh. The engine reads the container's size, so it now sees a height that does not change when a phone's toolbar shows or hides.
- [ ] **Step 9: Rebuild and re-run.** Run `sh brand/ember/light/build.sh`, then `node --test brand/ember/light/ember-light-math.test.mjs`. Expected: the bundle builds and every test passes.
- [ ] **Step 10: Checkpoint.** No commit.

---

## Chunk 3: The guide

### Task 4: Swap the light engine into the hour-lite guide only

**Files:** Modify: `tools/afterglow_specimen.py` (new constants beside `LITE_CSS`, and `build_lite()`). **Not** `tools/density_b_family.py`.

The older builds inline `brand/ember/ember.bundle.js`, `B.EMBER_CSS` and `B.GUIDE_JS` (through `B.with_ember`). `build_lite()` receives that HTML from `B.build("b1-column")` and swaps the three parts in its own output.

- [ ] **Step 1: The selectors** (in `afterglow_specimen.py`). Photographs get the edge band and boxes get the wash. Text with its own background (`.wpill`, `.pill`, `.btn`) counts as a box, because `background-clip: text` would remove its fill:

```python
_S = ".deck .sheet:not(.bcover) "
LIGHT_PHOTOS = _S + ":is(figure, .appimg)"
LIGHT_BOXES = _S + ":is(.panel, .wtile, .sw, .appbody, .pcard, .plabel, .pposter, .fallband, .step, .wpill, .pill, .btn)"
LIGHT_TEXT = (_S + ":is(h2, h3, p, li, dt, dd, th, td, figcaption, a, .foot span, .wspec, "
              ".tlab, .tsamp, .tnum, .stageread, .pwm, .wmtext, .pfine, .tri > span)")
LIGHT_SURFACES = LIGHT_PHOTOS + ", " + LIGHT_BOXES
LIGHT_LIT = LIGHT_SURFACES + ", " + LIGHT_TEXT
```

- [ ] **Step 2: `LIGHT_CSS`.** It takes the place of `B.EMBER_CSS` whole, so it repeats the container rules (with the viewport-height change from Task 3b Step 8) and then the surface treatments. `[data-lit]` attaches to the `:is(...)` compound at the end of `LIGHT_TEXT`, so it targets the lit element itself:

```python
LIGHT_CSS = f"""
  /* the ember, light revision (spec 2026-10-13): a canvas behind the sheets draws every sheet's ground once it has drawn */
  #ember{{position:fixed;left:0;top:0;width:100%;height:100vh;height:100lvh;z-index:0;pointer-events:none}}
  #ember canvas{{display:block;width:100%;height:100%}}
  .deck{{position:relative;z-index:1}}
  @media screen{{.ember-on .sheet:not(.bcover){{background:transparent!important}}}}
  @media print{{#ember{{display:none}}}}
  /* what it lights (§3.4): light clipped to the letters; a soft-light band on a photograph's edge facing the light;
     a soft-light wash in boxes. No rim, no glow, no shadow. */
  {LIGHT_LIT}{{--li:0;--ec:216,178,96;--px:50%;--py:-200px;--rr:208px}}
  :where({LIGHT_SURFACES}){{position:relative}}
  {LIGHT_BOXES}::after{{content:"";position:absolute;inset:0;pointer-events:none;mix-blend-mode:soft-light;
    background:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),var(--li)) 0%,rgba(var(--ec),calc(.4 * var(--li))) 50%,transparent 100%)}}
  {LIGHT_PHOTOS}::after{{content:"";position:absolute;inset:0;pointer-events:none;mix-blend-mode:soft-light;
    background:radial-gradient(circle var(--band,0px) at var(--ex,-999px) var(--ey,-999px),rgba(var(--ec),var(--li)) 0%,rgba(var(--ec),calc(.4 * var(--li))) 50%,transparent 100%)}}
  {LIGHT_TEXT}[data-lit]{{color:transparent;-webkit-background-clip:text;background-clip:text;
    background-image:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),var(--li)) 0%,rgba(var(--ec),calc(.4 * var(--li))) 50%,transparent 100%),linear-gradient(var(--tc),var(--tc))}}
  @media print{{{LIGHT_SURFACES}::after{{display:none}}[data-lit]{{color:var(--tc)!important;background:none!important}}}}
"""
```

- [ ] **Step 3: `swap_ember(html)`.** Each replacement asserts exactly one match, so a change upstream fails loudly instead of leaving v23 in place:

```python
def swap_ember(html):
    """Aaron, 13 Oct: the hour-lite guide takes the light revision; the older builds keep v23 untouched."""
    esc = lambda t: t.replace("</script", "<\\/script")
    old_js = esc((D.ROOT / "brand/ember/ember.bundle.js").read_text())
    new_js = esc((D.ROOT / "brand/ember/light/ember-light.bundle.js").read_text())
    old_lit = 'lit: "' + B.EMBER_LIT + '"'
    for a in (old_js, B.EMBER_CSS, old_lit):
        assert html.count(a) == 1, f"swap_ember: want one of {a[:40]!r}, found {html.count(a)}"
    html = html.replace(old_js, new_js, 1).replace(B.EMBER_CSS, LIGHT_CSS, 1)
    return html.replace(old_lit, 'lit: "' + LIGHT_LIT + '", photos: "' + LIGHT_PHOTOS + '"', 1)
```

`D` is the module that `afterglow_specimen.py` already uses for `D.ROOT`. If `EMBER_CSS` reaches the page with different whitespace (for example, if `with_ember` alters it), match on what `with_ember` actually inserts.

- [ ] **Step 4: Call it, and drop the v23 colour options.** In `build_lite()`, delete these two lines:

```python
    html = html.replace("groundAt: guideGroundAt, lit:", 'groundAt: guideGroundAt, chroma: "match", chromaScale: 1.2, lit:', 1)   # Aaron, 12 Oct: the ember at the page's own chroma
    assert 'chroma: "match"' in html
```

Then call `html = swap_ember(html)` in their place, before `refall` and `recopy` run.

### Task 5: The guide's copy (spec §5)

**Files:** Modify: `tools/afterglow_specimen.py` (the `COPY` table)

- [ ] **Step 1: Find the exact source strings.** Run:
`python3 -c "import re;h=open('brand/2026-10-12-guide-hour-lite.html').read();[print(repr(h[h.find(t)-80:h.find(t)+220])) for t in ('The one accent of contrast','in 0.7 seconds','Never a shadow, a dark pattern','#321C5B','The ember is the one exception')]"`
Note how the page 11 chips are marked up: each chip has a background and a hex label.

- [ ] **Step 2: Append to `COPY`** (one entry per line). The old text must be copied exactly from Step 1, entities included. `recopy()` matches any run of whitespace:

```python
    # the ember, light revision (spec 2026-10-13 §5)
    ("The one accent of contrast. It follows the cursor in the colour of the page beneath it, and goes out when the cursor stops.",
     "The one accent of contrast: a small warm light wherever the cursor moves, cooling down the fall as it fades."),
    ("Move, and it lights. Stop, and in 0.7 seconds it goes out.", "Move, and it lights. Stop, and in 0.9 seconds it is gone."),
    ("Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render.",
     "Never an object, an edge, a shadow, or a page that needs it to render."),
    ("The ember is the one exception, an accent of contrast that raises the chroma of the colour it sits on.",
     "The ember is the one exception: a small warm light that raises the chroma of what it touches, then cools down the fall."),
```

The chips: page 11 sits on rose (#893A50, the rose card's span). Its fresh light is `freshColour([137,58,80])` = **#DA6F57**, and it cools to **#341D5E**. Add entries that replace the chip's hex labels `#321C5B` and `#5304E4` **and** their chip backgrounds with `#DA6F57` and `#341D5E`, using the exact markup from Step 1. If a hex appears more than once on the page (in a label and a style), give each occurrence its own entry with enough surrounding markup to match exactly once, because `recopy` asserts one match.

- [ ] **Step 3: Rebuild the guide.** Run `python3 tools/afterglow_specimen.py`. Expected: `brand/2026-10-12-guide-hour-lite.html 33 photographs; ...` and no assertion error. If a `COPY` entry fails ("copy edit matched 0 times"), re-copy its old text from Step 1.

- [ ] **Step 4: Run the guide tests.** Run `python3 tools/test_afterglow_specimen.py`. Expected: `17 pass, 0 fail`.

- [ ] **Step 5: Checkpoint.** No commit.

### Task 6: A check script for the light revision

**Files:** Create: `tools/check_ember_light.py`. **Not** `tools/check_b1.py`, which checks the older build and stays untouched.

- [ ] **Step 1:** Write `tools/check_ember_light.py`, modelled on the ember section of `tools/check_b1.py` (Playwright, served over `http://localhost:8765`, a `fails` list, exit code 1 on any failure). It opens `brand/2026-10-12-guide-hour-lite.html` and checks:
  - exactly one canvas under `#ember`;
  - `ember-on` is set after the first frame;
  - `window.EmberMath.sizeScale` exists (so the light bundle loaded, not v23);
  - beside the pointer after 10 frames of movement on page 11, a photograph, a swatch and a paragraph each have `--li` over 0.3;
  - print hides `#ember`, and no lit text stays transparent;
  - context loss removes `ember-on` and every `data-lit`.

  Each of the Task 7 checks goes in as its own function in this same script.
- [ ] **Step 2:** Run `python3 tools/check_ember_light.py`. Expected: `0 fail`.

## Chunk 4: Verification against the spec (§6)

Serve the repo with `python3 -m http.server 8765` (from the repo root) for every step.

### Task 7: The checks

- [ ] **Step 1: No dead stop.** In Playwright at 1440×900, open the guide, scroll to page 11 and move the mouse right at 15 px per 16 ms for 30 steps, then stop. Record `ember.E.cx` on every frame through `ember.onFrame` for 600 ms. Expected: after the last pointer event, `cx` keeps increasing for at least 15 frames. Each frame-to-frame step is no larger than the one before it (allow 0.5 px for frame jitter), and it ends between 20 and 64 px past the pointer.
- [ ] **Step 2: Nothing drawn.** At 1440, 1920 and 390 wide, with `deviceScaleFactor: 2`, take screenshots mid-stroke and 600 ms after a stop on pages 11, 06 and 03. Expected by eye: no edge, outline, band, highlight or stair-step anywhere.
- [ ] **Step 3: Ceiling.** On page 03 (gold), page 06 and page 11, screenshot before moving and again mid-stroke. For every pixel that changed, convert both to OKLab L. Expected: no changed pixel has `L_after > max(L_before, 0.781) + 0.01`.
- [ ] **Step 4: Cost.** On page 11, wrap `ember.onFrame` to record the maximum `ember.lightMs` over a 2 s stroke. Expected: under 2 ms. (The 60 fps check on a 2020 MacBook Air is Aaron's, by eye.)
- [ ] **Step 5: Fallbacks.**
  - **Reduced motion:** `page.emulate_media(reduced_motion="reduce")`. One still, faint light follows the pointer, with no trail and no glide (`ember.phase` stays `"idle"`).
  - **Print:** `#ember` computes `display:none`, and no element keeps `color: transparent` under print media.
  - **Context loss:** `ember.renderer.forceContextLoss()` removes `ember-on`, the sheets keep their CSS grounds, and every `data-lit` attribute is gone.
- [ ] **Step 5b: Responsive.** Emulate 390 × 844 with a coarse pointer, touch, `isMobile` and `deviceScaleFactor: 3`. Drag a finger across page 11 with `page.touchscreen` or touch events. Expected: `ember.scale === .75`; a touch's measured light reaches no further than 105 px; `ember.renderer.getPixelRatio()` is 1.5; the computed `#ember` rule uses `100lvh` (read it from the stylesheet text; desktop emulation has no toolbar, so a real toolbar toggle can only be checked on a phone, which is Aaron's); after counting calls to `ember.makeTargets` and resizing to 390 × 764 mid-stroke, the count is unchanged, so the light survives; the maximum `ember.lightMs` is under 4 ms; and `document.querySelectorAll('[data-lit]').length` equals the number of elements with `--li` over 0.002.
- [ ] **Step 6: Tune the ground.** Open the guide and the prototype (`c3`) side by side on page 11, then page 03. If the ground reads as a shape, lower `groundGain` (pass it in `GUIDE_JS`'s options). If the ground is invisible where the prototype shows a faint warmth, raise it. Record the final value in the spec's §3.4 ("6% is the starting value" becomes the value chosen).
- [ ] **Step 6b: Run the older checks too.** Run `python3 tools/check_b1.py` and compare it with a run made before Task 2 (record that run in Task 1 if you can). Expected: the same result, because nothing it builds or reads has changed.

### Task 8: Prove the older builds are untouched

- [ ] **Step 1:** Run `shasum -c "$TMPDIR/ember-baseline.sha"`. Expected: every line `OK`.
- [ ] **Step 2:** Run `git status --short brand/ember tools/density_b_family.py tools/check_b1.py`. Expected: only the new `brand/ember/light/` folder appears as new. Every other path shows exactly the status it had before this plan (it was already uncommitted work).

- [ ] **Step 7: Hand over to Aaron.** Open `brand/2026-10-12-guide-hour-lite.html` and the prototype `c3`. He signs off the feel (size, strength, life, cooling, glide) and the photograph edge band (its 18% depth is a starting value). No commit until he says.
