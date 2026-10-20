"""Task 6: the one rule. No hover, focus or press colour is lighter (OKLCH L) than rest."""
import re
from common import *

def L(css):
    nums = [float(x) for x in re.findall(r"[\d.]+", css)[:4]]
    if len(nums) == 4 and nums[3] == 0: return None
    r, g, b_ = [c / 255 for c in nums[:3]]
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b_ = lin(r), lin(g), lin(b_)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b_) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b_) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817104234 * g + 0.6299058133 * b_) ** (1 / 3)
    return 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s

TARGETS = [".site-header__menu summary", ".site-header__side--start > a", ".site-header__wordmark", ".site-header__side--end > a >> nth=0",
           ".site-header__side--end > a >> nth=-1", ".film-hero__button", ".film-hero__control"]
p, b = browser()
pg = page(b)
pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(1500)
pg.route("**/cart/add*", lambda r: r.abort())
for sel in TARGETS:
    el = pg.locator(sel)
    read = lambda: el.evaluate("e => { const s = getComputedStyle(e); return [s.color, s.backgroundColor] }")
    pg.mouse.move(5, 450); pg.wait_for_timeout(500)
    rest = read()
    el.hover(); pg.wait_for_timeout(500); hover = read()
    box = el.bounding_box(); pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); pg.mouse.down(); pg.wait_for_timeout(500); press = read(); pg.mouse.move(5, 450); pg.mouse.up()
    pg.mouse.move(5, 450); pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    el.focus(); pg.evaluate("document.activeElement && document.activeElement.matches(':focus-visible')"); pg.wait_for_timeout(500); focus = read()
    pg.evaluate("document.activeElement.blur()")
    for state, vals in (("hover", hover), ("press", press), ("focus", focus)):
        for i, part in enumerate(("text", "fill")):
            a, z = L(rest[i]), L(vals[i])
            if a is None or z is None: continue
            check(f"{sel} {state} {part} not lighter", z <= a + 1e-6, f"{rest[i]} -> {vals[i]}")
b.close(); p.stop(); finish()
