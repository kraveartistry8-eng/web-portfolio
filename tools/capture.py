# -*- coding: utf-8 -*-
"""Pin a reference page to disk as an image, and say out loud whether the capture is usable.

    python3 ~/.claude/skills/gauntlet-loop/scripts/capture.py https://stripe.com/pricing
    python3 .../capture.py https://example.com --name edge-survive --mobile-only --out .

Writes references/YYYY-MM-DD-<slug>/{desktop,mobile}-{fold,full}.png and a capture.txt
beside them recording the URL, the viewport and what was dismissed. Every check prints
PASS or WARN. A WARN means look at the PNG before you use it as a quality bar: a capture
that is mostly flat colour is a consent wall or an unfired hero, and comparing work
against it produces fluent nonsense.
"""
import sys, re, io, json, datetime, pathlib, collections, urllib.parse
from playwright.sync_api import sync_playwright
from PIL import Image

# Captures land in the project you are working in, not next to this script.
# Override with --out. This matters because the skill is installed once in
# ~/.claude/skills and used from many different repos.
ROOT = pathlib.Path.cwd()
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}

# Freeze motion so the hero is captured in its final state, not mid-animation.
FREEZE = """*,*::before,*::after{animation:none!important;transition:none!important;
animation-duration:0s!important;transition-duration:0s!important;
scroll-behavior:auto!important;caret-color:transparent!important}"""

CONSENT_SELECTORS = [
    # Named consent platforms, most common first. A CMP's own class is far more
    # reliable than guessing at button text, which varies by site and language.
    "#onetrust-accept-btn-handler",
    "button.cky-btn-accept", "[data-cky-tag='accept-button']",          # CookieYes
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept",                            # Cookiebot
    ".osano-cm-accept-all",                                             # Osano
    "#didomi-notice-agree-button",                                      # Didomi
    ".qc-cmp2-summary-buttons button[mode='primary']",                  # Quantcast
    "#iubenda-cs-banner .iubenda-cs-accept-btn",                        # Iubenda
    ".cm-btn-success", ".cm-btn-accept-all",                            # Klaro
    "#hs-eu-confirmation-button",                                       # HubSpot
    ".cc-allow", ".cc-dismiss",                                         # Cookie Consent
    "#cookie-accept", ".cookie-accept", ".accept-cookies",
    "[data-testid='uc-accept-all-button']",                             # Usercentrics
    "button[aria-label*='accept' i]", "button[id*='accept' i]",
]

# Accept-ish, but never the buttons that open preferences or refuse. Getting this
# wrong is worse than not clicking: "Manage options" opens a modal that then covers
# the page for the whole capture.
ACCEPT_TEXT = re.compile(r"\b(accept|allow|agree|got it|okay|ok)\b", re.I)
REFUSE_TEXT = re.compile(
    r"\b(manage|settings|preferences|customi[sz]e|options|reject|decline|necessary|"
    r"selected|choices|more info|learn more|partners|purposes)\b", re.I)

# A fixed or sticky block of real size whose words are about cookies. Used both to
# wait for a banner to exist and to tell whether dismissing it worked.
CONSENT_PROBE = """() => {
  const vw = innerWidth, vh = innerHeight;
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (!['fixed','sticky'].includes(s.position)) continue;
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity < 0.1) continue;
    const r = e.getBoundingClientRect();
    if (r.width * r.height < vw * vh * 0.015) continue;
    const t = (e.innerText || '').trim();
    if (/cookie|consent|privacy|gdpr/i.test(t)) return t.slice(0, 80);
  }
  return null;
}"""


def same_page(a, b):
    """Is this the same page, ignoring cosmetic differences?

    http->https, a bare host gaining www., and a trailing slash are canonicalisation,
    not a redirect to somewhere else. Only a changed host or path means the server
    handed back a different page, which is the case worth warning about.
    """
    def norm(u):
        p = urllib.parse.urlsplit(u if "//" in u else "//" + u)
        host = (p.netloc or "").lower().split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        # Decode percent-encoding before comparing: a space in a path comes back
        # as %20 and would otherwise read as a redirect to a different page.
        path = urllib.parse.unquote(p.path or "/")
        return host, path.rstrip("/") or "/"
    return norm(a) == norm(b)


def slug(url):
    s = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:60]


def consent_present(page):
    try:
        return page.evaluate(CONSENT_PROBE)
    except Exception:
        return None


