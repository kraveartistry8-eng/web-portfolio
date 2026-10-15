# Afterglow Ember Satin: Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v23 ember on the hour-lite guide with the approved satin ember:
- **The satin:** the satin pressed by the ember, with the type, panels, swatches and photographs printed on it.
- **The light:** c3 unchanged on top of it, then the raking light at a third.

All of it runs on the live guide rasterised in the browser.

**Architecture:**
- **What is seen:** the guide's sheets are rasterised near the viewport into a page view and a ground view of the window. The prototype's pipeline runs on those views unchanged and draws one fixed canvas.
- **The pipeline:** the satin cloth (Three.js), then c3 (2D canvas), then the raking light (WebGL2).
- **The real HTML:** stays in the page, invisible, for links, selection, find-in-page and screen readers.
- **Code:** every number and every shader comes from the prototype. The prototype code is moved into modules, not rewritten.

**Tech Stack:**
- Three.js 0.160.0 and WebGL2, bundled with esbuild, as the current `brand/ember/build.sh` does.
- `node --test` for the pure maths.
- Python 3 and Playwright for the guide build and the browser checks, headless on the real GPU.

**Spec:** [docs/superpowers/specs/2026-10-14-afterglow-ember-satin-design.md](../specs/2026-10-14-afterglow-ember-satin-design.md), approved by Aaron on 14 Oct 2026. Its §9 records the proven mechanism.

**Reference prototype:** `brand/ember-directions/satin-combined.html`, at its defaults: P2d, satin a third, raking light a third.

**Proof of the mechanism:** `brand/ember-directions/satin-live.html`, with `brand/ember-directions/proof/raster.js`.

Serve both from the repo root with `python3 -m http.server 8765`. **Where the plan and the prototype disagree, the prototype wins.**

**No commits.** Aaron commits only when he says. Every "Checkpoint" step means stop and report the state. It never means `git commit`.

**Isolation.** The older builds must not change: the current engine in `brand/ember/`, the frozen `brand/ember/v23/`, `tools/density_b_family.py`, `tools/check_b1.py` and every older guide HTML file stay byte-for-byte. Only `build_lite()` in `tools/afterglow_specimen.py` swaps the new engine into its own output. Task 1 records the baseline; Task 12 proves it.

**Plain-language steps.** By Aaron's feature-design rule, the steps below describe scope and sequence, not syntax. The code to move is named by file and section in the prototype or the proof, and the engineer copies it from there.

**Lesson from 13 Oct.** That build failed by re-deriving the prototype with a different mechanism, and no blind check was run before Aaron saw it. Here, every visual task ends with a side-by-side against the prototype, and Task 11 is a blind gate before Aaron is shown anything.

---

## File map

| File | Responsibility | Change |
|---|---|---|
| `brand/ember/satin/satin-math.js` | Pure maths: tiers, viewport-unit pinning, nearness, bend easing step, frame-budget step-down, phone sizes | Create |
| `brand/ember/satin/satin-math.test.mjs` | Tests for the maths | Create |
| `brand/ember/satin/raster.js` | Serialises one sheet into an SVG foreignObject and draws it to a canvas, from the proof's `raster.js` | Create |
| `brand/ember/satin/views.js` | Keeps rasters of sheets near the viewport and draws the page view and ground view of the window | Create |
| `brand/ember/satin/cloth.js` | The satin: cloth simulation, press, mask, eased bend and satin shader. P2d values only | Create |
| `brand/ember/satin/c3.js` | c3, verbatim from the prototype: input, glide, touches, cooling, surfaces | Create |
| `brand/ember/satin/rake.js` | The raking light: the splat field, the keep mask and the mode-0 display shader | Create |
| `brand/ember/satin/engine.js` | Assembles the layers, input, tiers, reduced motion, hidden tab, frame budget, fallback; exposes `window.EmberSatin` | Create |
| `brand/ember/satin/build.sh` | Bundles `engine.js` and Three.js 0.160.0 into `ember-satin.bundle.js` | Create |
| `brand/ember/satin/ember-satin.bundle.js` | Built output | Built |
| `brand/ember/satin/harness.html` | A page that loads the bundle over a copy of the hour-lite guide, for the checks | Create |
| `tools/afterglow_specimen.py` | `build_lite()` only: swaps the v23 bundle, container, CSS and boot for the satin ones | Modify |
| `tools/check_ember_satin.py` | Browser checks of the built guide | Create |
| `tools/test_afterglow_specimen.py` | One added test: the hour-lite output carries the satin engine and not the v23 one | Modify |
| `brand/ember/*`, `brand/ember/v23/`, `tools/density_b_family.py`, `tools/check_b1.py`, older guide HTML | Older builds | **Untouched** |
| `brand/ember-directions/*` | Prototype and proof, the reference | **Untouched** |

