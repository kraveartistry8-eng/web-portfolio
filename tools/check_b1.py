import os, re, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from afterglow_hours import HOURS, sheet_times
DECK = os.path.abspath("brand/2026-10-10-density-b1-column.html")
fails = []
html = open(DECK).read()
srcs = re.findall(r'moodboard-media/[^"\')]+\.jpg', html)
ALLOWED = ("f3MgZ_1", "7BF3FrZ", "gE_ypMW")  # repeats Aaron approved, 11 Oct
dupes = {s for s in srcs if srcs.count(s) > 1 and not any(k in s for k in ALLOWED)}
if dupes: fails.append(f"repeated images: {sorted(dupes)}")
if "evenly spaced" in html: fails.append("page 4 caption still says 'evenly spaced'")
if not re.search(r"--fall:linear-gradient\([^;]*#BF15B7[^;]*\)", html): fails.append("--fall token lacks the magenta end")
if not re.search(r"\.fallband\{[^}]*#BF15B7", html): fails.append("fall band lacks the magenta end")
# the hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): page 08 sets its stage's hour over the lead frame
secs = re.split(r'(?=<section class="sheet)', html)[1:]
for i, (want, lead) in enumerate(zip(HOURS, ("wRU1tGM", "tLwiMVf", "gE_ypMW", "7BF3FrZ")), 7):
    sx = secs[i] if len(secs) > i else ''
    m = re.search(r'<p class="hour[^"]*"[^>]*>(.*?)</p>', sx)
    if not m or m.group(1) != want: fails.append(f"sheet {i + 1} hour is {m and m.group(1)!r}, want {want!r}")
    if not re.search(r'class="hpanel"[^>]*>\s*<img[^>]+' + lead, sx): fails.append(f'sheet {i + 1} panel does not hold {lead}')
    if len(re.findall(r'<figure[^>]*>', sx.split('class="stamps"', 1)[1]) if 'class="stamps"' in sx else []) != 4: fails.append(f'sheet {i + 1} wants 4 .stamps figures')
m = re.search(r'<p class="hour[^"]*"[^>]*>(.*?)</p>', secs[0] if secs else '')
if not m or m.group(1) != '19:12': fails.append(f"cover hour is {m and m.group(1)!r}, want '19:12'")
if "One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark." not in (secs[0] if secs else ''): fails.append("cover note missing")
s3 = secs[2] if len(secs) > 2 else ''
got = re.findall(r'<div class="sw[^"]*"[^>]*>.*?<p class="hour[^"]*"[^>]*>(.*?)</p>', s3, re.S)
if got != HOURS: fails.append(f"sheet 3 hours {got}, want {HOURS}")
import subprocess  # sheet 3's readings as committed before the hour (e71db09): none may be lost
base = subprocess.run(["git", "show", "e71db09:brand/2026-10-10-density-b1-column.html"], capture_output=True, text=True).stdout
b3 = re.split(r'(?=<section class="sheet)', base)[3]
for t in sorted(set(re.findall(r'<(?:dd|p class="sw[nr]")[^>]*>(.*?)</', b3))):
    if t not in s3: fails.append(f"sheet 3 lost the reading {t!r}")
tk = re.search(r'<div class="ticks">(.*?)</div>', secs[3] if len(secs) > 3 else '', re.S)
spans = re.findall(r'<span[^>]*>(.*?)</span>', tk.group(1)) if tk else []
hrs = [re.search(r'class="thr">(.*?)<', x) for x in spans]
if [m and m.group(1) for m in hrs] != ["19:12", "19:40", "20:15", "21:30", "dark", None]: fails.append(f"sheet 4 tick hours {[m and m.group(1) for m in hrs]}")
if not re.search(r'<p class="fbig serif">Afterglow.*?19:12.*?</p>', secs[4] if len(secs) > 4 else ''): fails.append("sheet 5 display specimen lacks 19:12")
if "Images are made between 19:12 and 21:30, or lit to look as though they were." not in (secs[6] if len(secs) > 6 else ''): fails.append("sheet 7 lacks the 19:12-21:30 line")
if "Images are made at the end of the day or lit to look as though they were." in html: fails.append("sheet 7 still has the old line")
n_img = len(re.findall(r'<img[^>]+src="[^"]*moodboard-media', html))
if n_img != 33: fails.append(f'{n_img} guide images, want 33 (34 before the hour, less f3MgZ_1 off sheet 3; it stays on sheet 9)')
# the Ember page and the rule that makes room for it (Task 4)
n_sheets = html.count('<section class="sheet')
if n_sheets != 15: fails.append(f"sheet count {n_sheets}, want 15")
if "f3MgZ_1" not in (secs[8] if len(secs) > 8 else ''): fails.append("f3MgZ_1 is gone from sheet 9")
if html.count("R6euaYP") != 1: fails.append(f"R6euaYP appears {html.count('R6euaYP')} times, want once")
if "No state change brightens." in html: fails.append("the old rule 'No state change brightens.' is still in the deck")
for ref in ("page 03", "page 07"):
    if ref not in html: fails.append(f"cross-reference '{ref}' is gone")
