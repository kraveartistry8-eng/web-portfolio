"""Builds the Step 3 storyboard: three directions for the guide's Ember page, on the guide's own CSS,
with the v23 engine wired to the sheet grounds (option 1). Run with --stills to build the still-capture page."""
import base64, os, re, sys

ROOT = "/Users/aaronstreets/Desktop/CLIENTS/web portfolio"
CONTENT = ROOT + "/.superpowers/brainstorm/14594-1791742976/content"
SCR = os.path.dirname(os.path.abspath(__file__)) + "/uni/stills"
GUIDE = open(ROOT + "/brand/2026-10-10-density-b1-column.html").read()
HEAD = GUIDE[GUIDE.index("<head>") + 6:GUIDE.index("</head>")].replace("<title>Afterglow Brand Guide</title>", "<title>Ember Page Directions</title>")
V23 = open(CONTENT + "/ember-v23.html").read()
G0, G1 = "#321C5B", "#1D1231"          # the Ember page's slice: deep violet, after the four stages, before Use and misuse
STILL_MODE = "--stills" in sys.argv


def uri(name):
    p = os.path.join(SCR, name)
    if not os.path.exists(p):
        return ""
    kind = "png" if p.endswith(".png") else "jpeg"
    return f"data:image/{kind};base64," + base64.b64encode(open(p, "rb").read()).decode()


def hot(hexc):
    c = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    l = .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    return "#" + "".join(f"{max(0, min(255, round(l + (v - l) * 3.55))):02X}" for v in c)


EMBER = hot(G0)

FOOT = '<footer class="foot"><span class="mark">Afterglow</span><span>Motion</span><span class="doc">Brand guide &middot; October 2026</span><span class="pg">12</span></footer>'
PH = ('<div class="ph"><h2 class="t">The ember</h2><p class="lead">The one accent of contrast. It follows the cursor '
      'in the colour of the page beneath it, and goes out when the cursor stops.</p>{extra}</div>')


def sheet(body, extra="", cls=""):
    return (f'<section class="sheet light imagery ember {cls}" data-ground="{G0},{G1}" '
            f'style="background:linear-gradient(180deg,{G0},{G1})"><div class="carry">{PH.format(extra=extra)}'
            f'<div class="lbody">{body}</div></div>{FOOT}</section>')


COLOUR = (f'<div class="panel"><p class="pk">Colour</p><div class="chips"><span style="background:{G0}"></span><i>&rarr;</i>'
          f'<span style="background:{EMBER}"></span></div><p class="pl">The page&rsquo;s own colour, pushed to high chroma: '
          f'{G0} becomes {EMBER}. Everywhere else chroma stays at 0.110.</p></div>')
LIGHT = ('<div class="panel"><p class="pk">Light</p><p class="tval">A rim</p><p class="pl">Panels catch a light on the edge '
         'facing the ember; text, on the side facing it. Nothing is cast: no shadow, no darkening.</p></div>')
STOP = ('<div class="panel"><p class="pk">Stop</p><p class="tval">0.7 s</p><p class="pl">The head coasts on and slows while '
        'the tail runs in to meet it. They come to rest together and go out as a dot.</p></div>')
NEVER = ('<p class="never"><b>Never</b> a shadow &middot; a dark pattern &middot; a piece that breaks off &middot; a stepped edge '
         '&middot; a page that needs it to render</p>')

NEVERCOL = ('<div class="nevercol"><p class="pk">Never</p><ul><li>A shadow</li><li>A dark pattern</li><li>A piece that breaks off</li>'
            '<li>A stepped edge</li><li>A page that needs it to render</li></ul></div>')
