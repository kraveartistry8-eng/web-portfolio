// Ember satin engine: the satin, c3 and the raking light over the live guide (spec 2026-10-14, plan Task 7).
// One fixed canvas above the deck shows the guide's own sheets, rasterised near the viewport (views.js), drawn on by the
// three layers in the spec's order (§3.6): the satin cloth, c3 over it, the raking light over both. The real HTML stays
// in the page, invisible, for links, selection, find-in-page and screen readers.
import { createViews } from "./views.js";
import { createC3 } from "./c3.js";
import { createCloth } from "./cloth.js";
import { createRake } from "./rake.js";
import { tier as tierOf, createBudget } from "./satin-math.js";
import { prof } from "./prof.js";

const CSS = `
  #ember-satin{position:fixed;left:0;top:0;display:block;pointer-events:none;z-index:5;opacity:0;transition:opacity 150ms linear}
  #ember-satin-vh{position:fixed;left:0;top:0;width:1px;height:100vh;height:100lvh;visibility:hidden;pointer-events:none}
  html.satin-on .deck{opacity:0}
  @media print{#ember-satin{display:none!important}html.satin-on .deck{opacity:1!important}}
  html.satin-peek #ember-satin{visibility:hidden}`;

let S = null, lastStats = null;   // the running engine; the last run's stats, kept after a stop

