# -*- coding: utf-8 -*-
"""Afterglow brand guide.

Twenty sheets. Each carries its own slice of the fall, so the deck deepens gold to
violet across its whole length and the document is an example of the brand rather than a
description of it. Readings sit in void panels, because a number read off a mid-ramp
colour is a number nobody can check.

Medium-agnostic on purpose. The event art direction in brand/2026-10-03-afterglow-brief.md
(four rooms, the bottle revealed last, no wordmark in sight) governs the launch night and
not the brand, which is settled in the design spec. None of it is carried here.

Every value renders from brand/resources/design-tokens.json. Run tools/guide_audit.py.
"""
import io, json, pathlib, importlib.util

ROOT = pathlib.Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("ba", ROOT / "tools" / "brand_audit.py")
B = importlib.util.module_from_spec(_s)
try:
    _s.loader.exec_module(B)
except SystemExit:
    pass

T = json.loads(io.open(ROOT / "brand/resources/design-tokens.json", encoding="utf-8").read())
OUT = ROOT / "brand/2026-10-09-afterglow-brand-guide.html"
C = T["color"]
STAGES = [C["stages"][str(n)] for n in (1, 2, 3, 4)]
RAMP = [s["value"] for s in STAGES]
VOID, SDEEP, SURF = C["ground"]["value"], C["surface-deep"]["value"], C["surface"]["value"]
TEXT, MUTED, BORDER = C["text"]["value"], C["muted"]["value"], C["border"]["value"]
SC = T["typography"]["scale"]["steps"]
SP = T["spacing"]["scale"]
MO = T["motion"]
DISPLAY = T["typography"]["display"]["family"]
BODY = T["typography"]["body"]["family"]
TITLE = "Afterglow Brand Guide"
DATE = "October 2026"
STOPS = list(zip((0.0, 1 / 3.0, 2 / 3.0, 1.0), RAMP))
N = 20
MEDIA = ROOT / "brand" / "moodboard-media"
MANIFEST = json.loads(
    io.open(ROOT / "brand/resources/imagery-manifest.json", encoding="utf-8").read())


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def fall(t):
    t = max(0.0, min(1.0, t))
    for i in range(3):
        (p0, c0), (p1, c1) = STOPS[i], STOPS[i + 1]
        if p0 <= t <= p1:
            f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
            a, b = _rgb(c0), _rgb(c1)
            return "#%02X%02X%02X" % tuple(int(round(a[j] + (b[j] - a[j]) * f))
                                           for j in range(3))
    return RAMP[-1]


def slice_css(i):
    t0, t1 = i / float(N), (i + 1) / float(N)
    pts = [t0] + [s for s, _ in STOPS if t0 < s < t1] + [t1]
    return "linear-gradient(180deg,%s)" % ", ".join(
        "%s %.4f%%" % (fall(t), (t - t0) / (t1 - t0) * 100) for t in pts)


def cmyk(hexv):
    """Converted from sRGB, not matched. Printed as guidance for a proof, never as a
    specification: a converted value and an inked value are different things."""
    r, g, b = (x / 255.0 for x in _rgb(hexv))
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return tuple(int(round(v * 100)) for v in (c, m, y, k))


def ratio(a, b):
    return B.contrast(a, b)


def num(fg, bg):
    return ('<b class="num" data-fg="%s" data-bg="%s">%.2f:1</b>'
            % (fg.upper(), bg.upper(), ratio(fg, bg)))


def ink(i, ground=None):
    """Which of the two text colours the sheet's own ground carries. Measured at the
    sheet's midpoint, or on the flat colour a stage sheet stands on; never chosen."""
    mid = ground or fall((i + 0.5) / float(N))
    return "dark" if ratio(VOID, mid) >= ratio(TEXT, mid) else "light"


def panel(inner, cls=""):
    return '        <div class="panel %s">\n%s        </div>\n' % (cls, inner)


