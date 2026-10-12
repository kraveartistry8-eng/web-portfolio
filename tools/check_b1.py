import os, re, sys
from playwright.sync_api import sync_playwright
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
# the Ember page and the rule that makes room for it (Task 4)
n_sheets = html.count('<section class="sheet')
if n_sheets != 15: fails.append(f"sheet count {n_sheets}, want 15")
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
 s.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect();
  if(r.width&&r.height&&getComputedStyle(e).position!=='fixed')over=Math.max(over,r.bottom-b.bottom,r.right-b.right,b.left-r.left)});
 const f=s.querySelector('footer,.foot');const fr=f?Math.round(f.getBoundingClientRect().top-b.top):null;
 out.push({n:i+1,h:Math.round(b.height),over:Math.round(over),foot:fr,bg:s.getAttribute('style')||''})});
 return {sheets:out,hscroll:document.documentElement.scrollWidth-innerWidth}}"""
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
        if w == 1440:
            feet = {s["foot"] for s in r["sheets"]}
            if len(feet) > 1: fails.append(f"1440px: running head offsets differ {sorted(x for x in feet if x is not None)}")
            if "#BF15B7" not in r["sheets"][-1]["bg"]: fails.append("last sheet ground does not end on #BF15B7")
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
    pg.emulate_media(media="print")
    r = pg.evaluate("() => [getComputedStyle(document.getElementById('ember') || document.body).display, getComputedStyle(document.querySelectorAll('.sheet')[1]).backgroundImage]")
    if r[0] != "none": fails.append("test_print_grounds: #ember prints")
    if "gradient" not in r[1]: fails.append("test_print_grounds: sheet 2 prints without its gradient")
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
        ctx.close()
    br.close()
print("\n".join(fails) or "PASS"); sys.exit(1 if fails else 0)
