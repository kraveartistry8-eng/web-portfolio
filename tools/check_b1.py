import os, re, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from afterglow_hours import HOURS, sheet_times
import afterglow_specimen as A
import subprocess as _sp
BASE = _sp.run(["git", "show", f"{A.BASE_REF}:brand/2026-10-10-density-b1-column.html"], capture_output=True, text=True).stdout
DECK = os.path.abspath("brand/guide-sources/2026-10-10-density-b1-column.html")
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
    if 'class="strip"' in sx:  # the specimen colour page (spec 2026-10-12 §4): the strip, four stamps, the hour under it
        if len(re.findall(r'<figure[^>]*>', sx.split('class="strip"', 1)[1])) != 5: fails.append(f'sheet {i + 1} strip wants 5 figures')
        if len(re.findall(r'<p class="stamp">', sx)) != 4: fails.append(f'sheet {i + 1} wants 4 minute stamps')
        if not re.search(r'class="lead"[^>]*>\s*<img[^>]+' + lead, sx): fails.append(f'sheet {i + 1} strip does not lead with {lead}')
        if not re.search(r'<p class="hour">' + want + '</p>', sx): fails.append(f"sheet {i + 1} hour is not {want!r}")
        continue
    m = re.search(r'<p class="hour[^"]*"[^>]*>(.*?)</p>', sx)
    if not m or m.group(1) != want: fails.append(f"sheet {i + 1} hour is {m and m.group(1)!r}, want {want!r}")
    if not re.search(r'class="hpanel"[^>]*>\s*<img[^>]+' + lead, sx): fails.append(f'sheet {i + 1} panel does not hold {lead}')
    if len(re.findall(r'<figure[^>]*>', sx.split('class="stamps"', 1)[1]) if 'class="stamps"' in sx else []) != 4: fails.append(f'sheet {i + 1} wants 4 .stamps figures')
# the specimen sheets 01-05 (spec 2026-10-12 §4); their old readings now live on reference sheet 16
if "One fragrance in four stages, from 19:12 until it is dark." not in (secs[0] if secs else ''): fails.append("cover line missing")
if "<svg" not in (secs[0] if secs else ''): fails.append("cover lacks the mark")
s3 = secs[2] if len(secs) > 2 else ''
got = re.findall(r'<div class="sws">.*?<p class="hour[^"]*"[^>]*>(.*?)</p>', s3, re.S)
if got != HOURS: fails.append(f"sheet 3 hours {got}, want {HOURS}")
import subprocess  # the readings as committed before the hour (e71db09): none may be lost, and they now sit on sheet 16
base = subprocess.run(["git", "show", "e71db09:brand/2026-10-10-density-b1-column.html"], capture_output=True, text=True).stdout
b3 = re.split(r'(?=<section class="sheet)', base)[3]
s16 = secs[15] if len(secs) > 15 else ''
for t in sorted(set(re.findall(r'<(?:dd|p class="sw[nr]")[^>]*>(.*?)</', b3))):
    if t not in s16: fails.append(f"sheet 16 lacks the reading {t!r}")
