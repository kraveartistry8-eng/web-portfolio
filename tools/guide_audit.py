# -*- coding: utf-8 -*-
"""Audit for brand/guide-sources/2026-10-09-afterglow-brand-guide.html.

Deliberately small. The old guideline document needed thirty-odd checks because its
ground was a function of scroll position; this one is flat, so almost nothing can be
wrong in a way the eye cannot see. What the eye cannot check is whether a printed
number still matches the token it came from, which is what most of this holds.

Photography is the exception, and it is the part the eye is worst placed to audit: an
image either clears the lightness ceiling or it does not, and a slot is either 5:4 or a
few percent off, and nobody sees four percent. So the imagery checks read the same
manifest the build read and measure the same document and the same PDF the reader gets.
A check that cannot fail is worse than none, because it manufactures confidence; each of
these has a test that breaks the document in exactly the way it guards against.
"""
import io, json, os, pathlib, re, sys, importlib.util

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("ba", ROOT / "tools" / "brand_audit.py")
B = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(B)
except SystemExit:
    pass

# The three inputs can be pointed elsewhere so the tests can audit a mutated copy of the
# document and prove each check fails when it should; left alone, this audits the real files.
DOC = pathlib.Path(os.environ.get("GUIDE_AUDIT_DOC")
                   or ROOT / "brand/guide-sources/2026-10-09-afterglow-brand-guide.html")
PDF = pathlib.Path(os.environ.get("GUIDE_AUDIT_PDF") or DOC.with_suffix(".pdf"))
MANIFEST = pathlib.Path(os.environ.get("GUIDE_AUDIT_MANIFEST")
                        or ROOT / "brand/resources/imagery-manifest.json")
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
        imagery_checks(pg, rows)
        b.close()


# The ratio every slot holds, as the guide states it. The document carries it as --slot;
# the audit asserts the two agree rather than trusting either alone.
SLOT = 5 / 4.0
# WCAG's floors for text and for large text, the same pair the guide's own contrast sheet
# prints. They are a standard, not a token, so they are named once here.
FLOOR_BODY, FLOOR_LARGE = 4.5, 3.0


def _hex_of(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb[:3])


def _over(top, base):
    """top is [r,g,b] or [r,g,b,a] laid over the opaque rgb base."""
    a = top[3] if len(top) > 3 else 1.0
    return [top[i] * a + base[i] * (1 - a) for i in range(3)]


def _page_clips(page):
    """The visible slots on a printed page: every clip rectangle that an image fills.
    Chromium prints an image larger than its slot and clips it, so the image's own box
    says nothing about the crop; the clip is the slot. Full-sheet clips are the sheet."""
    pw, ph = page.rect.width, page.rect.height
    imgs = [b[1] for b in page.get_bboxlog() if "image" in b[0]]
    seen = []
    for d in page.get_drawings(extended=True):
        if d["type"] != "clip":
            continue
        r = d["scissor"]
        if r.width >= pw - 1 or r.height < 10 or r.height >= ph - 40:
            continue
        if any(i[0] <= r.x0 + 1 and i[1] <= r.y0 + 1 and i[2] >= r.x1 - 1
               and i[3] >= r.y1 - 1 for i in imgs):
            box = tuple(round(v, 2) for v in r)
            if box not in seen:
                seen.append(box)
    return sorted(seen, key=lambda r: (round(r[1]), r[0]))


