"""Task 1: the palette, hairline and motion tokens are output on :root with the guide's values."""
from common import *

WANT = {"ground": "#080808", "surface-recessed": "#141414", "surface-raised": "#2b2b2b", "muted": "#c0c0c0",
        "text": "#eeecea", "gold": "#d8b260", "after-gold": "#bc6f4c", "rose": "#893a50",
        "deep-violet": "#341d5e", "magenta": "#bf15b7"}

p, b = browser()
pg = page(b)
pg.goto(BASE + "/", wait_until="domcontentloaded")
read = lambda prop: pg.evaluate("p => getComputedStyle(document.documentElement).getPropertyValue(p).trim().toLowerCase()", prop)
for k, v in WANT.items():
    got = read(f"--color-{k}")
    check(f"--color-{k} is {v}", got == v, f"got {got!r}")
hair = pg.evaluate("""() => { const d = document.createElement('div'); d.style.color = 'var(--color-hairline)';
  document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }""")
check("--color-hairline is #C0C0C0 at 22%", hair.replace(" ", "") in ("rgba(192,192,192,0.22)", "color(srgb0.7529410.7529410.752941/0.22)"), f"got {hair!r}")
check("--dur is 450ms", read("--dur") == "450ms", read("--dur"))
check("--ease is the guide curve", read("--ease").replace(" ", "") == "cubic-bezier(0.2,0,0.2,1)", read("--ease"))
fd, fb = read("--font-display"), read("--font-body")
check("--font-display is Instrument Serif", "instrument serif" in fd, fd)
check("--font-body is Space Grotesk", "space grotesk" in fb, fb)
b.close(); p.stop(); finish()
