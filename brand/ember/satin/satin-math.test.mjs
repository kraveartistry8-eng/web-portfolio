import { test } from 'node:test';
import assert from 'node:assert/strict';
import { tier, pinViewportUnits, near, bendStep, createBudget, phoneSizes } from './satin-math.js';

test('tier by width', () => {
  for (const w of [390, 576]) assert.deepEqual(tier(w, true), { name: 'phone', grid: [60, 36], steps: 1, dprCap: 1.5 });
  for (const w of [577, 992]) assert.deepEqual(tier(w, false), { name: 'tablet', grid: [90, 54], steps: 2, dprCap: 2 });
  for (const w of [993, 1440]) assert.deepEqual(tier(w, false), { name: 'desktop', grid: [120, 72], steps: 2, dprCap: 2 });
  assert.equal(tier(1440, true).name, 'desktop');
});

test('pinViewportUnits turns vh-family lengths into px', () => {
  assert.equal(pinViewportUnits('min(820px,94svh)', 900), 'min(820px,846.00px)');
  assert.equal(pinViewportUnits('-10vh', 900), '-90.00px');
  assert.equal(pinViewportUnits('.5dvh', 800), '4.00px');
  assert.equal(pinViewportUnits('100lvh', 700), '700.00px');
  assert.equal(pinViewportUnits('50vw 10vmin 3px', 900), '50vw 10vmin 3px');
  assert.equal(pinViewportUnits('10vhx', 900), '10vhx');
  assert.equal(pinViewportUnits('calc(100vh - 2px)', 900), 'calc(900.00px - 2px)');
});

test('pinViewportUnits leaves base64 font data alone', () => {
  const b64 = 'url(data:font/woff2;base64,AAb12vh+Qz9vh/x+1vh/5svh.7dvhA==)';
  assert.equal(pinViewportUnits(b64, 900), b64);
  assert.equal(pinViewportUnits(`src:${b64};height:94svh`, 900), `src:${b64};height:846.00px`);
});

test('near keep band edges', () => {
  assert.equal(near(0, -799, 800).keep, true);  assert.equal(near(0, -800, 800).keep, false);
  assert.equal(near(1599, 100, 800).keep, true); assert.equal(near(1600, 100, 800).keep, false);
});
test('near evict band edges', () => {
  assert.equal(near(0, -2400, 800).evict, false); assert.equal(near(0, -2401, 800).evict, true);
  assert.equal(near(3200, 0, 800).evict, false);  assert.equal(near(3201, 0, 800).evict, true);
});

test('bendStep rates', () => {
  const [a, b] = bendStep(0, 0, 1);               // rising: .2 then .25
  assert.ok(Math.abs(a - .2) < 1e-12); assert.ok(Math.abs(b - .05) < 1e-12);
  const [a2, b2] = bendStep(1, 1, 0);             // falling: .06 then .08
  assert.ok(Math.abs(a2 - .94) < 1e-12); assert.ok(Math.abs(b2 - (1 + (.94 - 1) * .08)) < 1e-12);
});
test('bendStep release never overshoots below 0', () => {
  let a = 1, b = 1;
  for (let i = 0; i < 200; i++) { [a, b] = bendStep(a, b, 0); assert.ok(a >= 0 && b >= 0); }
});
test('bendStep release: b falls monotonically and decelerates after its biggest drop (no snap)', () => {
  let a = 1, b = 1; const bs = [b];
  for (let i = 0; i < 60; i++) { [a, b] = bendStep(a, b, 0); bs.push(b); }
  const drops = []; for (let i = 1; i < bs.length; i++) drops.push(bs[i - 1] - bs[i]);
  assert.ok(drops.every(d => d >= 0), 'monotonic');
  // the drop may accelerate for a few frames first, so check from the largest drop onward
  const m = drops.indexOf(Math.max(...drops));
  for (let i = m + 1; i < drops.length; i++) assert.ok(drops[i] <= drops[i - 1] + 1e-12, 'drop ' + i);
});

const run = (bud, fps, secs, t0) => { const ms = 1000 / fps; let t = t0, lv = 0; for (let i = 0; i < Math.round(secs * fps); i++) { t += ms; lv = bud.push(ms, t); } return [lv, t]; };
test('budget stays 0 at 50 fps', () => { assert.equal(run(createBudget(), 50, 5, 0)[0], 0); });
test('budget stays 0 for 1.9 s at 40 fps', () => { assert.equal(run(createBudget(), 40, 1.9, 0)[0], 0); });
test('budget steps up per full 2 s below 45 fps, never down', () => {
  const b = createBudget(); let [lv, t] = run(b, 40, 2.1, 0); assert.equal(lv, 1);
  [lv, t] = run(b, 40, 2.1, t); assert.equal(lv, 2);
  [lv] = run(b, 60, 10, t); assert.equal(lv, 2);
});

test('phoneSizes', () => {
  assert.deepEqual(phoneSizes('desktop'), { rim: 76, bendCap: 8 });
  assert.deepEqual(phoneSizes('tablet'), { rim: 76, bendCap: 8 });
  assert.deepEqual(phoneSizes('phone'), { rim: 56, bendCap: 6 });
});
