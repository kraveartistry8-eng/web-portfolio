# Afterglow Guide: Specimen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild every sheet of the Afterglow guide as one centred object with a caption and a tag. Every reading moves, word for word, to four reference sheets at the back. The new mark leads the cover and the products.

**Architecture:** A new module, `tools/afterglow_specimen.py`, takes the deck that `density_b_family.build("b1-column")` already produces as its source. It keeps each sheet's opening tag, ground, running head and hour, and replaces only the sheet's body. Content is never retyped, so nothing can drift: what leaves a sheet is moved as markup into the reference sheets. `density_b_family.py`'s main writes b1 through the new module, and b2–b4 are untouched.

**Tech Stack:**
- Python 3, string-built HTML, the existing `density_directions.page` / `foot`
- Playwright on headless Chromium, run with `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`
- The inline EmberEngine bundle, unchanged

**Spec:** `docs/superpowers/specs/2026-10-12-afterglow-guide-specimen-design.md`

## Global Constraints

- **Output:** `brand/2026-10-10-density-b1-column.html`, 19 sheets.
- **Grounds:**
  - Sheets 1–13 keep their slice of the fall, and sheets 14–19 are dark.
  - The magenta sliver ends the last sheet (19).
  - No sheet is lighter than the one before it.
- **Hours:** running-head times equal `sheet_times(19, 13)`. Hours are never changed, reordered or animated.
- **Photographs:**
  - Only the guide's current photographs, each used exactly once in the new deck. 7BF3FrZ, gE_ypMW and f3MgZ_1 each appear once.
  - No board images. No imagery of Black women with short or shaved hair.
- **Nothing deleted:** every text string of the deck at commit 4c88531 appears in the new deck, except the rewrites in `REWRITES` (Task 1).
- **Sheet grammar (sheets 1–15):**
  - one object, centred both ways
  - caption: Instrument Serif 18 px, line height 1.35, at most two lines of at most 34 characters
  - tag: Space Grotesk 11 px capitals, bottom left
  - at most 3 type sizes per sheet, the running head included, with the hours counted as part of the object
- **The mark:** inline copy of `brand/mark/afterglow-mark-light.svg` or `-dark.svg`, never redrawn.
  - At least 48 px wide.
  - #EEECEA on dark grounds, #080808 on gold.
  - Clear space at least the cap's height.
- **Over photographs:** no scrim, shadow or blend.
- **The ember:** no space composed for it, and no change to its behaviour or selectors.
- **No borrowed grammar:** no three-column code / name / count label strip.
- **Process:**
  - Headless GPU only.
  - Commit only when Aaron says.
  - No Shopify change.
- **Approval gate:** Task 2 builds page 08 and STOPS for Aaron's visual approval before Task 3.

## Open question for Aaron (asked at the go-ahead)

The spec keeps every photograph but places no home for **qNdZUES**, the head-as-an-edge photograph now on sheet 05. This plan puts it on reference sheet 17, at 150 × 188, beside the type scale, unless Aaron says otherwise.

## Review Focus

1. **Reference sheets overflowing at 1440.** Moved content may not fit 820 px. Expected: text never shrinks below 11 px; the sheet grows to its natural height, at least 820. Test: `ref_sheets_never_clip` in Task 4.
2. **A string surviving only inside hidden markup.** For example, a moved block inside a `display:none` rule at some width. Expected: every preserved string is visible at 1440 and at 390. Test: `preserved_strings_visible` in Task 4.
3. **The mark at small widths.** At 390 on page 14 the poster mark (40 px) is below the 48 px minimum. Expected: no mark renders below 48 px at any width. Test: `mark_min_width` in Task 6.
4. **Fonts blocked, offline.** The 160 px "19:12" on 05 and the 130 px wordmark on 01 in the fallback face. Expected: no sideways scroll and no clipped glyph. Test: extend the fonts-blocked loop to every sheet, in Task 7.
5. **The strip at 1024.** Five frames plus 4 × 16 px gaps at about 690 px. Expected: one row, no overflow, frames in their spec ratio. Test: `strip_one_row_1024` in Task 3.

