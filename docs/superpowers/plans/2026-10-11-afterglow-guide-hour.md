# Afterglow Guide: The Hour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the four stages into four hours of one evening across the Afterglow guide: huge hour numerals on the stage sheets, and each sheet's own time in its running head.

**Architecture:** The hour maths (fall position to clock time) lives in one small pure module with unit tests. The sheet builders in the generator consume it. Browser checks extend the existing `tools/check_b1.py`. Page 08 is built first and shown to Aaron; nothing after Task 3 starts without his approval.

**Tech Stack:** Python 3 generator, pytest, Playwright on the real GPU (headless only), the existing EmberEngine bundle (unchanged).

**Spec:** `docs/superpowers/specs/2026-10-11-afterglow-guide-hour-design.md`

## Global Constraints

- The hours: Gold of last light is 19:12, After gold 19:40, Rose 20:15 and Deep violet 21:30; the ground is "dark". They are never changed or reordered, and never animated.
- Use only images already in the guide, each once (the allowed repeats are f3MgZ_1, 7BF3FrZ and gE_ypMW). No imagery of Black women with short or shaved hair.
- No sheet is lighter than the one before it. Every sheet keeps its ground from `ground(i, n_fall)`.
- Numerals over photographs get no scrim, shadow, blend or outline. Where a numeral crosses a photograph it must pass 3:1; if it fails, move the crop.
- Numerals are Instrument Serif 400, line height 0.8, tracking −0.03 em, never widened. The 150% width is the wordmark's alone.
- No reading (hex, OKLCH, CMYK, contrast) and no page number is removed from any sheet.
- No change to the ember's behaviour, and no change to the Shopify theme.
- Playwright runs headless with `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`, never headed.
- Commit only when Aaron says.

## Review Focus

1. **Fonts blocked offline.** At 390 px the fallback serif is wider, and a 150 px "21:30" must not push the sheet sideways. The existing fonts-blocked check covers this once numerals exist; Task 3 confirms it runs over page 08.
2. **768 px colour sheet.** The 0.6-weight column falls under 120 px, so the sheet must switch to rows below 993 px. Task 5 tests that at 768 px.
3. **Sheet count changes.** If a sheet is added, every time must move with it. Task 1 tests `sheet_times(14)` as well as `sheet_times(15)`.
4. **Ember over numerals.** The numerals are `p` elements, so they are lit text. Task 3 checks that a numeral's `--li` rises beside the ember.
5. **Print.** Times in the running head must print, and numerals must not overflow an A4 landscape page. Task 4 adds a print-media check that every sheet's footer time is visible.

---

### Task 1: The hour maths

**Files:**
- Create: `tools/afterglow_hours.py`
- Test: `tools/test_afterglow_hours.py`
- Modify: `docs/superpowers/specs/2026-10-11-afterglow-guide-hour-design.md` (§2 table)

**Interfaces:**
- Produces:
  - `HOURS = ["19:12", "19:40", "20:15", "21:30"]`
  - `hour_at(t: float) -> str`, which returns "HH:MM", or "dark" at t ≥ 1
  - `sheet_times(n_sheets: int = 15, n_fall: int = 13) -> list[str]`, one entry per sheet. Sheet 1 (the cover) is "19:12". Sheet k from 2 to n_fall is `hour_at((k-1)/n_fall)`. Sheets after n_fall are "dark".

- [ ] **Step 1: Write the failing tests**

