"""Shared helpers for the Afterglow theme checks. Base URL from THEME_URL, default the theme dev proxy."""
import os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("THEME_URL", "http://127.0.0.1:9292")
FAILS = []

def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)

def finish():
    print(f"\n{'FAILED' if FAILS else 'OK'}: {len(FAILS)} failing")
    sys.exit(1 if FAILS else 0)

def browser():
    p = sync_playwright().start()
    return p, p.chromium.launch()

def page(b, w=1440, h=900, mobile=False, **kw):
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, **kw)
    return ctx.new_page()