WANT = ["Move, and it lights. Stop, and in 0.7 seconds it goes out.", "#321C5B \u2192 #5304E4",
        "Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render.",
        "The light only brightens where the ember is.", "Hover, focus and active states still deepen and never lighten.",
        "The ember is the one exception"]
MEASURE = """()=>{const out=[];document.querySelectorAll('.sheet').forEach((s,i)=>{
 const b=s.getBoundingClientRect();let over=0;
 s.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect();let bot=r.bottom,rt=r.right,lf=r.left;
  for(let a=e.parentElement;a&&a!==s;a=a.parentElement){const c=getComputedStyle(a);if(c.overflowX!=='visible'||c.overflowY!=='visible'){const q=a.getBoundingClientRect();bot=Math.min(bot,q.bottom);rt=Math.min(rt,q.right);lf=Math.max(lf,q.left)}}
  if(r.width&&r.height&&getComputedStyle(e).position!=='fixed')over=Math.max(over,bot-b.bottom,rt-b.right,b.left-lf)});  // what a clipping parent hides is not overflow
 const f=s.querySelector('footer,.foot');const fr=f?Math.round(f.getBoundingClientRect().top-b.top):null;
 out.push({n:i+1,h:Math.round(b.height),over:Math.round(over),foot:fr,bg:s.getAttribute('style')||''})});
 return {sheets:out,hscroll:document.documentElement.scrollWidth-innerWidth}}"""
def _rl(c):
    c = [x / 255 for x in c]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def crossing_contrast(pg, i):
    """Contrast between the hour's ink and the photograph under the part of the numeral that crosses it.
    Shoots the crossing with the numeral shown and hidden; pixels that change are glyph, and the hidden shot is what lies behind them."""
    import io
    from PIL import Image
    box = pg.evaluate(f"""() => {{ const s = document.querySelectorAll('.sheet')[{i}], h = s.querySelector('p.hour'), p = s.querySelector('.hpanel');
      if (!h || !p) return null; scrollTo(0, s.offsetTop); const a = h.getBoundingClientRect(), b = p.getBoundingClientRect();
      const x0 = Math.max(a.left, b.left), x1 = Math.min(a.right, b.right), y0 = Math.max(a.top, b.top), y1 = Math.min(a.bottom, b.bottom);
      return x1 - x0 > 4 && y1 - y0 > 4 ? {{x: x0, y: y0, width: x1 - x0, height: y1 - y0, ink: getComputedStyle(h).color}} : null; }}""")
    if not box: return None
    pg.wait_for_timeout(200)
    clip = {k: box[k] for k in ("x", "y", "width", "height")}
    on = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
    pg.evaluate(f"() => document.querySelectorAll('.sheet')[{i}].querySelector('p.hour').style.visibility = 'hidden'")
    off = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
    pg.evaluate(f"() => document.querySelectorAll('.sheet')[{i}].querySelector('p.hour').style.visibility = ''")
    ink = _rl([int(v) for v in re.findall(r"\d+", box["ink"])[:3]])
    under = [_rl(b) for a, b in zip(on.getdata(), off.getdata()) if sum(abs(x - y) for x, y in zip(a, b)) > 90]
    if len(under) < 50: return None
    bg = sum(under) / len(under)
    return round((max(ink, bg) + .05) / (min(ink, bg) + .05), 2)


