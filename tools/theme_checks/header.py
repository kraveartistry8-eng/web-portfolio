"""Task 3: the header floats over the film on the homepage only, and reduces on phones."""
from common import *

p, b = browser()
pg = page(b)
pg.goto(BASE + "/", wait_until="load")
h = pg.locator(".site-header")
pos = h.evaluate("e => getComputedStyle(e).position")
bg = h.evaluate("e => getComputedStyle(e).backgroundColor")
check("homepage header is overlaid", pos == "absolute", pos)
check("homepage header has no ground", bg in ("rgba(0, 0, 0, 0)", "transparent"), bg)
hero_top = pg.locator(".film-hero").evaluate("e => e.getBoundingClientRect().top")
check("film starts at the top of the page", hero_top == 0, str(hero_top))
wm = pg.locator(".site-header__wordmark")
box, vw = wm.bounding_box(), 1440
check("wordmark centred", abs(box["x"] + box["width"] / 2 - vw / 2) < 2, str(box))
fam = wm.evaluate("e => getComputedStyle(e).fontFamily")
check("wordmark in display font", "Instrument Serif" in fam, fam)
check("wordmark 26px", wm.evaluate("e => getComputedStyle(e).fontSize") == "26px")
check("wordmark widened 150%", "matrix(1.5, 0, 0, 1" in wm.evaluate("e => getComputedStyle(e).transform"))
bar = [e.inner_text() for e in pg.locator(".site-header__side > a, .site-header__side summary").all() if e.is_visible()]
bar = " ".join(t for t in bar).upper()
for name in ("MENU", "SEARCH", "ACCOUNT", "BAG"):
    check(f"{name} visible on desktop", name in bar, bar)
small = pg.evaluate("""() => [...document.querySelectorAll('.site-header a, .site-header summary')]
  .filter(e => e.offsetParent).map(e => e.getBoundingClientRect()).filter(r => r.height < 44 || r.width < 44).length""")
check("every header target at least 44x44", small == 0, f"{small} too small")
check("bag shows a space before the count", "Bag (" in pg.locator(".site-header").inner_text().title() or "BAG (" in pg.locator(".site-header").inner_text().upper())

m = page(b, 390, 844, True)
m.goto(BASE + "/", wait_until="load")
vis = lambda sel: m.locator(sel).first.is_visible()
check("phone: Menu visible", vis(".site-header__menu summary"))
check("phone: Bag visible", vis("a[href*='/cart']"))
check("phone: Search hidden from bar", not m.locator(".site-header__side--start > .site-header__wide").is_visible())
check("phone: Account hidden from bar", m.locator(".site-header__side--end > .site-header__wide").count() == 0 or not m.locator(".site-header__side--end > .site-header__wide").is_visible())
check("phone: wordmark 22px", m.locator(".site-header__wordmark").evaluate("e => getComputedStyle(e).fontSize") == "22px")

o = page(b)
o.goto(BASE + "/collections/all", wait_until="load")
check("other pages: header not overlaid", o.locator(".site-header").evaluate("e => getComputedStyle(e).position") != "absolute")
b.close(); p.stop(); finish()
