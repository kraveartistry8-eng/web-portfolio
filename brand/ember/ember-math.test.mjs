import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fallAt, fieldSize, decay, stopTime, cutAge, coastSpeed, capOffset, rippleFade,
         encodeAge, decodeAge, hot, lightTarget, easeLight, emberColour, oklch, lift, emberColourMatched } from './ember-math.js';

test('fallAt hits each stop', () => { assert.deepEqual(fallAt(0), [216,178,96]); assert.deepEqual(fallAt(.6), [137,58,80]); assert.deepEqual(fallAt(.96), [8,8,8]); assert.deepEqual(fallAt(1), [191,21,183]); });
test('fallAt clamps', () => { assert.deepEqual(fallAt(-1), fallAt(0)); assert.deepEqual(fallAt(2), fallAt(1)); });
test('fieldSize is a quarter, at least 360x225 (225x360 in portrait)', () => { assert.deepEqual(fieldSize(1440,900), [360,225]); assert.deepEqual(fieldSize(1920,1080), [480,270]); assert.deepEqual(fieldSize(390,844), [225,360]); assert.deepEqual(fieldSize(768,1024), [225,360]); });
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
test('emberColour is luma plus chroma x2.2, plus 40, clamped', () => { assert.deepEqual(emberColour([8,8,8]), [48,48,48]); assert.deepEqual(emberColour([255,0,0]).map(v => v >= 0 && v <= 255), [true,true,true]); assert.equal(emberColour([255,0,0])[0], 255); });

// matched chroma (Aaron, 12 Oct): the ember lifts the page's lightness and keeps its chroma and hue exactly
const near = (a, b, tol) => Math.abs(a - b) <= tol;
test('lift keeps chroma and hue, and raises lightness', () => {
  for (const c of [[216,178,96], [188,111,76], [137,58,80], [52,29,94]]) {
    const [L0, C0, h0] = oklch(c), [L1, C1, h1] = oklch(lift(c, .2));
    assert.ok(near(C1, C0, .006), `chroma ${C0} -> ${C1}`); assert.ok(near(h1, h0, 3), `hue ${h0} -> ${h1}`); assert.ok(L1 > L0 + .08, `L ${L0} -> ${L1}`);
  }
});
test('lift stays in gamut by giving up lightness, never chroma', () => {
  const out = lift([216,178,96], .4);
  assert.ok(out.every(v => v >= 0 && v <= 255)); assert.ok(near(oklch(out)[1], oklch([216,178,96])[1], .006));
});
test('emberColourMatched has the ground\'s chroma', () => {
  const c = [137,58,80]; assert.ok(near(oklch(emberColourMatched(c))[1], oklch(c)[1], .006));
});
test('lift can scale chroma by k, keeping hue', () => {
  const c = [137,58,80], [, C0, h0] = oklch(c), [, C1, h1] = oklch(lift(c, .15, 1.6));
  assert.ok(near(C1, C0 * 1.6, .01), `chroma ${C0} -> ${C1}`); assert.ok(near(h1, h0, 3));
});
test('emberColourMatched takes the same scale', () => {
  const c = [52,29,94]; assert.ok(near(oklch(emberColourMatched(c, 1.6))[1], oklch(c)[1] * 1.6, .012));
});