# A: the live ember is the page's picture
A = sheet('<div class="efield"><p class="pk">Live &middot; try it here, then stop</p><p class="wordmark fwm">Afterglow</p>'
          '</div>'
          '<div class="panel arow"><div><p class="pk">Colour</p><p class="pl"><span class="chipi" style="background:#9A4C4F"></span><span class="chipi" style="background:#FF212C"></span>'
          'The page&rsquo;s own colour, pushed to high chroma. Everywhere else chroma stays at 0.110.</p></div>'
          '<div><p class="pk">Light</p><p class="pl">Panels catch a rim on the edge facing it; text, on the side facing it. Nothing is cast.</p></div>'
          '<div><p class="pk">Stop &middot; 0.7 s</p><p class="pl">The head coasts on while the tail runs in. They meet and go out as a dot.</p></div></div>', extra='<p class="lead">Move, and it lights. Stop, and it goes out.</p>' + NEVERCOL, cls="dirA")

# B: the stop as a filmstrip, which is also what print shows
FR = [("v_stop", "Stop", "The tail end leaves at the pace it had."), ("v_t2", "0.2 s", "The head coasts on, slowing."),
      ("v_t3", "0.3 s", "The tail end gathers pace."), ("v_t4", "0.4 s", "It reaches the stretch the head coasted."),
      ("v_t5", "0.5 s", "They meet and come to rest."), ("v_t6", "0.6 s", "Out, as a dot.")]
hero = FR[0]
side = "".join(f'<li><span class="th" style="background-image:url({uri(n + ".png")})"></span><span><b>{t}</b>{c}</span></li>' for n, t, c in FR[1:])
strip = (f'<p class="rhuge bstate">0.7 seconds from stop to out.</p><div class="brow"><figure class="bhero"><div class="fimg" style="background-image:url({uri(hero[0] + ".png")})"></div>'
         f'<figcaption><b>{hero[1]}</b>{hero[2]}</figcaption></figure><ol class="blist">{side}</ol></div>')
B = sheet(f'<div class="bwrap">{strip}</div>{NEVER}', extra=f'<div class="phstack">{COLOUR}{LIGHT}</div>', cls="dirB")

# C: the rules as Do and Don't pairs, in the guide's misuse grammar
def pair(title, line, do, dont):
    return (f'<div class="epair"><div class="ptiles"><div class="ptile">{do}<span class="wpill wdo">Do</span></div>'
            f'<div class="ptile">{dont}<span class="wpill">Don&rsquo;t</span></div></div>'
            f'<p class="dk">{title}</p><p class="pl">{line}</p></div>')
img = lambda n: f'<div class="fimg" style="background-image:url({uri(n)})"></div>'
rim = (f'<div class="dcard" style="box-shadow:inset 2px 0 0 {EMBER},inset 0 2px 0 rgba(255,33,44,.45);'
       f'background:radial-gradient(circle at 0 0,rgba(255,33,44,.22),transparent 55%),#141414"></div>')
wash = f'<div class="dcard" style="background:{EMBER}"></div>'
lit = (f'<div class="dcard" style="background:radial-gradient(circle at 0 50%,rgba(255,33,44,.25),transparent 60%),#141414;'
       f'box-shadow:inset 2px 0 0 {EMBER}"></div>')
shade = '<div class="dcard" style="background:#141414;box-shadow:14px 14px 22px rgba(0,0,0,.7)"></div>'
C = sheet('<div class="egrid panel">'
          + pair("Light, not print", "Small molten globs brighter than the melt. Never dark spots.", img("v_glob.png"), img("v19_leopard.jpg"))
          + pair("Whole to the end", "The tail runs into the head. Nothing tears or breaks off.", img("v_whole.png"), img("v19_torn.jpg"))
          + pair("A rim, not a wash", "A panel takes light on the edge facing the ember.", rim, wash)
          + pair("Light, never shadow", "The ember lights what is near it and darkens nothing.", lit, shade)
          + '</div><p class="never">The stills are real frames: the right ones from the build, the wrong ones from rejected rounds.</p>',
          cls="dirC")

LABEL = ('<div class="dlabel"><b>{k}</b><span>{name}</span><em>{premise}</em></div>')