---

### Task 1: Scaffold, the mark and the preservation check

**Files:**
- Create: `tools/afterglow_specimen.py`
- Create: `tools/test_afterglow_specimen.py` (a plain-script runner like `tools/test_afterglow_hours.py`)
- Modify: `tools/density_b_family.py`, its `__main__`, so b1 is written from `afterglow_specimen.build()`

**Interfaces:**
- Produces:
  - `mark_svg(width: int, ink: str = "light") -> str`. Reads the brand SVG, sets the width and a height of width × 190/300, and asserts width ≥ 48.
  - `texts(html: str) -> list[str]`. The visible text strings, with scripts and styles stripped, entities unescaped and whitespace collapsed.
  - `lost_strings(old: str, new: str) -> list[str]`. Every string of `texts(old)` not found in the whitespace-collapsed text of `new`, ignoring `REWRITES` keys.
  - `REWRITES: dict[str, str]`, the old → new pairs, exact:
    - "There is no drawn logotype. The wordmark is Instrument Serif, widened to 150%." → "The mark is three triangles: the bottle, the A and the G. The wordmark is Instrument Serif, widened to 150%."
    - "One fragrance in four stages, each an hour of one evening, from 19:12 until it is dark." → "One fragrance in four stages, from 19:12 until it is dark."
  - `sections(html: str) -> list[str]`, `body_of(section: str) -> str` and `with_body(section: str, body: str) -> str`. `with_body` keeps the opening tag and the running head, and replaces everything else.
  - `build() -> tuple[str, int]`: (html, photograph count). In this task it returns the source deck unchanged.
  - `BASE_REF = "4c88531"`: the commit whose deck is the word-for-word source.

- [ ] **Step 1: Write the failing tests.**
  - `test_mark_svg_width`: `'width="120"'` and `'height="76"'` are in `mark_svg(120)`, and `mark_svg(40)` raises AssertionError.
  - `test_mark_svg_ink`: "#080808" is in `mark_svg(60, "dark")`.
  - `test_lost_strings_finds_a_drop`: for an old `<p>a b</p><p>c</p>` and a new `<p>a  b</p>`, the result is `["c"]`.
  - `test_lost_strings_honours_rewrites`: the old logotype line, absent from the new deck, is not reported.
  - `test_build_preserves_everything`: `lost_strings(git show BASE_REF deck, build()[0]) == []`.
- [ ] **Step 2: Run the tests.** Run `python3 tools/test_afterglow_specimen.py`. Expected: FAIL, ModuleNotFoundError afterglow_specimen.
- [ ] **Step 3: Implement the Interfaces above** in `tools/afterglow_specimen.py`, and route b1 in `density_b_family.__main__` through `build()`.
- [ ] **Step 4: Run the tests again.** Run `python3 tools/test_afterglow_specimen.py && python3 tools/density_b_family.py && python3 tools/check_b1.py`. Expected: 5/5 PASS, and check_b1 PASS, because the deck is unchanged.
- [ ] **Step 5: Ledger.** No commit: Aaron commits.

### Task 2: Page 08, the five-photograph strip (approval gate)

**Files:**
- Modify: `tools/afterglow_specimen.py`
- Modify: `tools/check_b1.py`. Replace the hpanel, stamps and crossing-contrast asserts for sheet 8 with the strip asserts below. Their equivalents for 9–11 come in Task 3.
- Test: `tools/test_afterglow_specimen.py`

**Interfaces:**
- Consumes: `with_body`, `sections` and `REF_HOLD` (below).
- Produces:
  - `STAMPS: dict[int, tuple[str, str, str, str]]`, with the spec's values:
    - 0: ("19:18", "19:24", "19:31", "19:37")
    - 1: ("19:46", "19:53", "20:01", "20:09")
    - 2: ("20:24", "20:35", "20:48", "21:02")
    - 3: ("21:38", "21:45", "21:53", "22:00")
  - `colour_page(k: int, section: str) -> str`. The new sheet: a `.strip` of five `figure`s, then the hour at 56 px, the stage's one line, and the tag "<hex> · five frames, warm to cool".
    - The photographs, their order and their crops come from the source sheet.
    - The lead frame is 300 × 375. The four others are 150 × 188, aligned on their feet with 16 px gaps, each with its minute stamp.
  - `REF_HOLD: list[str]`. Markup removed from sheets, in sheet order, waiting for the reference sheets (Task 4). Each task appends to it.
  - Shared CSS: `SPEC_CSS`. Holds `.obj` (centred both ways), `.cap` and `.tag`.