def dismiss_consent(page, wait_ms=5000):
    """Dismiss a consent banner, confirming it actually went away.

    Consent scripts are injected asynchronously, so a click attempted at
    domcontentloaded usually finds nothing there yet - which is why this waits for a
    banner to appear before trying, and why the caller runs it again after the page
    settles. Clicking blind and hoping is how a banner ends up in the pinned image.
    """
    waited = 0
    while waited < wait_ms and not consent_present(page):
        page.wait_for_timeout(250)
        waited += 250
    if not consent_present(page):
        return None

    clicked = []
    for sel in CONSENT_SELECTORS:
        if not consent_present(page):
            break
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible(timeout=400):
                el.click(timeout=1500, force=True)
                page.wait_for_timeout(600)
                clicked.append(sel)
        except Exception:
            pass

    if consent_present(page):
        try:
            for btn in page.get_by_role("button").all()[:80]:
                if not consent_present(page):
                    break
                try:
                    label = (btn.inner_text(timeout=400) or "").strip()
                except Exception:
                    continue
                if not label or len(label) > 40:
                    continue
                if ACCEPT_TEXT.search(label) and not REFUSE_TEXT.search(label):
                    try:
                        if btn.is_visible():
                            btn.click(timeout=1500, force=True)
                            page.wait_for_timeout(600)
                            clicked.append("button: " + label)
                    except Exception:
                        pass
        except Exception:
            pass

    return {"clicked": clicked, "remaining": consent_present(page)} if clicked else (
        {"clicked": [], "remaining": consent_present(page)})


def settle(page):
    """Trigger lazy content, then come back to the top. Returns (height_before, height_after)."""
    h0 = page.evaluate("document.body.scrollHeight")
    page.evaluate("""async () => {
        const step = window.innerHeight;
        for (let y = 0; y < document.body.scrollHeight; y += step) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 120));
        }
        window.scrollTo(0, 0);
    }""")
    page.wait_for_timeout(700)
    try:
        page.evaluate("document.fonts && document.fonts.ready")
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    page.wait_for_timeout(300)
    return h0, page.evaluate("document.body.scrollHeight")


