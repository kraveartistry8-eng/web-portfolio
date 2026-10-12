"""Browser checks for the ember engine, against brand/ember/harness.html (plan Task 2).

Headless on the real GPU only: a headed window picks up Aaron's real mouse. Prints one line per failure
and exits 1, or prints PASS.
"""
import io, math, os, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = "file://" + os.path.join(ROOT, "brand/ember/harness.html")
GPU = ["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"]
fails, errors = [], []


def fail(msg):
    fails.append(msg)


def page_for(br, w=1440, h=900, **ctx):
    pg = br.new_context(viewport={"width": w, "height": h}, **ctx).new_page()
    pg.on("console", lambda m: m.type == "error" and errors.append(f"{w}px: {m.text}"))
    pg.on("pageerror", lambda e: errors.append(f"{w}px: {e}"))
    return pg


def load(pg, query=""):
    pg.goto(HARNESS + query)
    pg.wait_for_function("window.ember && document.documentElement.classList.contains('ember-on')", timeout=8000)
    pg.evaluate(HELPERS)


# In-page helpers: a frame recorder, a pixel probe read straight after each render, and a sweep that moves the
# pointer a fixed step every frame, so the stop can be checked frame by frame.
HELPERS = """() => {
  window.__rec = []; window.__headMax = 0;
  const diff = (a, b) => Math.max(...a.map((v, i) => Math.abs(v - b[i])));
  window.__px = (em, x, y) => { const gl = em.renderer.getContext(), d = em.renderer.getPixelRatio(), b = new Uint8Array(4);
    gl.readPixels(Math.round(x * d), Math.round((em.H - y) * d), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, b); return [b[0], b[1], b[2]]; };
  window.__probe = (em) => {
    if (em.phase === 'moving' && window.__gapPt) window.__gapMax = Math.max(window.__gapMax || 0, diff(__px(em, ...__gapPt), em.groundRGB(__gapPt[1])));
    if (em.phase === 'moving') window.__headMax = Math.max(window.__headMax, diff(__px(em, em.head.x, em.head.y), em.groundRGB(em.head.y)));
    if (em.phase !== 'stopping' || em.cutAge === null) return [];
    const lm = em.lastMoveT / 1000, cut = em.cutAge, hist = em.history, bad = [];
    const alive = hist.filter(h => lm - h.t < cut + .02);
    for (let i = 0; i < hist.length; i += 2) { const h = hist[i], a0 = lm - h.t;
      if (a0 <= cut + .1 || Math.hypot(h.x - em.head.x, h.y - em.head.y) < 90) continue;
      if (alive.some(p => Math.hypot(p.x - h.x, p.y - h.y) < 90)) continue;
      const d = diff(__px(em, h.x, h.y), em.groundRGB(h.y)); if (d > 40) bad.push([Math.round(h.x), Math.round(h.y), d]); }
    return bad; };
  ember.onFrame = (em, drew) => { __rec.push({now: performance.now(), phase: em.phase, hx: em.head.x, hy: em.head.y,
    cx: em.cutHead.x, cy: em.cutHead.y, el: em.stopElapsed, T: em.stopT, idle: em.idle, dt: em.lastDt, lm: em.lastMoveT,
    drew, bad: drew ? __probe(em) : []}); };
  window.__sweep = (pts) => new Promise(res => { let i = 0; const step = () => { if (i >= pts.length) return res();
    const [x, y] = pts[i++]; window.dispatchEvent(new PointerEvent('pointermove', {clientX: x, clientY: y, pointerType: 'mouse', bubbles: true}));
    requestAnimationFrame(step); }; requestAnimationFrame(step); });
}"""


def line_pts(x0, x1, y, step):
    n = int(abs(x1 - x0) / step)
    return [[x0 + (x1 - x0) * i / n, y] for i in range(n + 1)]


def arc_pts(cx, cy, r, n):
    return [[cx - r * math.cos(math.pi * i / n), cy - r * math.sin(math.pi * i / n)] for i in range(n + 1)]


