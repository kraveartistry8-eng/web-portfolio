# Afterglow Brand Guidelines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a visual brand guideline document for Afterglow that both demonstrates and describes the brand, and fill every Week 2 token it depends on.

**Architecture:** The project already has a working pattern for this: `tools/audit.py` and `tools/coverage.py` check the roadmap, and both must pass before the PDF is reprinted. This plan follows it. A new `tools/brand_audit.py` encodes the spec's verification criteria as checks that fail first and pass as the work lands. Two throwaway HTML explorations let Aaron pick the colour ramp and the type by eye; their outcomes are recorded in `design-tokens.json`, and the guideline document renders from those tokens rather than restating them.

**Tech Stack:** Python 3.9, Playwright, Pillow (all already installed and used by `tools/`). Hand-authored HTML and CSS, no framework, matching `design/` and `archive/colour/`.

**Spec:** `docs/superpowers/specs/2026-10-07-afterglow-brand-guidelines-design.md` (what the document says)
and `docs/superpowers/specs/2026-10-07-afterglow-guideline-direction-spec.md` (what it looks like, direction: The Descent with measured specimens, in the Margin form)

## Global Constraints

- Six neutral tokens are locked and must appear unchanged: ground `#080808`, surface-deep `#141414`, surface `#2B2B2B`, text `#EEECEA`, muted `#C0C0C0`, border `rgba(192,192,192,0.22)`.
- No token value anywhere may be `#39FF14` or `#FF00BD`.
- Stage lightness falls monotonically across the four stages when converted to OKLCH.
- Stage roles: stage 1 may be text, stage 2 large text or fills only, stages 3 and 4 never text.
- No state change brightens. Hover, focus and active deepen or shift hue, never lighten.
- No em-dashes in anything that gets printed. Repo convention, stated in `README.md`.
- Dated filenames are `YYYY-MM-DD-slug`. The date is when the artifact was made.
- Motion has no overshoot, spring or bounce.
- The document is legible at 390px wide with no horizontal scroll.
- `brand/resources/voice-tone.md` is not modified by any task.
- The document's ground is a continuous fall, stage 1 at the top to stage 4 at the end, lightness falling monotonically. It never resets.
- Nothing brightens: no state, hover, focus, section or print rule may produce a lighter value than the one before it.
- No number appears in the document that was not computed from the real colour.
- A failing ratio is printed as the reason for a restriction, never hidden.
- Nothing is laid on the fall. Readings sit in a void ledger beside it, anchored to the position of the value they describe.
- Ledger rows stack in document order at small widths and never reflow into a grid.
- A position-dependent ratio is recomputed per viewport, never reprinted from another width.
- The rail carries position and no values; the ledger carries values and no position of its own. They are never merged.
- The rail is the folio. No page numbers.
- Full-height elements use `svh`. Never `vh`, and never `dvh`.
- Interactive targets are at least 44 by 44px; nothing reveals meaning on hover alone.

## Review Focus

- **A ramp that is monotonic but unusable.** L can fall correctly while stage 1 is still too dark to be text on void, breaking the role table. Task 2 asserts each stage against its role's contrast floor, not just the ordering.
- **PDF margins on a void document.** `tools/render.py` sets Letter with 0.55in margins and those margins render white. A full-bleed dark document will print with white borders around it. Task 6 asserts the rendered PDF's page edges are the ground colour.
- **A display face that cannot ship.** A font chosen on the specimen page may not be in Shopify's library and may have no webfont licence. Task 3 records which of the two delivery routes the choice requires before the choice is final.
- **Token file damaged during the fill.** `design-tokens.json` carries `_note` and `_forbidden` keys that explain decisions. A careless rewrite drops them. Task 4 asserts they survive.
- **Gradient banding.** A subtle gradient several thousand pixels tall bands visibly, worst at the violet end where the steps are closest. This is the one risk that could invalidate the direction, which is why Task 5 is a spike that runs before anything is built on it.
- **Contrast is a function, not a value.** Every text block sits on a different ground value. A checker that tests one constant proves nothing; Task 7 samples the rendered ground at each text element's own position.
- **Print page breaks through a ledger row.** A row separated from the ground it points at loses the thing it demonstrates, and a leader rule crossing a page boundary points off the page. Task 9 asserts no row is cut or orphaned from its anchor.
- **A reading that was true at another width.** Ledger rows go inline at 390px and no longer sit at the height of the value they describe, so a ratio copied from the desktop layout becomes a false number in the one document that cannot print one. Task 8 recomputes every printed ratio at 390px and compares it to what is on the page.
- **Screen-only compliance.** The no-brightening rule can hold in the stylesheet while a `print` or `prefers-reduced-motion` block reintroduces a light background. Task 6 checks the computed background under print emulation, not just the default.

