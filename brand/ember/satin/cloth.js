// The satin, moved from brand/ember-directions/satin-combined.html (its second script, "the ground is a real sheet of
// cloth"), P2d only: the V2 weight with P2d's cloth overrides, the press, the ember-shape mask with its 1.7 s hold, the
// elements' light (elem 2), the eased bend at x3 and the satin fragment shader at a third. The variant table, its buttons,
// the notes, P2e's crisp mode, the band mode and the strength buttons are removed. The cursor grab is removed too: P2d's
// grab is 0, so it never moved the cloth.
// Changes the plan asks for: the grid, steps and pixel ratio come from the tier; the rim and the bend cap from phoneSizes;
// the bend is measured in CSS px (4 CSS px base at any width) and clamped to the tier's cap; mediump on phones; the ember's
// shape is read from c3's light canvas passed in here.
import * as THREE from "three";
import { bendStep, phoneSizes } from "./satin-math.js";
import { prof } from "./prof.js";

// V2 weight with P2d's overrides. grab: how much of the drag the cloth takes; home: pull back to flat per step; damp;
// bend: fold stiffness; iters: constraint passes; depth: shading relief
const CLOTH = { grab: 0, reach: 250, home: .0035, damp: .97, bend: .32, iters: 5, depth: 3 };
// where the folds may show: only inside the ember's own shape and a short way past its rim (14 Oct: "they should contour the
// shape of the ember and only radiate a short distance from it"). hold: how long the shape lingers after the ember has gone, s
const P2D = { hold: 1.7, press: 17 };
const STRENGTH = .33;   // picked by eye, 14 Oct: P2d at a third. How much of the satin shows: the folds are a hint in the ground, not an object
const BEND_GAIN = 3;    // picked by eye, 14 Oct: x3
// Aaron judged the prototype in a real browser running it at about 33 fps, and the prototype advances everything per frame:
// one mask update (its hold and fade), two cloth steps and one bend-easing step. So that is one fixed unit here, run 33
// times a second whatever the display's rate, from an accumulator; at most two units (four cloth steps) catch up in one
// rendered frame, and any excess is dropped, so a slow frame never spirals. Every frame renders the latest state.
const UNIT = 1000 / 33, CATCH_UP = 2;

// one fabric constraint between particles a and b, on the positions array (module level, no closure, so it inlines)
function constrain(pos, a, b, len, k) {
  const ax = a * 3, bx = b * 3;
  const dx = pos[bx] - pos[ax], dy = pos[bx + 1] - pos[ax + 1], dz = pos[bx + 2] - pos[ax + 2];
  const d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1e-6, c = (d - len) / d * .5 * k;
  pos[ax] += dx * c; pos[ax + 1] += dy * c; pos[ax + 2] += dz * c; pos[bx] -= dx * c; pos[bx + 1] -= dy * c; pos[bx + 2] -= dz * c;
}

// THREE's computeVertexNormals for an indexed geometry, on the typed arrays directly (same sums in the same order, without a
// Vector3 per read): each face's cross product (C - B) x (A - B) is added to its three corners, then every normal is normalised
function vertexNormals(geo) {
  const p = geo.attributes.position.array, na = geo.attributes.normal, n = na.array, ix = geo.index.array;
  n.fill(0);
  for (let f = 0; f < ix.length; f += 3) {
    const a = ix[f] * 3, b = ix[f + 1] * 3, c = ix[f + 2] * 3;
    const cbx = p[c] - p[b], cby = p[c + 1] - p[b + 1], cbz = p[c + 2] - p[b + 2];
    const abx = p[a] - p[b], aby = p[a + 1] - p[b + 1], abz = p[a + 2] - p[b + 2];
    const x = cby * abz - cbz * aby, y = cbz * abx - cbx * abz, z = cbx * aby - cby * abx;
    n[a] += x; n[a + 1] += y; n[a + 2] += z; n[b] += x; n[b + 1] += y; n[b + 2] += z; n[c] += x; n[c + 1] += y; n[c + 2] += z;
  }
  for (let i = 0; i < n.length; i += 3) { const s = 1 / (Math.sqrt(n[i] * n[i] + n[i + 1] * n[i + 1] + n[i + 2] * n[i + 2]) || 1); n[i] *= s; n[i + 1] *= s; n[i + 2] *= s; }
  na.needsUpdate = true;
}