# A2: A refined against Bob Beaute and Frame.io: one hero, one label line, one reading plate, quiet rules
A2 = (f'<section class="sheet light imagery ember dirA2" data-ground="{G0},{G1}" style="background:linear-gradient(180deg,{G0},{G1})"><div class="carry">'
      '<div class="ph"><h2 class="t">The ember</h2><p class="lead">The one accent of contrast. It follows the cursor in the colour of the page beneath it, '
      'and goes out when the cursor stops.</p><p class="lead">Panels and type catch its light on the side facing it. Nothing is cast.</p>'
      '<figure class="a2fig"><img src="' + uri("R6euaYP.jpg") + '" alt=""></figure>'
      '<p class="quiet">Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render.</p></div>'
      '<div class="lbody"><div class="efield a2">'
      '<p class="wordmark fwm2">Afterglow</p>'
      '<div class="tri"><span>Live</span><span>Move, and it lights. Stop, and in 0.7 seconds it goes out.</span>'
      f'<span><span class="chipi" style="background:{G0}"></span>{G0} &rarr; <span class="chipi" style="background:{EMBER}"></span>{EMBER}</span></div></div></div>'
      f'</div>{FOOT}</section>')

# A3: the brand moment. Wordmark, photograph, one line; the rules behind a toggle, always shown in print
A3 = (f'<section class="sheet light imagery ember dirA3" data-ground="{G0},{G1}" style="background:linear-gradient(180deg,{G0},{G1})"><div class="carry">'
      '<div class="ph"><h2 class="t">The ember</h2><figure class="a2fig a3fig"><img src="' + uri("R6euaYP.jpg") + '" alt=""></figure></div>'
      '<div class="lbody"><div class="efield a2"><p class="wordmark fwm2">Afterglow</p>'
      '<div class="rules" id="rules"><p>The one accent of contrast. It follows the cursor in the colour of the page beneath it, and goes out when the cursor stops.</p>'
      '<p>Panels and type catch its light on the side facing it. Nothing is cast.</p>'
      '<p><span class="chipi" style="background:#9A4C4F"></span>#9A4C4F &rarr; <span class="chipi" style="background:#FF212C"></span>#FF212C: the page&rsquo;s own colour at high chroma. Everywhere else, 0.110.</p>'
      '<p>Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render.</p></div>'
      '<div class="tri"><button class="rtog" onclick="document.getElementById(\'rules\').classList.toggle(\'open\');this.classList.toggle(\'on\')">The rules</button>'
      '<span>Move, and it lights. Stop, and in 0.7 seconds it goes out.</span><span>Live</span></div></div></div>'
      f'</div>{FOOT}</section>')

# D: real guide content placed in the field, so the viewer watches the ember light it
D = sheet('<p class="rhuge astate">It lights what it passes.</p>'
          '<div class="efield play"><p class="pk">Live &middot; pass the ember over each piece</p>'
          '<div class="panel pp p1"><p class="pk">Eau de parfum</p><p class="tval">$180</p><p class="pl">A panel catches a rim on the edge facing it.</p></div>'
          '<p class="lead pp p2">Text takes light on the side that faces it, and nothing behind it darkens.</p>'
          '<div class="panel pp p3"><p class="pk">Travel, 10 ml</p><p class="tval">$48</p></div>'
          '<span class="call c1">Rim</span><span class="call c2">Text edge</span><span class="call c3">Glow, never shadow</span></div>'
          f'{NEVER}', cls="dirD")

# E: the four stages stacked in the field, so the viewer watches its colour change with the ground
STG = [("Gold", "#D8B260", "#080808"), ("After gold", "#BC6F4C", "#080808"), ("Rose", "#893A50", "#EEECEA"), ("Deep violet", "#341D5E", "#EEECEA")]
bands = "".join(f'<div class="band4" data-ground="{g},{g}" style="background:{g};color:{t}"><span><b>{n}</b>{g}</span>'
                f'<span class="eh"><i style="background:{hot(g)}"></i>the ember here: {hot(g)}</span></div>' for n, g, t in STG)
