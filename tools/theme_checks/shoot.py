"""Screenshot a URL at 1440x900 and 390x844 (2x). Usage: shoot.py URL OUT_PREFIX"""
import sys
from common import browser, page
url, out = sys.argv[1], sys.argv[2]
p, b = browser()
for tag, (w, h, m) in {"d": (1440, 900, False), "m": (390, 844, True)}.items():
    pg = page(b, w, h, m, device_scale_factor=1 if not m else 2)
    pg.goto(url, wait_until="load"); pg.wait_for_timeout(3000)
    pg.screenshot(path=f"{out}-{tag}.png")
b.close(); p.stop()