---

### Task 1: Brand audit harness

**Files:**
- Create: `tools/brand_audit.py`
- Read: `brand/resources/design-tokens.json`, `brand/BRAND-IDENTITY.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `python3 tools/brand_audit.py` exits 0 when all checks pass, 1 otherwise, printing one `PASS`/`FAIL` line per check. Later tasks add checks to it and run it as their verification. It follows the structure of `tools/audit.py`: a `chk(cond, msg)` helper collecting into `OK` and `FAIL` lists.

- [ ] **Step 1: Write the failing checks**

In `tools/brand_audit.py`, implement these checks over `brand/resources/design-tokens.json`:

```
no_nulls          every value under color.stages, typography, spacing, radius,
                  shadow and motion is non-null
neutrals_locked   the six neutral hex values equal the Global Constraints values
no_forbidden      "#39FF14" and "#FF00BD" appear nowhere except under _forbidden
notes_intact      keys beginning "_" present in the file today are still present
no_week2          "Week 2" does not appear in brand/BRAND-IDENTITY.md
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 tools/brand_audit.py`
Expected: exit 1, with `no_nulls` and `no_week2` failing. `neutrals_locked`, `no_forbidden` and `notes_intact` pass already.

- [ ] **Step 3: Commit**

```bash
git add tools/brand_audit.py
git commit -m "test: add brand token audit, failing on unset Week 2 values"
```

---

### Task 2: Stage palette, explore and record

**Files:**
- Create: `brand/2026-10-07-stage-palette.html`
- Modify: `brand/resources/design-tokens.json` (`color.stages`)
- Modify: `tools/brand_audit.py`

**Interfaces:**
- Consumes: Task 1's `chk` helper.
- Produces: `color.stages.1..4` each carrying `name`, `value` (hex), and `oklch` (an `{l, c, h}` object). Later tasks read `value` for rendering and `oklch` for the monotonicity check.

- [ ] **Step 1: Add the ramp checks to `tools/brand_audit.py`**

```
l_monotonic       oklch.l strictly decreases from stage 1 to stage 4
hue_one_way       oklch.h rotates in one direction with no reversal
stage_roles       contrast vs #080808: stage 1 >= 4.5:1, stage 2 >= 3:1,
                  stages 3 and 4 recorded but unconstrained
stage_named       stage 2 has a non-null name drawn from the voice-tone vocabulary
```

Contrast uses the WCAG relative-luminance formula. Put it in a `contrast(hex_a, hex_b)` helper, since Task 6 reuses it.

- [ ] **Step 2: Run to verify the new checks fail**

Run: `python3 tools/brand_audit.py`
Expected: exit 1, ramp checks failing on null stage values.

- [ ] **Step 3: Build `brand/2026-10-07-stage-palette.html`**

Three candidate ramps, labelled A, B and C. All three share one L schedule falling in even steps; they differ in chroma shaping, with rose as the chroma peak in at least one. Render on the real `#080808` ground. Each stage appears three ways: as a full-bleed fill, as 48px text, and as a 24px mark. Print each stage's hex, its OKLCH triple, and its measured contrast against `#080808`, `#141414` and `#2B2B2B`. Follow the layout conventions in `archive/colour/2026-09-21-palette.html`.

- [ ] **Step 4: Present the page and wait for a pick**

Open it for Aaron. He picks a ramp, or asks for adjustments and the page is regenerated. Do not proceed on an assumed pick.

- [ ] **Step 5: Record the chosen ramp**

Write the four stages into `design-tokens.json` with `name`, `value` and `oklch`. Name stage 2 from the `voice-tone.md` vocabulary list.

