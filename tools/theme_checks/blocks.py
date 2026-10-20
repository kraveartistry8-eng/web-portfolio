"""Task 4: the line, product line and buy blocks, and Add to bag states."""
import json, os
from common import *

THEME = os.path.join(os.path.dirname(__file__), "../../afterglow")
schema = open(f"{THEME}/blocks/line.liquid").read() if os.path.exists(f"{THEME}/blocks/line.liquid") else ""
check("line block file exists", bool(schema))
if schema:
    sj = json.loads(schema.split("{% schema %}")[1].split("{% endschema %}")[0])
    check("line block has a preset named Line", any("line" in p["name"].lower() for p in sj.get("presets", [])), str(sj.get("presets")))
    sizes = [o["value"] for s in sj["settings"] if s["id"] == "size" for o in s["options"]]
    check("line sizes are xl, x3, x4", sizes == ["xl", "x3", "x4"], str(sizes))

p, b = browser()
pg = page(b)
pg.goto(BASE + "/", wait_until="load")
check("line rendered by the line block", pg.locator(".film-hero .line-block h1, .film-hero h1.line-block").count() == 1)
check("line text default", pg.locator(".film-hero h1").inner_text().strip() == "Breathe in the last of the sun.")
check("line at 61px on desktop", pg.locator(".film-hero h1").evaluate("e => getComputedStyle(e).fontSize") == "61.04px",
      pg.locator(".film-hero h1").evaluate("e => getComputedStyle(e).fontSize"))
prod = pg.locator(".film-hero__product").inner_text().strip().lower()
check("product line from product", prod == "afterglow · eau de parfum · 50 ml", prod)
check("price reads $180", pg.locator(".film-hero__price").inner_text().strip() == "$180", pg.locator(".film-hero__price").inner_text())
btn = pg.locator(".film-hero__button")
check("button is a real submit button", btn.evaluate("e => e.tagName") == "BUTTON")
check("button at least 48px tall", btn.bounding_box()["height"] >= 48)

# failure: add request rejected
pg.route("**/cart/add*", lambda r: r.fulfill(status=422, content_type="application/json", body='{"status":422,"description":"Sold out"}'))
before = pg.locator("[data-cart-count]").inner_text()
btn.click(); pg.wait_for_timeout(800)
check("failed add: label back to rest", btn.inner_text().strip().lower() == "add to bag", btn.inner_text())
check("failed add: message shown", pg.locator(".film-hero__error").is_visible())
check("failed add: count unchanged", pg.locator("[data-cart-count]").inner_text() == before)
pg.wait_for_timeout(4300)
check("failed add: message gone after 4s", not pg.locator(".film-hero__error").is_visible())
pg.unroute("**/cart/add*")

# adding state, then success
def slow(route):
    pg.wait_for_timeout(700); route.continue_()
pg.route("**/cart/add*", slow)
btn.click(); pg.wait_for_timeout(250)
check("adding: label reads Adding", btn.inner_text().strip().lower() == "adding", btn.inner_text())
check("adding: further presses ignored", btn.evaluate("e => e.disabled || e.getAttribute('aria-disabled') === 'true'"))
pg.wait_for_url("**/cart", timeout=8000)
check("success: lands on the cart", pg.url.rstrip("/").endswith("/cart"), pg.url)
check("success: bag count is 1", pg.locator("[data-cart-count]").inner_text().strip() == "1", pg.locator("[data-cart-count]").inner_text())

n = page(b)
n.goto(BASE + "/?view=qa-noproduct", wait_until="load")
check("no product: section still renders", n.locator(".film-hero h1").count() == 1)
check("no product: no product line", n.locator(".film-hero__product").count() == 0)
check("no product: no button", n.locator(".film-hero__button").count() == 0)
check("no product: no Liquid error", "Liquid error" not in n.content())
b.close(); p.stop(); finish()
