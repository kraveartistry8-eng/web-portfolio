# -*- coding: utf-8 -*-
"""Audit for brand/2026-10-09-afterglow-design-system.html.

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

DOC = ROOT / "brand/2026-10-09-afterglow-design-system.html"
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
                    border: cs.borderTopWidth,
                    foot: !!s.querySelector('.foot .pg'),
                    pg: (s.querySelector('.foot .pg') || {}).textContent};
        })""")
        bad = []
        for i, s in enumerate(sheets):
            if not s["foot"]:
                bad.append("sheet %s has no folio" % s["n"])
            elif (s["pg"] or "").strip() != s["n"]:
                bad.append("sheet %s prints folio %s" % (s["n"], s["pg"]))
            if s["border"] == "0px":
                bad.append("sheet %s has no edge" % s["n"])
            if i and s["top"] <= sheets[i - 1]["top"] + sheets[i - 1]["h"]:
                bad.append("sheet %s is not separated from the one before it" % s["n"])
        chk(sheets and not bad,
            "sheets_discrete  every sheet is bounded, separated and numbered%s"
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
        roles = pg.evaluate("""() => [...document.querySelectorAll('.role')].map(e => ({
            name: e.querySelector('.rname').childNodes[0].textContent.trim(),
            tag: e.querySelector('.rname em').textContent.trim(),
            rule: e.querySelector('.rrule').textContent.trim()}))""")
        rbad = []
        for st, got in zip(stages, roles):
            ratio = B.contrast(st["value"], void)
            want = ("Text, marks, rules" if ratio >= 4.5
                    else "Large text, fills" if ratio >= 3.0 else "Ground only")
            if got["tag"] != want:
                rbad.append("%s reads %.2f:1 and is tagged %r, not %r"
                            % (st["name"], ratio, got["tag"], want))
            if ("%.2f:1" % ratio) not in got["rule"]:
                rbad.append("%s role text does not carry its own ratio" % st["name"])
        chk(len(roles) == 4 and not rbad,
            "roles_match_numbers each role follows from the ratio beside it%s"
            % ("  :: " + "; ".join(rbad) if rbad else "  :: 4 roles, all derived"))

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
    return report()


def report():
    for m in OK:
        print("  PASS  %s" % m)
    for m in FAIL:
        print("  FAIL  %s" % m)
    print("\n  %d pass, %d fail" % (len(OK), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
