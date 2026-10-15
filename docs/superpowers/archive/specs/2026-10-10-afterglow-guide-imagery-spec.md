# Afterglow brand guide — imagery section and back half

Spec, 10 October 2026. Direction C1 → C1a → **crop option 3, two rows of three**, picked by
Aaron from `brand/2026-10-10-guide-imagery-c-family.html`,
`brand/2026-10-10-guide-imagery-c1-fix.html` and
`brand/2026-10-10-guide-imagery-c1a-crop.html` in that order.
Scope: B and C — a new imagery section, and the back half of the guide reshaped to argue from
the mood board rather than assert in prose.

---

## Overview

The brand guide contains zero images across fifteen sheets. Sheet 11, *Art direction*, states
five imaging rules entirely in prose. The 49-reference mood board at
`brand/2026-10-09-afterglow-moodboard.html` is now the evidence for exactly those rules.

This feature introduces photography to the document for the first time, as a section of stage
sheets: each sheet's ground is one stage of the fall, and it carries only the references that
live at that value. The images sit on the colour they describe, so the claim that the palette
is a description of light is made by the page rather than by a caption.

---

## Structure

Six new sheets replacing the single prose sheet 11.

| Sheet | Ground | What it carries |
|---|---|---|
| Imagery opener | the fall at that position | The five rules, set at display size. No images |
| Gold of last light | `#D8B260` slice | 6 references, 3 × 2 grid |
| After gold | `#BC6F4C` slice | 6 references |
| Rose | `#893A50` slice | 6 references |
| Deep violet | `#341D5E` slice | 6 references |
| Misuse | the fall at that position | 6 cut references, each labelled with the rule it breaks |

The guide goes from 15 sheets to 20. `tools/build_guide.py` asserts the sheet count equals the
number of slices of the fall, so `N` moves with the list and every existing sheet's ground
shifts position on the ramp. That is intended — the fall is divided by the document, not fixed
to the old count — but it means every sheet re-renders and every contrast reading is recomputed.

### Which reference goes on which sheet

Computed, not chosen. Each reference's upper-quartile OKLCH lightness is measured from a 16×16
downsample, and it is assigned to the stage whose lightness is nearest. The script lives in
`brand/moodboard-source/` alongside `measure-chroma.py`.

A pure nearest-value rule is unbalanced: it yields 7 / 10 / 11 / 21 across the four stages.
**Resolution: each sheet takes the 6 references nearest its value and no more.** 24 of the 49
appear in the guide. The mood board remains the complete set and the guide cites it by name.
A guide is not a catalogue, and six frames is enough to set a standard.

---

## Sheet anatomy, stage sheet

Top to bottom, and nothing else on the sheet:

1. **Stage name** at the display step, flush left, set large enough to be the sheet's largest
   element by a stated margin — see *Proportion* below. This is the C1a change: the name is a
   title, not a label in a header row.
2. **Swatch, hex and lightness**, right-aligned on the name's baseline, at the monospace `--xs`.
3. **One-line rule**, directly under the name, at `--xs`.
4. **The grid**: six references, three across and two down.
5. **The existing footer**, unchanged.

### Proportion

C1a was argued on the grounds that a display-size name gives the sheet "a dominant first stop"
so "the eye lands top-left, then falls to the grid." That rationale does not survive checking —
the scanning-order claim behind it is a text-page finding (the F-pattern) applied to a sheet
that is mostly photograph, and it is not evidence for this layout. The layout is still right;
the reason is replaced with one that can be verified in a render rather than asserted:

- The stage name is the largest element on the sheet, at no less than **3×** the cap height of
  any other text on it.
- It is the **only** text above the grid apart from its own swatch reading and the one-line rule.
- The field between the rule and the top of the grid is a **stated** proportion, identical on
  all four stage sheets, not whatever is left over. Target **14% of sheet height**, which is what
  the 5:4 grid leaves at print size.

That third rule is the one that matters. Six equal tiles with an unresolved gap above them is
the failure C1a was raised against, and consistency across the four sheets is what separates
deliberate space from a layout that ran out of content.

