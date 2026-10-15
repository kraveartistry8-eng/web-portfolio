"""Four variants of density direction B: every sheet carries a photograph.

Built on tools/density_directions.py so the panels, leads and stage spreads are the same; only
how the photograph sits on the sheet changes. Rules every variant keeps:
  - no photograph appears twice in a deck (asserted at build time)
  - the stage spreads keep their 24 manifest references; every other slot takes an unused one
  - art direction is the most image-led sheet in the deck
  - the ground falls gold to violet across the deck and the last two sheets are void
Writes brand/2026-10-10-density-b{1..4}-*.html
"""
import re
from collections import Counter

import density_directions as D
from afterglow_hours import HOURS, stamp_times
from density_directions import S, STAGES, foot, page, stage_sheet, lead_apps, SYSTEM

# Unused mood board references, chosen by eye and checked against the ceiling (all L p75 <= 0.781).
# Left out: PNTk-Dh (another brand's bottle), F20ztHX / fC3QclQ / Na_PDmV (green or teal),
# sh51Sqi / a2QG-_S (daylight, no falling light), 4RH87Zk / eSgBkag (too abstract to carry a sheet).
M = "moodboard-media/"
# Every slot is set here, by Aaron from the mood board labels on 10 Oct; the build asserts no repeats.
VIDEO = {"4RH87Zk-arc", "NHyQ2Ii", "gm8x-Nc", "QOH4dl-", "ZpX9SWA", "85R4fhS", "v9AvMbv", "fMmCZqp", "mPNk84g"}


def media(stem):
    return M + (f"posters/{stem}.jpg" if stem in VIDEO else f"{stem}.jpg")


COVER = media("ZY6XxOv")                      # body dissolving in heat
CARRY = [media("7BF3FrZ"),                    # wordmark: open window, moon, violet sky
         media("f3MgZ_1"),                    # four stages: wet skin in gold
         media("gE_ypMW"),                    # the fall: dusk silhouette
         media("qNdZUES"),                    # two faces: head as an edge
         media("Eje8BSd")]                    # grid and the one rule: figure dissolving in orange haze
AD_HERO = media("OOqXr-G")                    # one light source, falling: the rule as a photograph
AD_SEQ = [media("USalI5W"), media("fMmCZqp"), media("e4jFDHF")]  # L .378 > .342 > .205
CARD = media("bNQYoLz")                       # product card
VOICE = M + "posters/PNTk-Dh-bottle.jpg"   # the bottle, last. A Viktor&Rolf stand-in: replace with Afterglow's own
# Five per spread, the first as a lead frame. Aaron struck lgBEnyK, k4KfGf3, NHyQ2Ii, gm8x-Nc from gold,
# QOH4dl- and ZpX9SWA from after gold, 85R4fhS from rose, v9AvMbv from deep violet (10 Oct).
# L8J-98T comes from the Afterglow Savee board; it was never pulled into the mood board.
SPREADS = [["wRU1tGM", "0x4Ubi2", "_SNh4mJ", "GVEgivk", "p-PXFnN"],
           ["tLwiMVf", "udQHGQp", "6pLfDFq", "f3MgZ_1", "Zul1TsA"],     # L1 lead (LV earbud + monogram jacket: retouch or replace before external), L3 (A16 declined); open slots: pick from A1-A22 (xy_NvPh removed: Aaron, no short-haired or bald women)
           ["gE_ypMW", "QfZU9JX", "HNrkkNB", "eXM8fJo", "Y1VfHK4"],     # R11 lower crop, pink beam; R9 kFiKBuu tried, Aaron declined; open slots: wine-rose, hue ~5 (V1/V2 or new search)
           ["7BF3FrZ", "0M3EBK4", "GU1xDFf", "fC3QclQ", "r-0SzGb"]]  # open slots: pick from V1-V12 (4RH87Zk-arc removed: Aaron)
RULES = re.findall(r'<p class="rbig">(.*?)</p>\s*<p class="pl">(.*?)</p>', S["12"]["colr"], re.S)
# Aaron, 11 Oct: these two carry enough weight to appear twice (system page and stage page)
ALLOWED_REPEATS = ("f3MgZ_1", "7BF3FrZ", "gE_ypMW")
MAGENTA = "#BF15B7"  # sampled from the magenta under the sun in GU1xDFf (Gold through violet); not #FF00BD


DOC_FALL = [(0, "#D8B260"), (.30, "#BC6F4C"), (.60, "#893A50"), (.84, "#341D5E"), (1, "#080808")]


def doc_at(t):
    """The document's own ground: the band's stops, without the magenta, ending in void."""
    for (t0, c0), (t1, c1) in zip(DOC_FALL, DOC_FALL[1:]):
        if t <= t1:
            return D.mix(c0, c1, (t - t0) / (t1 - t0))
    return DOC_FALL[-1][1]


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ground(i, n_fall):
    """Sheet i of n_fall takes its own slice of the fall; ink is whichever has more contrast at its midpoint."""
    a, b, m = doc_at(i / n_fall), doc_at((i + 1) / n_fall), doc_at((i + .5) / n_fall)
    L = _lum(m)
    ink = "dark" if (L + .05) / (_lum("#080808") + .05) > (_lum("#EEECEA") + .05) / (L + .05) else "light"
    return f"background:linear-gradient(180deg,{a},{b})", ink


def cover():
    return (f'<section class="sheet bcover"><div class="bimg"><img src="{COVER}" alt=""></div>'
            f'<div class="covergrid"><div><p class="kick">Brand guide &middot; October 2026</p>'
            f'<h1 class="wordmark">Afterglow</h1><p class="covline">The light only ever deepens.</p></div>'
            f'<div class="covmeta"><p class="pl" style="color:inherit;opacity:.82">Four stages, two faces, one grid. '
            f'Every sheet carries a photograph from the stage its ground sits in.</p></div></div>{foot("Cover", 1)}</section>')


def cover_hour():
    """The cover as the first hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): 19:12 across the cover photograph."""
    return (f'<section class="sheet bcover hcover"><figure class="hpanel"><img src="{COVER}" alt="" '
            f'style="object-position:50% 0%;transform:scale(1.07);transform-origin:50% 0"></figure>'
            f'<p class="hour">{HOURS[0]}</p>'
            f'<p class="covnote">One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark.</p>'
            f'{foot("Cover", 1)}</section>')


HOUR_PX = (190, 120, 90, 64)   # the four stages' hours at 1440: each later hour gets less room


def colour_hours(sec):
    """Sheet 3 as four hours, rebuilt from its finished markup so every reading the copy pass wrote is kept."""
    open_tag = re.match(r'<section class="([^"]*)"([^>]*)>', sec)
    h2 = re.search(r'<h2 class="t">.*?</h2>', sec).group(0)
    lead = re.search(r'<p class="lead">.*?</p>', sec).group(0)
    notes = "".join(re.findall(r'<p class="fine2">.*?</p>', sec))
    sws = re.findall(r'<div class="sw" (style="[^"]*")>(.*?</p>)(<dl>.*?</dl>)(<p class="swr">.*?</p>)</div>', sec)
    assert len(sws) == 4, len(sws)
    cols = "".join(f'<div class="sw" {st[:-1]};--hs:{px}"><p class="hour">{h}</p>{n}{dl}{r}</div>'
                   for (st, n, dl, r), h, px in zip(sws, HOURS, HOUR_PX))
    foot_html = re.search(r'<footer class="foot">.*?</footer>', sec).group(0)
    return (f'<section class="{open_tag.group(1)} hcolour"{open_tag.group(2)}><div class="hintro">{h2}<div>{lead}{notes}</div></div>'
            f'<div class="hcols">{cols}</div>{foot_html}</section>')


def fig(src, cls=""):
    return f'<figure class="{cls}"><img src="{src}" alt=""></figure>'


# ---- the four ways a photograph sits on a system sheet ----
def sys_column(i, sec, title, lead, body, img, style, ink):
    return (f'<section class="sheet {ink} imagery" style="{style}"><div class="carry">'
            f'<div class="ph"><h2 class="t">{title}</h2><p class="lead">{lead}</p>{fig(img)}</div>'
            f'<div class="lbody">{body}</div></div>{foot(sec, i)}</section>')


def sys_edge(i, sec, title, lead, body, img, style, ink):
    side = "l" if i % 2 else "r"
    return (f'<section class="sheet {ink} imagery edge {side}" style="{style}">{fig(img, "eimg")}'
            f'<div class="mhead"><h2 class="t">{title}</h2><p class="lead">{lead}</p></div>'
            f'<div class="lbody">{body}</div>{foot(sec, i)}</section>')


AIM = {CARRY[0]: "50% 50%", CARRY[1]: "50% 50%", CARRY[2]: "50% 40%", CARRY[3]: "50% 55%", CARRY[4]: "50% 35%"}


def sys_band(i, sec, title, lead, body, img, style, ink):
    f = fig(img, "bandimg").replace("<img ", f'<img style="object-position:{AIM[img]}" ')
    return (f'<section class="sheet {ink} imagery band" style="{style}">{f}'
            f'<div class="mhead"><h2 class="t">{title}</h2><p class="lead">{lead}</p></div>'
            f'<div class="lbody">{body}</div>{foot(sec, i)}</section>')


