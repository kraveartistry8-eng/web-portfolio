# -*- coding: utf-8 -*-
"""Audit for brand/2026-10-09-afterglow-brand-guide.html.

Deliberately small. The old guideline document needed thirty-odd checks because its
ground was a function of scroll position; this one is flat, so almost nothing can be
wrong in a way the eye cannot see. What the eye cannot check is whether a printed
number still matches the token it came from, which is what most of this holds.
"""
import io, json, pathlib, re, sys, importlib.util

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("ba", ROOT / "tools" / "brand_audit.py")
B = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(B)
except SystemExit:
    pass

DOC = ROOT / "brand/2026-10-09-afterglow-brand-guide.html"
PDF = DOC.with_suffix(".pdf")
T = json.loads(io.open(ROOT / "brand/resources/design-tokens.json", encoding="utf-8").read())
OK, FAIL = [], []


def chk(cond, msg):
    (OK if cond else FAIL).append(msg)


def main():
    from playwright.sync_api import sync_playwright
    C = T["color"]
    void = C["ground"]["value"]
    stages = [C["stages"][str(n)] for n in (1, 2, 3, 4)]

    if not DOC.exists():
        chk(False, "document         %s does not exist" % DOC.name)
        return report()

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(DOC.resolve().as_uri())
        pg.wait_for_timeout(1200)

        # ---------- sheets_discrete
        sheets = pg.evaluate("""() => [...document.querySelectorAll('.sheet')].map(s => {
            const r = s.getBoundingClientRect(), cs = getComputedStyle(s);
            return {n: s.dataset.sheet, h: Math.round(r.height),
                    top: Math.round(r.top + window.scrollY),
                    bg: cs.backgroundImage, stage: !!s.querySelector('.stagehead'),
                    bgc: cs.backgroundColor,
                    foot: !!s.querySelector('.foot .pg'),
                    pg: (s.querySelector('.foot .pg') || {}).textContent};
        })""")
        bad = []
        for i, s in enumerate(sheets):
            if not s["foot"]:
                bad.append("sheet %s has no folio" % s["n"])
            elif (s["pg"] or "").strip() != s["n"]:
                bad.append("sheet %s prints folio %s" % (s["n"], s["pg"]))
            if s["stage"]:
                if "gradient" in (s["bg"] or "") or s["bgc"] == "rgba(0, 0, 0, 0)":
                    bad.append("stage sheet %s is not a flat field" % s["n"])
            elif "gradient" not in (s["bg"] or ""):
                bad.append("sheet %s carries no slice of the fall" % s["n"])
            if i and abs(s["top"] - (sheets[i - 1]["top"] + sheets[i - 1]["h"])) > 1:
                bad.append("sheet %s does not meet the one before it" % s["n"])
        chk(sheets and not bad,
            "sheets_fall      every sheet is numbered and carries its slice%s"
            % ("  :: " + "; ".join(bad) if bad else "  :: %d sheets" % len(sheets)))

        # ---------- ratios_true
        # Every printed ratio carries the pair it was computed from, and both colours
        # must be tokens. An internally consistent invention would otherwise pass.
        claims = pg.evaluate("""() => [...document.querySelectorAll('[data-fg][data-bg]')]
            .map(e => ({fg: e.dataset.fg, bg: e.dataset.bg,
                        shown: e.textContent.trim()}))""")
        palette = {v.upper() for v in
                   [C[k]["value"] for k in ("ground", "surface-deep", "surface",
                                            "text", "muted")]
                   + [s["value"] for s in stages] + ["#A8832F"]}
        wrong = []
        for c in claims:
            try:
                printed = float(c["shown"].split(":")[0])
            except ValueError:
                wrong.append("%r is not a ratio" % c["shown"])
                continue
            real = B.contrast(c["fg"], c["bg"])
            if abs(printed - real) > 0.005:
                wrong.append("%s on %s printed %.2f, computed %.2f"
                             % (c["fg"], c["bg"], printed, real))
            for col in (c["fg"], c["bg"]):
                if col.upper() not in palette:
                    wrong.append("%s is not a token this system defines" % col)
        chk(claims and not wrong,
            "ratios_true      every printed ratio recomputes from its own pair%s"
            % ("  :: " + "; ".join(sorted(set(wrong))[:3]) if wrong
               else "  :: %d ratios against a %d colour palette"
                    % (len(claims), len(palette))))

        # ---------- values_from_tokens
        text = pg.inner_text("body")
        missing = [v for v in
                   [s["value"] for s in stages]
                   + [C[k]["value"] for k in ("ground", "surface-deep", "surface",
                                              "text", "muted")]
                   if v.upper() not in text.upper()]
        sizes = [k for k, v in T["typography"]["scale"]["steps"].items()
                 if ("%g px" % v) not in text]
        spaces = [k for k, v in T["spacing"]["scale"].items()
                  if ("%d px" % v) not in text]
        gaps = (["colour %s" % m for m in missing] + ["type step %s" % k for k in sizes]
                + ["space step %s" % k for k in spaces])
        chk(not gaps,
            "values_from_tokens every token value appears in the document%s"
            % ("  :: missing " + ", ".join(gaps[:5]) if gaps
               else "  :: 9 colours, 8 type steps, 8 space steps"))

        # ---------- roles_match_numbers
        # The role beside a swatch is the one place a sentence can contradict the
        # measurement printed next to it. It is derived, so this proves it stayed so.
        roles = pg.evaluate("""() => ({
            tags: [...document.querySelectorAll('.tbl td.role')].map(e => e.textContent.trim()),
            rules: [...document.querySelectorAll('.rr p')].map(e => e.textContent.trim())})""")
        rbad = []
        for st, tag, rule in zip(stages, roles["tags"], roles["rules"]):
            ratio = B.contrast(st["value"], void)
            want = ("Text, marks, rules" if ratio >= 4.5
                    else "Large text, fills" if ratio >= 3.0 else "Ground only")
            if tag != want:
                rbad.append("%s reads %.2f:1 and is tagged %r, not %r"
                            % (st["name"], ratio, tag, want))
            if ("%.2f:1" % ratio) not in rule:
                rbad.append("%s role text does not carry its own ratio" % st["name"])
        chk(len(roles["tags"]) == 4 and len(roles["rules"]) == 4 and not rbad,
            "roles_match_numbers each role follows from the ratio beside it%s"
            % ("  :: " + "; ".join(rbad) if rbad
               else "  :: 4 roles, all derived"))

        # ---------- no_brightening
        css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>",
                                   io.open(DOC, encoding="utf-8").read(), re.S))
        rules = B.parse_rules(css)
        variables = {k: v for sel, d in rules if sel.strip().endswith(":root")
                     for k, v in d.items() if k.startswith("--")}
        lifts = []
        for sel, decls in rules:
            if not re.search(r":(hover|focus-visible|focus|active)", sel):
                continue
            base = re.sub(r":(hover|focus-visible|focus|active)", "", sel)
            resting = next((d for s2, d in rules if s2.strip() == base.strip()), {})
            for prop, val in decls.items():
                if prop not in ("color", "background", "background-color"):
                    continue
                a = B.css_colour(resting.get(prop, ""), variables)
                c2 = B.css_colour(val, variables)
                if a and c2 and B.oklch(c2)[0] > B.oklch(a)[0] + 0.002:
                    lifts.append("%s lifts %s from L %.3f to L %.3f"
                                 % (sel, prop, B.oklch(a)[0], B.oklch(c2)[0]))
        chk(not lifts,
            "no_brightening   no state in the document lightens%s"
            % ("  :: " + "; ".join(lifts) if lifts else "  :: states checked against rest"))

        # ---------- no_h_scroll
        widths = []
        for w in (1440, 1024, 900, 390, 320):
            pg.set_viewport_size({"width": w, "height": 900})
            pg.wait_for_timeout(260)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            if sw > w + 1:
                widths.append("%dpx scrolls to %dpx" % (w, sw))
        chk(not widths,
            "no_h_scroll      no horizontal scroll at any width%s"
            % ("  :: " + "; ".join(widths) if widths
               else "  :: 1440, 1024, 900, 390 and 320"))

        chk(not errors, "no_console_errors the document loads clean%s"
            % ("  :: " + "; ".join(errors[:2]) if errors else "  :: no page errors"))
        b.close()

    # ---------- pdf_sheets
    if not PDF.exists():
        chk(False, "pdf_sheets       %s does not exist; run tools/render.py" % PDF.name)
    else:
        import fitz
        d = fitz.open(str(PDF))
        n, stale = d.page_count, PDF.stat().st_mtime < DOC.stat().st_mtime
        d.close()
        chk(n == len(sheets) and not stale,
            "pdf_sheets       one sheet of paper per sheet of the document%s"
            % ("  :: %d sheets against %d in the document%s"
               % (n, len(sheets), ", and the PDF is stale" if stale else "")
               if (n != len(sheets) or stale) else "  :: %d sheets, current" % n))
    return None


