# -*- coding: utf-8 -*-
"""Render brand/2026-10-07-afterglow-guidelines.html from design-tokens.json.

The document renders from the tokens rather than restating them, so a value can
only be wrong in one place. Every position in the fall is computed here from the
recorded ramp, never typed.
"""
import io
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import brand_audit as B

TOKENS = json.loads(io.open(ROOT / "brand" / "resources" / "design-tokens.json",
                            encoding="utf-8").read())
OUT = ROOT / "brand" / "2026-10-07-afterglow-guidelines.html"

C = TOKENS["color"]
STAGES = [C["stages"][str(n)] for n in (1, 2, 3, 4)]
RAMP = [s["value"] for s in STAGES]
VOID = C["ground"]["value"]
TEXT = C["text"]["value"]
MUTED = C["muted"]["value"]
TYPO = TOKENS["typography"]
SCALE = TYPO["scale"]["steps"]
SPACE = TOKENS["spacing"]["scale"]
MOTION = TOKENS["motion"]


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ground(t):
    """The fall at document position t, interpolated in sRGB the way an unprefixed
    CSS gradient interpolates."""
    t = max(0.0, min(1.0, t))
    stops = list(zip((0.0, 1 / 3.0, 2 / 3.0, 1.0), RAMP))
    for i in range(3):
        (p0, c0), (p1, c1) = stops[i], stops[i + 1]
        if p0 <= t <= p1:
            f = (t - p0) / (p1 - p0)
            a, b = _rgb(c0), _rgb(c1)
            return "#%02X%02X%02X" % tuple(
                int(round(a[j] + (b[j] - a[j]) * f)) for j in range(3))
    return RAMP[-1]


def solve(fn, target, rising=True):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2.0
        v = fn(m) if rising else -fn(m)
        if v < (target if rising else -target):
            lo = m
        else:
            hi = m
    return hi


# Rounded to the precision the document writes into data-at, so the ground computed
# here and the ground recomputed from the attribute are the same colour. Left at full
# bisection precision the two land either side of a .5 rounding and the document prints
# a hex one unit off the fall it claims to be reading.
CROSSOVER = round(solve(lambda t: B.contrast(TEXT, ground(t)), 4.5), 6)
# where dark and light display type read exactly the same, so the inversion
# never accepts a worse ratio than it must
_lo, _hi = 0.0, 1.0
for _ in range(60):
    _m = (_lo + _hi) / 2.0
    if B.contrast(VOID, ground(_m)) > B.contrast(TEXT, ground(_m)):
        _lo = _m
    else:
        _hi = _m
INVERSION = round(_hi, 6)


N_PAGES = 12

# Page numbers the copy cross-references. Named here so a reference cannot drift from
# the page it points at; build() asserts the page list agrees with them.
P_SURFACE, P_ROLES, P_TYPE, P_SPACING, P_USAGE, P_VOICE = 7, 8, 9, 10, 11, 12


def page_of(t):
    """Document position t as (page index, position within that page). The fall is
    indexed to pages, so a page that runs long deepens over its own length."""
    idx = min(N_PAGES - 1, int(t * N_PAGES))
    return idx, t * N_PAGES - idx


def ratio(fg, bg):
    """A printed ratio carries the two colours it was computed from, so the audit can
    recompute it instead of trusting it."""
    return ('<b class="num" data-fg="%s" data-bg="%s">%.2f:1</b>'
            % (fg.upper(), bg.upper(), B.contrast(fg, bg)))


def ok_text(fg, bg, large=False):
    floor = 3.0 if large else 4.5
    r = B.contrast(fg, bg)
    return "clears %s:1" % ("3" if large else "4.5") if r >= floor else "fails %s:1" % (
        "3" if large else "4.5")


def ledger_row(at, kicker, pairs, note, anchored=True, swatch=None, style="",
               doc_at=None):
    """`at` is the row's position inside its own page. `doc_at` is the same value as a
    fraction of the whole document, which is what the narrow note reports."""
    rows = "".join("<dt>%s</dt><dd>%s</dd>" % (k, v) for k, v in pairs)
    sw = ('<span class="lsw" style="background:%s"></span>' % swatch) if swatch else ""
    attrs = ' data-at="%.6f"' % at if anchored else ""
    if doc_at is None:
        doc_at = at
    # a row centred on t=0 or t=1 would hang half off the column
    edge = " first" if at <= 0.001 else (" last" if at >= 0.999 else "")
    return ("""      <div class="lrow%s"%s style="--at:%.6f;%s">
        <p class="lk">%s%s</p>
        <dl>%s</dl>
        <p class="lnote wide">%s</p>%s
      </div>\n""" % (("" if not anchored else " anchored") + edge, attrs, at, style,
                     sw, kicker, rows, note,
                     ('\n        <p class="lnote narrow">The fall reaches this value at '
                      '%.1f per cent of the document.</p>' % (doc_at * 100)) if anchored else ""))


