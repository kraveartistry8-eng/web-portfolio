# Afterglow Guide B1 Polish Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make deck B1 read as one document: one sheet template, no clipping at any width, the magenta end carried wherever the fall appears as a gradient, with content and images unchanged.

**Architecture:** All changes go into the generator `tools/density_b_family.py` (B1 CSS, sheet builders, document ground) and, where a helper is shared, `tools/density_directions.py`. The deck HTML is never hand-edited; it is rebuilt. A new check script measures the rendered deck so every task has a pass/fail.

**Tech Stack:** Python 3 generator, static HTML/CSS, Playwright (Chromium) for measurement.

**Spec:** approved in conversation 10 Oct 2026 (polish spec: one template, stage pages, text, dead space, responsive, magenta).

---

### Task 1: Write the check that fails today

**Files:**
- Create: `tools/check_b1.py`

- [ ] **Step 1: Write the check.** It opens the B1 deck at 1440, 768 and 390 wide and reports, per width: each sheet's height, how far any element pokes past its sheet, and page-level sideways scroll. At 1440 it also reads each footer rule's distance from its sheet's bottom edge. It also asserts: no repeated moodboard image, the phrase "evenly spaced" is gone, the fall band and the fall token both end on #BF15B7, and the last sheet's ground ends on #BF15B7. Exit code 1 on any failure, with one line per failure.

```python
import os, re, sys
from playwright.sync_api import sync_playwright
DECK = os.path.abspath("brand/2026-10-10-density-b1-column.html")
fails = []
html = open(DECK).read()
srcs = re.findall(r'moodboard-media/[^"\')]+\.jpg', html)
dupes = {s for s in srcs if srcs.count(s) > 1}
if dupes: fails.append(f"repeated images: {sorted(dupes)}")
if "evenly spaced" in html: fails.append("page 4 caption still says 'evenly spaced'")
if not re.search(r"--fall:linear-gradient\([^;]*#BF15B7[^;]*\)", html): fails.append("--fall token lacks the magenta end")
if not re.search(r"\.fallband\{[^}]*#BF15B7", html): fails.append("fall band lacks the magenta end")
MEASURE = """()=>{const out=[];document.querySelectorAll('.sheet').forEach((s,i)=>{
 const b=s.getBoundingClientRect();let over=0;
 s.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect();
  if(r.width&&r.height&&getComputedStyle(e).position!=='fixed')over=Math.max(over,r.bottom-b.bottom,r.right-b.right,b.left-r.left)});
 const f=s.querySelector('footer,.foot');const fr=f?Math.round(b.bottom-f.getBoundingClientRect().top):null;
 out.push({n:i+1,h:Math.round(b.height),over:Math.round(over),foot:fr,bg:s.getAttribute('style')||''})});
 return {sheets:out,hscroll:document.documentElement.scrollWidth-innerWidth}}"""
with sync_playwright() as p:
    br = p.chromium.launch()
    for w in (1440, 768, 390):
        pg = br.new_page(viewport={"width": w, "height": 1000})
        pg.goto("file://" + DECK); pg.wait_for_timeout(800)
        r = pg.evaluate(MEASURE)
        if r["hscroll"] > 0: fails.append(f"{w}px: sideways scroll {r['hscroll']}px")
        for s in r["sheets"]:
            if s["over"] > 1: fails.append(f"{w}px sheet {s['n']}: content overflows by {s['over']}px")
            if w == 1440 and s["h"] != 820: fails.append(f"1440px sheet {s['n']}: height {s['h']}, want 820")
        if w == 1440:
            feet = {s["foot"] for s in r["sheets"]}
            if len(feet) > 1: fails.append(f"1440px: footer offsets differ {sorted(x for x in feet if x is not None)}")
            if "#BF15B7" not in r["sheets"][-1]["bg"]: fails.append("last sheet ground does not end on #BF15B7")
    br.close()
print("\n".join(fails) or "PASS"); sys.exit(1 if fails else 0)
```

- [ ] **Step 2: Run it and confirm it fails.** Run `python3 tools/check_b1.py`. Expected: FAIL lines for sheets 7, 8–11 and 13 heights, the 390px sideways scroll and overflows on sheets 2, 3, 5, 6 and 13, the caption, the fall token and the last-sheet ground.

### Task 2: One template on desktop

**Files:** Modify `tools/density_b_family.py` (B1 CSS block and `spread()`), and `tools/density_directions.py` only if the footer helper lives there.

- [ ] Fix every desktop sheet at 1440 × 820, overflow hidden only at the sheet edge, never on content.
- [ ] Place the footer the same way on every sheet: same side margins, same distance from the bottom, its rule always drawn.
- [ ] Stage pages 8–11: move the grid to about 48px under the header bar and let it fill to the footer, so those sheets come back to 820.
- [ ] Sheets 7 and 13: tighten whichever block pushes them past 820. No content is removed.
- [ ] Deep violet: give the header bar and colour chip a 1px outline at 35% white.
- [ ] Rebuild with `python3 tools/density_b_family.py`. Run the check: the desktop height and footer lines must be gone.

### Task 3: Text and dead space

**Files:** Modify `tools/density_b_family.py`; the caption lives in the source guide panel that the generator lifts, so the rewrite happens in the generator as a string replacement after the lift.

- [ ] Page 4: replace "Four stops, evenly spaced." with "Four stages fall to the void and end on a sliver of #BF15B7." Keep the surrounding rule untouched.
- [ ] Pages 5 and 6: re-break the headings so no single word is left on a line (a non-breaking space between the last two words).
- [ ] Page 6: stop the grid-column overlay at the edge of the body copy so the copy sits on a plain ground.
- [ ] Page 5: close up the empty middle column; page 2: close up the space under "Six ways to break it" by moving existing content, adding nothing.
- [ ] Rebuild, run the check: the caption line must be gone. Screenshot pages 2, 4, 5 and 6 and look at them.

### Task 4: The magenta carried through

**Files:** Modify `tools/density_b_family.py` (document ground and CSS token override).

- [ ] Override the fall token so it reads gold, after gold, rose, violet, void, then the #BF15B7 sliver, in the same proportions as the fall band.
- [ ] The document ground: the last sheet stays void and ends with a magenta sliver along its bottom edge, matching the band's sliver (void, then a short fade into #BF15B7). Sheet 13 and the body of sheet 14 stay fully black.
- [ ] Leave the misuse tiles exactly as they are.
- [ ] Rebuild, run the check: the fall token and last-sheet lines must be gone.

### Task 5: Responsive

**Files:** Modify `tools/density_b_family.py` (B1 CSS: two breakpoint blocks).

- [ ] 577–992px: sheets take their natural height; each image column drops under its title; panels keep two columns; stage grids go two across with the lead image full width on top.
- [ ] 576px and below: single column, in order title, image, readings, panels; "Six ways to break it" full width, one rule per row; the wordmark scales to the screen width; stage grids one across; 16px side gutters.
- [ ] Headings scale fluidly between their phone and desktop sizes.
- [ ] Rebuild, run the check: zero failures at all three widths. Screenshot 390px sheets 2, 3, 5, 6 and 13 and look at them.

### Task 6: Prove it

- [ ] Run `python3 tools/check_b1.py`. Expected: `PASS`.
- [ ] Re-render all 14 sheets and the 390px view; hand them and the pinned Frame.io bands to a fresh critic with labels stripped. Record the verdict and the single biggest gap.
- [ ] Open the deck for Aaron.
- [ ] Commit the generator, the check script, the rebuilt deck and this plan, only when Aaron asks.