def sweep_and_settle(pg, pts):
    pg.evaluate("() => { __rec.length = 0; }")
    pg.evaluate("(p) => __sweep(p)", pts)
    pg.wait_for_function("ember.phase === 'idle' && __rec.some(r => r.phase === 'stopping')", timeout=6000)
    pg.wait_for_timeout(50)
    return pg.evaluate("() => __rec")


def check_stop(rec, label):
    """Spec 5: the head moves and the cut advances every frame until T; they meet; the field is empty by T + 60 ms."""
    stop = [r for r in rec if r["phase"] == "stopping"]
    if not stop:
        return fail(f"{label}: never entered 'stopping'")
    i0 = rec.index(stop[0])
    gaps = sorted(b["now"] - a["now"] for a, b in zip(rec, rec[1:]) if b["now"] > a["now"])
    fr = gaps[len(gaps) // 2]
    lag = stop[0]["now"] - stop[0]["lm"]
    if not (33 <= lag <= 34 + 1.5 * fr):
        fail(f"{label}: 'stopping' began {lag:.0f} ms after the last move, want 34 ms within a frame ({fr:.0f} ms)")
    T = stop[0]["T"]
    for a, b in zip(rec[i0:], rec[i0 + 1:]):
        if b["phase"] != "stopping" or b["el"] >= T - fr / 1000:   # the last frame before T is where they meet
            break
        if math.hypot(b["hx"] - a["hx"], b["hy"] - a["hy"]) < 1e-3:
            fail(f"{label}: head held still at {b['el']:.3f} s of {T:.3f}")
            break
        if math.hypot(b["cx"] - a["cx"], b["cy"] - a["cy"]) < 1e-3:
            fail(f"{label}: tail end held still at {b['el']:.3f} s of {T:.3f}")
            break
    atT = next((r for r in stop if r["el"] >= T), stop[-1])
    gap = math.hypot(atT["hx"] - atT["cx"], atT["hy"] - atT["cy"])
    if gap >= 2:
        fail(f"{label}: head and tail end {gap:.1f} px apart at {atT['el']:.3f} s (T = {T:.3f})")
    idle = next((r for r in rec[i0:] if r["phase"] == "idle"), None)
    if not idle or not idle["idle"]:
        fail(f"{label}: never went idle after the stop")
    elif (idle["now"] - stop[0]["lm"]) / 1000 > T + .06 + 1.5 * fr / 1000:
        fail(f"{label}: idle at {(idle['now'] - stop[0]['lm']) / 1000:.3f} s, want by T + 60 ms = {T + .06:.3f} s")
    bad = [b for r in rec for b in r["bad"]]
    if bad:
        fail(f"{label}: {len(bad)} lit pixels where the cut had already passed, first {bad[:3]}")


# A fake clock drives frames by hand, so the stop can land at any offset past 34 ms. Each frame the canvas row under
# a straight sweep is read back, and the visible tail end (leftmost lit pixel) is tracked: it must advance every frame,
# with no jump, until it meets the head.
FAKE = """async (stopAt) => { const em = ember; em.paused = true; cancelAnimationFrame(em.raf); em.raf = 0;
  let now = performance.now() + 1000; const real = performance.now.bind(performance); performance.now = () => now;
  const y = 600, gl = em.renderer.getContext(), d = em.renderer.getPixelRatio(), W = Math.round(em.W * d), row = new Uint8Array(W * 4);
  const g = em.groundRGB(y), lit = i => Math.max(Math.abs(row[i] - g[0]), Math.abs(row[i + 1] - g[1]), Math.abs(row[i + 2] - g[2])) > 40;
  const frame = (dtMs) => { now += dtMs; em.animate(); gl.readPixels(0, Math.round((em.H - y) * d), W, 1, gl.RGBA, gl.UNSIGNED_BYTE, row);
    let x = -1; for (let i = 0; i < W; i++) if (lit(i * 4)) { x = i / d; break; } return {x, phase: em.phase, el: em.stopElapsed, T: em.stopT}; };
  for (let i = 0; i <= 50; i++) { window.dispatchEvent(new PointerEvent('pointermove', {clientX: 200 + i * 6, clientY: y, pointerType: 'mouse'})); frame(1000 / 60); }
  const out = [frame(1000 / 60), frame(stopAt - 1000 / 60)];
  for (let i = 0; i < 60; i++) { const f = frame(1000 / 60); out.push(f); if (f.phase === 'idle') break; }
  performance.now = real; em.paused = false; em.lastT = 0; em.wake(); return out; }"""


def check_fake_clock_stop(pg, stop_at):
    fr = pg.evaluate(FAKE, stop_at)
    run = [f for f in fr if f["phase"] == "stopping" and f["x"] >= 0 and f["el"] < f["T"] - .02]
    steps = [b["x"] - a["x"] for a, b in zip(run, run[1:])]
    if not steps:
        return fail(f"test_stop_fake_clock({stop_at} ms): no stopping frames read")
    med = sorted(steps)[len(steps) // 2]
    held = sum(1 for s in steps if s <= 0)
    if held or max(steps) > max(4 * med, 6):
        fail(f"test_stop_fake_clock({stop_at} ms): tail end held {held} frames, largest step {max(steps):.1f} px vs median {med:.1f}")


with sync_playwright() as p:
    br = p.chromium.launch(headless=True, args=GPU)

    # 1-3: the canvas, pointer events, sideways scroll, at each width
    for w, h in ((1440, 900), (768, 1024), (390, 844)):
        pg = page_for(br, w, h)
        load(pg)
        r = pg.evaluate("""() => { const c = document.querySelector('#ember canvas');
          return {n: document.querySelectorAll('#ember canvas').length, pe: c && getComputedStyle(c).pointerEvents,
                  hs: document.documentElement.scrollWidth - innerWidth}; }""")
        if r["n"] != 1: fail(f"{w}px: {r['n']} canvases under #ember, want 1")
        if r["pe"] != "none": fail(f"{w}px: canvas pointer-events is {r['pe']}, want none")
        if r["hs"] > 0: fail(f"{w}px: sideways scroll {r['hs']}px")
        pg.context.close()

    pg = page_for(br)
    load(pg)
    # 4: field size at 1440
    fw = pg.evaluate("() => [ember.fieldW, ember.fieldH]")
    if fw != [360, 225]: fail(f"1440px: field {fw}, want [360, 225]")
    # 5 and 6: a straight sweep at a fixed speed, then a stop, frame by frame
    rec = sweep_and_settle(pg, line_pts(200, 1240, 680, 14))
    head = pg.evaluate("() => __headMax")
    if head < 40: fail(f"sweep: the head differs from the ground by {head}, want at least 40")
    check_stop(rec, "test_stop_frame_by_frame")
    # a new stroke starts where the pointer is: nothing joins it to where the last one came to rest (spec 2.9, no jump)
    pg.evaluate("() => { window.__gapPt = [720, 490]; window.__gapMax = 0; }")
    sweep_and_settle(pg, line_pts(200, 420, 300, 14))
    gap = pg.evaluate("() => { const g = __gapMax; window.__gapPt = null; return g; }")
    if gap > 40: fail(f"test_stroke_start_no_jump: lit by {gap} between the last rest point and the new stroke")
    # 7: a semicircle, then a stop
    check_stop(sweep_and_settle(pg, arc_pts(720, 760, 300, 90)), "test_stop_on_curve")
    # 10: once idle, nothing renders; the next move wakes it
    pg.wait_for_timeout(1500)
    f0 = pg.evaluate("() => ember.renderer.info.render.frame")
    pg.wait_for_timeout(500)
    f1 = pg.evaluate("() => ember.renderer.info.render.frame")
    pg.mouse.move(300, 500); pg.mouse.move(340, 520)
    pg.wait_for_timeout(120)
    f2 = pg.evaluate("() => ember.renderer.info.render.frame")
    if f1 != f0: fail(f"test_idle_stops_rendering: {f1 - f0} renders while idle")
    if f2 <= f1: fail("test_idle_stops_rendering: a pointer move did not wake it")
    # the GPU cut, under hand-timed frames: a stop landing just past 34 ms, and one landing on a whole frame
    for stop_at in (34.05, 50):
        check_fake_clock_stop(pg, stop_at)
        pg.wait_for_timeout(300)
    # a resize that leaves the field size unchanged (a phone toolbar showing or hiding) keeps the trail
    pg.evaluate("(p) => __sweep(p)", line_pts(200, 700, 640, 14))
    ids = pg.evaluate("() => [ember.rtA.texture.uuid, ember.agA.texture.uuid, ember.history.length]")
    pg.set_viewport_size({"width": 1440, "height": 880})
    pg.wait_for_timeout(80)
    ids2 = pg.evaluate("() => [[ember.rtA.texture.uuid, ember.rtB.texture.uuid], [ember.agA.texture.uuid, ember.agB.texture.uuid], ember.history.length]")
    if ids[0] not in ids2[0] or ids[1] not in ids2[1] or ids2[2] == 0:
        fail("test_resize_keeps_trail: a resize with the same field size reallocated the fields and wiped the trail")
    pg.set_viewport_size({"width": 1440, "height": 900})
    pg.wait_for_function("ember.phase === 'idle'", timeout=3000)
    # 13: hidden mid-stop pauses; shown again, the first frame's dt is clamped and the stop clears
    pg.evaluate("(p) => __sweep(p)", line_pts(200, 900, 600, 14))
    pg.wait_for_function("ember.phase === 'stopping'", timeout=3000)
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); }")
    if not pg.evaluate("() => ember.paused"): fail("test_hidden_tab_pauses: not paused while hidden")
    pg.wait_for_timeout(1200)
    pg.evaluate("() => { __rec.length = 0; Object.defineProperty(document, 'hidden', {configurable: true, get: () => false}); document.dispatchEvent(new Event('visibilitychange')); }")
    pg.wait_for_timeout(300)
    r = pg.evaluate("() => ({paused: ember.paused, phase: ember.phase, first: __rec[0] && __rec[0].dt})")
    if r["paused"]: fail("test_hidden_tab_pauses: still paused once shown")
    if r["first"] is None or r["first"] > .1: fail(f"test_hidden_tab_pauses: first frame back dt {r['first']}, want <= 0.1")
    if r["phase"] != "idle": fail(f"test_hidden_tab_pauses: phase {r['phase']} after return, want the stop cleared")
    # 14: the ground re-bakes when the document grows
    pg.evaluate("() => { window.__rb = 0; const o = ember.rebakeGround.bind(ember); ember.rebakeGround = () => { __rb++; o(); }; const d = document.createElement('div'); d.style.height = '1000px'; document.body.appendChild(d); }")
    pg.wait_for_timeout(1000)
    if pg.evaluate("() => __rb") < 1: fail("test_ground_rebakes_on_height_change: no re-bake within 1 s")
    # 16: a card's rim lights when the ember passes its corner
    pg.evaluate("() => document.querySelectorAll('.card')[0].scrollIntoView({block: 'center'})")
    pg.wait_for_timeout(200)
    b = pg.evaluate("() => { const r = document.querySelectorAll('.card')[0].getBoundingClientRect(); return [r.left, r.top]; }")
    for i in range(24):
        pg.mouse.move(b[0] - 12 + (i % 2) * 24, b[1] - 12 + (i % 3) * 8)
        pg.wait_for_timeout(16)
    li = pg.evaluate("() => +getComputedStyle(document.querySelectorAll('.card')[0]).getPropertyValue('--li')")
    if li <= .5: fail(f"test_card_rim_lit: --li {li} after 400 ms at the corner, want > 0.5")
    # 12: resize reallocates the field
    pg.set_viewport_size({"width": 1920, "height": 1080})
    pg.wait_for_timeout(300)
    fw = pg.evaluate("() => [ember.fieldW, ember.fieldH]")
    if fw != [480, 270]: fail(f"test_resize_reallocates_field: {fw}, want [480, 270]")
    pg.mouse.move(400, 500); pg.mouse.move(600, 520)
    pg.wait_for_timeout(100)
    pg.context.close()

    # 17: the 8-bit fallback passes the same stop check
    pg = page_for(br)
    load(pg, "?byte=1")
    if not pg.evaluate("() => ember.byteTargets"): fail("test_8bit_fallback: forceByteTargets did not take")
    check_stop(sweep_and_settle(pg, line_pts(200, 1240, 680, 14)), "test_8bit_fallback")
    pg.context.close()

    # 8: reduced motion holds one still ember at the pointer, with no trail
    pg = page_for(br, reduced_motion="reduce")
    load(pg)
    for i in range(30):
        pg.mouse.move(200 + i * 25, 650)
    pg.wait_for_timeout(400)
    a = pg.screenshot(clip={"x": 0, "y": 450, "width": 1440, "height": 400})
    pg.wait_for_timeout(500)
    b2 = pg.screenshot(clip={"x": 0, "y": 450, "width": 1440, "height": 400})
    if a != b2: fail("reduced motion: the canvas changed over 500 ms while the pointer was still")
    # GL pixels are only readable inside a frame, so this reads the screenshot (nothing in the DOM sits at y 650)
    shot = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    g = pg.evaluate("() => ember.groundRGB(650)")
    at, behind = shot.getpixel((925, 650)), shot.getpixel((300, 650))
    if max(abs(x - y) for x, y in zip(at, g)) < 40: fail(f"reduced motion: no ember at the pointer ({at} on ground {g})")
    if max(abs(x - y) for x, y in zip(behind, g)) > 12: fail(f"reduced motion: a trail behind the pointer ({behind} on ground {g})")
    pg.context.close()

    # 9: on touch, scrolling drives it and the end of scrolling stops it
    pg = page_for(br, 390, 844, has_touch=True, is_mobile=True, device_scale_factor=2)
    load(pg)
    if not pg.evaluate("() => matchMedia('(pointer: coarse)').matches"): fail("touch: pointer is not coarse in the mobile context")
    pg.evaluate("() => new Promise(res => { let i = 0; const s = () => { if (i++ > 30) return res(); scrollBy(0, 14); requestAnimationFrame(s); }; requestAnimationFrame(s); })")
    ph = pg.evaluate("() => ember.phase")
    if ph != "moving": fail(f"test_touch_scroll_stop: phase {ph} while scrolling, want moving")
    pg.wait_for_function("ember.phase === 'stopping'", timeout=2000)
    pg.wait_for_function("ember.phase === 'idle'", timeout=3000)
    pg.context.close()

    # 15: the canvas is capped at 2x
    pg = page_for(br, device_scale_factor=3)
    load(pg)
    r = pg.evaluate("() => [ember.renderer.domElement.width, document.getElementById('ember').clientWidth]")
    if r[0] != 2 * r[1]: fail(f"test_dpr_cap: canvas {r[0]} px wide at 3x, want {2 * r[1]}")
    pg.context.close()

    # 11: with JavaScript off the harness reads in full on its own ground
    pg = page_for(br, java_script_enabled=False)
    pg.goto(HARNESS)
    if not pg.locator("main").is_visible(): fail("no JS: main is not visible")
    if "ember-on" in (pg.get_attribute("html", "class") or ""): fail("no JS: ember-on is set")
    pg.context.close()
    br.close()

    # 18: with no WebGL, no canvas is added and nothing errors
    br = p.chromium.launch(headless=True, args=["--disable-3d-apis", "--disable-webgl"])
    pg = page_for(br)
    pg.goto(HARNESS)
    pg.wait_for_timeout(500)
    r = pg.evaluate("() => [document.querySelectorAll('#ember canvas').length, document.documentElement.classList.contains('ember-on')]")
    if r != [0, False]: fail(f"no WebGL: canvases {r[0]}, ember-on {r[1]}; want none and off")
    br.close()

if errors: fail(f"console errors: {errors[:4]}")
print("\n".join(fails) or "PASS")
sys.exit(1 if fails else 0)