def sys_inset(i, sec, title, lead, body, img, style, ink):
    return (f'<section class="sheet light imagery inset" style="background:#080808">{fig(img, "fullimg")}'
            f'<div class="ihead panel"><h2 class="t">{title}</h2><p class="lead">{lead}</p></div>'
            f'<div class="lbody">{body}</div>{foot(sec, i)}</section>')


# ---- art direction: the most image-led sheet, in each variant's grammar ----
def rules_html(big=True):
    # Instrument Serif draws 1 like l, so a reading inside a serif rule is set in the body face
    num = lambda t: re.sub(r"L\s*0\.\d+", lambda m: f'<span class="arn">{m.group(0)}</span>', t)
    return "".join(f'<li><p class="ar">{num(r)}</p><p class="ard">{d}</p></li>' for r, d in RULES)


def seq():
    return (f'<div class="seq"><p class="pk2">Then, warm to cool across a set, never back</p><div class="seqrow">'
            f'{"".join(fig(s) for s in AD_SEQ)}</div></div>')


def ad(mode, pg, style, ink):
    head = (f'<p class="pk2">Art direction</p><p class="adbig">One light source, and it is falling.</p>'
            f'<p class="adlead">{S["12"]["lead"]}</p>')
    rest = f'<ol class="adrules">{rules_html()}</ol>'
    if mode == "inset":
        return (f'<section class="sheet light imagery ad adinset" style="background:#080808">{fig(AD_HERO, "fullimg")}'
                f'<div class="adpanel panel">{head}{rest}</div>{seq()}{foot("Imagery", pg)}</section>')
    if mode == "band":
        return (f'<section class="sheet {ink} imagery ad adband" style="{style}">{fig(AD_HERO, "adbandimg")}'
                f'<div class="adbelow"><div>{head}</div>{rest}</div>{foot("Imagery", pg)}</section>')
    if mode == "edge":
        return (f'<section class="sheet {ink} imagery ad adedge" style="{style}">{fig(AD_HERO, "adeimg")}'
                f'<div class="adtext">{head}{rest}{seq()}</div>{foot("Imagery", pg)}</section>')
    return (f'<section class="sheet {ink} imagery ad adcol" style="{style}"><div class="adgrid">'
            f'{fig(AD_HERO, "adhero")}<div class="adtext">{head}{rest}{seq()}</div></div>{foot("Imagery", pg)}</section>')


def apps(pg):
    body = lead_apps().replace(re.search(r'<img src="([^"]+)" alt="Reference for the product card"',
                                         lead_apps()).group(1), CARD)
    return (f'<section class="sheet night"><div class="mhead"><h2 class="t">Digital and print</h2>'
            f'<p class="lead">What a storefront is mostly made of, and what the fall needs from a press.</p></div>'
            f'<div class="lbody">{body}</div>{foot("Applications", pg)}</section>')


def voice(pg):
    return D.voice_sheet(pg, "background:#080808").replace(D.src_of(D.PHOTOS[3][5]), VOICE)


CUT = M + "3ASXlcU-trim.jpg"  # Afterglow Offcuts board, Aaron's pick: a body in cold blue water


def spread(k, pg, style, ink):
    name, hexv, L, _ = STAGES[k]
    hint = {1: "pick from A1&ndash;A22", 2: "pick from R1&ndash;R10", 3: "pick from V1&ndash;V12"}.get(k, "")
    crop = {"9HB093h": "50% 0%", "HNrkkNB": "50% 30%", "GVEgivk": "50% 10%", "udQHGQp": "50% 64%"}  # head, or the glass, near the top
    figs = "".join(f'<figure data-stage="{k + 1}"><img src="{media(f)}" alt=""' + (f' style="object-position:{crop[f]}"' if f in crop else '') + '></figure>' if f else
                   f'<figure class="open"><span>Open slot<br>{hint}</span></figure>'
                   for f in SPREADS[k])
    return (f'<section class="sheet {ink} imagery spread{" violet" if k == 3 else ""}" style="{style}">'
            f'<div class="stagehead"><h2 class="stagename"><i class="schip" style="background:{hexv}"></i>{name}</h2>'
            f'<span class="stageread">{hexv} &middot; L {L}</span></div>'
            f'<hr class="stagebar" style="background:{hexv}"><div class="imgs">{figs}</div>{foot("Imagery", pg)}</section>')


LEAD_AIM = {"wRU1tGM": "50% 40%"}   # the lead frame's crop in the full-height panel; moved, never scrimmed, if the hour fails 3:1 over it


def spread_hour(k, pg, style, ink):
    """A stage spread as its hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): the lead frame as a full-height panel,
    the hour set huge across it, the stage's name and readings as a note, the other four frames as one row."""
    name, hexv, L, _ = STAGES[k]
    crop = {"9HB093h": "50% 0%", "HNrkkNB": "50% 30%", "GVEgivk": "50% 10%", "udQHGQp": "50% 64%"}
    img = lambda f: f'<img src="{media(f)}" alt=""' + (f' style="object-position:{crop[f]}"' if f in crop else '') + '>'
    lead = SPREADS[k][0]
    stamps = "".join(f'<figure data-stage="{k + 1}">{img(f)}</figure>' for f in SPREADS[k][1:])
    return (f'<section class="sheet {ink} imagery hsheet" style="{style}" data-hour="{k}">'
            f'<figure class="hpanel" data-stage="{k + 1}"><img src="{media(lead)}" alt="" style="object-position:{LEAD_AIM.get(lead, "50% 50%")}"></figure>'
            f'<p class="hour">{HOURS[k]}</p>'
            f'<div class="hrow"><div class="hnote"><h2 class="t hname">{name}</h2><p class="stageread">{hexv} &middot; L {L}</p>'
            f'<p class="stagecap">{STAGE_CAPS[k]}</p></div><div class="stamps">{stamps}</div></div>'
            f'{foot("Imagery", pg)}</section>')


