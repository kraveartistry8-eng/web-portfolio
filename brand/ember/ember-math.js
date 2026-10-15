// The ember's maths: everything that can be tested without a GPU (spec §2, 2026-10-11-afterglow-ember-design.md).

// the fall over the whole document: gold, after gold, rose, deep violet, void, then a sliver of magenta
export const FALL = [[0, "#D8B260"], [.30, "#BC6F4C"], [.60, "#893A50"], [.84, "#341D5E"],
                     [.95, "#080808"], [.972, "#080808"], [.994, "#BF15B7"], [1, "#BF15B7"]];

const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const luma = c => .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
const clamp255 = v => Math.min(255, Math.max(0, v));

export function fallAt(t) {
  t = Math.min(1, Math.max(0, t));
  for (let i = 1; i < FALL.length; i++) if (t <= FALL[i][0]) {
    const a = rgb(FALL[i - 1][1]), b = rgb(FALL[i][1]), k = (t - FALL[i - 1][0]) / (FALL[i][0] - FALL[i - 1][0] || 1);
    return a.map((v, j) => v + (b[j] - v) * k);
  }
  return rgb(FALL[FALL.length - 1][1]);
}

// a quarter of the viewport on each axis, never under 360 x 225 (§2.8)
export const fieldSize = (cssW, cssH) => { const [a, b] = cssW >= cssH ? [360, 225] : [225, 360];
  return [Math.max(a, Math.round(cssW / 4)), Math.max(b, Math.round(cssH / 4))]; };

// fading is timed in seconds: a per-frame factor at 60 fps, scaled to the real frame time
export const decay = (perFrame, dt) => perFrame ** (dt * 60);

// §2.4: pushed to high chroma; the max keeps the tail at the head's intensity
export function hot(c, heat) {
  const l = luma(c), k = 1 + 3.4 * Math.max(heat, .75);
  return c.map(v => clamp255(l + (v - l) * k));
}

// §2.3: one stop time, T = 0.25 + 0.75 x c0, with c0 at most where a full trail visibly ends
export const stopTime = c0 => .25 + .75 * Math.min(.58, c0);
export const coastSpeed = (v0, t, T) => Math.min(v0, 8) * Math.max(0, 1 - t / T);
export const cutAge = (c0, t, T) => c0 - t - (c0 / (T * T)) * t * t;
export const capOffset = (d, speed) => Math.min(.3, d * d / (2 * .07 * speed));
export const rippleFade = (t, T) => (1 - Math.min(1, t / T)) ** 2;

// the 8-bit fallback stores age over 0-2 s, which covers the longest stop (T = 1 s)
export const encodeAge = sec => Math.min(1, Math.max(0, sec / 2));
export const decodeAge = v => v * 2;

// §2.7: light on cards and text
export const lightTarget = (heat, distPx) => Math.min(1, 1.3 * heat / (1 + (distPx / 140) ** 2));
export const easeLight = (current, target) => current + (target - current) * .12;
export function emberColour(c) {
  const l = luma(c);
  return c.map(v => Math.round(clamp255(l + (v - l) * 2.2 + 40)));
}

// ---- matched chroma (Aaron, 12 Oct): the ember lifts the page's lightness in OKLab and keeps its chroma and hue ----
const toLin = v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; };
const toSrgb = v => 255 * (v <= .0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - .055);
function toLab(c) {
  const [r, g, b] = c.map(toLin);
  const l = Math.cbrt(.4122214708 * r + .5363325363 * g + .0514459929 * b), m = Math.cbrt(.2119034982 * r + .6806995451 * g + .1073969566 * b),
        s = Math.cbrt(.0883024619 * r + .2817188376 * g + .6299787005 * b);
  return [.2104542553 * l + .793617785 * m - .0040720468 * s, 1.9779984951 * l - 2.428592205 * m + .4505937099 * s, .0259040371 * l + .7827717662 * m - .808675766 * s];
}
function fromLab([L, a, b]) {
  const l = (L + .3963377774 * a + .2158037573 * b) ** 3, m = (L - .1055613458 * a - .0638541728 * b) ** 3, s = (L - .0894841775 * a - 1.291485548 * b) ** 3;
  return [4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s, -.0041960863 * l - .7034186147 * m + 1.707614701 * s];
}
export function oklch(c) { const [L, a, b] = toLab(c); return [L, Math.hypot(a, b), (Math.atan2(b, a) * 180 / Math.PI + 360) % 360]; }
// raise lightness by dL and scale chroma by k (1 keeps it), hue unchanged; where that leaves sRGB, give up lightness, never chroma
export function lift(c, dL, k = 1) {
  let [L, a, b] = toLab(c); a *= k; b *= k;
  const ok = x => fromLab([x, a, b]).every(v => v >= -1e-4 && v <= 1 + 1e-4);
  let lo = L, hi = L + dL;
  if (!ok(hi)) { for (let i = 0; i < 24; i++) { const mid = (lo + hi) / 2; if (ok(mid)) lo = mid; else hi = mid; } hi = lo; }
  return fromLab([hi, a, b]).map(v => Math.round(clamp255(toSrgb(Math.min(1, Math.max(0, v))))));
}
// the light the ember casts on cards and text, at the ground's own chroma
export const emberColourMatched = (c, k = 1) => lift(c, .22, k);