- [ ] **Step 6: Run the audit to verify the ramp checks pass**

Run: `python3 tools/brand_audit.py`
Expected: ramp checks PASS. `no_nulls` still fails on typography, spacing, radius, shadow and motion.

- [ ] **Step 7: Commit**

```bash
git add brand/2026-10-07-stage-palette.html brand/resources/design-tokens.json tools/brand_audit.py
git commit -m "feat: define the four Afterglow stage colours"
```

---

### Task 3: Type, explore and record

**Files:**
- Create: `brand/2026-10-07-type-specimen.html`
- Modify: `brand/resources/design-tokens.json` (`typography`)
- Modify: `tools/brand_audit.py`

**Interfaces:**
- Consumes: Task 2's recorded stage values, for setting specimens on the real ground.
- Produces: `typography.display.family`, `typography.body.family`, `typography.scale` (an object with `ratio` and `base`), `typography.tracking`, `typography.leading`, and `typography.delivery` set to either `"shopify_library"` or `"self_hosted"` per face.

- [ ] **Step 1: Add the type checks to `tools/brand_audit.py`**

```
type_set          display.family and body.family are non-null
scale_measured    typography.scale has a numeric ratio and a base size,
                  and every named step is derivable from them
delivery_recorded each face records a delivery route of shopify_library
                  or self_hosted
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 tools/brand_audit.py`
Expected: the three type checks FAIL.

- [ ] **Step 3: Build `brand/2026-10-07-type-specimen.html`**

Candidate pairings on the `#080808` ground. Each candidate shows: `AFTERGLOW` as the wordmark, one hero line from the brief, a paragraph of `voice-tone.md` body copy at the proposed body size, and the scale rendered as its steps. State for each face whether it is in Shopify's font library or needs self-hosting, since that is a build cost and part of the choice.

- [ ] **Step 4: Present the page and wait for a pick**

Open it for Aaron. Do not proceed on an assumed pick.

- [ ] **Step 5: Record the choice**

Write families, scale ratio and base, tracking, leading, and the delivery route per face into `design-tokens.json`.

- [ ] **Step 6: Run the audit to verify the type checks pass**

Run: `python3 tools/brand_audit.py`
Expected: type checks PASS.

- [ ] **Step 7: Commit**

```bash
git add brand/2026-10-07-type-specimen.html brand/resources/design-tokens.json tools/brand_audit.py
git commit -m "feat: choose Afterglow display and body faces"
```

---

### Task 4: Remaining tokens

**Files:**
- Modify: `brand/resources/design-tokens.json` (`spacing`, `radius`, `shadow`, `motion`)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `spacing.base` and `spacing.scale`, `radius` values, `shadow` value, `motion.duration` and `motion.ease`. The document in Task 5 reads all of these.

- [ ] **Step 1: Fill the remaining tokens**

The spec decides the substance of three of these already, so record them rather than re-deciding: radius is near-zero, shadow is absent or a hairline because elevation is carried by the surface steps, and motion has no overshoot, spring or bounce. Choose a spacing base and scale, and a motion duration band and easing curve that settles rather than arrives.

- [ ] **Step 2: Run the audit to verify `no_nulls` passes**

Run: `python3 tools/brand_audit.py`
Expected: every token check PASS. `no_week2` still fails, since `BRAND-IDENTITY.md` is untouched until Task 6.

- [ ] **Step 3: Commit**

```bash
git add brand/resources/design-tokens.json
git commit -m "feat: set Afterglow spacing, radius, shadow and motion tokens"
```

---

### Task 5: Banding spike

**Files:**
- Create: `brand/2026-10-07-banding-spike.html` (throwaway)

**Interfaces:**
- Consumes: the ramp recorded in Task 2.
- Produces: a decision recorded in the spec's colour section, one of: no mitigation needed, noise overlay, or stepped at section boundaries. Task 6 builds on whichever.

This is a spike, not a feature. Its output is an answer. Keep nothing but the decision.

- [ ] **Step 1: Build the full-height gradient**

A page the real document's expected height carrying only the four-stage fall, nothing else.

- [ ] **Step 2: Capture and inspect for banding**

