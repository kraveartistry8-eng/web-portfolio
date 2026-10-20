"""Task 6: layout at every width, plus the long-line case."""
from common import *

SIZES = [(390, 844, True), (768, 1024, True), (1280, 800, False), (1440, 900, False), (1920, 1080, False), (844, 390, True)]
p, b = browser()
for w, h, mob in SIZES:
    tag = f"{w}x{h}"
    pg = page(b, w, h, mob); pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(800)
    hero = pg.locator(".film-hero").bounding_box()
    want = h if (w, h) == (844, 390) else max(h, 560)
    check(f"{tag}: section height {want}", abs(hero["height"] - want) < 2, str(hero["height"]))
    check(f"{tag}: no horizontal scroll", pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
    copy = pg.locator(".film-hero__copy").bounding_box()
    phone = w <= 576
    if phone:
        check(f"{tag}: copy 20px in", abs(copy["x"] - 20) < 1, str(copy["x"]))
    else:
        check(f"{tag}: copy 32–52px in", 32 <= copy["x"] <= 52, str(copy["x"]))
    fs = float(pg.locator(".film-hero h1").evaluate("e => parseFloat(getComputedStyle(e).fontSize)"))
    if w >= 1440:
        check(f"{tag}: line held at 61.04px", abs(fs - 61.04) < 0.05, str(fs))
    if phone:
        check(f"{tag}: line 39px", abs(fs - 39.056) < 0.1, str(fs))
    btn = pg.locator(".film-hero__button").bounding_box()
    ctl = pg.locator(".film-hero__control").bounding_box()
    if phone:
        check(f"{tag}: button in bottom third", btn["y"] >= h * 2 / 3, str(btn["y"]))
        check(f"{tag}: control top right under nav", ctl["y"] < 120 and ctl["x"] + ctl["width"] > w - 24, str(ctl))
    else:
        check(f"{tag}: control level with button", abs((ctl["y"] + ctl["height"] / 2) - (btn["y"] + btn["height"] / 2)) < 4, f"{ctl} {btn}")
        check(f"{tag}: control at right", ctl["x"] + ctl["width"] > w - 56, str(ctl))
    copy_bottom = copy["y"] + copy["height"]
    check(f"{tag}: copy clear of the bottom edge", h - copy_bottom >= 20 - 0.5, str(h - copy_bottom))

for w, h, mob in [(390, 844, True), (1440, 900, False)]:
    tag = f"long line {w}"
    pg = page(b, w, h, mob); pg.goto(BASE + "/?view=qa-longline", wait_until="load"); pg.wait_for_timeout(800)
    line = pg.locator(".film-hero h1").bounding_box()
    ctl = pg.locator(".film-hero__control").bounding_box()
    hdr = pg.locator(".site-header").bounding_box()
    check(f"{tag}: inside the screen", line["x"] >= 0 and line["x"] + line["width"] <= w, str(line))
    check(f"{tag}: below the header", line["y"] >= hdr["y"] + hdr["height"], f"{line} {hdr}")
    overlap = not (line["x"] + line["width"] <= ctl["x"] or ctl["x"] + ctl["width"] <= line["x"] or line["y"] + line["height"] <= ctl["y"] or ctl["y"] + ctl["height"] <= line["y"])
    check(f"{tag}: clear of the pause control", not overlap, f"{line} {ctl}")
    if w == 1440:
        col4 = 52 + (1440 - 104 - 11 * 24) / 12 * 4 + 3 * 24
        check(f"{tag}: within the left four columns", line["x"] + line["width"] <= col4 + 1, f"{line['x'] + line['width']} > {col4}")
b.close(); p.stop(); finish()