with sync_playwright() as p:
    # headless on the real GPU only: a headed window picks up Aaron's real mouse
    br = p.chromium.launch(headless=True, args=["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
    for w in (1440, 768, 390):
        pg = br.new_page(viewport={"width": w, "height": 1000})
        pg.goto("file://" + DECK); pg.wait_for_timeout(800)
        r = pg.evaluate(MEASURE)
        if r["hscroll"] > 0: fails.append(f"{w}px: sideways scroll {r['hscroll']}px")
        for s in r["sheets"]:
            if s["over"] > 1: fails.append(f"{w}px sheet {s['n']}: content overflows by {s['over']}px")
            if w == 1440 and s["h"] != 820: fails.append(f"1440px sheet {s['n']}: height {s['h']}, want 820")
        if w == 1440:
            r12 = pg.evaluate("""() => { const s = document.querySelectorAll('.sheet')[11], h = s && s.querySelector('h2');
              return {h2: h && h.textContent.trim(), bg: s && s.getAttribute('style'), text: document.body.textContent.replace(/\\s+/g, ' ')}; }""")
            if r12["h2"] != "The ember": fails.append(f"sheet 12 h2 is {r12['h2']!r}, want 'The ember'")
            if "linear-gradient(180deg,#321C5B,#1D1231)" not in (r12["bg"] or ""): fails.append(f"sheet 12 ground {r12['bg']!r}")
            for t in WANT:
                if t not in r12["text"]: fails.append(f"missing text: {t!r}")
        if w == 390:
            tops = pg.evaluate("() => [...document.querySelectorAll('.sheet')[11].querySelectorAll('.tri > span')].map(e => e.getBoundingClientRect().top)")
            if len(tops) != 3 or not all(a < b for a, b in zip(tops, tops[1:])): fails.append(f"390px sheet 12: label line not stacked, tops {tops}")
        # the hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): every running head carries its sheet's time
        hr = pg.evaluate("() => [...document.querySelectorAll('.sheet')].map(s => { const e = s.querySelector('.foot .hr'); "
                         "return e ? [e.textContent.trim(), Math.round(e.getBoundingClientRect().width)] : [null, 0]; })")
        if [t for t, _ in hr] != sheet_times(len(hr)): fails.append(f"{w}px: running-head times {[t for t, _ in hr]}, want {sheet_times(len(hr))}")
        if any(wd == 0 for _, wd in hr): fails.append(f"{w}px: a running-head time is hidden on sheets {[i + 1 for i, (_, wd) in enumerate(hr) if wd == 0]}")
        sw = pg.evaluate("() => [...document.querySelectorAll('.sheet')[2].querySelectorAll('.sw')].map(e => { const r = e.getBoundingClientRect(); return [r.width, r.top]; })")
        if w == 1440 and (len(sw) != 4 or any(abs(a[0] / sw[0][0] - k / 1.6) > .02 for a, k in zip(sw, (1.6, 1, .8, .6)))):
            fails.append(f"1440px sheet 3: column widths {[round(a[0]) for a in sw]}, want 1.6 : 1 : 0.8 : 0.6")
        if w == 768 and not (len(sw) == 4 and all(a[1] < b[1] for a, b in zip(sw, sw[1:]))): fails.append(f"768px sheet 3: the four stages do not stack {sw}")
        if w == 390:
            e = pg.evaluate("() => { const s = document.querySelectorAll('.sheet')[7], h = s.querySelector('p.hour'); "
                            "return h ? [h.getBoundingClientRect().right, s.getBoundingClientRect().right] : null; }")
            if not e or e[0] > e[1] - 16: fails.append(f'390px sheet 8: hour runs to {e}, want inside the 16px gutter')
        if w == 1440:
            feet = {s["foot"] for s in r["sheets"]}
            if len(feet) > 1: fails.append(f"1440px: running head offsets differ {sorted(x for x in feet if x is not None)}")
            if "#BF15B7" not in r["sheets"][-1]["bg"]: fails.append("last sheet ground does not end on #BF15B7")
    # the hour crossing the photograph passes 3:1 against what is behind it (no scrim, no shadow)
    pg = br.new_page(viewport={"width": 1440, "height": 1000}); pg.goto("file://" + DECK); pg.wait_for_timeout(800)
    for i in [7, 8, 9, 10]:
        cr = crossing_contrast(pg, i)
        if cr is None or cr < 3: fails.append(f'1440px sheet {i + 1}: hour over the photograph at {cr}:1, want 3:1')
    pg.close()
    # the ember (Task 3): one canvas behind the sheets; grounds go transparent only once it has drawn
    SHEETS = """() => [...document.querySelectorAll('.sheet')].map(s => { const c = getComputedStyle(s);
      return {cover: s.classList.contains('bcover'), bc: c.backgroundColor, bi: c.backgroundImage}; })"""
    pg = br.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.goto("file://" + DECK)
    try:
        pg.wait_for_function("document.documentElement.classList.contains('ember-on')", timeout=6000)
    except Exception:
        fails.append("ember: ember-on never set on <html>")
    if pg.evaluate("() => document.querySelectorAll('#ember canvas').length") != 1: fails.append("ember: want exactly one canvas under #ember")
    for i, s in enumerate(pg.evaluate(SHEETS)):
        if not s["cover"] and (s["bc"] != "rgba(0, 0, 0, 0)" or s["bi"] != "none"):
            fails.append(f"ember: sheet {i + 1} keeps its ground with ember-on ({s['bc']}, {s['bi'][:40]})")
    # everything reacts (Aaron, 11 Oct): a photograph, a colour swatch and body text each catch the ember's light
    pg.evaluate("() => scrollTo(0, document.querySelectorAll('.sheet')[2].offsetTop)"); pg.wait_for_timeout(300)
    for sel in (".sheet:nth-child(2) figure", ".sheet:nth-child(3) .sw", ".sheet:nth-child(3) .fine2", ".sheet:nth-child(8) p.hour"):
        if not pg.evaluate(f"() => !!document.querySelector('{sel}')"): fails.append(f"everything reacts: no {sel}"); continue
        pg.evaluate(f"() => scrollTo(0, document.querySelector('{sel}').getBoundingClientRect().top + scrollY - 200)"); pg.wait_for_timeout(300)
        b = pg.evaluate(f"() => {{ const r = document.querySelector('{sel}').getBoundingClientRect(); return [r.left, r.bottom]; }}")
        for i in range(26):
            pg.mouse.move(b[0] + 30 + (i % 2) * 24, b[1] + 6 + (i % 3) * 4); pg.wait_for_timeout(16)
        li = pg.evaluate(f"() => +getComputedStyle(document.querySelector('{sel}')).getPropertyValue('--li') || 0")
        if li <= .4: fails.append(f"everything reacts: {sel} --li {li} beside the ember, want > 0.4")
        pg.wait_for_timeout(600)
    n = pg.evaluate("() => ember.lit.length")
    if n < 400: fails.append(f"everything reacts: only {n} elements are lit")
    pg.evaluate("() => { window.__lm = 0; const o = ember.onFrame; ember.onFrame = (e, d) => { __lm = Math.max(__lm, e.lightMs || 0); o && o(e, d); }; }")
    for i in range(40):
        pg.mouse.move(200 + i * 25, 300 + (i % 5) * 30); pg.wait_for_timeout(16)
    lm = pg.evaluate("() => __lm")
    if not lm or lm > 4: fails.append(f"everything reacts: light loop took {lm} ms in a frame, want under 4")
    pg.emulate_media(media="print")
    r = pg.evaluate("() => [getComputedStyle(document.getElementById('ember') || document.body).display, getComputedStyle(document.querySelectorAll('.sheet')[1]).backgroundImage]")
    if r[0] != "none": fails.append("test_print_grounds: #ember prints")
    if "gradient" not in r[1]: fails.append("test_print_grounds: sheet 2 prints without its gradient")
    hid = pg.evaluate("() => [...document.querySelectorAll('.sheet')].map((s, i) => { const e = s.querySelector('.foot .hr'); return e && e.getBoundingClientRect().width ? 0 : i + 1; }).filter(Boolean)")
    if hid: fails.append(f"print: running-head time hidden on sheets {hid}")
    pg.emulate_media(media="screen")
    pg.evaluate("() => ember.renderer.forceContextLoss()")
    pg.wait_for_timeout(400)
    r = pg.evaluate("() => [document.documentElement.classList.contains('ember-on'), getComputedStyle(document.querySelectorAll('.sheet')[1]).backgroundImage]")
    if r[0]: fails.append("test_context_lost_restores_ground: ember-on still set")
    if "gradient" not in r[1]: fails.append("test_context_lost_restores_ground: sheet 2 has no gradient")
    if errs: fails.append(f"ember: console errors {errs[:3]}")
    pg.close()
    # with JavaScript off the deck is complete: heights hold and every sheet keeps its ground
    ctx = br.new_context(viewport={"width": 1440, "height": 1000}, java_script_enabled=False)
    pg = ctx.new_page(); pg.goto("file://" + DECK); pg.evaluate("() => document.fonts.ready.then(() => 0)"); pg.wait_for_timeout(300)
    r = pg.evaluate(MEASURE)
    for s in r["sheets"]:
        if s["over"] > 1 or s["h"] != 820: fails.append(f"no JS: sheet {s['n']} height {s['h']}, overflow {s['over']}")
    if "gradient" not in pg.evaluate("() => getComputedStyle(document.querySelectorAll('.sheet')[1]).backgroundImage"):
        fails.append("no JS: sheet 2 lost its ground")
    ctx.close()
    # opened offline: with the web fonts blocked the fallback face must not push anything sideways
    for w in (1440, 390):
        ctx = br.new_context(viewport={"width": w, "height": 1000}, java_script_enabled=False)
        ctx.route("**/fonts.g*/**", lambda r: r.abort())
        pg = ctx.new_page(); pg.goto("file://" + DECK); pg.wait_for_timeout(400)
        hs = pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
        if hs > 0: fails.append(f"{w}px, fonts blocked: sideways scroll {hs}px")
        hour_sheets = pg.evaluate("() => [...document.querySelectorAll('.sheet')].map((s, i) => s.querySelector('p.hour') ? i + 1 : 0).filter(Boolean)")
        for s in pg.evaluate(MEASURE)["sheets"]:  # overflow-x:clip hides a too-wide numeral from the scroll test; measure the hour sheets
            if s["n"] in hour_sheets and s["over"] > 1: fails.append(f"{w}px, fonts blocked: sheet {s['n']} overflows by {s['over']}px")
        ctx.close()
    br.close()
print("\n".join(fails) or "PASS"); sys.exit(1 if fails else 0)