def sheet(i, section, title, lead, body, cls=""):
    return """
  <section class="sheet %(tone)s %(cls)s" data-sheet="%(n)02d"
           style="background:%(g)s">
    <div class="grid">
      <div class="col-l">
        <h2 class="t">%(title)s</h2>
        <p class="lead">%(lead)s</p>
      </div>
      <div class="col-r">
%(body)s      </div>
    </div>
    <footer class="foot">
      <span class="mark">Afterglow</span><span>%(section)s</span>
      <span class="doc">%(doc)s &middot; %(date)s</span><span class="pg">%(n)02d</span>
    </footer>
  </section>
""" % dict(n=i + 1, tone=ink(i), cls=cls, g=slice_css(i), title=title, lead=lead,
           body=body, section=section, doc=TITLE, date=DATE)


def stage_sheet(i, stage_key, body):
    """A full-width sheet for one stage: name, reading, rule, grid, footer and nothing
    else. No .col-l/.col-r split, because the grid wants the whole width. Its ground is the
    stage's own colour, flat, so the images sit on the colour they describe; the folio is
    sheet()'s, the slice of the fall is not. Every extra element here costs print height
    the sheet does not have, and .sheet clips in print without a word."""
    st = C["stages"][stage_key]
    return """
  <section class="sheet %(tone)s" data-sheet="%(n)02d" style="background:%(v)s">
    <div class="stagehead">
      <h2 class="stagename">%(name)s</h2>
      <span class="stageread"><span class="dot ring" style="background:%(v)s"></span>%(v)s
        &middot; L %(l).3f</span>
    </div>
    <hr class="stagerule">
    <div class="imgs">
%(body)s    </div>
    <footer class="foot">
      <span class="mark">Afterglow</span><span>Imagery</span>
      <span class="doc">%(doc)s &middot; %(date)s</span><span class="pg">%(n)02d</span>
    </footer>
  </section>
""" % dict(n=i + 1, tone=ink(i, st["value"]), name=st["name"], v=st["value"],
           l=B.oklch(st["value"])[0], body=body, doc=TITLE, date=DATE)


def _on_disk(name):
    """A reference that is not on disk fails the build here, by name, rather than
    shipping a broken image element into a document that looks finished."""
    f = MEDIA / name  # name may carry a posters/ prefix
    if not f.is_file() or f.stat().st_size == 0:
        raise SystemExit("imagery: %s is missing or empty; the manifest points at a "
                         "file the guide cannot show" % f.relative_to(ROOT))
    return "moodboard-media/" + name


def figure(ref, stage="", alt=""):
    """One slot of the grid. A video is the pair .scr and .prt: the clip for screen, its
    poster for print, because Chromium prints a video as whichever frame is showing."""
    src = _on_disk(ref["file"])
    if ref["kind"] == "video":
        if not ref.get("poster"):
            raise SystemExit("imagery: %s is a video with no poster; print would take "
                             "whichever frame is showing" % ref["file"])
        poster = _on_disk(ref["poster"])
        return ("""      <figure data-stage="%(st)s">
        <video class="scr" src="%(s)s" poster="%(p)s" autoplay muted loop playsinline
               preload="metadata" aria-label="%(a)s"></video>
        <img class="prt" src="%(p)s" alt="%(a)s">
      </figure>\n""" % dict(st=stage, s=src, p=poster, a=alt))
    return """      <figure data-stage="%s"><img src="%s" alt="%s"></figure>\n""" % (
        stage, src, alt)


def stage_figures(stage_key):
    """The alt text states the image's role and nothing else. No description of the
    picture exists to be written, and one invented here could not be checked."""
    refs, name = MANIFEST["stages"][stage_key], C["stages"][stage_key]["name"]
    return "".join(figure(r, stage_key, "Reference %d of %d for %s" % (k + 1, len(refs), name))
                   for k, r in enumerate(refs))