def stage_row(i):
    for j, st in enumerate(STAGES):
        if j != i:
            continue
        doc_at = (0.0, 1 / 3.0, 2 / 3.0, 1.0)[i]
        at = page_of(doc_at)[1]
        hexv = st["value"]
        o = st["oklch"]
        role = ("Text, marks and rules on the void",
                "Large text or fills. Borderline as text",
                "Ground, never a letterform",
                "Ground, never a letterform")[i]
        return ledger_row(
            at, "Stage %d &middot; %s" % (i + 1, st["name"]),
            [("Hex", hexv),
             ("OKLCH", "%.3f &nbsp;%.3f &nbsp;%.1f" % (o["l"], o["c"], o["h"])),
             ("On void", ratio(hexv, VOID)),
             ("Text on it", ratio(TEXT, hexv)),
             ("Role", role)],
            "Read off the ground at this line, where the fall passes through it.",
            swatch=hexv, doc_at=doc_at)
    return ""


def crossover_row():
    g = ground(CROSSOVER)
    return ledger_row(
        page_of(CROSSOVER)[1], "Crossover",
        [("Ground", g),
         ("OKLCH L", "%.3f" % B.oklch(g)[0]),
         ("Text on it", ratio(TEXT, g))],
        "The first position in the document that carries body copy.",
        swatch=g, doc_at=CROSSOVER)


def surface_rows():
    """The six neutrals are not on the ramp, so they cannot be read off the ground.
    They are specified in the ledger itself, which is the void."""
    items = [
        (0.20, "Ground", C["ground"], None),
        (0.45, "Surface, recessed", C["surface-deep"], C["surface-deep"]["value"]),
        (0.70, "Surface, raised", C["surface"], C["surface"]["value"]),
    ]
    out = []
    for at, label, tok, bg in items:
        v = tok["value"]
        out.append(ledger_row(
            at, label,
            [("Hex", v),
             ("OKLCH L", "%.3f" % B.oklch(v)[0]),
             ("Text on it", ratio(TEXT, v)),
             ("Muted on it", ratio(MUTED, v)),
             ("Use", tok.get("use", ""))],
            "Not on the ramp, so it is read off this column rather than the page.",
            anchored=False, swatch=v,
            style=("background:%s;" % bg) if bg else ""))
    return "".join(out)


def statement(text, cls="statement"):
    return '          <p class="%s">%s</p>\n' % (cls, text)


def stagemark(text):
    return '          <p class="stagemark">%s</p>\n' % text


def sec(folio, title, inner):
    """A specification page's heading block. The folio is the page number, which is the
    document's only number, so a cross-reference cannot drift from what it points at."""
    return ("""          <p class="secnum">%02d</p>
          <h2 class="sechead">%s</h2>
%s""" % (folio, title, inner))


def p(text, cls="copy"):
    return '          <p class="%s">%s</p>\n' % (cls, text)


