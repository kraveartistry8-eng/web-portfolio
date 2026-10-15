// The views, moved from brand/ember-directions/satin-live.html (the block "live: the guide's sheets are rasterised as they
// come near the viewport"): a cache of sheet rasters near the viewport, and the page view and ground view of the window
// drawn from it at the current pixel ratio, #080808 where no sheet is drawn.
// Added by the plan: nearness and eviction from near(); the sheet under the viewport is rasterised first, then the sheets
// after it, then those before it, one at a time, yielding to the browser between sheets; a raster is valid only at the
// generation and the box size it was made at (a width change or a font load clears the cache; a height-only change keeps
// every raster whose box did not change, so the mobile browser bar never re-rasterises); a dirty flag the engine reads.
import { sheet as rasterSheet, resetStyles } from "./raster.js";
import { near } from "./satin-math.js";

export function createViews(deck, { onError = e => { throw e; } } = {}) {
  const img = document.createElement("canvas"), gimg = document.createElement("canvas");
  const shot = new Map();   // sheet -> { page, ground, gen, cw, ch } at the current width
  let W = 1, H = 1, DPR = 1, gen = 0, busy = false, stopped = false;
  const sheets = () => [...deck.querySelectorAll(".sheet")];
  const box = el => { const r = el.getBoundingClientRect(); return { r, cw: Math.ceil(r.width), ch: Math.ceil(r.height) }; };
  const valid = (s, b) => !!(s && s.page && s.gen === gen && s.cw === b.cw && s.ch === b.ch);
  const api = { page: img, ground: gimg, dirty: true, rasters: 0 };

  // the next sheet to rasterise: under the viewport first, then after it (nearest first), then before it (nearest first)
  function next() {
    let best = null, rank = Infinity;
    for (const el of sheets()) {
      const b = box(el), { r } = b, n = near(r.top, r.bottom, H), have = shot.get(el);
      if (!n.keep) { if (have && n.evict) shot.delete(el); continue; }
      if (valid(have, b)) continue;
      const k = r.bottom > 0 && r.top < H ? r.top : r.top >= H ? 1e6 + r.top : 2e6 - r.bottom;
      if (k < rank) { rank = k; best = el; }
    }
    return best;
  }
  async function pump() {
    if (busy || stopped) return;
    busy = true;
    try {
      for (let el; !stopped && (el = next());) {
        const g = gen, { cw, ch } = box(el);
        const [page, ground] = await Promise.all([rasterSheet(el, { dpr: DPR }), rasterSheet(el, { dpr: DPR, ground: true })]);
        api.rasters++;
        if (g === gen && !stopped) { shot.set(el, { page, ground, gen: g, cw, ch }); api.dirty = true; }
        await new Promise(r => setTimeout(r, 0));   // yield, so scrolling never stalls
      }
    } catch (e) { stopped = true; onError(e); }
    finally { busy = false; }
  }
  function drawViews() {
    for (const [v, k] of [[img, "page"], [gimg, "ground"]]) {
      if (v.width !== W * DPR || v.height !== H * DPR) { v.width = W * DPR; v.height = H * DPR; }
      const g = v.getContext("2d"); g.fillStyle = "#080808"; g.fillRect(0, 0, v.width, v.height);
      for (const [el, s] of shot) { if (!s[k]) continue; const b = box(el), { r } = b; if (r.bottom < 0 || r.top > H || !valid(s, b)) continue; g.drawImage(s[k], r.left * DPR, r.top * DPR, s[k].width, s[k].height); }
    }
  }
  // every sheet in the window is rasterised at the current size
  function complete() {
    for (const el of sheets()) { const b = box(el), { r } = b; if (r.bottom > 0 && r.top < H && !valid(shot.get(el), b)) return false; }
    return true;
  }
  function clear() { gen++; shot.clear(); api.dirty = true; }

  return Object.assign(api, {
    // a new width or pixel ratio clears the cache; a new height only redraws
    size(w, h, dpr) {
      if (w !== W || dpr !== DPR) clear();
      W = w; H = h; DPR = dpr; api.dirty = true; pump();
    },
    // the fonts finished loading: the styles are read again and everything re-rasterised
    reset() { resetStyles(); clear(); pump(); },
    scrolled() { api.dirty = true; pump(); },
    draw: drawViews, complete, pump,
    stop() { stopped = true; shot.clear(); },
  });
}