---

## Chunk 1: Baseline and maths

### Task 1: Baseline what must not change

**Files:** none changed. Write `$TMPDIR/ember-satin-baseline.txt`.

- [ ] **Step 1:** Record a SHA-256 checksum of every file under:
  - `brand/ember/` (excluding the new `satin/` folder);
  - `brand/ember/v23/` and `brand/ember-directions/`;
  - `tools/density_b_family.py` and `tools/check_b1.py`;
  - every `brand/*.html` except `brand/2026-10-12-guide-hour-lite.html`.

  Save the list to `$TMPDIR/ember-satin-baseline.txt`. Also save the output of `git status --porcelain` to `$TMPDIR/ember-satin-status.txt`; the tree already has many uncommitted changes from earlier work, and Task 12 compares against this snapshot, not against a clean tree.
- [ ] **Step 2:** Run the existing suites so later failures can't be blamed on this work: the ember maths with `node --test brand/ember/ember-math.test.mjs`, then `python3 tools/test_afterglow_specimen.py`, then `python3 tools/check_b1.py`. Record the pass counts; any failure already present is noted, not fixed.
- [ ] **Step 3:** Checkpoint. Report the counts and the baseline path.

### Task 2: The pure maths, test first

**Files:** create `brand/ember/satin/satin-math.js` and `brand/ember/satin/satin-math.test.mjs`.

The functions, each with the values that come from the spec or the prototype:

| Function | Behaviour | Tests |
|---|---|---|
| tier | From width and coarse pointer, gives the cloth grid, steps per frame and pixel-ratio cap. Phone: width up to 576 → 60 × 36, 1 step, cap 1.5. Tablet: 577–992 → 90 × 54, 2 steps, cap 2. Desktop above that → 120 × 72, 2 steps, cap 2. | Each boundary, at 390, 576, 577, 992, 993 and 1440 |
| pinViewportUnits | Rewrites every length in viewport-height units (vh, svh, dvh, lvh) in a stylesheet text to the same length in px for a given window height, to two decimals. Leaves width units and everything else alone. | 94 small-viewport-height units at a 900 px window become 846.00 px; a negative and a decimal value; width units untouched |
| near | Given a sheet's top and bottom and the window height, says whether to keep its raster: within one window above or two below. Says whether to evict it: more than three windows above or four below. | Both edges of each band |
| bendStep | One frame of the two-stage bend easing, from the prototype's eased-bend function in `satin-combined.html` (the function that starts "the bend the elements follow is eased on its own"). One flag decides for both stages: it is gathering when the target is larger in magnitude than the first stage's current value, otherwise releasing. Gathering moves the first stage 0.2 and the second 0.25 of the way; releasing moves them 0.06 and 0.08. | The rates; the release never overshoots zero; a 60-frame release from 1 decreases monotonically, with no frame-to-frame drop larger than the one before it once past the peak (no snap) |
| budget | From recent frame times, gives the step-down level: 0 for everything, 1 for no bend, 2 for no satin. It steps down when the mean frame rate stays below 45 fps for 2 s, and never steps back up. | Holding at 50 fps stays at 0; 40 fps for 1.9 s stays; 40 fps for 2.1 s goes to 1; then goes to 2 after a further 2 s; recovery never returns it |
| phoneSizes | The press rim blur and the bend cap by tier: desktop and tablet 76 px and 8 px; phone 56 px and 6 px. | Each tier |

- [ ] **Step 1:** Write the tests in the table above in `satin-math.test.mjs`, in the style of `brand/ember/ember-math.test.mjs` (node:test and strict assert).
- [ ] **Step 2:** Run `node --test brand/ember/satin/satin-math.test.mjs`. Expected: every test fails because the module is missing.
- [ ] **Step 3:** Write `satin-math.js` with the six functions as plain ES-module exports, no DOM.
- [ ] **Step 4:** Run the tests again. Expected: all pass.
- [ ] **Step 5:** Checkpoint.

---

## Chunk 2: Rasterising the live guide

### Task 3: The rasteriser

**Files:** create `brand/ember/satin/raster.js`.