def spec_pages():
    """Everything below the crossover, where the fall carries body copy for the rest
    of the document and keeps deepening."""
    g_cross = ground(CROSSOVER)
    sd, sf = C["surface-deep"]["value"], C["surface"]["value"]
    d_fam, b_fam = TYPO["display"]["family"], TYPO["body"]["family"]
    sc = TYPO["scale"]
    out = []

    out.append(sec(P_SURFACE, "The surface map", "".join([
        p("Void is the page. %s is recessed, %s is raised, and the hairline is the border "
          "token at %s. Shadow is absent from this list on purpose: on a void ground, "
          "elevation reads through the surface steps, because a shadow has nothing to fall on."
          % (sd, sf, C["border"]["value"])),
        p("Those three are not on the ramp, so they cannot be read off the page the way a "
          "stage can. They are specified "
          '<span class="wide-only">in the column to the right</span>'
          '<span class="narrow-only">in the readings below</span>'
          ", which is the void and steps through them, so the family is demonstrated by "
          "the thing reporting it."),
    ])))

    roles = "".join(
        """          <div class="role">
            <p class="rolename">%s</p>
            <p class="rolerule">%s</p>
            <p class="rolemeas">On void %s &middot; %s &middot; text on it %s</p>
          </div>\n""" % (
            st["name"], rule,
            ratio(st["value"], VOID), ok_text(st["value"], VOID, large=True),
            ratio(TEXT, st["value"]))
        for st, rule in zip(STAGES, [
            "Light enough to set as text, a mark or a rule on the void.",
            "Large text or fills. Borderline as running text and not to be used as it.",
            "Fills, grounds and large shapes. Never a letterform.",
            "Fills, grounds and large shapes. Never a letterform."]))
    out.append(sec(P_ROLES, "Stage roles", "".join([
        p("A ramp whose lightness falls monotonically cannot carry text at both ends. The "
          "later stages land near 2:1 and 1.4:1 on the void, which is not a flaw in the rule, "
          "it is what the rule implies. The failing numbers are printed because they are the "
          "reason for the restriction."),
        '          <div class="roles">\n' + roles + "          </div>\n",
    ])))

    specimen = "".join(
        """          <div class="tstep">
            <span class="tlabel">%s</span>
            <span class="tsample" style="font-size:%grem">Deepening</span>
            <span class="tmeta">%g px &middot; %.4g rem</span>
          </div>\n""" % (name, sc["steps"][name] / 16.0, sc["steps"][name],
                         sc["steps"][name] / 16.0)
        for name in ("xs", "base", "md", "lg", "xl", "2xl"))
    out.append(sec(P_TYPE, "Type", "".join([
        p("Display is %s, body is %s. Both are in Shopify's font library, so neither ships as "
          "a webfont; the cost is one added font picker, since the theme carries exactly one."
          % (d_fam, b_fam)),
        p("The scale is a ratio, not a list. Base %g px, ratio %g, every step derived. This "
          "section is set in those faces at those sizes, so it is a specimen of itself."
          % (sc["base"], sc["ratio"])),
        '          <div class="tspec">\n' + specimen + "          </div>\n",
    ])))

    out.append(sec(P_SPACING, "Spacing, radius, shadow, motion", "".join([
        p("Spacing is an %g px base and whole multiples of it: %s. Eight divides the %g px "
          "type base, so space and text sit on one grid rather than two that nearly agree."
          % (TOKENS["spacing"]["base"],
             ", ".join(str(SPACE[k]) for k in ("2xs", "xs", "sm", "md", "lg", "xl", "2xl", "3xl")),
             sc["base"])),
        p("Radius is %g. Shadow is %s. Motion runs at %g ms on %s, a curve that ends at its "
          "destination and never passes it, which is what deepening rather than snapping means "
          "in a timing function."
          % (TOKENS["radius"]["default"], TOKENS["shadow"]["default"],
             MOTION["duration"]["base"], MOTION["ease"])),
    ])))

    out.append(sec(P_USAGE, "Usage", "".join([
        p("The brand's central idea is a sentence about mood that nobody can act on: the light "
          "only ever deepens. The usable form is an interaction rule."),
        p("No state change brightens. Hover, focus and active deepen or shift hue, and never "
          "lighten. Nothing fades up to a brighter value. That is checkable in a diff, which "
          "is the main reason this document is worth having.", "rule"),
        p("Stages three and four are never letterforms. Stage two is not running text. Those "
          "are not preferences; the measured ratios on page %02d are the reason." % P_ROLES),
        p("Where the rules stop. Cart and checkout are plain and fast, and the atmosphere stops "
          "there on purpose, exactly as the voice does. The deepening discipline serves "
          "browsing and gets out of the way where clarity beats mood. Applied to a payment "
          "form it would make the form worse."),
    ])))

    out.append(sec(P_VOICE, "Voice", "".join([
        p("Unhurried and physical. It names heat, light, breath and skin. It describes a "
          "sequence, because the product is a sequence. Certain without pushing: the brand "
          "does not argue for itself, and assumes you will understand it if you are shown it "
          "in the right order."),
        p("The full voice, the word lists and the tone by context live in "
          "<a href=\"resources/voice-tone.md\">voice-tone.md</a>, which this document does not "
          "duplicate."),
    ])))

    return out