def flatness(png_path):
    """Share of the image taken by its single most common colour, after quantising."""
    im = Image.open(png_path).convert("RGB")
    im.thumbnail((240, 240))
    px = [(r // 24, g // 24, b // 24) for r, g, b in im.getdata()]
    top = collections.Counter(px).most_common(1)[0][1]
    return top / len(px), len(set(px))


def capture(url, outdir, which):
    results, notes = [], {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name in which:
            w, h = VIEWPORTS[name]
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=2,
                is_mobile=(name == "mobile"),
                has_touch=(name == "mobile"),
                user_agent=None if name == "desktop" else
                ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                 "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
            )
            page = ctx.new_page()
            failed_requests = []
            page.on("requestfailed", lambda r: failed_requests.append(r.url))
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.add_style_tag(content=FREEZE)
            clicked = dismiss_consent(page)
            page.add_style_tag(content=FREEZE)  # re-apply, banners often inject their own
            h0, h1 = settle(page)
            late = dismiss_consent(page, wait_ms=1200)  # late injection, or it came back
            if late and late["clicked"]:
                clicked = {"clicked": (clicked or {}).get("clicked", []) + late["clicked"],
                           "remaining": late["remaining"]}
                page.wait_for_timeout(400)

            fold = outdir / f"{name}-fold.png"
            full = outdir / f"{name}-full.png"
            page.screenshot(path=str(fold))
            page.screenshot(path=str(full), full_page=True)

            # How much readable content is actually in the fold. A consent wall or an
            # unfired hero is flat AND nearly wordless; a dark minimal design is flat
            # and full of words. Pixels alone cannot tell those two apart.
            fold_text = page.evaluate("""() => {
                const vh = innerHeight; let n = 0;
                for (const e of document.body.querySelectorAll('h1,h2,h3,p,li,a,span,button')) {
                    const r = e.getBoundingClientRect();
                    if (r.top > vh || r.bottom < 0 || r.width === 0) continue;
                    const s = getComputedStyle(e);
                    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity < 0.1) continue;
                    n += (e.textContent || '').trim().length;
                }
                return n;
            }""")
            auth = page.evaluate("""() => {
                const vh = innerHeight;
                const hasPw = !!document.querySelector('input[type=password]');
                const AUTH = new RegExp(['sign ?in','log ?in','join now','create (an )?account','forgot password','continue with (google|apple|facebook|github)','email or phone','already a member'].join('|'), 'i');
                let authChars = 0, total = 0;
                for (const e of document.body.querySelectorAll('h1,h2,h3,p,li,a,span,button,label')) {
                    const r = e.getBoundingClientRect();
                    if (r.top > vh || r.bottom < 0 || r.width === 0) continue;
                    const s = getComputedStyle(e);
                    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity < 0.1) continue;
                    const t = (e.textContent || '').trim();
                    total += t.length;
                    if (AUTH.test(t)) authChars += t.length;
                }
                return {hasPw, ratio: total ? authChars / total : 0};
            }""")
            broken = page.evaluate("""() => [...document.images]
                .filter(i => i.complete && i.naturalWidth === 0).length""")
            # A big fixed element only matters if it actually paints over the page.
            # Sites commonly use a transparent full-viewport wrapper for scroll effects
            # (Pentagram, Stripe), and counting those made this check cry wolf on exactly
            # the mainstream sites someone would pick as a bar.
            covering = page.evaluate("""() => {
                const vw = innerWidth, vh = innerHeight;
                const paints = (s) => {
                    if (s.backgroundImage && s.backgroundImage !== 'none') return true;
                    const m = (s.backgroundColor || '').match(/rgba?\(([^)]+)\)/);
                    if (!m) return false;
                    const parts = m[1].split(',').map(x => parseFloat(x));
                    return parts.length < 4 ? true : parts[3] > 0.1;
                };
                return [...document.body.querySelectorAll('*')].filter(e => {
                    const s = getComputedStyle(e);
                    if (s.position !== 'fixed' || s.display === 'none' || +s.opacity < 0.1) return false;
                    const r = e.getBoundingClientRect();
                    if (r.width * r.height <= vw * vh * 0.5) return false;
                    return paints(s);
                }).length;
            }""")
            notes[name] = {"viewport": f"{w}x{h}", "requested_url": url,
                           "landed_url": page.url,
                           "redirected": not same_page(page.url, url),
                           "consent_clicked": clicked,
                           "consent_remaining": consent_present(page),
                           "has_password_field": auth["hasPw"],
                           "auth_text_ratio": round(auth["ratio"], 3),
                           "height_before_scroll": h0, "height_after_scroll": h1,
                           "fold_text_chars": fold_text, "broken_images": broken,
                           "fullscreen_fixed_layers": covering,
                           "failed_requests": len(failed_requests)}
            results.append((name, fold, full, notes[name]))
            ctx.close()
        browser.close()
    return results, notes


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 2
    url = args[0]
    if not url.startswith(("http", "file://")):
        url = "https://" + url
    name = None
    if "--name" in args:
        name = args[args.index("--name") + 1]
    which = ["desktop", "mobile"]
    if "--desktop-only" in args:
        which = ["desktop"]
    if "--mobile-only" in args:
        which = ["mobile"]

    base = ROOT
    if "--out" in args:
        base = pathlib.Path(args[args.index("--out") + 1]).expanduser().resolve()
    today = datetime.date.today().isoformat()
    outdir = base / "references" / f"{today}-{name or slug(url)}"
    outdir.mkdir(parents=True, exist_ok=True)

    results, notes = capture(url, outdir, which)

    FAIL, OK = [], []
    def chk(cond, msg, why=""):
        (OK if cond else FAIL).append(msg if cond else msg + (" - " + why if why else ""))

    for name_, fold, full, n in results:
        share, distinct = flatness(fold)
        words = n["fold_text_chars"]
        # Flat AND wordless is a dead capture. Flat and wordy is just a dark design.
        chk(not (share > 0.55 and words < 200),
            f"{name_} fold has content ({words} chars of visible text, {share:.0%} one tone)",
            "flat and nearly wordless is a consent wall or a hero that never fired")
        chk(words >= 50, f"{name_} fold is not blank ({words} chars of visible text)")
        chk(n["fullscreen_fixed_layers"] == 0,
            f"{name_} has no full-screen fixed layer over the page "
            f"({n['fullscreen_fixed_layers']} found)",
            "something is covering the page: a modal, a consent wall or an age gate")
        chk(n["broken_images"] == 0,
            f"{name_} images all loaded ({n['broken_images']} broken)")
        chk(not n.get("redirected"),
            f"{name_} stayed on the requested URL",
            f"it landed on {n.get('landed_url')!r} instead, so the image is of a "
            f"different page than the one you asked for")
        chk(not (n.get("has_password_field") or n.get("auth_text_ratio", 0) > 0.35),
            f"{name_} fold is not a sign-in page",
            f"password field present: {n.get('has_password_field')}, "
            f"{n.get('auth_text_ratio', 0):.0%} of fold text is sign-in wording - this is "
            f"an auth wall, which no other check can see because a login form is itself a "
            f"perfectly well-built page")
        chk(not n.get("consent_remaining"),
            f"{name_} has no consent banner left on the page",
            f"a cookie banner survived into the capture: {n.get('consent_remaining')!r}")
        chk(n["height_after_scroll"] >= n["height_before_scroll"],
            f"{name_} page height stable after scrolling "
            f"({n['height_before_scroll']} -> {n['height_after_scroll']})")
        OK.append(f"{name_} written: {fold.name}, {full.name}")

    (outdir / "capture.txt").write_text(json.dumps(
        {"url": url, "captured": datetime.datetime.now().isoformat(timespec="seconds"),
         "viewports": notes}, indent=2), encoding="utf-8")

    for m in OK:
        print("  PASS ", m)
    for m in FAIL:
        print("  WARN ", m)
    print()
    try:
        shown = outdir.relative_to(pathlib.Path.cwd())
    except ValueError:
        shown = outdir
    print("  pinned to:", shown)
    if FAIL:
        print("  LOOK AT THE PNG before using this as a quality bar.")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
