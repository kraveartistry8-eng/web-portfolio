# -*- coding: utf-8 -*-
"""Audit the Afterglow brand tokens and guideline document.

Mirrors tools/audit.py: checks collect into OK and FAIL, each prints one line,
and the exit status is the gate. Later tasks add checks here and run this as
their verification, so the harness is written to fail before the work lands.
"""
import io
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "brand" / "resources" / "design-tokens.json"
IDENTITY = ROOT / "brand" / "guide-sources" / "BRAND-IDENTITY.md"
VOICE = ROOT / "brand" / "resources" / "voice-tone.md"

VOID = "#080808"
SURFACE_DEEP = "#141414"
SURFACE = "#2B2B2B"


def rgb(hex_value):
    h = hex_value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_value):
    r, g, b = [_linear(c) for c in rgb(hex_value)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(hex_a, hex_b):
    """WCAG relative-luminance contrast ratio. Task 6 reuses this."""
    la, lb = luminance(hex_a), luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def oklch(hex_value):
    """sRGB hex to OKLCH (l, c, h). Lightness here is perceptual, which is the
    only space in which "the light only ever deepens" is a measurable claim."""
    r, g, b = [_linear(c) for c in rgb(hex_value)]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s3 = [math.copysign(abs(v) ** (1.0 / 3.0), v) for v in (l, m, s_)]
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s3
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s3
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s3
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360.0


def voice_vocabulary():
    """The words that belong to Afterglow, read from voice-tone.md rather than
    copied here, so the list stays single-sourced."""
    text = io.open(VOICE, encoding="utf-8").read()
    match = re.search(
        r"## Words that belong to Afterglow\s*\n(.*?)\n##", text, re.S)
    if not match:
        return set()
    words = re.split(r"[,\n]", match.group(1))
    return set(w.strip().lower() for w in words if w.strip())

OK = []
FAIL = []


def chk(cond, msg):
    (OK if cond else FAIL).append(msg)


def leaves(obj, prefix=""):
    """Every scalar in the tree, as (dotted path, value)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            for item in leaves(v, prefix + "." + str(k) if prefix else str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in leaves(v, "%s[%d]" % (prefix, i)):
                yield item
    else:
        yield prefix, obj


def get(tree, dotted):
    """Fetch a dotted path, or the sentinel MISSING."""
    cur = tree
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


PRINT_BLOCKS = []

MISSING = object()


PAGE_T = """
            const __pgs = [...document.querySelectorAll('.page')].map(p => {
                const r = p.getBoundingClientRect();
                return {top: r.top + window.scrollY, h: r.height};
            });
            // The fall runs page by page: page i carries the slice from i/n to (i+1)/n,
            // whatever each page's height turns out to be.
            function __t(y) {
                const n = __pgs.length;
                if (!n) return 0;
                for (let i = 0; i < n; i++) {
                    const g = __pgs[i];
                    if (y >= g.top - 0.5 && y <= g.top + g.h + 0.5)
                        return (i + Math.min(1, Math.max(0, (y - g.top) / g.h))) / n;
                }
                return y < __pgs[0].top ? 0 : 1;
            }
"""

TEXT_PROBE = """() => {""" + PAGE_T + """
            const out = [];
            document.querySelectorAll('.measure *, .crossover em').forEach(e => {
                if (!e.textContent.trim()) return;
                if (e.children.length && !['P','H1','H2','SPAN','B','EM','DT','DD','A'].includes(e.tagName)) return;
                const b = e.getBoundingClientRect();
                if (!b.height) return;
                const cs = getComputedStyle(e);
                // the nearest ancestor that actually paints decides the background
                let node = e, bg = null;
                while (node && node !== document.documentElement) {
                    const c = getComputedStyle(node).backgroundColor;
                    if (c && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(c)) { bg = c; break; }
                    if (node.classList && (node.classList.contains('doc')
                        || node.classList.contains('page'))) break;
                    node = node.parentElement;
                }
                out.push({tag: e.tagName, text: e.textContent.trim().slice(0, 34),
                          color: cs.color, size: parseFloat(cs.fontSize),
                          weight: cs.fontWeight, bg: bg,
                          t: __t(b.top + window.scrollY + b.height / 2)});
            });
            return out;
        }"""

DOC = ROOT / "brand" / "guide-sources" / "2026-10-07-afterglow-guidelines.html"

_HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
_RGBA = re.compile(r"rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)")


def _expand(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def css_colour(value, variables):
    """Resolve a CSS colour value to a hex string, following var() one level deep.
    Returns None when the value is not a colour we can reason about."""
    seen = 0
    while "var(" in value and seen < 8:
        m = re.search(r"var\(\s*(--[\w-]+)\s*(?:,([^()]*))?\)", value)
        if not m:
            break
        name, fallback = m.group(1), (m.group(2) or "").strip()
        value = value[:m.start()] + variables.get(name, fallback) + value[m.end():]
        seen += 1
    m = _HEX.search(value)
    if m:
        return _expand(m.group(0))
    m = _RGBA.search(value)
    if m:
        return "#%02X%02X%02X" % tuple(int(round(float(m.group(i)))) for i in (1, 2, 3))
    return None


def parse_rules(css):
    """[(selector, {property: value})] for top-level rules, at-rule bodies included."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{", "", css)          # flatten media blocks
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = " ".join(m.group(1).split())
        decls = {}
        for part in m.group(2).split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                decls[k.strip().lower()] = v.strip()
        if sel and decls:
            out.append((sel, decls))
    return out


# The six locked neutrals, copied from the plan's Global Constraints.
NEUTRALS = {
    "color.ground.value": "#080808",
    "color.surface-deep.value": "#141414",
    "color.surface.value": "#2B2B2B",
    "color.text.value": "#EEECEA",
    "color.muted.value": "#C0C0C0",
    "color.border.value": "rgba(192,192,192,0.22)",
}

# Krave production tracker accents. They belong to a different brand.
FORBIDDEN = ("#39FF14", "#FF00BD")

# Explanatory keys present when this harness was written. They carry the reasoning
# behind a decision, so a careless rewrite of the token file must not drop them.
NOTE_KEYS = (
    "color.stages._note",
    "color._forbidden",
    "typography._status",
    "spacing._status",
    "radius._status",
    "shadow._status",
    "motion._status",
)

# Values the build cannot proceed without. A missing key has no value to be null,
# so absence has to be checked separately or Task 4 could pass with nothing set.
REQUIRED = (
    ["color.stages.%d.%s" % (n, f) for n in (1, 2, 3, 4) for f in ("name", "value")]
    + [
        "typography.display.family",
        "typography.body.family",
        "typography.scale",
        "typography.tracking",
        "typography.leading",
        "spacing.base",
        "spacing.scale",
        "motion.duration",
        "motion.ease",
    ]
)

# The spec fixes the substance of these but not their shape, so require a value
# of some kind rather than a key name the spec never chose.
REQUIRED_BRANCHES = ("radius", "shadow")

TOKEN_BRANCHES = ("color.stages", "typography", "spacing", "radius", "shadow", "motion")