def pages():
    """The twelve pages, in order. Six state and six specify, and the crossover falls
    on the turn between them because it sits at exactly 50 per cent of the fall."""
    s1, s2 = STAGES[0], STAGES[1]
    gold_ratio = B.contrast(TEXT, RAMP[0])
    specs = spec_pages()

    out = [
        dict(tone="dark", folio=None,
             inner=('          <h1 class="wordmark">Afterglow</h1>\n'
                    + stagemark("Stage one. %s." % s1["name"])),
             rows=stage_row(0)),
        dict(tone="dark", folio=None,
             inner=statement("One fragrance told in four stages, from the gold of last "
                             "light to deep violet. You do not see the bottle until the end."),
             rows=""),
        dict(tone="dark", folio=None,
             inner=statement("The light only ever deepens, never brightens."),
             rows=""),
        dict(tone="dark", folio=None,
             inner=statement("This page is obeying that rule. The ground beneath this page "
                             "is darker than the ground you started on, and it will not "
                             "return.", "statement quiet"),
             rows=""),
        dict(tone="dark", folio=None,
             inner=stagemark("Stage two. %s." % s2["name"]),
             rows=stage_row(1)),
        dict(tone="dark", folio=None,
             inner=statement("Below this turn the ground carries body copy. Above it nothing "
                             "does: primary text reads %.2f:1 on the gold end and fails even "
                             "the large-text floor, so everything so far is set in the void "
                             "and sized as display." % gold_ratio, "statement quiet"),
             rows=""),
    ]

    rows_for = {P_SURFACE: crossover_row() + surface_rows(),
                P_TYPE: stage_row(2),
                P_VOICE: stage_row(3)}
    for n, inner in zip((P_SURFACE, P_ROLES, P_TYPE, P_SPACING, P_USAGE, P_VOICE), specs):
        out.append(dict(tone="light", folio=n, inner=inner, rows=rows_for.get(n, "")))

    assert len(out) == N_PAGES, "page list is %d long, N_PAGES is %d" % (len(out), N_PAGES)
    for i, pg_ in enumerate(out):
        if pg_["folio"] is not None:
            assert pg_["folio"] == i + 1, ("page %d carries folio %02d"
                                           % (i + 1, pg_["folio"]))
    # the inversion must land on a page turn, which is the whole reason for twelve
    idx, frac = page_of(CROSSOVER)
    assert frac == 0.0 and idx == N_PAGES // 2, (
        "crossover at %.6f falls %.4f into page %d, not on a turn" % (CROSSOVER, frac, idx + 1))
    return out


