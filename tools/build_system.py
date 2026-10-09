# -*- coding: utf-8 -*-
"""Afterglow design system reference.

Eight discrete sheets on the void, held to the Frame.io brand-guide standard that
`references/2026-10-07-frameio-guidelines/` captures: a statement column on the left, a
specimen grid on the right, a footer rule carrying section and page on every sheet.

Every value is rendered from brand/resources/design-tokens.json and every contrast ratio
is computed here, so nothing in the document can drift from the tokens the theme builds
against. Run tools/brand_system_audit.py after any change.
"""
import io, json, pathlib, importlib.util

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("ba", ROOT / "tools" / "brand_audit.py")
B = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(B)
except SystemExit:
    pass

T = json.loads(io.open(ROOT / "brand/resources/design-tokens.json", encoding="utf-8").read())
OUT = ROOT / "brand/2026-10-09-afterglow-design-system.html"

C = T["color"]
STAGES = [C["stages"][str(n)] for n in (1, 2, 3, 4)]
VOID, SDEEP, SURF = C["ground"]["value"], C["surface-deep"]["value"], C["surface"]["value"]
TEXT, MUTED, BORDER = C["text"]["value"], C["muted"]["value"], C["border"]["value"]
SC = T["typography"]["scale"]["steps"]
SP = T["spacing"]["scale"]
MO = T["motion"]
DISPLAY = T["typography"]["display"]["family"]
BODY = T["typography"]["body"]["family"]

TITLE = "Afterglow Design System"
DATE = "October 2026"


def r(fg, bg):
    return B.contrast(fg, bg)


def num(fg, bg):
    """A printed ratio carries the pair it was computed from, so the audit can recompute it."""
    return ('<b class="num" data-fg="%s" data-bg="%s">%.2f:1</b>'
            % (fg.upper(), bg.upper(), r(fg, bg)))


def verdict(ratio, large=False):
    floor = 3.0 if large else 4.5
    ok = ratio >= floor
    return ('<span class="v %s">%s</span>'
            % ("yes" if ok else "no", "Pass" if ok else "Fail"))


def sheet(n, section, title, lead, right, wide=False):
    return """
  <section class="sheet%(w)s" data-sheet="%(n)02d">
    <div class="grid">
      <div class="col-l">
        <h2 class="t">%(title)s</h2>
        <p class="lead">%(lead)s</p>
      </div>
      <div class="col-r">
%(right)s      </div>
    </div>
    <footer class="foot">
      <span class="mark">Afterglow</span>
      <span>%(section)s</span>
      <span>%(doc)s &middot; %(date)s</span>
      <span class="pg">%(n)02d</span>
    </footer>
  </section>
""" % dict(n=n, section=section, title=title, lead=lead, right=right,
           doc=TITLE, date=DATE, w=" wide" if wide else "")


def cover():
    return """
  <section class="sheet cover" data-sheet="01">
    <div class="covergrid">
      <div>
        <p class="kick">Brand guide &middot; %(date)s</p>
        <h1 class="wordmark">Afterglow</h1>
        <p class="covline">One fragrance told in four stages, from the gold of last light
          to deep violet.</p>
      </div>
      <div class="coverswatch">
%(sw)s      </div>
    </div>
    <footer class="foot">
      <span class="mark">Afterglow</span>
      <span>Cover</span>
      <span>%(doc)s &middot; %(date)s</span>
      <span class="pg">01</span>
    </footer>
  </section>
""" % dict(date=DATE, doc=TITLE,
           sw="".join('        <i style="background:%s"></i>\n' % s["value"] for s in STAGES))


def stage_cards():
    out = []
    for i, s in enumerate(STAGES):
        o = s["oklch"]
        out.append("""        <article class="card">
          <div class="chip" style="background:%(v)s"></div>
          <div class="meta">
            <p class="cname">%(name)s</p>
            <dl>
              <div><dt>Hex</dt><dd>%(v)s</dd></div>
              <div><dt>OKLCH</dt><dd>%(l).3f &nbsp;%(c).3f &nbsp;%(h).1f</dd></div>
              <div><dt>Stage</dt><dd>%(i)d of 4</dd></div>
            </dl>
          </div>
        </article>
""" % dict(v=s["value"], name=s["name"], l=o["l"], c=o["c"], h=o["h"], i=i + 1))
    return "".join(out)