Run: `python3 tools/capture.py file://<abs path> --out . --name banding-spike`
Then sample columns of the full-page PNG with Pillow and count distinct quantised tones per 100px band. Expected: smooth if the count rises steadily; banding shows as long runs of one tone separated by steps.

- [ ] **Step 3: Look at the PNG**

The measurement finds steps; the eye decides whether they read. Open it.

- [ ] **Step 4: Record the decision and delete the spike**

Write the chosen mitigation into the direction spec's colour section. Delete the spike file.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-10-07-afterglow-guideline-direction-spec.md
git commit -m "spike: settle gradient banding mitigation for the fall"
```

---

### Task 6: Document shell

**Files:**
- Create: `brand/2026-10-07-afterglow-guidelines.html`
- Modify: `tools/brand_audit.py`

**Interfaces:**
- Consumes: tokens from Tasks 2 to 4, the banding decision from Task 5.
- Produces: the document with its structure but no content sections. Task 7 fills it.

- [ ] **Step 1: Add the shell checks to `tools/brand_audit.py`**

```
fall_monotonic    ground lightness sampled at ten even document positions
                  falls monotonically from first to last
no_brightening    no :hover, :focus or :active rule declares a colour or
                  background lighter in OKLCH L than its resting value
rail_is_folio     no element contains a page number; the rail exists
ledger_is_void    the ledger column's computed background is the void or a
                  surface step, never a value from the fall
svh_not_vh        no stylesheet rule uses vh or dvh units
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 tools/brand_audit.py`
Expected: shell checks FAIL, the document not existing yet.

- [ ] **Step 3: Build the shell**

The fall as one gradient on the document sized to its full height, scrolling with content and never fixed. The ledger as a void column at the right edge of the measure, running the document's full height and carrying no content yet. The rail outside it, the same gradient at 3px with a sticky marker. The crossover rule positioned where primary text first reaches 4.5:1 against the fall, labelled with that ratio. The fixed top-left slug carrying section and document title on the void. Section boundaries as hairlines.

- [ ] **Step 4: Run to verify the shell checks pass**

Run: `python3 tools/brand_audit.py`
Expected: shell checks PASS.

- [ ] **Step 5: Commit**

```bash
git add brand/2026-10-07-afterglow-guidelines.html tools/brand_audit.py
git commit -m "feat: build the guideline document shell"
```

---

### Task 7: Content sections and contrast as a function

**Files:**
- Modify: `brand/2026-10-07-afterglow-guidelines.html`
- Modify: `tools/brand_audit.py`

**Interfaces:**
- Consumes: the shell from Task 6; the content spec's section list.
- Produces: the complete document at desktop width.

- [ ] **Step 1: Add the positional contrast check**

```
text_on_fall    for every text element, sample the rendered ground at that
                element's own document position and compute its ratio there.
                Body text 4.5:1 minimum, large text 3:1, nothing exempt.
specimen_truth  every ratio printed in the document equals the computed
                ratio for those two colours, to two decimal places
ledger_anchored every ledger row sits within 4px of the document position
                where the fall equals the value that row describes
```

`specimen_truth` is the one that matters. A specification document that prints a number it did not measure is worse than one that prints none.

- [ ] **Step 2: Run to verify they fail**

Run: `python3 tools/brand_audit.py`
Expected: both FAIL, no content sections existing yet.

- [ ] **Step 3: Build the content sections**

In the order the content spec fixes: the brand in one line; the four stages as a sequence that deepens; the surface map; stage roles with measured ratios; type set in the chosen faces as its own specimen; spacing, radius, shadow, motion; usage rules including the deepening rule in testable form and where the rules stop at checkout; voice summary pointing to `voice-tone.md`.

Nothing is laid on the fall. Each stage is proved at the one position where the descent passes through it, with its reading in a ledger row joined to that position by a leader rule, failing ratios included. The ramp therefore fixes the colour section's running order. The six neutrals are not on the ramp and cannot be read off the ground, so they are specified in the ledger itself: its background steps to the surface values across the surface-map rows, and the column demonstrates the family it reports.

- [ ] **Step 4: Run to verify both checks pass**

Run: `python3 tools/brand_audit.py`
Expected: PASS. A failure here means a printed number is wrong, which is a content bug, not a threshold to relax.

- [ ] **Step 5: Commit**

```bash
git add brand/2026-10-07-afterglow-guidelines.html tools/brand_audit.py
git commit -m "feat: add guideline content sections with measured specimens"
```

---

### Task 8: Responsive

**Files:**
- Modify: `brand/2026-10-07-afterglow-guidelines.html`
- Modify: `tools/brand_audit.py`

**Interfaces:**
- Consumes: the complete desktop document.
- Produces: the document at 390px through desktop.

- [ ] **Step 1: Add the responsive checks**

```
no_h_scroll_390   at 390px, scrollWidth <= clientWidth
fall_survives     ground lightness at 390px falls monotonically across the
                  same ten positions, same as desktop