def read_contrast(pg, all_sheets=False):
    """Every line of text on the sheets in scope, with the ratio it reads at against the ground
    it sits on: the panel it is in, the flat stage colour, or the worse end of the fall's slice.
    Scope is the sheets that carry imagery, or every sheet for a full survey."""
    void = T["color"]["ground"]["value"]
    base0 = [int(void[i:i + 2], 16) for i in (1, 3, 5)]  # an unpainted element sits on the void
    texts = pg.evaluate(r"""(all) => {
        const num = s => (s.match(/[\d.]+/g) || []).map(Number);
        const out = [];
        document.querySelectorAll('.sheet').forEach(sh => {
            const sec = (sh.querySelector('.foot span:nth-child(2)') || {}).textContent;
            if (!all && !(sec === 'Imagery' || sh.querySelector('.imgs, .misuse-tile, .appimg'))) return;
            sh.querySelectorAll('*').forEach(e => {
                if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
                const cs = getComputedStyle(e);
                if (cs.display === 'none' || cs.visibility === 'hidden') return;
                if (!e.getBoundingClientRect().width) return;
                const layers = []; let grad = null, node = e;
                while (node && node !== document.documentElement) {
                    const c = getComputedStyle(node), b = num(c.backgroundColor);
                    if (node.classList.contains('sheet') &&
                        c.backgroundImage.includes('gradient')) { grad = c.backgroundImage; break; }
                    if (b.length >= 3 && (b.length < 4 || b[3] > 0)) {
                        layers.push(b); if (b.length < 4 || b[3] >= 1) break;
                    }
                    node = node.parentElement;
                }
                out.push({n: sh.dataset.sheet, what: (e.className || e.tagName),
                          text: e.textContent.trim().slice(0, 24), fg: num(cs.color),
                          layers, grad, size: parseFloat(cs.fontSize),
                          weight: parseInt(cs.fontWeight)});
            });
        });
        return out;
    }""", all_sheets)
    rows = []
    for t_ in texts:
        ends = re.findall(r"rgba?\(([^)]*)\)", t_["grad"] or "")
        if t_["grad"]:
            bases = [[float(x) for x in re.split(r"[ ,]+", g.strip()) if x][:3]
                     for g in (ends[0], ends[-1])]
        else:
            bases = [base0]
        for base in bases:
            for layer in reversed(t_["layers"]):
                base = _over(layer, base)
            ink = _over(t_["fg"], base)
            large = t_["size"] >= 24 or (t_["size"] >= 18.66 and t_["weight"] >= 700)
            rows.append({"n": t_["n"], "el": t_["what"], "text": t_["text"],
                         "got": B.contrast(_hex_of(ink), _hex_of(base)), "on": _hex_of(base),
                         "floor": FLOOR_LARGE if large else FLOOR_BODY})
    return len(texts), rows