---

## The grid

Three columns, two rows, in document order left to right then down.

| Property | Value |
|---|---|
| Columns | 3, equal |
| Rows | 2, equal |
| Gutter | 8px, the `--sp-xs` base unit, both axes |
| Slot ratio | **5:4 landscape (1.25)** |
| Column width at print | 3.278in, from a 10.0in content width |
| Slot height at print | 2.622in |
| Grid block at print | 5.328in |
| Frames | flush to the grid, not inset. Radius 0, shadow none |

The slot ratio is the fixed quantity and the grid height follows from it, so screen and print
crop the same frames the same way. The alternative — fixing the grid height and letting the
ratio float — crops differently at every viewport, which makes the art direction unreviewable.

### Why three across and not six

Measured from the files, not estimated. Crop is the share of source area lost to `cover` fill,
averaged over the twelve references on the two sheets that were mocked up:

| Layout | Slot ratio | Mean crop | Worst frame | References kept |
|---|---|---|---|---|
| 6 across, one row | 0.293 | **66.5%** | 84.6% | 6 |
| 4 across, one row | 0.489 | 40.4% | 74.2% | 4 |
| **3 across, two rows** | **1.25** | **36.0%** | **47.2%** | **6** |
| Justified, no crop | native | 0% | 0% | 6 |

Three across wins on every axis that was in contention: it roughly halves the crop against the
six-across strip, beats the four-across option on crop *and* keeps two more references per
stage, and it is the only option that fills the sheet without the grid growing taller.

The justified row was the fourth option and is not viable. Option 1 on the crop sheet is
misrendered — it claims zero crop and delivers 58%, because the row is told to fill both the
content width and a fixed height, and it cannot do both while holding twelve different native
aspects. Rendered honestly, zero crop forces the band to **1.30in of an 8.05in sheet**: a thin
strip under a large dead field, which is the exact composition C1a was raised to remove. The
trade is real and it is not worth taking.

Source aspects run 0.66 to 1.90, mostly portrait with three landscape. A 5:4 landscape slot
therefore crops the portraits top and bottom and the landscapes left and right, which is the
normal cost of a grid and is now a known quantity rather than a surprise.

---

## The back half, reshaped

- **Art direction opener** keeps the five rules but stops explaining them, because the four
  stage sheets that follow are the explanation.
- **Digital** currently shows a product card, a button and the surface steps as CSS specimens.
  It gains one reference beside the card showing the imagery those components sit with.
- **Print and production** gains the one measured constraint photography introduces: the
  brightest value in any placed image must sit at or below gold at L 0.781, and that is now
  checkable rather than stated.
- **Misuse** is new to the imagery half. It follows the Frame.io pattern already pinned in
  `references/design-standards.md`: each wrong example is a tile carrying a small pill label and
  a one-line caption naming the rule it breaks.

---

## States

This is a document, not an interaction. It has four render targets, and all four are tested.

| State | Trigger | Behaviour |
|---|---|---|
| Screen, wide | viewport above 900px | 3 × 2 grid, 5:4 slots |
| Screen, medium | 600px to 900px | 2 × 3 grid, 5:4 slots, document order preserved |
| Screen, narrow | below 600px | 1 column, 5:4 slots, document order preserved |
| Print and PDF | print emulation and the rendered PDF | 3 × 2 grid. Video references resolve to a poster frame |

## Motion

The guide has no motion and gains none. The only moving elements are the 13 video references.
On screen they play muted and looped with no controls, and they honour `prefers-reduced-motion`
by holding on the poster frame — the same frame print uses, so a reduced-motion screen and a
printed sheet show the same picture. In print and PDF they resolve to that single poster frame,
extracted at one third of the clip duration. That offset is a choice, not an inherited
convention — the mood board build has no poster step — and it is pinned so the printed frame is
reproducible rather than whichever frame happened to be on screen.

## Colour and visual detail

