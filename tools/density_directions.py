"""Builds three density directions for the Afterglow guide from the rendered guide itself.

Every panel, table and photograph is lifted verbatim from brand/2026-10-09-afterglow-brand-guide.html,
so a direction can only differ in layout and order, never in content. Writes:
  brand/2026-10-10-density-a-light-first.html
  brand/2026-10-10-density-b-carried-stage.html
  brand/2026-10-10-density-c-contact-sheet.html
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = (ROOT / "brand/guide-sources/2026-10-09-afterglow-brand-guide.html").read_text()
CSS = re.search(r"<style>(.*?)</style>", SRC, re.S).group(1)
HEAD = SRC.split("<style>")[0]

STAGES = [("Gold of last light", "#D8B260", "0.781", "dark"),
          ("After gold", "#BC6F4C", "0.619", "dark"),
          ("Rose", "#893A50", "0.461", "light"),
          ("Deep violet", "#341D5E", "0.301", "light")]
FALL = ["#D8B260", "#BC6F4C", "#893A50", "#341D5E"]


def sections():
    out = {}
    for m in re.finditer(r'<section class="sheet ([^"]*)" data-sheet="(\d+)"(.*?)</section>', SRC, re.S):
        body = m.group(3)
        h2 = re.search(r'<h2 class="(?:t|stagename)">(.*?)</h2>', body, re.S)
        lead = re.search(r'<p class="lead">(.*?)</p>', body, re.S)
        colr = re.search(r'<div class="col-r">(.*)</div>\s*</div>\s*<footer', body, re.S)
        imgs = re.findall(r'<figure data-stage="\d">.*?</figure>', body, re.S)
        out[m.group(2)] = dict(h2=h2 and h2.group(1), lead=lead and lead.group(1),
                               colr=colr and colr.group(1), imgs=imgs, body=body)
    return out


S = sections()
# Stills only, so the board renders the same frame every time: a video keeps its poster.
PHOTOS = [[re.sub(r'<video class="scr".*?</video>\s*', "", f, flags=re.S).replace('class="prt" ', "")
           for f in S[n]["imgs"]] for n in ("13", "14", "15", "16")]


def src_of(fig):
    return re.search(r'src="([^"]+)"', fig).group(1)


def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def fall_at(t):
    """Colour on the fall at t in 0..1."""
    t = max(0, min(1, t)) * 3
    i = min(int(t), 2)
    return mix(FALL[i], FALL[i + 1], t - i)


def ground(i, n):
    a, b = fall_at(i / n), fall_at((i + 1) / n)
    ink = "dark" if (i + .5) / n < .45 else "light"
    return f"background:linear-gradient(180deg,{a},{b})", ink


def foot(section, pg):
    return (f'<footer class="foot"><span class="mark">Afterglow</span><span>{section}</span>'
            f'<span class="doc">Afterglow Brand Guide &middot; October 2026</span>'
            f'<span class="pg">{pg:02d}</span></footer>')


def blk(n, title=None, lead=True):
    s = S[n]
    t = title or s["h2"]
    ld = f'<p class="blead">{s["lead"]}</p>' if lead and s["lead"] else ""
    return f'<div class="blk"><h3 class="bt">{t}</h3>{ld}<div class="bbody">{s["colr"]}</div></div>'


def stage_sheet(k, pg, cls="", extra=""):
    name, hexv, L, ink = STAGES[k]
    figs = "".join(PHOTOS[k])
    return (f'<section class="sheet {ink} imagery {cls}" style="background:{hexv}">'
            f'<div class="stagehead"><h2 class="stagename">{name}</h2>'
            f'<span class="stageread">{hexv} &middot; L {L}</span></div><hr class="stagerule">'
            f'{extra}<div class="imgs">{figs}</div>{foot("Imagery", pg)}</section>')


EXTRA_CSS = """
  /* density directions: shared */
  .mhead{display:flex;align-items:baseline;gap:var(--sp-xl);margin-bottom:var(--sp-lg)}
  .mhead .lead{max-width:60ch}
  .mgrid{flex:1;display:grid;gap:var(--sp-lg);padding-bottom:var(--sp-lg);min-height:0;align-content:start}
  .mgrid.c2{grid-template-columns:repeat(2,minmax(0,1fr))}
  .mgrid.c3{grid-template-columns:repeat(3,minmax(0,1fr))}
  .mgrid .span2{grid-column:span 2}
  .blk{display:flex;flex-direction:column;gap:var(--sp-xs);min-width:0}
  .bt{margin:0;font-family:var(--display);font-weight:400;font-size:var(--lg);line-height:1.1}
  .blead{margin:0 0 var(--sp-2xs);font-size:var(--xs);max-width:52ch;opacity:.8}
  .bbody{display:flex;flex-direction:column;gap:var(--sp-sm);min-width:0}
  .bbody .fine{display:none}
  .bbody .wmstage{padding:var(--sp-md) 0}
  .bbody .wmtext{font-size:clamp(40px,4.4vw,64px)}
  .bbody .panel{padding:var(--sp-sm) var(--sp-md)}
  .bbody .tbl td{padding:6px var(--sp-xs) 6px 0}
  .bbody .tbl th{padding-right:var(--sp-xs)}
  .bbody .dot{margin-right:var(--sp-xs)}
  .bbody .srow{padding:6px 0}.bbody .chip{height:40px}
  .bbody .fallbar{min-height:150px}
  .bbody .gcols{height:64px}
  .bbody .rbig{font-size:var(--lg)}
  .bbody .tstep{grid-template-columns:34px minmax(0,1fr) 116px;gap:var(--sp-sm)}
  .bbody .tbl th,.bbody .tbl td{white-space:normal}
  .bbody .tbl th{letter-spacing:.06em}
  .sheet.night{background:#080808;color:var(--text)}
  .sheet.night .panel{background:#141414}
  .sheet.night .lead,.sheet.night .blead{color:var(--muted);opacity:1}
  .sheet.night .foot{border-color:var(--border);color:var(--muted)}
  .sheet.night .foot .mark,.sheet.night .foot .pg{color:var(--text)}
  .sheet.night .wmbox{outline-color:var(--border)}
  /* A: chapter opener */
  .hero{flex:1;display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:var(--sp-2xl);
    padding-bottom:var(--sp-xl);min-height:0}
  .hero figure{margin:0;position:relative;overflow:hidden;min-height:0}
  .hero figure img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .hero .panel .rbig{font-size:var(--lg)}
  .chap{font-size:var(--xs);letter-spacing:.14em;text-transform:uppercase;margin:0 0 var(--sp-sm)}
  /* B: the carried photograph */
  .carry{flex:1;display:grid;grid-template-columns:minmax(0,2.7fr) minmax(0,9.3fr);gap:var(--sp-xl);
    padding-bottom:var(--sp-lg);min-height:0}
  .carry .ph{display:flex;flex-direction:column;gap:var(--sp-md);min-height:0}
  .carry .ph h2{margin:0}
  .carry .ph figure{flex:1;margin:0;position:relative;overflow:hidden;min-height:0}
  .carry .ph figure img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .carry .ph .cap{font-size:var(--xs);letter-spacing:.04em;opacity:.8;margin:0}
  .bcover{padding:0 !important;color:var(--text)}
  .bcover .bimg{position:absolute;inset:0}
  .bcover .bimg img{width:100%;height:100%;object-fit:cover;display:block}
  .bcover .bimg::after{content:"";position:absolute;inset:0;
    background:linear-gradient(180deg,rgba(8,8,8,0) 40%,rgba(8,8,8,.78))}
  .bcover .covergrid{position:relative;padding:var(--pad) var(--pad) var(--sp-xl);flex:1;
    display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:var(--sp-2xl);align-items:end}
  .bcover .foot{position:relative;margin:0 var(--pad);border-color:rgba(238,236,234,.3);color:var(--muted)}
  .bcover .foot .mark,.bcover .foot .pg{color:var(--text)}
  /* C: contact sheet cover */
  .ccover{padding:0 !important;background:#080808;color:var(--text)}
  .cgrid{flex:1;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));grid-template-rows:repeat(4,1fr);gap:3px;min-height:0}
  .cgrid figure{margin:0;position:relative;overflow:hidden}
  .cgrid figure img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .cgrid .ctitle{grid-column:span 2;grid-row:span 2;background:#D8B260;color:#080808;
    padding:var(--sp-lg);display:flex;flex-direction:column;justify-content:space-between}
  .cgrid .ctitle .wordmark{font-size:clamp(48px,5.4vw,84px);margin:0}
  .cgrid .ctitle .covline{font-size:var(--lg)}
  .cgrid .band{display:flex;align-items:flex-end;padding:var(--sp-sm);font-size:var(--xs);
    letter-spacing:.12em;text-transform:uppercase}
  .ccover .foot{margin:0 var(--pad);border-color:var(--border);color:var(--muted)}
  .ccover .foot .mark,.ccover .foot .pg{color:var(--text)}
  .toc{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:var(--sp-md);font-size:var(--xs);
    border-top:1px solid currentColor;padding-top:var(--sp-sm);margin-top:var(--sp-md)}
  .toc b{display:block;font-weight:400;font-variant-numeric:tabular-nums;opacity:.7}
  .strip{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:var(--sp-xs);margin-top:var(--sp-lg)}
  .strip figure{margin:0;position:relative;aspect-ratio:5/4;overflow:hidden}
  .strip figure img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .sheet > .strip ~ .imgs{margin-top:var(--sp-lg)}
"""


# ---------- lead elements: one thing per spec sheet reads first, at real scale ----------
CONTRAST = {  # on void, on #141414, on #2B2B2B, text on it, role
    0: ("9.97", "9.17", "7.05", "1.70", "Text, marks, rules"),
    1: ("5.26", "4.84", "3.72", "3.23", "Text, marks, rules"),
    2: ("2.66", "2.44", "1.88", "6.40", "Ground only"),
    3: ("1.41", "1.30", "1.00", "12.01", "Ground only")}
OK = {0: "0.781 0.110 84.9", 1: "0.619 0.110 44.7", 2: "0.461 0.110 5.0", 3: "0.301 0.110 295.2"}
CMYK = {0: "0 18 56 15", 1: "0 41 60 26", 2: "0 58 42 46", 3: "45 69 0 63"}


def lead_identity():
    donts = re.search(r'<div class="donts">.*?</div>\s*</div>\s*</div>', S["03"]["colr"], re.S).group(0)
    return (f'<div class="lg l75"><div class="wmhero"><div class="wmbox"><span class="wmspace"></span>'
            f'<span class="wmtext">Afterglow</span></div>'
            f'<p class="cap2">Instrument Serif 400, tracking 0. Clear space is the cap height of the A on every side. '
            f'Minimum 96 px on screen, 24 mm in print.</p></div>'
            f'<div class="sup"><h3 class="bt">Six ways to break it</h3><div class="panel">{donts}</div></div></div>')


def lead_colour():
    cols = []
    for k, (name, hexv, L, ink) in enumerate(STAGES):
        c = CONTRAST[k]
        fg = "#080808" if ink == "dark" else "#EEECEA"
        cols.append(f'<div class="sw" style="background:{hexv};color:{fg}"><p class="swn">{name}</p>'
                    f'<dl><dt>Hex</dt><dd>{hexv}</dd><dt>OKLCH</dt><dd>{OK[k]}</dd><dt>CMYK</dt><dd>{CMYK[k]}</dd>'
                    f'<dt>On void</dt><dd>{c[0]}:1</dd><dt>On #141414</dt><dd>{c[1]}:1</dd><dt>On #2B2B2B</dt><dd>{c[2]}:1</dd>'
                    f'<dt>Text on it</dt><dd>{c[3]}:1</dd></dl><p class="swr">{c[4]}</p></div>')
    return (f'<div class="swatches">{"".join(cols)}</div>'
            f'<p class="fine2">Body floor 4.5:1, large-text floor 3:1. CMYK is converted for a proof, not matched; '
            f'each Pantone is matched against a physical guide and written back here.</p>')


def lead_fall():
    rules = re.search(r'<ul class="rules">.*?</ul>', S["07"]["colr"], re.S).group(0)
    neut = [("Ground", "#080808", "0.134"), ("Surface, recessed", "#141414", "0.191"), ("Surface, raised", "#2B2B2B", "0.289"),
            ("Muted", "#C0C0C0", "0.808"), ("Text", "#EEECEA", "0.944")]
    ticks = "".join(f'<span style="left:{x}%"><b>{h}</b>{x:g}%</span>' for x, h in
                    ((0, "#D8B260"), (33.3, "#BC6F4C"), (66.7, "#893A50"), (100, "#341D5E")))
    chips = "".join(f'<div class="nc"><i style="background:{v}"></i><p>{n}</p><p class="m">{v} &middot; L {l}</p></div>'
                    for n, v, l in neut)
    return (f'<p class="fallhero">Gold to violet. Never reversed.</p><div class="fallband"></div><div class="ticks">{ticks}</div>'
            f'<div class="lg l57"><div><h3 class="bt">Neutrals and surfaces</h3><div class="neut">{chips}</div>'
            f'<p class="fine2">Border is rgba(192,192,192,0.22), a hairline. No neutral is a stage and no stage is a neutral.</p></div>'
            f'<div class="panel">{rules}</div></div>')


def lead_type():
    c = S["08"]["colr"]
    ladder = c[c.index('<div class="tspec">'):].rstrip()
    ladder = ladder[:ladder.rindex("</div>")]  # drop the panel's own close; the tspec is what is kept
    setting = re.search(r'<table class="tbl">.*?</table>', S["09"]["colr"], re.S).group(0)
    return (f'<div class="lg ltype"><div class="faceshero">'
            f'<div><p class="pk2">Display &middot; Instrument Serif 400 &middot; headings and the wordmark</p>'
            f'<p class="fbig serif">Afterglow</p></div>'
            f'<div><p class="pk2">Body &middot; Space Grotesk 400 &middot; everything else</p>'
            f'<p class="fbig sans">The light only ever deepens.</p></div>'
            f'</div><div class="sup"><div class="panel">{ladder}</div><div class="panel">{setting}</div></div></div>')


def lead_grid():
    tri = re.search(r'<div class="trio">.*?</p></div>\s*</div>', S["11"]["colr"], re.S).group(0)
    space = re.search(r'<div class="space">.*?</div>', S["10"]["colr"], re.S).group(0)
    meas = re.search(r'<table class="tbl">.*?</table>', S["10"]["colr"], re.S).group(0)
    cols = "".join("<span></span>" for _ in range(12))
    return (f'<div class="gbg">{cols}</div>'
            f'<div class="rulehero"><p class="pk2">The one rule</p><p class="rhuge">No state change brightens.</p>'
            f'<p class="cap2">Hover, focus and active deepen or shift hue and never lighten. In print and film a later panel '
            f'is never lighter than the one before it. The one rule here that can be checked in a diff.</p></div>'
            f'<div class="lg l444"><div class="panel">{tri}</div><div class="panel">{meas}</div><div class="panel">{space}</div></div>')


def lead_apps():
    arts = re.findall(r'<article class="app">.*?</article>', S["18"]["colr"] + S["19"]["colr"], re.S)
    prod = re.search(r'<ul class="rules">.*?</ul>', S["19"]["colr"], re.S).group(0)
    card, btn, steps, pcard, plabel, poster = arts
    return (f'<div class="lg lapps"><div class="panel pcardhero">{card}</div>'
            f'<div class="sup"><div class="panel"><div class="apps2">{btn}{steps}</div></div>'
            f'<div class="panel"><div class="prints">{pcard}{plabel}{poster}</div></div>'
            f'<div class="prod"><p class="pk2">Production</p>{prod}</div></div></div>')


def voice_sheet(pg, style):
    c = S["20"]["colr"]
    paras = re.findall(r'<p class="pl">(.*?)</p>', c, re.S)
    return (f'<section class="sheet light imagery voice" style="{style}"><div class="lg lvoice">'
            f'<div class="vtext"><p class="pk2">Voice</p>'
            f'<p class="vbig">Unhurried and physical. It names heat, light, breath and skin.</p>'
            f'<p class="vbody">{paras[0].split("skin.", 1)[1].strip()}</p>'
            f'<div class="vcols"><div><p class="pk2">Where the rules stop</p><p class="vbody">{paras[1]}</p></div>'
            f'<div><p class="pk2">Elsewhere</p><p class="vbody">{paras[2]}</p></div></div></div>'
            f'<figure class="vimg"><img src="{src_of(PHOTOS[3][5])}" alt=""></figure></div>'
            f'{foot("Voice", pg)}</section>')


LEAD_CSS = """
  .lbody{flex:1;display:flex;flex-direction:column;gap:var(--sp-lg);padding-bottom:var(--sp-lg);min-height:0;position:relative}
  .lg{display:grid;gap:var(--sp-xl);min-height:0}
  .lg.l75{grid-template-columns:minmax(0,7fr) minmax(0,5fr);flex:1;align-items:center}
  .lg.l57{grid-template-columns:minmax(0,7fr) minmax(0,5fr);align-items:start}
  .lg.l444{grid-template-columns:minmax(0,5fr) minmax(0,4fr) minmax(0,3fr);align-items:start;margin-top:auto}
  .sup{display:flex;flex-direction:column;gap:var(--sp-sm)}
  .sup .donts{grid-template-columns:repeat(2,minmax(0,1fr))}
  .wmhero{display:flex;flex-direction:column;align-items:flex-start;gap:var(--sp-lg)}
  .wmhero .wmtext{font-size:clamp(72px,9.5vw,148px)}
  .wmhero .wmbox{padding:calc(var(--sp-lg)*1.6)}
  .wmhero .wmspace{outline-offset:calc(var(--sp-lg) * -1.6)}
  .cap2{margin:0;font-size:var(--xs);max-width:52ch;opacity:.85}
  .fine2{margin:0;font-size:var(--xs);max-width:90ch;opacity:.8}
  .pk2{margin:0 0 var(--sp-2xs);font-size:var(--xs);letter-spacing:.12em;text-transform:uppercase;opacity:.8}
  .swatches{flex:1;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));min-height:0}
  .sw{display:flex;flex-direction:column;padding:var(--sp-lg);min-height:0}
  .swn{margin:0 0 auto;font-family:var(--display);font-size:var(--x2);line-height:1}
  .sw dl{display:grid;grid-template-columns:auto 1fr;gap:4px var(--sp-md);margin:var(--sp-lg) 0 var(--sp-md);font-size:var(--xs);
    font-variant-numeric:tabular-nums}
  .sw dt{letter-spacing:.1em;text-transform:uppercase;opacity:.72}
  .sw dd{margin:0;white-space:nowrap}
  .sw{padding:var(--sp-lg) var(--sp-md)}
  .sw dl{font-size:11.5px;gap:4px var(--sp-sm)}
  .sw dt,.sw dd{line-height:1.35}
  .swr{margin:0;padding-top:var(--sp-sm);border-top:1px solid currentColor;font-size:var(--xs);letter-spacing:.1em;text-transform:uppercase}
  .fallband{flex:1;min-height:120px;background:linear-gradient(90deg,#D8B260,#BC6F4C 33.33%,#893A50 66.67%,#341D5E)}
  .ticks{position:relative;height:34px;margin-top:calc(var(--sp-lg) * -1 + 6px);font-size:var(--xs);font-variant-numeric:tabular-nums}
  .ticks span{position:absolute;top:0;transform:translateX(-50%);white-space:nowrap;opacity:.85}
  .ticks span:first-child{transform:none}.ticks span:last-child{transform:translateX(-100%)}
  .ticks b{font-weight:400;margin-right:var(--sp-xs)}
  .neut{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:var(--sp-sm);margin:var(--sp-sm) 0}
  .nc i{display:block;height:64px;box-shadow:0 0 0 1px rgba(192,192,192,.22) inset}
  .nc p{margin:var(--sp-xs) 0 0;font-size:var(--xs)}.nc .m{margin-top:2px;opacity:.75;font-variant-numeric:tabular-nums}
  .lbody .tbl th,.lbody .tbl td{white-space:normal;padding-right:var(--sp-sm)}
  .lbody .tstep{grid-template-columns:34px minmax(0,1fr) 112px;gap:var(--sp-sm)}
  .lg.ltype{grid-template-columns:minmax(0,5fr) minmax(0,7fr);align-items:start}
  .carry .fbig.serif{font-size:clamp(64px,7vw,96px)}
  .faceshero{display:flex;flex-direction:column;gap:var(--sp-lg)}
  .fbig{margin:0;line-height:1}
  .fbig.serif{font-family:var(--display);font-size:clamp(72px,8.4vw,124px);letter-spacing:-.02em}
  .fbig.sans{font-family:var(--body);font-size:var(--x2)}
  .gbg{position:absolute;inset:0 0 var(--sp-lg);display:grid;grid-template-columns:repeat(12,1fr);gap:var(--sp-lg);pointer-events:none}
  .gbg span{background:currentColor;opacity:.07}
  .rulehero{position:relative;padding-top:var(--sp-md)}
  .rhuge{margin:0 0 var(--sp-md);font-family:var(--display);font-size:clamp(56px,7vw,104px);line-height:.98;letter-spacing:-.02em;max-width:12ch}
  .lg.l444{position:relative}
  .lg.lapps{grid-template-columns:minmax(0,4fr) minmax(0,8fr);flex:1;align-items:stretch}
  .pcardhero{display:flex;padding:var(--sp-lg)}.pcardhero .app{flex:1}
  .pcardhero .appbody{min-height:0}.pcardhero .appimg{min-height:320px}
  .pcardhero .aname{font-size:var(--x2)}
  .apps2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-lg)}
  .apps2 .appbody{min-height:0}
  .sup .prints .pcard,.sup .prints .plabel,.sup .prints .pposter{max-height:170px}
  .prod .rules{columns:2;column-gap:var(--sp-xl);color:inherit;opacity:.85;max-width:none}
  .prod .rules li{break-inside:avoid}
  .voice{color:var(--text)}
  .lg.lvoice{flex:1;grid-template-columns:minmax(0,7fr) minmax(0,5fr);padding-bottom:var(--sp-xl);min-height:0}
  .vtext{display:flex;flex-direction:column;justify-content:flex-end;gap:var(--sp-md)}
  .vbig{margin:0;font-family:var(--display);font-size:clamp(44px,5.2vw,76px);line-height:1;letter-spacing:-.015em;max-width:16ch}
  .vbody{margin:0;font-size:var(--base);max-width:58ch;opacity:.86}
  .vbody a{color:var(--s1)}
  .vcols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-xl);margin-top:var(--sp-md);
    padding-top:var(--sp-md);border-top:1px solid var(--border)}
  .vcols .vbody{font-size:var(--xs)}
  .vimg{margin:0;position:relative;overflow:hidden;min-height:0}
  .vimg img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .fallhero{margin:0;font-family:var(--display);font-size:clamp(40px,4.6vw,66px);line-height:1;letter-spacing:-.015em}
  .sheet .mhead h2.t{font-size:var(--x3);margin:0;white-space:nowrap}
  .carry .ph h2.t{font-size:var(--x3)}