def report():
    for m in OK:
        print("  PASS  %s" % m)
    for m in FAIL:
        print("  FAIL  %s" % m)
    print("\n  %d pass, %d fail" % (len(OK), len(FAIL)))
    return 1 if FAIL else 0


def extra_checks():
    """Checks this document needs that the flat one did not."""
    from playwright.sync_api import sync_playwright
    C = T["color"]
    stages = [C["stages"][str(n)] for n in (1, 2, 3, 4)]
    ramp = [s["value"] for s in stages]
    stops = list(zip((0.0, 1 / 3.0, 2 / 3.0, 1.0), ramp))

    def rgbt(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

    def fall(t):
        t = max(0.0, min(1.0, t))
        for i in range(3):
            (p0, c0), (p1, c1) = stops[i], stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                a, b = rgbt(c0), rgbt(c1)
                return "#%02X%02X%02X" % tuple(int(round(a[j] + (b[j] - a[j]) * f))
                                               for j in range(3))
        return ramp[-1]

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(DOC.resolve().as_uri())
        pg.wait_for_timeout(1100)

        rows = pg.evaluate("""() => [...document.querySelectorAll('.sheet')].map(s => ({
            n: s.dataset.sheet, tone: s.classList.contains('dark') ? 'dark' : 'light',
            bg: getComputedStyle(s).backgroundImage,
            stage: !!s.querySelector('.stagehead'),
            bgc: getComputedStyle(s).backgroundColor}))""")
        n = len(rows)

        # ---------- fall_joins: sheet k ends on the value sheet k+1 opens on
        def stops_of(img):
            out = []
            for st in re.findall(r"rgba?\(([^)]*)\)", img or ""):
                parts = [x.strip() for x in re.split(r"[ ,]+", st) if x.strip()]
                try:
                    out.append("#%02X%02X%02X"
                               % tuple(int(float(parts[i])) for i in range(3)))
                except (ValueError, IndexError):
                    pass
            return out
        def hex_of(rgb):
            m = re.findall(r"\d+", rgb or "")
            return "#%02X%02X%02X" % tuple(int(x) for x in m[:3]) if len(m) >= 3 else ""
        seams, wrong = [], []
        # A stage sheet stands on its own stage colour, exactly and flat. The fall runs
        # through every other sheet and resumes at its own position after the four.
        stage_rows = [r_ for r_ in rows if r_["stage"]]
        for r_, st in zip(stage_rows, stages):
            if hex_of(r_["bgc"]) != st["value"].upper() or "gradient" in (r_["bg"] or ""):
                wrong.append("stage sheet %s stands on %s, not %s (%s)"
                             % (r_["n"], hex_of(r_["bgc"]) or r_["bg"], st["value"],
                                st["name"]))
        if len(stage_rows) != len(stages):
            wrong.append("%d stage sheets against %d stages" % (len(stage_rows), len(stages)))
        for i, r_ in enumerate(rows):
            if r_["stage"]:
                continue
            got = stops_of(r_["bg"])
            want = [fall(i / float(n)).upper(), fall((i + 1) / float(n)).upper()]
            if [g.upper() for g in got[:1]] != want[:1] or \
               [g.upper() for g in got[-1:]] != want[-1:]:
                wrong.append("sheet %s runs %s, the fall runs %s there"
                             % (r_["n"], " to ".join(got[:2]) or "nothing", " to ".join(want)))
            if i and not rows[i - 1]["stage"]:
                prev = stops_of(rows[i - 1]["bg"])
                if prev and got and prev[-1].upper() != got[0].upper():
                    seams.append("sheet %s opens on %s, sheet %s closed on %s"
                                 % (r_["n"], got[0], rows[i - 1]["n"], prev[-1]))
        chk(not wrong and not seams,
            "fall_joins       the deck is one fall cut into sheets%s"
            % ("  :: " + "; ".join((wrong + seams)[:3]) if (wrong or seams)
               else "  :: %d sheets, %d seams, all exact; %d stage sheets on their own stage"
               % (n, sum(1 for i, q in enumerate(rows) if i and not q["stage"]
                         and not rows[i - 1]["stage"]), len(stage_rows))))

        # ---------- ink_measured: the text colour on a sheet is the better of the two
        ibad = []
        for i, r_ in enumerate(rows):
            mid = (stages[sum(1 for q in rows[:i] if q["stage"])]["value"] if r_["stage"]
                   else fall((i + 0.5) / float(n)))
            want = "dark" if B.contrast(C["ground"]["value"], mid) >= \
                             B.contrast(C["text"]["value"], mid) else "light"
            if r_["tone"] != want:
                ibad.append("sheet %s is set %s on %s, where %s reads higher"
                            % (r_["n"], r_["tone"], mid, want))
        chk(not ibad,
            "ink_measured     every sheet uses the ink its own ground reads best%s"
            % ("  :: " + "; ".join(ibad[:3]) if ibad else "  :: %d sheets" % n))

        # ---------- readings_on_void: nothing is read off a mid-ramp colour
        stray = pg.evaluate("""() => {
            const out = [];
            document.querySelectorAll('.tbl, .srow dl, .rules').forEach(e => {
                if (!e.closest('.panel')) {
                    out.push((e.closest('.sheet') || {dataset:{}}).dataset.sheet || '?');
                }
            });
            return out;
        }""")
        chk(not stray,
            "readings_on_void every table and list sits in a void panel%s"
            % ("  :: sheets " + ", ".join(sorted(set(stray))) if stray
               else "  :: no reading sits on the fall"))

        # ---------- no_event_rules: the launch art direction does not bind the brand
        text = pg.inner_text("body").lower()
        banned = [w for w in ("four rooms", "until the end", "without a logo",
                              "no logo in sight", "doors at", "brooklyn", "walk through it")
                  if w in text]
        chk(not banned,
            "no_event_rules   no launch-night art direction is stated as a brand rule%s"
            % ("  :: found " + ", ".join(banned) if banned
               else "  :: medium-agnostic throughout"))

        # ---------- print_values: a print medium is actually specified
        need = ["cmyk", "pantone", "mm", "pt", "stock", "uncoated"]
        missing = [w for w in need if w not in text]
        chk(not missing,
            "print_values     the guide specifies a print medium%s"
            % ("  :: missing " + ", ".join(missing) if missing
               else "  :: CMYK, Pantone slot, millimetres, points, stock"))
        b.close()


if __name__ == "__main__":
    main()
    extra_checks()
    sys.exit(report())
