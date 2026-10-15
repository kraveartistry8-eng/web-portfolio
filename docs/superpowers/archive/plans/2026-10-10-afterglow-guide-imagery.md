# Afterglow Guide Imagery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the guide's single prose art-direction sheet with six sheets that argue the
imaging rules from the mood board, each stage sheet carrying six references in a 3 × 2 grid.

**Architecture:** Two new build-time scripts compute what is currently judged by eye — which
reference belongs to which stage, and which poster frame stands in for each video — and write
the result to a reviewable JSON manifest. `build_guide.py` reads that manifest and emits the six
sheets through a new full-width sheet builder alongside the existing two-column one. The grid is
CSS only; print determinism comes from swapping each video for its poster image at print media,
not from the video element.

**Tech Stack:** Python 3 (stdlib only), ffmpeg (already present, used by the mood board build),
Playwright/Chromium for audit and PDF, CSS Grid. No new pip or npm dependencies.

**Spec:** `docs/superpowers/specs/2026-10-10-afterglow-guide-imagery-spec.md`

## Global Constraints

- Brightness ceiling: a reference's **upper-quartile** OKLCH lightness must be at or below
  **L 0.781** (gold of last light). Measured from a 16×16 downsample, the same statistic the
  stage assignment uses. Specular highlights are permitted; a bright body is not.
- Slot ratio is **5:4 landscape (1.25)**, fixed at every breakpoint and in the PDF.
- Grid gutter is **8px**, the `--sp-xs` token, on both axes.
- The field between the one-line rule and the top of the grid is **14% of sheet height**,
  identical on all four stage sheets.
- Each stage sheet carries exactly **6** references; 24 of the 49 reach the guide.
- Radius 0, shadow none, no white or light panel behind any image.
- No hover-dependent content. No `100vh`. Breakpoints at 600px and the guide's existing 900px.
- Every value still renders from `brand/resources/design-tokens.json`; no hand-edited HTML.
- Sheet count moves 15 → 20, so `N` in `tools/build_guide.py` moves with the sheet list.

## Review Focus

1. **A stage has fewer than six eligible references** once the L 0.781 filter runs. Expected: the
   build fails loudly naming the stage and the count, not a sheet with four frames. (Task 2)
2. **A manifest entry points at a missing or unreadable file.** Expected: the build fails naming
   the file, rather than emitting a broken image element into the guide. (Task 4)
3. **Two stages are equidistant from one reference's lightness.** Expected: assignment is
   deterministic across runs — same input, same manifest, byte for byte. (Task 2)
4. **A video shorter than its poster offset, or a single-frame file.** Expected: a poster is still
   extracted, from the last available frame, rather than ffmpeg writing a zero-byte file. (Task 1)
5. **The grid overflows the 8.05in print sheet** at a stage whose name wraps to two lines.
   Expected: the sheet still fits one page and `pdf_sheets` stays green. Measured 10 Oct 2026:
   the stage sheet clears by about 11.9px, so `footer_in_page` is what holds this. (Task 5)

A sixth, pinned because the whole document rests on it: **the guide must not state a rule its own
exemplars break.** The reworded brightness rule and the manifest are generated from one
measurement, and Task 4 Step 5 asserts the old wording is gone. (Task 2, Task 4)

---

### Task 1: Poster frames for the video references

**Files:**
- Create: `tools/make_posters.py`
- Create: `brand/moodboard-media/posters/` (output, one `.jpg` per `.mp4`)
- Test: `tools/test_guide_audit.py`

**Interfaces:**
- Produces: `make_posters.main() -> dict[str, str]` mapping each video filename to its poster
  filename, and writing the poster files. Poster offset is one third of clip duration, the
  offset the mood board already uses.

- [ ] **Step 1: Write the failing test**

```python
def test_poster_offset_is_one_third():
    assert make_posters.offset(9.0) == 3.0

def test_short_clip_still_yields_a_frame():
    # a clip shorter than one frame at the computed offset falls back to the last frame
    assert make_posters.offset(0.04) >= 0.0

def test_every_video_reference_has_a_nonempty_poster():
    posters = make_posters.main()
    assert len(posters) == 13
    for v, p in posters.items():
        assert (MEDIA / "posters" / p).stat().st_size > 0
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python3 tools/test_guide_audit.py`
Expected: FAIL, `make_posters` not importable.