- [ ] **Step 1:** Move the proof's `brand/ember-directions/proof/raster.js` into an ES module that exports the same two operations: rasterise one sheet, as page or as ground, at a pixel ratio; and collect the page styles once.

  Keep the proof's behaviour exactly:
  - the linked Google Fonts stylesheet is inlined, with its font files as data URLs;
  - the page's own style elements are included, except any marked as belonging to the engine;
  - the style text goes in a CDATA section;
  - photographs are inlined as data URLs, resolved against the document's base URL;
  - the ground version hides each child of the sheet;
  - the SVG is at least as tall as the window;
  - viewport-height units are pinned with `pinViewportUnits` from Task 2;
  - in WebKit only, the image is drawn again twice, 60 ms apart, so photographs appear.
- [ ] **Step 2:** Add a style-cache reset, so that a font load or resize re-reads the styles.
- [ ] **Step 3:** Create the check script `tools/check_ember_satin.py`. Start it with one check, **raster fidelity**:
  - On the current hour-lite guide, served over http, switch off the v23 ember first: hide its container element, remove the class that marks the ember as running from the root and body elements, and add a style that forces the ember's per-element light variable to zero on every element, so no lit text shadows are captured.
  - For each sheet, scroll it into view, take a native screenshot of the sheet's box (height capped at the window), rasterise the same sheet at the page's pixel ratio, crop it to the screenshot's size, and compare the mean absolute difference per channel.
  - Rasterise sheets 01, 03, 05, 11 and 15 and compare each with a native screenshot of the same sheet.
  - **Pass:** mean difference under 1.0/255 in Chromium at 1× and 2×, and under 1.5/255 in WebKit at 2×.

  Install Playwright's WebKit if it is missing.
- [ ] **Step 4:** Run `python3 tools/check_ember_satin.py raster`. Expected: PASS for every sheet in both engines.
- [ ] **Step 5:** Checkpoint.

### Task 4: The views

**Files:** create `brand/ember/satin/views.js`.

- [ ] **Step 1:** Move the proof's live-view code from `satin-live.html`, the block that starts at "live: the guide's sheets are rasterised…": the sheet cache, the near-viewport rastering, eviction, and drawing the page view and ground view of the window at the current pixel ratio. Replace its inline distance tests with `near` from Task 2. The views fill with #080808 where no sheet is drawn, as the proof does.
- [ ] **Step 2:** Make it start rasterising the sheet under the viewport first, then the sheets after it, then the sheets before it. Make one sheet at a time and yield to the browser between sheets, so scrolling never stalls.
- [ ] **Step 3:** Clear the cache and re-raster when:
  - the window width changes, debounced by 150 ms;
  - the device rotates;
  - the document's fonts finish loading.

  A change of height alone only redraws the views, so the mobile browser bar never re-rasterises.
- [ ] **Step 4:** Expose a "dirty" flag that the engine reads each frame. Scrolling sets it. The keep mask (Task 6) is rebuilt at most every 120 ms, as in the proof.
- [ ] **Step 5:** Extend the check script with **views at rest**:
  - load the harness from Task 8 with the effect switched off at the source (a URL flag that skips the three layers and draws the page view straight to the canvas);
  - scroll to sheets 03, 11 and 16, wait 1.5 s, and compare the canvas with a native screenshot;
  - **pass:** mean under 1.0/255.

  This check needs Task 8's harness, so mark it pending until then.
- [ ] **Step 6:** Checkpoint.

---

## Chunk 3: The three layers

Each task moves code from the prototype `brand/ember-directions/satin-combined.html` into one module, keeping every number. The module reads its page and ground from the views (Task 4) instead of from `r/sNN.png` and `r/gNN.png`. **Don't simplify any shader or constant.**

### Task 5: The satin cloth

**Files:** create `brand/ember/satin/cloth.js`.

- [ ] **Step 1:** Move the cloth module from the prototype's second script, the one that starts "Ember rerun (14 Oct 2026): the ground is a real sheet of cloth". Keep only what P2d uses:
  - the V2 weight with P2d's cloth overrides;
  - the press;
  - the mask with its 1.7 s hold;
  - the elements' light (elem 2) and the eased bend at ×3;
  - the satin fragment shader.

  Remove the variant table, its buttons, the notes, P2e's crisp mode, the band mode and the strength buttons. Fix the satin strength at a third and the bend gain at 3.