- [ ] **Step 1: Write the failing tests.**
  - `test_colour_page_08`:
    - sheet 8 holds the five original srcs in order, wRU1tGM first
    - its 4 stamps read `STAMPS[0]`
    - its hour reads "19:12"
    - it contains a `.cap` with the stage line
  - `test_build_preserves_everything` (Task 1) stays green, because anything removed from 08 is held in `REF_HOLD` and emitted.
  - Until Task 4 exists, `REF_HOLD` is emitted as a temporary visible block at the end of the last sheet. It is never hidden, so the preservation test stays honest.
- [ ] **Step 2: Run the tests.** Run `python3 tools/test_afterglow_specimen.py`. Expected: FAIL in test_colour_page_08.
- [ ] **Step 3: Implement `colour_page` and `SPEC_CSS`,** and apply them to sheet 8 only.
- [ ] **Step 4: Run the tests and check sheet 8 in the browser.** Run the tests, build, then `python3 tools/check_b1.py`. Expected:
  - all tests PASS
  - check_b1 has no sheet-8 failures, with sheet 8 at 820 px, no overflow, and 0 hscroll at 1440, 768 and 390
- [ ] **Step 5: Screenshot sheet 8** at 1440, 768 and 390, headless, into the storyboard folder, as `page08-specimen.png`.
- [ ] **Step 6: STOP for Aaron's visual approval.** Show the screenshot and the served page. Ask no blind critic yet: Aaron's eye gates first, and critics come in Task 8.

### Task 3: Pages 09–11 and 07

**Files:** `tools/afterglow_specimen.py`, `tools/check_b1.py` and the test file.

**Interfaces:**
- Consumes: `colour_page` and `STAMPS`.
- Produces: `art_direction(section: str) -> str`. The same strip: OOqXr-G as the lead, then USalI5W, fMmCZqp and e4jFDHF, captioned "L 0.378", "L 0.342" and "L 0.205". The caption is "One light source, and it is falling."

- [ ] **Step 1: Write the failing tests.**
  - `test_colour_pages`: for k 1–3, sheet 8+k holds its five srcs in order with leads tLwiMVf, gE_ypMW and 7BF3FrZ, its stamps read `STAMPS[k]`, and its hour reads `HOURS[k]`.
  - `test_art_direction`: four srcs in order, and the three L captions.
  - check_b1 `strip_one_row_1024`: at 1024 the five figures of sheets 7–11 share one top-aligned foot line, and no sheet overflows.
  - check_b1, 768: the lead is on its own row at 260 wide, and four at 140 sit beneath it.
  - check_b1, 390: the lead is full width less 32 px at 4:5, and the others sit 2 × 2.
- [ ] **Step 2: Run the tests.** Expected: FAIL in test_colour_pages.
- [ ] **Step 3: Apply** `colour_page` to sheets 9–11, and `art_direction` to sheet 7.
- [ ] **Step 4: Run the tests, build and check_b1.** Expected: PASS for sheets 7–11 at 1440, 1024, 768 and 390.
- [ ] **Step 5: Ledger.**

### Task 4: The reference sheets, 16–19

**Files:** `tools/afterglow_specimen.py`, `tools/check_b1.py` and the test file.

**Interfaces:**
- Consumes: `REF_HOLD`, `mark_svg` and `sheet_times`.
- Produces: `reference(n: int, title: str, lead: str, held: list[str]) -> str`, for n 16–19.
  - The ground is #080808. The running head comes from `density_directions.foot`.
  - The lead element is first, then `held` in columns: 4 at 1440, 2 at 768 and 1 at 390.
  - Hairlines only, no boxes. Text is Space Grotesk 11 px, line height 1.6, with Instrument Serif 16–20 px heads.