- [ ] **Step 3: Implement `offset(duration: float) -> float` and `main() -> dict` in `tools/make_posters.py`**

Probe duration with `ffprobe`, extract with `ffmpeg` at the offset, clamping the offset into the
clip so a short file yields its last frame rather than nothing. Write JPEGs at the longest edge
the print slot needs (3.28in at 300dpi ≈ 984px) — larger is wasted weight in the PDF.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `python3 tools/test_guide_audit.py`
Expected: PASS, 13 posters written.

- [ ] **Step 5: Commit**

```bash
git add tools/make_posters.py tools/test_guide_audit.py brand/moodboard-media/posters
git commit -m "feat: extract deterministic poster frames for the video references"
```

---

### Task 2: Measure every reference and assign it to a stage

**Files:**
- Create: `tools/assign_references.py`
- Create: `brand/resources/imagery-manifest.json`
- Test: `tools/test_guide_audit.py`

**Interfaces:**
- Consumes: the poster map from Task 1, for measuring videos on their poster frame rather than
  an arbitrary frame.
- Produces: `assign_references.measure(path) -> dict` with keys `l_p75`, `aspect`, `kind`
  (`"image"` or `"video"`); `assign_references.main() -> None`, writing the manifest. Manifest
  shape: `{"stages": {"1": [{"file", "kind", "poster", "l_p75", "aspect"}, … 6 entries], …}}`,
  stage keys `"1"` through `"4"` matching the token file's stage keys.

- [ ] **Step 1: Write the failing test**

```python
def test_upper_quartile_matches_the_known_measurement():
    m = assign_references.measure(MEDIA / "mPNk84g.mp4")
    assert abs(m["l_p75"] - 0.825) < 0.01

def test_every_assigned_reference_clears_the_ceiling():
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    for stage, refs in man["stages"].items():
        assert len(refs) == 6, "stage %s has %d" % (stage, len(refs))
        for r in refs:
            assert r["l_p75"] <= 0.781

def test_assignment_is_deterministic():
    before = (ROOT / "brand/resources/imagery-manifest.json").read_text()
    assign_references.main()
    assert (ROOT / "brand/resources/imagery-manifest.json").read_text() == before

def test_a_starved_stage_fails_the_build():
    with pytest.raises(SystemExit):
        assign_references.pick(eligible=[], stage_l=0.3, want=6)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python3 tools/test_guide_audit.py`
Expected: FAIL, `assign_references` not importable.

- [ ] **Step 3: Implement `measure`, `pick(eligible, stage_l, want) -> list`, and `main` in `tools/assign_references.py`**

Reuse the OKLCH conversion already in `tools/brand_audit.py` rather than writing a second one —
`build_guide.py` and `guide_audit.py` both import it the same way. Downsample to 16×16 through
ffmpeg, take the 75th percentile of lightness. Filter to references at or below L 0.781, then
give each stage the `want` nearest its own lightness, each reference used once. Break ties on
filename so repeated runs agree. Exit with a message naming the stage and the count when a stage
cannot be filled. Sort manifest keys and round floats to 4 places so the file is diffable.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `python3 tools/test_guide_audit.py`
Expected: PASS, four stages of six.

- [ ] **Step 5: Commit**

```bash
git add tools/assign_references.py brand/resources/imagery-manifest.json tools/test_guide_audit.py
git commit -m "feat: assign mood board references to stages by measured lightness"
```

---

### Task 3: The grid, in the template

**Files:**
- Modify: `tools/guide_template.html:160-162` (replace the `.imgs` placeholder rules),
  `tools/guide_template.html:199-213` (the 900px block), `tools/guide_template.html:221-226`
  (the print block)

**Interfaces:**
- Produces: the class names Task 4 emits — `.stagehead`, `.stagename`, `.stageread`, `.stagerule`,
  `.imgs` (the grid), `.imgs > figure`, and the print/screen swap pair `.scr` / `.prt`.

- [ ] **Step 1: Add the grid rules**

