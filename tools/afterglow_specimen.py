"""The Afterglow guide as a set of specimens (spec docs/superpowers/specs/2026-10-12-afterglow-guide-specimen-design.md).

Takes the deck density_b_family builds for b1 as its source. Each sheet keeps its opening tag (ground, classes), its running
head and its hour; only its body is replaced, by one centred object, a caption and a tag. Nothing is retyped: whatever
leaves a sheet is moved as markup to the reference sheets at the back, and lost_strings proves no string was lost
against the deck as committed before this work (BASE_REF).
"""
import html as H
import re

import density_b_family as B
import density_directions as D

BASE_REF = "4c88531"   # the hour, committed: the word-for-word source
# the only strings that change; every other string of the BASE_REF deck must survive somewhere in the new one
REWRITES = {
    "There is no drawn logotype. The wordmark is Instrument Serif, widened to 150%.":
        "The mark is three triangles: the bottle, the A and the G. The wordmark is Instrument Serif, widened to 150%.",
    "One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark.":
        "One fragrance in four stages, from 19:12 until it is dark.",
}
MARK_MIN = 48   # px wide: below this the A and the G stop reading


def mark_svg(width, ink="light"):
    """The approved mark, inline, at width px. Never redrawn: the brand file is the source."""
    assert width >= MARK_MIN, f"the mark is never used below {MARK_MIN} px wide, asked for {width}"
    svg = (D.ROOT / f"brand/mark/afterglow-mark-{ink}.svg").read_text().strip()
    return svg.replace("<svg ", f'<svg class="amark" width="{width}" height="{round(width * 190 / 300)}" role="img" aria-label="Afterglow" ', 1)


def _squash(s):
    return re.sub(r"\s+", " ", H.unescape(s)).strip()