# ---------------------------------------------------------------- sheet bodies
def s_stages():
    rows = "".join("""          <div class="srow">
            <span class="chip" style="background:%(v)s"></span>
            <div class="sinfo">
              <p class="sname">%(n)s</p>
              <dl><div><dt>Hex</dt><dd>%(v)s</dd></div>
                  <div><dt>OKLCH</dt><dd>%(l).3f &nbsp;%(c).3f &nbsp;%(h).1f</dd></div>
                  <div><dt>CMYK</dt><dd>%(cm)s</dd></div>
                  <div><dt>Pantone</dt><dd class="todo">match on proof</dd></div></dl>
            </div>
          </div>\n""" % dict(v=s["value"], n=s["name"], l=s["oklch"]["l"],
                             c=s["oklch"]["c"], h=s["oklch"]["h"],
                             cm=" ".join(str(x) for x in cmyk(s["value"])))
        for s in STAGES)
    return panel(rows) + """        <p class="fine">CMYK is converted from sRGB for a proof,
          not matched. A Pantone is an inked colour under controlled light and cannot be
          derived from a hex, so each is left to be matched against a physical guide and
          written back here.</p>\n"""


def s_contrast():
    head = """          <table class="tbl">
            <thead><tr><th>Stage</th><th>On void</th><th>On %s</th><th>On %s</th>
              <th>Text on it</th><th>Role</th></tr></thead><tbody>\n""" % (SDEEP, SURF)
    body = "".join("""              <tr><td><span class="dot" style="background:%(v)s"></span>%(n)s</td>
                <td>%(a)s</td><td>%(b)s</td><td>%(c)s</td><td>%(d)s</td>
                <td class="role">%(role)s</td></tr>\n"""
        % dict(v=s["value"], n=s["name"], a=num(s["value"], VOID),
               b=num(s["value"], SDEEP), c=num(s["value"], SURF),
               d=num(TEXT, s["value"]), role=role_of(s["value"])[0])
        for s in STAGES)
    rules = "".join("""            <div class="rr"><span class="dot" style="background:%s"></span>
              <p>%s</p></div>\n""" % (s["value"], role_of(s["value"])[1]) for s in STAGES)
    return (panel(head + body + "          </tbody></table>\n")
            + panel('          <div class="rrs">\n' + rules + "          </div>\n"))


def role_of(v):
    r = ratio(v, VOID)
    if r >= 4.5:
        return ("Text, marks, rules",
                "Clears the body floor on the void at %.2f:1. Usable as a letterform at "
                "any size, in any medium." % r)
    if r >= 3.0:
        return ("Large text, fills",
                "Clears the large-text floor at %.2f:1 and not the body floor. Headings "
                "and fills." % r)
    return ("Ground only",
            "Reads %.2f:1 on the void, under every text floor. A ground, never a "
            "letterform." % r)


def s_neutrals():
    items = [("Ground", C["ground"]), ("Surface, recessed", C["surface-deep"]),
             ("Surface, raised", C["surface"]), ("Text", C["text"]),
             ("Muted", C["muted"]), ("Border", C["border"])]
    rows = []
    for label, tok in items:
        v = tok["value"]
        hexish = v.startswith("#")
        rows.append("""              <tr><td><span class="dot%(ring)s" style="background:%(sw)s"></span>%(l)s</td>
                <td class="mono">%(v)s</td><td>%(ok)s</td><td>%(cm)s</td>
                <td class="use">%(use)s</td></tr>\n"""
            % dict(l=label, v=v, sw=v if hexish else "transparent",
                   ring="" if hexish else " ring",
                   ok=("%.3f" % B.oklch(v)[0]) if hexish else "n/a",
                   cm=" ".join(str(x) for x in cmyk(v)) if hexish else "n/a",
                   use=tok.get("use", "")))
    return panel("""          <table class="tbl">
            <thead><tr><th>Token</th><th>Value</th><th>OKLCH L</th><th>CMYK</th>
              <th>Use</th></tr></thead><tbody>\n""" + "".join(rows)
                 + "          </tbody></table>\n")