- **The four stage sheets carry their own stage colour as a flat field**, taken from the token
  file: gold `#D8B260`, after gold `#BC6F4C`, rose `#893A50`, deep violet `#341D5E`. This is the
  one place the deck departs from "every sheet takes its positional slice", and it departs
  deliberately: a stage sheet is the only kind of sheet that is *about* a named stage, and the
  section's whole claim is that the images sit on the colour they describe. A "Deep violet"
  sheet printed on mauve makes that claim false on the page.
  An earlier draft of this spec said grounds are always positional, which contradicted the
  Overview and the Structure table and was built that way before it was caught. Corrected
  10 October 2026.
- The imagery opener and the misuse sheet are narrative sheets and keep their positional slice.
- `fall_joins` is amended accordingly: continuity is asserted across the sixteen narrative
  sheets, and each stage sheet is required to equal its stage token exactly. That is a stronger
  assertion than the one it replaces, not an exemption.
- Ink is re-derived per sheet by measurement, never hardcoded. Gold at L 0.781 and deep violet
  at L 0.301 are far apart, so the stage sheets will not all take the same ink.
- Radius 0 and shadow none, unchanged. A frame's edge is its own contrast against the ground.
- Caption and reading colour is the text token at the opacity the sheet's own ground allows,
  measured, not assumed. On gold and after gold that means the void-coloured ink the light
  sheets already use.

## Typography

No new type, and this is load-bearing: sheet 7 states the system has **two faces**, so a third
family for hex codes would contradict the document. There is no monospace in this guide — the
`.mono` class is letter-spacing on the body face, nothing more. Stage name in Instrument Serif
at the `--x3` display step. Hex and lightness in the **body face with `.mono` tracking and
tabular numerals**, at `--xs`, which is how every other reading in the guide is already set. Captions at `--xs`. The five rules on the
opener at the largest display step the sheet allows, matching how Frame.io sets a section
statement.

## Responsive

Mobile first. The single column is the base and the grid is the enhancement.

- **Base, below 600px**: one column, full content width, 5:4 slots, document order. Six frames
  stacked is a long sheet on a phone and that is correct — the guide is read, not scanned.
- **600px to 900px**: two columns, three rows. A new breakpoint, placed where the content breaks:
  below 600px a three-column slot is under 180px wide and the frame stops being readable as a
  photograph.
- **Above 900px**: three columns, two rows. 900px is the guide's existing break and is not moved.
- The existing mobile block already collapses `.imgs` to one column. The new grid uses that class
  so it inherits the behaviour rather than adding a second rule that can drift from it.
- **Type** stays on the existing `clamp` tokens. No new type scale, no new font sizes.
- **No hover-dependent content anywhere.** The mood board reveals its descriptor on hover. That
  cannot carry into the guide: hover does not exist on touch and does not exist in print.
  Captions are always visible.
- **No full-height elements**, so no `100vh` exposure. The sheet's `min-height` already uses
  `svh` and stays that way.
- Nothing is interactive, so there are no touch targets to size. The existing `touch_targets`
  check continues to pass trivially.
- **Videos**: `playsinline` and `muted` are required or iOS takes them fullscreen on play. Six
  looping clips on one sheet is the worst case; references on screen use the web-resolution
  encodes already in `moodboard-media`, not the source files.

## What it must not do

- **Must not brighten.** No placed image's upper quartile may sit above gold at L 0.781. This
  is the one rule the whole document rests on and it is now measurable — see the decision above
  on which statistic it is measured with. Specular highlights are permitted; a bright *body*
  is not.
- **Must not bleed to the sheet edge.** `pdf_edges` requires every page edge to carry the
  ground. This is the specific reason C2 was not chosen.
- **Must not split the grid across a sheet.** `no_cut_row` forbids it, and it now has to hold
  for a two-row block, not a one-row strip.
- **Must not let the slot ratio float with the viewport.** 5:4 is fixed at every breakpoint and
  in print. A frame that crops differently on a phone than on a press is not art direction.
- **Must not put a caption on an unmeasured ground.** `text_on_fall` measures every text element
  against the ground it actually sits on, and that now includes readings over colour.