HOUR_CSS = """
  /* offline the hour falls back to a local serif sized to Instrument Serif's digits (19:40 at 1.567 em), so it never outgrows its sheet */
  @font-face{font-family:'Hour Georgia';src:local('Georgia');size-adjust:67%}
  @font-face{font-family:'Hour Times';src:local('Times New Roman'),local('Times');size-adjust:73.6%}
  /* the hour (spec 2026-10-11-afterglow-guide-hour-design.md): a stage spread is its hour, set across the lead frame */
  .hour{margin:0;font-family:'Instrument Serif','Hour Georgia','Hour Times',serif;font-weight:400;line-height:.8;letter-spacing:-.03em;white-space:nowrap;
    font-variant-numeric:lining-nums;color:inherit;position:relative;z-index:2}
  .hsheet{position:relative;padding-right:calc(38% + var(--pad))!important}
  :is(.hsheet,.hcover) .hpanel{position:absolute;top:0;right:0;bottom:0;width:38%;margin:0;overflow:hidden}
  :is(.hsheet,.hcover) .hpanel img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
  .hsheet .hour{font-size:min(520px,36.1vw);margin:auto calc(-1 * var(--pad) - .25em) 0 0;align-self:flex-end;order:1}  /* its end crosses a quarter em onto the panel */
  .hsheet .hrow{display:grid;grid-template-columns:minmax(0,30ch) minmax(0,1fr);gap:var(--sp-lg);position:relative;z-index:3}
  .hsheet .hname{font-size:22px;line-height:1.1;margin:0 0 var(--sp-sm);white-space:normal}
  .hsheet .stageread,.hsheet .stagecap{font-size:12px;line-height:1.55;margin:0;max-width:30ch;opacity:1}
  .hsheet .stamps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--sp-sm);align-self:start}
  .hsheet .stamps figure{margin:0;aspect-ratio:4/5;overflow:hidden;position:relative}
  .hsheet .stamps img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
  @media screen and (max-width:992px){
    .hsheet .hrow{grid-template-columns:1fr}
    .hsheet .stamps{grid-template-columns:repeat(2,minmax(0,1fr))}
  }
  /* the fall: each stop's hour under its percentage; the type specimen sets the hour beside the wordmark */
  .ticks{height:46px}
  .ticks .thr{display:block;font-style:normal;opacity:.8}
  .ticks span.tdark{display:block}
  .ticks .tdark .thr{margin-top:1.4em}
  .fbig.serif{display:flex;flex-wrap:wrap;column-gap:.5em;white-space:normal}  /* the hour sits beside the name, or under it where the column is narrow */
  .fbig .fhr{letter-spacing:-.03em;font-variant-numeric:lining-nums}
  /* the cover: 19:12 across the photograph */
  .hcover{background:#080808;display:flex;flex-direction:column}
  .bcover.hcover.sheet.sheet{padding:0 calc(38% + var(--pad)) var(--pad) var(--pad)!important}
  .sheet.bcover.hcover .foot{margin:var(--sp-md) 0 0!important}
  .hcover .covnote{margin:var(--sp-xl) 0 0;font-size:12px;line-height:1.55;max-width:30ch;color:#EEECEA;position:relative;z-index:3}
  .hcover .hour{font-size:min(430px,29.9vw);margin:auto calc(-1 * var(--pad) - .25em) 0 0;align-self:flex-end;order:1;color:#EEECEA}
  /* the four stages: four hours, each later one given less room */
  .hcolour .hintro{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:var(--sp-lg);margin-bottom:var(--sp-lg)}
  .hcolour .hintro h2.t{margin:0}
  .hcolour .hintro .lead{margin:0 0 var(--sp-sm)}
  .hcolour.sheet.sheet{--hpad:var(--pad);padding-left:var(--hpad)!important;padding-right:var(--hpad)!important;padding-bottom:0!important}
  .hcolour .hcols{flex:1;min-height:0;display:grid;grid-template-columns:1.6fr 1fr .8fr .6fr;margin:0 calc(var(--hpad) * -1)}
  .hcolour .sw{padding:var(--sp-lg) var(--sp-md);min-width:0;overflow:hidden}
  .hcolour .sw .hour{font-size:min(calc(var(--hs) * 1px),calc(var(--hs) * 100vw / 1440));margin-bottom:auto}
  .hcolour .swn{margin:var(--sp-md) 0 0;font-size:22px}
  .hcolour .sw dl{grid-template-columns:1fr;gap:0;margin:var(--sp-sm) 0}
  .hcolour .sw dt{font-size:9.5px;margin-top:4px}
  @media screen and (max-width:992px){
    .hsheet .hour{margin-top:var(--sp-xl)}
    .hcover{min-height:100svh}
    .hcolour .hintro{grid-template-columns:1fr}
    .hcolour .hcols{grid-template-columns:1fr;min-height:1100px;
      grid-template-rows:minmax(min-content,1.6fr) minmax(min-content,1fr) minmax(min-content,.8fr) minmax(min-content,.6fr)}
    .hcolour .sw{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:auto 1fr;column-gap:var(--sp-lg);align-content:start}
    .hcolour .sw .hour{grid-column:1;font-size:calc(var(--hs) * .6px);margin:0}
    .hcolour .swn{grid-column:1;margin:var(--sp-sm) 0 0}
    .hcolour .sw dl,.hcolour .swr{grid-column:2;grid-row:1 / span 2;align-self:start}
    .hcolour .swr{grid-row:3}
  }
  @media screen and (max-width:576px){
    .hsheet{padding-right:var(--sp-md)!important}
    .bcover.hcover.sheet.sheet{padding:0 var(--sp-md) var(--sp-lg)!important}
    :is(.hsheet,.hcover) .hpanel{position:relative;inset:auto;width:auto;margin:0 calc(var(--sp-md) * -1);aspect-ratio:4/5}
    :is(.hsheet,.hcover) .hour{font-size:calc((100vw - 32px) / 1.62);margin:-.2em 0 var(--sp-lg);align-self:flex-start;order:0}
    .hcover .covnote{margin:0}
    .hcolour .sw .hour{font-size:calc(var(--hs) * .5px)}
    .hcolour.sheet.sheet{--hpad:var(--sp-md)}
  }
"""


def misuse(pg, style, ink):
    """The opposite of art direction: a frame the measure cut, shown at the size the lamp gets."""
    return (f'<section class="sheet {ink} imagery misuse" style="{style}"><div class="mugrid">'
            f'<figure class="cut"><img src="{CUT}" alt="A frame cut from the set"><span class="pill">Don&rsquo;t</span>'
            f'<figcaption>From the offcuts. Cold where the brand is warm, lit from everywhere through water, '
            f'blue from edge to edge. Nothing in it falls, and nothing in it deepens.</figcaption></figure>'
            f'<div class="mutext"><h2 class="t">{S["17"]["h2"]}</h2><p class="lead">Six ways to break the five rules, '
            f'beside a frame cut from the brand. Each tile is built from tokens; the photograph is the real thing.</p>'
            f'{S["17"]["colr"]}</div></div>{foot("Imagery", pg)}</section>')


EMBER_G0, EMBER_G1, EMBER_HOT = "#321C5B", "#1D1231", "#5304E4"   # the page's slice, and the ember on it
EMBER_IMG = media("R6euaYP")                  # a hand lit by one streak of warm light; used nowhere else


def ember_page(pg, style, ink):
    """Page 12, the ember (spec 4.1, direction A-prime): the live ember is the page's picture."""
    chip = lambda c: f'<span class="chipi" style="background:{c}"></span>'
    return (f'<section class="sheet {ink} imagery ember" style="{style}"><div class="carry">'
            f'<div class="ph"><h2 class="t">The ember</h2>'
            f'<p class="lead">The one accent of contrast. It follows the cursor in the colour of the page beneath it, '
            f'and goes out when the cursor stops.</p>'
            f'<p class="lead">Type, panels, colour and photographs catch its light on the side facing it. Nothing is cast.</p>'
            f'<figure class="efig"><img src="{EMBER_IMG}" alt="A hand lit by one streak of warm light"></figure>'
            f'<p class="never">Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that '
            f'needs it to render.</p></div>'
            f'<div class="lbody"><div class="efield"><p class="wordmark fwm2">Afterglow</p>'
            f'<div class="tri"><span>Live</span><span>Move, and it lights. Stop, and in 0.7 seconds it goes out.</span>'
            f'<span>{chip(EMBER_G0)}{EMBER_G0} &rarr; {chip(EMBER_HOT)}{EMBER_HOT}</span></div></div></div>'
            f'</div>{foot("Motion", pg)}</section>')


EMBER_PAGE_CSS = """
  /* page 12, the ember: a title column, and an open field whose one hero is the wordmark */
  /* page 6: the one rule is longer now; it sets in two lines so its caption clears the column overlay */
  @media screen and (min-width:993px){.s6 .rulehero .rhuge{max-width:22ch;font-size:clamp(56px,6vw,88px)}}
  .ember .ph .lead + .lead{margin-top:0}
  .efig{margin:var(--sp-sm) 0 0;flex:1;min-height:0;overflow:hidden;position:relative}
  .efig img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 40%;display:block}
  .ember .never{margin:var(--sp-sm) 0 0;font-size:var(--xs);line-height:1.5;color:#EEECEA;opacity:.7;max-width:32ch}
  .efield{flex:1;min-height:0;position:relative;display:flex;flex-direction:column;justify-content:center}
  .fwm2{margin:0 auto 0 4%;font-size:clamp(44px,12.5vw,200px);line-height:1;color:#EEECEA;position:relative}
  .tri{position:absolute;left:0;right:0;bottom:0;display:grid;grid-template-columns:1fr 2fr 1fr;padding-top:var(--sp-sm);
    border-top:1px solid rgba(238,236,234,.22);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#EEECEA}
  .tri > span:nth-child(2){text-align:center;text-transform:none;letter-spacing:0;font-family:var(--display);font-size:20px;line-height:1}
  .tri > span:last-child{text-align:right}
  .chipi{display:inline-block;width:10px;height:10px;margin-right:4px;vertical-align:0}
  @media screen and (max-width:992px){.efig{flex:none;aspect-ratio:4/3}.efield{min-height:300px}}
  @media screen and (max-width:576px){.tri{position:static;grid-template-columns:1fr;gap:4px;margin-top:var(--sp-lg)}
    .tri > span{text-align:left!important}.efield{justify-content:flex-start;padding-top:var(--sp-xl)}}
"""


VARIANTS = {
    "b1-column": ("Column", sys_column, "col"),
    "b2-edge": ("Edge", sys_edge, "edge"),
    "b3-band": ("Band", sys_band, "band"),
    "b4-inset": ("Inset", sys_inset, "inset"),
}