Three equal columns and two rows above 900px, two columns between 600px and 900px, one column
below 600px — written mobile-first, so one column is the base and the others are `min-width`
enhancements. Every slot holds the 5:4 ratio at all three. Gutter is the `--sp-xs` token on both
axes. The field above the grid is 14% of sheet height and is set once, not per sheet.

- [ ] **Step 2: Add the print swap**

At print media the video element is hidden and its poster image shown; on screen the reverse.
This is the whole reason print is deterministic — Chromium prints a video as whatever frame is
showing, which varies run to run. Verified 10 October 2026; see the spec.

Under `prefers-reduced-motion: reduce` the same swap runs on screen, so a reduced-motion reader
and a printed sheet see the same picture rather than two different frames of the same clip.

- [ ] **Step 3: Verify the ratio holds at every width**

Run: `python3 tools/guide_audit.py`
Expected: `no_h_scroll` still PASS at 1440, 1024, 900, 390 and 320.

- [ ] **Step 4: Commit**

```bash
git add tools/guide_template.html
git commit -m "feat: 3x2 reference grid with a deterministic print swap"
```

---

### Task 4: The six sheets

**Files:**
- Modify: `tools/build_guide.py:40` (`N`), `tools/build_guide.py:339-357` (replace `s_imagery`),
  `tools/build_guide.py:440-487` (the sheet list)

**Interfaces:**
- Consumes: the manifest from Task 2; the class names from Task 3.
- Produces: `stage_sheet(i, stage_key, body) -> str`, a full-width sheet with no `.col-l` /
  `.col-r` split, carrying `data-sheet` and its slice of the fall exactly as `sheet()` does;
  `s_imagery_opener() -> str`; `s_imagery_misuse() -> str`.

- [ ] **Step 1: Write the failing test**

```python
def test_twenty_sheets_and_the_fall_still_divides():
    html = build_guide.build()
    assert html.count('class="sheet') == 20
    assert build_guide.N == 20

def test_each_stage_sheet_carries_six_figures():
    html = build_guide.build()
    for stage in ("1", "2", "3", "4"):
        assert html.count('data-stage="%s"' % stage) == 6

def test_a_missing_reference_file_fails_the_build():
    with pytest.raises(SystemExit):
        build_guide.figure({"file": "nope.jpg", "kind": "image"})
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python3 tools/test_guide_audit.py`
Expected: FAIL, 15 sheets against 20.

- [ ] **Step 3: Implement `stage_sheet`, `figure`, `s_imagery_opener` and `s_imagery_misuse`**

`figure(ref) -> str` emits one grid slot: an image, or a video plus its poster image in the
swap pair, carrying `data-stage`. It exits naming the file when the file is not on disk. The
stage sheet sets the stage name at the `--x3` display step with the swatch, hex and lightness
right-aligned on its baseline and the one-line rule beneath, then the grid. The opener carries
the five rules at the largest display step the sheet allows, no images, and keeps them in a void
panel so `readings_on_void` stays green. Misuse follows the existing `.donts` pattern: a tile, a
pill label, a one-line caption naming the rule broken.

- [ ] **Step 4: Reword the brightness rule and reshape the back half**

Three edits to existing sheet bodies, all in `build_guide.py`:

- The imagery opener's second rule changes from "The brightest value in an image sits at or below
  the gold of last light" to "**The upper quartile of an image's lightness sits at or below the
  gold of last light**", with the L value still interpolated from the token. This is the decision
  recorded in the spec; the old wording is contradicted by eleven of the twelve references the
  guide is about to print.
- `s_digital` gains one reference beside the product card, from the manifest, showing the imagery
  those components sit with.
- `s_print` gains the one constraint photography introduces, stated as a checkable number rather
  than a sentence about mood: no placed image's upper quartile above gold.

- [ ] **Step 5: Write the failing test for the reworded rule**

```python
def test_the_brightness_rule_names_the_upper_quartile():
    html = build_guide.build()
    assert "upper quartile" in html.lower()
    assert "brightest value in an image" not in html.lower()
```

- [ ] **Step 6: Run the test and confirm it passes**

Run: `python3 tools/test_guide_audit.py && python3 tools/build_guide.py`
Expected: PASS, 20 sheets written.

- [ ] **Step 7: Commit**