- **Must not introduce a white or light panel** to sit images on. Elevation stays the surface steps.
- **Must not restate the mood board's descriptors.** Those are written in Céline's form for a
  mood board. Guide captions name the rule the frame demonstrates.
- **Must not leave the field above the grid to chance.** Equal on all four stage sheets or the
  section reads as four attempts at one layout.

## The brightness rule contradicted its own evidence — settled

Sheet 11 currently states: *"No specular flash, no blown highlight. The brightest value in an
image sits at or below the gold of last light, L 0.781."* Measured against the twelve references
on the two mocked stage sheets, that rule fails almost everywhere:

| Statistic | References at or below L 0.781 |
|---|---|
| Absolute brightest pixel | 1 of 12 |
| 99th percentile | 4 of 12 |
| **Upper quartile** | **11 of 12** |

A max-pixel reading fails any photograph with a highlight in it, which is nearly all of them.
The guide cannot print as exemplars a set of frames that break the rule stated three sheets
earlier, so one of the two has to move.

**Proposed resolution: restate the rule on the upper quartile.** "The upper quartile of an
image's lightness sits at or below gold, L 0.781." That is the statistic the stage-assignment
script already uses, so the document measures brightness one way throughout rather than two.
It keeps the rule's intent — no frame whose *body* is brighter than last light — and stops it
forbidding a specular that every one of these photographs has.

Measured across all 49 references on 10 October 2026, three fail and drop out:
`Fr3gA2Q.jpg` (L 0.856), `GVEgivk.jpg`, and `mPNk84g.mp4` (L 0.869, measured on its poster
frame rather than frame 0 — see the ruling in the execution ledger). Each stage still fills its
six from the references that remain.

The alternatives, for completeness: hold the max-pixel rule and lose eleven of twelve
references, which is not a guide; or allow a stated fraction of pixels above gold, which needs
a second number invented to support the first.

**Settled 10 October 2026**, carried by Aaron's approval of this spec. Sheet 11's wording
changes from "the brightest value" to "the upper quartile", and `mPNk84g.mp4` drops off the
deep violet sheet in favour of the next-nearest reference.

**The opener's sub-line states the rule as "Up to a quarter of the frame may pass it; the rest
may not."** An earlier draft said "A highlight may pass it", which understates what a p75
ceiling permits — up to 25% of a frame's pixels may exceed L 0.781, which is a quarter of the
picture, not a highlight. The misuse sheet must agree with this: a tile illustrating the broken
rule shows an over-lit *body*, not a blown specular, because a small blown highlight does not
break the rule as written. A guide whose misuse page contradicts its own rule page is the exact
failure this section exists to prevent.

---

## New audit checks required

The guide's harness (`tools/guide_audit.py`) runs 13 checks and none of them know about
images. Six are needed:

1. `image_never_brightens` — every placed image's upper-quartile lightness is at or below
   L 0.781, measured the same way the stage assignment measures it.
2. `image_on_ground` — no image touches a page edge; the ground does.
3. `poster_in_print` — every video reference resolves to a still in the PDF.
4. `caption_contrast` — every caption clears its floor against the ground it sits on, which is
   `text_on_fall` extended to the new elements.
5. `grid_ratio_holds` — every slot measures 5:4 within 1% at every tested viewport and in the
   PDF, and the field above the grid is equal across the four stage sheets.
6. `footer_in_page` — every sheet's footer sits wholly inside its page in the PDF. Measured
   10 October 2026, a stage sheet clears the 8.05in page by about 11.9px, and `.sheet` carries
   `overflow:hidden` in print — so without this check a stage name that wrapped to two lines
   would be clipped in silence rather than reported.

---

## Open, and blocking nothing yet

- Stage 3 and 4 names. The guide prints "Rose" and "Deep violet" from the tokens; the pick from
  `brand/2026-10-09-stage-three-four-names.html` is still open. These sheets print whatever the
  tokens say, so a later rename re-renders without touching this spec.
- The 5 conditional references stay out until their named fix is done.
- Nothing blocking. The brightness statistic is settled above.