export function createCloth({ light, tier, dpr, mediump = false }) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, precision: mediump ? "mediump" : "highp" });
  renderer.setPixelRatio(dpr);
  let W = 1, H = 1;
  const camera = new THREE.OrthographicCamera(0, W, H, 0, -2000, 2000);
  const scene = new THREE.Scene();
  const tex = { page: null, ground: null };
  let rim = phoneSizes(tier.name).rim, bendCap = phoneSizes(tier.name).bendCap, steps = tier.steps;
  let bendOn = true, acc = 0, lastT = null, probe = null;
  function logProbe(t) {
    const b = geo.attributes.bend.array; let s = 0;
    for (const i of probe.idx) s += Math.hypot(b[i * 2], b[i * 2 + 1]) * BEND_GAIN * 4;
    probe.log.push([t, s / probe.idx.length]);
  }
  // still: the last tick changed nothing that is drawn (the mask exactly; the drawn cloth within 1/100 px and the eased bend within 1/1000 px, below float32 jitter), so the next tick over a
  // dark light would draw the same frame and the engine may skip it. The press can leave a faint mask (alpha rounds to a
  // fixed point under the hold's fade), so this tests for no change, not for an empty mask.
  let still = false, snapP = null, snapB = null, snapM = null;
  function stillCheck() {
    const p = geo.attributes.position.array, b = geo.attributes.bend.array;
    let s = !!snapP && snapP.length === p.length && snapB.length === b.length && !!md && !!snapM && snapM.length === md.length;
    if (s) for (let i = 0; i < p.length; i++) if (Math.abs(p[i] - snapP[i]) > 1e-2) { s = false; break; }   // 1/100 px: float32 rounding at the frame's far edge alone jitters about 1e-3
    if (s) for (let i = 0; i < b.length; i++) if (Math.abs(b[i] - snapB[i]) > 1e-4) { s = false; break; }   // 1e-4 of bend is about 1/1000 CSS px
    if (s) for (let i = 3; i < md.length; i += 4) if (md[i] !== snapM[i]) { s = false; break; }
    if (!snapP || snapP.length !== p.length) snapP = new Float32Array(p.length); snapP.set(p);
    if (!snapB || snapB.length !== b.length) snapB = new Float32Array(b.length); snapB.set(b);
    if (md) { if (!snapM || snapM.length !== md.length) snapM = new Uint8ClampedArray(md.length); snapM.set(md); }
    return s;
  }

  // the cloth
  let NX = tier.grid[0], NY = tier.grid[1];
  const OVER = .3;   // the cloth reaches 30% past every edge of the screen, so where it is held is never seen
  let pos, prev, rest, geo, mesh, mat, bendA;
  function build(w, h, t = tier, d = dpr) {
    tier = t; NX = tier.grid[0]; NY = tier.grid[1]; steps = tier.steps; ({ rim, bendCap } = phoneSizes(tier.name));
    renderer.setPixelRatio(d);
    W = w; H = h;
    renderer.setSize(W, H); camera.right = W; camera.top = H; camera.updateProjectionMatrix();
    if (mesh) { scene.remove(mesh); geo.dispose(); }
    geo = new THREE.PlaneGeometry(W * (1 + 2 * OVER), H * (1 + 2 * OVER), NX - 1, NY - 1);
    geo.translate(W / 2, H / 2, 0);
    const a = geo.attributes.position.array;
    rest = new Float32Array(a); pos = new Float32Array(a); prev = new Float32Array(a);
    // the weave is never perfectly flat: a whisper of relief lets compression buckle into folds
    for (let i = 0; i < NX * NY; i++) { const x = rest[i * 3], y = rest[i * 3 + 1];
      const z = (Math.sin(x * .031 + y * .017) + Math.sin(x * .013 - y * .029 + 2.)) * .35; pos[i * 3 + 2] = prev[i * 3 + 2] = z; rest[i * 3 + 2] = z; }
    geo.setAttribute("move", new THREE.BufferAttribute(new Float32Array(NX * NY), 1));
    geo.setAttribute("bend", new THREE.BufferAttribute(new Float32Array(NX * NY * 2), 2)); bendA = new Float32Array(NX * NY * 2);
    mesh = new THREE.Mesh(geo, mat); scene.add(mesh);
    MH = Math.round(MW * H / W); hist.length = 0; mx2.clearRect(0, 0, MW, MH); still = false;
    fit();
  }
  mat = new THREE.ShaderMaterial({
    uniforms: { page: { value: null }, ground: { value: null }, res: { value: new THREE.Vector2(1, 1) }, rect: { value: new THREE.Vector4(0, 0, 1, 1) }, depth: { value: CLOTH.depth }, amount: { value: STRENGTH }, mask: { value: null }, bendGain: { value: BEND_GAIN }, dpr: { value: dpr }, bendCap: { value: bendCap } },
    vertexShader: `
      attribute float move; attribute vec2 bend; varying vec3 vN; varying float vZ; varying float vMove; varying vec2 vBend;
      void main(){ vN = normalize(normalMatrix * normal); vZ = position.z; vMove = move; vBend = bend; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      precision ${mediump ? "mediump" : "highp"} float;
      uniform sampler2D page, ground; uniform vec2 res; uniform vec4 rect; uniform float depth, amount; uniform sampler2D mask;
      varying vec3 vN; varying float vZ; varying float vMove; varying vec2 vBend; uniform float bendGain, dpr, bendCap;
      vec3 screen(vec3 a, vec3 b){ return 1. - (1. - a) * (1. - b); }
      float lum(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
      void main(){
        vec2 f = gl_FragCoord.xy;   // screen px: the page is pinned, only the cloth moves
        vec2 p = vec2(f.x, res.y - f.y); vec2 iu = (p - rect.xy) / rect.zw;
        vec3 n = normalize(vN); n.xy *= depth * smoothstep(.0, 2.5, vMove); n = normalize(n);   // only cloth that has really moved shows relief
        float ma = texture2D(mask, p / res).a;
        float m = smoothstep(.0, .6, ma);   // the ember's shape, softened by its rim
        // type, panels and photographs are printed on the satin, so they bend a few px with the swell. The bend is fixed at
        // what was picked at a tenth (x3), whatever the satin's strength; 4 CSS px base at any width, clamped to the tier's cap
        vec2 off = vBend * bendGain * 4. * dpr; float ol = length(off), cap = bendCap * dpr; if (ol > cap) off *= cap / ol;
        iu = (p - off - rect.xy) / rect.zw;
        vec3 pg = texture2D(page, iu).rgb, gd = texture2D(ground, iu).rgb;
        vec3 L = normalize(vec3(-.42, .6, .68)), V = vec3(0., 0., 1.), Hh = normalize(L + V);
        float diff = dot(n, L) - L.z;   // relative to the flat sheet: at rest the ground is exactly as drawn
        // satin: a narrow sheen that runs along the folds (anisotropic, threads running across the page)
        vec3 T = normalize(vec3(1., 0., 0.) - n * n.x); float th = dot(T, Hh);
        float shp = 26.;
        float aniso = pow(sqrt(max(0., 1. - th * th)), shp) - pow(sqrt(max(0., 1. - pow(dot(normalize(vec3(1.,0.,0.)), Hh), 2.))), shp);   // low, wide satin sheen
        float dark = smoothstep(.42, .22, lum(gd));
        float up = clamp(diff * 1.7 + max(0., aniso) * .45, 0., 1.), down = clamp(-diff * 2.6, 0., 1.);
        vec3 hi = mix(screen(gd, vec3(.40, .34, .24)), screen(gd, gd * .9 + vec3(.08)), dark);
        vec3 lo = mix(gd * .66, gd * .42, dark);   // deep, soft valleys
        float grain = (fract(sin(dot(floor(f), vec2(12.9898, 78.233))) * 43758.5453) - .5) * .06 * smoothstep(.0, .02, 1. - n.z);
        float am = amount * m;
        vec3 sat = mix(gd, mix(mix(gd, hi, up), lo, down) + grain, am);
        float onTop = smoothstep(.006, .025, distance(pg, gd));
        // the elements take the same light and shade as the satin they sit on, in their own colour
        vec3 el = mix(pg, mix(mix(pg, screen(pg, vec3(.40, .34, .24)), up), pg * .66, down), am);
        gl_FragColor = vec4(mix(pg * (sat / max(gd, vec3(.004))), el, onTop), 1.);
      }`,
  });

  // cloth step: verlet, then fabric constraints (stretch, shear, bend), then a gentle pull back to flat
  const idx = (i, j) => j * NX + i;
  function step() {
    const o = CLOTH, rp = P2D;
    const sx = W * (1 + 2 * OVER) / (NX - 1), sy = H * (1 + 2 * OVER) / (NY - 1), dg = Math.hypot(sx, sy);
    for (let i = 0; i < NX * NY; i++) {
      const k = i * 3;
      const vx = (pos[k] - prev[k]) * o.damp, vy = (pos[k + 1] - prev[k + 1]) * o.damp, vz = (pos[k + 2] - prev[k + 2]) * o.damp;
      prev[k] = pos[k]; prev[k + 1] = pos[k + 1]; prev[k + 2] = pos[k + 2];
      pos[k] += vx; pos[k + 1] += vy; pos[k + 2] += vz;
      let zr = rest[k + 2];
      if (rp.press && md) {   // the ember presses the cloth down where it lies
        const mx = Math.min(MW - 1, Math.max(0, pos[k] / W * MW | 0)), my = Math.min(MH - 1, Math.max(0, (H - pos[k + 1]) / H * MH | 0));
        zr -= rp.press * md[(my * MW + mx) * 4 + 3] / 255;
      }
      pos[k] += (rest[k] - pos[k]) * o.home; pos[k + 1] += (rest[k + 1] - pos[k + 1]) * o.home; pos[k + 2] += (zr - pos[k + 2]) * Math.max(o.home, rp.press ? .08 : 0);
    }
    const P = pos, R = rest, nx = NX, ny = NY, bend = o.bend, bendL = o.bend * .35;
    for (let it = 0; it < o.iters; it++) {
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
        const a = j * nx + i;
        if (i < nx - 1) constrain(P, a, a + 1, sx, 1);
        if (j < ny - 1) constrain(P, a, a + nx, sy, 1);
        if (i < nx - 1 && j < ny - 1) { constrain(P, a, a + nx + 1, dg, .5); constrain(P, a + 1, a + nx, dg, .5); }
        if (i < nx - 2) constrain(P, a, a + 2, sx * 2, bend);
        if (j < ny - 2) constrain(P, a, a + 2 * nx, sy * 2, bend);
        if (i < nx - 4) constrain(P, a, a + 4, sx * 4, bendL);   // long-range stiffness: a few broad swells, never pleats
        if (j < ny - 4) constrain(P, a, a + 4 * nx, sy * 4, bendL);
      }
      // the edges are held
      for (let i = 0; i < nx; i++) for (let e = 0; e < 2; e++) { const k = ((e ? ny - 1 : 0) * nx + i) * 3; P[k] = R[k]; P[k + 1] = R[k + 1]; P[k + 2] = R[k + 2]; }
      for (let j = 0; j < ny; j++) for (let e = 0; e < 2; e++) { const k = (j * nx + (e ? nx - 1 : 0)) * 3; P[k] = R[k]; P[k + 1] = R[k + 1]; P[k + 2] = R[k + 2]; }
    }
    // what is drawn is the cloth with its relief smoothed once, so the mesh never shows as a stitched crest
    const out = geo.attributes.position.array; out.set(pos);
    for (let j = 1; j < NY - 1; j++) for (let i = 1; i < NX - 1; i++) { const k = idx(i, j) * 3 + 2;
      out[k] = pos[k] * .4 + (pos[idx(i - 1, j) * 3 + 2] + pos[idx(i + 1, j) * 3 + 2] + pos[idx(i, j - 1) * 3 + 2] + pos[idx(i, j + 1) * 3 + 2]) * .15; }
    const mv = geo.attributes.move.array;
    for (let i = 0; i < NX * NY; i++) { const k = i * 3; const ex = pos[k] - rest[k], ey = pos[k + 1] - rest[k + 1], ez = (pos[k + 2] - rest[k + 2]) * 2; mv[i] = Math.sqrt(ex * ex + ey * ey + ez * ez); }
    geo.attributes.move.needsUpdate = true;
    const tn = prof.mark(); geo.attributes.position.needsUpdate = true; vertexNormals(geo); prof.add('cloth.normals', tn);
  }

  // the page and ground views (canvases, or images for the side-by-side)
  function setViews(page, ground) {
    if (tex.page) { tex.page.dispose(); tex.ground.dispose(); }
    tex.page = new THREE.CanvasTexture(page); tex.ground = new THREE.CanvasTexture(ground);
    for (const t of [tex.page, tex.ground]) { t.colorSpace = THREE.NoColorSpace; t.flipY = false; t.minFilter = t.magFilter = THREE.LinearFilter; t.generateMipmaps = false; }
    mat.uniforms.page.value = tex.page; mat.uniforms.ground.value = tex.ground;
    fit();
  }
  function fit() {
    if (!tex.page || !tex.page.image) return;
    const im = tex.page.image, dpr = renderer.getPixelRatio(), iw = im.naturalWidth || im.width, ih = im.naturalHeight || im.height; if (!iw) return;
    const s = Math.max(W / iw, H / ih);
    mat.uniforms.res.value.set(W * dpr, H * dpr);
    mat.uniforms.rect.value.set((W - iw * s) / 2 * dpr, 0, iw * s * dpr, ih * s * dpr);
    mat.uniforms.dpr.value = dpr; mat.uniforms.bendCap.value = bendCap;
  }
  // the ember's shape, small and softened by the rim, for the mask and the press
  const MW = 180, mc = document.createElement("canvas"), mx2 = mc.getContext("2d", { willReadFrequently: true }); let MH = 112, md = null;
  // the light is shrunk on the GPU first, so only the small image is read back to the CPU canvas (not the full-size light)
  // The prototype's mask, on each of its frames, read the light c3 drew on the frame before: light one prototype frame
  // (UNIT) old. A faster display draws the light more often, so the light is kept as a short history of small copies,
  // one per rendered frame, and each unit reads the copy nearest to UNIT before it.
  const hist = [];   // { c, x, t }, newest last
  function snapLight(t) {
    let h = hist.length >= 12 ? hist.shift() : null;
    if (!h) { const c = document.createElement("canvas"); h = { c, x: c.getContext("2d") }; }
    if (h.c.width !== MW || h.c.height !== MH) { h.c.width = MW; h.c.height = MH; }
    h.x.clearRect(0, 0, MW, MH); h.x.drawImage(light, 0, 0, MW, MH); h.t = t; hist.push(h);
  }
  function lightAt(t) {
    let best = hist[hist.length - 1];
    for (const h of hist) if (Math.abs(h.t - t) < Math.abs(best.t - t)) best = h;
    return best.c;
  }
  const maskTex = new THREE.CanvasTexture(mc); maskTex.flipY = false; maskTex.colorSpace = THREE.NoColorSpace; maskTex.minFilter = maskTex.magFilter = THREE.LinearFilter;
  function emberShape(src) {
    const rp = P2D;
    MH = Math.round(MW * H / W); if (mc.height !== MH) { mc.width = MW; mc.height = MH; }
    const k = MW / W;
    mx2.globalCompositeOperation = "destination-out"; mx2.fillStyle = `rgba(0,0,0,${Math.min(1, 1 / (60 * rp.hold) * 3)})`; mx2.fillRect(0, 0, MW, MH); mx2.globalCompositeOperation = "lighter";   // the shape lingers, fading over hold
    mx2.filter = `blur(${rim * k}px)`;
    mx2.drawImage(src, 0, 0); mx2.filter = "none"; mx2.globalCompositeOperation = "source-over";
    md = mx2.getImageData(0, 0, MW, MH).data;
    maskTex.needsUpdate = true; mat.uniforms.mask.value = maskTex;
  }
  // the bend the elements follow is eased on its own: it gathers over about a fifth of a second and lets go over about a second,
  // through two smoothing stages, so it starts and finishes softly instead of snapping back as the swell lies down
  let bendB = null;
  function easeTheBend() {
    if (!bendB || bendB.length !== NX * NY * 2) bendB = new Float32Array(NX * NY * 2);
    const z = geo.attributes.position.array, mv = geo.attributes.move.array, out = geo.attributes.bend.array, d = CLOTH.depth || 3;
    const sx = W * (1 + 2 * OVER) / (NX - 1), sy = H * (1 + 2 * OVER) / (NY - 1);
    for (let j = 1; j < NY - 1; j++) for (let i = 1; i < NX - 1; i++) {
      const v = idx(i, j), k = v * 3;
      let gx = -(z[(v + 1) * 3 + 2] - z[(v - 1) * 3 + 2]) / (2 * sx) * d, gy = -(z[(v + NX) * 3 + 2] - z[(v - NX) * 3 + 2]) / (2 * sy) * d;
      const l = Math.sqrt(gx * gx + gy * gy + 1), on = Math.min(1, Math.max(0, mv[v] / 2.5)), g = on * on * (3 - 2 * on);
      let mk = 1;
      if (md) { const mx = Math.min(MW - 1, Math.max(0, rest[k] / W * MW | 0)), my = Math.min(MH - 1, Math.max(0, (H - rest[k + 1]) / H * MH | 0)), a = Math.min(1, md[(my * MW + mx) * 4 + 3] / 255 / .6); mk = a * a * (3 - 2 * a); }
      const tx = gx / l * g * mk * .65, ty = gy / l * g * mk * .65;   // matched to P2b's deepest bend
      for (const [c, t] of [[0, tx], [1, ty]]) {
        const b = v * 2 + c; [bendA[b], bendB[b]] = bendStep(bendA[b], bendB[b], t); out[b] = bendB[b];
      }
    }
    geo.attributes.bend.needsUpdate = true;
  }
  // frame budget level 1 and reduced motion: no bend. The eased bend is let go at once, so nothing is left displaced
  function setBend(on) {
    if (on === bendOn) return; bendOn = on; mat.uniforms.bendGain.value = on ? BEND_GAIN : 0;
    still = false;
    if (!on && bendA) { bendA.fill(0); if (bendB) bendB.fill(0); geo.attributes.bend.array.fill(0); geo.attributes.bend.needsUpdate = true; }
  }

  return {
    canvas: renderer.domElement, build, setViews, setBend,
    refresh() { if (tex.page) { tex.page.needsUpdate = tex.ground.needsUpdate = true; fit(); } },
    // one rendered frame at time now (ms): the fixed units due since the last frame, then the render
    tick(now = performance.now()) {
      if (!mesh || !mat.uniforms.page.value) return false;
      snapLight(lastT === null ? now - UNIT : lastT);   // the light c3 drew on the last rendered frame
      acc = lastT === null ? UNIT : acc + Math.max(0, now - lastT); lastT = now;
      let n = Math.floor(acc / UNIT + 1e-6);   // (the epsilon: a unit's worth of float sums is a unit)
      if (n > CATCH_UP) { n = CATCH_UP; acc = n * UNIT; }   // behind by more: the excess is dropped
      acc -= n * UNIT;
      for (let u = 0; u < n; u++) {
        let t = prof.mark(); emberShape(lightAt(now - acc - (n - u) * UNIT)); prof.add('cloth.mask', t); t = prof.mark(); for (let i = 0; i < steps; i++) step(); prof.add('cloth.sim', t);
        t = prof.mark(); if (bendOn) easeTheBend(); prof.add('cloth.bend', t); still = stillCheck();
        if (probe) logProbe(now - acc - (n - 1 - u) * UNIT);
      }
      const t = prof.mark(); renderer.render(scene, camera); prof.add('cloth.render', t); return true;
    },
    // the engine skipped frames (idle): the time it skipped is not owed
    rest() { lastT = null; acc = 0; },
    get still() { return still; },
    // for the idle check: the largest mask alpha (0-255), displacement from rest (the move attribute) and eased bend (CSS px)
    // for the no-snap check: the eased bend (CSS px, before the cap) at screen points (CSS px), logged once per unit with
    // the unit's own time, so a check can resample it without aliasing against the 33 Hz step
    probe(points) {
      if (!points) { probe = null; return; }
      probe = { log: [], idx: points.map(([x, y]) => { let best = 0, d = Infinity;
        for (let i = 0; i < NX * NY; i++) { const dx = rest[i * 3] - x, dy = rest[i * 3 + 1] - (H - y), e = dx * dx + dy * dy; if (e < d) { d = e; best = i; } }
        return best; }) };
    },
    get probeLog() { return probe ? probe.log : null; },
    info() {
      let m = 0, v = 0, b = 0; if (md) for (let i = 3; i < md.length; i += 4) if (md[i] > m) m = md[i];
      if (geo) { for (const x of geo.attributes.move.array) if (x > v) v = x; for (const x of geo.attributes.bend.array) if (Math.abs(x) > b) b = Math.abs(x); }
      // where the cloth has moved: the centroid (screen CSS px) of the displacement, for the scroll check
      let sx = 0, sy = 0, sw = 0;
      if (geo) { const mv = geo.attributes.move.array; for (let i = 0; i < mv.length; i++) if (mv[i] > .5) { sx += rest[i * 3] * mv[i]; sy += (H - rest[i * 3 + 1]) * mv[i]; sw += mv[i]; } }
      return { mask: m, move: v, bend: b * BEND_GAIN * 4, cx: sw ? sx / sw : null, cy: sw ? sy / sw : null };
    },
    dispose() { if (tex.page) { tex.page.dispose(); tex.ground.dispose(); } maskTex.dispose(); if (geo) geo.dispose(); mat.dispose(); renderer.dispose(); renderer.forceContextLoss(); },
  };
}