```bash
git add tools/build_guide.py brand/2026-10-09-afterglow-brand-guide.html tools/test_guide_audit.py
git commit -m "feat: six imagery sheets, the mood board as the guide's evidence"
```

---

### Task 5: Six audit checks, each of which can fail

**Files:**
- Modify: `tools/guide_audit.py:205-318` (`extra_checks`)
- Test: `tools/test_guide_audit.py`

**Interfaces:**
- Consumes: the manifest from Task 2, the rendered document from Task 4.
- Produces: five named checks on the existing `chk(cond, msg)` convention —
  `image_never_brightens`, `image_on_ground`, `poster_in_print`, `caption_contrast`,
  `grid_ratio_holds`, `footer_in_page`.

- [ ] **Step 1: Write the failing test, one mutation per check**

Each case mutates the document so exactly one check should bite, following the pattern in
`tools/test_brand_audit.py`: a check that cannot fail manufactures confidence.

```python
CASES = [
    ("image_never_brightens", 'swap one reference for one measured above L 0.781'),
    ("image_on_ground",       'push one figure to the sheet edge'),
    ("poster_in_print",       'remove one poster image from the swap pair'),
    ("caption_contrast",      'set one reading to the ground colour it sits on'),
    ("grid_ratio_holds",      'change one slot from 5:4 to 4:3'),
    ("footer_in_page",        'make one stage name wrap to two lines'),
]

def test_each_new_check_bites():
    for name, mutation in CASES:
        out = run_audit_on(mutated_copy(mutation))
        assert "FAIL  %s" % name in out, "%s did not bite" % name
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python3 tools/test_guide_audit.py`
Expected: FAIL, none of the six checks exist.

- [ ] **Step 3: Implement the six checks in `extra_checks`**

`grid_ratio_holds` measures every slot at 1440, 900, 700 and 390 and in the PDF, asserts 1.25
within 1%, and asserts the field above the grid is equal across the four stage sheets.
`image_on_ground` asserts no figure's bounding box touches a page edge. `poster_in_print`
asserts every video has a poster sibling and that it is what print media shows.
`caption_contrast` extends the existing `text_on_fall` reasoning to the new readings.
`image_never_brightens` reads the manifest rather than re-measuring, so the build and the audit
cannot disagree about what was measured. `footer_in_page` asserts every sheet's footer is wholly
inside its page in the PDF: the stage sheets clear the 8.05in sheet by only about 11.9px, and
`.sheet` carries `overflow:hidden` in print, so a stage name that wraps to two lines would be
clipped silently rather than reported. This check is what makes that thin margin safe, and it
is Review Focus item 5's real protection.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `python3 tools/test_guide_audit.py`
Expected: PASS, six checks each bitten by its own mutation.

- [ ] **Step 5: Commit**

```bash
git add tools/guide_audit.py tools/test_guide_audit.py
git commit -m "feat: six audit checks for the imagery section, each proven to bite"
```

---

### Task 6: Render, and the whole document green

**Files:**
- Modify: `brand/2026-10-09-afterglow-brand-guide.pdf` (regenerated)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Render the PDF**

Run: `python3 tools/render.py brand/2026-10-09-afterglow-brand-guide.html`
Expected: `console errors: none`, 20 pages.

- [ ] **Step 2: Run the full audit**

Run: `python3 tools/guide_audit.py`
Expected: 19 pass, 0 fail. `pdf_sheets` was already failing as stale before this work and clears
here. `fall_joins` and `ink_measured` recompute against N = 20 — if a sheet's ink flips from dark
to light, that is the build measuring correctly, not a regression, but confirm each flipped sheet
still clears its contrast floor.

- [ ] **Step 3: Confirm the PDF weight is sane**

Run: `ls -lh brand/2026-10-09-afterglow-brand-guide.pdf`
Expected: well under 25MB. The guide was 272K with no images; 24 references at print resolution
is the whole increase. If it is larger, the posters and JPEGs are oversized for a 3.28in slot.

- [ ] **Step 4: Commit**

```bash
git add brand/2026-10-09-afterglow-brand-guide.pdf brand/2026-10-09-afterglow-brand-guide.html
git commit -m "feat: render the guide with its imagery section"
```