- Routing: every `REF_HOLD` entry carries its destination (16, 17, 18 or 19), per the spec §4. Entries are appended as `(dest, markup)` from now on; Task 2's entries get a destination now.
- The leads:
  - 16: the fall band with its hours and stops.
  - 17: "Deepening" as a descending type-scale column, with qNdZUES at 150 × 188 beside it (the open question).
  - 18: the four art-direction rules as one numbered list in Instrument Serif 22 px.
  - 19: the mark's construction drawing, showing the gap, the cap and the serif measures.
- The magenta sliver moves from sheet 15's ground to sheet 19's.

- [ ] **Step 1: Write the failing tests.**
  - `test_nineteen_sheets`: there are 19 sections, and the running-head times equal `sheet_times(19)`.
  - `test_reference_order`: sheets 16–19 have the heads "Colour", "Type and layout", "Imagery" and "Wordmark, mark, products and voice".
  - check_b1 `ref_sheets_never_clip`: at 1440, sheets 16–19 have no overflow, their height is at least 820, and every text node in them is at least 11 px.
  - check_b1 `preserved_strings_visible`: at 1440 and 390, each preserved string lies in a rendered element with width and height above 0.
  - check_b1: the last sheet's ground ends on #BF15B7, and sheet 15's ground does not contain it.
- [ ] **Step 2: Run the tests.** Expected: FAIL, because there are 15 sections.
- [ ] **Step 3: Implement `reference` and the routing,** and append the four sheets.
- [ ] **Step 4: Run the tests and check_b1.** Expected: PASS, and `test_build_preserves_everything` PASS.
- [ ] **Step 5: Ledger.**

### Task 5: Sheets 01–06

**Files:** `tools/afterglow_specimen.py`, `tools/check_b1.py` and the test file.

**Interfaces:**
- Consumes: `with_body`, `mark_svg`, `REF_HOLD` and `SPEC_CSS`.
- Produces: one function per sheet, each `(section: str) -> str`. Each moves what leaves its sheet into `REF_HOLD` with a destination.
  - `cover_sheet`:
    - the mark at 260 px, stacked on one axis with the wordmark at 130 px, widened 150%
    - caption "One fragrance in four stages, from 19:12 until it is dark."
    - no photograph
    - ground #080808, and `bcover` kept
  - `wordmark_sheet`:
    - ZY6XxOv at 300 × 375, with the wordmark at 64 px beneath it
    - caption from `REWRITES`
    - 7BF3FrZ removed
  - `stages_sheet`: four 120 × 150 swatches, each with its hour at 44 px and its name; tag "Four hours of one evening".
  - `fall_sheet`:
    - the band at 960 × 120, with the hours at 28 px beneath it
    - caption "Gold to violet, never reversed."
    - gE_ypMW removed
  - `type_sheet`:
    - "19:12" in Instrument Serif at 160 px, then "The light only ever deepens." in Space Grotesk at 22 px
    - tag "Instrument Serif · Space Grotesk"
    - qNdZUES routed to 17
  - `rule_sheet`:
    - "The light only brightens where the ember is." in Instrument Serif at 56 px, at most 22 characters to the line
    - Eje8BSd at 240 × 300 beside it on the axis
    - tag "Twelve columns · eight spacing steps"

- [ ] **Step 1: Write the failing tests.**
  - `test_sheets_01_06`:
    - each sheet's object and caption text match the spec values above
    - the cover holds an `<svg` and no `<img`
    - sheet 2 holds ZY6XxOv and not 7BF3FrZ
  - `test_photographs_once`: every moodboard src appears exactly once. The count is 31: 33, less the two old repeats, with qNdZUES kept.
  - check_b1 `grammar`: on sheets 1–15 at 1440, there are at most 3 distinct computed font sizes outside `.obj`, the object counting as one, and every `.cap` is at most two lines.
  - Retire the old cover-note, sheet-3 column-ratio and tick asserts. The tick hours move to sheet 16, and the readings check now targets sheet 16.