ledger_inline     at 390px every ledger row is full width, directly under the
                  passage it annotates, in document order, never in a grid
no_dead_leaders   at 390px no leader rule is rendered, since an inline row
                  does not sit at the height of its value
ratios_recomputed every ratio printed at 390px equals the ratio computed
                  against the ground that element actually sits on there
touch_targets     every interactive element is at least 44 by 44px
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 tools/brand_audit.py`

- [ ] **Step 3: Build the small-viewport behaviour**

Mobile-first, breakpoints where the content breaks. The rail moves to a 3px bar fixed at the top, filling as the reader descends, labels moving inline to section openers. The slug collapses to the section name and stops being fixed. The ledger stops being a column: rows move inline under the passage they annotate, their leader rules are dropped because there is no longer a height to point at, and each row names its own position instead. Ledger data stacks label above value. The ledger returns as a column above 760px; measure caps above 1180px.

Every printed ratio is recomputed at this width rather than carried over. A reading that was true at 1180px and reprinted unchanged at 390px is a false number, and this document's whole claim is that it does not print those.

- [ ] **Step 4: Run to verify they pass**

Run: `python3 tools/brand_audit.py`

- [ ] **Step 5: Commit**

```bash
git add brand/2026-10-07-afterglow-guidelines.html tools/brand_audit.py
git commit -m "feat: responsive behaviour for the guideline document"
```

---

### Task 9: Print, PDF and index

**Files:**
- Modify: `tools/render.py:4-5`, `tools/brand_audit.py`, `brand/BRAND-IDENTITY.md`
- Create: `brand/2026-10-07-afterglow-guidelines.pdf`

**Interfaces:**
- Consumes: the finished document.
- Produces: a rendered PDF, a passing audit, an updated index.

- [ ] **Step 1: Add the print checks**

```
print_ground     under print emulation the ground is still the fall, not white
no_cut_row       no ledger row crosses a page boundary, and no row is on a
                 different page from the ground its leader rule points at
pdf_edges        the rendered PDF's page corners are the ground colour,
                 sampled with Pillow, not white margin
```

- [ ] **Step 2: Parameterize `tools/render.py`**

Lines 4 and 5 take an optional source path, defaulting to the roadmap. Margins become zero for this source so the document controls its own padding.

- [ ] **Step 3: Verify the roadmap still renders**

Run: `python3 tools/render.py`
Expected: `pdf written`, console errors `none`. Proves the existing pipeline is unbroken.

- [ ] **Step 4: Render the guideline and run the print checks**

Run: `python3 tools/render.py brand/2026-10-07-afterglow-guidelines.html`
Then: `python3 tools/brand_audit.py`
Expected: both clean.

- [ ] **Step 5: Update `brand/BRAND-IDENTITY.md`**

Replace every "Week 2" row with its real value. Add the guideline document to Resource Files.

- [ ] **Step 6: Run the full audit**

Run: `python3 tools/brand_audit.py`
Expected: exit 0, every check PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/render.py tools/brand_audit.py brand/BRAND-IDENTITY.md brand/2026-10-07-afterglow-guidelines.pdf
git commit -m "feat: render and verify the Afterglow guideline document"
```

---

## Note on commits

This repository is not under version control yet. Every task ends with a commit step as
written, which requires `git init` first. If the repo is still absent when execution starts,
either initialise it or treat the commit steps as checkpoints and say so, rather than
silently skipping them.