def build():
    out = []
    for i, page in enumerate(pages()):
        g0 = ground(i / float(N_PAGES))
        g1 = ground((i + 1) / float(N_PAGES))
        # The crossover is drawn on the turn it happens at, not at a percentage of a
        # scroll. page_of() has already asserted that turn is a page boundary.
        xo = ("" if i != page_of(CROSSOVER)[0] else
              '      <div class="crossover" aria-hidden="true">\n'
              '        <em>Body copy may begin</em><span></span><em>%.2f:1</em>\n'
              '      </div>\n' % B.contrast(TEXT, ground(CROSSOVER)))
        out.append(
            '    <section class="page %s" data-page="%02d" style="--g0:%s;--g1:%s">\n'
            '%s'
            '      <main class="measure">\n%s      </main>\n'
            '      <aside class="ledger" aria-hidden="true">\n%s      </aside>\n'
            '      <nav class="rail" aria-label="Position in the fall">\n'
            '        <b class="rm"><i>Page</i>%02d / %02d<u>%.3f L</u></b>\n'
            '        <span class="tick"></span>\n'
            '      </nav>\n'
            '    </section>\n'
            % (page["tone"], i + 1, g0, g1, xo, page["inner"], page["rows"],
               i + 1, N_PAGES, B.oklch(g0)[0]))
    body = "".join(out)

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Afterglow Brand Guidelines</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">
<style>
  /* Generated by tools/build_guidelines.py from brand/resources/design-tokens.json.
     Do not edit by hand: every value here is rendered from a recorded token, and the
     positions in the fall are computed from the ramp rather than typed.

     The fall runs %(s1)s to %(s4)s over the whole document and never resets.
     Crossover, where %(text)s first clears 4.5:1 on the ground: %(xo).2f%%.
     Inversion, where dark and light display type read alike at %(inv_ratio).2f:1: %(inv).2f%%. */
  :root{
    --void:%(void)s; --surface-deep:%(sdeep)s; --surface:%(surface)s;
    --text:%(text)s; --muted:%(muted)s; --border:%(border)s;
    --s1:%(s1)s; --s2:%(s2)s; --s3:%(s3)s; --s4:%(s4)s;
    --display:'%(display)s',Georgia,serif;
    --body:'%(body_face)s',system-ui,sans-serif;
    --xs:%(xs)srem; --base:%(base)srem; --md:%(md)srem; --lg:%(lg)srem;
    --xl:%(xl)srem; --x2:%(x2)srem; --x3:%(x3)srem; --x4:%(x4)srem;
    --sp-2xs:%(sp2xs)spx; --sp-xs:%(spxs)spx; --sp-sm:%(spsm)spx; --sp-md:%(spmd)spx;
    --sp-lg:%(splg)spx; --sp-xl:%(spxl)spx; --sp-2xl:%(sp2xl)spx; --sp-3xl:%(sp3xl)spx;
    --radius:%(radius)spx; --shadow:%(shadow)s;
    --dur:%(dur)sms; --ease:%(ease)s;
    --gut:clamp(20px,4vw,64px); --rail:92px; --ledger:clamp(190px,25%%,296px);
  }
  *{box-sizing:border-box}
  /* Proximity, never mandatory. A page is a minimum of one screen and the
     specification pages run longer, and mandatory snapping on a container taller than
     the viewport pulls the reader back off content they are still reading. Proximity
     only decides where a free scroll comes to rest. */
  html{-webkit-text-size-adjust:100%%;scroll-snap-type:y proximity;
    scroll-behavior:smooth}
  @media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
  body{margin:0;background:var(--void);color:var(--text);
    font-family:var(--body);font-weight:%(w_body)s;font-size:var(--base);line-height:%(lead_body)s}

  /* The slug. Fixed, on the void, outside the fall. It replaces a four-field footer
     because the rail already carries position and two indicators would compete. */
  .slug{position:fixed;top:0;left:0;z-index:5;display:flex;gap:var(--sp-sm);
    align-items:baseline;padding:var(--sp-sm) var(--gut);background:var(--void);
    font-size:var(--xs);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
    border-bottom:1px solid var(--border);border-right:1px solid var(--border)}
  .slug b{color:var(--text);font-weight:400}

  .doc{position:relative}

  /* The fall, cut into %(npages)d pages. Each page carries the slice of the ramp from its
     own start to its own end, so page N opens on exactly the value page N-1 closed on.
     The ramp is indexed to pages rather than to pixels: a page that runs longer than a
     screen deepens over its own length instead of faster than its neighbours. */
  .page{position:relative;display:grid;
    grid-template-columns:minmax(0,1fr) var(--ledger) var(--rail);
    min-height:100svh;scroll-snap-align:start;
    background:linear-gradient(180deg,var(--g0) 0%%,var(--g1) 100%%)}

  /* A page is a minimum of one screen, never a maximum. Clipping to the viewport
     would silently cut the specification pages, which are the longest. */
  .measure{grid-column:1;display:flex;flex-direction:column;gap:var(--sp-2xl);
    justify-content:center;padding:calc(var(--sp-3xl) * 1.5) var(--gut)}

  /* Above the turn every value is set in the void; below it the ground carries
     primary. Which half a page is in is a measured fact, not a preference. */
  .page.dark{color:var(--void)}
  .page.light{color:var(--text)}
  .page.light .measure{justify-content:flex-start;gap:0}

  /* Above the crossover every value is set in the void. Primary text reads 1.70:1 on
     the gold end and fails even the large-text floor, so dark is not a preference. */
  .wordmark{font-family:var(--display);font-weight:400;margin:0;
    font-size:clamp(var(--x3),11vw,8rem);line-height:1;letter-spacing:%(track_wm)s}
  .statement{font-family:var(--display);font-weight:400;margin:0;
    font-size:clamp(var(--xl),5vw,var(--x4));line-height:%(lead_disp)s;
    letter-spacing:%(track_disp)s;max-width:21ch}
  .statement.quiet{font-size:clamp(var(--lg),3vw,var(--x2));max-width:30ch}
  .stagemark{font-family:var(--display);font-weight:400;margin:0;
    font-size:var(--xl);line-height:%(lead_disp)s;letter-spacing:%(track_disp)s}

  /* Below it the ground carries primary for the rest of the document. Muted never
     appears on the fall: it fails at every position, so the void column is its only home. */
  .secnum{font-size:var(--xs);letter-spacing:.18em;margin:0 0 var(--sp-xs);
    font-variant-numeric:tabular-nums}
  .sechead{font-family:var(--display);font-weight:400;font-size:var(--x2);
    line-height:%(lead_disp)s;letter-spacing:%(track_disp)s;margin:0 0 var(--sp-lg)}
  .copy{max-width:58ch;margin:0 0 var(--sp-lg)}
  .rule{border-left:2px solid var(--s1);padding-left:var(--sp-md);max-width:54ch}

  .roles{display:flex;flex-direction:column;gap:var(--sp-lg);margin-top:var(--sp-lg)}
  .role{border-top:1px solid var(--border);padding-top:var(--sp-sm)}
  .rolename{font-family:var(--display);font-size:var(--lg);margin:0 0 4px}
  .rolerule{margin:0 0 6px;max-width:48ch}
  .rolemeas{margin:0;font-size:var(--xs);font-variant-numeric:tabular-nums}

  .tspec{display:flex;flex-direction:column;gap:var(--sp-sm);margin-top:var(--sp-lg);
    border-top:1px solid var(--border);padding-top:var(--sp-lg)}
  .tstep{display:grid;grid-template-columns:56px minmax(0,1fr) auto;
    gap:var(--sp-md);align-items:baseline}
  .tlabel{font-size:var(--xs);letter-spacing:.14em;text-transform:uppercase}
  .tsample{line-height:1.1}
  .tmeta{font-size:var(--xs);white-space:nowrap;font-variant-numeric:tabular-nums}

  /* The ledger. A void column carrying the document's readings, each row anchored to
     the position of the value it describes. Empty until Task 7 fills it. */
  .ledger{grid-column:2;position:relative;background:var(--void);
    border-left:1px solid var(--border)}
  .page:not(:first-child) .ledger{border-top:1px solid var(--border)}

  /* A row carries its own void ground. On the wide layout it sits over the ledger
     column, which is the same colour; at 390px the column is gone and the row brings
     the void with it, which is the only way its labels stay readable on the fall. */
  /* Anchored to its position inside its own page, which is where the fall actually
     reaches the value the row reports. */
  .lrow{position:absolute;left:calc(100%% - var(--rail) - var(--ledger));
    width:var(--ledger);top:calc(var(--at) * 100%%);background:var(--void);
    transform:translateY(-50%%);padding:var(--sp-sm) var(--sp-md)}
  .lrow.first{transform:none;top:var(--sp-md)}
  .lrow.last{transform:none;top:auto;bottom:var(--sp-md)}
  /* Unanchored rows are not readings off the ground, so they are not positioned
     against it. They stack in the column, clear of whatever is anchored above. */
  .lrow.anchored + .lrow:not(.anchored){margin-top:calc(var(--sp-3xl) * 4)}
  .lrow:not(.anchored){position:static;width:auto;transform:none;
    margin:var(--sp-lg) var(--sp-sm);padding:var(--sp-sm) var(--sp-md);
    border:1px solid var(--border)}
  /* The leader joins the row to the ground it was read from. */
  .lrow.anchored::before{content:"";position:absolute;left:0;top:50%%;
    width:var(--sp-md);height:1px;background:var(--s1);transform:translateX(-100%%)}
  .lrow.anchored.first::before{top:var(--sp-lg)}
  .lrow.anchored.last::before{top:auto;bottom:var(--sp-lg)}
  .lk{display:flex;align-items:center;gap:8px;margin:0 0 6px;font-size:var(--xs);
    letter-spacing:.12em;text-transform:uppercase;color:var(--s1);line-height:1.3}
  .lsw{flex:0 0 12px;width:12px;height:12px}
  .lrow dl{display:grid;grid-template-columns:92px minmax(0,1fr);gap:4px 10px;
    margin:0;font-size:var(--xs);line-height:1.45}
  .lrow dt{color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
  .lrow dd{margin:0;color:var(--text);font-variant-numeric:tabular-nums}
  .lnote{margin:6px 0 0;font-size:var(--xs);line-height:1.45;color:var(--muted);max-width:28ch}
  /* "Read off the ground at this line" is true only while the row is at that line.
     Inline, it is not, so the row names its own position instead. */
  .lnote.narrow{display:none}
  /* The same problem as the ledger note, in running copy: a sentence that points at a
     column is false on a layout that has no column. */
  .narrow-only{display:none}

  /* The rail. A void strip outside the ledger, one per page. It is the folio, and it
     reads both numbers a paged document has: which page, and how dark that page opens.
     The lightness is still the point; the page number exists now because pages do. */
  .rail{grid-column:3;position:relative;background:var(--void);
    border-left:1px solid var(--border)}
  .page:not(:first-child) .rail{border-top:1px solid var(--border)}
  .rm{position:sticky;top:var(--sp-md);display:block;padding-right:var(--sp-sm);
    text-align:right;font-size:var(--xs);
    font-variant-numeric:tabular-nums;color:var(--text);font-weight:400;line-height:1.3}
  .rm i{font-style:normal;display:block;font-size:%(tiny)srem;letter-spacing:.12em;
    text-transform:uppercase;color:var(--muted);margin-bottom:2px}
  .rm u{text-decoration:none;color:var(--muted);display:block;margin-top:2px}
  .rail .tick{position:absolute;right:0;top:0;width:9px;height:1px;background:var(--s1)}
  /* A single bar across the top, filling as the reader descends. It replaces the
     sticky indicator the one-page document needed: the rail mark now names the page. */
  .marker{position:fixed;top:0;left:0;height:3px;width:0;background:var(--s1);
    opacity:1;z-index:6}
  @supports (animation-timeline:scroll()){
    .marker{animation:railfill linear both;animation-timeline:scroll(root block)}
  }

  /* The crossover. The one horizontal rule in the document that is not a section
     boundary, drawn where the fall first carries body copy. */
  /* Drawn on the turn into the page it opens, which is where the inversion happens. */
  .crossover{position:absolute;left:0;top:0;transform:translateY(-50%%);
    width:calc(100%% - var(--rail) - var(--ledger));
    display:flex;align-items:center;gap:var(--sp-sm);padding-inline:var(--gut);
    pointer-events:none}
  .crossover span{flex:1;height:1px;background:rgba(238,236,234,.45)}
  .crossover em{font-style:normal;font-size:var(--xs);letter-spacing:.14em;
    text-transform:uppercase;color:var(--text);white-space:nowrap}

  /* Underlined by text-decoration rather than a border, so the vertical padding that
     brings the tap target past 44px does not drag the rule away from the text. Padding on
     an inline box grows the hit area without changing the line it sits in. */
  a{color:var(--s1);text-decoration:underline;text-underline-offset:3px;
    text-decoration-thickness:1px;text-decoration-color:rgba(216,178,96,.45);
    padding-block:14px;
    transition:color var(--dur) var(--ease),text-decoration-color var(--dur) var(--ease)}
  a:hover,a:focus-visible{color:%(link_hover)s;text-decoration-color:rgba(168,131,47,.45)}

  @media (max-width:860px){
    .page{grid-template-columns:1fr}
    /* A page stops being a screen it has to fill and becomes a screen it has to clear:
       at this width the specification pages all run long, and centring short ones on a
       tall phone screen would strand the heading below the fold. */
    .measure{justify-content:flex-start;
      padding:calc(var(--sp-2xl) * 1.5) var(--gut) calc(var(--sp-2xl) * 2)}
    /* The ledger stops being a column. Its rows move inline, directly under the
       passage they annotate, each carrying the void with it. */
    /* The slug stops being fixed so it does not eat a short viewport, and loses its
       second field, which the document title already carries in the tab. */
    .slug{position:static;border-right:0}
    .slug span{display:none}
    /* The column goes, the readings do not. Hiding the ledger here hid every row
       with it, which is the one thing the narrow layout must not do. */
    .ledger{grid-column:1;position:static;background:transparent;border-left:0;
      border-top:0;padding:0 var(--gut) var(--sp-2xl)}
    .lrow,.lrow:not(.anchored){position:static;width:auto;transform:none;border:0;
      margin:var(--sp-lg) 0;padding:var(--sp-md)}
    .lrow.anchored + .lrow:not(.anchored){margin-top:var(--sp-lg)}
    .lrow.first,.lrow.last{position:static;transform:none;top:auto;bottom:auto}
    /* An inline row is no longer at the height of the value it describes, so a leader
       would point at nothing. It is dropped, and the row names its position instead. */
    .lrow.anchored::before{display:none}
    .lnote.wide{display:none}
    .lnote.narrow{display:block}
    .wide-only{display:none}
    .narrow-only{display:inline}
    .lrow dl{grid-template-columns:auto minmax(0,1fr)}
    /* The rail stops being a column. Its mark moves to the head of the page it
       belongs to, where it still reads the page and the lightness; the fixed bar at
       the top of the window carries progress. */
    .rail{grid-column:1;grid-row:1;position:static;border-left:0;border-top:0;
      background:transparent}
    .rail .tick{display:none}
    .rm{position:static;text-align:left;padding:var(--sp-md) var(--gut) 0;
      color:var(--muted)}
    .rm u{display:inline;margin-left:4px}
    .crossover{width:100%%}
  }
  @media (prefers-reduced-motion:reduce){
    a{transition:none}
  }

  /* Print resolves the ground to its value at each page's own position, so the
     printed artifact carries the same fall as the screen one. Nothing here sets a
     lighter value: a print stylesheet that reintroduced a white page would break the
     brand's central rule in the one place nobody looks. */
  @keyframes railfill{from{width:0}to{width:100%%}}

  @page{margin:0;size:Letter}
  @media print{
    html{scroll-snap-type:none}
    /* One page of the document is one sheet. The fall is already cut at exactly these
       boundaries, so the printed artifact and the screen one break in the same places
       and carry the same values at the same points. */
    .page{min-height:auto;break-after:page;page-break-after:always}
    .page:last-child{break-after:auto;page-break-after:auto}
    .measure{justify-content:flex-start;padding:var(--sp-lg) var(--gut) var(--sp-md)}
    .slug{position:static;border-right:0}
    /* a sticky marker has no meaning on a fixed page */
    .marker{display:none}
    /* An absolutely positioned row does not paginate: it is laid out against a
       container spanning every sheet, so break-inside cannot hold it together and two
       of them straddled a boundary. In print the ledger goes inline, exactly as it
       does at 390px, and each row sits with the passage it annotates. */
    .page{grid-template-columns:minmax(0,1fr) 0 var(--rail)}
    /* A page of the document is a sheet of paper. A stack of readings pushed three of
       them onto a second sheet, and a page spread over two sheets halves the rate its
       slice of the fall descends, which is what put a flat band over an inch. The
       readings go across instead of down, and every page fits its sheet. */
    .ledger{grid-column:1;position:static;background:transparent;border-left:0;
      border-top:0;padding:0 var(--gut) var(--sp-lg);
      display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
      gap:var(--sp-md);align-items:start}
    .lrow.anchored{grid-column:1 / -1}
    .lnote{max-width:none}
    /* the role list is the last thing standing between page 08 and its sheet */
    .roles{gap:var(--sp-sm);margin-top:var(--sp-md)}
    .rm{position:static}
    .lrow,.lrow:not(.anchored){position:static;width:auto;transform:none;border:0;
      margin:0;padding:var(--sp-sm) 0}
    .lrow.first,.lrow.last{position:static;transform:none;top:auto;bottom:auto}
    .lrow.anchored::before{display:none}
    .lnote.wide{display:none}
    .lnote.narrow{display:block}
    .wide-only{display:none}
    .narrow-only{display:inline}
    .crossover{width:calc(100%% - var(--rail))}
    /* a reading split across two sheets loses the thing it demonstrates */
    .lrow,.role,.tstep,.crossover{break-inside:avoid;page-break-inside:avoid}
    .sechead{break-after:avoid;page-break-after:avoid}
  }
</style>
</head>
<body>

  <div class="slug"><b>Afterglow</b><span>Brand Guidelines</span></div>

  <span class="marker" aria-hidden="true"></span>

  <div class="doc">
%(body)s  </div>

</body>
</html>
""" % dict(
        void=VOID, sdeep=C["surface-deep"]["value"], surface=C["surface"]["value"],
        text=TEXT, muted=MUTED, border=C["border"]["value"],
        s1=RAMP[0], s2=RAMP[1], s3=RAMP[2], s4=RAMP[3],
        display=TYPO["display"]["family"], body_face=TYPO["body"]["family"],
        xs=SCALE["xs"] / 16.0, base=SCALE["base"] / 16.0, md=SCALE["md"] / 16.0,
        lg=SCALE["lg"] / 16.0, xl=SCALE["xl"] / 16.0, x2=SCALE["2xl"] / 16.0,
        x3=SCALE["3xl"] / 16.0, x4=SCALE["4xl"] / 16.0,
        tiny=round(SCALE["xs"] / 16.0 * 0.82, 4),
        sp2xs=SPACE["2xs"], spxs=SPACE["xs"], spsm=SPACE["sm"], spmd=SPACE["md"],
        splg=SPACE["lg"], spxl=SPACE["xl"], sp2xl=SPACE["2xl"], sp3xl=SPACE["3xl"],
        radius=TOKENS["radius"]["default"], shadow=TOKENS["shadow"]["default"],
        dur=MOTION["duration"]["base"], ease=MOTION["ease"],
        lead_body=TYPO["leading"]["body"], lead_disp=TYPO["leading"]["display"],
        w_body=TYPO["body"]["weight"], w_display=TYPO["display"]["weight"],
        track_disp=TYPO["tracking"]["display"], track_wm=TYPO["tracking"]["wordmark"],
        xo=CROSSOVER * 100.0, xo_frac=CROSSOVER,
        xo_ratio=B.contrast(TEXT, ground(CROSSOVER)),
        inv=INVERSION * 100.0, inv_ratio=B.contrast(TEXT, ground(INVERSION)),
        link_hover="#A8832F", npages=N_PAGES,
        body=body)


if __name__ == "__main__":
    html = build()
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("wrote %s (%d lines)" % (OUT.name, html.count("\n") + 1))
    idx, frac = page_of(CROSSOVER)
    print("%d pages  crossover %.3f%% (page %02d, %.4f in)  inversion %.3f%%"
          % (N_PAGES, CROSSOVER * 100, idx + 1, frac, INVERSION * 100))
    for i in range(N_PAGES):
        print("  page %02d  %s to %s  L %.3f to %.3f"
              % (i + 1, ground(i / float(N_PAGES)), ground((i + 1) / float(N_PAGES)),
                 B.oklch(ground(i / float(N_PAGES)))[0],
                 B.oklch(ground((i + 1) / float(N_PAGES)))[0]))
