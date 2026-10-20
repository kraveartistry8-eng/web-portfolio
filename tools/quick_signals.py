"""Measure the quick signals for step 4 of the cold-list pipeline, and capture what the reviewer looks at.

Aaron, 19 Oct: the ten-second "does anything jump out that I'd fix?" call is his, with a blind reviewer
alongside. This script does the part neither of them can see by eye, and prepares screenshots for the reviewer.

Per site:
  perf, lcp_s, cls, tbt_ms   Google PageSpeed Insights, mobile: the numbers a founder can check themselves
  field_lcp, field_inp       real-user data from Chrome, when the site has enough traffic to report it
  js_errors, broken          console errors, and images, scripts, styles or fonts that failed to load
  screenshots                home page on phone and desktop, plus one product page, for the reviewer

Run: python3 tools/quick_signals.py --file outreach/brand-checks/<list>.txt
     PSI_KEY=<google api key> raises PageSpeed's daily limit once batches reach hundreds.
Writes <list>-signals.csv beside the list, and screenshots to <list>-shots/.
"""
import argparse
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
PHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1")


CHROMIUM = next(Path.home().glob(
    "Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"), None)


def lighthouse(url):
    """The same lab test PageSpeed runs, on this laptop. Used when PageSpeed's keyless daily quota is spent.
    It needs Playwright's Chromium: the installed Chrome closes the page mid-trace under Lighthouse."""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "lh.json"
        env = {**os.environ, "CHROME_PATH": str(CHROMIUM)} if CHROMIUM else os.environ
        subprocess.run(["npx", "-y", "lighthouse@13.5.0", url, "--only-categories=performance", "--form-factor=mobile",
                        "--output=json", f"--output-path={out}", "--quiet", "--chrome-flags=--headless=new"],
                       env=env, capture_output=True, timeout=300)
        if not out.exists():
            return {"psi_note": "Lighthouse failed"}
        d = json.loads(out.read_text())
    # an audit can come back without a value (no LCP recorded, page errored mid-trace); a blank beats a crash
    # that loses the whole run, which is what happened to all three runs on 20 Oct
    num = lambda k: d["audits"].get(k, {}).get("numericValue")
    lcp, cls, tbt = num("largest-contentful-paint"), num("cumulative-layout-shift"), num("total-blocking-time")
    return {
        "perf": round((d["categories"]["performance"]["score"] or 0) * 100),
        "lcp_s": round(lcp / 1000, 1) if lcp is not None else "",
        "cls": round(cls, 3) if cls is not None else "",
        "tbt_ms": round(tbt) if tbt is not None else "",
        "psi_note": "local Lighthouse (lab only, no real-user data)" + ("" if lcp is not None else "; no LCP recorded"),
    }


def pagespeed(url):
    q = {"url": url, "strategy": "mobile", "category": "performance"}
    if os.environ.get("PSI_KEY"):
        q["key"] = os.environ["PSI_KEY"]
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(q)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(api, timeout=120) as r:
                d = json.load(r)
            break
        except Exception as e:  # PageSpeed times out on heavy pages now and then; a retry usually lands
            if getattr(e, "code", None) == 429 or attempt == 2:  # out of quota, or down: measure locally instead
                return lighthouse(url)
            time.sleep(10)
    lh, audits = d.get("lighthouseResult", {}), d.get("lighthouseResult", {}).get("audits", {})
    field = d.get("loadingExperience", {}).get("metrics", {})
    num = lambda k: audits.get(k, {}).get("numericValue")
    return {
        "perf": round((lh.get("categories", {}).get("performance", {}).get("score") or 0) * 100),
        "lcp_s": round(num("largest-contentful-paint") / 1000, 1) if num("largest-contentful-paint") else "",
        "cls": round(num("cumulative-layout-shift"), 3) if num("cumulative-layout-shift") is not None else "",
        "tbt_ms": round(num("total-blocking-time")) if num("total-blocking-time") is not None else "",
        "field_lcp": field.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("category", ""),
        "field_inp": field.get("INTERACTION_TO_NEXT_PAINT", {}).get("category", ""),
    }