def build(key):
    name, sysfn, admode = VARIANTS[key]
    # cover, 5 system, art direction, 4 stages, the ember, misuse on the fall; then 2 on void
    off, n_fall = 0, (13 if key == "b1-column" else 12)
    sh = [cover_hour() if key == "b1-column" else cover()]
    for i, ((sec, title, lead, fn), img) in enumerate(zip(SYSTEM, CARRY)):
        style, ink = ground(i + 1 + off, n_fall)
        sh.append(sysfn(i + 2 + off, sec, title, lead, fn(), img, style, ink).replace('imagery', f'imagery s{i + 2}', 1))
    style, ink = ground(6 + off, n_fall)
    sh.append(ad(admode, 7 + off, style, ink))
    for k in range(4):
        style, ink = ground(7 + k + off, n_fall)
        sh.append((spread_hour if key == "b1-column" else spread)(k, 8 + k + off, style, ink))
    style, ink = ground(11 + off, n_fall)
    if key == "b1-column":
        assert style == f"background:linear-gradient(180deg,{EMBER_G0},{EMBER_G1})", style
        sh.append(ember_page(12 + off, style, ink))
    else:
        off -= 1  # the other variants have no Ember page
    style, ink = ground(12 + off, n_fall)
    sh.append(misuse(13 + off, style, ink))
    sh.append(apps(14 + off))
    # the document's own fall ends as the band does: void, then a sliver of magenta at the very end
    sh.append(voice(15 + off).replace('style="background:#080808"', f'style="background:linear-gradient(180deg,#080808 0%,#080808 98.4%,{MAGENTA} 100%)"', 1))
    html = page(f"Afterglow — Direction B{key[1]}: {name}", sh)
    html = html.replace("</style>", B_CSS + (POLISH_CSS if key == "b1-column" else "") + "</style>", 1)
    hour_of = dict(zip((0, 30, 60, 84, 95), HOURS + ["dark"])) if key == "b1-column" else {}   # the hour each stop stands for; the magenta sliver has none
    ticks = "".join((f'<span class="tdark" style="left:{x}%"><i class="thr">dark</i></span>' if x == 95 and hour_of else   # the void's swatch label stays hidden; its hour shows
                     f'<span style="left:{x}%"><b>{h}</b>{x:g}%' + (f'<i class="thr">{hour_of[x]}</i>' if x in hour_of else '') + '</span>') for x, h in
                    ((0, "#D8B260"), (30, "#BC6F4C"), (60, "#893A50"), (84, "#341D5E"), (95, "#080808"), (100, MAGENTA)))
    html = re.sub(r'<div class="ticks">.*?</div>', f'<div class="ticks">{ticks}</div>', html, flags=re.S)
    html = html.replace("No stop may be added, moved or removed. Four stops, evenly spaced.",
                        f"Four stages fall to the void and end on a sliver of {MAGENTA}. No stage may be added, moved or removed.")
    if key == "b1-column":
        html = copy_pass(html)
        html = html.replace('<p class="fbig serif">Afterglow</p>', f'<p class="fbig serif">Afterglow<span class="fhr">{HOURS[0]}</span></p>', 1)
        i = html.index('imagery s3"'); a = html.rindex('<section', 0, i); b = html.index('</section>', i) + len('</section>')
        html = html[:a] + colour_hours(html[a:b]) + html[b:]
        # the hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): each running head carries its sheet's time
        html = stamp_times(html, n_fall)
        # titles (11 Oct): the tab names the document, each head names its page's subject, the name is not said twice
        html = re.sub(r"<title>.*?</title>", "<title>Afterglow Brand Guide</title>", html, count=1)
        html = html.replace("<span>Identity</span>", "<span>Wordmark</span>")
        html = re.sub(r'<div class="plabel"><span class="pwm sm">Afterglow</span>\s*<span class="pfine">',
                      '<div class="plabel"><div class="plfall"><span class="pwm sm">Afterglow</span></div><span class="pfine">', html)
        html = html.replace('<span class="doc">Afterglow Brand Guide &middot; October 2026</span>', '<span class="doc">Brand guide &middot; October 2026</span>')
        html = html.replace(">Two faces, one scale<", ">Two faces, one&nbsp;scale<").replace(">Grid and the one rule<", ">Grid and the one&nbsp;rule<")
        i = html.index('imagery s5"'); a = html.index('<div class="panel"><table class="tbl">', i); b = html.index("</table>", a) + len("</table></div>")
        roles = html[a:b]; html = html[:a] + html[b:]
        f = html.index('<p class="fbig sans">', i); f = html.index("</div>", f) + len("</div>")
        html = html[:f] + roles + html[f:]
    if key == "b1-column":
        html = with_ember(html.replace("</style>", EMBER_PAGE_CSS + HOUR_CSS + "</style>", 1))
    srcs = [s for s in re.findall(r'<img[^>]+src="([^"]+)"', html) if "moodboard-media" in s]
    dup = [s for s, c in Counter(srcs).items() if c > 1 and not any(k in s for k in ALLOWED_REPEATS)]
    assert not dup, f"{key}: repeated {dup}"
    return html, len(srcs)


