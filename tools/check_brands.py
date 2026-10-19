"""Check a list of brand sites for the signals that make a cold prospect worth a look.

Step 2 of the cold-list pipeline (Aaron, 19 Oct): a store database supplies the brands, this reads each one
from outside, and Aaron judges the shortlist by eye. Everything here is public: a store's home page, its
/meta.json and its /products.json, which most Shopify stores serve.

For each site it reports:
  shopify       whether the site runs on Shopify at all
  theme         the theme's name, the theme it was built from, and whether that is a Theme Store theme
                (by id, or by the name it was built from, since a copied theme loses its id)
  products      how many products the store publishes
  launched_90d  how many of those were first published in the last 90 days (launch cadence)
  newest        the date of the most recent product

Shopify Plus cannot be read reliably from outside, so it is left to the store database in step 1.

Run: python3 tools/check_brands.py carhartt.com outlier.nyc ...
     python3 tools/check_brands.py --file brands.txt      (one domain per line)
Writes outreach/brand-checks/<date>.csv and prints a table.
"""
import argparse
import csv
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outreach/brand-checks"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
WINDOW_DAYS = 90
MAX_PAGES = 20  # 250 products a page; enough for any store in the band


def get(url, timeout=25):
    for _ in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.geturl(), r.read().decode("utf-8", "replace"), r.headers
        except urllib.error.HTTPError as e:
            # Python 3.9's opener does not follow 308, which Vercel-hosted stores use for their locale redirect
            if e.code in (307, 308) and e.headers.get("location"):
                url = urllib.parse.urljoin(url, e.headers["location"])
                continue
            raise
    raise urllib.error.URLError("too many redirects")


# Theme Store themes common on stores in the band. A brand that copies one into its own repo loses the
# theme_store_id, so the name the theme was built from is the reliable signal, not the id.
STORE_THEMES = {
    "dawn", "horizon", "skeleton", "refresh", "sense", "craft", "crave", "studio", "taste", "origin", "ride",
    "colorblock", "spotlight", "trade", "publisher", "debut", "brooklyn", "narrative", "simple", "minimal",
    "prestige", "impulse", "impact", "broadcast", "palo alto", "symmetry", "motion", "warehouse", "focal",
    "be yours", "expanse", "pipeline", "empire", "district", "flow", "showcase", "streamline", "stiletto",
    "split", "local", "combine", "enterprise", "xtra", "concept", "hyper", "ella", "shrine", "kalles",
}


def theme_of(html):
    m = re.search(r"Shopify\.theme\s*=\s*(\{.*?\});", html)
    if not m:
        return {}
    try:
        t = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    return {
        "theme": t.get("name") or "",
        "built_from": t.get("schema_name") or "",
        # a Theme Store id means the theme was bought or installed from Shopify's store, not built for the brand
        "theme_store": "yes" if t.get("theme_store_id") or (t.get("schema_name") or "").strip().lower() in STORE_THEMES
        else "no",
    }


def launches(base):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=WINDOW_DAYS)
    total, recent, newest = 0, 0, None
    for page in range(1, MAX_PAGES + 1):
        try:
            _, body, _ = get(f"{base}/products.json?limit=250&page={page}")
            items = json.loads(body).get("products", [])
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
            return (total or None), (recent if total else None), newest
        if not items:
            break
        for p in items:
            stamp = p.get("published_at") or p.get("created_at")
            if not stamp:
                continue
            when = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            total += 1
            recent += when >= since
            newest = max(newest, when) if newest else when
        time.sleep(0.4)
    return total, recent, newest


def check(domain):
    row = {"domain": domain, "shopify": "", "theme": "", "built_from": "", "theme_store": "",
           "products": "", "launched_90d": "", "newest": "", "note": ""}
    try:
        final, html, headers = get(f"https://{domain}")
    except urllib.error.HTTPError as e:
        server = (e.headers.get("server") or "").lower()
        # big brands sit behind bot protection that refuses any script; that is a fact about them, not a bug
        guard = "Akamai" if "akamai" in server else "Cloudflare" if "cloudflare" in server else ""
        row["note"] = f"blocked by {guard} bot protection ({e.code})" if guard and e.code == 403 else f"home page returned {e.code}"
        return row
    except Exception as e:  # unreachable or not a web store; recorded rather than raised
        row["note"] = f"home page failed: {type(e).__name__}"
        return row
    base = re.match(r"https?://[^/]+", final).group(0)
    powered = (headers.get("powered-by") or "").lower()
    shopify = "cdn.shopify.com" in html or "Shopify.theme" in html or "myshopify.com" in html or "shopify" in powered
    row["shopify"] = "yes" if shopify else "no"
    if "hydrogen" in powered or "oxygen" in powered:
        # already headless: the brand has an engineering function, which is tier 3 work, not a theme
        row["theme"] = "headless (Hydrogen)"
    if base.rstrip("/") != f"https://{domain}":
        row["note"] = f"redirects to {base}"
    if not shopify:
        return row
    # a closed or password-protected store still answers, so catch it before reading anything else
    if "/password" in final or re.search(r"store is closed|opening soon|enter store using password", html, re.I):
        row["note"] = "store closed or password protected"
        return row
    row.update(theme_of(html))
    total, recent, newest = launches(base)
    row["products"] = "" if total is None else total
    row["launched_90d"] = "" if recent is None else recent
    row["newest"] = newest.date().isoformat() if newest else ""
    if total is None:
        row["note"] = (row["note"] + "; " if row["note"] else "") + "product feed hidden"
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", nargs="*")
    ap.add_argument("--file")
    a = ap.parse_args()
    domains = list(a.domains)
    if a.file:
        domains += [l.strip() for l in Path(a.file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    rows = []
    for d in domains:
        d = re.sub(r"^https?://|/.*$", "", d.strip())
        rows.append(check(d))
        r = rows[-1]
        print(f"{r['domain']:<28} shopify={r['shopify']:<3} theme={r['theme'][:22]:<22} from={r['built_from'][:12]:<12} "
              f"store={r['theme_store']:<3} products={str(r['products']):<5} new90={str(r['launched_90d']):<4} "
              f"newest={r['newest']:<10} {r['note']}")
    OUT.mkdir(parents=True, exist_ok=True)
    # one file per list, so checking a second list the same day does not overwrite the first
    path = OUT / (f"{Path(a.file).stem}-results.csv" if a.file else f"{dt.date.today().isoformat()}.csv")
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