E = sheet('<p class="rhuge astate">One ember, the colour of where it is.</p>'
          '<div class="efield"></div>'
          f'<div class="stack">{bands}</div>'
          '<p class="never"><b>Rule</b> the page&rsquo;s colour at that point, pushed to high chroma. Move down through the stages.</p>', cls="dirE")

# F: a live readout of the ember's own numbers
F = sheet('<p class="rhuge astate">Every number here is live.</p>'
          '<div class="frow"><div class="efield"><p class="pk">Live &middot; move, then stop, and read the panel</p></div>'
          '<div class="panel readout"><p class="pk">Ember</p>'
          '<div class="rd"><em>Phase</em><b id="r-phase">Waiting</b></div>'
          '<div class="rd"><em>Speed</em><b id="r-speed">0 px/s</b></div>'
          '<div class="rd"><em>Heat</em><b id="r-heat">0%</b></div>'
          '<div class="rd"><em>Colour</em><b><i id="r-chip"></i><span id="r-hex">&mdash;</span></b></div>'
          '<div class="rd"><em>Since stop</em><b id="r-since">&mdash;</b></div>'
          '<div class="rbar"><span id="r-bar"></span></div><p class="pl">The bar runs from the stop to out: the head coasts while the tail runs in, and they meet at the end.</p></div></div>'
          f'{NEVER}', cls="dirF")

DIRS = LABEL.format(k="A&prime;", name="Specimen, teaching, on deep violet", premise="Page 12: after the four stages, before Use and misuse.") + A2
if STILL_MODE:
    DIRS = sheet('<div class="efield"></div>', cls="still")