tk = re.search(r'<div class="ticks">(.*?)</div>', s16, re.S)
spans = re.findall(r'<span[^>]*>(.*?)</span>', tk.group(1)) if tk else []
hrs = [re.search(r'class="thr">(.*?)<', x) for x in spans]
if [m and m.group(1) for m in hrs] != ["19:12", "19:40", "20:15", "21:30", "dark", None]: fails.append(f"sheet 16 tick hours {[m and m.group(1) for m in hrs]}")
if not re.search(r'<p class="fbig serif">Afterglow.*?19:12.*?</p>', secs[16] if len(secs) > 16 else ''): fails.append("sheet 17 display specimen lacks 19:12")
if "Images are made between 19:12 and 21:30, or lit to look as though they were." not in html: fails.append("the deck lacks the 19:12-21:30 line")
if "Images are made at the end of the day or lit to look as though they were." in html: fails.append("sheet 7 still has the old line")
n_img = len(re.findall(r'<img[^>]+src="[^"]*moodboard-media', html))
if n_img != 31: fails.append(f'{n_img} guide images, want 31 (33 before the specimen, less the second 7BF3FrZ and gE_ypMW)')
# the Ember page and the rule that makes room for it (Task 4)
n_sheets = html.count('<section class="sheet')
if n_sheets != 19: fails.append(f"sheet count {n_sheets}, want 19")
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
    for w in (1440, 1024, 768, 390):
        pg = br.new_page(viewport={"width": w, "height": 1000})
        pg.goto("file://" + DECK); pg.wait_for_timeout(800)
        r = pg.evaluate(MEASURE)
        if r["hscroll"] > 0: fails.append(f"{w}px: sideways scroll {r['hscroll']}px")
        for s in r["sheets"]:
            if s["over"] > 1: fails.append(f"{w}px sheet {s['n']}: content overflows by {s['over']}px")
            if w == 1440 and (s["h"] < 820 if s["n"] >= 16 else s["h"] != 820): fails.append(f"1440px sheet {s['n']}: height {s['h']}, want 820" + (" or more" if s["n"] >= 16 else ""))
        if w == 1440:
            r12 = pg.evaluate("""() => { const s = document.querySelectorAll('.sheet')[11], h = s && s.querySelector('h2');
              return {h2: h && h.textContent.trim(), bg: s && s.getAttribute('style'), text: document.body.textContent.replace(/\\s+/g, ' ')}; }""")
            if "The ember" not in r12["text"]: fails.append("the deck lost the heading 'The ember'")  # it moved to sheet 17 (spec 2026-10-12)
            if "linear-gradient(180deg,#321C5B,#1D1231)" not in (r12["bg"] or ""): fails.append(f"sheet 12 ground {r12['bg']!r}")
            for t in WANT:
                if t not in r12["text"]: fails.append(f"missing text: {t!r}")
        if w == 390:
            # page 14 (spec 2026-10-12 §6): the label first, then the poster and the card side by side
            pr = pg.evaluate("() => { const s = document.querySelectorAll('.sheet')[13]; return ['.label', '.poster', '.card'].map(q => { const r = s.querySelector(q).getBoundingClientRect(); return [r.top, r.bottom]; }); }")
            if not (pr[0][1] <= pr[1][0] and abs(pr[1][1] - pr[2][1]) <= 1): fails.append(f"390px sheet 14: want the label above, poster and card side by side: {pr}")
        if w == 1440:
            g = pg.evaluate("""() => [...document.querySelectorAll('.sheet')].slice(0, 15).map(s => { const z = new Set(); let obj = 0;
              s.querySelectorAll('*').forEach(e => { if (![...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()) || !e.getClientRects().length) return;
                if (e.closest('.oo, .strip, .swc, .fhrs, .hline .hour, .rspec, .wmc, .amark')) obj = 1; else z.add(getComputedStyle(e).fontSize); });
              const caps = [...s.querySelectorAll('.obj > .cap')].map(c => Math.round(c.getBoundingClientRect().height / parseFloat(getComputedStyle(c).lineHeight)));
              return [z.size + obj, [...z], caps]; })""")
            for n, (k, z, caps) in enumerate(g, 1):
                if k > 3: fails.append(f"1440px sheet {n}: {k} type sizes, want 3 or fewer ({z} + object)")
                if any(c > 2 for c in caps): fails.append(f"1440px sheet {n}: a caption runs to {max(caps)} lines")
        # mark_min_width (spec §2): no mark under 48 px at any width
        mw = pg.evaluate("() => [...document.querySelectorAll('svg.amark')].map(e => Math.round(e.getBoundingClientRect().width))")
        if not mw or min(mw) < 48: fails.append(f"{w}px: a mark under 48 px wide: {mw}")
        # preserved_strings_visible (spec 2026-10-12 §4): every string of the committed deck is on a rendered element
        vis = pg.evaluate("""() => { const w = document.createTreeWalker(document.querySelector('main'), NodeFilter.SHOW_TEXT); const out = [];
          for (let n; (n = w.nextNode());) { const e = n.parentElement, c = getComputedStyle(e);
            if (e.getClientRects().length && c.visibility !== 'hidden' && +c.opacity > 0) out.push(n.textContent); }
          return out.join(' '); }""")
        vis = re.sub(r"\s+", " ", vis)
        chrome = set(A.texts("".join(re.findall(r'<footer class="foot">.*?</footer>', BASE))))  # the running head's labels fold away on a phone by design
        hidden = [t for t in A.lost_strings(BASE, "") if t not in vis and t not in chrome] if w in (1440, 390) else []
        if hidden: fails.append(f"{w}px: {len(hidden)} preserved strings not visible, e.g. {hidden[:4]}")
        # the hour (spec 2026-10-11-afterglow-guide-hour-design.md §3): every running head carries its sheet's time
        hr = pg.evaluate("() => [...document.querySelectorAll('.sheet')].map(s => { const e = s.querySelector('.foot .hr'); "
                         "return e ? [e.textContent.trim(), Math.round(e.getBoundingClientRect().width)] : [null, 0]; })")
        if [t for t, _ in hr] != sheet_times(len(hr)): fails.append(f"{w}px: running-head times {[t for t, _ in hr]}, want {sheet_times(len(hr))}")
        if any(wd == 0 for _, wd in hr): fails.append(f"{w}px: a running-head time is hidden on sheets {[i + 1 for i, (_, wd) in enumerate(hr) if wd == 0]}")
        if w == 390:
            e = pg.evaluate("() => { const s = document.querySelectorAll('.sheet')[7], h = s.querySelector('p.hour'); "
                            "return h ? [h.getBoundingClientRect().right, s.getBoundingClientRect().right] : null; }")
            if not e or e[0] > e[1] - 16: fails.append(f'390px sheet 8: hour runs to {e}, want inside the 16px gutter')
        if w == 1440:
            feet = {s["foot"] for s in r["sheets"]}
            if len(feet) > 1: fails.append(f"1440px: running head offsets differ {sorted(x for x in feet if x is not None)}")
            if "#BF15B7" not in r["sheets"][-1]["bg"]: fails.append("last sheet ground does not end on #BF15B7")
            if any("#BF15B7" in x["bg"] for x in r["sheets"][:-1]): fails.append("a sheet before the last carries the magenta")
            # ref_sheets_never_clip: the reference sheets grow; their type never drops under 11 px
            small = pg.evaluate("""() => [...document.querySelectorAll('.sheet.ref')].flatMap((s, i) => [...s.querySelectorAll('*')].filter(e =>
              [...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 11).map(e => (16 + i) + ':' + e.textContent.trim().slice(0, 30)))""")
            if small: fails.append(f"reference type under 11 px: {small[:5]}")
    # the strips (spec 2026-10-12 §6): one row at 1024; at 768 the lead alone then four at 140; at 390 the lead full width, then 2 x 2
    STRIP = """() => [...document.querySelectorAll('.sheet')].slice(6, 11).map(s => [...s.querySelectorAll('.strip figure')].map(f => {
      const r = (f.closest('.fr') || f).getBoundingClientRect();  /* a frame's foot is under its stamp */ return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.bottom)]; }))"""
    for w in (1024, 768, 390):
        pg = br.new_page(viewport={"width": w, "height": 1000}); pg.goto("file://" + DECK); pg.wait_for_timeout(500)
        for n, figs in enumerate(pg.evaluate(STRIP), 7):
            if not figs: continue
            lead, rest = figs[0], figs[1:]
            if w == 1024 and not all(abs(f[3] - lead[3]) <= 1 for f in rest): fails.append(f"1024px sheet {n}: strip not on one row, feet {[f[3] for f in figs]}")
            if w == 768 and (abs(lead[2] - 260) > 1 or any(abs(f[2] - 140) > 1 or f[1] <= lead[3] - 1 for f in rest) or len({f[1] for f in rest}) != 1):
                fails.append(f"768px sheet {n}: want the lead at 260 alone, then a row at 140: {figs}")
            if w == 390 and (abs(lead[2] - (390 - 32)) > 1 or len({f[1] for f in rest}) != min(2, (len(rest) + 1) // 2)):
                fails.append(f"390px sheet {n}: want the lead full width less 32, the rest two by two: {figs}")
        r = pg.evaluate(MEASURE)
        if w == 1024:
            for x in r["sheets"]:
                if x["over"] > 1: fails.append(f"1024px sheet {x['n']}: content overflows by {x['over']}px")
        pg.close()
    # the hour crossing the photograph passes 3:1 against what is behind it (no scrim, no shadow)
    pg = br.new_page(viewport={"width": 1440, "height": 1000}); pg.goto("file://" + DECK); pg.wait_for_timeout(800)
    for i in [i for i in [7, 8, 9, 10] if 'class="strip"' not in secs[i]]:  # the specimen pages set the hour on the ground, not over a photograph
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
    for sel in (".sheet:nth-child(2) figure", ".sheet:nth-child(3) .swc", ".sheet:nth-child(16) dd", ".sheet:nth-child(8) p.hour"):
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
        if s["over"] > 1 or (s["h"] < 820 if s["n"] >= 16 else s["h"] != 820): fails.append(f"no JS: sheet {s['n']} height {s['h']}, overflow {s['over']}")
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
        for s in pg.evaluate(MEASURE)["sheets"]:  # overflow-x:clip hides a too-wide numeral or wordmark from the scroll test; measure every sheet
            if s["over"] > 1: fails.append(f"{w}px, fonts blocked: sheet {s['n']} overflows by {s['over']}px")
        ctx.close()
    br.close()
print("\n".join(fails) or "PASS"); sys.exit(1 if fails else 0)
