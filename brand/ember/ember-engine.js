import {
  WebGLRenderer, Scene, OrthographicCamera, Clock, Mesh, PlaneGeometry, ShaderMaterial, Vector2,
  WebGLRenderTarget, DataTexture, HalfFloatType, UnsignedByteType, LinearFilter, NearestFilter, RGBAFormat, Color,
} from "three";
import * as EmberMath from "./ember-math.js";
import { fallAt, fieldSize, decay, stopTime, coastSpeed, cutAge, rippleFade, lightTarget, easeLight, emberColour, emberColourMatched } from "./ember-math.js";

const GROUND_N = 2048;

/**
 * EmberEngine, after StylizedShadowEngine: the same shape (constructor, init, setupListeners, onWindowResize,
 * animate, dispose, getFragmentShader), with the box swapped for a heat field the cursor writes into.
 * Ported from the approved reference build, v23 (docs/superpowers/specs/2026-10-11-afterglow-ember-reference.html).
 * Spec: docs/superpowers/specs/2026-10-11-afterglow-ember-design.md
 */
export class EmberEngine {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      groundAt: fallAt,        // the page's colour from top (0) to bottom (1)
      lit: "",                 // what catches the ember's light
      onFirstFrame: () => {},
      onLost: () => {},
      onFrame: null,
      forceByteTargets: false,
      stopDetect: .034,        // seconds without movement that count as a stop
      coastMax: 8,             // px per frame: the fastest the head coasts
      chroma: "push",
      chromaScale: 1,          // matched only: the ember's chroma as a multiple of the page's (1 = the same)          // "push": v23, the page's chroma pushed up toward white heat; "match": lightness only, the page's own chroma
      ...options,
    };
    this.onFrame = this.options.onFrame;
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.coarse = matchMedia("(pointer: coarse)").matches;
    this.phase = "idle"; this.idle = true; this.paused = false;
    this.stopT = 0; this.stopElapsed = 0; this.cutAge = null; this.lastDt = 0; this.lastMoveT = -1e9;
    this.head = { x: 0, y: 0 }; this.cutHead = { x: 0, y: 0 }; this.history = [];
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
    // the context is made here, so a browser without WebGL fails quietly before Three is involved
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
    this.clock = new Clock();
    this.E = { x: this.W / 2, y: this.H * .6, vx: 0, vy: 0, heat: 0, moved: 0, lastMove: -1e9, known: false };

    const vs = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position, 1.0); }`;
    const geo = new PlaneGeometry(2, 2), pre = this.byteTargets ? "#define BYTE_AGE 1\n" : "";
    this.sim = new ShaderMaterial({
      uniforms: { uField: { value: null }, uPos: { value: new Vector2() }, uPrev: { value: new Vector2() }, uAmt: { value: 0 },
                  uAsp: { value: 1 }, uDecay: { value: 1 }, uDecayHead: { value: 1 } },
      vertexShader: vs, fragmentShader: pre + AGE_GLSL + SIM_GLSL });
    this.ageSim = new ShaderMaterial({
      uniforms: { uAge: { value: null }, uPos: { value: new Vector2() }, uPrev: { value: new Vector2() }, uAmt: { value: 0 },
                  uAsp: { value: 1 }, uDt: { value: 0 } },
      vertexShader: vs, fragmentShader: pre + AGE_GLSL + AGE_SIM_GLSL });
    this.material = new ShaderMaterial({
      uniforms: { uField: { value: null }, uTime: { value: 0 }, uScroll: { value: 0 }, uVh: { value: this.H }, uDoc: { value: 1 },
                  uAsp: { value: 1 }, uHead: { value: new Vector2(.5, .5) }, uAge: { value: null }, uSince: { value: 0 },
                  uCut: { value: -100 }, uRip: { value: 1 }, uMatch: { value: this.options.chroma === "match" ? 1 : 0 }, uCk: { value: this.options.chromaScale }, uGround: { value: null }, uFieldSize: { value: new Vector2(1, 1) } },
      vertexShader: vs, fragmentShader: pre + this.getFragmentShader(), extensions: { derivatives: true } });
    this.simScene = new Scene(); this.simScene.add(new Mesh(geo, this.sim));
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
    on(window, "resize", () => this.onWindowResize());
    on(window, "pointermove", e => {
      if (e.pointerType === "touch") return;
      if (lx !== null) { E.vx = e.clientX - lx; E.vy = e.clientY - ly; E.moved += Math.hypot(E.vx, E.vy); }
      lx = E.x = e.clientX; ly = E.y = e.clientY; E.known = true; this.wake();
    });
    // touch: scroll speed stands in for cursor speed, and the ember sits at the last touch point
    on(window, "touchstart", e => { const t = e.touches[0]; if (t) { E.x = t.clientX; E.y = t.clientY; E.known = true; } });
    on(window, "scroll", () => {
      const d = scrollY - ls; ls = scrollY;
      if (this.coarse || lx === null) { E.vx = 0; E.vy = -d; E.moved += Math.abs(d) * .8; if (this.coarse) E.known = true; }
      this.dirty = true; this.wake();
    });
    on(document, "visibilitychange", () => {
      this.paused = document.hidden;
      if (this.paused) { cancelAnimationFrame(this.raf); this.raf = 0; } else { this.dirty = true; this.wake(); }
    });
    // late images and fonts change the document's height: the ground is re-baked so colours stay aligned
    if (window.ResizeObserver) {
      let h = document.documentElement.scrollHeight;
      this.ro = new ResizeObserver(() => { const n = document.documentElement.scrollHeight; if (n !== h) { h = n; this.rebakeGround(); this.collectLit(); } });
      this.ro.observe(document.body); this.ro.observe(document.documentElement);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { if (!this.disposed) this.collectLit(); });
    this.renderer.domElement.addEventListener("webglcontextlost", e => { e.preventDefault(); this.lose(); }, false);
  }

  // heat and age fields: a quarter of the viewport on each axis, at least 360 x 225 (spec 2.8)
  makeTargets() {
    [this.rtA, this.rtB, this.agA, this.agB].forEach(t => t && t.dispose());
    const [W, H] = fieldSize(this.W, this.H), byte = this.byteTargets;
    this.fieldW = W; this.fieldH = H;
    const rt = (filter) => new WebGLRenderTarget(W, H, { type: byte ? UnsignedByteType : HalfFloatType, format: RGBAFormat,
      minFilter: filter, magFilter: filter, depthBuffer: false, stencilBuffer: false });
    // 8-bit age is packed in two bytes, so it is read with a 4-tap bilinear blend in the shader, never filtered raw
    this.rtA = rt(LinearFilter); this.rtB = rt(LinearFilter); this.agA = rt(byte ? NearestFilter : LinearFilter); this.agB = rt(byte ? NearestFilter : LinearFilter);
    const r = this.renderer;
    r.setClearColor(new Color(0, 0, .5), .5);          // empty heat, velocity at its zero (0.5)
    [this.rtA, this.rtB].forEach(t => { r.setRenderTarget(t); r.clear(); });
    r.setClearColor(new Color(1, 1, 1), 1);           // age starts old
    [this.agA, this.agB].forEach(t => { r.setRenderTarget(t); r.clear(); });
    r.setRenderTarget(null); r.setClearColor(0x080808, 1);
    this.material.uniforms.uFieldSize.value.set(W, H);
    this.history = [];
  }

  onWindowResize() {
    this.W = this.container.clientWidth || innerWidth; this.H = this.container.clientHeight || innerHeight;
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(this.W, this.H, false);
    // a phone toolbar showing or hiding resizes the window mid-scroll; the trail survives unless the field must change
    const [fw, fh] = fieldSize(this.W, this.H);
    if (fw !== this.fieldW || fh !== this.fieldH) this.makeTargets();
    clearTimeout(this.rebakeT); this.rebakeT = setTimeout(() => { this.rebakeGround(); this.collectLit(); }, 100);
    this.dirty = true; this.wake();
  }

  // the ground: the host's colour source, read into a 1 x 2048 strip from the top of the document to the bottom
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

  // the baked ground at a viewport y, as the display pass reads it
  groundRGB(y) {
    const t = (scrollY + y) / document.documentElement.scrollHeight, i = Math.max(0, Math.min(GROUND_N - 1, Math.floor(t * GROUND_N))) * 4;
    return [this.groundPx[i], this.groundPx[i + 1], this.groundPx[i + 2]];
  }

  // what catches the light, and where each piece sits in the document. Positions are measured here, on load, resize
  // and height changes, never per frame, so lighting every element on a long page costs no layout.
  collectLit() {
    this.lit = this.options.lit ? [...document.querySelectorAll(this.options.lit)] : [];
    const sx = scrollX, sy = scrollY;
    this.litBoxes = this.lit.map(el => { el._li = el._li || 0; const r = el.getBoundingClientRect();
      return { l: r.left + sx, t: r.top + sy, r: r.right + sx, b: r.bottom + sy, w: r.width }; });
  }

  wake() { if (!this.raf && !this.paused && !this.disposed && !this.failed) this.raf = requestAnimationFrame(t => this.tick(t)); }

  tick() {
    this.raf = 0;
    if (this.paused || this.disposed) return;
    const busy = this.animate();
    if (busy) this.wake();
  }

  // one frame: the heat pass, the age pass, the display pass. Returns whether another frame is needed.
  animate() {
    const E = this.E, o = this.options, now = performance.now(), su = this.sim.uniforms;
    const dt = Math.min(.1, (now - (this.lastT || now)) / 1000) || 1 / 60; this.lastT = now; this.lastDt = dt;
    const amt = Math.min(1, E.moved / 60); if (E.moved > 2) E.lastMove = now; E.moved = 0;
    const since = now - E.lastMove, moving = !this.reduced && since < o.stopDetect * 1000;
    if (moving && !this.wasMoving) E.strokeStart = now;
    this.wasMoving = moving; this.lastMoveT = E.lastMove;
    E.heat = Math.min(1, E.heat * (moving ? decay(.992, dt) : decay(.965, dt)) + amt * .5);   // the light cools with the body
    const asp = this.W / this.H;
    su.uField.value = this.rtA.texture; su.uPrev.value.copy(su.uPos.value); su.uAsp.value = asp;

    // the stop (spec 2.3): one time T. The head coasts to rest at T while the tail end, leaving where the moving taper
    // ended at the pace it had, runs forward along the path to meet it there. Then the field is cleared.
    const stopS = since / 1000, stroke = (E.lastMove - (E.strokeStart || E.lastMove)) / 1000 + .05;
    const c0 = Math.min(.58, stroke), T = stopTime(c0);
    if (E.cx === undefined) { E.cx = E.x; E.cy = E.y; E.cvx = 0; E.cvy = 0; }
    let coastAmt = 0, write = 0, cut = -100, clear = false, start = false;
    if (this.reduced) {
      // one ember, held still at the pointer: no trail, no ripple, no animation
      E.cx = E.x; E.cy = E.y; su.uPrev.value.set(E.cx / this.W, 1 - E.cy / this.H);
      this.phase = "idle"; write = E.known ? .25 : 0;
    } else if (moving) {
      // a new stroke starts at the pointer: nothing is drawn from where the last one came to rest
      if (this.phase === "idle") { start = true; E.cx = E.x; E.cy = E.y; E.cvx = E.cvy = 0; su.uPrev.value.set(E.x / this.W, 1 - E.y / this.H); }
      if (amt > 0) { E.cvx = E.cvx * .5 + (E.x - E.cx) * .5; E.cvy = E.cvy * .5 + (E.y - E.cy) * .5; }   // speed only from frames that moved
      E.cx = E.x; E.cy = E.y; E.coast = null; this.phase = "moving"; write = amt;
    } else if (this.phase === "moving" || this.phase === "stopping") {
      if (!E.coast) { const m = Math.hypot(E.cvx, E.cvy), q = m > o.coastMax ? o.coastMax / m : 1; E.coast = { x: E.cx, y: E.cy, vx: E.cvx * q, vy: E.cvy * q }; }
      const C = E.coast, Tc = Math.max(.05, T - o.stopDetect), tc = Math.min(Tc, Math.max(0, stopS - o.stopDetect));
      const d = (tc - tc * tc / (2 * Tc)) * 60;          // distance so far, in frames of the starting speed
      E.cx = C.x + C.vx * d; E.cy = C.y + C.vy * d;
      coastAmt = Math.min(1, coastSpeed(Math.hypot(C.vx, C.vy), tc, Tc) / 10);
      write = coastAmt > .02 ? coastAmt : 0;
      cut = cutAge(c0, stopS, T);
      if (stopS < T + .06) this.phase = "stopping"; else { this.phase = "idle"; clear = true; write = 0; }
    }
    const stopping = this.phase === "stopping";
    this.stopT = T; this.stopElapsed = moving ? 0 : stopS; this.cutAge = stopping ? cut : null;
    su.uDecayHead.value = this.reduced || clear ? 0 : moving ? decay(.935, dt) : 1;   // held while the tail runs in, cleared after
    su.uDecay.value = this.reduced || clear ? 0 : moving ? decay(.955, dt) : 1;
    su.uPos.value.set(E.cx / this.W, 1 - E.cy / this.H); su.uAmt.value = write;
    
    this.head.x = E.cx; this.head.y = E.cy;
    if (write > .02 && !this.reduced) this.remember(now / 1000, E.cx, E.cy);
    if (stopping) this.cutHead = this.pointAt(E.lastMove / 1000 - cut);
    else { this.cutHead.x = E.cx; this.cutHead.y = E.cy; }

    const field = this.phase !== "idle" || clear || (this.reduced && E.known);
    const drew = field || this.dirty || !this.drawn;
    if (drew) {
      const r = this.renderer;
      r.setRenderTarget(this.rtB); r.render(this.simScene, this.camera); [this.rtA, this.rtB] = [this.rtB, this.rtA];
      const ag = this.ageSim.uniforms;
      ag.uAge.value = this.agA.texture; ag.uPos.value.copy(su.uPos.value); ag.uPrev.value.copy(su.uPrev.value);
      // a zero-length segment writes age over a whole disc; only a stroke's first point may do that, or a stop that
      // lands just past 34 ms re-ages the trail behind the head and the tail end holds, then jumps
      const segPx = Math.hypot((su.uPos.value.x - su.uPrev.value.x) * this.W, (su.uPos.value.y - su.uPrev.value.y) * this.H);
      ag.uAmt.value = this.reduced || (segPx < .1 && !start) ? 0 : write; ag.uAsp.value = asp; ag.uDt.value = dt;
      r.setRenderTarget(this.agB); r.render(this.ageScene, this.camera); [this.agA, this.agB] = [this.agB, this.agA];
      const u = this.material.uniforms;
      u.uField.value = this.rtA.texture; u.uAge.value = this.agA.texture;
      u.uTime.value = this.reduced ? 0 : this.clock.getElapsedTime(); u.uScroll.value = scrollY;
      u.uHead.value.set(E.cx / this.W, 1 - E.cy / this.H); u.uSince.value = stopS; u.uCut.value = stopping ? cut : -100;
      u.uRip.value = this.reduced ? 0 : moving ? 1 : rippleFade(stopS, T);
      u.uVh.value = this.H; u.uDoc.value = document.documentElement.scrollHeight; u.uAsp.value = asp;
      r.setRenderTarget(null); r.render(this.scene, this.camera);
      this.dirty = false;
      if (!this.drawn) { this.drawn = true; this.options.onFirstFrame(); }
    }
    this.idle = this.phase === "idle";
    const lights = this.lightElements();
    E.vx *= .6; E.vy *= .6;
    if (this.onFrame) this.onFrame(this, drew);
    return !this.idle || lights;
  }

  // the path the head has written, for the cut's position on screen
  remember(t, x, y) {
    const h = this.history, last = h[h.length - 1];
    if (last && Math.hypot(last.x - x, last.y - y) < .01) last.t = t; else h.push({ t, x, y });
    while (h.length > 2 && t - h[0].t > 3) h.shift();
  }

  pointAt(t) {
    const h = this.history;
    if (!h.length) return { x: this.E.cx, y: this.E.cy };
    if (t <= h[0].t) return { x: h[0].x, y: h[0].y };
    for (let i = 1; i < h.length; i++) if (t <= h[i].t) {
      const a = h[i - 1], b = h[i], k = (t - a.t) / (b.t - a.t || 1);
      return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
    }
    const z = h[h.length - 1]; return { x: z.x, y: z.y };
  }

  // light on cards and text (spec 2.7): measured from the nearest point of each box, eased like light. Returns
  // whether any light is still moving. All reads come before all writes, so the page lays out once per frame.
  lightElements() {
    if (!this.lit.length) return false;
    const t0 = performance.now(), E = this.E, X = E.cx, Y = E.cy, sx = scrollX, sy = scrollY;
    const c = (this.options.chroma === "match" ? emberColourMatched(this.groundRGB(Y), this.options.chromaScale) : emberColour(this.groundRGB(Y))).join(",");
    let active = false;
    for (let i = 0; i < this.lit.length; i++) {
      const el = this.lit[i], B = this.litBoxes[i];
      const r = { left: B.l - sx, top: B.t - sy, right: B.r - sx, bottom: B.b - sy, width: B.w, height: B.b - B.t };
      if (r.bottom < -200 || r.top > this.H + 200 || !r.width) { if (el._li) { el._li = 0; el.style.setProperty("--li", "0"); } continue; }
      const nx = Math.max(r.left, Math.min(X, r.right)), ny = Math.max(r.top, Math.min(Y, r.bottom));
      const target = lightTarget(E.heat, Math.hypot(X - nx, Y - ny));
      const li = easeLight(el._li, target);
      if (Math.abs(li - target) > .002) active = true;
      if (li < .002 && el._li < .002) { if (el._li) { el._li = 0; el.style.setProperty("--li", "0"); } continue; }
      el._li = li;
      const cx = X - (r.left + r.width / 2), cy = Y - (r.top + r.height / 2), cd = Math.hypot(cx, cy) || 1, s = el.style;
      s.setProperty("--li", li.toFixed(3));
      s.setProperty("--px", (X - r.left).toFixed(0) + "px"); s.setProperty("--py", (Y - r.top).toFixed(0) + "px");
      s.setProperty("--rr", (156 + 156 * E.heat).toFixed(0) + "px");
      s.setProperty("--tx", (cx / cd * 1.5).toFixed(2) + "px"); s.setProperty("--ty", (cy / cd * 1.5).toFixed(2) + "px");
      s.setProperty("--ec", c);
    }
    this.lightMs = performance.now() - t0;
    return active || E.heat > .002;
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
    [this.rtA, this.rtB, this.agA, this.agB, this.groundTex].forEach(t => t && t.dispose());
    (this.lit || []).forEach(el => ["--li", "--px", "--py", "--rr", "--tx", "--ty", "--ec"].forEach(k => el.style.removeProperty(k)));
    if (this.renderer) { this.renderer.dispose(); this.renderer.domElement.remove(); }
    if (this.scene) this.scene.clear();
  }

  getFragmentShader() { return AGE_GLSL + DISPLAY_GLSL; }
}

// the age field: r is seconds since the ember passed (0-2 s packed into r and g on 8-bit targets), then the distance
// from the path's centre line and the speed when written
const AGE_GLSL = `
  uniform vec2 uFieldSize;
  #ifdef BYTE_AGE
  vec3 unpackAge(vec4 t){ return vec3((t.r * 255. * 256. + t.g * 255.) / 65535. * 2., t.b * .1, t.a * 8.); }
  vec4 packAge(vec3 a){ float v = floor(clamp(a.x / 2., 0., 1.) * 65535. + .5);
    return vec4(floor(v / 256.) / 255., mod(v, 256.) / 255., clamp(a.y / .1, 0., 1.), clamp(a.z / 8., 0., 1.)); }
  vec3 ageTexel(sampler2D t, vec2 uv){ return unpackAge(texture2D(t, uv)); }
  vec3 ageAt(sampler2D t, vec2 uv){                      // a 4-tap bilinear blend, so filtering never drops to nearest
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

// heat (r: the thin tail, g: the head), velocity (ba, centred on 0.5)
const SIM_GLSL = `
  uniform sampler2D uField; uniform vec2 uPos, uPrev; uniform float uAmt, uAsp, uDecay, uDecayHead; varying vec2 vUv;
  void main(){ vec4 o = texture2D(uField, vUv); vec2 v = (o.ba - .5) * 2.;
    o = texture2D(uField, vUv - v * .003); v = (o.ba - .5) * 2. * .9;   // a light drift in the direction of travel
    float h = o.r * uDecay, g = o.g * uDecayHead;
    // no cut here: the heat is held whole while the display cut runs in. Cutting heat per texel stepped the last frames.
    vec2 a = uPrev, b = uPos, p = vUv; a.x *= uAsp; b.x *= uAsp; p.x *= uAsp; vec2 ab = b - a;
    float k = clamp(dot(p - a, ab) / max(dot(ab, ab), 1e-6), 0., 1.); vec2 d = p - (a + ab * k);
    float on = uAmt > .02 ? clamp(.65 + uAmt, 0., 1.) : 0.;
    float s = exp(-dot(d, d) / .00035) * on;            // the tail: a thin line, never additive
    float sh = exp(-dot(d, d) / .0022) * on;            // the head: additive, so it swells into a teardrop
    h = max(h, min(1., s)); g = min(1., g + sh * 1.3);
    gl_FragColor = vec4(h, g, v * .5 + .5); }`;

const AGE_SIM_GLSL = `
  uniform sampler2D uAge; uniform vec2 uPos, uPrev; uniform float uAmt, uAsp, uDt; varying vec2 vUv;
  // age runs smoothly down each frame's segment; written only ahead of the segment's start, so a path that curves
  // back never re-ages older trail
  void main(){ vec3 A = ageTexel(uAge, vUv); float a = A.x + uDt;
    vec2 pa = uPrev, pb = uPos, p = vUv; pa.x *= uAsp; pb.x *= uAsp; p.x *= uAsp; vec2 ab = pb - pa; float len = length(ab);
    float kr = dot(p - pa, ab) / max(len * len, 1e-8), k = clamp(kr, 0., 1.); vec2 d = p - (pa + ab * k);
    if (uAmt > .02 && dot(d, d) < .0066 && (kr > 0. || len < 1e-4)) { float na = uDt * (1. - k);
      if (na <= a) { a = na; A.y = length(d); A.z = len / max(uDt, 1e-3); } }
    gl_FragColor = packAge(vec3(a, A.y, A.z)); }`;

const DISPLAY_GLSL = `
  uniform sampler2D uField, uAge, uGround; uniform float uTime, uScroll, uVh, uDoc, uAsp, uSince, uCut, uRip, uMatch, uCk; uniform vec2 uHead; varying vec2 vUv;
  // matched chroma: colour handled in OKLab, so the ember can lighten or darken the page's colour and keep its chroma and hue
  vec3 lin(vec3 c){ return mix(c / 12.92, pow((c + .055) / 1.055, vec3(2.4)), step(.04045, c)); }
  vec3 gam(vec3 c){ c = max(c, 0.); return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
  vec3 toLab(vec3 c){ vec3 r = lin(c);
    vec3 m = pow(max(vec3(dot(r, vec3(.4122214708, .5363325363, .0514459929)), dot(r, vec3(.2119034982, .6806995451, .1073969566)),
                         dot(r, vec3(.0883024619, .2817188376, .6299787005))), 0.), vec3(1. / 3.));
    return vec3(dot(m, vec3(.2104542553, .793617785, -.0040720468)), dot(m, vec3(1.9779984951, -2.428592205, .4505937099)), dot(m, vec3(.0259040371, .7827717662, -.808675766))); }
  vec3 labLin(vec3 q){ vec3 m = vec3(q.x + .3963377774 * q.y + .2158037573 * q.z, q.x - .1055613458 * q.y - .0638541728 * q.z, q.x - .0894841775 * q.y - 1.291485548 * q.z); m = m * m * m;
    return vec3(dot(m, vec3(4.0767416621, -3.3077115913, .2309699292)), dot(m, vec3(-1.2684380046, 2.6097574011, -.3413193965)), dot(m, vec3(-.0041960863, -.7034186147, 1.707614701))); }
  bool inG(vec3 r){ return all(greaterThanEqual(r, vec3(-.001))) && all(lessThanEqual(r, vec3(1.001))); }
  vec3 liftL(vec3 c, float d, float k){ vec3 q = toLab(c); q.yz *= k; float lo = q.x, hi = q.x + d;   // out of gamut, it gives up lightness, never chroma
    if (!inG(labLin(vec3(hi, q.yz)))) { for (int i = 0; i < 8; i++) { float md = .5 * (lo + hi); if (inG(labLin(vec3(md, q.yz)))) lo = md; else hi = md; } hi = lo; }
    return gam(clamp(labLin(vec3(hi, q.yz)), 0., 1.)); }
  float heat(vec2 p){ vec4 f = texture2D(uField, p); return max(f.r, f.g); }
  float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
  float noise3d(vec3 p){ vec3 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
    return mix(mix(mix(hash(i.xy + i.z), hash(i.xy + vec2(1,0) + i.z), f.x),
                   mix(hash(i.xy + vec2(0,1) + i.z), hash(i.xy + vec2(1,1) + i.z), f.x), f.y),
               mix(mix(hash(i.xy + i.z + 1.0), hash(i.xy + vec2(1,0) + i.z + 1.0), f.x),
                   mix(hash(i.xy + vec2(0,1) + i.z + 1.0), hash(i.xy + vec2(1,1) + i.z + 1.0), f.x), f.y), f.z); }
  void main(){
    vec4 o = texture2D(uField, vUv); float h = heat(vUv); vec2 v = (o.ba - .5) * 2.;
    vec2 sp = vUv * vec2(uAsp, 1.);
    // the stop: a clean cut from the tail end into the head, its own anti-aliased edge with no outline on it;
    // the sides go a little before the centre line, so the end comes out as a rounded cap
    float cutA = 1.;
    if (uCut > -50.) { vec3 A = ageAt(uAge, vUv);
      float a0 = A.x - uSince + min(.3, A.y * A.y / (2. * .07 * max(A.z, .05)));
      float w = max(fwidth(a0) * 1.5, .004); cutA = 1. - smoothstep(uCut - w, uCut + w, a0); }
    float thr = .2 + (noise3d(vec3(sp * 30., uTime * 4.)) - .5) * .05;   // surface jitter: scale 30, fast
    // the liquid, as lava-lamp light: small molten globs, warped into each other and drifting upward
    vec2 lp = sp * 19. + vec2(0., -uTime * .49);
    float w1 = noise3d(vec3(lp, uTime * .22));
    float lv = noise3d(vec3(lp * 1.15 + vec2(w1 * 1.6, w1 * 1.1), uTime * .3 + 5.));
    float ink = smoothstep(.60, .74, lv);
    float oj = (noise3d(vec3(sp * 80., 0.)) - .5) * .06;                // outline jitter: scale 80, still
    vec2 dh = vec2(heat(vUv + vec2(.006, 0.)) - heat(vUv - vec2(.006, 0.)), heat(vUv + vec2(0., .006)) - heat(vUv - vec2(0., .006)));
    // edge ripple, at the head only: rings run outward in a band just outside the silhouette and displace the ground
    vec2 hd = vUv - uHead; hd.x *= uAsp;
    float near = smoothstep(.015, thr, h) * (1. - smoothstep(thr, thr + .03, h)) * exp(-dot(hd, hd) / .006) * uRip;
    float ring = sin(h * 90. - uTime * 9.);
    vec2 q = vUv + normalize(dh + 1e-5) * ring * near * .045 - v * .07;
    vec3 base = texture2D(uGround, vec2(.5, clamp((uScroll + (1. - q.y) * uVh) / uDoc, 0., 1.))).rgb;
    vec3 col = base * (1. + ring * near * .26);
    if (uMatch < .5) { float lb = dot(col, vec3(.2126, .7152, .0722)); col = clamp(lb + (col - lb) * (1. + near * 1.4), 0., 1.); }
    else col = liftL(base, ring * near * .06, 1.);                          // matched: the ripple bends the light, it adds no chroma
    // the ember: the page's colour pushed to high chroma; the tail keeps the head's intensity
    float hi = max(h, .75), l = dot(base, vec3(.2126, .7152, .0722));
    vec3 hot = clamp(l + (base - l) * (1. + 3.4 * hi), 0., 1.);
    float hs = h - ink * .035;
    // the edge in screen distance (heat over its slope), so jitter and bumps move it by pixels, never by fragments
    float G = max(length(dh) / .012, .5);
    float sd = (h - .2) / G + (noise3d(vec3(sp * 30., uTime * 4.)) - .5) * .003 - ink * .0025;
    float aa = fwidth(sd);
    float body = smoothstep(-aa, aa + .002, sd) * cutA;
    vec3 nrm = normalize(vec3(-dh * 9., 1.));
    float diff = dot(nrm, normalize(vec3(2., 4., 5.)));
    float fd = max(fwidth(diff), 1e-4);                                 // cel bands keep their values, edges over a pixel
    float cel = smoothstep(.1 - fd, .1 + fd, diff) * .4 + smoothstep(.5 - fd, .5 + fd, diff) * .5 + .1;
    vec3 core = mix(hot, vec3(1.), .26) * 1.06;                        // the globs run toward white heat
    vec3 liquid = mix(hot * .93, core, ink);                            // both tones are light
    vec3 glow = core * pow(lv, 3.) * .9;
    float fres = pow(1. - nrm.z, 3.);
    vec3 rim = hot * .6 * fres * 2.5;
    vec3 emb = liquid * cel + glow + rim;
    float edge = max(smoothstep(thr + .02 + oj, thr + .09 + oj, hs),   // the marker outline thickens as it cools,
                     smoothstep(.0035, .0060, sd));                     // but is never wider than about 5 px
    emb = mix(vec3(.03), emb, edge) + rim * .6;
    if (uMatch > .5) {                                                   // matched: every tone is the page's own colour, lighter or darker
      float dl = .08 + .12 * cel + ink * .10 + pow(lv, 3.) * .10 + fres * .14;
      emb = mix(liftL(base, -.6, 1.), liftL(base, dl, uCk), edge); }
    col = mix(col, emb, body);
    gl_FragColor = vec4(clamp(col, 0., 1.), 1.); }`;

if (typeof window !== "undefined") { window.EmberEngine = EmberEngine; window.EmberMath = EmberMath; }