def document_checks(chk, tokens):
    """Checks that need the rendered document. They fail loudly while it does not exist."""
    if not DOC.exists():
        for name in ("fall_monotonic", "no_brightening", "rail_is_folio",
                     "ledger_is_void", "svh_not_vh", "specimen_truth", "faces_loaded",
                     "ledger_anchored", "text_on_fall", "ledger_clear", "ground_truth",
                     "crossover_in_fall", "no_h_scroll_390", "ledger_inline",
                     "no_dead_leaders", "fall_survives", "ratios_recomputed",
                     "touch_targets", "print_ground", "pages_snap", "pages_join",
                     "crossover_on_break", "one_numbering"):
            chk(False, "%-16s %s  :: %s does not exist yet"
                % (name, "needs the document", DOC.name))
        return

    ramp0 = [get(tokens, "color.stages.%d.value" % n) for n in (1, 2, 3, 4)]

    def _fall(t):
        """The fall at document position t, interpolated in sRGB the way an
        unprefixed CSS gradient interpolates."""
        t = max(0.0, min(1.0, t))
        stops = list(zip((0.0, 1 / 3.0, 2 / 3.0, 1.0), ramp0))
        for i in range(3):
            (p0, c0), (p1, c1) = stops[i], stops[i + 1]
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0)
                a_, b_ = rgb(c0), rgb(c1)
                return "#%02X%02X%02X" % tuple(
                    int(round(a_[j] + (b_[j] - a_[j]) * f)) for j in range(3))
        return ramp0[-1]

    html = io.open(DOC, encoding="utf-8").read()
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))

    # ---------- svh_not_vh
    # case-insensitive, and inline style attributes count as stylesheet rules
    inline_styles = " ".join(re.findall(r'style="([^"]*)"', html))
    units = re.findall(r"[\d.]+((?:[sdl])?vh)\b", (css + " " + inline_styles), re.I)
    units = [u.lower() for u in units]
    wrong = sorted(set(u for u in units if u != "svh"))
    chk(not wrong,
        "svh_not_vh       full-height values use svh only%s"
        % ("  :: found " + ", ".join(wrong) if wrong else "  :: %d svh values" % len(units)))

    # ---------- no_brightening
    rules = parse_rules(css)
    variables = {}
    for sel, decls in rules:
        if sel.endswith(":root") or sel == ":root":
            for k, v in decls.items():
                if k.startswith("--"):
                    variables[k] = v
    # Split every rule on commas. "a:hover,a:focus-visible" reduced whole gives the
    # base "a,a", which matches no resting rule, and the fallback then hides the very
    # violation this check exists to find.
    def selectors(sel):
        return [p.strip() for p in sel.split(",") if p.strip()]

    STATE = r":(hover|focus-visible|focus|active)"
    # Every property through which a state can get lighter. Comparing only color and
    # background let filter:brightness(2.2) and a white border through.
    COLOUR_PROPS = ("color", "background-color", "background", "border-color",
                    "border-bottom-color", "border-top-color", "border-left-color",
                    "border-right-color", "border-bottom", "border-top", "border",
                    "outline-color", "outline", "text-decoration-color",
                    "caret-color", "box-shadow", "text-shadow")
    resting = {}
    for sel, decls in rules:
        for one in selectors(sel):
            if re.search(STATE, one):
                continue
            if "opacity" in decls:
                resting.setdefault(one, {})["opacity"] = decls["opacity"]
            for prop in COLOUR_PROPS:
                if prop in decls:
                    resting.setdefault(one, {})[prop] = decls[prop]
    brighter = []
    checked = 0
    unresolved = []
    for sel, decls in rules:
        for one in selectors(sel):
            if not re.search(STATE, one):
                continue
            base = re.sub(STATE, "", one).strip()
            # a filter or a blend mode can brighten anything, and the brand uses none
            for prop in ("filter", "backdrop-filter", "mix-blend-mode"):
                v = decls.get(prop)
                if v and v.strip().lower() not in ("none", "normal"):
                    brighter.append("%s sets %s:%s, which can lighten anything"
                                    % (one, prop, v.strip()))
            if "opacity" in decls:
                try:
                    new_o = float(decls["opacity"])
                    old_o = float(resting.get(base, {}).get("opacity", 1.0))
                    if new_o > old_o + 1e-6:
                        brighter.append("%s raises opacity from %g to %g" % (one, old_o, new_o))
                except ValueError:
                    pass
            for prop in COLOUR_PROPS:
                if prop not in decls:
                    continue
                new_c = css_colour(decls[prop], variables)
                if new_c is None:
                    continue
                old_raw = resting.get(base, {}).get(prop)
                if old_raw is None:
                    # No resting declaration to compare against. Say so rather than
                    # inventing a default that could pass a real brightening.
                    unresolved.append("%s %s has no resting %s on %s" % (one, prop, prop, base))
                    continue
                old_c = css_colour(old_raw, variables)
                if old_c is None:
                    unresolved.append("%s %s resting value %r is not a colour"
                                      % (one, prop, old_raw))
                    continue
                checked += 1
                if oklch(new_c)[0] > oklch(old_c)[0] + 0.002:
                    brighter.append("%s %s %s (L %.3f) is lighter than %s (L %.3f)"
                                    % (one, prop, new_c, oklch(new_c)[0],
                                       old_c, oklch(old_c)[0]))
    brighter += unresolved
    chk(not brighter,
        "no_brightening   no state is lighter than its resting value%s"
        % ("  :: " + "; ".join(brighter) if brighter
           else "  :: %d state declarations checked" % checked))

    from playwright.sync_api import sync_playwright
    from PIL import Image
    import tempfile

    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        pg.goto(DOC.resolve().as_uri())
        pg.wait_for_timeout(700)

        # ---------- faces_loaded
        # "It is set in the chosen faces" is a stated form requirement. Offline, or if
        # the font host fails, the document silently renders in Georgia and system-ui
        # and the requirement is false with nothing to show for it.
        pg.evaluate("() => document.fonts.ready")
        pg.wait_for_timeout(900)
        want_faces = [get(tokens, "typography.display.family"),
                      get(tokens, "typography.body.family")]
        loaded = pg.evaluate("""(f) => f.map(n => {
            const c = document.createElement('canvas').getContext('2d');
            c.font = '400 48px serif';
            const base = c.measureText('Afterglow Hamburgefonstiv').width;
            c.font = '400 48px "' + n + '", serif';
            const got = c.measureText('Afterglow Hamburgefonstiv').width;
            return [n, document.fonts.check('400 48px "' + n + '"'),
                    Math.abs(got - base) > 0.5];
        })""", want_faces)
        missing = ["%s did not load" % n for n, ok, distinct in loaded if not (ok and distinct)]
        chk(not missing,
            "faces_loaded     the document is set in the chosen faces%s"
            % ("  :: " + "; ".join(missing) if missing
               else "  :: %s" % ", ".join(n for n, _, _ in loaded)))

        # ---------- rail_is_folio
        rail = pg.query_selector(".rail")
        # The rail reads position in the fall. Now that pages exist it reads the page
        # too, and a mark that gave one without the other would be half a folio.
        marks = pg.evaluate("""() => [...document.querySelectorAll('.rail .rm')]
            .map(e => (e.textContent || '').replace(/\\s+/g, ' ').trim())""")
        no_l = [m for m in marks if "L" not in m]
        no_page = [m for m in marks if not re.search(r"\d{2}\s*/\s*\d{2}", m)]
        ok_rail = rail is not None and marks and not no_l and not no_page
        chk(ok_rail,
            "rail_is_folio    every rail mark carries its page and its lightness%s"
            % ("  :: %d marks" % len(marks) if ok_rail
               else "  :: rail %s, without lightness %s, without page %s"
                    % (rail is not None, no_l, no_page)))

        # ---------- ledger_is_void
        bg = pg.evaluate("""() => {
            const l = document.querySelector('.ledger');
            if (!l) return null;
            return getComputedStyle(l).backgroundColor;
        }""")
        allowed = {get(tokens, "color.ground.value"),
                   get(tokens, "color.surface-deep.value"),
                   get(tokens, "color.surface.value")}
        got = css_colour(bg or "", {}) if bg else None
        chk(got is not None and got.upper() in {a.upper() for a in allowed},
            "ledger_is_void   the ledger sits on the void or a surface step%s"
            % ("  :: %s" % got if got and got.upper() in {a.upper() for a in allowed}
               else "  :: ledger background is %r" % (bg,)))

        # ---------- pages_snap
        # The document is twelve pages, each at least one screen, each a snap point.
        # A page that is exactly one screen tall would clip the long specification
        # pages, so the check requires a minimum and forbids a maximum.
        pages = pg.evaluate("""() => {
            const ps = [...document.querySelectorAll('.page')];
            const host = document.scrollingElement;
            return {
                n: ps.length,
                snapType: getComputedStyle(host).scrollSnapType
                          || getComputedStyle(document.body).scrollSnapType,
                rows: ps.map(p => {
                    const r = p.getBoundingClientRect(), cs = getComputedStyle(p);
                    const m = p.querySelector('.measure');
                    const mr = m ? m.getBoundingClientRect() : r;
                    return {top: r.top + window.scrollY, height: r.height,
                            align: cs.scrollSnapAlign,
                            minh: cs.minHeight,
                            overflow: cs.overflow,
                            x: mr.right + window.scrollX - 40,
                            folio: (p.querySelector('.secnum') || {}).textContent || null,
                            page: p.getAttribute('data-page')};
                })};
        }""")
        vh = pg.evaluate("window.innerHeight")
        bad = []
        if pages["n"] != 12:
            bad.append("%d pages, not 12" % pages["n"])
        if "y" not in (pages["snapType"] or ""):
            bad.append("the scroll container has no y snap type (%r)" % pages["snapType"])
        for r in pages["rows"]:
            if r["align"] != "start":
                bad.append("page %s aligns %s, not start" % (r["page"], r["align"]))
            if r["height"] < vh - 1:
                bad.append("page %s is %.0fpx, under one screen of %dpx"
                           % (r["page"], r["height"], vh))
            if r["overflow"] in ("hidden", "clip"):
                bad.append("page %s clips its content" % r["page"])
        chk(not bad,
            "pages_snap       twelve pages, each a screen or more, each a snap point%s"
            % ("  :: " + "; ".join(bad) if bad
               else "  :: 12 pages, shortest %.0fpx against a %dpx screen"
                    % (min(r["height"] for r in pages["rows"]), vh)))

        def _page_fall(index, frac):
            """The fall inside page `index`, which carries the slice of the ramp from
            index/12 to (index+1)/12. The ramp is indexed to pages, not to pixels."""
            n = max(1, pages["n"])
            return _fall((index + max(0.0, min(1.0, frac))) / float(n))

        # ---------- fall_monotonic
        # Sampled inside the measure's right padding: the fall is there, no glyph is,
        # and the fixed slug never reaches it. Clipped in page coordinates, never
        # viewport coordinates, or every sample lands on whatever is pinned at y=0.
        tmp = pathlib.Path(tempfile.gettempdir()) / "afterglow-fall.png"

        def sample(x, y):
            pg.screenshot(path=str(tmp), full_page=True,
                          clip={"x": x, "y": y, "width": 3, "height": 3})
            return oklch("#%02X%02X%02X"
                         % Image.open(tmp).convert("RGB").getpixel((1, 1)))[0]

        ls, want, where = [], [], []
        for idx, r in enumerate(pages["rows"]):
            for frac in (0.0, 1.0):
                y = r["top"] + (r["height"] - 3) * frac
                ls.append(sample(r["x"], y))
                want.append(oklch(_page_fall(idx, frac))[0])
                where.append("page %s %s" % (r["page"], "top" if frac == 0.0 else "foot"))
        if not ls:
            rises, strays = ["no page carried a sample: the document has no pages"], []
        rises = ["%s (%.4f) is not below %s (%.4f)" % (where[i + 1], ls[i + 1], where[i], ls[i])
                 for i in range(len(ls) - 1) if ls[i + 1] > ls[i] + 0.0005] or (
                 ["no page carried a sample: the document has no pages"] if not ls else [])
        # A sample that landed on a rule or a glyph instead of the ground would make
        # this check meaningless, so each one must also match the fall it claims to be.
        strays = ["%s sampled L %.4f, the fall is L %.4f there" % (where[i], ls[i], want[i])
                  for i in range(len(ls)) if abs(ls[i] - want[i]) > 0.01]
        chk(not rises and not strays,
            "fall_monotonic   ground lightness falls across every page%s"
            % ("  :: " + "; ".join(rises + strays) if (rises or strays)
               else "  :: %d samples, %.3f down to %.3f" % (len(ls), ls[0], ls[-1])))

        # ---------- pages_join
        # The break is survivable only if page N ends on the colour page N+1 begins on.
        # Measured from the rendered pixels, not from the CSS that was asked for.
        seams = []
        for i in range(len(pages["rows"]) - 1):
            foot, top = ls[i * 2 + 1], ls[(i + 1) * 2]
            if abs(foot - top) > 0.004:
                seams.append("page %s foots at L %.4f, page %s opens at L %.4f"
                             % (pages["rows"][i]["page"], foot,
                                pages["rows"][i + 1]["page"], top))
        if len(pages["rows"]) < 2:
            seams.append("fewer than two pages to join")
        chk(not seams,
            "pages_join       every page opens on the value the one before it closed on%s"
            % ("  :: " + "; ".join(seams) if seams
               else "  :: %d seams, widest %.4f L"
                    % (len(pages["rows"]) - 1,
                       max(abs(ls[i * 2 + 1] - ls[(i + 1) * 2])
                           for i in range(len(pages["rows"]) - 1)))))

        # ---------- crossover_on_break
        # Twelve pages exist so the inversion lands on a page turn. If the crossover
        # drifts off the boundary a reader meets two text colours on one ground.
        xo = pg.evaluate("""() => {
            const c = document.querySelector('.crossover');
            if (!c) return null;
            const r = c.getBoundingClientRect();
            return r.top + window.scrollY + r.height / 2;
        }""")
        rows = pages["rows"]
        half = len(rows) // 2
        boundary = rows[half]["top"] if len(rows) > half else None
        off = None if (xo is None or boundary is None) else abs(xo - boundary)
        chk(off is not None and off <= 2.0,
            "crossover_on_break the inversion lands on the turn into page %02d%s"
            % (half + 1,
               ("  :: no crossover or no page boundary to measure against" if off is None
                else "  :: %.1fpx off the boundary" % off) if (off is None or off > 2.0)
               else "  :: %.1fpx off a %.0fpx page" % (off, rows[half]["height"])))

        # ---------- one_numbering
        # The page number is the only number. A section folio that disagrees with the
        # page it sits on is a second numbering system, and cross-references drift.
        mismatched = ["page %s carries folio %s" % (r["page"], r["folio"].strip())
                      for r in rows
                      if r["folio"] and r["folio"].strip() != (r["page"] or "").strip()]
        folio_count = len([r for r in rows if r["folio"]])
        # A check that matched nothing and reported success is the defect this harness
        # was already caught committing once. The specification pages all carry a folio.
        if not rows:
            mismatched.append("the document has no pages to number")
        if rows and folio_count != len(rows) // 2:
            mismatched.append("%d folios across %d pages, expected %d"
                              % (folio_count, len(rows), len(rows) // 2))
        chk(not mismatched,
            "one_numbering    every section folio is its own page number%s"
            % ("  :: " + "; ".join(mismatched) if mismatched
               else "  :: %d folios, all matching" % folio_count))

        # ---------- specimen_truth
        # Recomputing contrast(data-fg, data-bg) only proves the arithmetic is
        # self-consistent: any internally consistent lie passes. So the colours
        # themselves must also be ones the document measured, not ones it invented.
        claims = pg.evaluate("""() => {
            const pgs = [...document.querySelectorAll('.page')];
            const docAt = row => {
                const host = row.closest('.page');
                const i = pgs.indexOf(host);
                return i < 0 ? parseFloat(row.dataset.at)
                             : (i + parseFloat(row.dataset.at)) / pgs.length;
            };
            return [...document.querySelectorAll('[data-fg][data-bg]')].map(e => {
                const row = e.closest('[data-at]');
                const dt = e.closest('dd') && e.closest('dd').previousElementSibling;
                return {fg: e.dataset.fg, bg: e.dataset.bg, shown: e.textContent.trim(),
                        at: row ? docAt(row) : null,
                        label: dt ? dt.textContent.trim() : ''};
            });
        }""")
        palette = set()
        for path in ("color.ground.value", "color.surface-deep.value", "color.surface.value",
                     "color.text.value", "color.muted.value"):
            v = get(tokens, path)
            if isinstance(v, str):
                palette.add(v.upper())
        for n in (1, 2, 3, 4):
            palette.add(get(tokens, "color.stages.%d.value" % n).upper())
        ats = sorted({c["at"] for c in claims if c["at"] is not None})
        for a_ in ats:
            palette.add(_fall(a_).upper())

        wrong = []
        for c in claims:
            try:
                printed = float(c["shown"].split(":")[0])
            except ValueError:
                wrong.append("%r is not a ratio" % c["shown"]); continue
            real = contrast(c["fg"], c["bg"])
            if abs(printed - real) > 0.005:
                wrong.append("%s on %s printed %.2f, computed %.2f"
                             % (c["fg"], c["bg"], printed, real))
            for role, col in (("fg", c["fg"]), ("bg", c["bg"])):
                if col.upper() not in palette:
                    wrong.append("%s is not a colour this document measured; the "
                                 "palette is %s" % (col, ", ".join(sorted(palette))))
            # a row anchored in the fall must name the ground the fall actually reaches
            if c["at"] is not None and c["label"].lower() == "ground":
                want = _fall(c["at"]).upper()
                if c["bg"].upper() != want:
                    wrong.append("the row at t=%.4f names ground %s; the fall reaches %s"
                                 % (c["at"], c["bg"], want))
        chk(claims and not wrong,
            "specimen_truth   every printed ratio describes colours the document measured%s"
            % ("  :: " + "; ".join(sorted(set(wrong))[:4]) if wrong
               else "  :: %d ratios recomputed against a %d colour palette"
                    % (len(claims), len(palette))))

        # the declared ground of every anchored row, checked against the fall itself
        grounds = pg.evaluate("""() => {
            const pgs = [...document.querySelectorAll('.page')];
            return [...document.querySelectorAll('.lrow[data-at]')].map(e => {
                const dts = [...e.querySelectorAll('dt')];
                const g = dts.find(d => d.textContent.trim().toLowerCase() === 'ground');
                const i = pgs.indexOf(e.closest('.page'));
                const at = parseFloat(e.dataset.at);
                return {at: i < 0 ? at : (i + at) / pgs.length,
                        ground: g && g.nextElementSibling
                                ? g.nextElementSibling.textContent.trim() : null};
            }).filter(x => x.ground);
        }""")
        gbad = ["the row at t=%.4f prints ground %s; the fall reaches %s"
                % (g["at"], g["ground"], _fall(g["at"]))
                for g in grounds if g["ground"].upper() != _fall(g["at"]).upper()]
        chk(not gbad,
            "ground_truth     a named ground equals the fall at that position%s"
            % ("  :: " + "; ".join(gbad) if gbad
               else "  :: %d named grounds checked" % len(grounds)))

        # ---------- ledger_anchored
        rows = pg.evaluate("""() => {
            return [...document.querySelectorAll('.lrow[data-at]')].map(e => {
                const host = e.closest('.page').getBoundingClientRect();
                const top = host.top + window.scrollY, h = host.height;
                const b = e.getBoundingClientRect();
                const centre = b.top + window.scrollY + b.height / 2;
                return {at: parseFloat(e.dataset.at),
                        actual: (centre - top) / h,
                        wanted_px: parseFloat(e.dataset.at) * h,
                        actual_px: centre - top,
                        top_px: b.top + window.scrollY - top,
                        bottom_px: (b.top + window.scrollY + b.height) - top,
                        page_px: h,
                        label: (e.querySelector('.lk') || {}).textContent || ''};
            });
        }""")
        off, edges = [], 0
        for r in rows:
            # an endpoint row is clamped so it does not hang off the column; it is held
            # to the edge it is pinned to instead of to its own centre
            if r["at"] <= 0.001 or r["at"] >= 0.999:
                edges += 1
                want = 0.0 if r["at"] <= 0.001 else 1.0
                # A clamped row is pinned by one edge, not centred, and these rows are
                # tall. Holding its centre to the page edge would be a test of how
                # little the row says, so the pinned edge is what gets measured.
                gap = r["top_px"] if want == 0.0 else r["page_px"] - r["bottom_px"]
                if gap < -1.0 or gap > 48.0:
                    off.append("%s is pinned to the %s edge but sits %.0fpx from it"
                               % (r["label"].strip()[:24], "top" if want == 0.0 else "bottom",
                                  gap))
                continue
            if abs(r["actual_px"] - r["wanted_px"]) > 4.0:
                off.append("%s sits %.1fpx into its page, the fall reaches its value at %.1fpx"
                           % (r["label"].strip()[:28], r["actual_px"], r["wanted_px"]))
        chk(rows and not off,
            "ledger_anchored  each row sits where the fall reaches its value%s"
            % ("  :: " + "; ".join(off) if off
               else "  :: %d rows within 4px, %d endpoint rows held to their edge"
                    % (len(rows) - edges, edges)))

        # ---------- ledger_clear
        # Rows are positioned by the value they describe, not by flow, so nothing stops
        # two of them landing on top of each other and clipping their own readings.
        boxes = pg.evaluate("""() => [...document.querySelectorAll('.lrow')].map(e => {
            const b = e.getBoundingClientRect();
            return {top: b.top + window.scrollY, bottom: b.bottom + window.scrollY,
                    label: (e.querySelector('.lk') || {}).textContent || ''};
        })""")
        boxes.sort(key=lambda b: b["top"])
        clashes = []
        for i in range(len(boxes) - 1):
            a_, b_ = boxes[i], boxes[i + 1]
            if b_["top"] < a_["bottom"] - 0.5:
                clashes.append("%s overlaps %s by %.0fpx"
                               % (" ".join(a_["label"].split())[:26],
                                  " ".join(b_["label"].split())[:26],
                                  a_["bottom"] - b_["top"]))
        chk(boxes and not clashes,
            "ledger_clear     no two ledger rows overlap%s"
            % ("  :: " + "; ".join(clashes) if clashes
               else "  :: %d rows, closest gap %.0fpx"
                    % (len(boxes), min((boxes[i + 1]["top"] - boxes[i]["bottom"])
                                       for i in range(len(boxes) - 1)))))

        # ---------- text_on_fall
        # Contrast here is a function of position, not a constant. Every text element is
        # measured against the ground at its own place in the document.
        els = pg.evaluate(TEXT_PROBE)
        fails = []
        measured = 0
        for e in els:
            fg = css_colour(e["color"], {})
            if fg is None:
                continue
            bg = css_colour(e["bg"], {}) if e["bg"] else _fall(e["t"])
            pt = e["size"] * 72.0 / 96.0
            large = pt >= 18 or (pt >= 14 and e["weight"] in ("700", "bold", "800", "900"))
            floor = 3.0 if large else 4.5
            r = contrast(fg, bg)
            measured += 1
            if r < floor - 0.005:
                fails.append("%s %r at t=%.3f: %s on %s is %.2f:1, needs %.1f:1"
                             % (e["tag"], e["text"], e["t"], fg, bg, r, floor))
        chk(not fails,
            "text_on_fall     every text element clears its floor where it sits%s"
            % ("  :: " + "; ".join(fails[:6]) if fails
               else "  :: %d elements measured against their own ground" % measured))

        # ================= 390px =================
        mp = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mp.goto(DOC.resolve().as_uri())
        mp.wait_for_timeout(700)

        sw = mp.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        chk(sw[0] <= sw[1] + 1,
            "no_h_scroll_390  no horizontal scroll at 390px  :: %d vs %d" % tuple(sw))

        # ---------- ledger_inline
        rows390 = mp.evaluate("""() => {
            const m = document.querySelector('.measure').getBoundingClientRect();
            return [...document.querySelectorAll('.lrow')].map(e => {
                const b = e.getBoundingClientRect();
                return {top: b.top + window.scrollY, bottom: b.bottom + window.scrollY,
                        width: b.width, measure: m.width,
                        pos: getComputedStyle(e).position,
                        label: (e.querySelector('.lk') || {}).textContent || ''};
            });
        }""")
        bad = []
        for r in rows390:
            if r["pos"] != "static":
                bad.append("%s is still %s" % (" ".join(r["label"].split())[:22], r["pos"]))
            if r["width"] < r["measure"] * 0.75:
                bad.append("%s is %.0fpx wide in a %.0fpx measure"
                           % (" ".join(r["label"].split())[:22], r["width"], r["measure"]))
        order = [r["top"] for r in rows390]
        if order != sorted(order):
            bad.append("rows are not in document order")
        for i in range(len(rows390) - 1):
            if rows390[i + 1]["top"] < rows390[i]["bottom"] - 0.5:
                bad.append("rows sit side by side")
                break
        chk(rows390 and not bad,
            "ledger_inline    at 390px rows are full width and in document order%s"
            % ("  :: " + "; ".join(bad[:4]) if bad else "  :: %d rows stacked" % len(rows390)))

        # ---------- no_dead_leaders
        # Binding this to .lrow.anchored::before only asserted that a display:none rule
        # exists for that exact selector; any other painted leader sailed through.
        leaders = mp.evaluate("""() => {
            const out = [];
            document.querySelectorAll('.lrow').forEach(e => {
                const cs = getComputedStyle(e);
                for (const side of ['Left', 'Right']) {
                    if (parseFloat(cs['border' + side + 'Width']) > 0) {
                        out.push('border-' + side.toLowerCase() + ' on ' + e.className);
                    }
                }
                for (const pseudo of ['::before', '::after']) {
                    const p = getComputedStyle(e, pseudo);
                    if (p.display === 'none' || p.content === 'none') continue;
                    const w = parseFloat(p.width) || 0, h = parseFloat(p.height) || 0;
                    if (w > 0 && h > 0) out.push(pseudo + ' paints ' + w + 'x' + h +
                                                 ' on ' + e.className);
                }
            });
            return out;
        }""")
        chk(not leaders,
            "no_dead_leaders  nothing paints a leader at 390px%s"
            % ("  :: " + "; ".join(leaders[:4]) if leaders
               else "  :: no borders and no painted pseudo-elements on any row"))

        # ---------- fall_survives
        rows390 = mp.evaluate("""() => [...document.querySelectorAll('.page')].map(p => {
            const r = p.getBoundingClientRect();
            return {top: r.top + window.scrollY, height: r.height,
                    page: p.getAttribute('data-page')};
        })""")
        ls390, want390, where390 = [], [], []
        n390 = max(1, len(rows390))
        for idx, r in enumerate(rows390):
            for frac in (0.02, 0.98):
                y = r["top"] + (r["height"] - 3) * frac
                mp.screenshot(path=str(tmp), full_page=True,
                              clip={"x": 2, "y": y, "width": 3, "height": 3})
                ls390.append(oklch("#%02X%02X%02X"
                                   % Image.open(tmp).convert("RGB").getpixel((1, 1)))[0])
                want390.append(oklch(_fall((idx + frac) / float(n390)))[0])
                where390.append("page %s %s" % (r["page"], "top" if frac < .5 else "foot"))
        if not ls390:
            ls390, want390, where390 = [1.0, 1.0], [0.0, 0.0], ["no pages", "no pages"]
        rises390 = ["%s (%.4f) is not below %s (%.4f)"
                    % (where390[i + 1], ls390[i + 1], where390[i], ls390[i])
                    for i in range(len(ls390) - 1) if ls390[i + 1] > ls390[i] + 0.0005]
        strays390 = ["%s sampled L %.4f, the fall is L %.4f there"
                     % (where390[i], ls390[i], want390[i])
                     for i in range(len(ls390)) if abs(ls390[i] - want390[i]) > 0.01]
        chk(not rises390 and not strays390,
            "fall_survives    the fall still deepens at 390px%s"
            % ("  :: " + "; ".join(rises390 + strays390) if (rises390 or strays390)
               else "  :: %s" % " > ".join("%.3f" % x for x in ls390)))

        # ---------- ratios_recomputed
        # Elements move at this width, so the ground under them changes. Nothing printed
        # may be carried over from the wide layout without being true here too.
        claims390 = mp.evaluate("""() => [...document.querySelectorAll('[data-fg][data-bg]')]
            .map(e => [e.dataset.fg, e.dataset.bg, e.textContent.trim()])""")
        els390 = mp.evaluate(TEXT_PROBE)
        bad390 = []
        for fg, bg, shown in claims390:
            try:
                printed = float(shown.split(":")[0])
            except ValueError:
                bad390.append("%r is not a ratio" % shown); continue
            if abs(printed - contrast(fg, bg)) > 0.005:
                bad390.append("%s on %s printed %.2f, computed %.2f"
                              % (fg, bg, printed, contrast(fg, bg)))
        n390 = 0
        for e in els390:
            fg = css_colour(e["color"], {})
            if fg is None:
                continue
            bg = css_colour(e["bg"], {}) if e["bg"] else _fall(e["t"])
            pt = e["size"] * 72.0 / 96.0
            large = pt >= 18 or (pt >= 14 and e["weight"] in ("700", "bold", "800", "900"))
            floor = 3.0 if large else 4.5
            r = contrast(fg, bg)
            n390 += 1
            if r < floor - 0.005:
                bad390.append("%s %r at t=%.3f: %s on %s is %.2f:1, needs %.1f:1"
                              % (e["tag"], e["text"], e["t"], fg, bg, r, floor))
        chk(not bad390,
            "ratios_recomputed every ratio and every element holds at 390px%s"
            % ("  :: " + "; ".join(bad390[:5]) if bad390
               else "  :: %d ratios and %d elements rechecked" % (len(claims390), n390)))
        # ---------- touch_targets
        # The Global Constraint names no viewport, and the one link measured 42px tall
        # at the default desktop width while this check ran only at 390.
        TARGETS = """() => [...document.querySelectorAll('a,button,[role=button],input,select')]
            .map(e => { const b = e.getBoundingClientRect();
                        return {t: e.tagName, w: Math.round(b.width), h: Math.round(b.height),
                                s: (e.textContent||'').trim().slice(0,18)}; })
            .filter(x => x.h < 44 || x.w < 44)"""
        small = []
        for width in (1440, 1024, 860, 390, 320):
            tp = br.new_page(viewport={"width": width, "height": 900})
            tp.goto(DOC.resolve().as_uri())
            tp.wait_for_timeout(350)
            small += [(width, x) for x in tp.evaluate(TARGETS)]
            tp.close()
        chk(not small,
            "touch_targets    every interactive target is at least 44 by 44px%s"
            % ("  :: " + "; ".join("at %dpx, %s %r is %dx%d"
                                   % (w, x["t"], x["s"], x["w"], x["h"])
                                   for w, x in small[:3]) if small
               else "  :: clear at 1440, 1024, 860, 390 and 320"))

        mp.close()

        # ================= print =================
        pp = br.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=1)
        pp.goto(DOC.resolve().as_uri())
        pp.emulate_media(media="print")
        pp.wait_for_timeout(700)

        # ---------- print_ground
        # Asserting that the background-image string merely contains "gradient" passes
        # on a white gradient. Every stop the print stylesheet paints has to be a colour
        # from the ramp, and no painted surface may be lighter than the void.
        grounds = pp.evaluate("""() => {
            const cs = n => getComputedStyle(document.querySelector(n));
            return {pages: [...document.querySelectorAll('.page')]
                        .map(p => getComputedStyle(p).backgroundImage),
                    pageColor: cs('.page').backgroundColor,
                    body: cs('body').backgroundColor,
                    ledger: cs('.ledger').backgroundColor,
                    measure: cs('.measure').backgroundColor};
        }""")
        bad_print = []
        printed_pages = grounds["pages"] or []
        if not printed_pages:
            bad_print.append("no page paints a ground under print")
        n_pp = len(printed_pages)
        for i, img in enumerate(printed_pages):
            img = img or ""
            if "gradient" not in img:
                bad_print.append("page %02d paints no fall under print: %r" % (i + 1, img))
                continue
            # Each page carries its own slice, so "is it a stage colour" is the wrong
            # question. The right one is whether it is the value the fall reaches at
            # this page's own boundaries.
            want = [_fall(i / float(n_pp)).upper(), _fall((i + 1) / float(n_pp)).upper()]
            got = []
            for st in re.findall(r"rgba?\(([^)]*)\)", img):
                parts = [p.strip() for p in re.split(r"[ ,]+", st) if p.strip()]
                try:
                    got.append("#%02X%02X%02X"
                               % tuple(int(float(parts[j])) for j in range(3)))
                except (ValueError, IndexError):
                    continue
            if got[:2] != want:
                bad_print.append("page %02d prints %s, the fall runs %s there"
                                 % (i + 1, " to ".join(got[:2]) or "nothing",
                                    " to ".join(want)))
        void_l = oklch(get(tokens, "color.ground.value"))[0]
        for name in ("pageColor", "body", "ledger", "measure"):
            c = css_colour(grounds[name] or "", {})
            if c is not None and oklch(c)[0] > void_l + 0.002:
                bad_print.append("%s under print is %s, lighter than the void" % (name, c))
        chk(not bad_print,
            "print_ground     the fall survives print emulation%s"
            % ("  :: " + "; ".join(sorted(set(bad_print))[:4]) if bad_print
               else "  :: %d pages, each printing the slice of the fall it carries"
                    % n_pp))

        # block texts taken from the DOM rather than scraped out of the HTML with a
        # regex that mis-nests across section boundaries; no_cut_row reads these.
        global PRINT_BLOCKS
        PRINT_BLOCKS = pp.evaluate("""() => [...document.querySelectorAll('.lrow, .role, .tstep')]
            .map(e => ({cls: e.className.split(' ')[0],
                        text: (e.innerText || '').replace(/\\s+/g, ' ').trim()}))
            .filter(b => b.text.length > 12)""")

        pp.close()

        br.close()
        try:
            tmp.unlink()
        except OSError:
            pass


def pdf_checks(chk, tokens):
    """The printed artifact, not the page that produced it."""
    pdf = ROOT / "brand" / "guide-sources" / "2026-10-07-afterglow-guidelines.pdf"
    if not pdf.exists():
        for n in ("pdf_edges", "no_cut_row", "pdf_current", "pdf_banding"):
            chk(False, "%-16s needs the rendered PDF  :: %s does not exist yet"
                % (n, pdf.name))
        return
    try:
        import fitz
    except ImportError:
        chk(False, "pdf_edges        the PDF's corners are the ground, not white margin"
                   "  :: PyMuPDF is not installed, so this cannot be verified")
        return
    # A check that reads a committed artifact proves nothing about the document as it
    # stands now. Both print checks were validating a PDF older than the HTML.
    stale = pdf.stat().st_mtime < DOC.stat().st_mtime - 1
    chk(not stale,
        "pdf_current      the PDF is newer than the document it renders%s"
        % ("  :: the PDF predates the HTML; re-run tools/render.py" if stale
           else "  :: rendered after the last change"))

    doc = fitz.open(str(pdf))
    white = []
    sampled = 0
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=36)
        w, h = pix.width, pix.height
        # The top corners of page 1 are the void slug, not the fall, so corners alone
        # proved less than the pass line claimed. The mid-height edges are always ground.
        for name, (x, y) in (("top left", (2, 2)), ("top right", (w - 3, 2)),
                             ("bottom left", (2, h - 3)), ("bottom right", (w - 3, h - 3)),
                             ("left edge", (2, h // 2)), ("right edge", (w - 3, h // 2))):
            r, g, b = pix.pixel(x, y)[:3]
            sampled += 1
            # a Letter margin prints white; the fall never reaches L 0.9
            if oklch("#%02X%02X%02X" % (r, g, b))[0] > 0.9:
                white.append("page %d %s is #%02X%02X%02X" % (i + 1, name, r, g, b))
    pages = [" ".join(doc[i].get_text().split()) for i in range(doc.page_count)]
    doc.close()
    chk(not white,
        "pdf_edges        every page edge carries the ground, not white margin%s"
        % ("  :: " + "; ".join(white[:4]) if white
           else "  :: %d points across %d pages, corners and mid-height edges"
                % (sampled, sampled // 6)))

    # ---------- pdf_banding
    # The screen answer rested on Chromium's gradient dithering. The PDF has no dither:
    # the fall is emitted as flat vector fills, one per quantisation step.
    #
    # The step between adjacent fills is therefore always about one sRGB unit whatever
    # the ramp does, so measuring it proves nothing. What varies, and what an eye would
    # actually catch, is how TALL each flat is: a shallower ramp or a longer document
    # stretches every band until it reads as a stripe. That is what this holds.
    ramp_pdf = [get(tokens, "color.stages.%d.value" % n) for n in (1, 2, 3, 4)]
    LOCUS = []
    for k in range(2001):
        t = k / 2000.0
        stops = list(zip((0.0, 1 / 3.0, 2 / 3.0, 1.0), ramp_pdf))
        for i in range(3):
            (p0, c0), (p1, c1) = stops[i], stops[i + 1]
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0)
                a_, b_ = rgb(c0), rgb(c1)
                LOCUS.append(tuple(a_[j] + (b_[j] - a_[j]) * f for j in range(3)))
                break

    def on_fall(c):
        return min(max(abs(c[j] - q[j]) for j in range(3)) for q in LOCUS) <= 1.5

    # A flat taller than this is wide enough on a Letter sheet to read as a stripe
    # rather than as a gradient. Measured at 150 dpi.
    MAX_BAND_IN = 1.0
    doc2 = fitz.open(str(pdf))
    n_pages = doc2.page_count
    wide, measured, longest = [], 0, 0.0
    for i in range(n_pages):
        pix = doc2[i].get_pixmap(dpi=150)
        # Sampled inside the gutter, where the fall is and no glyph is. A column
        # through the text column is broken up by every line it crosses, which turns a
        # page-high flat into a stack of short ones and hides exactly what this looks
        # for. More than one column, because one unlucky column is not a measurement.
        for frac in (0.015, 0.030):
            x = int(pix.width * frac)
            col = [pix.pixel(x, y)[:3] for y in range(pix.height)]
            runs, prev, st = [], None, 0
            for k, c in enumerate(col):
                if c != prev:
                    if prev is not None:
                        runs.append((st, k - st, prev))
                    prev, st = c, k
            runs.append((st, len(col) - st, prev))
            for y, length, c in runs:
                if not on_fall(c):
                    continue
                measured += 1
                inches = length / 150.0
                longest = max(longest, inches)
                if inches > MAX_BAND_IN:
                    wide.append("page %d: a flat band of %.2f in at #%02X%02X%02X"
                                % (i + 1, inches, c[0], c[1], c[2]))
    doc2.close()
    chk(measured and not wide,
        "pdf_banding      no flat band in the printed fall exceeds %.2f in%s"
        % (MAX_BAND_IN,
           "  :: " + "; ".join(sorted(set(wide))[:3]) if wide
           else "  :: %d bands measured, longest %.2f in" % (measured, longest)))

    # ---------- no_cut_row
    # Text in the PDF is uppercased by text-transform, so matching the HTML's mixed
    # case silently found nothing and the check skipped every ledger row while
    # reporting that it had examined them.
    # Whitespace is not comparable between the two: the DOM runs adjacent elements
    # together ("Ground#A2544E") where the PDF separates them, and text-transform
    # uppercases one side only. Strip both to letters and digits.
    def norm(x):
        return re.sub(r"[^0-9A-Z]", "", x.upper())

    pages_n = [norm(p) for p in pages]
    split, unresolved = [], []
    for b in PRINT_BLOCKS:
        flat = norm(b["text"])
        if len(flat) < 24:
            continue
        head, tail_ = flat[:20], flat[-20:]
        hp = {i for i, pg_ in enumerate(pages_n) if head in pg_}
        tp = {i for i, pg_ in enumerate(pages_n) if tail_ in pg_}
        if not hp or not tp:
            unresolved.append("%s %r could not be located in the PDF"
                              % (b["cls"], b["text"][:26]))
            continue
        if not (hp & tp):
            split.append("%s %r starts on page %d and ends on page %d"
                         % (b["cls"], b["text"][:26], min(hp) + 1, min(tp) + 1))
    blocks = PRINT_BLOCKS
    split += unresolved
    chk(blocks and not split,
        "no_cut_row       no row, role or step is split across a sheet%s"
        % ("  :: " + "; ".join(split[:4]) if split
           else "  :: %d blocks checked against %d pages" % (len(blocks), len(pages))))


def main():
    tokens = json.loads(io.open(TOKENS, encoding="utf-8").read())

    # ---------- no_nulls
    nulls = []
    for branch in TOKEN_BRANCHES:
        sub = get(tokens, branch)
        if sub is MISSING:
            nulls.append(branch + " (branch absent)")
            continue
        for path, value in leaves(sub, branch):
            if any(part.startswith("_") for part in path.split(".")):
                continue
            if value is None:
                nulls.append(path)
    missing = [p for p in REQUIRED if get(tokens, p) is MISSING]
    for branch in REQUIRED_BRANCHES:
        sub = get(tokens, branch)
        real = []
        if isinstance(sub, dict):
            real = [k for k in sub if not k.startswith("_")]
        if not real:
            missing.append(branch + " (no value, only notes)")
    chk(
        not nulls and not missing,
        "no_nulls         every token value is set%s"
        % (
            ""
            if not nulls and not missing
            else "  :: null %s  :: missing %s" % (sorted(nulls), sorted(missing))
        ),
    )

    stages = [get(tokens, "color.stages.%d" % n) for n in (1, 2, 3, 4)]
    values = [s.get("value") if isinstance(s, dict) else None for s in stages]
    recorded = [s.get("oklch") if isinstance(s, dict) else None for s in stages]
    ramp_set = all(isinstance(v, str) and v.startswith("#") for v in values)

    # ---------- oklch_matches_hex
    if not ramp_set:
        chk(False, "oklch_matches  recorded OKLCH agrees with the hex  :: ramp not set")
    else:
        drift = []
        for i, (v, rec) in enumerate(zip(values, recorded), start=1):
            if not isinstance(rec, dict):
                drift.append("stage %d has no oklch object" % i)
                continue
            L, C, H = oklch(v)
            for key, got, want in (("l", rec.get("l"), L), ("c", rec.get("c"), C),
                                   ("h", rec.get("h"), H)):
                if not isinstance(got, (int, float)) or abs(got - want) > 0.005 * (
                        360.0 if key == "h" else 1.0):
                    drift.append("stage %d %s recorded %r, computed %.4f"
                                 % (i, key, got, want))
        chk(not drift,
            "oklch_matches    recorded OKLCH agrees with the hex%s"
            % ("" if not drift else "  :: " + "; ".join(drift)))

    # ---------- l_monotonic
    if not ramp_set:
        chk(False, "l_monotonic      lightness falls across the four stages  :: ramp not set")
    else:
        ls = [oklch(v)[0] for v in values]
        rises = ["stage %d (%.4f) is not below stage %d (%.4f)"
                 % (i + 2, ls[i + 1], i + 1, ls[i])
                 for i in range(3) if ls[i + 1] >= ls[i]]
        chk(not rises,
            "l_monotonic      lightness falls across the four stages, %s%s"
            % (" > ".join("%.3f" % x for x in ls),
               "" if not rises else "  :: " + "; ".join(rises)))

    # ---------- hue_one_way
    if not ramp_set:
        chk(False, "hue_one_way      hue rotates one way along the arc  :: ramp not set")
    else:
        hs = [oklch(v)[2] for v in values]
        deltas = [((hs[i + 1] - hs[i] + 180.0) % 360.0) - 180.0 for i in range(3)]
        signs = set(1 if d > 0 else (-1 if d < 0 else 0) for d in deltas)
        chk(len(signs) == 1 and 0 not in signs,
            "hue_one_way      hue rotates one way along the arc, %s, steps %s%s"
            % (" -> ".join("%.1f" % x for x in hs),
               " ".join("%+.1f" % d for d in deltas),
               "" if len(signs) == 1 and 0 not in signs else "  :: direction reverses"))

    # ---------- stage_roles
    if not ramp_set:
        chk(False, "stage_roles      stages 1 and 2 clear their contrast floors  :: ramp not set")
    else:
        ratios = [contrast(v, VOID) for v in values]
        misses = []
        if ratios[0] < 4.5:
            misses.append("stage 1 is %.2f:1 on void, needs 4.5:1 to be text" % ratios[0])
        if ratios[1] < 3.0:
            misses.append("stage 2 is %.2f:1 on void, needs 3:1 for large text" % ratios[1])
        chk(not misses,
            "stage_roles      on void: %s (3 and 4 recorded, unconstrained)%s"
            % (", ".join("s%d %.2f:1" % (i + 1, r) for i, r in enumerate(ratios)),
               "" if not misses else "  :: " + "; ".join(misses)))

    # ---------- stage_named
    name2 = stages[1].get("name") if isinstance(stages[1], dict) else None
    vocab = voice_vocabulary()
    drawn = bool(name2) and any(
        w in vocab for w in re.findall(r"[a-z']+", str(name2).lower()))
    chk(drawn,
        "stage_named      stage 2 is named from the Afterglow vocabulary%s"
        % ("" if drawn else "  :: name is %r" % (name2,)))

    # ---------- type_set
    typo = get(tokens, "typography")
    fams = {f: get(tokens, "typography.%s.family" % f) for f in ("display", "body")}
    unset = sorted(f for f, v in fams.items() if not isinstance(v, str) or not v.strip())
    chk(not unset,
        "type_set         both faces are chosen%s"
        % ("  :: " + ", ".join(fams.get(f) and f or f for f in unset) + " unset"
           if unset else "  :: display %(display)s, body %(body)s" % fams))

    # ---------- scale_measured
    scale = get(tokens, "typography.scale")
    if not isinstance(scale, dict):
        chk(False, "scale_measured   the scale is a measured ratio, not eyeballed  :: scale not set")
    else:
        ratio, base = scale.get("ratio"), scale.get("base")
        steps = scale.get("steps")
        problems = []
        if not isinstance(ratio, (int, float)) or ratio <= 1:
            problems.append("ratio is %r" % (ratio,))
        if not isinstance(base, (int, float)) or base <= 0:
            problems.append("base is %r" % (base,))
        if not isinstance(steps, dict) or not steps:
            problems.append("no named steps")
        if not problems:
            for name, value in sorted(steps.items()):
                if not isinstance(value, (int, float)):
                    problems.append("%s is %r" % (name, value)); continue
                # every step has to be base * ratio ** n for a whole n, or the scale
                # is a list of sizes someone liked rather than a scale
                n = math.log(value / base) / math.log(ratio)
                if abs(n - round(n)) > 0.02:
                    problems.append("%s=%g is base*ratio**%.3f, not a whole step"
                                    % (name, value, n))
        chk(not problems,
            "scale_measured   every step derives from ratio and base%s"
            % ("  :: " + "; ".join(problems) if problems
               else "  :: %g from %g, %d steps" % (ratio, base, len(steps))))

    # ---------- delivery_recorded
    routes = {}
    for f in ("display", "body"):
        v = get(tokens, "typography.%s.delivery" % f)
        routes[f] = "not set" if v is MISSING else v
    allowed = ("shopify_library", "self_hosted")
    wrong = ["%s is %r" % (f, v) for f, v in sorted(routes.items()) if v not in allowed]
    chk(not wrong,
        "delivery_recorded each face records how it ships%s"
        % ("  :: " + "; ".join(wrong) if wrong
           else "  :: display %(display)s, body %(body)s" % routes))

    # ---------- spacing_measured
    sp = get(tokens, "spacing")
    if not isinstance(sp, dict):
        chk(False, "spacing_measured every step is a whole multiple of the base  :: spacing not set")
    else:
        sbase, sscale = sp.get("base"), sp.get("scale")
        issues = []
        if not isinstance(sbase, (int, float)) or sbase <= 0:
            issues.append("base is %r" % (sbase,))
        elif not isinstance(sscale, dict) or not sscale:
            issues.append("no scale")
        else:
            for name, value in sorted(sscale.items()):
                if not isinstance(value, (int, float)):
                    issues.append("%s is %r" % (name, value)); continue
                # half steps are allowed, arbitrary numbers are not
                k = value / float(sbase)
                if abs(k * 2 - round(k * 2)) > 1e-6:
                    issues.append("%s=%g is base x %.3f, not a whole or half step" % (name, value, k))
        chk(not issues,
            "spacing_measured every step is a multiple of the base%s"
            % ("  :: " + "; ".join(issues) if issues
               else "  :: %g px base, %d steps" % (sbase, len(sscale))))

    # ---------- motion_no_overshoot
    # "Deepening, never snapping" is a Global Constraint with no other test. A curve
    # whose control points leave the unit square passes its destination and comes back,
    # which is exactly the bounce the brand rules out.
    ease = get(tokens, "motion.ease")
    m = re.match(r"\s*cubic-bezier\(([^)]*)\)\s*$", str(ease))
    if not m:
        chk(False, "motion_no_overshoot the easing curve never overshoots  :: ease is %r" % (ease,))
    else:
        try:
            pts = [float(x) for x in m.group(1).split(",")]
        except ValueError:
            pts = []
        if len(pts) != 4:
            chk(False, "motion_no_overshoot the easing curve never overshoots  :: cannot read %r" % (ease,))
        else:
            x1, y1, x2, y2 = pts
            out_of_square = [n for n, v in (("y1", y1), ("y2", y2)) if not 0.0 <= v <= 1.0]
            bad_x = [n for n, v in (("x1", x1), ("x2", x2)) if not 0.0 <= v <= 1.0]
            chk(not out_of_square and not bad_x,
                "motion_no_overshoot the easing curve settles, never passes its value%s"
                % ("  :: " + ", ".join(out_of_square + bad_x) + " outside 0..1"
                   if (out_of_square or bad_x) else "  :: %s" % ease))

    # ---------- neutrals_locked
    wrong = [
        "%s is %r, expected %r" % (p, get(tokens, p), want)
        for p, want in sorted(NEUTRALS.items())
        if get(tokens, p) != want
    ]
    chk(
        not wrong,
        "neutrals_locked  the six neutrals are unchanged%s"
        % ("" if not wrong else "  :: " + "; ".join(wrong)),
    )

    # ---------- no_forbidden
    strays = []
    for path, value in leaves(tokens):
        if path.startswith("color._forbidden"):
            continue
        if isinstance(value, str) and any(f.lower() in value.lower() for f in FORBIDDEN):
            strays.append(path)
    chk(
        not strays,
        "no_forbidden     no tracker accent outside _forbidden%s"
        % ("" if not strays else "  :: " + ", ".join(sorted(strays))),
    )

    # ---------- notes_intact
    dropped = [k for k in NOTE_KEYS if get(tokens, k) is MISSING]
    chk(
        not dropped,
        "notes_intact     explanatory keys survive the fill%s"
        % ("" if not dropped else "  :: dropped " + ", ".join(dropped)),
    )

    # ---------- no_week2
    identity = io.open(IDENTITY, encoding="utf-8").read()
    hits = identity.lower().count("week 2")
    chk(
        hits == 0,
        "no_week2         BRAND-IDENTITY.md has no Week 2 rows%s"
        % ("" if hits == 0 else "  :: %d occurrence(s)" % hits),
    )

    document_checks(chk, tokens)
    pdf_checks(chk, tokens)

    print("\n".join("  PASS  " + m for m in OK))
    if FAIL:
        print()
        print("\n".join("  FAIL  " + m for m in FAIL))
    print()
    print("  %d pass, %d fail" % (len(OK), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