def s_fall():
    stops = "".join("""              <tr><td>%d</td><td class="mono">%s</td>
                <td>%.4g%%</td><td>%s</td></tr>\n"""
        % (i + 1, c, p * 100, STAGES[i]["name"]) for i, (p, c) in enumerate(STOPS))
    return ("""        <div class="fallspec">
          <div class="fallbar"></div>
          <div class="fallmeta">
"""
            + panel("""            <table class="tbl">
              <thead><tr><th>Stop</th><th>Value</th><th>Position</th><th>Stage</th></tr>
              </thead><tbody>\n""" + stops + "            </tbody></table>\n")
            + """          </div>
        </div>
"""
            + panel("""          <p class="pk">Rules</p>
          <ul class="rules">
            <li>Gold to violet, top to bottom or left to right. Never reversed, because
              the one thing the ramp says is that the light deepens.</li>
            <li>Interpolated in sRGB. Specifying it in another space changes every
              intermediate value and the measured ratios stop holding.</li>
            <li>No stop may be added, moved or removed. Four stops, evenly spaced.</li>
            <li>Nothing smaller than 24&nbsp;px of type sits directly on it. Type on the
              fall uses the floor for the darkest value it crosses.</li>
            <li>In print it is a four-colour build or a gradient mesh; it is not two
              spot inks, which cannot hold the middle.</li>
          </ul>\n"""))


def s_wordmark():
    return ("""        <div class="wmstage">
          <div class="wmbox"><span class="wmspace"></span>
            <span class="wmtext">Afterglow</span></div>
        </div>
"""
            + panel("""          <p class="pk">Construction</p>
          <p class="pl">Set in %s at 400, tracking 0, no optical adjustment. There is no
            drawn logotype: the wordmark is the typeface, which is what keeps it
            reproducible by anyone who has the guide.</p>
          <p class="pk">Clear space</p>
          <p class="pl">The cap height of the A on every side, measured from the
            bounding box of the word. At the minimum size of 96&nbsp;px, or 24&nbsp;mm in
            print, that is %d&nbsp;px.</p>\n""" % (DISPLAY, SP["lg"])))


def s_misuse():
    bad = [("Do not recolour", "Outside the four stages and the two text neutrals."),
           ("Do not stretch", "No horizontal or vertical scaling, ever."),
           ("Do not outline", "No stroke, no shadow, no glow. Shadow is not in the system."),
           ("Do not stack", "One line. The word does not break."),
           ("Do not set small on the fall",
            "Below 24 px it fails its floor somewhere on the ramp."),
           ("Do not substitute", "If the face is unavailable the wordmark is set as an "
                                 "image, not in a fallback.")]
    cells = "".join("""            <div class="dont"><p class="dk">%s</p><p>%s</p></div>\n"""
                    % (k, v) for k, v in bad)
    return panel('          <div class="donts">\n' + cells + "          </div>\n")


def s_type():
    order = ["4xl", "3xl", "2xl", "xl", "lg", "md", "base", "xs"]
    rows = "".join("""            <div class="tstep"><span class="tlab">%s</span>
              <span class="tsamp" style="font-size:%srem">Deepening</span>
              <span class="tnum">%g px &middot; %s rem</span></div>\n"""
        % (k, "%.4g" % (SC[k] / 16.0), SC[k], "%.4g" % (SC[k] / 16.0)) for k in order)
    return (panel("""          <div class="faces">
            <div class="face"><p class="pk">Display</p>
              <p class="fsamp serif">Afterglow</p>
              <p class="pl">%(d)s &middot; 400 &middot; headings and the wordmark</p></div>
            <div class="face"><p class="pk">Body</p>
              <p class="fsamp">Afterglow</p>
              <p class="pl">%(b)s &middot; 400 &middot; everything else</p></div>
          </div>\n""" % dict(d=DISPLAY, b=BODY))
            + panel('          <div class="tspec">\n' + rows + "          </div>\n"))