function start(deck, opts = {}) {
  if (S) return;
  // Firefox lays the rasterised sheets out differently at a pixel ratio of 2 (mean 3-10/255 from the native page, 14 Oct
  // 2026), and an inaccurate raster throws no error, so the fallback would not catch it: in Firefox the native page shows,
  // with no ember, until a fix is planned with Aaron.
  if (/firefox/i.test(navigator.userAgent) && !opts.firefox) { lastStats = { shown: false, failed: null, mode: "off: Firefox" }; return; }
  // (opts.lift overrides c3's dark-ground lift, for calibration)
  const ql = new URLSearchParams(location.search).get("lift");   // ?lift=n: by-eye comparisons of the dark-ground lift
  const o = { layers: true, budget: true, prof: false, ...(ql !== null && ql !== "" && isFinite(+ql) ? { lift: +ql } : {}), ...opts }; prof.on = !!o.prof; prof.acc = {}; prof.frames = 0;
  const root = document.documentElement, off = [];
  const on = (t, ev, fn, op) => { t.addEventListener(ev, fn, op); off.push(() => t.removeEventListener(ev, fn, op)); };
  const style = document.createElement("style"); style.setAttribute("data-satin", ""); style.textContent = CSS; document.head.appendChild(style);
  const vh = document.createElement("div"); vh.id = "ember-satin-vh"; vh.setAttribute("aria-hidden", "true");
  let cv = document.createElement("canvas"); cv.id = "ember-satin"; cv.setAttribute("aria-hidden", "true");
  document.body.append(vh, cv);
  const coarse = matchMedia("(pointer: coarse)").matches;
  const stableH = () => Math.round(vh.getBoundingClientRect().height) || innerHeight;   // the large viewport: the mobile bar never changes it
  let W = root.clientWidth, H = stableH(), T = tierOf(W, coarse), DPR = Math.min(T.dprCap, devicePixelRatio || 1);
  const rm = matchMedia("(prefers-reduced-motion: reduce)");
  let fresh = true, lastMode = -1, lastRasters = 0;
  let reduced = rm.matches, level = 0, raf = 0, lastNow = 0, focused = false, state = "deck", tShow = 0, tSize = 0;
  const budget = createBudget(), stats = { shown: false, frames: 0, skipped: 0, wake: { fresh: 0, light: 0, cloth: 0 }, clothFrames: 0, level: 0, tier: T.name, failed: null, mode: "" };

  S = { stop, stats, info: () => cloth ? cloth.info() : null, cloth: () => cloth, c3: () => c3, isCanvas: () => state === "canvas" }; lastStats = stats;
  let views = null, c3 = null, rake = null, cloth = null, out2d = null;
  try { init(); } catch (e) { fail(e); }
  function init() {
  views = createViews(deck, { onError: fail });
  S.views = views;
  if (!o.layers) { out2d = cv.getContext("2d"); stats.mode = "views"; }
  else {
    try { rake = createRake(cv, { mediump: T.name === "phone" }); } catch (e) { rake = null; }
    if (!rake) {   // no WebGL2: c3 alone, as the 2D canvas it already is, over the page view
      const c = document.createElement("canvas"); c.id = cv.id; c.setAttribute("aria-hidden", "true"); cv.replaceWith(c); cv = c;
      c3 = createC3({ canvas: cv, ...(o.lift != null ? { darkLift: o.lift } : {}) }); stats.mode = "c3";
    } else {
      c3 = createC3(o.lift != null ? { darkLift: o.lift } : {});
      try { cloth = createCloth({ light: c3.light, tier: T, dpr: DPR, mediump: T.name === "phone" }); stats.mode = "satin"; }
      catch (e) { cloth = null; stats.mode = "c3+rake"; }
    }
    c3.setGlide(!reduced);
    off.push(c3.attach(window));
    // a lost WebGL context: the deck shows again and the engine stops
    if (rake) on(cv, "webglcontextlost", () => fail(new Error("WebGL context lost")));
    if (cloth) on(cloth.canvas, "webglcontextlost", () => fail(new Error("WebGL context lost (satin)")));
  }
  listen();
  sizeAll();
  run();
  }

  function sizeAll() {
    fresh = true; W = root.clientWidth; H = stableH(); T = tierOf(W, coarse); DPR = Math.min(T.dprCap, devicePixelRatio || 1); stats.tier = T.name;
    cv.style.width = W + "px"; cv.style.height = H + "px";
    views.size(W, H, DPR);
    if (out2d) { cv.width = W * DPR; cv.height = H * DPR; }
    if (c3) c3.size(W, H, DPR);
    if (rake) rake.size(W, H, DPR);
    if (cloth) { cloth.build(W, H, T, DPR); cloth.setViews(views.page, views.ground); }   // new textures: the views were resized
  }

  // the page view, with the selection drawn into it, becomes what every layer reads (the proof's refreshLive)
  function selColour() {
    const c = getComputedStyle(deck, "::selection").backgroundColor;
    return c && c !== "rgba(0, 0, 0, 0)" && c !== "transparent" ? c : "Highlight";
  }
  function drawSelection() {
    const sel = getSelection(); if (!sel || sel.isCollapsed || !sel.rangeCount) return;
    const range = sel.getRangeAt(0); if (!range.intersectsNode(deck)) return;
    const g = views.page.getContext("2d"); g.save(); g.globalAlpha = .35; g.fillStyle = "#3390ff"; g.fillStyle = selColour();
    for (const r of range.getClientRects()) g.fillRect(r.left * DPR, r.top * DPR, r.width * DPR, r.height * DPR);
    g.restore();
  }
  function refresh(now) {
    views.dirty = false; views.draw(); drawSelection();
    if (c3) { c3.setPage(views.page); c3.setGround(views.ground); }
    if (rake) rake.upload(views.page, views.ground);
    if (cloth) cloth.refresh();
  }

  // the canvas shows only over a complete window; otherwise the deck shows, crossfaded over 150 ms, never black
  function toCanvas() {
    if (state === "canvas") return; state = "canvas"; cv.style.opacity = "1";
    clearTimeout(tShow); tShow = setTimeout(() => { if (state === "canvas") { if (!root.classList.contains("satin-peek")) root.classList.add("satin-on"); stats.shown = true; } }, 160);   // (peek: the checks are looking at the native page)
  }
  function toDeck() {
    if (state === "deck") return; state = "deck"; clearTimeout(tShow);
    // the deck shows at once and the canvas goes at once: its last frame is of a scroll position already left, so fading
    // it would ghost the page that was there over the page that is (measured by the no-flash check). At rest the canvas
    // and the deck are the same picture, so the swap itself is unseen; coming back, the canvas fades in over 150 ms.
    root.classList.remove("satin-on"); cv.style.transition = "none"; cv.style.opacity = "0";
    requestAnimationFrame(() => { cv.style.transition = ""; });
  }

  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = now - (lastNow || now); lastNow = now; const t0 = prof.mark();
    try {
      let t = prof.mark(); if (views.dirty) { refresh(now); fresh = true; } prof.add('views.refresh', t);
      t = prof.mark(); const done = views.complete(); prof.add('views.complete', t);
      if (!done || focused) { toDeck(); fresh = true; return; }   // a sheet in the window is not rasterised yet (a fast scroll), or keyboard focus is in the deck (the deck shows its focus ring)
      // idle: nothing has changed since the last frame drawn, so it is left on the canvas, and the frame is not counted by the budget
      const satin = !!cloth && !reduced && level < 2, mode = satin * 2 + (level < 1);
      if (mode !== lastMode) { lastMode = mode; fresh = true; }
      const c3still = out2d || c3.still(now), clothStill = out2d || !satin || cloth.still;
      if (!fresh && state === "canvas" && c3still && clothStill) { stats.skipped++; if (cloth) cloth.rest(); return; }
      stats.wake[fresh ? "fresh" : !c3still ? "light" : "cloth"]++;   // why this frame did work
      fresh = false;
      // the budget measures the effect's own cost: a frame in which a sheet raster was produced (or the views redrawn for one) is not counted
      const rastered = views.rasters !== lastRasters; lastRasters = views.rasters;
      if (o.budget && !rastered && dt > 0 && dt < 500) level = stats.level = budget.push(dt, now);
      if (out2d) out2d.drawImage(views.page, 0, 0);
      else if (!rake) c3.frame(now, null);
      else {
        let base = null;
        if (cloth && !satin) cloth.rest();
        if (cloth && !reduced && level < 2) { cloth.setBend(level < 1); if (cloth.tick(now)) { base = cloth.canvas; stats.clothFrames++; } }   // reduced motion and level 2: no satin; level 1: no bend
        c3.frame(now, base);
        t = prof.mark(); rake.setPage(c3.canvas); prof.add('rake.upload', t); t = prof.mark(); rake.draw(now, c3.trail); prof.add('rake.draw', t);
      }
      stats.frames++; if (prof.on) { prof.frames++; prof.add('frame.total', t0); }
      toCanvas();
    } catch (e) { fail(e); }
  }
  function run() { if (!raf && !document.hidden && S) { lastNow = 0; raf = requestAnimationFrame(frame); } }
  function pause() { if (raf) cancelAnimationFrame(raf); raf = 0; }

  function fail(e) { stats.failed = String(e && e.message || e); console.warn("ember satin stopped:", e); stop(); }
  function stop() {
    pause(); clearTimeout(tShow); clearTimeout(tSize);
    for (const f of off) f(); off.length = 0;
    if (views) views.stop();
    root.classList.remove("satin-on", "satin-peek");
    try { if (cloth) cloth.dispose(); } catch (e) {}
    try { if (rake) rake.dispose(); } catch (e) {}
    cv.remove(); vh.remove(); style.remove();
    if (S && S.stats === stats) S = null;
  }

  function safeSize() { try { sizeAll(); } catch (e) { fail(e); } }
  function listen() {
  on(window, "scroll", () => views.scrolled(), { passive: true });
  on(window, "resize", () => {
    if (root.clientWidth !== W || stableH() !== H) { clearTimeout(tSize); tSize = setTimeout(safeSize, 150); }   // width (or the window itself) changed
    views.scrolled();   // a height-only change only redraws
  });
  on(window, "orientationchange", () => { clearTimeout(tSize); tSize = setTimeout(safeSize, 150); });
  // keyboard focus inside the deck (WCAG 2.4.7): the deck shows, with its focus ring, until focus leaves it
  on(deck, "focusin", e => { let k = true; try { k = e.target.matches(":focus-visible"); } catch (x) {} if (k) { focused = true; toDeck(); } });
  on(deck, "focusout", e => { if (!e.relatedTarget || !deck.contains(e.relatedTarget)) { focused = false; fresh = true; } });
  on(document, "visibilitychange", () => { if (document.hidden) pause(); else run(); });
  on(document, "selectionchange", () => { views.dirty = true; });
  if (document.fonts) on(document.fonts, "loadingdone", () => views.reset());
  on(rm, "change", () => { reduced = rm.matches; if (c3) c3.setGlide(!reduced); });
  }
}