def hero_product(base):
    """The highest-priced product in the store, which is far likelier to be the one the brand is built around.
    The first item in the feed was often a sample set, a candle or a belt buckle (fragrance batch, 19 Oct)."""
    try:
        req = urllib.request.Request(f"{base}/products.json?limit=250", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            items = json.load(r).get("products", [])
    except Exception:
        return None
    price = lambda p: max((float(v.get("price") or 0) for v in p.get("variants", [])), default=0)
    # gift cards carry the biggest price in many stores and say nothing about how the brand sells
    items = [p for p in items if "gift" not in (p.get("product_type", "") + p.get("title", "")).lower()]
    return f"{base}/products/{max(items, key=price)['handle']}" if items else None


def clear_popups(pg):
    for sel in ["button[aria-label*='lose' i]", "button:has-text('No thanks')", "button:has-text('Accept')"]:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=400):
                el.click(timeout=800)
                pg.wait_for_timeout(400)
        except Exception:
            pass
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)


def browse(browser, domain, shots):
    out = {"js_errors": 0, "broken": 0, "product_url": ""}
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA, locale="en-US")
    pg = ctx.new_page()
    pg.on("console", lambda m: out.__setitem__("js_errors", out["js_errors"] + (m.type == "error")))
    # broken means an image, script, stylesheet or font the page asked for and did not get. Aborted requests are
    # left out: browsers cut off trackers and prefetches all the time, and counting them buried the real breakage
    def failed(r):
        if r.resource_type in ("image", "script", "stylesheet", "font") and "ABORTED" not in (r.failure or ""):
            out["broken"] += 1
    def bad_status(r):
        if r.status >= 400 and r.request.resource_type in ("image", "script", "stylesheet", "font"):
            out["broken"] += 1
    pg.on("requestfailed", failed)
    pg.on("response", bad_status)
    pg.goto(f"https://{domain}", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    base = re.match(r"https?://[^/]+", pg.url).group(0)
    clear_popups(pg)
    pg.screenshot(path=str(shots / f"{domain}-1-desktop.png"))
    # the feed is refused (429) when Shopify is already throttling this address: 9 of 10 on 20 Oct.
    # Fall back to the first product the home page links to, so the reviewer always has a product page
    product = hero_product(base) or pg.evaluate(
        # skip gift cards, appointments and order forms: 5 of 40 fallbacks landed on one (20 Oct)
        "() => { const a = [...document.querySelectorAll('a[href*=\"/products/\"]')].find(a =>"
        " !/gift|card|appointment|booking|consult|order-form|sample/i.test(a.href)); return a ? a.href : null }")
    if product:
        out["product_url"] = product
        pg.goto(product, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(4000)
        clear_popups(pg)
        pg.screenshot(path=str(shots / f"{domain}-3-product.png"))
    ctx.close()
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, user_agent=PHONE_UA)
    pg = ctx.new_page()
    pg.goto(f"https://{domain}", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    clear_popups(pg)
    pg.screenshot(path=str(shots / f"{domain}-2-phone.png"))
    ctx.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    a = ap.parse_args()
    lst = Path(a.file)
    domains = [re.sub(r"^https?://|/.*$", "", l.strip()) for l in lst.read_text().splitlines()
               if l.strip() and not l.startswith("#")]
    shots = lst.with_name(f"{lst.stem}-shots")
    shots.mkdir(exist_ok=True)
    fields = ["domain", "perf", "lcp_s", "cls", "tbt_ms", "field_lcp", "field_inp", "js_errors", "broken",
              "product_url", "psi_note", "browse_note"]
    path = lst.with_name(f"{lst.stem}-signals.csv")
    # written a row at a time, so a crash late in a long list keeps everything measured before it
    f = path.open("w", newline="")
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        for d in domains:
            row = {"domain": d}
            try:
                row.update(pagespeed(f"https://{d}"))
            except Exception as e:
                row["psi_note"] = f"speed test failed: {type(e).__name__}"
            try:
                row.update(browse(browser, d, shots))
            except Exception as e:
                row["browse_note"] = f"browser load failed: {type(e).__name__}"
            w.writerow(row)
            f.flush()
            print(d, {k: v for k, v in row.items() if k != "domain"}, flush=True)
        browser.close()
    f.close()
    print(path, shots, sep="\n")


if __name__ == "__main__":
    main()
