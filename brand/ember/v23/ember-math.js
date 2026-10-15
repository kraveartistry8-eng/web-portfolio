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