"""


def page(title, sheets):
    return (HEAD.replace("<title>Afterglow Brand Guide</title>", f"<title>{title}</title>")
            + "<style>" + CSS + EXTRA_CSS + LEAD_CSS + "</style>\n</head>\n<body>\n<main class=\"deck\">\n"
            + "\n".join(sheets) + "\n</main>\n</body>\n</html>\n")


def spec_sheet(pg, section, title, lead, blocks, cols="c2", style="", ink="night"):
    st = f' style="{style}"' if style else ""
    body = blocks if isinstance(blocks, str) else f'<div class="mgrid {cols}">{"".join(blocks)}</div>'
    if isinstance(blocks, str):
        body = f'<div class="lbody">{body}</div>'
    return (f'<section class="sheet {ink}"{st}><div class="mhead"><h2 class="t">{title}</h2>'
            f'<p class="lead">{lead}</p></div>{body}'
            f'{foot(section, pg)}</section>')


SYSTEM = [("Identity", "The wordmark", "There is no drawn logotype. The wordmark is the typeface.", lead_identity),
          ("Colour", "The four stages", "One ramp. Lightness falls and chroma stays flat at 0.110, so the stages differ in depth, not intensity.", lead_colour),
          ("Colour", "The fall", "The gradient is an asset with a specification, not an effect applied by eye.", lead_fall),
          ("Type", "Two faces, one scale", "Both are in Shopify&rsquo;s library. The scale is a ratio of 1.25, not a list.", lead_type),
          ("Layout", "Grid and the one rule", "Twelve columns in both media, one spacing base that divides the type base.", lead_grid)]


def apps_sheet(pg, style, ink):
    return spec_sheet(pg, "Applications", "Digital and print",
                      "What a storefront is mostly made of, and what the fall needs from a press.", lead_apps(), style=style, ink=ink)


def cover(pg=1):
    return re.search(r'<section class="sheet dark cover".*?</section>', SRC, re.S).group(0)


# ---------- A: the light first ----------
def build_a():
    sh = [cover()]
    hero_img = src_of(PHOTOS[0][2])
    sh.append(f'<section class="sheet dark imagery" style="background:linear-gradient(180deg,#D4A85D,#D09E5A)">'
              f'<div class="hero"><figure><img src="{hero_img}" alt=""></figure>'
              f'<div><p class="chap">Chapter one &middot; The light</p><h2 class="t">{S["12"]["h2"]}</h2>'
              f'<p class="lead" style="margin-bottom:var(--sp-lg)">{S["12"]["lead"]}</p>{S["12"]["colr"]}</div></div>'
              f'{foot("Imagery", 2)}</section>')
    for k in range(4):
        sh.append(stage_sheet(k, 3 + k))
    sh.append(f'<section class="sheet light imagery" style="background:linear-gradient(180deg,#341D5E,#1E1238)">'
              f'<div class="grid"><div class="col-l"><h2 class="t">{S["17"]["h2"]}</h2><p class="lead">{S["17"]["lead"]}</p></div>'
              f'<div class="col-r">{S["17"]["colr"]}</div></div>{foot("Imagery", 7)}</section>')
    lead2 = "Chapter two &middot; The system. After deep violet the ground is night, so every reading sits on one surface."
    for i, (sec, title, lead, fn) in enumerate(SYSTEM):
        sh.append(spec_sheet(8 + i, sec, title, (lead2 + " " if i == 0 else "") + lead, fn()))
    sh.append(apps_sheet(13, "", "night"))
    sh.append(voice_sheet(14, "background:#080808"))
    return page("Afterglow — Density A: The light first", sh)


# ---------- B: every sheet carries its stage ----------
def build_b():
    sh = [f'<section class="sheet bcover"><div class="bimg"><img src="{src_of(PHOTOS[0][0])}" alt=""></div>'
          f'<div class="covergrid"><div><p class="kick">Brand guide &middot; October 2026</p>'
          f'<h1 class="wordmark">Afterglow</h1><p class="covline">The light only ever deepens.</p></div>'
          f'<div class="covmeta"><p class="pl" style="color:inherit;opacity:.82">Four stages, two faces, one grid. '
          f'Every sheet carries a photograph from the stage its ground sits in.</p></div></div>{foot("Cover", 1)}</section>']
    carry = [(0, 1), (0, 3), (1, 1), (1, 3), (2, 0)]
    n = len(SYSTEM) + 6
    for i, ((sec, title, lead, fn), (k, j)) in enumerate(zip(SYSTEM, carry)):
        style, ink = ground(i + 1, n)
        sh.append(f'<section class="sheet {ink} imagery" style="{style}"><div class="carry">'
                  f'<div class="ph"><h2 class="t">{title}</h2><p class="lead">{lead}</p>'
                  f'<figure><img src="{src_of(PHOTOS[k][j])}" alt=""></figure>'
                  f'<p class="cap">{STAGES[k][0]} &middot; {STAGES[k][1]}</p></div>'
                  f'<div class="lbody">{fn()}</div></div>{foot(sec, i + 2)}</section>')
    pg = len(SYSTEM) + 2
    style, ink = ground(len(SYSTEM) + 1, n)
    sh.append(f'<section class="sheet {ink} imagery" style="{style}"><div class="grid"><div class="col-l">'
              f'<h2 class="t">{S["12"]["h2"]}</h2><p class="lead">{S["12"]["lead"]}</p></div>'
              f'<div class="col-r">{S["12"]["colr"]}</div></div>{foot("Imagery", pg)}</section>')
    for k in range(4):
        sh.append(stage_sheet(k, pg + 1 + k))
    vg = "background:linear-gradient(180deg,#341D5E,#2A174C)"
    sh.append(f'<section class="sheet light imagery" style="{vg}">'
              f'<div class="grid"><div class="col-l"><h2 class="t">{S["17"]["h2"]}</h2><p class="lead">{S["17"]["lead"]}</p></div>'
              f'<div class="col-r">{S["17"]["colr"]}</div></div>{foot("Imagery", pg + 5)}</section>')
    sh.append(apps_sheet(pg + 6, vg, "light imagery"))
    sh.append(voice_sheet(pg + 7, "background:linear-gradient(180deg,#2A174C,#1E1238)"))
    return page("Afterglow — Density B: Every sheet carries its stage", sh)


# ---------- C: contact sheet and index ----------
def build_c():
    cells = ['<div class="ctitle"><div><p class="kick">Brand guide &middot; October 2026</p>'
             '<h1 class="wordmark">Afterglow</h1></div><p class="covline">The light only ever deepens.</p></div>']
    for k, st in enumerate(PHOTOS):
        name, hexv, _, ink = STAGES[k]
        col = "#080808" if ink == "dark" else "#EEECEA"
        cells.append(f'<div class="band" style="background:{hexv};color:{col}">{k + 1} &middot; {name}</div>')
        cells += [f'<figure><img src="{src_of(p)}" alt=""></figure>' for p in st[:4]]
    sh = [f'<section class="sheet ccover"><div class="cgrid">{"".join(cells)}</div>{foot("Cover", 1)}</section>']
    toc = ('<div class="toc"><span><b>02&ndash;06</b>The system</span><span><b>07</b>Art direction</span>'
           '<span><b>08&ndash;11</b>The four stages</span><span><b>12&ndash;13</b>Misuse, digital, print</span><span><b>14</b>Voice</span></div>')
    for i, (sec, title, lead, fn) in enumerate(SYSTEM):
        st, ink = ground(i + 1, 14)
        sh.append(spec_sheet(i + 2, sec, title, lead, fn(), style=st, ink=ink)
                  .replace("<footer", (toc if i == 0 else "") + "<footer", 1))
    st, ink = ground(6, 14)
    sh.append(f'<section class="sheet {ink} imagery" style="{st}"><div class="grid"><div class="col-l">'
              f'<h2 class="t">{S["12"]["h2"]}</h2><p class="lead">{S["12"]["lead"]}</p></div>'
              f'<div class="col-r">{S["12"]["colr"]}</div></div>{foot("Imagery", 7)}</section>')
    for k in range(4):
        sh.append(stage_sheet(k, 8 + k))
    sh.append(f'<section class="sheet light imagery" style="background:linear-gradient(180deg,#341D5E,#2A174C)">'
              f'<div class="grid"><div class="col-l"><h2 class="t">{S["17"]["h2"]}</h2><p class="lead">{S["17"]["lead"]}</p></div>'
              f'<div class="col-r">{S["17"]["colr"]}</div></div>{foot("Imagery", 12)}</section>')
    sh.append(apps_sheet(13, "background:linear-gradient(180deg,#2A174C,#22133F)", "light imagery"))
    sh.append(voice_sheet(14, "background:linear-gradient(180deg,#2A174C,#1E1238)"))
    return page("Afterglow — Density C: Contact sheet and index", sh)


if __name__ == "__main__":
    for name, fn in (("a-light-first", build_a), ("b-carried-stage", build_b), ("c-contact-sheet", build_c)):
        p = ROOT / f"archive/afterglow-explorations/2026-10-10-density-{name}.html"   # explorations, archived 15 Oct
        p.write_text(fn())
        print(p.relative_to(ROOT))