- [ ] **Step 2:** Replace the bend easing loop's inner arithmetic with `bendStep` from Task 2.
- [ ] **Step 3:** Take the grid size and steps per frame from `tier`, and the rim blur and bend cap from `phoneSizes`. The bend is measured in CSS px, not scaled by window width: the prototype scales its 4 px base by the window's device width over 1440, which shrinks the bend on narrow windows; replace that with the device pixel ratio alone, so the base is 4 CSS px at any width, the gain of 3 gives about 8 CSS px at the steepest slope, and the result is clamped to the tier's cap (8 px, or 6 px on phones).
- [ ] **Step 3b:** On the phone tier, compile the satin and raking-light shaders at medium float precision instead of high.
- [ ] **Step 4:** Read the ember's shape from c3's light canvas (Task 6), passed in at construction rather than through a global.
- [ ] **Step 5:** Expose: build (called only when the window width changes or the device rotates, never on a height-only change), refresh when the views change, one tick per frame (simulate and render, returning whether it drew), and dispose.
- [ ] **Step 6:** Side-by-side. Make a small test page in `brand/ember/satin/` that runs this module alone over the prototype's own captures of page 11 (`brand/ember-directions/r/s11.png` as the page, `r/g11.png` as the ground). Run the Task 9 stroke on it and on `satin-combined.html` page 11, and in the prototype read the cloth's own canvas from its exported cloth object (not the final screen, which carries c3 and the raking light). Pass: mean difference under 2/255 at each of the three frames.
- [ ] **Step 7:** Checkpoint.

### Task 6: c3 and the raking light

**Files:** create `brand/ember/satin/c3.js` and `brand/ember/satin/rake.js`.