- [ ] **Step 2: Run the tests.** Expected: FAIL in test_sheets_01_06.
- [ ] **Step 3: Implement the six functions** and wire them in.
- [ ] **Step 4: Run the tests and check_b1.** Expected: PASS at 1440, 1024, 768 and 390.
- [ ] **Step 5: Ledger.**

### Task 6: Sheets 12–15

**Files:** `tools/afterglow_specimen.py`, `tools/check_b1.py` and the test file.

**Interfaces:**
- Produces: `ember_sheet`, `misuse_sheet`, `apps_sheet` and `voice_sheet`, each `(section) -> str`.
  - `ember_sheet`: R6euaYP at 300 × 375, with the caption "Move, and it lights. Stop, and in 0.7 seconds it goes out."
  - `misuse_sheet`: 3ASXlcU-trim at 300 × 375 with its "Don't" tag, and the caption "A frame rejected from the set: cold, lit from everywhere, and nothing in it falls."
  - `apps_sheet`:
    - the label at 280 × 420: the mark at 150 px and the wordmark at 26 px at the top, and one centred line at its foot, "19:12 — Eau de parfum, 50 ml"
    - the poster (bNQYoLz, mark at 40 px, clamped to 48 px) and the card (mark at 56 px), at about half the label's size
    - tag "The label leads · card and poster follow"
  - `voice_sheet`: PNTk-Dh-bottle at 300 × 375, with the caption "Unhurried and physical. It names heat, light, breath and skin."
- Ruling carried: the spec's "mark at 40 px" on the poster conflicts with its own 48 px minimum. The minimum wins, so the poster mark is 48 px.

- [ ] **Step 1: Write the failing tests.**
  - `test_sheets_12_15`: the captions and srcs above.
  - The label line is one element, not three spans.
  - check_b1: the old sheet-12 WANT strings are still in the deck, now on 17 or 19.
  - check_b1 `mark_min_width`: every `svg` from the mark is at least 48 px wide at 1440, 768 and 390.
  - check_b1: on page 14 at 390 the label sits above the poster and card, which share a row.
- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Implement the four functions** and wire them in.
- [ ] **Step 4: Run the tests and check_b1.** Expected: PASS.
- [ ] **Step 5: Ledger.**

### Task 7: The whole deck, every width

**Files:** `tools/check_b1.py` and `tools/afterglow_specimen.py`.

- [ ] **Step 1: Extend the browser checks.**
  - Widths are 1440, 1024, 768 and 390.
  - Sheets 1–15 are 820 high at 1440, with no overflow anywhere and 0 hscroll.
  - Running-head offsets are equal at 1440.
  - Fonts blocked: no overflow on any sheet at 1440 and 390, not just the hour sheets.
  - The ember block stays as is:
    - one canvas
    - ember-on
    - grounds go transparent
    - at least 400 lit elements
    - under 4 ms per frame
    - print and context-loss checks
  - "Everything reacts" now targets sheet 2's figure, sheet 3's `.sw`, a reference `dd`, and sheet 8's hour.
- [ ] **Step 2: Run it.** Expected: any failure lists the sheet and the width.
- [ ] **Step 3: Fix each failure at its cause.** Never loosen a threshold without a ledgered ruling.
- [ ] **Step 4: Run the full suite:** the tests, the build, then check_b1. Expected: all PASS.
- [ ] **Step 5: Ledger.**

### Task 8: Blind critique and final review

- [ ] **Step 1: Critique against Bob Beauté.** Screenshot sheets 1, 3, 8, 14 and 17 at 1440. Hand them to a fresh critic with the labels stripped, alongside the pinned Bob Beauté set. Binary question: which is better, and what is the single biggest gap?
- [ ] **Step 2: Critique against Journ by Landscape,** the same way, with a separate fresh critic.
- [ ] **Step 3: Report both verdicts to Aaron verbatim.** Act on them only with his say.
- [ ] **Step 4: Final whole-branch review** by a fresh reviewer on the most capable model. Then one fix pass for Critical and Important findings. Minor findings go to the ledger.