function stop() { if (S) S.stop(); }
// for the checks: show the native page in place of the canvas (true), or the canvas again (false)
function peek(v) { document.documentElement.classList.toggle("satin-peek", !!v); if (S && v) document.documentElement.classList.remove("satin-on"); else if (S && S.stats.shown && S.isCanvas()) document.documentElement.classList.add("satin-on"); }

export const EmberSatin = {
  start, stop, peek,
  get stats() { return S ? S.stats : lastStats; },
  prof,
  get info() { return S && S.info ? S.info() : null; },
  probe(points) { const c = S && S.cloth(); if (c) c.probe(points); },
  // for the checks: c3's live touches and the time of the newest (ms, performance.now())
  // for the checks: the last glow layer, the content mask and the views, as data URLs
  // for the checks: whether the page under the glow is lifted for a dark ground now (false: the page view itself)
  get lifting() { const c = S && S.c3(); return c ? c.lifting : null; },
  get touches() { const c = S && S.c3(); if (!c) return null; const t = c.trail; return { n: t.length, last: t.length ? t[t.length - 1].t : null }; },
  get probeLog() { const c = S && S.cloth(); return c ? c.probeLog : null; },
  get rasters() { return S ? S.views.rasters : 0; },
};
if (typeof window !== "undefined") window.EmberSatin = EmberSatin;