```python
from afterglow_hours import HOURS, hour_at, sheet_times
def test_stops_are_the_hours():
    assert [hour_at(t) for t in (0, .30, .60, .84)] == HOURS
def test_ground_is_dark():
    assert hour_at(1) == "dark" and hour_at(1.2) == "dark"
def test_past_violet_runs_at_violet_rate():
    assert hour_at(.84 + .16 / 2) == "21:55"          # 312.5 min per unit past .84
def test_sheet_times_for_the_guide():
    assert sheet_times() == ["19:12", "19:19", "19:26", "19:34", "19:41", "19:50", "19:59", "20:08",
                             "20:20", "20:44", "21:08", "21:32", "21:56", "dark", "dark"]
def test_times_never_go_back():
    mins = [int(h[:2]) * 60 + int(h[3:]) for h in sheet_times() if h != "dark"]
    assert mins == sorted(mins)
def test_times_move_when_a_sheet_is_removed():
    assert sheet_times(14, 12)[11] != sheet_times()[11]
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `cd tools && python3 -m pytest test_afterglow_hours.py -q`
Expected: ImportError (no module `afterglow_hours`).

- [ ] **Step 3: Implement `hour_at` and `sheet_times`**

Minutes after 19:12 are piecewise linear through (0, 0), (.30, 28), (.60, 63) and (.84, 138). Past .84 they continue at 75/.24 minutes per unit. Round to the nearest minute.

- [ ] **Step 4: Run them and confirm they pass**

Run: `cd tools && python3 -m pytest test_afterglow_hours.py -q`
Expected: 6 passed.

- [ ] **Step 5: Correct the spec's §2 table**

Replace the table with the computed times. Change the sentence about sheet 12 to say it reads 21:32.

---

### Task 2: Time in every running head

**Files:**
- Modify: `tools/density_b_family.py`, in `build()` (the b1-column branch) and in `B_CSS`
- Test: `tools/check_b1.py`

**Interfaces:**
- Consumes: `sheet_times()` from Task 1.
- Produces: each sheet's `<footer class="foot">` gains `<span class="hr">HH:MM</span>`, placed directly before `<span class="pg">`.

- [ ] **Step 1: Add the failing check to `tools/check_b1.py`**

At 1440 px, the text of `.sheet .foot .hr` for each of the 15 sheets must equal `sheet_times()`. At 390 px each `.hr` must have a non-zero width; the sheet name may hide, but the time and page number may not.

- [ ] **Step 2: Run it and confirm it fails**

Run: `python3 tools/density_b_family.py && python3 tools/check_b1.py`
Expected: a failure line naming `.hr` for each sheet.

- [ ] **Step 3: Insert the times**

In the b1-column branch of `build()`, after `copy_pass`, insert the time span into each footer in sheet order. The span takes the `.pg` span's type: caption size, tracking 0.14 em, upper case. Below 577 px, hide `.foot .doc` and the section name, and keep `.hr` and `.pg`.

- [ ] **Step 4: Run it and confirm it passes**

Run: `python3 tools/density_b_family.py && python3 tools/check_b1.py`
Expected: `PASS`. The running-head offsets stay equal, so the existing check still holds.

---

### Task 3: Page 08, then stop for Aaron

**Files:**
- Modify: `tools/density_b_family.py`. Add `spread_hour(k, pg, style, ink)` beside `spread()`; `build()` calls it for k = 0 only. Add its CSS to `B_CSS`.
- Test: `tools/check_b1.py`

**Interfaces:**
- Consumes: `HOURS` from Task 1; `SPREADS`, `STAGES` and `media()`, which exist already.
- Produces:
  - `spread_hour(k, pg, style, ink) -> str`, with the same signature and footer as `spread()`. Task 4 calls it for k = 0 to 3.
  - The markup it produces:
    - `.panel` holds the lead frame `SPREADS[k][0]`
    - `p.hour` holds `HOURS[k]`
    - `.note` holds the stage name, hex, L and the stage's existing one-line description
    - `.stamps` holds four `figure` elements for `SPREADS[k][1:]`

Layout, from spec §3, §4 and §7:
- **Desktop.**
  - The panel is right, 38% wide, full height.
  - The numeral is low left, sized `min(520px, 36.1vw)`, and crosses onto the panel.
  - The note is top left. The four frames sit in one row across the left field, below the running head.
- **577 to 992 px.** The numeral is capped so the widest hour covers no more than 85% of the sheet width. The frames go into two rows of two.
- **576 px and below.**
  - The panel goes on top, full width, at 4:5.
  - The numeral overlaps the panel's foot by a quarter of its own height, and the widest hour fills the width inside the 16 px gutters.
  - The note follows below, then the frames in a two-by-two grid.

- [ ] **Step 1: Add the failing checks to `tools/check_b1.py`**
  - Sheet 8's `p.hour` text is "19:12".
  - Sheet 8's `.panel img` src contains "wRU1tGM".
  - Sheet 8 has 4 `.stamps figure` elements.
  - The total number of moodboard `<img>` elements is unchanged from before this task. Record the number in the check.
  - At 1440 px, at a point where `p.hour` crosses `.panel`, the contrast between numeral pixels and the photograph pixels next to them is at least 3:1. Sample from a screenshot, not readPixels.
  - Beside the ember, sheet 8's `p.hour` reaches `--li` above 0.4. Use the mouse loop the everything-reacts check already uses.
  - At 390 px, the `p.hour` right edge is within the sheet minus 16 px.

- [ ] **Step 2: Run them and confirm they fail**

Run: `python3 tools/density_b_family.py && python3 tools/check_b1.py`
Expected: failures for "19:12", "wRU1tGM" and ".stamps".

- [ ] **Step 3: Implement `spread_hour` and route k = 0 to it**

- [ ] **Step 4: Run every check and confirm it passes**

Run: `python3 tools/density_b_family.py && python3 tools/check_b1.py && cd tools && python3 -m pytest -q`
Expected: `PASS`, and every pytest passes. This includes the existing overflow checks at 1440, 768 and 390, and the fonts-blocked check.

- [ ] **Step 5: Show Aaron page 08 at 1440, 768 and 390**

Take headless GPU screenshots of sheet 8 at each width and show them. **Stop here.** Do not start Task 4 until Aaron approves. If he asks for changes, revise this task and show again.

---

### Task 4: Spreads 09 to 11

**Files:**
- Modify: `tools/density_b_family.py`, in `build()` (route k = 1 to 3 to `spread_hour`). Once nothing calls the old `spread()`, delete it.
- Test: `tools/check_b1.py`

- [ ] **Step 1: Extend the checks**
  - Sheets 8 to 11 carry `p.hour` texts equal to `HOURS`.
  - Their panels hold wRU1tGM, tLwiMVf, gE_ypMW and 7BF3FrZ.
  - Each sheet has 4 stamps.
  - The 3:1 crossing check runs on all four sheets.
  - Print media: every `.foot .hr` has a non-zero width.

- [ ] **Step 2: Run them and confirm they fail.** The expected failures are on sheets 9 to 11.

- [ ] **Step 3: Route k = 1 to 3.** If a crossing fails 3:1, change that lead frame's `object-position` and nothing else.

- [ ] **Step 4: Run every check and confirm it passes.** The commands and expected output are the same as Task 3, Step 4.

---

### Task 5: Cover and the four stages

**Files:**
- Modify: `tools/density_b_family.py`, the `cover()` function, plus a new `colour_hours()` that replaces `lead_colour` for sheet 3 in the b1-column branch. Add their CSS to `B_CSS`.
- Test: `tools/check_b1.py`

**Interfaces:**
- Consumes: `HOURS`, and `STAGES`, `OK`, `CMYK` and `CONTRAST` from `density_directions`.
- Produces: a cover with `p.hour` "19:12" and the copy from spec §3. Sheet 3 gets four `.sw` columns weighted 1.6 : 1 : 0.8 : 0.6, each with `p.hour`.

**The cover:**
- The ground is #080808, with ZY6XxOv in a 38% panel on the right. The image is cropped at `object-position` 50% 0% and scale 1.07 from the top.
- The numeral is set at `min(430px, 29.9vw)`.
- The note reads exactly: "One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark."
- The kicker and date stay in the running head.

**Sheet 3:**
- The hours are set at 190, 120, 90 and 64 px at 1440, scaled by vw below.
- Each column then carries its stage name, at 22 px Instrument Serif, and every reading `lead_colour` carries now, in the same order.
- The h2 "The four stages" and its lead stay on the sheet, in the first column above the hour.
- The photograph f3MgZ_1 leaves this sheet. It is an allowed repeat and still appears on sheet 9.
- Below 993 px, the columns become four rows whose heights keep the 1.6 : 1 : 0.8 : 0.6 weighting.

- [ ] **Step 1: Update and extend the checks**
  - Move the everything-reacts photograph probe from `.sheet:nth-child(3) .ph figure` to sheet 2's figure. Record this as a ruling in the ledger: sheet 3 no longer has a photograph.
  - Sheet 1's `p.hour` text is "19:12".
  - Sheet 3 has 4 `.sw`, whose `p.hour` texts equal `HOURS`.
  - Every reading string `lead_colour()` produces is still in sheet 3's text.
  - At 1440 px, the `.sw` widths are in the ratio 1.6 : 1 : 0.8 : 0.6, within 2%.
  - At 768 px, the `.sw` elements stack: their tops are strictly increasing.

- [ ] **Step 2: Run them and confirm they fail.**

- [ ] **Step 3: Implement `cover()` and `colour_hours()`.**

- [ ] **Step 4: Run every check and confirm it passes.** The commands and expected output are the same as Task 3, Step 4.

---

### Task 6: The fall, the type specimen and the art direction line

**Files:**
- Modify: `tools/density_b_family.py`. This covers the `ticks` generation in `build()`, the `COPY` list, and sheet 5's display specimen.
- Test: `tools/check_b1.py`

- [ ] **Step 1: Add the failing checks**
  - Sheet 4's `.ticks` contains, in order, "19:12", "19:40", "20:15", "21:30" and "dark".
  - The 100% magenta tick has no hour.
  - Sheet 5's specimen contains "19:12".
  - Sheet 7 contains "Images are made between 19:12 and 21:30, or lit to look as though they were."
  - The old sentence that line replaces is gone.

- [ ] **Step 2: Run them and confirm they fail.**

- [ ] **Step 3: Implement the changes.**
  - Each tick gains a line under its percentage with the hour, at the reading size.
  - Sheet 5's display specimen sets "19:12" beside "Afterglow". The numerals are not widened.
  - Sheet 7's line goes through `COPY`, replacing "Images are made at the end of the day or lit to look as though they were."

- [ ] **Step 4: Run every check and confirm it passes**, then take headless screenshots of all 15 sheets at 1440 and 390 for Aaron.

---

### Task 7: Blind critics and handover

- [ ] **Step 1: Run blind critics.** Spawn three fresh critics in parallel, one per group: cover with sheet 3, sheets 8 to 11, and sheets 4, 5 and 7. Each gets its sheets at 1440 with labels stripped, beside the pinned Bob Beauté captures in `references/ember/references/2026-10-11-bob-beaute-kurppa-hosk/`. Each says which is better and names the biggest gap.
- [ ] **Step 2: Report to Aaron.** Give him the verdicts, the screenshots and any rulings. Commit only when he says.