def s_setting():
    return (panel("""          <table class="tbl">
            <thead><tr><th>Role</th><th>Screen</th><th>Print</th><th>Leading</th>
              <th>Tracking</th></tr></thead><tbody>
              <tr><td>Display</td><td>%(x4)g&ndash;%(x2)g px</td><td>36&ndash;72 pt</td>
                <td>1.02</td><td>&minus;0.015 em</td></tr>
              <tr><td>Heading</td><td>%(xl)g px</td><td>18&ndash;24 pt</td>
                <td>1.1</td><td>&minus;0.01 em</td></tr>
              <tr><td>Body</td><td>%(base)g px</td><td>9.5&ndash;11 pt</td>
                <td>1.55</td><td>0</td></tr>
              <tr><td>Caption</td><td>%(xs)g px</td><td>7&ndash;8 pt</td>
                <td>1.45</td><td>0.08 em</td></tr>
              <tr><td>Label</td><td>%(xs)g px uppercase</td><td>7 pt uppercase</td>
                <td>1.3</td><td>0.12 em</td></tr>
            </tbody></table>\n""" % dict(x4=SC["4xl"], x2=SC["2xl"], xl=SC["xl"],
                                         base=SC["base"], xs=SC["xs"]))
            + panel("""          <p class="pk">Both media</p>
          <p class="pl">Sizes are authored in rem on screen so a reader's font-size
            preference is respected, and in points in print. The ratio is the same %g in
            both, from a %g px base, so a layout can be moved between them without
            redrawing the hierarchy.</p>\n"""
                    % (T["typography"]["scale"]["ratio"],
                       T["typography"]["scale"]["base"])))


def s_grid():
    cols = "".join('<span></span>' for _ in range(12))
    return ("""        <div class="gridstage"><div class="gcols">%s</div></div>\n""" % cols
            + panel("""          <table class="tbl">
            <thead><tr><th>Measure</th><th>Screen</th><th>Print</th></tr></thead><tbody>
              <tr><td>Columns</td><td>12</td><td>12</td></tr>
              <tr><td>Gutter</td><td>%(lg)d px</td><td>4 mm</td></tr>
              <tr><td>Margin</td><td>%(xl)d&ndash;%(x3)d px</td><td>12 mm</td></tr>
              <tr><td>Baseline</td><td>%(base)d px</td><td>4 mm</td></tr>
              <tr><td>Max measure</td><td>58 ch</td><td>58 ch</td></tr>
            </tbody></table>
          <p class="pk">Spacing</p>
          <div class="space">%(scale)s</div>
          <p class="pl">A %(base)d px base and whole multiples of it. Eight divides the
            %(tb)g px type base, so space and text sit on one grid rather than two that
            nearly agree.</p>\n"""
                    % dict(lg=SP["lg"], xl=SP["xl"], x3=SP["3xl"], base=T["spacing"]["base"],
                           tb=T["typography"]["scale"]["base"],
                           scale="".join(
                               '<span class="sstep"><i style="width:%dpx"></i>'
                               '<em>%s</em><b>%d px</b></span>' % (SP[k], k, SP[k])
                               for k in ("2xs", "xs", "sm", "md", "lg", "xl", "2xl", "3xl")))))


def s_system():
    return panel("""          <div class="trio">
            <div class="tile"><p class="pk">Radius</p><p class="tval">%(r)g</p>
              <p class="pl">Square. Restraint and a dark ground point there.</p></div>
            <div class="tile"><p class="pk">Shadow</p><p class="tval">%(s)s</p>
              <p class="pl">Elevation reads through the two surface steps.</p></div>
            <div class="tile"><p class="pk">Motion</p><p class="tval">%(d)g ms</p>
              <p class="pl">%(e)s. Ends at its destination, never passes it.</p></div>
          </div>
          <p class="pk">The one rule</p>
          <p class="rbig">No state change brightens.</p>
          <p class="pl">On screen that is hover, focus and active: they deepen or shift
            hue and never lighten. In print and in film it is the same rule about
            sequence: a later panel is never lighter than the one before it. It is the
            only rule here that can be checked in a diff, which is why it is written this
            way and not as a sentence about mood.</p>\n"""
                 % dict(r=T["radius"]["default"], s=T["shadow"]["default"],
                        d=MO["duration"]["base"], e=MO["ease"]))