def texts(html):
    """The visible text strings of a page, in order: no head, scripts or styles; entities unescaped, whitespace collapsed."""
    html = re.sub(r"<head>.*?</head>|<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    return [t for t in (_squash(x) for x in re.findall(r">([^<>]+)<", html)) if t]


def lost_strings(old, new):
    """Every string of old that new no longer carries; the REWRITES sentences are exempt."""
    have = " ".join(texts(new))
    out = []
    for s in texts(old):
        for k in REWRITES:
            s = s.replace(k, "").strip()
        if s and s not in have:
            out.append(s)
    return out


def sections(html):
    return re.findall(r'<section class="sheet.*?</section>', html, flags=re.S)


def body_of(section):
    a = section.index(">") + 1
    return section[a:section.index('<footer class="foot"')]


def with_body(section, body):
    """The sheet with its opening tag and running head kept, and everything else replaced by body."""
    a = section.index(">") + 1
    return section[:a] + body + section[section.index('<footer class="foot"'):]


# ---- the sheet grammar (spec §3): one object centred both ways, an 18 px caption, an 11 px tag ----
SPEC_CSS = """
  /* the specimen sheets: one object, centred both ways; the running head above it, the tag at the foot */
  .deck .sheet.spc{display:flex;flex-direction:column}
  .spc .obj{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;min-height:0;text-align:center}
  .spc .cap{margin:0;font:400 18px/1.35 'Instrument Serif',Georgia,serif;letter-spacing:0;max-width:34ch}
  .deck .sheet .foot span{font-size:11px}  /* spec §5: the running head and the tags share one size */
  .spc .cap.wide{max-width:56ch}  /* 02's caption is fixed copy, 107 characters: two lines at this measure */
  .spc .tag{margin:0 0 var(--sp-md);font:400 11px/1.4 'Space Grotesk',system-ui,sans-serif;letter-spacing:.13em;text-transform:uppercase;align-self:flex-start}
  .spc figure{margin:0;overflow:hidden;flex:none}
  .spc figure img{display:block;width:100%;height:100%;object-fit:cover}
  /* the colour pages: five frames as one strip, lead first, aligned on their feet */
  .strip{display:flex;align-items:flex-end;gap:16px}
  .strip .lead{width:min(300px,20.8vw);aspect-ratio:4/5}
  .strip .fr{display:flex;flex-direction:column;gap:6px}
  .strip .fr figure{width:min(150px,10.4vw);aspect-ratio:4/5}
  .strip .stamp{margin:0;font:400 11px/1 'Space Grotesk',system-ui,sans-serif;letter-spacing:.12em;text-align:left;font-variant-numeric:tabular-nums}
  .spc .hline{display:flex;align-items:baseline;gap:24px;width:100%;max-width:min(964px,calc(62.4vw + 64px))}  /* as wide as the strip, so the hour starts on the lead frame's edge */
  .spc .hline .hour{font-size:56px;line-height:1}
  .spc .hline .cap{max-width:none;text-align:left}
  @media screen and (max-width:992px){
    .strip{flex-wrap:wrap;justify-content:center;max-width:620px}
    .strip .lead{width:260px;flex-basis:100%;max-width:260px;margin:0 calc((100% - 260px) / 2)}
    .strip .fr figure{width:140px}
    .spc .hline{flex-direction:column;align-items:center;gap:12px;max-width:620px}
    .spc .hline .cap{text-align:center;max-width:34ch}
    .spc .obj{padding:var(--sp-lg) 0}
  }
  @media screen and (max-width:576px){
    .strip{display:grid;grid-template-columns:1fr 1fr;width:100%;gap:12px}
    .strip .lead{grid-column:1 / -1;width:100%;max-width:none;margin:0}
    .strip .fr figure{width:100%}
  }
"""
REF_HOLD = []   # (destination sheet, markup): what left a sheet, waiting for its reference sheet (spec §4, 16-19)
# minute stamps inside each stage's hour (spec §4, 08-11)
STAMPS = {0: ("19:18", "19:24", "19:31", "19:37"), 1: ("19:46", "19:53", "20:01", "20:09"),
          2: ("20:24", "20:35", "20:48", "21:02"), 3: ("21:38", "21:45", "21:53", "22:00")}


def _retag(section, old, new):
    """Swap one class on the sheet's opening tag; where the sheet never had it, just add the new one."""
    a = section.index(">")
    head = section[:a]
    m = re.search(r'class="([^"]*)"', head)
    cls = [c for c in m.group(1).split() if c != old]
    cls += [new] if new not in cls else []
    return head[:m.start(1)] + " ".join(cls) + head[m.end(1):] + section[a:]


def colour_page(k, section):
    """A stage as its five photographs (spec §4, 08-11): the strip, the hour and the stage's line under it, the hex as the tag.
    The frames, their order and crops come from the source sheet; the stage's reading moves to reference sheet 16."""
    imgs = re.findall(r'<img [^>]*>', section)
    assert len(imgs) == 5, f"stage {k}: want five frames, found {len(imgs)}"
    hour = re.search(r'<p class="hour">(.*?)</p>', section).group(1)
    name = re.search(r'<h2 class="t hname">(.*?)</h2>', section).group(1)
    read = re.search(r'<p class="stageread">.*?</p>', section).group(0)
    line = re.search(r'<p class="stagecap">(.*?)</p>', section).group(1)
    hexv = D.STAGES[k][1]
    REF_HOLD.append((16, f'<div class="rstage"><h4>{name}</h4>{read}</div>'))
    rest = "".join(f'<div class="fr"><figure data-stage="{k + 1}">{im}</figure><p class="stamp">{t}</p></div>'
                   for im, t in zip(imgs[1:], STAMPS[k]))
    body = (f'<div class="obj"><div class="strip"><figure class="lead" data-stage="{k + 1}">{imgs[0]}</figure>{rest}</div>'
            f'<div class="hline"><p class="hour">{hour}</p><p class="cap">{line}</p></div></div>'
            f'<p class="tag">{name} &middot; {hexv} &middot; five frames, warm to cool</p>')
    return with_body(_retag(section, "hsheet", "spc"), body)


def art_direction(section):
    """Art direction as a strip (spec §4, 07): the one-light frame leads, the three after it stamped with their lightness.
    The written rules, the lead paragraph and the set's heading move to reference sheet 18."""
    imgs = re.findall(r'<img [^>]*>', section)
    assert len(imgs) == 4, f"art direction: want four frames, found {len(imgs)}"
    for pat in (r'<p class="adlead">.*?</p>', r'<ol class="adrules">.*?</ol>', r'<p class="pk2">Then, .*?</p>'):
        REF_HOLD.append((18, re.search(pat, section, re.S).group(0)))
    rest = "".join(f'<div class="fr"><figure>{im}</figure><p class="stamp">{t}</p></div>'
                   for im, t in zip(imgs[1:], ("L 0.378", "L 0.342", "L 0.205")))
    body = (f'<div class="obj"><div class="strip"><figure class="lead">{imgs[0]}</figure>{rest}</div>'
            '<p class="cap">One light source, and it is falling.</p></div><p class="tag">Art direction</p>')
    return with_body(_retag(section, "adcol", "spc"), body)


# ---- sheets 01-06 (spec §4) ----
def _hold(dest, section, *pats):
    """Move each matched block of the source sheet to a reference sheet; a pattern that finds nothing is a mistake."""
    for pat in pats:
        m = re.search(pat, section, re.S)
        assert m, f"nothing to hold for {dest}: {pat[:50]}"
        REF_HOLD.append((dest, _balanced(m.group(0))))


def _balanced(block):
    """A greedy match can run past its own end into the sheet's closing tags; shed them, so a moved block never closes the columns it lands in."""
    block = block.rstrip()
    while block.count("</div>") > len(re.findall(r"<div\b", block)) and block.endswith("</div>"):
        block = block[:-len("</div>")].rstrip()
    assert block.count("</div>") == len(re.findall(r"<div\b", block)), f"unbalanced block: {block[:60]}"
    return block


def _wm(px, cls="wmc"):
    return f'<p class="{cls}" style="--wm:{px}px">Afterglow</p>'


def cover_sheet(section):
    """01: the mark and the wordmark on one axis, one line under them. The photograph moves to 02."""
    body = (f'<div class="obj covobj">{mark_svg(260)}{_wm(130)}<p class="cap">{REWRITES[next(k for k in REWRITES if k.startswith("One fragrance"))]}</p></div>')
    return with_body(_retag(section, "hcover", "spc"), body)


def wordmark_sheet(section, cover):
    """02: the cover's photograph with the wordmark under it; the tiles and the specification move to 19. 7BF3FrZ leaves (it is 11's lead)."""
    _hold(19, section, r'<h2 class="t">The wordmark</h2>', r'<div class="wmhero">.*?<p class="cap2">.*?</p></div>', r'<div class="sup">.*</div>')
    img = re.search(r'<img [^>]*>', cover).group(0)   # the cover's crop comes with it: its 7% zoom keeps a badge in the source out of frame
    cap = REWRITES["There is no drawn logotype. The wordmark is Instrument Serif, widened to 150%."]
    body = f'<div class="obj"><figure class="f45">{img}</figure>{_wm(64)}<p class="cap wide">{cap}</p></div><p class="tag">The wordmark</p>'
    return with_body(_retag(section, "carry", "spc"), body)


def stages_sheet(section):
    """03: the four stages as four swatches, each its hour and name. The readings and the notes move to 16."""
    _hold(16, section, r'<div class="hintro">.*?</div></div>')
    sws = re.findall(r'<div class="sw" style="(background:[^;]+;color:[^;]+);[^"]*">(.*?<p class="swn">(.*?)</p>.*?)</div>(?=<div class="sw"|</div>$)', body_of(section), re.S)
    assert len(sws) == 4, len(sws)
    cells = ""
    for (st, inner, name), hr in zip(sws, B.HOURS):
        REF_HOLD.append((16, f'<div class="rsw"><h4>{name}</h4>' + re.search(r'<dl>.*?</dl><p class="swr">.*?</p>', inner, re.S).group(0) + '</div>'))
        cells += f'<div class="sws"><figure class="swc" style="{st}"><p class="hour">{hr}</p></figure><p class="swname">{name}</p></div>'
    body = f'<div class="obj"><div class="swrow">{cells}</div></div><p class="tag">Four hours of one evening</p>'
    return with_body(_retag(section, "hcolour", "spc"), body)


FALL_STOPS = ((0, "19:12"), (30, "19:40"), (60, "20:15"), (84, "21:30"), (95, "dark"))


def fall_sheet(section):
    """04: the fall as a band with each stop's hour under it. Everything else moves to 16 (the band and its ticks lead 16 already)."""
    _hold(16, section, r'<h2 class="t">The fall</h2>', r'<p class="lead">.*?</p>', r'<p class="fallhero">.*?</p>', r'<div class="lg l57">.*?</ul></div></div>')
    hrs = "".join(f'<b class="fhr" style="left:{x}%">{h}</b>' for x, h in FALL_STOPS)
    body = f'<div class="obj"><div class="fband"></div><div class="fhrs">{hrs}</div><p class="cap">Gold to violet, never reversed.</p></div>'
    return with_body(_retag(section, "carry", "spc"), body)


def type_sheet(section):
    """05: the two faces as one specimen. The roles, the scale and the notes move to 17, and the photograph with them."""
    _hold(17, section, r'<h2 class="t">.*?</h2>', r'<p class="lead">.*?</p>', r'<figure class=""><img [^>]*></figure>', r'<div class="faceshero">.*?</table></div></div>')
    body = ('<div class="obj"><div class="oo"><p class="spx serif">19:12</p><p class="spx sans">The light only ever deepens.</p></div></div>'
            '<p class="tag">Instrument Serif &middot; Space Grotesk</p>')
    return with_body(_retag(section, "carry", "spc"), body)


def rule_sheet(section):
    """06: the one rule as a specimen, its photograph beside it on the axis. The grid, spacing, radius, shadow and motion move to 17."""
    _hold(17, section, r'<h2 class="t">.*?</h2>', r'<p class="lead">.*?</p>', r'<p class="pk2">The one rule</p>', r'<p class="cap2">.*?</p>', r'<div class="lg l444">.*</div></div></div>')
    img = re.search(r'<img [^>]*>', section).group(0)
    body = (f'<div class="obj"><div class="rrow"><p class="rspec">The light only brightens where the ember is.</p><figure class="f45 r240">{img}</figure></div></div>'
            '<p class="tag">Twelve columns &middot; eight spacing steps</p>')
    return with_body(_retag(section, "carry", "spc"), body)


# ---- sheets 12-15 (spec §4) ----
def _photo_sheet(section, cls, cap, wide=False, extra="", tag=""):
    img = re.search(r'<img [^>]*>', section).group(0)
    t = f'<p class="tag">{tag}</p>' if tag else ''
    return with_body(_retag(section, cls, "spc"),
                     f'<div class="obj"><figure class="f45">{img}{extra}</figure><p class="cap{" wide" if wide else ""}">{cap}</p></div>{t}')


def ember_sheet(section):
    """12: the hand in its one streak of light. The ember's description, its rule and its live field move to 17."""
    _hold(17, section, r'<h2 class="t">The ember</h2>', r'<p class="lead">.*?</p><p class="lead">.*?</p>', r'<p class="never">.*?</p>', r'<div class="lbody">.*</div></div>')
    return _photo_sheet(section, "carry", "Move, and it lights. Stop, and in 0.7 seconds it goes out.")


def misuse_sheet(section):
    """13: the rejected frame with its Don't. The five pairs, the heading and the frame's long caption move to 18."""
    _hold(18, section, r'<figcaption>.*?</figcaption>', r'<div class="mutext">.*</div>\s*</div>')
    return _photo_sheet(section, "mugrid", "A frame rejected from the set: cold, lit from everywhere, and nothing in it falls.", wide=True,
                        extra='<span class="pill">Don&rsquo;t</span>')


def apps_sheet(section):
    """14: the label leads; the poster and the card follow at about half its size. Everything else moves to 19.
    The poster's mark is 48 px, the mark's minimum, where the spec drew 40 (ruling in the ledger)."""
    img = re.search(r'<img [^>]*>', section).group(0)
    _hold(19, section, r'<div class="mhead">.*?</div>', r'<div class="lbody">.*</div></div>')
    REF_HOLD[-1] = (19, REF_HOLD[-1][1].replace(img, ''))   # the photograph goes to the poster; the card diagram keeps its colour
    label = (f'<figure class="label"><div class="ltop">{mark_svg(150, "dark")}<span class="wmc lwm" style="--wm:26px">Afterglow</span></div>'
             '<p class="lline">19:12 &mdash; Eau de parfum, 50 ml</p></figure>')
    poster = f'<figure class="poster">{img}<div class="pmk">{mark_svg(48)}</div></figure>'
    card = f'<figure class="card">{mark_svg(56)}</figure>'
    body = (f'<div class="obj"><div class="prow">{label}<div class="pfol">{poster}{card}</div></div></div>'
            '<p class="tag">The label leads &middot; card and poster follow</p>')
    return with_body(_retag(section, "mhead", "spc"), body)


def voice_sheet(section):
    """15: the bottle. The voice, where the rules stop and where else to look move to 19."""
    _hold(19, section, r'<div class="vtext">.*?</div></div></div>')
    return _photo_sheet(section, "lvoice", "Unhurried and physical. It names heat, light, breath and skin.")


SHEETS_CSS = """
  /* 12-15 */
  .spc .f45{position:relative}
  .spc .f45 .pill{position:absolute;left:10px;top:10px}
  .prow{display:flex;align-items:flex-end;gap:48px}
  .pfol{display:flex;flex-direction:column;gap:20px;align-items:flex-start}
  .spc .label{width:280px;height:420px;padding:28px 20px 20px;display:flex;flex-direction:column;justify-content:space-between;align-items:center;
    background:linear-gradient(180deg,#D8B260,#BC6F4C 30%,#893A50 60%,#341D5E 84%,#080808 95%,#BF15B7);color:#EEECEA;overflow:visible}
  .label .ltop{display:flex;flex-direction:column;align-items:center;gap:16px}
  .label .lwm{display:inline-block;color:#080808}
  .lline{margin:0;font:400 11px/1.4 'Space Grotesk',system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase}
  .spc .poster{position:relative;width:140px;height:210px}
  .poster .pmk{position:absolute;left:10px;top:10px}
  .spc .card{width:200px;height:129px;background:#141414;display:flex;align-items:center;justify-content:center}
  @media screen and (max-width:992px){ .spc .label{width:224px;height:336px} .prow{gap:32px} }
  @media screen and (max-width:576px){ .prow{flex-direction:column;align-items:center} .pfol{flex-direction:row;align-items:flex-end;gap:16px} .spc .card{width:170px;height:110px} .spc .poster{width:120px;height:180px} }
  /* 01-06 (spec §4) */
  /* offline the wordmark falls back to a local serif sized to Instrument Serif's "Afterglow" (326 : 431 Georgia, 409 Times at 100 px) */
  @font-face{font-family:'Mark Georgia';src:local('Georgia');size-adjust:75.7%}
  @font-face{font-family:'Mark Times';src:local('Times New Roman'),local('Times');size-adjust:79.7%}
  .spc .wmc{margin:0;font:400 min(var(--wm),calc((100vw - 32px) / 5.2))/1 'Instrument Serif','Mark Georgia','Mark Times',serif;transform:scaleX(1.5);white-space:nowrap;letter-spacing:0}
  .covobj{gap:30px}
  .covobj .amark{width:min(260px,46vw);height:auto}
  .spc .f45{width:min(300px,100%);aspect-ratio:4/5}
  .spc .f45.r240{width:240px}
  .swrow{display:flex;gap:24px}
  .sws{display:flex;flex-direction:column;gap:10px;text-align:left}
  .spc .swc{width:120px;height:150px;padding:12px;display:flex;align-items:flex-end;overflow:visible}
  .swc .hour{font-size:44px;line-height:1}
  .swname{margin:0;font:400 11px/1.4 'Space Grotesk',system-ui,sans-serif;letter-spacing:.13em;text-transform:uppercase}
  .fband{width:min(960px,100%);height:120px;background:linear-gradient(90deg,#D8B260,#BC6F4C 30%,#893A50 60%,#341D5E 84%,#080808 95%,#080808 97.2%,#BF15B7 99.4%)}
  .fhrs{position:relative;width:min(960px,100%);height:40px;margin-top:-16px}
  .fhrs .fhr{position:absolute;top:0;font:400 28px/1 'Instrument Serif','Hour Georgia','Hour Times',serif;letter-spacing:-.03em;transform:translateX(-50%)}
  .fhrs .fhr[style*="left:0%"]{transform:none}
  .spx{margin:0}
  .spx.serif{font:400 min(160px,calc((100vw - 32px) / 2.6))/1 'Instrument Serif','Hour Georgia','Hour Times',serif;letter-spacing:-.03em}
  .spx.sans{margin-top:18px;font:400 22px/1.3 'Space Grotesk',system-ui,sans-serif}
  .rrow{display:flex;align-items:center;gap:64px}
  .rspec{margin:0;max-width:11em;font:400 56px/1.05 'Instrument Serif',Georgia,serif;text-align:left}
  @media screen and (max-width:992px){ .rrow{flex-direction:column;gap:32px} .rspec{text-align:center} }
  @media screen and (max-width:576px){
    .swrow{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .rspec{font-size:40px}
    .fhrs{height:64px}
    .fhrs .fhr{font-size:20px}
    .fhrs .fhr:nth-child(even){top:30px}
  }
  .ref .rlead .ticks{margin-top:10px}
"""


# ---- the reference sheets (spec §4, 16-19): one lead element, then everything a reader looks up, in calm columns ----
REF_TITLES = {16: "Colour", 17: "Type and layout", 18: "Imagery", 19: "Wordmark, mark, products and voice"}
REF_CSS = """
  /* the reference sheets: the lead first, then the readings at 11 px in columns, hairlines and no boxes; a sheet grows rather than shrink its type */
  .deck .sheet.ref{display:flex;flex-direction:column;height:auto;min-height:820px}
  .ref .rlead{margin:var(--sp-lg) 0 var(--sp-xl)}
  .ref .rcols{columns:4 220px;column-gap:40px;padding-bottom:var(--sp-xl);font:400 11px/1.6 'Space Grotesk',system-ui,sans-serif}
  .ref .rcols > *{break-inside:avoid;margin:0 0 var(--sp-lg);padding:10px 0 0;border-top:1px solid rgba(238,236,234,.22)}
  .deck .sheet.ref .rcols :is(p,li,dt,dd,td,th,span,em,b,a,figcaption,i){font-size:max(11px,1em);line-height:1.6;letter-spacing:.02em}  /* never under 11 px, whatever the moved block's own rule */
  .deck .sheet.ref .rcols :is(p,li,dt,dd,td,th,span,em,b,a,figcaption,i):not(.wspec,.tsamp){font-size:11px}
  .deck .sheet.ref .rcols :is(h2,h3,h4,.pk2,.dk,.ar,.rhuge,.vbig,.fallhero){margin:0 0 6px;font:400 18px/1.25 'Instrument Serif',Georgia,serif;letter-spacing:0;text-transform:none;max-width:none}
  /* a moved block brings its old grid with it; in a column it reads as plain stacked content, its diagrams at one small size */
  .deck .sheet.ref .rcols :is(div,article,ul,section):not(.wtile,.step,.appimg,.pcard,.plabel,.pposter,.plfall,.space,.sstep){display:block;width:auto;min-width:0;height:auto;min-height:0;max-height:none;padding:0;margin:0;grid-template-columns:none;columns:auto;position:static;transform:none;aspect-ratio:auto}
  .deck .sheet.ref .rcols :is(div,article)+:is(div,article,p,h3,ul){margin-top:10px}
  .deck .sheet.ref .rcols :is(.wtile,.appimg,.pcard,.plabel,.pposter){display:flex;align-items:center;justify-content:center;gap:6px;width:100%;height:36px!important;min-height:0;max-height:none!important;aspect-ratio:auto!important;margin:6px 0;padding:0 8px;position:relative;overflow:hidden}
  .deck .sheet.ref .rcols .appimg img{display:none}
  .deck .sheet.ref .rcols :is(span,i,em,b){position:static}
  .deck .sheet.ref .rcols .wmspace{display:none}
  .deck .sheet.ref .rcols dl{display:grid;grid-template-columns:auto 1fr;gap:0 12px;margin:4px 0}
  .deck .sheet.ref .rcols dd{margin:0}
  .deck .sheet.ref .rcols :is(.wtile .wpill,.wtile .wspec){position:static;transform:none}
  .deck .sheet.ref .rcols .wspec{font:400 18px/1 'Instrument Serif',Georgia,serif}
  .deck .sheet.ref .rcols .nc{display:grid;grid-template-columns:16px 1fr;column-gap:8px}
  .deck .sheet.ref .rcols .nc i{display:block;width:16px;height:16px;grid-row:span 2}
  .deck .sheet.ref .rcols .nc p{margin:0}
  .deck .sheet.ref .rcols .step{display:block;padding:6px 8px;margin:4px 0}
  .deck .sheet.ref .rcols .btn{display:inline-block;padding:6px 10px;margin:4px 6px 4px 0}
  .deck .sheet.ref .rcols .space{display:block}
  .deck .sheet.ref .rcols .sstep{display:grid;grid-template-columns:64px 32px 1fr;align-items:center;margin:2px 0}
  .deck .sheet.ref .rcols .sstep i{display:block;height:6px;background:currentColor;opacity:.6}
  .deck .sheet.ref .rcols table{width:100%;border-collapse:collapse;table-layout:auto}
  .deck .sheet.ref .rcols :is(td,th){padding:2px 8px 2px 0;text-align:left;white-space:normal}
  .deck .sheet.ref .rcols .efield .wordmark{font:400 18px/1.25 'Instrument Serif',Georgia,serif}
  .deck .sheet.ref .rcols .tri span{display:block}
  .deck .sheet.ref .rcols .chipi{display:inline-block;width:10px;height:10px;vertical-align:middle;margin-right:4px}
  .deck .sheet.ref .rcols .gbg{display:none}
  .deck .sheet.ref .rcols ul{padding-left:1.1em}
  .deck .sheet.ref .rcols li{display:list-item;margin:0 0 4px}
  .ref .rcols .panel{background:none;border:0;padding:0;margin:0}
  .ref .rcols :is(.wtile,.wtile *){font-size:revert}
  .ref .rcols .ard{margin:0 0 8px}
  .ref .rcols figure{width:150px;aspect-ratio:150/188;margin:0;overflow:hidden}
  .ref .rcols figure img{display:block;width:100%;height:100%;object-fit:cover}
  .ref .rlead .adrules{margin:0;padding:0;columns:2 420px;column-gap:56px}
  .ref .rlead .adrules li,.ref .rlead .adrules li:first-child{display:grid;grid-template-columns:2.4em 1fr;break-inside:avoid;counter-increment:r}  /* all five rules; sheet 07 hid the first under its headline */
  .ref .rlead .adrules li > *{grid-column:2}
  .ref .rlead .adrules .ar{margin:0;font:400 22px/1.25 'Instrument Serif',Georgia,serif}
  .ref .rlead .adrules .ard{margin:4px 0 var(--sp-md);font:400 11px/1.6 'Space Grotesk',system-ui,sans-serif;letter-spacing:.02em}
  .ref .rlead .adrules .arn{font:inherit}
  .ref .mcon{display:flex;align-items:center;gap:var(--sp-2xl,64px);flex-wrap:wrap}
  .ref .mcon dl{display:grid;grid-template-columns:auto auto;gap:4px 24px;margin:0;font:400 11px/1.6 'Space Grotesk',system-ui,sans-serif;letter-spacing:.02em}
  .ref .mcon dt{text-transform:uppercase;letter-spacing:.13em;opacity:.7}
  .ref .mcon dd{margin:0}
  @media screen and (max-width:992px){ .ref .rcols{columns:2} .deck .sheet.ref{min-height:0} }
  @media screen and (max-width:576px){ .ref .rcols{columns:1} .ref .rlead .adrules{columns:1} }
"""


def mark_construction():
    """Sheet 19's lead: the mark large, with its measures (spec §2). The geometry is the brand file's; only the numbers are set beside it."""
    rows = (("Parts", "Three equilateral triangles of side S, and a cap"), ("Gap", "0.16 S, square to the slope"),
            ("Cap", "0.23 S wide, 0.27 S high, 0.26 S above the peak"), ("Stroke", "0.04 S, mitred, no fills"),
            ("A serifs", "0.31 of the side, inward from each foot"), ("G", "turns in at 0.42 from the point; serif 0.2 of the side"),
            ("Opening", "0.38 of the side, the same in the A and the G"), ("Minimum", "48 px wide on screen"),
            ("Clear space", "the cap's height on every side"))
    dl = "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows)
    return f'<div class="mcon">{mark_svg(420)}<dl>{dl}</dl></div>'


def reference(n, title, lead, held):
    """A reference sheet: the lead element, then what was held for it, in sheet order; on the void, the hour 'dark'."""
    foot = (f'<footer class="foot"><span class="mark">Afterglow</span><span>{title}</span>'
            f'<span class="doc">Brand guide &middot; October 2026</span><span class="hr">dark</span><span class="pg">{n:02d}</span></footer>')
    return (f'<section class="sheet night ref" style="background:#080808"><div class="rlead">{lead}</div>'
            f'<div class="rcols">{"".join(held)}</div>{foot}</section>')


def build():
    html, n = B.build("b1-column")
    REF_HOLD.clear()
    secs = sections(html)
    new = list(secs)
    new[0] = cover_sheet(secs[0])
    new[1] = wordmark_sheet(secs[1], secs[0])
    new[2] = stages_sheet(secs[2])
    new[3] = fall_sheet(secs[3])
    new[4] = type_sheet(secs[4])
    new[5] = rule_sheet(secs[5])
    new[6] = art_direction(secs[6])
    new[11] = ember_sheet(secs[11])
    new[12] = misuse_sheet(secs[12])
    new[13] = apps_sheet(secs[13])
    new[14] = voice_sheet(new[14])
    for k in range(4):
        new[7 + k] = colour_page(k, secs[7 + k])
    # the fall's magenta sliver ends the deck, so it moves from 15 to the last reference sheet
    new[14] = re.sub(r'style="background:linear-gradient\(180deg,#080808 0%,#080808 98.4%,#BF15B7 100%\)"', 'style="background:#080808"', new[14], count=1)
    fall = re.search(r'<div class="fallband"></div><div class="ticks">.*?</div>', secs[3], re.S).group(0)
    tspec = re.search(r'<div class="tspec">.*?</div>\s*</div></div>', secs[4], re.S).group(0)
    held = lambda d: [m for dest, m in REF_HOLD if dest == d]
    ol = next(m for m in held(18) if m.startswith('<ol class="adrules">'))
    leads = {16: fall, 17: tspec, 18: ol, 19: mark_construction()}
    refs = [reference(n, REF_TITLES[n], leads[n], [m for m in held(n) if m != leads[n]]) for n in range(16, 20)]
    refs[-1] = refs[-1].replace('style="background:#080808"', 'style="background:linear-gradient(180deg,#080808 0%,#080808 98.4%,#BF15B7 100%)"', 1)
    for a, b in zip(secs, new):
        html = html.replace(a, b, 1)
    html = html.replace("</main>", "\n".join(refs) + "\n</main>", 1)
    html = html.replace("</style>", SPEC_CSS + SHEETS_CSS + REF_CSS + "</style>", 1)
    return html, n


# ---- "big numbers, less text" (Aaron, 12 Oct): the hour deck as it is, its densest readings moved to the reference sheets ----
def _move(dest, section, pat, lead=None):
    """Take the matched block out of the sheet and hold it for a reference sheet (or as that sheet's lead)."""
    m = re.search(pat, section, re.S)
    assert m, f"nothing to move for {dest}: {pat[:50]}"
    block = _balanced(m.group(0))
    if lead is not None:
        lead[dest] = block
    else:
        REF_HOLD.append((dest, block))
    return section.replace(block, "", 1)


LITE_CSS = """
  /* the leftovers at the back: three calm columns, room between blocks */
  .deck .sheet.ref .rcols{columns:3 300px;column-gap:72px}
  .deck .sheet.ref .rcols > *{margin:0 0 var(--sp-xl);padding-top:14px}
  .ref .rlead{margin:var(--sp-xl) 0 var(--sp-2xl,64px)}
  .ref .rlead .ticks{margin-top:14px}
  /* the fall names its stages; the uses sit under the ticks */
  /* The fall: the four stages read like the neutrals under them */
  .neut.stages{margin-bottom:var(--sp-md)}
  .neut.stages .use{font-style:italic}
  @media screen and (max-width:576px){ .s4 .ticks{display:none} .neut.stages .use{font-size:10px} }
  @media screen and (min-width:993px) and (max-width:1366px), screen and (min-width:993px) and (max-height:860px){
    .s4 .fallband{height:56px} .s4 .nc i{height:36px} .s4 .lbody{gap:var(--sp-sm)} .s4 .neut.stages{margin-bottom:var(--sp-sm)}
    .s4 .fallhero{font-size:clamp(32px,3.4vw,48px)} .s4 .nc p{margin-top:2px} }   /* the stages under it carry every hex; on a phone the labels collide */
  .s4 .fallband{flex:0 0 auto;height:96px;min-height:0}
  .s4 .lbody{gap:var(--sp-md)}
  /* Aaron, 13 Oct: the stage cards' big hours are black, whatever the stage */
  .deck .hsheet .hour{color:#080808}
  /* the cover: the photograph full bleed, darkened toward the type, the wordmark at its foot */
  .hcover .hpanel{width:100%!important}
  .hcover .hpanel::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,8,8,.75),rgba(8,8,8,0) 55%)}
  .bcover.hcover.sheet.sheet{padding-right:var(--pad)!important}
  .hcover .hour.hwm{font-size:10.4vw!important;margin:auto 0 0!important;align-self:flex-start!important;z-index:3}
  @media screen and (min-width:993px){ .deck .sheet.hcover{height:max(100svh,calc(100vw * .5694));min-height:0} }   /* the 1440 x 820 framing Aaron picked, at any width */
  .hcover .hour.hwm .wmtext{font-size:1em!important}
  .hcover .covnote{z-index:3}.hcover .foot{position:relative;z-index:3}
  @media screen and (max-width:992px){
    .hcover .hpanel{position:absolute!important;inset:0!important;width:auto!important;margin:0!important;aspect-ratio:auto!important}
    .hcover .hpanel::after{background:linear-gradient(180deg,rgba(8,8,8,.6),rgba(8,8,8,0) 22%,rgba(8,8,8,0) 50%,rgba(8,8,8,.8))}
    .hcover .hour.hwm{font-size:calc((100vw - 32px) / 6.4)!important;order:1;margin:auto 0 0!important}
  }
  @media screen and (max-width:992px){ .deck .sheet.ref .rcols{columns:2} }
  @media screen and (max-width:576px){ .deck .sheet.ref .rcols{columns:1} }
"""


def build_lite():
    """Big numbers, less text (Aaron, 12 Oct): each sheet keeps the part of its detail that fits its open ground;
    what does not fit waits at the back, spaced out."""
    html, n = B.build("b1-column")
    REF_HOLD.clear()
    secs = sections(html)
    new = list(secs)
    leads = {}
    # 02 keeps the five right ways to use the wordmark; the five ways to break it go to the back
    new[1] = _move(19, new[1], r'<h3 class="bt">Five ways to break it</h3><div class="wdonts">.*</div>')
    # Aaron, 13 Oct: The four stages folds into The fall. Its four stages sit above the neutrals and read the same way:
    # a chip, the name, the hex with its lightness, and its use; OKLCH, CMYK and the contrast pairs go to the back, and 03 goes
    s = new[2]
    chips = []
    for name in re.findall(r'<p class="swn">(.*?)</p>', s):
        m = re.search(r'<p class="swn">' + re.escape(name) + r'</p><dl>(.*?)</dl><p class="swr">(.*?)</p>', s, re.S)
        pairs = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', m.group(1))
        REF_HOLD.append((16, '<div class="rsw"><h4>' + name + '</h4><dl>'
                         + "".join(f'<dt>{t}</dt><dd>{d}</dd>' for t, d in pairs[1:]) + '</dl></div>'))
        v = dict(pairs[:3])
        use = "Text, logo, lines" if m.group(2).startswith("For text") else "Backgrounds only"
        chips.append(f'<div class="nc"><i style="background:{v["Hex"]}"></i><p>{name}</p>'
                     f'<p class="m">{v["Hex"]} &middot; L {v["OKLCH"].split()[0]}</p><p class="m use">{use}</p></div>')
    assert len(chips) == 4
    for _ in range(2):
        s = _move(16, s, r'<p class="fine2">.*?</p>')
    new[2] = ""
    f = new[3]
    lead = re.search(r'<p class="lead">The fall is.*?</p>', f).group(0)
    f = f.replace(lead, '<p class="lead">The brand&rsquo;s four colours, called stages, run from sunset into night, each darker than the last '
                  'at the same intensity. In order, falling to black and ending on a sliver of magenta, they make the fall, the brand&rsquo;s '
                  'gradient. Build it from these values, never by eye.</p>', 1)
    nh = '<div><h3 class="bt">Neutrals and surfaces</h3>'
    assert nh in f
    new[3] = f.replace(nh, '<div><h3 class="bt">The four stages</h3><div class="neut stages">' + "".join(chips) + '</div>'
                       '<h3 class="bt">Neutrals and surfaces</h3>', 1)
    # 04 keeps its neutrals; the build rules go to the back
    new[3] = _move(16, new[3], r'<div class="panel"><ul class="rules">.*?</ul></div>')
    # 05 keeps the roles table; the scale leads the type page at the back
    new[4] = _move(17, new[4], r'<div class="sup">.*</div>', lead=leads)
    # 06 keeps radius, shadow and motion; the measures and the spacing steps go to the back
    new[5] = _move(17, new[5], r'<div class="panel"><table class="tbl">.*?</table></div>')
    new[5] = _move(17, new[5], r'<div class="panel"><div class="space">.*?</div></div>')
    # 07's written rules lead the imagery page at the back; 13 keeps its five pairs
    new[6] = _move(18, new[6], r'<ol class="adrules">.*?</ol>', lead=leads)
    # 14 keeps the card, the label and the poster; buttons, surfaces and production go to the back
    new[13] = _move(19, new[13], r'<div class="panel"><div class="apps2">.*?</article></div></div>')
    new[13] = _move(19, new[13], r'<div class="prod">.*?</ul></div>')
    # 15: where the rules stop, and where else to look
    new[14] = _move(19, new[14], r'<div class="vcols">.*?</div></div>')
    new[14] = re.sub(r'style="background:linear-gradient\(180deg,#080808 0%,#080808 98.4%,#BF15B7 100%\)"', 'style="background:#080808"', new[14], count=1)
    leads[16] = re.search(r'<div class="fallband"></div><div class="ticks">.*?</div>', secs[3], re.S).group(0)
    leads[19] = mark_construction()
    held = lambda d: [m for dest, m in REF_HOLD if dest == d]
    refs = [reference(k, REF_TITLES[k], leads[k], held(k)) for k in range(16, 20)]
    refs[-1] = refs[-1].replace('style="background:#080808"', 'style="background:linear-gradient(180deg,#080808 0%,#080808 98.4%,#BF15B7 100%)"', 1)
    # Aaron, 13 Oct: the art direction set runs warm to cool: the red face stays, then the lit hand, then the lamp in the blue corridor
    for was, now in (("posters/fMmCZqp.jpg", "R6euaYP.jpg"), ("e4jFDHF.jpg", "CbRaZoU.jpg")):
        assert new[6].count("moodboard-media/" + was) == 1
        new[6] = new[6].replace("moodboard-media/" + was, "moodboard-media/" + now + "#ad", 1)   # the mark keeps it clear of the Ember swap below
    # Aaron, 13 Oct: the system pages come before the stage cards; art direction follows The fall
    new[3], new[6] = new[3] + "\n" + new[6], ""
    for a, b in zip(secs, new):
        html = html.replace(a + ("\n" if not b else ""), b, 1)
    html = html.replace("</main>", "\n".join(refs) + "\n</main>", 1)
    for was, now in (("art direction on page 07,", "art direction on page 04,"), ("pass on page 03.", "pass on page 15.")):   # the pages after 03 move up one
        assert was in html
        html = html.replace(was, now, 1)
    html = html.replace("</style>", REF_CSS + LITE_CSS + "</style>", 1)
    html = html.replace("moodboard-media/R6euaYP.jpg\"", "moodboard-media/5HaWaX_.jpg\"")
    html = html.replace(".jpg#ad", ".jpg")   # the Ember page photograph, Aaron's pick (Savee 5HaWaX_)
    html = unhour(recopy(refall(html)))
    # Aaron, 14 Oct (spec 2026-10-14-afterglow-ember-satin-design.md): this guide runs the satin ember, not v23. Its own output
    # only: the v23 container, bundle, boot script (guideGroundAt is the v23 engine's alone) and CSS go; the satin bundle and
    # its boot come in. The satin injects its own CSS (the canvas, the hidden deck while it runs, the print rule).
    v23 = (B.EMBER_CSS, '<div id="ember" aria-hidden="true"></div>\n',
           "<script>" + (D.ROOT / "brand/ember/ember.bundle.js").read_text().replace("</script", "<\\/script") + "</script>\n",
           "<script>" + B.GUIDE_JS.replace('"LIT"', '"' + B.EMBER_LIT + '"') + "</script>\n")
    for part in v23:
        assert html.count(part) == 1, f"satin swap: expected one v23 part, found {html.count(part)}: {part.strip()[:60]}"
        html = html.replace(part, "", 1)
    # Aaron, 15 Oct: "there should be no links on this guide". The two that point at internal documents keep their words
    html, n_links = re.subn(r"<a\b[^>]*>(.*?)</a>", r"\1", html, flags=re.S)
    assert n_links == 2, f"expected the two document links, found {n_links}"
    satin = (D.ROOT / "brand/ember/satin/ember-satin.bundle.js").read_text().replace("</script", "<\\/script")
    # over file:// the browser blocks the image and font reads the rasteriser needs (the photographs would draw blank), so
    # the engine stays off there and the native page shows, without the ember
    boot = ('(async function () { if (!window.EmberSatin || location.protocol === "file:") return; await document.fonts.ready; '
            'await Promise.all([].map.call(document.images, function (i) { return i.decode().catch(function () {}); })); '
            'EmberSatin.start(document.querySelector("main.deck")); })();')
    assert html.count("</body>") == 1
    return html.replace("</body>", f"<script>{satin}</script>\n<script>{boot}</script>\n</body>", 1), n


# Aaron, 13 Oct: only the wordmark page is solid gold and only the last page is black. 03 and the system pages fall through
# the evening (gold to deep violet; 03-06: The fall, art direction, type, grid); the stage cards then replay it, each on its own stage (08 gold, 09 after gold, 10 rose,
# 11 deep violet, at the band's stops); after them Motion repeats the rose card (Aaron, 13 Oct) and the rest falls on to black,
# at the foot of the second-last sheet; the last is void.
STOPS = (0, .30, .60, .84)


def lite_spans(n):
    """(top, bottom) of the fall for each sheet 1..n, or None for a void sheet."""
    spans = [None, (0, 0)]                                          # cover (own ground), then 02 the wordmark on gold
    spans += [(STOPS[3] * i / 4, STOPS[3] * (i + 1) / 4) for i in range(4)]   # 03-06, the system pages, fall through the evening
    spans += [(STOPS[k], STOPS[k + 1] if k < 3 else .90) for k in range(4)]   # 07-10, the stage cards, each on its stage
    spans += [(STOPS[2], STOPS[3])]                                 # 11, Motion, reads as the rose card does
    after = n - 1 - len(spans)                                      # 12 .. n-1 fall on from deep violet to black
    spans += [(STOPS[3] + (1 - STOPS[3]) * i / after, STOPS[3] + (1 - STOPS[3]) * (i + 1) / after) for i in range(after)]
    return spans + [None]


def refall(html):
    """Re-lay each sheet's ground on its span of the fall; ink follows the ground, each running head its time."""
    from afterglow_hours import hour_at
    secs = sections(html)
    spans = lite_spans(len(secs))
    out = []
    for k, (sec, sp) in enumerate(zip(secs, spans), 1):
        a = sec.index(">"); head, rest = sec[:a], sec[a:]
        if k >= 2:
            if sp:
                c0, c1, mid = B.doc_at(sp[0]), B.doc_at(sp[1]), B.doc_at((sp[0] + sp[1]) / 2)
                style = f"background:linear-gradient(180deg,{c0},{c1})"
                L = B._lum(mid)
                ink = "dark" if (L + .05) / (B._lum("#080808") + .05) > (B._lum("#EEECEA") + .05) / (L + .05) else "light"
            else:
                style, ink = "background:#080808", "night"
            if k == len(secs):
                style = "background:linear-gradient(180deg,#080808 0%,#080808 98.4%,#BF15B7 100%)"
            head = re.sub(r' style="[^"]*"', "", head) + f' style="{style}"'
            m = re.search(r'class="([^"]*)"', head)
            was = m.group(1).split()
            cls = [c for c in was if c not in ("dark", "light", "night")]
            cls.insert(1, "night" if ink == "light" and "night" in was else ink)   # a void sheet keeps its night styling while its ink stays light
            head = head[:m.start(1)] + " ".join(cls) + head[m.end(1):]
        t = "19:12" if k == 1 else (hour_at(sp[0]) if sp else "dark")
        rest = re.sub(r'<span class="hr">[^<]*</span>', f'<span class="hr">{t}</span>', rest, count=1)
        rest = re.sub(r'<span class="pg">\d+</span>', f'<span class="pg">{k:02d}</span>', rest, count=1)   # page numbers follow the order
        out.append(head + rest)
    for a_, b_ in zip(secs, out):
        html = html.replace(a_, b_, 1)
    return html


# Copy audit, 13 Oct (web-copywriter pass, read as a brand guide: the reader is a designer, photographer or printer applying
# the brand). Each line was wrong, ambiguous or passive; whitespace in the old text matches any run of whitespace.
COPY = [
    ("61.04&ndash;39.06 px", "39.06&ndash;61.04 px"),                                  # the range ran backwards
    ("Then, warm to cool across a set, never back", "Across a set, warm to cool, never back"),   # its "Then" followed nothing
    ("The palette is a description of light at a particular hour. Images are made to match it rather than graded toward it afterwards.",
     "The palette describes light at one hour of one evening. Shoot to match it; never grade toward it afterwards."),
    ("Hover, focus and active states still deepen and never lighten. In print and film, each panel or frame is never lighter than "
     "the one before it. It is the one rule a developer can check in the code.",
     "Everywhere else it only deepens. Hover, focus and active states darken, never lighten. In print and film, no panel or frame "
     "is lighter than the one before it. In code, no state is lighter than its resting state, so a developer can check it."),
    ("Five rules from the art direction on page 04, each shown right and wrong.",       # page 04 holds one line of them; 17 holds all
     "Five rules from the art direction, each shown right and wrong. The full rules are on page 17."),
    ("What a storefront is mostly made of, and what the fall needs from a press.",       # the press notes moved to 18
     "What a storefront is mostly made of. Press notes are on page 18."),
    ("Flat bands are the failure mode of a long gradient on paper. Keep any one flat under an inch at the size it is printed.",
     "Banding is how a long gradient fails on paper. At print size, no flat band may be wider than 25 mm."),   # the guide measures in mm
    ("the cap's height on every side", "the bottle cap&rsquo;s height, 0.27 S, on every side"),   # the wordmark's clear space is a different cap
    ("The atmosphere stops there on purpose, exactly as the voice does. Applied to a payment form or a warning label the discipline makes it worse.",
     "The atmosphere stops there on purpose: on a payment form or a warning label, it would only get in the way."),
    ("<li>In print it is a four-colour build or a gradient mesh; it is not two spot inks, which cannot hold the middle.</li>", ""),   # said again under Production
    ("Exposure is lifted at capture or the frame is not used.", "Exposure is set in camera. A frame that needs lifting afterwards is not used."),
    ("#EEECEA at full size, crossing after gold and deeper.", "#EEECEA at full size, over after gold or deeper."),
    ("#EEECEA or gold, the mark at night.", "#EEECEA or gold of last light."),
    ("Only the pairs that pass on page 15.", "Only in the colour pairs that pass on page 15."),
]


def recopy(html):
    for old, new in COPY:
        pat = r"\s+".join(re.escape(w) for w in old.split())
        html, k = re.subn(pat, new.replace("\\", "\\\\"), html)
        assert k == 1, f"copy edit matched {k} times: {old[:50]}"
    return html


def unhour(html):
    """Aaron, 13 Oct: the hour motif was overplayed. The hours stay on the four stage cards only; they leave the running
    heads, the fall's ticks, the type specimen and the cover note."""
    out = html
    for sec in sections(html):
        if ' hsheet"' in sec:
            continue
        new = re.sub(r'<span class="hr">[^<]*</span>', "", sec)
        new = re.sub(r'<i class="thr">[^<]*</i>', "", new)
        new = new.replace('<span class="fhr">19:12</span>', "")
        out = out.replace(sec, new, 1)
    cover = '<p class="hour">19:12</p>'                  # Aaron, 13 Oct: the cover is the photograph, full bleed, with the wordmark
    first = sections(out)[0]
    assert cover in first
    out = out.replace(first, first.replace(cover, '<p class="hour hwm"><span class="wmtext">Afterglow</span></p>', 1), 1)
    note = "One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark."
    assert note in out
    return out.replace(note, "One fragrance in four stages, from the last of the sun until it is dark.", 1)


if __name__ == "__main__":
    out = D.ROOT / "brand/2026-10-12-guide-hour-lite.html"
    html, n = build_lite()
    out.write_text(html)
    base = __import__("subprocess").run(["git", "show", f"{BASE_REF}:brand/2026-10-10-density-b1-column.html"], capture_output=True, text=True, cwd=D.ROOT).stdout
    print(out.relative_to(D.ROOT), n, "photographs; lost strings:", lost_strings(base, html)[:5])