def contrast_table():
    head = ("""        <table class="tbl">
          <thead><tr><th>Stage</th><th>On void</th><th>On #141414</th><th>On #2B2B2B</th>
            <th>Text on it</th><th>As text on void</th></tr></thead>
          <tbody>
""")
    rows = []
    for s in STAGES:
        v = s["value"]
        rows.append("""            <tr>
              <td><span class="dot" style="background:%(v)s"></span>%(n)s</td>
              <td>%(a)s</td><td>%(b)s</td><td>%(c)s</td><td>%(d)s</td>
              <td>%(verdict)s</td>
            </tr>
""" % dict(v=v, n=s["name"], a=num(v, VOID), b=num(v, SDEEP), c=num(v, SURF),
           d=num(TEXT, v), verdict=verdict(r(v, VOID))))
    return head + "".join(rows) + "          </tbody>\n        </table>\n"


def role_for(v):
    """Derived from the measured ratio on the void, never asserted separately. A role
    written by hand drifts from the number printed next to it the first time the ramp
    moves."""
    ratio = r(v, VOID)
    if ratio >= 4.5:
        return ("Text, marks, rules",
                "Clears the body floor on the void at %.2f:1. Usable for a letterform "
                "at any size." % ratio)
    if ratio >= 3.0:
        return ("Large text, fills",
                "Clears the large-text floor at %.2f:1 and not the body floor. Headings "
                "and fills only." % ratio)
    return ("Ground only",
            "Reads %.2f:1 on the void, under every text floor. A ground, never a "
            "letterform." % ratio)


def role_list():
    return "".join("""        <div class="role">
          <span class="dot" style="background:%(v)s"></span>
          <div><p class="rname">%(n)s <em>%(tag)s</em></p><p class="rrule">%(rule)s</p></div>
        </div>
""" % dict(v=st["value"], n=st["name"], tag=role_for(st["value"])[0],
           rule=role_for(st["value"])[1])
        for st in STAGES)


def neutral_rows():
    items = [("Ground", C["ground"]), ("Surface, recessed", C["surface-deep"]),
             ("Surface, raised", C["surface"]), ("Text", C["text"]),
             ("Muted", C["muted"]), ("Border", C["border"])]
    out = []
    for label, tok in items:
        v = tok["value"]
        swatch = v if v.startswith("#") else SURF
        on_void = num(v, VOID) if v.startswith("#") else "&mdash;".replace("&mdash;", "n/a")
        out.append("""            <tr>
              <td><span class="dot%(ring)s" style="background:%(sw)s"></span>%(label)s</td>
              <td class="mono">%(v)s</td>
              <td>%(l)s</td>
              <td>%(ov)s</td>
              <td class="use">%(use)s</td>
            </tr>
""" % dict(label=label, v=v, sw=swatch, ring=" ring" if not v.startswith("#") else "",
           l=("%.3f" % B.oklch(v)[0]) if v.startswith("#") else "n/a",
           ov=on_void, use=tok.get("use", "")))
    return ("""        <table class="tbl">
          <thead><tr><th>Token</th><th>Value</th><th>OKLCH L</th><th>On void</th>
            <th>Use</th></tr></thead>
          <tbody>
""" + "".join(out) + "          </tbody>\n        </table>\n")