CSS = """
<style>
  #ember{position:fixed;inset:0;z-index:0;pointer-events:none} #ember canvas{display:block;width:100vw;height:100vh}
  main.deck{position:relative;z-index:1}
  .ember-on .sheet.ember{background:transparent!important}
  .dlabel{display:flex;gap:16px;align-items:baseline;padding:28px var(--pad) 10px;color:#EEECEA;font-size:13px}
  .dlabel b{font-family:var(--display);font-weight:400;font-size:32px;line-height:1}
  .dlabel span{letter-spacing:.14em;text-transform:uppercase;font-size:11px}
  .dlabel em{font-style:normal;opacity:.7}
  .ember .panel{position:relative}
  .efield{flex:1;min-height:0;position:relative;border-top:1px solid rgba(238,236,234,.18)}
  .efield > .pk{position:absolute;left:0;top:var(--sp-sm);color:#EEECEA;opacity:.8;margin:0}
  .erow3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--sp-md)}
  .erow2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-md)}
  .chips{display:flex;align-items:center;gap:10px;margin-bottom:var(--sp-sm)} .chips span{width:56px;height:32px}
  .chips i{font-style:normal;opacity:.7}
  .never{margin:0;font-size:var(--xs);letter-spacing:.04em;color:#EEECEA;opacity:.85}
  .never b{letter-spacing:.14em;text-transform:uppercase;font-weight:500;margin-right:8px}
  .strip{flex:1;min-height:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));gap:var(--sp-md) 4px}
  .phstack{display:flex;flex-direction:column;gap:var(--sp-sm);margin-top:auto} .dirB .ph .panel .pl{margin-bottom:0}
  .frm{margin:0;display:flex;flex-direction:column;min-height:0}
  .fimg{flex:1;min-height:120px;background-size:cover;background-position:center;background-color:#1D1231}
  .dirB{--stillg:#944551}
  .strip{background:var(--stillg);padding:0} .strip .fimg{outline:1px solid rgba(238,236,234,.22);outline-offset:-1px}
  .strip .frm{background:var(--stillg)}
  .frm figcaption{padding:var(--sp-xs) 0 0;font-size:var(--xs);line-height:1.4;color:#EEECEA}
  .frm figcaption b{display:block;font-weight:500;letter-spacing:.1em;text-transform:uppercase;font-size:11px;margin-bottom:2px}
  .egrid{flex:1;min-height:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));gap:var(--sp-lg) var(--sp-xl)}
  .epair{display:flex;flex-direction:column;min-height:0}
  .ptiles{flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;gap:4px}
  .ptile{position:relative;min-height:0;display:flex;background:#141414} .ptile > div{flex:1}
  .ptile .wpill{position:absolute;top:8px;left:8px}
  .dcard{margin:22% 18%}
  .epair .dk{margin:var(--sp-xs) 0 2px;color:#EEECEA} .epair .pl{margin:0;color:#EEECEA;opacity:.85}
  /* the ember's light on panels: a rim and a faint glow, from the side facing it */
  .elit{--li:0;--ec:255,120,90;--px:50%;--py:-200px;--rr:300px}
  .elit::before{content:"";position:absolute;inset:0;pointer-events:none;border:2px solid transparent;z-index:2;
    border-image:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),var(--li)) 0%,rgba(var(--ec),calc(.45 * var(--li))) 40%,rgba(var(--ec),calc(.1 * var(--li))) 75%,transparent 100%) 1}
  .elit::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:radial-gradient(circle var(--rr) at var(--px) var(--py),rgba(var(--ec),calc(.2 * var(--li))),rgba(var(--ec),calc(.05 * var(--li))) 45%,transparent 75%);
    mix-blend-mode:screen;box-shadow:0 0 24px rgba(var(--ec),calc(.32 * var(--li)))}
  .lit{--tl:0;--tx:0px;--ty:0px;text-shadow:var(--tx) var(--ty) 0 rgba(var(--ec,255,120,90),calc(.9 * var(--tl))),0 0 10px rgba(var(--ec,255,120,90),calc(.35 * var(--tl)))}

  .arow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--sp-xl);padding:var(--sp-md) var(--sp-lg)} .arow .pl{margin:0;color:#EEECEA;opacity:.85}
  .chipi{display:inline-block;width:14px;height:14px;margin-right:4px;vertical-align:-2px} .chipi + .chipi{margin-right:8px}
  .astmt{font-family:var(--display);font-size:clamp(26px,2.4vw,36px);line-height:1.1;margin:0;color:#EEECEA}
  .dirA .efield{border-top:0}
  .nevercol{margin-top:auto;color:#EEECEA} .nevercol ul{list-style:none;margin:0;padding:0;font-size:var(--xs);line-height:1.9}
  .nevercol li{opacity:.85}
  .astate{margin:0;max-width:none;color:#EEECEA}
  .estate{position:absolute;left:0;bottom:var(--sp-md);margin:0;max-width:16ch;color:#EEECEA}
  .bwrap{flex:1;min-height:0;display:flex;flex-direction:column}
  .bstate{margin:0 0 var(--sp-md);max-width:none;color:#EEECEA}
  .brow{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:var(--sp-lg)}
  .bhero{margin:0;display:flex;flex-direction:column;min-height:0}
  .bhero .fimg{flex:1;min-height:0;background-size:cover;background-position:center;background-color:var(--stillg);outline:1px solid rgba(238,236,234,.22);outline-offset:-1px}
  .bhero figcaption,.blist span{font-size:var(--xs);line-height:1.4;color:#EEECEA}
  .bhero figcaption{padding-top:var(--sp-xs)}
  .bhero b,.blist b{display:block;font-weight:500;letter-spacing:.1em;text-transform:uppercase;font-size:11px;margin-bottom:2px}
  .blist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;justify-content:space-between;gap:var(--sp-xs);min-height:0}
  .blist li{display:grid;grid-template-columns:120px minmax(0,1fr);gap:var(--sp-sm);align-items:center}
  .blist .th{display:block;aspect-ratio:16/9;background-size:cover;background-position:center;background-color:var(--stillg);outline:1px solid rgba(238,236,234,.22);outline-offset:-1px}
  .dirC .egrid.panel{padding:var(--sp-lg);background:#080808}
  .dirC .ptiles{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}
  .dirC .ptile:last-child{opacity:.72}

  .dirD .play .pp{position:absolute;margin:0} .dirD .p1{left:6%;top:22%;width:250px} .dirD .p2{left:40%;top:30%;max-width:30ch;color:#EEECEA}
  .dirD .p3{right:4%;top:56%;width:220px}
  .fwm{position:absolute;left:6%;top:50%;translate:0 -50%;margin:0;font-size:clamp(72px,10.5vw,172px);line-height:1;color:#EEECEA}
  .ca{left:auto;right:0;top:var(--sp-sm)}
  .call{position:absolute;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#EEECEA;opacity:.75;padding-left:18px}
  .call::before{content:"";position:absolute;left:0;top:50%;width:12px;height:1px;background:currentColor}
  .dirD .c1{left:6%;top:calc(22% - 28px)} .dirD .c2{left:40%;top:calc(30% - 28px)} .dirD .c3{right:4%;top:calc(56% - 28px);margin-right:120px}
  .dirE .efield{border-top:0}
  .dirE .stack{position:absolute;left:0;right:0;top:46%;bottom:13%;display:grid;grid-template-rows:repeat(4,minmax(0,1fr));z-index:0}
  .dirE .carry,.dirE .foot{position:relative;z-index:1}
  .band4{padding:0 var(--pad)!important}
  .dirE .never{position:relative;z-index:1}
  .band4{display:flex;justify-content:space-between;align-items:center;padding:0 var(--sp-md);font-size:var(--xs)}
  .band4 b{font-weight:500;letter-spacing:.12em;text-transform:uppercase;font-size:11px;margin-right:12px}
  .band4 .eh{display:flex;align-items:center;gap:8px} .band4 .eh i{width:28px;height:16px;display:inline-block}
  .ember-on .band4{background:transparent!important}
  .frow{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:var(--sp-lg)}
  .readout{align-self:stretch;display:flex;flex-direction:column;gap:var(--sp-sm)}
  .rd{display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid rgba(238,236,234,.14);padding-top:var(--sp-xs)}
  .rd em{font-style:normal;font-size:var(--xs);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
  .rd b{font-family:var(--display);font-weight:400;font-size:28px;line-height:1;display:flex;align-items:center;gap:8px;font-variant-numeric:tabular-nums}
  #r-chip{width:20px;height:20px;display:inline-block;background:#1D1231}
  .rbar{height:4px;background:rgba(238,236,234,.14);margin-top:auto} .rbar span{display:block;height:100%;width:0;background:#EEECEA}
  @media print{.ember-on .band4{background:inherit!important}}
  .efield.a2{border-top:0;display:flex;flex-direction:column;justify-content:center}
  .fwm2{margin:0 auto 0 4%;font-size:clamp(44px,12.5vw,200px);line-height:1;color:#EEECEA;position:relative}
  @media (max-width:576px){.tri{grid-template-columns:1fr;gap:4px;position:static;margin-top:var(--sp-lg)} .tri span{text-align:left!important} .dirA2 .efield.a2{min-height:300px}}
  .tri{position:absolute;left:0;right:0;bottom:0;display:grid;grid-template-columns:1fr 2fr 1fr;padding-top:var(--sp-sm);border-top:1px solid rgba(238,236,234,.22);
    font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#EEECEA}
  .tri span:nth-child(2){text-align:center;text-transform:none;letter-spacing:0;font-family:var(--display);font-size:20px;line-height:1}
  .tri span:last-child{text-align:right}
  .ember .panel.plate{position:absolute;right:0;top:0;width:auto;padding:8px 12px;font-size:11px;letter-spacing:.06em;color:#EEECEA;display:flex;align-items:center;gap:6px}
  .plate i{font-style:normal;opacity:.6;margin:0 4px}
  .dirA2 .ph .lead + .lead{margin-top:0}
  .a2fig{margin:var(--sp-sm) 0 0;flex:1;min-height:0;overflow:hidden} .a2fig img{width:100%;height:100%;object-fit:cover;object-position:50% 40%;display:block}
  .tri .chipi{width:10px;height:10px;margin-right:4px;vertical-align:0}
  .dirA3 .a3fig{margin-top:var(--sp-md)}
  .rules{position:absolute;right:0;bottom:56px;width:min(420px,46%);background:#080808;padding:var(--sp-md) var(--sp-lg);font-size:var(--xs);line-height:1.55;color:#EEECEA;
    opacity:0;translate:0 8px;pointer-events:none;transition:opacity 450ms cubic-bezier(.2,0,.2,1),translate 450ms cubic-bezier(.2,0,.2,1)}
  .rules.open{opacity:1;translate:0 0;pointer-events:auto} .rules p{margin:0 0 var(--sp-xs)} .rules p:last-child{margin:0;opacity:.75}
  .rtog{all:unset;cursor:pointer;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#EEECEA;min-height:44px;display:inline-flex;align-items:center}
  .rtog::after{content:"+";margin-left:8px} .rtog.on::after{content:"\2013"} .rtog:focus-visible{outline:1px solid #EEECEA;outline-offset:4px}
  .dirA3 .tri{align-items:center}
  @media print{.rules{opacity:1!important;position:static;width:auto}}
  @media (max-width:576px){.rules{position:static;width:auto;display:none} .rules.open{display:block}}
  .quiet{margin-top:var(--sp-sm);font-size:var(--xs);line-height:1.5;color:#EEECEA;opacity:.7;max-width:32ch}
  .still .carry .ph{visibility:hidden} .still .foot{visibility:hidden}
  @media print{#ember{display:none}.ember-on .sheet.ember{background:linear-gradient(180deg,G0X,G1X)!important}}
</style>""".replace("G0X", G0).replace("G1X", G1)