def s_imagery_opener():
    """The five rules, set large, in a void panel and with no image beside them: the stage
    sheets that follow are the evidence, and an image here would be the first claim."""
    l1 = B.oklch(RAMP[0])[0]
    rules = [
        ("One light source, and it is falling.",
         "Images are made at the end of the day or lit to look as though they were."),
        ("The upper quartile of an image's lightness sits at or below the gold of last "
         "light, L %.3f." % l1,
         "Up to a quarter of the frame may pass it; the rest may not."),
        ("Warm to cool across a set, never back.",
         "A sequence follows the ramp in the same direction the ramp runs."),
        ("Grade toward the stages rather than to neutral.",
         "The palette is where the shadows and the highlights land."),
        ("Nothing is brightened in post.",
         "Exposure is lifted at capture or the frame is not used."),
    ]
    return panel("".join(
        """          <p class="rbig">%s</p>\n          <p class="pl">%s</p>\n""" % r
        for r in rules))


def s_imagery_misuse():
    """Each tile breaks one of the five rules using tokens only, so nothing here is itself
    a photograph that would have to clear the ceiling it is illustrating."""
    ramp = lambda cols: "linear-gradient(180deg,%s)" % ",".join(cols)
    # Each tile breaks one rule on the opener, in the opener's order.
    veil = "linear-gradient(rgba(%d,%d,%d,.4),rgba(%d,%d,%d,.4))" % (_rgb(TEXT) * 2)
    tiles = [
        ("Two light sources",
         "Breaks one light source, and it is falling.",
         "radial-gradient(circle at 12%% 20%%,%s,transparent 55%%),"
         "radial-gradient(circle at 88%% 80%%,%s,transparent 55%%),%s"
         % (RAMP[0], RAMP[3], VOID)),
        ("Flat light",
         "Breaks one light source, and it is falling: nothing falls.",
         RAMP[2]),
        ("Over-lit frame",
         "Breaks the upper quartile at or below gold: over a quarter of it passes.",
         "linear-gradient(180deg,%s 0%%,%s 38%%,%s 62%%,%s)" % (TEXT, TEXT, RAMP[0], RAMP[2])),
        ("Reversed set",
         "Breaks warm to cool, never back.",
         ramp(RAMP[::-1])),
        ("Graded to neutral",
         "Breaks grade toward the stages rather than to neutral.",
         "linear-gradient(180deg,%s,%s)" % (MUTED, SURF)),
        ("Lifted in post",
         "Breaks nothing is brightened in post: the shadows are raised.",
         "%s,%s" % (veil, RAMP[2])),
    ]
    cells = "".join("""            <div class="dont">
              <div class="misuse-tile" style="background:%s"></div>
              <p class="dk">%s</p><p>%s</p></div>\n""" % (bg, k, v) for k, v, bg in tiles)
    return panel('          <div class="donts">\n' + cells + "          </div>\n")


def _first_image(stage_key):
    """A still, not a clip: the card is the one place an image sits outside the swap."""
    return next(r["file"] for r in MANIFEST["stages"][stage_key] if r["kind"] == "image")


def s_digital():
    return panel("""          <div class="apps">
            <article class="app"><p class="pk">Product card</p>
              <div class="appbody" style="background:%(sd)s">
                <div class="appimg" style="background:%(s3)s">
                  <img src="%(ref)s" alt="Reference for the product card"></div>
                <p class="aname">Afterglow</p><p class="pl">$180</p></div></article>
            <article class="app"><p class="pk">Button, rest and hover</p>
              <div class="appbody" style="background:%(sd)s">
                <span class="btn" style="background:%(s1)s;color:%(v)s">Add to cart</span>
                <span class="btn" style="background:%(hv)s;color:%(v)s">Add to cart</span>
                <p class="pl">Hover deepens: L %(l1).3f to L %(lh).3f</p></div></article>
            <article class="app"><p class="pk">Surface steps</p>
              <div class="appbody" style="background:%(v)s">
                <div class="step" style="background:%(sd)s">Recessed %(sd)s</div>
                <div class="step" style="background:%(sf)s">Raised %(sf)s</div></div></article>
          </div>\n""" % dict(sd=SDEEP, sf=SURF, v=VOID, s1=RAMP[0], s3=RAMP[2],
                             hv="#A8832F", l1=B.oklch(RAMP[0])[0], lh=B.oklch("#A8832F")[0],
                             ref=_on_disk(_first_image("3"))))