B_CSS = f"""
  /* the fall ends: void, then a sliver of magenta */
  .fallband{{background:linear-gradient(90deg,#D8B260,#BC6F4C 30%,#893A50 60%,#341D5E 84%,#080808 95%,#080808 97.2%,{MAGENTA} 99.4%)}}
  .carry .ph figure{{flex:1}}
  .ticks span:nth-child(5){{display:none}}  /* void sits 5% from the end; its label would collide */
  /* edge: the photograph bleeds off one side, full height */
  .edge{{--ew:34%}}
  .edge.r{{padding-right:calc(var(--ew) + var(--pad))}}
  .edge.l{{padding-left:calc(var(--ew) + var(--pad))}}
  .eimg{{position:absolute;top:0;bottom:0;width:var(--ew);margin:0;overflow:hidden}}
  .edge.r .eimg{{right:0}}.edge.l .eimg{{left:0}}
  .eimg img,.bandimg img,.fullimg img,.adhero img,.adeimg img,.adbandimg img,.seq img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
  /* band: a letterbox across the top of the sheet */
  .band{{padding-top:0}}
  .bandimg{{position:relative;margin:0 calc(var(--pad) * -1) var(--sp-lg);height:31%;min-height:180px;overflow:hidden;flex:0 0 auto}}
  .band .lbody{{gap:var(--sp-md)}}
  .band .fallhero{{font-size:var(--x2)}}
  .band .rhuge{{font-size:clamp(40px,4.6vw,64px)}}
  .band .wmhero .wmtext{{font-size:clamp(56px,7vw,104px)}}
  /* inset: the photograph is the ground; readings stay in void panels over it */
  .inset{{color:var(--text)}}
  .fullimg{{position:absolute;inset:0;margin:0;overflow:hidden}}
  .inset > *:not(.fullimg){{position:relative}}
  .ihead{{align-self:flex-start;display:flex;align-items:baseline;gap:var(--sp-xl);margin-bottom:var(--sp-lg);max-width:100%}}
  .ihead h2.t{{font-size:var(--x3);margin:0;white-space:nowrap}}
  .ihead .lead{{color:var(--muted)}}
  .inset .lbody{{margin-left:36%}}
  .inset .lbody > *{{}}
  .inset .swatches,.inset .fallband,.inset .neut,.inset .faceshero,.inset .wmhero,.inset .rulehero,.inset .fallhero,.inset .ticks{{background-color:#080808}}
  .inset .fallhero,.inset .rulehero,.inset .faceshero,.inset .wmhero{{padding:var(--sp-md) var(--sp-lg)}}
  .inset .ticks{{padding:6px var(--sp-sm);margin-top:0}}
  .inset .lg>div:not(.panel):not(.sup),.inset .lg .sup{{background:#080808;padding:var(--sp-md)}}
  .inset .gbg{{display:none}}
  .inset .foot{{background:#080808;margin:0 calc(var(--pad) * -1);padding-left:var(--pad);padding-right:var(--pad);border-top:0;color:var(--muted)}}
  .inset .foot .mark,.inset .foot .pg{{color:var(--text)}}
  .edge .lg.ltype,.inset .lg.ltype{{grid-template-columns:minmax(0,3.6fr) minmax(0,8.4fr)}}
  .edge .fbig.serif,.inset .fbig.serif{{font-size:clamp(56px,5.6vw,84px)}}
  .edge .fbig.sans,.inset .fbig.sans{{font-size:var(--xl)}}
  .edge .lbody,.band .lbody{{gap:var(--sp-md)}}
  .edge .fallband{{min-height:80px}}
  .edge .wmhero .wmtext{{font-size:clamp(56px,6.6vw,100px)}}
  .edge .rhuge{{font-size:clamp(44px,5vw,72px)}}
  .inset .lbody{{margin-left:28%;gap:var(--sp-sm)}}
  .inset .fallband{{min-height:60px;flex:0 0 70px}}
  .inset .fallhero{{font-size:var(--x2)}}
  .inset .fine2{{display:none}}
  .inset .rhuge{{font-size:clamp(44px,5vw,72px)}}
  .inset .mhead,.inset .ihead{{margin-bottom:var(--sp-md)}}
  .adedge .foot .doc{{display:none}}
  .adedge .foot{{grid-template-columns:1fr 1fr auto}}
  /* type set in two rows where the sheet is short: faces across, then ladder beside setting */
  .band .lg.ltype,.inset .lg.ltype{{grid-template-columns:1fr}}
  .band .faceshero,.inset .faceshero{{flex-direction:row;align-items:flex-end;gap:var(--sp-xl);flex-wrap:wrap}}
  .band .faceshero .fbig.serif,.inset .faceshero .fbig.serif{{font-size:clamp(48px,5vw,72px)}}
  .band .faceshero .fbig.sans,.inset .faceshero .fbig.sans{{font-size:var(--lg)}}
  .band .lg.ltype .sup,.inset .lg.ltype .sup{{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:var(--sp-md);align-items:start}}
  .band.s5 .bandimg{{height:19%;min-height:0}}
  .band.s6 .bandimg{{height:24%;min-height:0}}
  .inset.s5 .lbody{{margin-left:22%}}
  .adcol .seqrow figure{{aspect-ratio:auto;height:112px}}
  .adcol .adbig{{font-size:clamp(40px,4.4vw,64px)}}
  .adcol .adlead{{margin-bottom:var(--sp-md)}}
  .adcol .seq{{margin-top:var(--sp-md)}}
  /* stage spreads carry their stage as a chip and a bar; the ground keeps falling */
  .schip{{display:inline-block;width:.62em;height:.62em;margin-right:.32em;vertical-align:.04em;box-shadow:0 0 0 1px rgba(238,236,234,.35)}}
  .stagebar{{border:0;height:6px;margin:var(--sp-sm) 0 0}}
  .spread .imgs{{grid-template-columns:minmax(0,1.5fr) repeat(2,minmax(0,1fr));grid-template-rows:repeat(2,auto)}}
  .spread .imgs > figure:first-child{{grid-row:span 2;aspect-ratio:auto}}
  .spread .imgs > figure.open{{display:flex;align-items:center;justify-content:center;text-align:center;
    outline:1px dashed rgba(238,236,234,.45);outline-offset:-1px;font-size:var(--xs);letter-spacing:.12em;
    text-transform:uppercase;color:rgba(238,236,234,.7);line-height:1.6}}
  /* misuse: a cut frame, as large as the lamp */
  .mugrid{{flex:1;display:grid;grid-template-columns:minmax(0,5.4fr) minmax(0,6.6fr);gap:var(--sp-xl);padding-bottom:var(--sp-lg);min-height:0}}
  .cut{{position:relative;margin:0;overflow:hidden;min-height:0}}
  .cut img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 12%}}
  .cut .pill{{position:absolute;top:var(--sp-md);left:var(--sp-md);padding:6px 12px;background:#080808;color:var(--text);
    font-size:var(--xs);letter-spacing:.14em;text-transform:uppercase}}
  .cut figcaption{{position:absolute;left:var(--sp-md);right:var(--sp-md);bottom:var(--sp-md);padding:var(--sp-sm) var(--sp-md);
    background:#080808;color:var(--text);font-size:var(--xs);line-height:1.5;max-width:46ch}}
  .mutext{{display:flex;flex-direction:column;gap:var(--sp-sm);min-width:0}}
  .mutext h2.t{{font-size:var(--x3);margin:0}}
  .mutext .lead{{margin-bottom:var(--sp-sm)}}
  .misuse .misuse-tile{{aspect-ratio:16/10}}
  /* art direction */
  .ad .pk2{{opacity:.8}}
  .adbig{{margin:0 0 var(--sp-md);font-family:var(--display);font-size:clamp(44px,5.4vw,80px);line-height:.98;letter-spacing:-.02em;max-width:12ch}}
  .adlead{{margin:0 0 var(--sp-lg);font-size:var(--base);max-width:46ch;opacity:.88}}
  .adrules{{list-style:none;margin:0;padding:0;counter-reset:r}}
  .adrules li{{counter-increment:r;display:grid;grid-template-columns:28px minmax(0,1fr);column-gap:var(--sp-sm);
    padding:var(--sp-xs) 0;border-top:1px solid currentColor;border-color:rgba(238,236,234,.25)}}
  .adrules li:first-child{{display:none}}
  .adrules li::before{{content:counter(r,decimal-leading-zero);grid-row:span 2;font-size:var(--xs);opacity:.7;padding-top:4px}}
  .ar{{margin:0;font-family:var(--display);font-size:var(--lg);line-height:1.1}}
  .arn{{font-family:var(--body);font-size:.86em;letter-spacing:.01em}}
  .ard{{margin:2px 0 0;font-size:var(--xs);opacity:.78}}
  .seq{{margin-top:var(--sp-lg)}}
  .seqrow{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--sp-xs);margin-top:var(--sp-xs)}}
  .seqrow figure{{position:relative;margin:0;aspect-ratio:4/5;overflow:hidden}}
  .adcol .adgrid{{flex:1;display:grid;grid-template-columns:minmax(0,6fr) minmax(0,6fr);gap:var(--sp-xl);padding-bottom:var(--sp-lg);min-height:0}}
  .adhero{{position:relative;margin:0 0 0 calc(var(--pad) * -1);margin-top:calc(var(--pad) * -1);overflow:hidden}}
  .adedge{{padding-left:calc(58% + var(--pad))}}
  .adeimg{{position:absolute;left:0;top:0;bottom:0;width:58%;margin:0;overflow:hidden}}
  .adedge .adtext{{flex:1;display:flex;flex-direction:column}}
  .adedge .adbig{{font-size:clamp(40px,4.4vw,64px)}}
  .adedge .adlead{{display:none}}
  .adband{{padding-top:0}}
  .adbandimg{{position:relative;margin:0 calc(var(--pad) * -1) var(--sp-lg);flex:1;min-height:0;overflow:hidden}}
  .adbelow{{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:var(--sp-xl);padding-bottom:var(--sp-lg)}}
  .adbelow .adbig{{font-size:clamp(36px,3.8vw,56px)}}
  .adbelow .adrules{{columns:2;column-gap:var(--sp-xl)}}
  .adbelow .adrules li{{break-inside:avoid}}
  .adinset{{color:var(--text)}}
  .adinset > *:not(.fullimg){{position:relative}}
  .adpanel{{align-self:flex-end;width:min(520px,42%);padding:var(--sp-lg)}}
  .adinset .seq{{position:absolute;left:var(--pad);bottom:72px;width:min(560px,40%);margin:0}}
  .adinset .seq .pk2{{color:var(--text);text-shadow:0 1px 8px rgba(0,0,0,.6)}}
  .adinset .foot{{margin-top:auto;background:#080808;margin-left:calc(var(--pad) * -1);margin-right:calc(var(--pad) * -1);
    padding-left:var(--pad);padding-right:var(--pad);border-top:0;color:var(--muted)}}
  .adinset .foot .mark,.adinset .foot .pg{{color:var(--text)}}
"""

# ---- the ember (spec 2026-10-11-afterglow-ember-design.md, option 1): one engine behind every sheet ----
# Everything reacts (Aaron, 11 Oct): every surface takes a rim and a glow, every piece of text an edge light.
# Inline runs (b, em) and the small chips take their parent's light. The cover keeps its own photograph and shade.
EMBER_CARDS = ".deck .sheet:not(.bcover) :is(.panel, .wtile, .sw, .appbody, .appimg, .pcard, .plabel, .pposter, .fallband, .step, figure)"
EMBER_TEXT = (".deck .sheet:not(.bcover) :is(h2, h3, p, li, dt, dd, th, td, figcaption, a, .foot span, .wspec, .wpill, .pill, "
              ".tlab, .tsamp, .tnum, .stageread, .btn, .pwm, .wmtext, .pfine, .tri > span)")
EMBER_LIT = EMBER_CARDS + ", " + EMBER_TEXT
EMBER_CSS = f"""
  /* the ember: a canvas behind the sheets that draws every sheet's ground once it has drawn its first frame */
  #ember{{position:fixed;inset:0;z-index:0;pointer-events:none}}
  #ember canvas{{display:block;width:100%;height:100%}}
  .deck{{position:relative;z-index:1}}
  @media screen{{.ember-on .sheet:not(.bcover){{background:transparent!important}}}}
  @media print{{#ember{{display:none}}}}
  /* what it lights (spec 2.7): a 2px rim brightest at the edge nearest it, a faint wash, a 24px glow. Nothing is cast. */
  {EMBER_CARDS},{EMBER_TEXT}{{--li:0;--ec:216,178,96;--px:50%;--py:-200px;--rr:312px;--tx:0px;--ty:0px}}
  :where({EMBER_CARDS}){{position:relative}}
  {EMBER_CARDS}::before{{content:"";position:absolute;inset:0;pointer-events:none;border:2px solid transparent;
    border-image:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),var(--li)) 0%,rgba(var(--ec),calc(.45 * var(--li))) 45%,rgba(var(--ec),calc(.1 * var(--li))) 90%,transparent 100%) 1}}
  {EMBER_CARDS}::after{{content:"";position:absolute;inset:0;pointer-events:none;mix-blend-mode:screen;
    background:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),calc(.2 * var(--li))),rgba(var(--ec),calc(.05 * var(--li))) 45%,transparent 75%);
    box-shadow:0 0 24px rgba(var(--ec),calc(.32 * var(--li)))}}
  {EMBER_TEXT}{{text-shadow:var(--tx) var(--ty) 0 rgba(var(--ec),calc(.9 * var(--li))),0 0 10px rgba(var(--ec),calc(.35 * var(--li)))}}
  @media print{{{EMBER_CARDS}::before,{EMBER_CARDS}::after{{display:none}}{EMBER_TEXT}{{text-shadow:none}}}}
"""
# The ground under a point is the innermost sheet (or [data-ground]) there, read from its own inline gradient.
GUIDE_JS = """
function guideGroundAt(t) {
  var g = guideGroundAt, H = document.documentElement.scrollHeight, now = performance.now();
  if (!g.c || g.h !== H || now - g.at > 100) {
    var hex = function (h) { return [1, 3, 5].map(function (i) { return parseInt(h.slice(i, i + 2), 16); }); };
    g.c = [].slice.call(document.querySelectorAll(".sheet, [data-ground]")).map(function (el) {
      var r = el.getBoundingClientRect(), m = /linear-gradient\(180deg,([^)]*)\)/.exec(el.getAttribute("style") || ""), stops = null;
      if (m) {
        var parts = m[1].split(",");
        stops = parts.map(function (p, i) { var q = /(#[0-9a-fA-F]{6})\s*([\d.]+)?%?/.exec(p.trim());
          return q && [q[2] !== undefined ? parseFloat(q[2]) / 100 : i / (parts.length - 1), hex(q[1])]; });
        if (stops.some(function (s) { return !s; })) stops = null;
      }
      return { top: r.top + scrollY, h: r.height, stops: stops };
    }).sort(function (a, b) { return a.h - b.h; });
    g.h = H; g.at = now;
  }
  var y = t * H;
  for (var n = 0; n < g.c.length; n++) { var s = g.c[n]; if (y < s.top || y >= s.top + s.h) continue;
    if (!s.stops) return [8, 8, 8];
    var k = (y - s.top) / s.h, S = s.stops;
    if (k <= S[0][0]) return S[0][1];
    for (var i = 1; i < S.length; i++) if (k <= S[i][0]) { var a = S[i - 1], b = S[i], f = (k - a[0]) / ((b[0] - a[0]) || 1);
      return a[1].map(function (v, j) { return v + (b[1][j] - v) * f; }); }
    return S[S.length - 1][1];
  }
  return [8, 8, 8];
}
(function () {
  function start() {
    if (!window.EmberEngine || start.done) return;   // window.ember is the #ember div until this runs
    start.done = true;
    var root = document.documentElement;
    window.ember = new EmberEngine(document.getElementById("ember"), {
      groundAt: guideGroundAt, lit: "LIT",
      onFirstFrame: function () { root.classList.add("ember-on"); },
      onLost: function () { root.classList.remove("ember-on"); }
    });
  }
  if (document.readyState === "complete") start(); else addEventListener("load", start);
})();
"""