# the engine: v23, wired to the guide
js = V23[V23.index('<script type="importmap">'):V23.rindex("</script>") + 9]
def R(a, b):
    global js
    assert js.count(a) == 1, a[:70]
    js = js.replace(a, b)
R('this.cards = [...document.querySelectorAll(".card")];',
  'this.cards = [...document.querySelectorAll(".sheet.ember .panel, .sheet.ember .ptile")]; this.cards.forEach(c => c.classList.add("elit"));')
R('this.texts = [...document.querySelectorAll("main h1, main h2, main .copy, main .kicker, .card .nm, .card .pr")];',
  'this.texts = [...document.querySelectorAll(".sheet.ember .t, .sheet.ember .lead, .sheet.ember .pk, .sheet.ember .tval, .sheet.ember .dk, .sheet.ember .rhuge, .sheet.ember .rd b, .sheet.ember .fwm, .sheet.ember .fwm2, .sheet.ember .tri span, .sheet.ember .rtog, .sheet.ember .band4 span")];')
# the ground: each sheet's own gradient, read into a 1 x 2048 strip; the gaps between sheets are the void
R("  fallAt(t) {", """  buildGround() {
    const N = 2048, docH = document.documentElement.scrollHeight, px = new Uint8Array(N * 4), hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const sheets = [...document.querySelectorAll(".sheet, [data-ground]")].map(el => { const r = el.getBoundingClientRect(), g = (el.dataset.ground || "#080808,#080808").split(",").map(hex);
      return { top: r.top + scrollY, h: r.height, a: g[0], b: g[1] }; }).sort((p, q) => p.h - q.h);   // the innermost ground under a point wins
    for (let i = 0; i < N; i++) { const y = (i + .5) / N * docH; let c = [8, 8, 8];
      for (const s of sheets) if (y >= s.top && y < s.top + s.h) { const k = (y - s.top) / s.h; c = s.a.map((v, j) => v + (s.b[j] - v) * k); break; }
      px.set([...c.map(Math.round), 255], i * 4); }
    this.groundPx = px;
    if (!this.groundTex) { this.groundTex = new THREE.DataTexture(px, 1, N, THREE.RGBAFormat); this.groundTex.magFilter = this.groundTex.minFilter = THREE.LinearFilter; }
    else this.groundTex.image.data = px;
    this.groundTex.needsUpdate = true; if (this.material) this.material.uniforms.uGround.value = this.groundTex;
  }
  groundAt(t) { const i = Math.max(0, Math.min(2047, Math.floor(t * 2048))) * 4, p = this.groundPx; return [p[i], p[i + 1], p[i + 2]]; }
  fallAt(t) { return this.groundAt(t); }
  _fallAtUnused(t) {""")
