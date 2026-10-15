// c3, the ember's light, moved verbatim from brand/ember-directions/satin-combined.html (its first script: the input, the
// glide, the touches, the cooling and the surfaces). It draws its frame onto a 2D canvas over a base: the satin cloth's
// canvas when the cloth drew, otherwise the page view (the prototype's frame function for mode X1).
// Only the wiring changed: the state lives in this closure instead of globals, and touch input is added (spec §6).

import { prof } from "./prof.js";

const FALL = [[216,178,96],[188,111,76],[137,58,80],[52,29,94]];
// how much the page is lifted under the ember's own glow where the ground is dark (see liftedPage)
export const LIFT = 0.4;   // 15 Oct, picked by eye by Aaron (0.6 matched gold sheet 03 and was "too intense")

export function createC3({ canvas = document.createElement("canvas"), glideOn = true, once = true, darkLift = LIFT } = {}) {
  const c2 = canvas, ctx = c2.getContext("2d");
  const fx = document.createElement("canvas"), fctx = fx.getContext("2d");   // the satin reads the ember's shape from here
  const tmp = document.createElement("canvas"), tctx = tmp.getContext("2d");
  const bl = document.createElement("canvas"), bctx = bl.getContext("2d");   // the light blurred once, used twice by the surfaces (same pixels)
  let viewStamp = 0;
  const probe = document.createElement("canvas"), pctx = probe.getContext("2d", { willReadFrequently: true });
  let W = 0, H = 0, DPR = 1, img = null, ready = false, light = false;
  let fresh = [], trail = [], last = null;

  function size(w, h, dpr) {
    DPR = dpr; W = w; H = h;
    for (const c of [c2, fx, tmp, bl]) { c.width = W * DPR; c.height = H * DPR; }
    probe.width = 192; probe.height = Math.round(192 * H / W);
    if (ready) pctx.drawImage(img, ...cover(probe.width, probe.height));
  }
  function cover(w, h) {
    const nw = img.naturalWidth || img.width, nh = img.naturalHeight || img.height;
    const s = Math.max(w / nw, h / nh);
    return [0, 0, nw, nh, (w - nw * s) / 2, 0, nw * s, nh * s];
  }
  // the page as drawn (the page view, or a capture): the probe the touches sample their colour from, and whether it is light
  function setPage(im) {
    img = im; ready = true; viewStamp++;
    pctx.drawImage(img, ...cover(probe.width, probe.height));
    const [r, g, b] = pctx.getImageData(probe.width >> 1, probe.height >> 1, 1, 1).data; light = (0.2126 * r + 0.7152 * g + 0.0722 * b) > 140;
  }
  const lum = c => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  function sample(x, y) {
    const px = Math.max(0, Math.min(probe.width - 1, Math.round(x / W * probe.width)));
    const py = Math.max(0, Math.min(probe.height - 1, Math.round(y / H * probe.height)));
    return Array.from(pctx.getImageData(px, py, 1, 1).data.slice(0, 3));
  }
  function lift(c, k = 1.6) { const L = lum(c), up = light ? 1 : 1.1, add = light ? 0 : 8; return c.map(v => Math.max(0, Math.min(255, (L + (v - L) * k) * up + add))); }
  const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  function lay(x, y, t, sp, ang) { const c = sample(x, y), q = { x, y, t, sp, ang, base: c, c: lift(c) }; fresh.push(q); trail.push(q); }
  let vel = { x: 0, y: 0 }, glide = null;
  const GLIDE_T = 320, GLIDE_V = 0.6, STOP = 34;
  function move(x, y, now) {
    if (!ready) return;
    const p = { x, y, t: now };
    const dx = last ? p.x - last.x : 0, dy = last ? p.y - last.y : 0, dist = Math.hypot(dx, dy);
    const sp = last ? Math.min(1.5, dist / Math.max(8, now - last.t)) : 0, ang = Math.atan2(dy, dx);
    if (last) { const k = 0.5, ddt = Math.max(8, now - last.t); vel = { x: vel.x * (1 - k) + dx / ddt * k, y: vel.y * (1 - k) + dy / ddt * k }; }
    const n = last ? Math.max(1, Math.ceil(dist / 10)) : 1;
    for (let i = 1; i <= n; i++) lay(last ? last.x + dx * i / n : p.x, last ? last.y + dy * i / n : p.y, now, sp, ang);
    last = p; glide = null;
  }
  function glideStep(now) {
    if (!glideOn) return;   // reduced motion: no glide
    if (!last || now - last.t < STOP) return;
    if (!glide) {
      const v = Math.hypot(vel.x, vel.y); if (v < 0.02) return;
      const v0 = Math.min(GLIDE_V, v);
      glide = { x0: last.x, y0: last.y, ux: vel.x / v, uy: vel.y / v, v0, t0: now, d: 0, done: false };
    }
    if (glide.done) return;
    const t = Math.min(1, (now - glide.t0) / GLIDE_T), dist = glide.v0 * GLIDE_T / 3 * (1 - (1 - t) ** 3), sp = glide.v0 * (1 - t) ** 2;
    while (glide.d + 10 <= dist) { glide.d += 10; lay(glide.x0 + glide.ux * glide.d, glide.y0 + glide.uy * glide.d, now, sp, Math.atan2(glide.uy, glide.ux)); }
    if (t >= 1) glide.done = true;
  }

  // ---- c3, verbatim from a2-family.html ----
  function round(p, r = 90 + 110 * p.sp, a = 0.10, c = p.c) {
    const g = fctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r);
    g.addColorStop(0, rgba(c, a)); g.addColorStop(0.5, rgba(c, a * 0.4)); g.addColorStop(1, rgba(c, 0));
    fctx.fillStyle = g; fctx.fillRect(p.x - r, p.y - r, 2 * r, 2 * r);
  }
  function cooling(now, o) {
    trail = trail.filter(p => now - p.t < o.life); fresh = [];
    fctx.setTransform(DPR, 0, 0, DPR, 0, 0); fctx.clearRect(0, 0, W, H); fctx.globalCompositeOperation = "lighter";
    const every = o.every || 2;
    trail.forEach((p, i) => {
      if (i % every && i !== trail.length - 1) return;
      const age = (now - p.t) / o.life, k = Math.min(2.999, age * 3), j = k | 0;
      const cooled = mix(FALL[j], FALL[j + 1], k - j);
      const c = mix(lift(mix(p.base, FALL[0], 0.35), 1.5), cooled, Math.min(1, age * 1.4));
      round(p, (o.r + o.rs * p.sp) * (1 + age * o.grow), o.a * (1 - age) ** 1.3, c);
    });
    fctx.setTransform(1, 0, 0, 1, 0, 0); fctx.globalCompositeOperation = "source-over";
  }
  function surfaces() {
    tctx.setTransform(1, 0, 0, 1, 0, 0); tctx.clearRect(0, 0, tmp.width, tmp.height);
    if (once) { bctx.clearRect(0, 0, bl.width, bl.height); bctx.filter = `blur(${6 * DPR}px)`; bctx.drawImage(fx, 0, 0); bctx.filter = "none"; tctx.drawImage(bl, 0, 0); }
    else { tctx.filter = `blur(${6 * DPR}px)`; tctx.drawImage(fx, 0, 0); tctx.filter = "none"; }
    tctx.globalCompositeOperation = "multiply";
    const pg = liftedPage();
    for (let i = 0; i < 3; i++) tctx.drawImage(pg, ...cover(tmp.width, tmp.height));
    tctx.globalCompositeOperation = "destination-in"; if (once) tctx.drawImage(bl, 0, 0); else { tctx.filter = `blur(${6 * DPR}px)`; tctx.drawImage(fx, 0, 0); tctx.filter = "none"; }
    tctx.globalCompositeOperation = "source-over";
    ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.drawImage(tmp, 0, 0); ctx.drawImage(tmp, 0, 0); ctx.restore();
  }
  // 14 Oct, Aaron: "only increase the intensity of the ember glow in the darker areas of the guide". The glow above is
  // multiplied by the page view three times (its brightness cubed), so it vanishes on dark grounds. Where the GROUND is dark
  // (the satin shader's curve, smoothstep(.42 -> .22) on luma) and off the content (type, photographs, panels and swatches,
  // where the page view differs from the ground view: the satin's onTop rule, softened by about 2 CSS px outside it), the
  // page it multiplies by is screened up by darkLift x darkness. Made once per views change, and only when the ember is lit;
  // where no ground is dark the page view itself is used, so light pages are unchanged to the byte.
  const ca = document.createElement("canvas"), cax = ca.getContext("2d", { willReadFrequently: true });
  const cb = document.createElement("canvas"), cbx = cb.getContext("2d", { willReadFrequently: true });
  const cm = document.createElement("canvas"), cmx = cm.getContext("2d");
  const cs = document.createElement("canvas"), csx = cs.getContext("2d");
  const lp = document.createElement("canvas"), lpx = lp.getContext("2d");
  let gimg = null, lifted = null, liftFor = -1;
  const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  function liftedPage() {
    if (!darkLift || !gimg) return img;
    if (liftFor === viewStamp) return lifted || img;
    liftFor = viewStamp; lifted = null;
    const w = Math.max(1, Math.round(W)), h = Math.max(1, Math.round(H));
    for (const c of [ca, cb, cm, cs]) if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    cax.drawImage(img, ...cover(w, h)); cbx.drawImage(gimg, ...cover(w, h));
    const A = cax.getImageData(0, 0, w, h), B = cbx.getImageData(0, 0, w, h), a = A.data, b = B.data;
    let any = false;
    for (let i = 0; i < a.length; i += 4) {
      const d = Math.hypot(a[i] - b[i], a[i + 1] - b[i + 1], a[i + 2] - b[i + 2]) / 255;
      const dark = smooth(.42, .22, (.2126 * b[i] + .7152 * b[i + 1] + .0722 * b[i + 2]) / 255), v = 255 * darkLift * dark;
      if (v >= .5) any = true;
      a[i] = a[i + 1] = a[i + 2] = 0; a[i + 3] = 255 * smooth(.006, .025, d);   // the content
      b[i] = b[i + 1] = b[i + 2] = v; b[i + 3] = 255;                           // the lift
    }
    if (!any) return img;
    cmx.putImageData(A, 0, 0);
    // the content mask, then softened copies of it on top: a soft edge about 2 CSS px wide outside the content, so edges
    // do not halo, while thin type keeps its full mask
    csx.clearRect(0, 0, w, h); csx.drawImage(cm, 0, 0); csx.filter = "blur(2px)"; csx.drawImage(cm, 0, 0); csx.drawImage(cm, 0, 0); csx.filter = "none";
    cbx.putImageData(B, 0, 0); cbx.globalCompositeOperation = "destination-out"; cbx.drawImage(cs, 0, 0); cbx.globalCompositeOperation = "source-over";
    const [nw, nh] = [img.naturalWidth || img.width, img.naturalHeight || img.height];
    if (lp.width !== nw || lp.height !== nh) { lp.width = nw; lp.height = nh; }
    lpx.globalCompositeOperation = "copy"; lpx.drawImage(img, 0, 0);
    const [, , , , dx, dy, dw, dh] = cover(w, h);   // the views were drawn into w x h this way; drawn back the other way
    lpx.globalCompositeOperation = "screen"; lpx.drawImage(cb, dx, dy, dw, dh, 0, 0, nw, nh); lpx.globalCompositeOperation = "source-over";
    return (lifted = lp);
  }
  function c3(now) { glideStep(now); let t = prof.mark(); cooling(now, { r: 52, rs: 40, a: 0.42, life: 900, grow: 0.25 }); prof.add('c3.cooling', t); t = prof.mark(); surfaces(); prof.add('c3.surfaces', t); }

  // the prototype's frame for mode X1: the cloth when it drew, else the page as drawn, then c3 over it
  // still: the last frame had no light and nothing is pending (no touch alive, no glide to come), so it was the base alone
  let dark = false;
  function still(now) {
    if (!ready || !dark || trail.some(p => now - p.t < 900)) return false;
    return !glideOn || !last || (glide ? glide.done : Math.hypot(vel.x, vel.y) < 0.02);
  }
  function frame(now, base) {
    if (!ready) return false;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, c2.width, c2.height);
    const t = prof.mark(); if (base) ctx.drawImage(base, 0, 0, c2.width, c2.height); else ctx.drawImage(img, ...cover(c2.width, c2.height)); prof.add('c3.base', t);
    c3(now); dark = trail.length === 0;
    return true;
  }

  // input (spec §6): pointer movement on the window, passive. A finger is the cursor while it is down (touch events keep
  // coming while the browser scrolls, pointer events do not); lifting it is a stop, so the glide and settle run; a tap lays
  // one touch. Nothing here prevents scrolling.
  const opts = { passive: true };
  const onPointer = e => { if (e.pointerType !== "touch") move(e.clientX, e.clientY, performance.now()); };
  const onTouchStart = e => { const t = e.touches[0]; if (!t) return; last = null; vel = { x: 0, y: 0 }; glide = null; move(t.clientX, t.clientY, performance.now()); };
  const onTouchMove = e => { const t = e.touches[0]; if (t) move(t.clientX, t.clientY, performance.now()); };
  function attach(target = window) {
    target.addEventListener("pointermove", onPointer, opts);
    target.addEventListener("touchstart", onTouchStart, opts);
    target.addEventListener("touchmove", onTouchMove, opts);
    return () => {
      target.removeEventListener("pointermove", onPointer, opts);
      target.removeEventListener("touchstart", onTouchStart, opts);
      target.removeEventListener("touchmove", onTouchMove, opts);
    };
  }

  return {
    canvas: c2, light: fx, size, setPage, frame, move, attach, still,
    get trail() { return trail; },
    setGlide(on) { glideOn = on; if (!on) glide = null; },
    setGround(g) { gimg = g; viewStamp++; },
    get lifting() { return !!lifted && liftFor === viewStamp; },
  };
}
