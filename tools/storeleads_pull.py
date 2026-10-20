"""Pull cold-list candidates from the Store Leads API: step 1 of the cold-list pipeline.

Filters are the ones agreed on 19 Oct: Shopify, US, active, estimated $5M-$20M a year. Brands already pulled
into an earlier list are skipped, so each pull only brings new names. The API key is read from .env
(STORELEADS_KEY=...), which git ignores; it never goes in a file that is committed.

A category matches when it is any of a store's categories, so a CBD store that also sells scent comes back
under fragrance. Check 1 in step 4 cuts those.

Run: python3 tools/storeleads_pull.py "/Beauty & Fitness/Face & Body Care/Perfumes & Fragrances" [more categories]
     python3 tools/storeleads_pull.py --sample 18 <categories...>   (a mixed batch, 18 a category)
     python3 tools/storeleads_pull.py --plus-only ...      (Shopify Plus stores only)
Writes outreach/brand-checks/<date>-sl-<slug>.txt (one domain a line, for check_brands and quick_signals)
and a .jsonl beside it with what Store Leads knows about each brand.
"""
import argparse
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outreach/brand-checks"
API = "https://storeleads.app/json/api/v1/all/domain"

# Store Leads estimates sales per month, in US cents. $5M-$20M a year is $416,667-$1,666,667 a month.
SALES_MIN = round(5_000_000 / 12 * 100)
SALES_MAX = round(20_000_000 / 12 * 100)


def key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("STORELEADS_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("STORELEADS_KEY is missing from .env")


def query(params, token):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Pro allows two requests a second; the API says how long to wait
                time.sleep(float(e.headers.get("Retry-After") or 2))
                continue
            raise
    raise SystemExit("Store Leads kept rate-limiting; try again in a minute")


def seen_before():
    """Every domain in an earlier Store Leads list, so a new pull only returns brands not yet looked at.
    Hand-picked test lists are left out on purpose: only Store Leads brands count (Aaron, 19 Oct), so a test
    brand that Store Leads returns still goes through the pipeline properly."""
    seen = set()
    for f in [*OUT.glob("*-sl-*.txt"), *OUT.glob("*storeleads*.txt")]:
        seen |= {l.strip().lower() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")}
    return seen


def pull(category, token, plus_only):
    params = {"f:cc": "US", "f:cat": category, "f:ermin": SALES_MIN, "f:ermax": SALES_MAX, "f:ds": "Active"}
    if plus_only:
        params["f:plan"] = "Shopify Plus"
    rows, cursor = [], None
    while True:
        d = query({**params, **({"cursor": cursor} if cursor else {})}, token)
        rows += d.get("domains", [])
        if not d.get("has_next_page"):
            return rows, d.get("total")
        cursor = d["next_cursor"]
        time.sleep(0.6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("categories", nargs="+")
    ap.add_argument("--plus-only", action="store_true")
    ap.add_argument("--sample", type=int, help="take this many per category, spread evenly across the sales band")
    a = ap.parse_args()
    token, seen = key(), seen_before()
    kept, total_found = {}, 0
    for cat in a.categories:
        rows, total = pull(cat, token, a.plus_only)
        rows = [r for r in rows if r.get("platform") == "shopify"]
        total_found += len(rows)
        new = [r for r in rows if r["name"].lower() not in seen and r["name"] not in kept]
        if a.sample and len(new) > a.sample:
            # evenly across the band, not just the biggest stores: the first page is sorted by sales
            new.sort(key=lambda r: r.get("estimated_sales") or 0)
            step = len(new) / a.sample
            new = [new[int(i * step)] for i in range(a.sample)]
        for r in new:
            kept[r["name"]] = r
        print(f"{cat}: {len(rows)} on Shopify in the band, {len(new)} taken")
    slug = re.sub(r"[^a-z0-9]+", "-", a.categories[0].rsplit("/", 1)[-1].lower()).strip("-")
    if len(a.categories) > 1:
        slug += f"-and-{len(a.categories) - 1}-more"
    stem = OUT / f"{dt.date.today().isoformat()}-sl-{slug}"
    header = f"# Store Leads API, {', '.join(a.categories)}; US, active, est. $5M-$20M/yr{', Plus only' if a.plus_only else ''}\n"
    stem.with_suffix(".txt").write_text(header + "".join(f"{d}\n" for d in kept))
    with stem.with_suffix(".jsonl").open("w") as f:
        for r in kept.values():
            f.write(json.dumps({k: r.get(k) for k in ("name", "categories", "plan", "estimated_sales", "city", "state",
                                                      "contact_info", "rank", "created_at")}) + "\n")
    print(f"{len(kept)} new brands, of {total_found} found -> {stem.with_suffix('.txt').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