def s_print():
    return panel("""          <div class="prints">
            <article class="app"><p class="pk">Card, 85 &times; 55 mm</p>
              <div class="pcard"><span class="pwm">Afterglow</span></div></article>
            <article class="app"><p class="pk">Label face</p>
              <div class="plabel"><span class="pwm sm">Afterglow</span>
                <span class="pfine">Eau de parfum &middot; 50 ml</span></div></article>
            <article class="app"><p class="pk">Poster, 2:3</p>
              <div class="pposter"><span class="pwm sm">Afterglow</span></div></article>
          </div>
          <p class="pk">Production</p>
          <ul class="rules">
            <li>The fall prints as a four-colour build or a gradient mesh. Two spot inks
              cannot hold the middle of the ramp.</li>
            <li>Uncoated stock shifts the ramp cooler and flattens the violet end. Proof
              on the stock, not on a house sheet.</li>
            <li>Flat bands are the failure mode of a long gradient on paper. Keep any one
              flat under an inch at the size it is printed.</li>
            <li>No placed image has an upper quartile above gold, L %(l1).3f. Checked on
              the file, not on the proof.</li>
            <li>No varnish or foil on the fall. A specular finish reverses the one rule
              wherever the light catches it.</li>
          </ul>\n""" % dict(l1=B.oklch(RAMP[0])[0]))


def s_voice():
    return panel("""          <p class="pk">Voice</p>
          <p class="pl">Unhurried and physical. It names heat, light, breath and skin. It
            describes a sequence, because the product is a sequence. Certain without
            pushing: the brand does not argue for itself, and assumes you will understand
            it if you are shown it in the right order.</p>
          <p class="pk">Where the rules stop</p>
          <p class="pl">Cart, checkout, shipping notices, legal and safety copy are plain
            and fast. The atmosphere stops there on purpose, exactly as the voice does.
            Applied to a payment form or a warning label the discipline makes it worse.</p>
          <p class="pk">Elsewhere</p>
          <p class="pl">The full voice, the word lists and the tone by context live in
            <a href="resources/voice-tone.md">voice-tone.md</a>. Event art direction for
            the launch is in <a href="2026-10-03-afterglow-brief.md">the brief</a> and
            governs that night only; nothing in it binds the brand.</p>\n""")


def cover():
    return """
  <section class="sheet %(tone)s cover" data-sheet="01" style="background:%(g)s">
    <div class="covergrid">
      <div><p class="kick">Brand guide &middot; %(date)s</p>
        <h1 class="wordmark">Afterglow</h1>
        <p class="covline">The light only ever deepens.</p></div>
      <div class="covmeta">
        <p class="pl">Four stages, two faces, one grid. Everything in this guide applies
          to any medium: screen, paper, film, surface.</p>
        <p class="pl">Values are rendered from the token file the build consumes, so a
          number here and a number in the code cannot disagree.</p>
      </div>
    </div>
    <footer class="foot"><span class="mark">Afterglow</span><span>Cover</span>
      <span class="doc">%(doc)s &middot; %(date)s</span><span class="pg">01</span></footer>
  </section>
""" % dict(tone=ink(0), g=slice_css(0), date=DATE, doc=TITLE)