- [ ] **Step 1:** Move c3 into `c3.js`, verbatim from the prototype's "c3, verbatim from a2-family.html" section, together with the pointer input, the touch laying, the glide and the probe it samples colours from. It draws its frame onto a 2D canvas whose base is the cloth's canvas, falling back to the page view when the cloth did not draw. That is the prototype's frame function for mode X1.
- [ ] **Step 2:** Move the raking light into `rake.js`:
  - the splat program and the field;
  - the keep-mask build (from the prototype's upload function);
  - the display program with only mode 0, the raking light, in live mode, reading c3's canvas each frame;
  - the gain fixed at a third.

  Remove modes 1 to 10, the fold and sheet programs, and their tables.
- [ ] **Step 3:** Pointer input:
  - Listen to pointer movement on the window, passive, so scrolling and clicks are never held up.
  - For touch, a finger is the cursor while it is down, and lifting it counts as a stop.
  - A tap lays one touch.
  - Never call anything that prevents scrolling.
- [ ] **Step 4:** Side-by-side: run c3 and the raking light over the same capture page as Task 5's test page, with the cloth's canvas as c3's base, and compare the final canvas with `satin-combined.html` on page 11 after the Task 9 stroke. Mean difference under 3/255 at each frame.
- [ ] **Step 5:** Checkpoint.

### Task 7: The engine

**Files:** create `brand/ember/satin/engine.js`.

- [ ] **Step 1:** Assemble the layers in the spec's order (§3.6), in one frame loop:
  1. refresh the views if they are dirty;
  2. tick the cloth;
  3. draw c3 over the cloth;
  4. upload c3's canvas;
  5. draw the raking light to the one visible canvas.
- [ ] **Step 2:** Set up the page:
  - one fixed canvas above the deck, with no pointer events, sized to the stable viewport height;
  - the deck made invisible only once the first full frame has been drawn with every sheet in the window rasterised (until then the deck shows as normal and the canvas is hidden), so loading never flashes;
  - while a sheet in the window is not yet rasterised (a fast scroll), the canvas draws the deck's live area through instead: the canvas hides and the deck shows until the views are complete again, crossfaded over 150 ms, never black;
  - a print rule that hides the canvas and shows the deck.
- [ ] **Step 3:** Selection. While the document has a selection inside the deck, draw its client rectangles into the page view in the browser's selection colour at 35% before the layers run, so selected text visibly highlights.
- [ ] **Step 4:** Behaviours:
  - **Reduced motion:** no cloth simulation or bend, and no glide. c3 and the raking light stay.
  - **Hidden tab:** the loop stops.
  - **Frame budget:** feed frame times to `budget` from Task 2. Level 1 turns off the bend, and level 2 turns off the cloth.
  - **No WebGL2:** c3 alone on its 2D canvas, over the page view.
  - **Rasterising fails** (any error in Task 3): the deck becomes visible again and the engine stops, so the guide is never blank.
- [ ] **Step 5:** Expose a global named EmberSatin with two operations: start, given the deck element, and stop.
- [ ] **Step 6:** Checkpoint.

---

## Chunk 4: Bundle, harness, guide

### Task 8: Bundle and harness

**Files:** create `brand/ember/satin/build.sh` and `brand/ember/satin/harness.html`.

- [ ] **Step 1:** Write `build.sh` on the pattern of `brand/ember/build.sh`. It bundles `engine.js` with Three.js 0.160.0 into `ember-satin.bundle.js` as a classic script that defines the global EmberSatin, then prints the size raw and gzipped.
- [ ] **Step 2:** Run `sh brand/ember/satin/build.sh`. Expected: the bundle is written, with the size printed.
- [ ] **Step 3:** Write `harness.html`. Like the proof, it fetches `brand/2026-10-12-guide-hour-lite.html`, keeps its styles and deck, drops the v23 container and scripts, loads the satin bundle, and starts it. It takes two URL flags:
  - one that switches the three layers off, for Task 4's check;
  - one that hides the proof UI for captures.
- [ ] **Step 4:** Run Task 4's pending "views at rest" check. Expected: PASS.
- [ ] **Step 5:** Checkpoint.

### Task 9: Match the prototype, before the guide

**Files:** extend `tools/check_ember_satin.py`.

- [ ] **Step 1:** Add a **prototype match** check:
  - Record the harness and `satin-live.html` with the same scripted stroke, at a 1440 × 900 window: scroll the sheet into view and wait 2 s; move to (300, 620); then 71 moves 16 ms apart, the n-th at x = 300 + 13n and y = 620 − 4n + 60 × sine(n ÷ 7); then capture at the last move, 330 ms later, and 500 ms after that.
  - Do this on sheets 03, 11 and 16.
  - **Pass:** mean difference between the two under 3/255 at each frame. Some difference comes from timing. (This compares with the proof, which runs on the same live guide; the comparison with the prototype itself is Task 6's side-by-side and Task 11's blind gate.)
- [ ] **Step 2:** Add an **idle exactness** check: 3 s after the last movement, the harness canvas matches a native screenshot of the same sheet within 1.0/255. At rest the page is exactly as drawn.
- [ ] **Step 2b:** Add a **no flash** check: from page load, and during a fast scroll from sheet 01 to sheet 16 in 300 ms, sample the visible screen every 16 ms; no sample may contain a run of #080808 larger than 5% of the window where the native page has none, and no frame-to-frame change of mean brightness may exceed 6/255 without a stroke.
- [ ] **Step 3:** Add a **confinement** check: at the stop frame, at least 90% of the pixels that differ from the idle frame by more than 2/255 lie within 200 px of the stroke's path, and the 90% radius is within 10% of the prototype's own on the same stroke. (Corrected 14 Oct: the plan first said 120 px, but c3's own light, unchanged and approved, reaches about 140 px plus blur; the prototype itself puts 90% of its change within 183–186 px.)
- [ ] **Step 4:** Add a **no-snap** check:
  - sample the wordmark's displacement from its rest position every 50 ms for 2 s after the stop on sheet 11;
  - after its peak, the value must fall monotonically;
  - no 50 ms drop may be larger than the drop before it, by more than 10%.
- [ ] **Step 5:** Run them all. Expected: PASS. If the prototype match fails, compare the modules with the prototype line by line and fix the difference; never re-tune the numbers to pass.
- [ ] **Step 6:** Checkpoint.

### Task 10: Wire into the hour-lite guide only

**Files:** modify `tools/afterglow_specimen.py` (`build_lite()` only) and `tools/test_afterglow_specimen.py`.

- [ ] **Step 1:** Write a failing test in `tools/test_afterglow_specimen.py`. It asserts that the hour-lite output:
  - contains the satin bundle;
  - contains its start call on the deck;
  - does not contain the v23 bundle's global or the v23 ember container;
  - does not contain the v23 lit-element CSS.
- [ ] **Step 2:** Run `python3 tools/test_afterglow_specimen.py`. Expected: the new test fails.
- [ ] **Step 3:** In `build_lite()`, on the finished output (that is, on the value it currently returns, after the unhour, recopy and refall passes; restructure the last line to assign it, swap, then return), swap in its own output only:
  - remove the v23 container, the v23 bundle script and the v23 boot script;
  - remove the v23 ember CSS block (the one that starts "the ember: a canvas behind the sheets") and the transparent-sheet rule;
  - inline `ember-satin.bundle.js`, escaping any closing script tag as `with_ember` does;
  - add the satin's small CSS (the canvas, the invisible deck while the engine runs, the print rule) and a boot that starts it on the deck after the fonts have loaded.

  Each removal is asserted to have happened exactly once. Nothing in `tools/density_b_family.py` changes. Remove the now-unused chroma replacement line only if the v23 boot script it edits has gone; keep its assert honest.
- [ ] **Step 4:** Run `python3 tools/afterglow_specimen.py`, then the test suite. Expected: the build writes `brand/2026-10-12-guide-hour-lite.html`, and every test passes, including the new one and the Task 1 baseline counts.
- [ ] **Step 5:** Checkpoint.

### Task 11: Checks on the built guide, then the blind gate

**Files:** extend `tools/check_ember_satin.py`.

- [ ] **Step 1:** Point every check from Tasks 3, 4 and 9 at the built guide as well as the harness, served over http. Expected: PASS.
- [ ] **Step 2:** Add the responsive and behaviour checks:
  - **390 × 844 at 3×, coarse pointer:**
    - the phone tier is used;
    - a touch drag scrolls the page by the drag distance (scrolling not blocked);
    - a tap produces one press;
    - there is no horizontal scroll.
  - **768 × 1024:** the tablet tier is used.
  - **Height-only resize:** no re-raster is counted.
  - **Reduced motion:** after a stroke, the bend and satin are zero, c3's light shows, the raking light shows on an edge facing the stroke, and the light stops within 34 ms of the last move (no glide).
  - **Scroll does not press:** scrolling with no pointer movement leaves the satin flat (no difference from the idle frame beyond 1/255 away from the scrolled content); and a swell left settling by a stroke stays at the same screen position while the page scrolls 200 px under it.
  - **Hidden tab:** no frames are drawn.
  - **Print:** the canvas is hidden and the deck shows.
  - **Links:** a link in the deck is clickable through the canvas.
  - **Selection:** a selection shows its highlight.
  - **Errors:** no console errors.
- [ ] **Step 2b:** Run the raster fidelity and the no-flash checks in Firefox too (install Playwright's Firefox if missing). Firefox is not a pass condition yet: report its numbers, and if its fidelity fails (an inaccurate raster throws no error, so the fallback would not trigger on its own), the engine does not start in Firefox: the native page shows, with no ember, until a fix is planned with Aaron.
- [ ] **Step 3:** Add a **frame-rate** report: the mean frame rate during a 2 s stroke at 1440 × 900 and at 390 × 844. Report it; don't fail on it. The frame-budget step-down covers slow devices.
- [ ] **Step 4:** Run all checks. Expected: PASS, with frame rates reported.
- [ ] **Step 5: The blind gate.** Record the built guide and `satin-combined.html` (its page buttons 03, 11, 16 via the page URL flag) with the Task 9 stroke, three frames each. For each page make one sheet per side: the three frames in a row, and below them the same frames with contrast ×1.8 and brightness ×1.6. Randomise which side is X and which is Y, keep the key outside the critic's folder, and give a fresh critic only the six images, asking per pair which implementation of the effect is better crafted and whether the difference is large, small or negligible, then overall whether a careful viewer could tell them apart by the effect alone.
  - **Passes:** the critic can't reliably tell them apart.
  - **Fails:** fix the named difference and repeat.

  Aaron is shown the built guide only after this passes.
- [ ] **Step 6:** Checkpoint. Open the built guide for Aaron, with the gate's verdict and the frame rates. Ask him to review it by eye.

### Task 12: Prove the older builds untouched

**Files:** none changed.

- [ ] **Step 1:** Recompute the checksums from Task 1 and compare them. Expected: identical, file for file.
- [ ] **Step 2:** Run `node --test brand/ember/ember-math.test.mjs` and `python3 tools/check_b1.py`. Expected: the same results as the Task 1 baseline.
- [ ] **Step 3:** Run `git status --porcelain`, compare it with `$TMPDIR/ember-satin-status.txt` from Task 1, and confirm that the only new or changed entries are:
  - new files under `brand/ember/satin/`;
  - `tools/afterglow_specimen.py`, `tools/test_afterglow_specimen.py` and `tools/check_ember_satin.py`;
  - the rebuilt `brand/2026-10-12-guide-hour-lite.html`.
- [ ] **Step 4:** Update the memory note `afterglow-specimen-paused.md` with the built state.
- [ ] **Step 5:** Checkpoint. Nothing is committed. Ask Aaron whether to commit.