def with_ember(html):
    """Inline the engine bundle (the deck stays a single file) and the container behind the sheets."""
    bundle = (D.ROOT / "brand/ember/ember.bundle.js").read_text().replace("</script", "<\\/script")
    html = html.replace("</style>", EMBER_CSS + "</style>", 1)
    html = html.replace("<body>\n", '<body>\n<div id="ember" aria-hidden="true"></div>\n', 1)
    js = GUIDE_JS.replace('"LIT"', '"' + EMBER_LIT + '"')
    return html.replace("</body>", f"<script>{bundle}</script>\n<script>{js}</script>\n</body>", 1)


# ---- copy pass (11 Oct): written for a reader who was not in the room ----
def _rep(html, old, new):
    """Replace old with new, tolerant of the source's line wrapping; fail loudly if old is gone."""
    pat = r"\s+".join(re.escape(w) for w in old.split())
    out, n = re.subn(pat, lambda m: new, html)
    assert n, f"copy pass: not found: {old[:60]}"
    return out


COPY = [
    ("There is no drawn logotype. The wordmark is the typeface.",
     "There is no drawn logotype. The wordmark is Instrument Serif, widened to 150%."),
    ("Instrument Serif 400, tracking 0.", "Instrument Serif 400 at 150% width, tracking 0."),
    # cover: its copy is the hour's note now (cover_hour), so the old cover line has no entry here
    # art direction: the light is an hour, so the shoot has one
    ("Images are made at the end of the day or lit to look as though they were.",
     "Images are made between 19:12 and 21:30, or lit to look as though they were."),
    # wordmark
    ("Outside the four stages and the two text neutrals.", "Only the palette, and only the pairs that pass on page 03."),
    ("Do not set small on the fall", "Do not set it small on the gradient"),
    ("Below 24 px it fails its floor somewhere on the ramp.", "Below 24 px it loses contrast somewhere along the gradient."),
    ("If the face is unavailable the wordmark is set as an image, not in a fallback.",
     "If Instrument Serif is unavailable, place the wordmark as an image. Never set it in another typeface."),
    # colour
    ("One ramp. Lightness falls and chroma stays flat at 0.110, so the stages differ in depth, not intensity.",
     "The brand&rsquo;s four colours, called stages, run from sunset into night. Each is darker than the last at the same "
     "intensity, so together they read as one light deepening."),
    ("<dt>Text on it</dt>", "<dt>#EEECEA on it</dt>"),
    ("<dt>On void</dt>", "<dt>On #080808</dt>"),
    ('<p class="swr">Text, marks, rules</p>', '<p class="swr">For text, logo and lines</p>'),
    ('<p class="swr">Ground only</p>', '<p class="swr">Backgrounds only, never as text</p>'),
    ("Body floor 4.5:1, large-text floor 3:1. CMYK is converted for a proof, not matched; each Pantone is matched against a physical guide and written back here.",
     "Each ratio is the contrast against that background. Body text needs 4.5:1 and large text 3:1. CMYK is for proofing "
     "only. Pantone matches will be added after the first print proof."),
    # the fall
    ("The gradient is an asset with a specification, not an effect applied by eye.",
     "The fall is the brand&rsquo;s gradient: the four stages in order, falling to black and ending on a sliver of magenta. Build it from these values, never by eye."),
    ("Border is rgba(192,192,192,0.22), a hairline. No neutral is a stage and no stage is a neutral.",
     "Borders are a hairline of #C0C0C0 at 22% opacity. A stage colour never stands in for a neutral, and a neutral never stands in for a stage."),
    ("Interpolated in sRGB. Specifying it in another space changes every intermediate value and the measured ratios stop holding.",
     "On screen, blend it in sRGB; any other colour space shifts the middle colours. For print, build the file from the same stops."),
    ("Four stages fall to the void and end on a sliver of #BF15B7. No stage may be added, moved or removed.",
     "The four stages fall to black, #080808, at 95%, then to a sliver of magenta, #BF15B7, over the last 3%. No stop may be added, moved or removed."),
    ("Nothing smaller than 24&nbsp;px of type sits directly on it. Type on the fall uses the floor for the darkest value it crosses.",
     "No type under 24&nbsp;px sits directly on it. Larger type must reach 3:1 against the darkest point it crosses."),
    # type
    ("Both are in Shopify&rsquo;s library. The scale is a ratio of 1.25, not a list.",
     "Instrument Serif for headings and the wordmark, Space Grotesk for everything else. Both are free in Shopify&rsquo;s "
     "font library. Each size is 1.25 times the one below it."),
    # grid
    ("Twelve columns in both media, one spacing base that divides the type base.",
     "Twelve columns on screen and in print. Every space is one of eight steps from 4 to 64 px."),
    ("The one rule here that can be checked in a diff.", "It is the one rule a developer can check in the code."),
    ("Square. Restraint and a dark ground point there.", "Square corners on everything."),
    ("Elevation reads through the two surface steps.", "Depth comes from the two surface colours, never from a shadow."),
    ("cubic-bezier(0.2, 0, 0.2, 1). Ends at its destination, never passes it.",
     "Eases in and out and stops where it lands, with no bounce. cubic-bezier(0.2, 0, 0.2, 1)."),
    # art direction
    ("The upper quartile of an image's lightness sits at or below the gold of last light,",
     "No more than a quarter of an image is brighter than gold of last light,"),
    ("Up to a quarter of the frame may pass it; the rest may not.",
     "Check it on the file: in a lightness histogram, the brightest quarter sits at or below L 0.781."),
    ("A sequence follows the ramp in the same direction the ramp runs.",
     "In a set, each image runs cooler than the one before it, gold first and violet last."),
    ("The palette is where the shadows and the highlights land.", "Shadows and highlights land on the stage colours, not on grey."),
    # misuse
    ("From the offcuts. Cold where", "A frame rejected from the set. Cold where"),
    ("Six ways to break the five rules, beside a frame cut from the brand. Each tile is built from tokens; the photograph is the real thing.",
     "Five rules from the art direction on page 07, each shown right and wrong. The tiles are diagrams. The photograph is a real frame rejected from the set."),
    ('<h2 class="t">Misuse</h2>', '<h2 class="t">Use and misuse</h2>'),
    ("Breaks the upper quartile at or below gold: over a quarter of it passes.",
     "Breaks the brightness limit: over a quarter of the frame is brighter than gold."),
    # applications
    ("Hover deepens: L 0.781 to L 0.630", "On hover the button darkens, from L 0.781 to 0.630. It never lightens. "
     "The light only brightens where the ember is."),
    # the one rule (spec 4): the ember is where the light brightens; states still deepen
    ("No state change brightens.", "The light only brightens where the ember is."),
    ("Hover, focus and active deepen or shift hue and never lighten.", "Hover, focus and active states still deepen and never lighten."),
    # chroma (spec 4)
    ('<p class="fine2">Each ratio is the contrast',
     '<p class="fine2">Chroma is flat at 0.110 on every stage. The ember is the one exception, an accent of contrast that '
     'raises the chroma of the colour it sits on.</p><p class="fine2">Each ratio is the contrast'),
    # one wrapped rule on the art direction sheet
    ("In print and film a later panel is never lighter than the one before it.",
     "In print and film, each panel or frame is never lighter than the one before it."),
    # production notes
    ("Proof on the stock, not on a house sheet.", "Proof on the stock it will print on, not the printer&rsquo;s standard paper."),
    ("No placed image has an upper quartile above gold, L 0.781.", "No placed image has more than a quarter of its frame brighter than gold, L 0.781."),
    ("A specular finish reverses the one rule wherever the light catches it.", "A glossy finish brightens wherever the light catches it, which breaks the one rule."),
    # voice
    ("Cart, checkout, shipping notices,", "Product copy uses this voice. Cart, checkout, shipping notices,"),
    ("The full voice, the word lists and the tone by context live in", "The full voice guide, with word lists and the tone for each page, is a separate document available from the brand owner:"),
    ("Event art direction for the launch is in", "Art direction for the launch event is in"),
    ("governs that night only; nothing in it binds the brand.", "applies to that night only. Nothing in it binds the brand."),
]