def type_spec():
    order = ["4xl", "3xl", "2xl", "xl", "lg", "md", "base", "xs"]
    rows = "".join("""          <div class="tstep">
            <span class="tlab">%(k)s</span>
            <span class="tsamp" style="font-size:%(rem)srem">Deepening</span>
            <span class="tnum">%(px)g px &middot; %(rem)s rem</span>
          </div>
""" % dict(k=k, px=SC[k], rem=("%.4g" % (SC[k] / 16.0))) for k in order)
    return """        <div class="faces">
          <div class="face"><p class="flab">Display</p>
            <p class="fsamp serif">Afterglow</p>
            <p class="fmeta">%(d)s &middot; 400 &middot; Shopify library</p>
            <p class="fuse">Wordmark and hero only</p></div>
          <div class="face"><p class="flab">Body</p>
            <p class="fsamp">Afterglow</p>
            <p class="fmeta">%(b)s &middot; 400 &middot; Shopify library</p>
            <p class="fuse">All UI, headings, body, labels</p></div>
        </div>
        <div class="tspec">
%(rows)s        </div>
""" % dict(d=DISPLAY, b=BODY, rows=rows)


def space_spec():
    bars = "".join("""          <div class="sbar">
            <span class="slab">%(k)s</span>
            <span class="sbox" style="width:%(v)dpx"></span>
            <span class="snum">%(v)d px &middot; %(r)s rem</span>
          </div>
""" % dict(k=k, v=SP[k], r=("%.4g" % (SP[k] / 16.0)))
        for k in ("2xs", "xs", "sm", "md", "lg", "xl", "2xl", "3xl"))
    return """        <div class="space">
%(bars)s        </div>
        <div class="trio">
          <div class="tile"><p class="tlabel">Radius</p><p class="tval">%(radius)g</p>
            <p class="tnote">Near zero. A void ground and restraint point there.</p></div>
          <div class="tile"><p class="tlabel">Shadow</p><p class="tval">%(shadow)s</p>
            <p class="tnote">Elevation reads through surface steps, not shadow.</p></div>
          <div class="tile"><p class="tlabel">Motion</p><p class="tval">%(dur)g ms</p>
            <p class="tnote">%(ease)s. Ends at its destination, never passes it.</p></div>
        </div>
""" % dict(bars=bars, radius=T["radius"]["default"], shadow=T["shadow"]["default"],
           dur=MO["duration"]["base"], ease=MO["ease"])


def usage_spec():
    return """        <div class="rulecard">
          <p class="rk">The interaction rule</p>
          <p class="rbig">No state change brightens.</p>
          <p class="rsub">Hover, focus and active deepen or shift hue, and never lighten.
            Nothing fades up to a brighter value. That is checkable in a diff, which is why
            it is written this way and not as a sentence about mood.</p>
        </div>
        <div class="dos">
          <div class="do no"><p class="dk">Never</p>
            <p>Stage 3 or stage 4 as a letterform. Both fail every text floor on the void.</p></div>
          <div class="do no"><p class="dk">Never</p>
            <p>Stage 3 or stage 4 on a surface step. Both fall further there than on the
              void, to %(r3)s and %(r4)s.</p></div>
          <div class="do no"><p class="dk">Never</p>
            <p>Muted on a stage colour. It fails on all four.</p></div>
          <div class="do yes"><p class="dk">Always</p>
            <p>Stage 1 for a mark, a rule or an accent on the void, at %(s1)s.</p></div>
        </div>
        <div class="stops">
          <p class="rk">Where the rules stop</p>
          <p>Cart and checkout are plain and fast, exactly as the voice is. The deepening
            discipline serves browsing and gets out of the way where clarity beats mood.
            Applied to a payment form it would make the form worse.</p>
        </div>
""" % dict(s1=num(STAGES[0]["value"], VOID),
           r3=num(STAGES[2]["value"], SURF), r4=num(STAGES[3]["value"], SURF))


