// The satin's maths: everything that can be tested without a DOM or a GPU.

// quality tier by viewport width; the pointer type is accepted for later and does not change the tier
export function tier(width, coarse) {
  if (width <= 576) return { name: 'phone', grid: [60, 36], steps: 1, dprCap: 1.5 };
  if (width <= 992) return { name: 'tablet', grid: [90, 54], steps: 2, dprCap: 2 };
  return { name: 'desktop', grid: [120, 72], steps: 2, dprCap: 2 };
}

// freeze vh/svh/dvh/lvh lengths to px for a given window height. Boundaries on both sides: never inside a word, a number or
// base64 data (a font inlined as a data URL can hold runs like "b12vh+"), so the number may not follow a word char, + / or .
export const pinViewportUnits = (css, h) =>
  css.replace(/(?<![\w+/.])(-?(?:\d+\.?\d*|\.\d+))(?:dvh|svh|lvh|vh)\b/g, (_, n) => (n * h / 100).toFixed(2) + 'px');

// which sheets to keep live and which to drop, by distance from the viewport
export const near = (top, bottom, winH) => ({
  keep: bottom > -winH && top < 2 * winH,
  evict: bottom < -3 * winH || top > 4 * winH,
});

// one frame of the two-stage bend easing; one shared rising/falling flag, quick up and slow down
export function bendStep(a, b, target) {
  const rising = Math.abs(target) > Math.abs(a), kA = rising ? .2 : .06, kB = rising ? .25 : .08;
  const a2 = a + (target - a) * kA;
  return [a2, b + (a2 - b) * kB];
}

// frame-rate budget: below 45 fps over a full 2 s window steps the level up (max 2), never back down
export function createBudget() {
  let level = 0, start = null, frames = [];
  return { push(frameMs, nowMs) {
    if (start === null) start = nowMs;
    frames.push([nowMs, frameMs]);
    while (frames.length && frames[0][0] < nowMs - 2000) frames.shift();
    if (nowMs - start >= 2000) {
      const sum = frames.reduce((s, f) => s + f[1], 0);
      if (frames.length * 1000 / sum < 45 && level < 2) level++;
      start = null; frames = [];       // restart the window
    }
    return level;
  } };
}

export const phoneSizes = name => name === 'phone' ? { rim: 56, bendCap: 6 } : { rim: 76, bendCap: 8 };