# what each stage is for, set under its bar
STAGE_CAPS = [
    "The last direct sun: warm, low and close to the skin. A set opens here.",
    "Copper and terracotta just after the sun drops. Skin, walls and sand still hold the heat.",
    "Wine-rose as the warmth fades, the light bouncing off walls and skin.",
    "Blue-violet night with one warm source at most. A set ends here.",
]

# the wordmark's six don'ts, drawn rather than listed
WM_DONTS = [  # the pill says don't, so the label names the mistake
    ("Recolour", "Only the pairs that pass on page 03.", 'style="color:#3D7BE0"', "Afterglow"),
    ("Narrow it", "Always 150% wide. Never the face&rsquo;s own width, never wider.", 'style="transform:none"', "Afterglow"),
    ("Outline", "No stroke, shadow or glow.",
     'style="color:transparent;-webkit-text-stroke:1px #EEECEA;text-shadow:0 0 14px rgba(216,178,96,.8)"', "Afterglow"),
    ("Stack", "One line. The word never breaks.", 'style="line-height:.86"', "After<br>glow"),
    ("Substitute", "No other typeface. If the font is missing, place it as an image.",
     'style="font-family:Georgia,\'Times New Roman\',serif;font-style:italic;font-weight:700"', "Afterglow"),
]


# and four that are right, each a pair that passes on the colour page
WM_DOS = [
    ("On black", "#EEECEA, the default. Gold of last light also passes.", "#080808", "#EEECEA"),
    ("On gold", "#080808 only. Nothing light sits on gold.", "#D8B260", "#080808"),
    ("On rose", "#EEECEA. Gold and #C0C0C0 pass at wordmark size.", "#893A50", "#EEECEA"),
    ("On deep violet", "#EEECEA or gold, the mark at night.", "#341D5E", "#D8B260"),
    ("On the fall", "#EEECEA at full size, crossing after gold and deeper.", "var(--fall)", "#EEECEA"),
]


def wm_tiles():
    dos = "".join(
        f'<div class="wdont"><div class="wtile" style="background:{bg};color:{fg}"><span class="wpill wdo">Do</span>'
        f'<span class="wspec" style="color:inherit">Afterglow</span></div><p class="dk">{k}</p><p>{d}</p></div>'
        for k, d, bg, fg in WM_DOS)
    cells = "".join(
        f'<div class="wdont"><div class="wtile"><span class="wpill">Don&rsquo;t</span>'
        f'<span class="wspec" {sty}>{word}</span></div><p class="dk">{k}</p><p>{d}</p></div>'
        for i, (k, d, sty, word) in enumerate(WM_DONTS))
    return (f'<h3 class="bt">Use it like this</h3><div class="wdonts wdos">{dos}</div>'
            f'<h3 class="bt">Five ways to break it</h3><div class="wdonts">{cells}</div>')


# the imagery rules, each shown right and wrong (11 Oct); the tiles are diagrams built from the palette
IMG_PAIRS = [
    ("One source", "radial-gradient(circle at 16% 18%,#D8B260 0,#BC6F4C 24%,#893A50 48%,#080808 86%)",
     "radial-gradient(circle at 12% 20%,#D8B260,transparent 55%),radial-gradient(circle at 88% 80%,#341D5E,transparent 55%),#080808",
     "One low, warm source. Not a second light."),
    ("Light that falls", "linear-gradient(115deg,#D8B260,#BC6F4C 30%,#893A50 62%,#080808)", "#893A50",
     "Light rakes across and falls away. Not flat and even."),
    ("Brightness limit", "linear-gradient(180deg,#D8B260 0,#D8B260 18%,#BC6F4C 45%,#893A50 72%,#341D5E)",
     "linear-gradient(180deg,#EEECEA 0%,#EEECEA 38%,#D8B260 62%,#893A50)",
     "The brightest quarter stops at gold. Not white highlights."),
    ("Graded to the stages", "linear-gradient(180deg,#BC6F4C,#341D5E)", "linear-gradient(180deg,#C0C0C0,#2B2B2B)",
     "Shadows and highlights land on stage colours. Not on grey."),
    ("Exposed at capture", "radial-gradient(circle at 50% 30%,#893A50 0,#893A50 28%,#080808 88%)",
     "linear-gradient(rgba(238,236,234,.4),rgba(238,236,234,.4)),#893A50",
     "Shadows stay deep, exposed right in camera. Not lifted in post."),
]


def img_pairs():
    rows = "".join(
        f'<div class="mprow"><div class="wtile" style="background:{do}"><span class="wpill wdo">Do</span></div>'
        f'<div class="wtile" style="background:{dont}"><span class="wpill">Don&rsquo;t</span></div>'
        f'<div class="mptext"><p class="dk">{k}</p><p>{d}</p></div></div>'
        for k, do, dont, d in IMG_PAIRS)
    return f'<div class="panel mplist">{rows}</div>'


def copy_pass(html):
    for old, new in COPY:
        html = _rep(html, old, new)
    html = _rep(html, '<h3 class="bt">Six ways to break it</h3>', '')
    i = html.index('imagery s2"'); a = html.index('<div class="panel"><div class="donts">', i)
    b = html.index("</div>\n        </div></div>", a) + len("</div>\n        </div>")
    html = html[:a] + wm_tiles() + html[b:]
    i = html.index('imagery misuse'); a = html.index('<div class="panel ">', i)
    b = html.index("</div>\n        </div>", a) + len("</div>\n        </div>")
    html = html[:a] + img_pairs() + html[b:]
    for k, cap in enumerate(STAGE_CAPS):
        bar = f'<hr class="stagebar" style="background:{STAGES[k][1]}">'
        if f'data-hour="{k}"' in html: continue  # an hour sheet carries its caption already
        assert bar in html
        html = html.replace(bar, bar + f'<p class="stagecap">{cap}</p>', 1)
    return html