def imagery_checks(pg, rows):
    """The six checks the photography section needs. They read the manifest the build
    read, the document at four widths, and the PDF the reader is handed."""
    import fitz
    C = T["color"]
    stage_vals = [C["stages"][str(n)]["value"] for n in (1, 2, 3, 4)]
    man = json.loads(io.open(MANIFEST, encoding="utf-8").read())
    css = io.open(DOC, encoding="utf-8").read()
    n_sheets = len(rows)
    stage_idx = [i for i, r_ in enumerate(rows) if r_["stage"]]

    pdf, pdf_why = None, ""
    if not PDF.exists():
        pdf_why = "%s does not exist; run tools/render.py" % PDF.name
    else:
        pdf = fitz.open(str(PDF))
        if pdf.page_count != n_sheets:
            pdf_why = ("the PDF has %d pages against %d sheets; it is stale, run "
                       "tools/render.py" % (pdf.page_count, n_sheets))
            pdf = None
    sheet_pt = re.search(r"@media print\s*\{\s*:root\s*\{[^}]*--sheet-h:\s*([\d.]+)in", css)
    sheet_pt = float(sheet_pt.group(1)) * 72 if sheet_pt else None

    # ---------- image_never_brightens
    # The ceiling is the first stage's lightness. Lightness is read from the manifest, which
    # measured the poster frame of a video and the file of a still, so the build and the
    # audit cannot disagree about what was measured. An image the manifest has not measured
    # fails: it is exactly how a bright reference would get in.
    ceiling = B.oklch(stage_vals[0])[0]  # unrounded; only the message rounds it
    measured = {}
    for refs in man["stages"].values():
        for r_ in refs:
            measured[r_["file"]] = r_["l_p75"]
            if r_.get("poster"):
                measured[r_["poster"]] = r_["l_p75"]
    placed = pg.evaluate("""() => [...document.querySelectorAll(
        'img[src], video[src], video[poster]')].map(e => ({
            src: (e.getAttribute('src') || e.getAttribute('poster') || ''),
            poster: e.getAttribute('poster') || ''}))""")
    names = []
    for e in placed:
        for ref in (e["src"], e["poster"]):
            if "moodboard-media/" in ref:
                names.append(ref.split("moodboard-media/", 1)[1])
    unknown = sorted({n for n in names if n not in measured})
    over = sorted({"%s L %.3f" % (n, measured[n]) for n in names
                   if n in measured and measured[n] > ceiling})
    top = max((measured[n] for n in names if n in measured), default=0)
    why = ([("over the ceiling: " + ", ".join(over))] if over else []) + \
          ([("not in the manifest, so never measured: " + ", ".join(unknown))]
           if unknown else []) + ([] if names else ["no placed images found"])
    chk(not why,
        "image_never_brightens every placed image's upper quartile is at or below L %.3f%s"
        % (ceiling, "  :: " + "; ".join(why) if why
           else "  :: %d placements of %d measured files, brightest L %.3f"
           % (len(names), len(set(names)), top)))

    # ---------- image_on_ground
    # An image that reaches a page edge stops being a picture on a ground and becomes the
    # ground. Measured at desktop and phone, and on the page the reader prints.
    EDGE = 1.0
    touch = []
    for w in (1440, 390):
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(260)
        for e in pg.evaluate("""() => [...document.querySelectorAll('.sheet')].flatMap(s => {
            const sr = s.getBoundingClientRect();
            return [...s.querySelectorAll('img, video')].filter(
                e => getComputedStyle(e).display !== 'none').map(e => {
                    const r = e.getBoundingClientRect();
                    return {n: s.dataset.sheet, l: r.left - sr.left, r: sr.right - r.right,
                            t: r.top - sr.top, b: sr.bottom - r.bottom};
                });
        })"""):
            side = [k for k in "lrtb" if e[k] < EDGE]
            if side:
                touch.append("sheet %s at %dpx, %d px from the edge"
                             % (e["n"], w, round(min(e[k] for k in side))))
    n_print = 0
    if pdf is not None and sheet_pt:
        for i in range(n_sheets):
            pw = pdf[i].rect.width
            for r in _page_clips(pdf[i]):
                n_print += 1
                if r[0] < EDGE or r[1] < EDGE or pw - r[2] < EDGE or sheet_pt - r[3] < EDGE:
                    touch.append("sheet %02d in print, slot at %.0f,%.0f to %.0f,%.0f"
                                 % (i + 1, r[0], r[1], r[2], r[3]))
    # n_print is required: a page-clip reader that found nothing must not pass by measuring nothing
    chk(not touch and pdf is not None and sheet_pt and n_print > 0,
        "image_on_ground  no image touches a page edge; the ground does%s"
        % ("  :: " + "; ".join(touch[:3]) if touch
           else "  :: " + (pdf_why or "no print height in the document") if not (
               pdf is not None and sheet_pt)
           else "  :: no slots found in print, so nothing was measured" if not n_print
           else "  :: every image inset from every edge, on screen at 1440 and 390 and "
                "%d slots in print" % n_print))

    # ---------- poster_in_print
    # Chromium prints a <video> as whichever frame is showing, so each clip carries a poster
    # that print shows instead. The stills the PDF holds on a stage sheet must be exactly the
    # manifest's: a poster for each video, the file for each still.
    swap = pg.evaluate("""() => [...document.querySelectorAll('.imgs > figure')].map(f => ({
        n: f.closest('.sheet').dataset.sheet,
        video: !!f.querySelector('video'),
        prt: (f.querySelector('img.prt') || {}).src || ''}))""")
    gone = ["sheet %s: a video with no poster in the swap" % q["n"]
            for q in swap if q["video"] and "posters/" not in q["prt"]]
    n_vid = sum(1 for refs in man["stages"].values() for r_ in refs if r_["kind"] == "video")
    if pdf is not None and len(stage_idx) == len(man["stages"]):
        for i, key in zip(stage_idx, sorted(man["stages"])):
            want = []
            for r_ in man["stages"][key]:
                pm = fitz.Pixmap(str(ROOT / "brand/moodboard-media" /
                                     (r_["poster"] or r_["file"])))
                want.append((pm.width, pm.height, r_["kind"], r_["file"]))
            have = sorted((im["width"], im["height"]) for im in pdf[i].get_image_info())
            left = list(have)
            for w_, h_, kind, f_ in sorted(want):
                if (w_, h_) in left:
                    left.remove((w_, h_))
                else:
                    gone.append("sheet %02d prints no %s for %s (%dx%d)"
                                % (i + 1, "poster" if kind == "video" else "still", f_, w_, h_))
            if left:
                gone.append("sheet %02d prints %d image(s) the manifest does not hold"
                            % (i + 1, len(left)))
    chk(pdf is not None and not gone and n_vid,
        "poster_in_print  every video reference resolves to a still in the PDF%s"
        % ("  :: " + "; ".join(gone[:3]) if gone
           else "  :: " + pdf_why if pdf is None
           else "  :: %d videos, each printed as its poster, on %d stage sheets"
           % (n_vid, len(stage_idx))))

    # ---------- caption_contrast
    # ink_measured proves the sheet's ink; this proves the words set in it. Every caption and
    # reading on a sheet that carries imagery is measured against the ground it sits on: the
    # panel it is in, or the flat stage colour, or the worse end of the fall's slice.
    # Measured twice: on screen at 1440, and under print emulation at Letter width, because a
    # colour rule set only for print would otherwise be invisible to a check about what the
    # PDF reader sees. The PDF's own text is not reconstructed; it is these same computed colours.
    pg.set_viewport_size({"width": 1440, "height": 900})
    pg.wait_for_timeout(260)
    n_text, rows_s = read_contrast(pg)
    pg.emulate_media(media="print")
    pg.set_viewport_size({"width": 1056, "height": 816})
    pg.wait_for_timeout(260)
    n_text_p, rows_p = read_contrast(pg)
    pg.emulate_media(media="null")
    low = ["sheet %s %r reads %.2f:1 on %s%s, below %.1f"
           % (r_["n"], r_["text"], r_["got"], r_["on"], " in print" if m_ else "", r_["floor"])
           for m_, rr in ((0, rows_s), (1, rows_p)) for r_ in rr if r_["got"] < r_["floor"]]
    worst = min([r_["got"] for r_ in rows_s + rows_p], default=0)
    chk(n_text and n_text_p and not low,
        "caption_contrast every caption and reading on a sheet that carries imagery clears "
        "its floor on its ground%s"
        % ("  :: " + "; ".join(sorted(set(low))[:3]) if low
           else "  :: %d lines on %d sheets, on screen and in print, lowest %.2f:1"
           % (n_text, len({r_["n"] for r_ in rows_s}), worst)))

    # ---------- grid_ratio_holds
    # The slot is the fixed quantity; the columns change. A slot that drifts to 4:3 is a
    # crop nobody chose. The field above the grid must read the same on all four stage
    # sheets or the set stops looking like a set.
    slot_css = pg.evaluate("getComputedStyle(document.documentElement)"
                           ".getPropertyValue('--slot')")
    m_ = re.match(r"\s*([\d.]+)\s*/\s*([\d.]+)", slot_css or "")
    declared = float(m_.group(1)) / float(m_.group(2)) if m_ else 0
    bad, fields, n_slots = [], {}, 0
    if abs(declared - SLOT) > 1e-9:
        bad.append("the document declares --slot as %r, not 5/4" % slot_css.strip())
    for w in (1440, 900, 700, 390):
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(260)
        got = pg.evaluate("""() => ({
            slots: [...document.querySelectorAll('.imgs > figure, .misuse-tile')].map(f => {
                const r = f.getBoundingClientRect();
                return {n: f.closest('.sheet').dataset.sheet, w: r.width, h: r.height};
            }),
            field: [...document.querySelectorAll('.stagerule')].map(h => {
                const g = h.closest('.sheet').querySelector('.imgs');
                return {n: h.closest('.sheet').dataset.sheet,
                        f: g.getBoundingClientRect().top - h.getBoundingClientRect().bottom};
            })})""")
        for q in got["slots"]:
            n_slots += 1
            if abs(q["w"] / q["h"] / SLOT - 1) > 0.01:
                bad.append("sheet %s at %dpx is %.3f, not 1.250" % (q["n"], w, q["w"] / q["h"]))
        spread = [q["f"] for q in got["field"]]
        fields[w] = spread
        if len(spread) != 4 or max(spread) - min(spread) > 0.5:
            bad.append("the field above the grid at %dpx runs %s"
                       % (w, "/".join("%.0f" % v for v in spread)))
    if pdf is not None:
        for i in stage_idx:
            clips = _page_clips(pdf[i])
            rule = [d["scissor"] for d in pdf[i].get_drawings(extended=True)
                    if d["type"] == "clip" and 0 < d["scissor"].height < 3
                    and d["scissor"].width > pdf[i].rect.width / 2]
            for r in clips:
                n_slots += 1
                if abs((r[2] - r[0]) / (r[3] - r[1]) / SLOT - 1) > 0.01:
                    bad.append("sheet %02d in print is %.3f, not 1.250"
                               % (i + 1, (r[2] - r[0]) / (r[3] - r[1])))
            if rule and clips:
                fields.setdefault("print", []).append(clips[0][1] - rule[0].y1)
        pf = fields.get("print", [])
        # Print snaps a clip to whole device pixels, so the same field varies by up to a pixel
        # (0.75pt) with where the head lands; a field that is really unequal is far more.
        if len(pf) != 4 or max(pf) - min(pf) > 1.5:
            bad.append("the field above the grid in print runs %s"
                       % "/".join("%.1f" % v for v in pf))
    else:
        bad.append(pdf_why)
    chk(not bad,
        "grid_ratio_holds every slot is 5:4 within 1%% at 1440, 900, 700, 390 and in print%s"
        % ("  :: " + "; ".join(bad[:3]) if bad
           else "  :: %d slots measured, field above the grid %.0f px on all four stage sheets"
           % (n_slots, fields[1440][0])))

    # ---------- footer_in_page
    # .sheet clips at 8.05in in print, so a footer pushed past it is dropped without a word:
    # the stage sheets clear it by about 12px, and a stage name that wraps would cost 40.
    # The folio is found on its own line and everything on that line must sit inside.
    lost = []
    if pdf is not None and sheet_pt:
        for i in range(n_sheets):
            words = pdf[i].get_text("words")
            folio = [w for w in words if w[4] == "%02d" % (i + 1)]
            if not folio:
                lost.append("sheet %02d prints no folio; its footer is clipped" % (i + 1))
                continue
            f = max(folio, key=lambda w: (w[1], w[0]))
            line = [w for w in words if abs(w[1] - f[1]) < 3]
            low_ = max(w[3] for w in line)
            if low_ > sheet_pt + 0.3 or min(w[1] for w in line) < 0:
                lost.append("sheet %02d footer ends %.1fpt, the sheet at %.1fpt"
                            % (i + 1, low_, sheet_pt))
            elif not any(w[4].upper() == "AFTERGLOW" for w in line):
                lost.append("sheet %02d footer has lost its mark" % (i + 1))
    chk(pdf is not None and sheet_pt and not lost,
        "footer_in_page   every sheet's footer sits wholly inside its page in the PDF%s"
        % ("  :: " + "; ".join(lost[:3]) if lost
           else "  :: " + (pdf_why or "no print height in the document") if not (
               pdf is not None and sheet_pt)
           else "  :: %d footers inside %.1fpt" % (n_sheets, sheet_pt)))
    if pdf is not None:
        pdf.close()


if __name__ == "__main__":
    main()
    extra_checks()
    sys.exit(report())