def build():
    sheets = [
        cover(),
        sheet(1, "Identity", "The wordmark",
              "There is no drawn logotype. The wordmark is the typeface, which keeps it "
              "reproducible by anyone holding this guide.", s_wordmark()),
        sheet(2, "Identity", "Misuse",
              "Six ways to break it. Each one is a thing the system cannot absorb, not a "
              "matter of taste.", s_misuse()),
        sheet(3, "Colour", "The four stages",
              "One ramp. Lightness falls and chroma stays flat at 0.110 throughout, so "
              "the stages differ in depth rather than in intensity.", s_stages()),
        sheet(4, "Colour", "Contrast and roles",
              "Every ratio is computed from the token. The body floor is 4.5:1 and the "
              "large-text floor is 3:1; a role is what the number allows.", s_contrast()),
        sheet(5, "Colour", "Neutrals and surfaces",
              "Six tokens that are not on the ramp. Elevation is carried by the two "
              "surface steps, which is why there is no shadow in the system.", s_neutrals()),
        sheet(6, "Colour", "The fall",
              "The gradient is an asset with a specification, not an effect applied by "
              "eye. This page is an instance of it.", s_fall()),
        sheet(7, "Type", "Two faces, one scale",
              "Both are in Shopify's library, so neither ships as a webfont. The scale "
              "is a ratio, not a list.", s_type()),
        sheet(8, "Type", "Setting for screen and print",
              "The same hierarchy in both media, so a layout moves between them without "
              "being redrawn.", s_setting()),
        sheet(9, "Layout", "Grid and spacing",
              "Twelve columns in both media and one spacing base that divides the type "
              "base.", s_grid()),
        sheet(10, "Layout", "Radius, shadow, motion, and the one rule",
              "Three values and the only rule in this document that can be checked "
              "automatically.", s_system()),
        sheet(11, "Imagery", "Art direction",
              "The palette is a description of light at a particular hour. Images are "
              "made to match it rather than graded toward it afterwards.",
              s_imagery_opener()),
        stage_sheet(12, "1", stage_figures("1")),
        stage_sheet(13, "2", stage_figures("2")),
        stage_sheet(14, "3", stage_figures("3")),
        stage_sheet(15, "4", stage_figures("4")),
        sheet(16, "Imagery", "Misuse",
              "Six ways to break the five rules. Each tile is built from tokens, so none "
              "of them is a photograph that would have to clear the ceiling.",
              s_imagery_misuse()),
        sheet(17, "Applications", "Digital",
              "The three things a storefront is mostly made of, in the tokens, and the "
              "imagery they sit with.", s_digital()),
        sheet(18, "Applications", "Print and production",
              "What the fall needs from a press, and what will break it.", s_print()),
        sheet(19, "Voice", "Voice, and where the rules stop",
              "The visual system and the voice stop in the same place, which is not an "
              "accident.", s_voice()),
    ]
    assert len(sheets) == N, "%d sheets against %d slices of the fall" % (len(sheets), N)
    tpl = io.open(ROOT / "tools" / "guide_template.html", encoding="utf-8").read()
    return tpl % dict(
        void=VOID, sdeep=SDEEP, surf=SURF, text=TEXT, muted=MUTED, border=BORDER,
        s1=RAMP[0], s4=RAMP[3], display=DISPLAY, body=BODY, title=TITLE,
        xs=SC["xs"] / 16.0, base=SC["base"] / 16.0, md=SC["md"] / 16.0, lg=SC["lg"] / 16.0,
        xl=SC["xl"] / 16.0, x2=SC["2xl"] / 16.0, x3=SC["3xl"] / 16.0, x4=SC["4xl"] / 16.0,
        sp2xs=SP["2xs"], spxs=SP["xs"], spsm=SP["sm"], spmd=SP["md"], splg=SP["lg"],
        spxl=SP["xl"], sp2xl=SP["2xl"], sp3xl=SP["3xl"],
        radius=T["radius"]["default"], dur=MO["duration"]["base"], ease=MO["ease"],
        fullfall="linear-gradient(180deg,%s)" % ", ".join(
            "%s %.4f%%" % (c, p * 100) for p, c in STOPS),
        sheets="".join(sheets))


if __name__ == "__main__":
    html = build()
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("wrote %s (%d lines, %d sheets)" % (OUT.name, html.count("\n") + 1, N))
    for i in range(N):
        print("  %02d  %s to %s  ink %s" % (i + 1, fall(i / float(N)),
                                            fall((i + 1) / float(N)), ink(i)))