R("uRip: { value: 1 }, uResolution", "uRip: { value: 1 }, uGround: { value: null }, uResolution")
R("this.cards = [...", "this.buildGround(); this.material.uniforms.uGround.value = this.groundTex;\n    this.cards = [...")
R("this.renderer.setSize(innerWidth, innerHeight); this.makeTargets();", "this.renderer.setSize(innerWidth, innerHeight); this.makeTargets(); this.buildGround();")
R("uniform sampler2D uAge; uniform float uSince, uCut, uRip;\n", "uniform sampler2D uAge; uniform float uSince, uCut, uRip; uniform sampler2D uGround;\n")
R("vec3 base = fall((uScroll + (1. - q.y) * uVh) / uDoc);", "vec3 base = texture2D(uGround, vec2(.5, clamp((uScroll + (1. - q.y) * uVh) / uDoc, 0., 1.))).rgb;")
# option 1: the sheets go transparent only once the engine has drawn its first frame
R("this.renderer.setRenderTarget(null); this.renderer.render(this.scene, this.camera);",
  "this.renderer.setRenderTarget(null); this.renderer.render(this.scene, this.camera);\n    if (!this.drawn) { this.drawn = true; document.documentElement.classList.add('ember-on'); }")
R('try { window.ember = new EmberEngine(document.getElementById("ember")); }', 'try { window.ember = new EmberEngine(document.getElementById("ember")); }')
READOUT = """
<script>
(function(){ const $ = id => document.getElementById(id); if (!$("r-phase")) return; let last = null, lastT = 0;
  function tick(now){ requestAnimationFrame(tick); const em = window.ember; if (!em || !em.E) return; const E = em.E;
    const since = now - E.lastMove, moving = since < 34, x = E.cx ?? E.x, y = E.cy ?? E.y;
    const stroke = (E.lastMove - (E.strokeStart || E.lastMove)) / 1000 + .05, c0 = Math.min(.58, stroke), T = .25 + .75 * c0;
    let sp = 0; if (last && now > lastT) sp = Math.hypot(x - last[0], y - last[1]) / ((now - lastT) / 1000); last = [x, y]; lastT = now;
    const phase = E.lastMove < 0 ? "Waiting" : moving ? "Moving" : since / 1000 < T ? "Coasting in" : "Out";
    $("r-phase").textContent = phase; $("r-speed").textContent = Math.round(sp) + " px/s"; $("r-heat").textContent = Math.round(E.heat * 100) + "%";
    const c = em.groundAt((scrollY + y) / document.documentElement.scrollHeight), l = .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
    const h = "#" + c.map(v => Math.max(0, Math.min(255, Math.round(l + (v - l) * 3.55))).toString(16).padStart(2, "0")).join("").toUpperCase();
    $("r-chip").style.background = h; $("r-hex").textContent = h;
    $("r-since").textContent = moving || E.lastMove < 0 ? "—" : (Math.min(since / 1000, T)).toFixed(2) + " s";
    $("r-bar").style.width = (moving || E.lastMove < 0 ? 0 : Math.min(1, since / 1000 / T) * 100) + "%"; }
  requestAnimationFrame(tick); })();
</script>"""
js = re.sub(r'catch \(err\) \{[^\n]*\}', 'catch (err) { console.warn("ember fallback", err); }', js)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>{HEAD}{CSS}</head>
<body>
<div id="ember"></div>
<main class="deck">{DIRS}</main>
{js}
{READOUT}
</body>
</html>"""
out = CONTENT + ("/ember-page-stills.html" if STILL_MODE else "/ember-page-directions.html")
open(out, "w").write(html)
print(out, len(html), "ember", EMBER)