# B1 polish (10 Oct, approved spec): one template on desktop, one column on a phone.
POLISH_CSS = f"""
  /* offline, the fallback face sets the wordmarks wider; a sheet clips sideways rather than scrolling the page */
  .sheet{{overflow-x:clip}}
  .wdonts{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--sp-md) var(--sp-lg)}}
  .wdont .dk,.wdont p{{color:inherit !important}}
  .arn{{white-space:nowrap}}
  .wdont .dk{{margin:var(--sp-xs) 0 2px}}
  .wdont p:not(.dk){{margin:0;font-size:var(--xs);line-height:1.45;opacity:.85}}
  .wtile{{position:relative;height:84px;background:#080808;display:flex;align-items:center;justify-content:center;overflow:hidden}}
  .wtile.wfall{{background:var(--fall)}}
  .wdonts.wdos,.wdonts:not(.wdos){{grid-template-columns:repeat(5,minmax(0,1fr));gap:var(--sp-md)}}
  .wdos{{margin-bottom:var(--sp-lg)}}
  .wdonts .wspec{{font-size:24px}}
  .wdonts .wspec[style*="Georgia"]{{font-size:19px}}
  /* the standard wordmark (11 Oct): Instrument Serif at 150% width; margin returns the extra width to the layout */
  .wordmark,.wmtext,.pwm,.aname{{display:inline-block;width:max-content!important;letter-spacing:0!important;white-space:nowrap;transform:scaleX(1.5);transform-origin:0 50%;margin-right:1.63em}}
  .night .pcard .pwm{{color:#EEECEA}}
  @media screen and (min-width:993px){{.adcol .adhero{{margin-top:0}}}}
  /* running head (11 Oct): the title strip tops every sheet, its rule above it */
  .sheet.sheet{{padding-top:0;padding-bottom:var(--pad)}}
  .sheet .foot{{order:-1;border-top:1px solid;border-bottom:0;padding:var(--sp-sm) 0 0;margin:var(--sp-md) 0 var(--sp-xl)!important}}
  .sheet.bcover .foot{{margin:var(--sp-md) var(--pad) 0!important;position:relative;z-index:3}}
  .sheet.bcover .foot,.sheet.bcover .foot span{{color:#EEECEA!important;border-color:rgba(238,236,234,.4)}}
  .foot{{grid-template-columns:1fr 1fr 1fr auto auto}} .adedge .foot{{grid-template-columns:1fr 1fr auto auto}}
  .foot .hr{{font-variant-numeric:tabular-nums;letter-spacing:.14em;text-transform:uppercase}}
  @media screen and (max-width:900px){{.foot{{grid-template-columns:1fr auto auto}}}}
  .bcover .bimg::before{{content:"";position:absolute;inset:0 0 auto;height:140px;z-index:1;background:linear-gradient(180deg,rgba(8,8,8,.62),rgba(8,8,8,0))}}
  .bcover.sheet.sheet{{padding:0!important}}
  @media screen and (max-width:576px){{.sheet.sheet{{padding-bottom:var(--sp-lg)}}}}
  .wspec{{transform:scaleX(1.5);transform-origin:50% 50%;white-space:nowrap}}
  @media screen and (max-width:992px){{.aname{{font-size:clamp(28px,5.4vw,48px)!important}}.pwm{{font-size:clamp(18px,2.9vw,26px)!important}}}}
  .wpill.wdo{{background:#080808;color:#EEECEA;box-shadow:inset 0 0 0 1px rgba(238,236,234,.6)}}
  .cut .pill,.cut figcaption{{background:#EEECEA!important;color:#080808!important}}
  /* page 13: the five rules as a ruled list, each row a do, a don't and the line that tells them apart */
  .mplist{{flex:1;display:grid;grid-template-rows:repeat(5,minmax(0,1fr));padding-top:var(--sp-sm);padding-bottom:var(--sp-sm)}}
  .mprow{{display:grid;grid-template-columns:64px 64px minmax(0,1fr);gap:4px;align-items:center;border-top:1px solid rgba(238,236,234,.14);padding:var(--sp-xs) 0}}
  .mprow:first-child{{border-top:0}}
  .mprow .wtile{{height:64px}}
  .mptext{{padding-left:var(--sp-lg)}}
  .mptext .dk{{margin:0 0 2px}}
  .mptext p:not(.dk){{margin:0;font-size:var(--xs);line-height:1.45;opacity:.85}}
  /* page 14: each print piece at its true proportion, standing on one baseline */
  .night .prints{{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:flex-start;gap:var(--sp-2xl)}}
  .night .prints .app{{flex:0 0 auto}}
  .night .prints .pcard,.night .prints .plabel,.night .prints .pposter{{height:144px!important;width:auto;max-height:none!important}}
  .night .prints .pcard{{aspect-ratio:85/55!important}}
  .night .prints .plabel{{aspect-ratio:1/1!important;background:#080808;padding:0;overflow:hidden}}
  .night .prints .pposter{{aspect-ratio:2/3!important}}
  .plabel .plfall{{flex:1;background:var(--fall);padding:var(--sp-sm)}}
  .plabel .pwm.sm{{font-size:16px!important}}
  .plabel .pfine{{display:block;padding:5px var(--sp-sm);background:#080808;color:#EEECEA;white-space:nowrap;font-size:10px}}
  .wspec{{font-family:var(--display);font-size:34px;line-height:1;color:#EEECEA;text-align:center}}
  .wpill{{position:absolute;top:6px;left:6px;padding:2px 6px;background:#EEECEA;color:#080808;font-size:9px;letter-spacing:.14em;text-transform:uppercase}}
  @media screen and (max-width:576px){{.wdonts{{grid-template-columns:1fr}}}}
  :root{{--fall:linear-gradient(180deg,#D8B260,#BC6F4C 30%,#893A50 60%,#341D5E 84%,#080808 95%,#080808 97.2%,{MAGENTA} 99.4%)}}
  .spread.violet .stagebar{{box-shadow:0 0 0 1px rgba(238,236,234,.35)}}
  @media screen and (min-width:993px){{
    .sheet{{height:var(--sheet-h);min-height:0}}
    /* page 2: the wordmark across the sheet, the six ways in a row of three beneath it */
    .s2 .lg.l75{{grid-template-columns:1fr;align-content:space-between;flex:1}}
    .s2 .wmhero{{flex-direction:row;align-items:flex-end;gap:var(--sp-xl)}}
    .s2 .wmhero .wmtext{{font-size:clamp(96px,8.4vw,128px)}}
    .s2 .wtile{{height:72px}}
    .s2 .wmhero .cap2{{max-width:30ch;margin:0}}
    .s2 .sup .donts{{grid-template-columns:repeat(3,minmax(0,1fr))}}
    /* page 5: faces and their roles share a column, the scale takes the other */
    .s5 .lg.ltype{{grid-template-columns:minmax(0,5fr) minmax(0,7fr);flex:1;align-items:stretch}}
    .s5 .faceshero{{justify-content:space-between}}
    .s5 .sup{{display:flex;flex-direction:column}}
    .s5 .sup .panel{{flex:1;display:flex;flex-direction:column}}
    .s5 .tspec{{flex:1;display:flex;flex-direction:column;justify-content:space-between}}
    /* page 6: the column overlay sits behind the panels, not the copy */
    .s6 .gbg{{top:56%}}
    .spread .stagecap{{margin:var(--sp-sm) 0 0;font-size:var(--base);max-width:62ch;opacity:.86}}
    .spread .stagecap + .imgs{{margin-top:var(--sp-lg)}}
    /* page 4: every neutral's name holds two lines, so the readings sit on one row */
    .neut .nc > p:not(.m){{min-height:2.6em}}
    /* page 13: the tile panel ends where the photograph ends */
    .mutext > :last-child{{margin-top:auto}}
    /* page 14: the production notes clear the footer like every other sheet */
    .night .lbody{{padding-bottom:var(--sp-xl)}}
    .night .prod .rules li{{line-height:1.4}}
    .spread .imgs{{flex:1;min-height:0;margin:var(--sp-2xl) 0 var(--sp-lg);grid-template-rows:repeat(2,minmax(0,1fr))}}
    .spread .imgs > figure{{aspect-ratio:auto;min-height:0}}
  }}
  /* tablet: sheets take their natural height, the photograph drops under its title */
  @media screen and (max-width:992px){{
    .sheet{{height:auto;min-height:0}}
    .carry,.adcol .adgrid,.mugrid{{grid-template-columns:1fr}}
    .carry .ph figure{{flex:none;aspect-ratio:4/3}}
    .lg,.lg.l75,.lg.l57,.lg.ltype,.lg.lapps,.lg.lvoice{{grid-template-columns:1fr}}
    .lg.l444{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .lg.l444 > :first-child{{grid-column:1 / -1}}
    .swatches{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .sw dd{{white-space:normal}}
    .adhero{{margin:0;aspect-ratio:4/3}}
    .cut{{aspect-ratio:4/3}}
    .spread .imgs{{grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:none;margin:var(--sp-lg) 0}}
    .spread .imgs > figure{{aspect-ratio:5/4}}
    .spread .imgs > figure:first-child{{grid-column:1 / -1;grid-row:auto;aspect-ratio:3/2}}
    .gbg{{display:none}}
  }}
  /* phone: one column, 16px gutters, nothing wider than the screen */
  @media screen and (max-width:576px){{
    .sheet{{padding:var(--sp-md) var(--sp-md) 0}}
    .mhead{{flex-wrap:wrap;gap:var(--sp-sm)}}
    .sheet .mhead h2.t,.carry .ph h2.t,.stagename{{font-size:clamp(28px,8vw,40px);white-space:normal}}
    .wmhero .wmtext,.s2 .wmhero .wmtext{{font-size:clamp(40px,12vw,96px)}}
    .wmhero .wmbox{{padding:var(--sp-md)}}
    .s2 .wmhero{{flex-direction:column;align-items:flex-start}}
    .sup .donts,.s2 .sup .donts,.donts{{grid-template-columns:1fr}}
    .wdonts.wdos,.wdonts:not(.wdos){{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .swatches,.lg.l444,.trio{{grid-template-columns:1fr}}
    .spread .imgs{{grid-template-columns:1fr}}
    .spread .imgs > figure:first-child{{grid-column:auto;aspect-ratio:4/5}}
    .lbody .tbl{{table-layout:fixed;width:100%;font-size:11px}}
    .lbody .tbl th,.lbody .tbl td{{padding-right:6px;white-space:normal;overflow-wrap:break-word}}
    .lbody .tbl th{{letter-spacing:.02em;font-size:9.5px}}
    /* the two largest specimens cannot fit a phone at true size; they scale to the screen */
    .tsamp[style*="3.815rem"]{{font-size:12.5vw!important}}
    .tsamp[style*="3.052rem"]{{font-size:11vw!important}}
    .lbody .tstep{{grid-template-columns:34px minmax(0,1fr) auto}}
    .tsamp{{overflow:hidden;text-overflow:clip}}
    .rhuge,.adbig,.fallhero{{font-size:clamp(36px,11vw,56px)}}
  }}
"""


if __name__ == "__main__":
    import afterglow_specimen  # b1 is the guide itself: the specimen build (spec 2026-10-12) wraps it
    for key in VARIANTS:
        html, n = afterglow_specimen.build() if key == "b1-column" else build(key)
        p = D.ROOT / f"brand/2026-10-10-density-{key}.html"
        p.write_text(html)
        print(p.relative_to(D.ROOT), n, "photographs, none repeated")
