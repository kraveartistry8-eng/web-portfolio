"""Task 5: film rendition and weight, first paint, reduced motion, pause, off-screen, refusal, fallbacks, darkening."""
import re
from common import *

def video_bytes(w, h, mobile):
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile)
    pg = ctx.new_page(); seen = {}
    def resp(r):
        if "/videos/" in r.url or r.url.endswith(".mp4") or ".mp4?" in r.url:
            try: seen[r.url] = seen.get(r.url, 0) + len(r.body())
            except Exception: seen[r.url] = seen.get(r.url, 0)
    pg.on("response", resp)
    pg.goto(BASE + "/", wait_until="load")
    dur = pg.evaluate("() => { const v = document.querySelector('.film-hero video'); return v ? v.duration * 1000 : 0 }") or 8000
    pg.wait_for_timeout(min(int(dur) + 1500, 15000))
    src = pg.evaluate("() => { const v = document.querySelector('.film-hero video'); return v ? v.currentSrc : '' }")
    ctx.close(); return src, sum(seen.values())

p, b = browser()
src, n = video_bytes(1440, 900, False)
m = re.search(r"(\d{3,4})p", src)
check("desktop: a rendition at 1080p or below", bool(m) and int(m.group(1)) <= 1080, src)
check("desktop: one loop under 4 MB", 0 < n < 4_000_000, f"{n} bytes")
src, n = video_bytes(390, 844, True)
m = re.search(r"(\d{3,4})p", src)
check("phone: a rendition at 720p or below", bool(m) and int(m.group(1)) <= 720, src)
check("phone: one loop under 2 MB", 0 < n < 2_000_000, f"{n} bytes")

pg = page(b)
html = None
pg.goto(BASE + "/", wait_until="domcontentloaded")
check("poster is preloaded", pg.locator("link[rel=preload][as=image]").count() >= 1)
check("video carries a poster", bool(pg.locator(".film-hero video").get_attribute("poster")))
check("no native controls", pg.locator(".film-hero video").get_attribute("controls") is None)
pg.wait_for_timeout(2500)
playing = lambda q: q.evaluate("() => { const v = document.querySelector('.film-hero video'); return !!v && !v.paused }")
check("film plays on load", playing(pg))
ctl = pg.locator(".film-hero__control")
ctl.click(); pg.wait_for_timeout(300)
check("pause: film paused", not playing(pg))
check("pause: label reads Play", ctl.inner_text().strip().lower() == "play", ctl.inner_text())
check("pause: no contradictory aria-pressed", ctl.get_attribute("aria-pressed") is None)
ctl.click(); pg.wait_for_timeout(500)
check("play: film resumes", playing(pg))
pg.evaluate("window.scrollTo(0, document.body.scrollHeight + 2000)"); pg.evaluate("document.body.style.minHeight='300vh'; window.scrollTo(0, 2000)")
pg.wait_for_timeout(800)
check("off screen: film pauses", not playing(pg))
pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(800)
check("back on screen: film resumes", playing(pg))
ctl.click(); pg.evaluate("window.scrollTo(0, 2000)"); pg.wait_for_timeout(500); pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(800)
check("visitor pause survives scrolling back", not playing(pg))

r = b.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce").new_page()
r.goto(BASE + "/", wait_until="load"); r.wait_for_timeout(2000)
check("reduced motion: film never starts", not playing(r))
check("reduced motion: control hidden", not r.locator(".film-hero__control").is_visible())

a = b.new_context(viewport={"width": 1440, "height": 900})
a.add_init_script("HTMLMediaElement.prototype.play = function () { return Promise.reject(new DOMException('blocked', 'NotAllowedError')); }")
ap = a.new_page(); ap.goto(BASE + "/", wait_until="load"); ap.wait_for_timeout(1500)
check("autoplay refused: poster stays (no controls)", ap.locator(".film-hero video").get_attribute("controls") is None and bool(ap.locator(".film-hero video").get_attribute("poster")))
check("autoplay refused: control hidden", not ap.locator(".film-hero__control").is_visible())

f = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True).new_page()
f.route("**/*HD-720p*", lambda r: r.fulfill(status=404, body=""))
f.goto(BASE + "/", wait_until="load"); f.wait_for_timeout(2500)
cs = f.evaluate("() => document.querySelector('.film-hero video').currentSrc")
check("phone: missing 720p falls back to a working film", "1080p" in cs and playing(f), cs)

e = page(b); e.goto(BASE + "/?view=qa-nomedia", wait_until="load")
check("nothing uploaded: no video or img", e.locator(".film-hero video, .film-hero__media img").count() == 0)
check("nothing uploaded: ground shows", e.locator(".film-hero").evaluate("x => getComputedStyle(x).backgroundColor") == "rgb(8, 8, 8)")
check("nothing uploaded: line visible", e.locator(".film-hero h1").is_visible())
bg = lambda q: q.locator(".film-hero__media").evaluate("x => getComputedStyle(x, '::after').backgroundImage")
full = bg(pg)
check("darken default: top 50%, bottom 85%", "0.5)" in full and "0.85)" in full, full)
z = page(b); z.goto(BASE + "/?view=qa-nodarken", wait_until="load")
zero = bg(z)
check("darken 0: no darkening", "0.5)" not in zero and "0.85)" not in zero, zero)
b.close(); p.stop(); finish()
