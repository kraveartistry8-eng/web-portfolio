// Per-stage frame timing for the checks (EmberSatin.start(deck, { prof: true })): ms accumulated by stage name.
export const prof = { on: false, acc: {}, frames: 0,
  mark() { return this.on ? performance.now() : 0; },
  add(name, t0) { if (this.on) this.acc[name] = (this.acc[name] || 0) + performance.now() - t0; } };
