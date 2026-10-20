"""Final-review fixes: one check per finding (I1–I7, M1, M5)."""
from common import *

p, b = browser()
playing = lambda q: q.evaluate("() => { const v = document.querySelector('.film-hero video'); return !!v && !v.paused }")

# I1 autoplay refused: the video steps aside and the poster shows as a plain image (no iOS glyph possible)
a = b.new_context(viewport={"width": 1440, "height": 900})
a.add_init_script("HTMLMediaElement.prototype.play = function () { return Promise.reject(new DOMException('blocked', 'NotAllowedError')); }")
ap = a.new_page(); ap.goto(BASE + "/", wait_until="load"); ap.wait_for_timeout(1500)
check("I1 refused: video hidden", not ap.locator(".film-hero video").is_visible())
check("I1 refused: poster image visible", ap.locator(".film-hero__poster").is_visible())
css = open("../../afterglow/sections/film-hero.liquid").read()
check("I1 webkit start-playback glyph suppressed", "-webkit-media-controls-start-playback-button" in css)

pg = page(b); pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(1500)
# I2 live region rendered empty, filled on failure, cleared after 4s
err = pg.locator(".film-hero__error")
check("I2 status region present at rest", err.count() == 1 and err.get_attribute("hidden") is None)
check("I2 status region empty at rest", err.inner_text().strip() == "")
pg.route("**/cart/add*", lambda r: r.fulfill(status=422, body="{}"))
pg.locator(".film-hero__button").click(); pg.wait_for_timeout(600)
check("I2 failure text set", len(err.inner_text().strip()) > 0)
pg.wait_for_timeout(4200)
check("I2 failure text cleared after 4s", err.inner_text().strip() == "")
pg.unroute("**/cart/add*")
# I3 no aria-pressed on a relabelling control
check("I3 control has no aria-pressed", pg.locator(".film-hero__control").get_attribute("aria-pressed") is None)
# I4 editor re-render: section:load re-initialises the film
pg.evaluate("""() => { const h = document.querySelector('.film-hero'); const v = h.querySelector('video');
  v.pause(); h.querySelector('.film-hero__control').hidden = true;
  const fresh = h.closest('.shopify-section').cloneNode(true); h.closest('.shopify-section').replaceWith(fresh);
  fresh.querySelector('video').pause();
  fresh.dispatchEvent(new CustomEvent('shopify:section:load', { bubbles: true, detail: { sectionId: 'film' } })); }""")
pg.wait_for_timeout(1500)
check("I4 film plays after section:load", playing(pg))
check("I4 control visible after section:load", pg.locator(".film-hero__control").is_visible())
# I7 back/forward cache: a restored page resets the button
pg.evaluate("""() => { const btn = document.querySelector('.film-hero__button'); btn.setAttribute('aria-disabled','true'); btn.textContent = 'Adding';
  window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })); }""")
check("I7 restored page: button at rest", pg.locator(".film-hero__button").inner_text().strip().lower() == "add to bag"
      and pg.locator(".film-hero__button").get_attribute("aria-disabled") is None)
# M1 add succeeds but cart.js fails: no false error, still lands on the cart
pg.route("**/cart.js*", lambda r: r.fulfill(status=500, body=""))
pg.locator(".film-hero__button").click(); pg.wait_for_timeout(300)
check("M1 no false error after a successful add", err.inner_text().strip() == "")
pg.wait_for_url("**/cart", timeout=8000)
check("M1 lands on the cart", pg.url.rstrip("/").endswith("/cart"))

# I5 long line on a sideways phone stays below the header
s = page(b, 844, 390, True); s.goto(BASE + "/?view=qa-longline", wait_until="load"); s.wait_for_timeout(800)
line, hdr = s.locator(".film-hero h1").bounding_box(), s.locator(".site-header").bounding_box()
check("I5 sideways long line below the header", line["y"] >= hdr["y"] + hdr["height"], f"{line} {hdr}")
# I6 desktop menu never opens empty
d = page(b); d.goto(BASE + "/", wait_until="load")
if d.locator(".site-header__menu summary").is_visible():
    d.locator(".site-header__menu summary").click(); d.wait_for_timeout(300)
    n = d.evaluate("() => [...document.querySelectorAll('.site-header__panel a')].filter(a => a.offsetParent).length")
    check("I6 desktop menu shows links when opened", n > 0, f"{n} visible links")
else:
    check("I6 desktop menu hidden when empty", True)
# M5 wordmark centred on phones
m = page(b, 390, 844, True); m.goto(BASE + "/", wait_until="load")
wb = m.locator(".site-header__wordmark").bounding_box()
check("M5 phone wordmark centred", abs(wb["x"] + wb["width"] / 2 - 195) < 2, str(wb))
b.close(); p.stop(); finish()
