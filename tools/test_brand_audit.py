# -*- coding: utf-8 -*-
"""Regression tests for the audit harness itself.

Every case here is a defect the harness once passed. A check that cannot fail is
worse than no check, because it manufactures confidence; these make each one
prove it still bites.

Run: python3 tools/test_brand_audit.py
"""
import io
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = ROOT / "brand" / "guide-sources" / "2026-10-07-afterglow-guidelines.html"
PDF = ROOT / "brand" / "guide-sources" / "2026-10-07-afterglow-guidelines.pdf"
sys.path.insert(0, str(ROOT / "tools"))
import brand_audit as B

PASSED, FAILED = [], []


def audit():
    r = subprocess.run([sys.executable, "tools/brand_audit.py"], cwd=str(ROOT),
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def render(src=None):
    subprocess.run([sys.executable, "tools/render.py",
                    "brand/guide-sources/2026-10-07-afterglow-guidelines.html"],
                   cwd=str(ROOT), capture_output=True, text=True, check=True)


def case(name, mutate, expect_fail, rerender=False):
    """Apply a mutation, require the named check to go red, then restore."""
    doc_backup = DOC.read_text(encoding="utf-8")
    pdf_backup = PDF.read_bytes() if PDF.exists() else None
    try:
        new = mutate(doc_backup)
        assert new != doc_backup, "%s: the mutation changed nothing" % name
        io.open(DOC, "w", encoding="utf-8").write(new)
        if rerender:
            render()
        _, out = audit()
        if ("FAIL  " + expect_fail) in out:
            PASSED.append(name)
        else:
            line = next((l.strip() for l in out.splitlines() if expect_fail in l), "(absent)")
            FAILED.append("%s: %s stayed green -> %s" % (name, expect_fail, line))
    finally:
        io.open(DOC, "w", encoding="utf-8").write(doc_backup)
        if pdf_backup is not None:
            PDF.write_bytes(pdf_backup)


# ---------------------------------------------------------------- C3
def lie_about_the_ground(s):
    """Claim the ground at the crossover is a violet it is not, with arithmetic
    that is internally consistent. The document must not be able to print a
    colour it did not measure."""
    fake = "#5B3F8A"
    m = re.search(r'<dt>Ground</dt><dd>(#[0-9A-F]{6})</dd>', s)
    real = m.group(1)
    s = s.replace("<dt>Ground</dt><dd>%s</dd>" % real,
                  "<dt>Ground</dt><dd>%s</dd>" % fake, 1)
    s = s.replace('data-bg="%s">%.2f:1' % (real, B.contrast("#EEECEA", real)),
                  'data-bg="%s">%.2f:1' % (fake, B.contrast("#EEECEA", fake)), 1)
    return s


# ---------------------------------------------------------------- C2
def whiten_the_printed_page(s):
    """The fall is painted per page now, so whitening .doc would be a mutation the
    document no longer notices. This whitens what actually carries the ground."""
    return s.replace("  @media print{",
                     "  @media print{\n"
                     "    .page{background:linear-gradient(180deg,#FFFFFF,#F2F2F2)}\n"
                     "    .ledger{background:#FFFFFF}", 1)


# ---------------------------------------------------------------- C1
def split_a_ledger_row(s):
    """Force a row to straddle a sheet: drop the break guard, put the readings back
    into one column so they stack, and make one tall enough to cross a boundary."""
    s = s.replace(".lrow,.role,.tstep,.crossover{break-inside:avoid;page-break-inside:avoid}",
                  ".crossover{break-inside:avoid}", 1)
    # The row has to be tall IN TEXT. A tall empty box straddles a boundary without
    # any of its words doing so, and no_cut_row matches on words.
    return s.replace("  @media print{", "  @media print{\n"
                     "    .ledger{display:block;padding-top:300px}\n"
                     "    .lrow{display:block}\n"
                     "    .lrow dl{line-height:9}\n"
                     "    .lnote{display:block;line-height:9}", 1)


# ---------------------------------------------------------------- I2
def brighten_by_filter(s):
    return s.replace("  a:hover,a:focus-visible{",
                     "  a:hover{filter:brightness(2.2)}\n"
                     "  a:hover,a:focus-visible{", 1)


def brighten_by_border(s):
    return s.replace("  a:hover,a:focus-visible{",
                     "  a:hover{border-bottom:1px solid #FFFFFF}\n"
                     "  a:hover,a:focus-visible{", 1)


# ---------------------------------------------------------------- I7
def paint_a_dead_leader(s):
    return s.replace("    .lrow.anchored::before{display:none}",
                     "    .lrow.anchored::before{display:none}\n"
                     "    .lrow.anchored{border-left:2px solid #D8B260}", 1)


case("C3 a fabricated ground colour", lie_about_the_ground, "specimen_truth")
case("C2 a white printed page", whiten_the_printed_page, "print_ground")
case("C1 a ledger row split across sheets", split_a_ledger_row, "no_cut_row", rerender=True)
case("I2 brightening by filter", brighten_by_filter, "no_brightening")
case("I2 brightening by border-color", brighten_by_border, "no_brightening")


# ---------------------------------------------------------------- I1
def test_stale_pdf():
    """The print checks must not validate an artifact older than the document.
    The condition is set explicitly rather than by writing a file, because restoring
    the fixtures above leaves both mtimes inside the check's one-second tolerance."""
    import os
    doc_backup = DOC.read_text(encoding="utf-8")
    pdf_times = (PDF.stat().st_atime, PDF.stat().st_mtime)
    try:
        io.open(DOC, "a", encoding="utf-8").write("\n<!-- touched -->\n")
        os.utime(PDF, (pdf_times[0], DOC.stat().st_mtime - 30))
        _, out = audit()
        if "FAIL  pdf_current" in out or "FAIL  pdf_edges" in out:
            PASSED.append("I1 a stale PDF")
        else:
            FAILED.append("I1 a stale PDF: the print checks validated an artifact "
                          "older than the document")
    finally:
        io.open(DOC, "w", encoding="utf-8").write(doc_backup)
        os.utime(PDF, pdf_times)


test_stale_pdf()


# ---------------------------------------------------------------- I5
def test_touch_targets_at_every_width():
    from playwright.sync_api import sync_playwright
    small = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in (1440, 860, 390, 320):
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto(DOC.resolve().as_uri())
            pg.wait_for_timeout(400)
            small += [(w, x) for x in pg.evaluate(
                """() => [...document.querySelectorAll('a,button,[role=button]')]
                     .map(e => { const r = e.getBoundingClientRect();
                                 return [Math.round(r.width), Math.round(r.height)]; })
                     .filter(([w, h]) => w < 44 || h < 44)""")]
            pg.close()
        b.close()
    if small:
        FAILED.append("I5 touch targets: under 44px at %s"
                      % ", ".join("%dpx wide -> %s" % (w, x) for w, x in small[:4]))
    else:
        PASSED.append("I5 touch targets at 1440, 860, 390 and 320")


test_touch_targets_at_every_width()


# ---------------------------------------------------------------- I6
def test_body_weight_is_servable():
    """Space Grotesk ships from Shopify's library as static weights. A weight the
    library cannot serve will snap in the theme and stop matching the specimen."""
    import json
    tok = json.loads(io.open(ROOT / "brand/resources/design-tokens.json",
                             encoding="utf-8").read())
    html = DOC.read_text(encoding="utf-8")
    m = re.search(r"body\{[^}]*font-weight:(\d+)", html)
    weight = int(m.group(1)) if m else None
    recorded = tok["typography"]["body"].get("weight")
    problems = []
    if weight is None or weight % 100 != 0:
        problems.append("the document sets font-weight %s, which is not a static weight"
                        % weight)
    if recorded is None:
        problems.append("typography.body.weight is not recorded, so the build has "
                        "nothing to carry over")
    elif weight is not None and int(recorded) != weight:
        problems.append("the document sets %s, the token records %s" % (weight, recorded))
    if problems:
        FAILED.append("I6 body weight: " + "; ".join(problems))
    else:
        PASSED.append("I6 body weight is a static weight and is recorded")


test_body_weight_is_servable()

# ---------------------------------------------------------------- I8
def test_banding_is_falsifiable():
    """A near-flat ramp stretches every printed band. If pdf_banding cannot see that,
    it is measuring something that does not vary."""
    import json, subprocess
    tok = ROOT / "brand/resources/design-tokens.json"
    bt = tok.read_text(encoding="utf-8")
    bp = PDF.read_bytes()

    def run(*a):
        return subprocess.run([sys.executable] + list(a), cwd=str(ROOT),
                              capture_output=True, text=True)
    try:
        d = json.loads(bt)
        # Flatten the bottom of the ramp, not the top. Flattening the top moves the
        # crossover off 50 per cent, the generator refuses to build a twelve-page
        # document whose inversion is not on a turn, and a build that never ran would
        # be read as the check staying green. The bottom leaves the crossover alone.
        d["color"]["stages"]["4"]["value"] = "#8A3B52"
        d["color"]["stages"]["4"]["oklch"] = {"l": 0.4644, "c": 0.1093, "h": 5.4}
        io.open(tok, "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False))
        built = run("tools/build_guidelines.py")
        rendered = run("tools/render.py", "brand/guide-sources/2026-10-07-afterglow-guidelines.html")
        if built.returncode or rendered.returncode:
            FAILED.append("I8 the mutated document never built, so nothing was measured"
                          " -> %s" % (built.stderr or rendered.stderr).strip().splitlines()[-1:])
        else:
            out = run("tools/brand_audit.py").stdout
            if "FAIL  pdf_banding" in out:
                PASSED.append("I8 a near-flat ramp bands in print")
            else:
                FAILED.append("I8 pdf_banding stayed green on a near-flat ramp")
    finally:
        io.open(tok, "w", encoding="utf-8").write(bt)
        run("tools/build_guidelines.py")
        run("tools/render.py", "brand/guide-sources/2026-10-07-afterglow-guidelines.html")
        run("tools/render.py", "brand/guide-sources/2026-10-07-afterglow-guidelines.html")
        PDF.write_bytes(bp)


test_banding_is_falsifiable()


print("\n".join("  PASS  " + m for m in PASSED))
if FAILED:
    print()
    print("\n".join("  FAIL  " + m for m in FAILED))
print()
print("  %d pass, %d fail" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