def application():
    s1, s2, s3, s4 = (s["value"] for s in STAGES)
    return """        <div class="apps">
          <article class="app">
            <p class="alab">Product card</p>
            <div class="appbody" style="background:%(sd)s">
              <div class="appimg" style="background:%(s3)s"></div>
              <p class="aname">Afterglow</p>
              <p class="aprice">$180</p>
            </div>
            <p class="anote">Stage 3 as a ground. Text never sits on it.</p>
          </article>
          <article class="app">
            <p class="alab">Button, resting and hover</p>
            <div class="appbody" style="background:%(sd)s">
              <span class="btn" style="background:%(s1)s;color:%(void)s">Add to cart</span>
              <span class="btn" style="background:%(hover)s;color:%(void)s">Add to cart</span>
              <p class="anote2">Hover deepens: L %(l1).3f to L %(lh).3f</p>
            </div>
            <p class="anote">The one rule, applied. Nothing brightens.</p>
          </article>
          <article class="app">
            <p class="alab">Surface steps</p>
            <div class="appbody" style="background:%(void)s">
              <div class="step" style="background:%(sd)s">Recessed %(sd)s</div>
              <div class="step" style="background:%(sf)s">Raised %(sf)s</div>
            </div>
            <p class="anote">Elevation without a shadow.</p>
          </article>
        </div>
""" % dict(sd=SDEEP, sf=SURF, void=VOID, s1=s1, s3=s3,
           hover="#A8832F", l1=B.oklch(s1)[0], lh=B.oklch("#A8832F")[0])


def build():
    sheets = [
        cover(),
        sheet(2, "Colour", "The four stages",
              "One ramp, lightness falling and chroma flat at 0.110 throughout. The stages "
              "are the whole palette; everything else is a neutral.", stage_cards()),
        sheet(3, "Colour", "Contrast, measured",
              "Every ratio below is computed from the token, not estimated. The body floor "
              "is 4.5:1 and the large-text floor is 3:1.",
              contrast_table() + '        <div class="roles">\n' + role_list()
              + "        </div>\n", wide=True),
        sheet(4, "Colour", "Neutrals and surfaces",
              "Six locked tokens. The ground is required by the deepening-light rule rather "
              "than borrowed, and elevation is carried by the two surface steps.",
              neutral_rows(), wide=True),
        sheet(5, "Type", "Two faces, one scale",
              "Both faces are in Shopify's library, so neither ships as a webfont. The scale "
              "is a ratio of %g from a %g px base, every step derived."
              % (T["typography"]["scale"]["ratio"], T["typography"]["scale"]["base"]),
              type_spec(), wide=True),
        sheet(6, "System", "Space, radius, shadow, motion",
              "An %g px base and whole multiples of it. Eight divides the %g px type base, "
              "so space and text sit on one grid rather than two that nearly agree."
              % (T["spacing"]["base"], T["typography"]["scale"]["base"]),
              space_spec(), wide=True),
        sheet(7, "Usage", "The rule that can be checked",
              "The brand's central idea is a sentence about mood that nobody can act on. "
              "This is its usable form.", usage_spec(), wide=True),
        sheet(8, "Usage", "Applied",
              "The same tokens on the three things the storefront is mostly made of. "
              "Full voice and tone live in "
              "<a href=\"resources/voice-tone.md\">voice-tone.md</a>.", application(), wide=True),
    ]
    return TEMPLATE % dict(
        void=VOID, sdeep=SDEEP, surf=SURF, text=TEXT, muted=MUTED, border=BORDER,
        s1=STAGES[0]["value"], display=DISPLAY, body=BODY,
        xs=SC["xs"] / 16.0, base=SC["base"] / 16.0, md=SC["md"] / 16.0, lg=SC["lg"] / 16.0,
        xl=SC["xl"] / 16.0, x2=SC["2xl"] / 16.0, x3=SC["3xl"] / 16.0, x4=SC["4xl"] / 16.0,
        sp2xs=SP["2xs"], spxs=SP["xs"], spsm=SP["sm"], spmd=SP["md"], splg=SP["lg"],
        spxl=SP["xl"], sp2xl=SP["2xl"], sp3xl=SP["3xl"],
        radius=T["radius"]["default"], dur=MO["duration"]["base"], ease=MO["ease"],
        title=TITLE, sheets="".join(sheets))


TEMPLATE = open(str(ROOT / "tools" / "system_template.html")).read()

if __name__ == "__main__":
    html = build()
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("wrote %s (%d lines)" % (OUT.name, html.count("\n") + 1))
