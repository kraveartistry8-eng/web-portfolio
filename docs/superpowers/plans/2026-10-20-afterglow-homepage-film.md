# Afterglow Homepage Film Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Afterglow homepage's first screen, direction A5 "The film", as a Shopify section a non-technical owner can change in the editor.

**Architecture:** A standard section (`sections/film-hero.liquid`) on a JSON homepage template, holding three blocks. One of them, the Line, is a reusable theme block in `blocks/` with a preset. Colours come from one theme-wide colour palette, and fonts from Shopify's font library. The site header floats over the section on the homepage only. A proof build on the dev store is compared blind with the static prototype before the full build goes ahead.

**Tech Stack:** Shopify Liquid (Skeleton theme, Shopify CLI 4.8.4), section and theme-block schemas, the `color_palette` and `video` settings, a product form for Add to bag, small per-component scripts, and Playwright for checks.

**Spec:** `docs/superpowers/specs/2026-10-20-afterglow-homepage-film-design.md`
**Prototype:** `.superpowers/brainstorm/homepage-1792523959/a5-the-film.html`

## Global Constraints

- Work in the theme repo `afterglow/` (private, its own git repo), on a new branch `feat/homepage-film`. Commit only when Aaron says.
- Use a standard section on a JSON template. Do not use the developer-preview `{% block %}` tag for this work; leave the existing layout files as they are, apart from the header overlay in Task 3.
- Colours: ground #080808, surface recessed #141414, surface raised #2B2B2B, muted #C0C0C0, text #EEECEA, gold #D8B260, after gold #BC6F4C, rose #893A50, deep violet #341D5E, magenta #BF15B7. The hairline is muted at 22%, mixed in CSS because palette colours cannot carry alpha.
- One rule: no hover, focus or press colour is lighter than its rest colour.
- Motion: 450 ms, curve 0.2, 0, 0.2, 1. No entrance animation, no parallax, no sound.
- Type: Instrument Serif 400 for display and the wordmark, widened to 150%. Space Grotesk 400 for everything else. Sizes, leading and tracking as in the spec's Typography table.
- Every piece of user-facing text goes through the locale file (`locales/en.default.json`).
- Square corners, no borders on the button, no shadows.
- Do not compose anything to make room for the ember. Do not show hours (such as 19:12) on this screen.
- No promo bar, discount pop-up or newsletter modal over the first screen.
- Film limits: wide cut under 4 MB, phone cut under 2 MB, as actually transferred for one loop.

## Review Focus

1. **No product picked, or the product deleted.** The section still renders the film and the line, and the product line and button are simply absent. Nothing shows "Liquid error" or an empty button. (Task 4)
2. **No film and no poster uploaded.** The section shows the #080808 ground and the type reads; no broken-video icon appears. (Task 5)
3. **Autoplay refused** (iOS Low Power Mode, data saver). The poster stays, and no browser play-button overlay appears over the film. (Task 5)
4. **Add to bag fails** (out of stock between page load and press, or a network error). The button returns to rest, a one-line message in muted text appears under it for 4 seconds, and the bag count does not change. (Task 4)
5. **An owner types a long line** (60 characters). It wraps balanced, stays within the left four columns on desktop, and never runs under the pause control or off screen on a 390 px phone. (Task 6)

---

### Task 1: Branch, palette and fonts

**Files:**
- Modify: `afterglow/config/settings_schema.json`
- Modify: `afterglow/config/settings_data.json`
- Modify: `afterglow/snippets/css-variables.liquid`
- Modify: `afterglow/locales/en.default.json`
- Test: `tools/theme_checks/palette.check.md`, a short written check run by script (see Step 4)

**Interfaces:**
- Produces: palette colour keys `ground`, `surface_recessed`, `surface_raised`, `muted`, `text`, `gold`, `after_gold`, `rose`, `deep_violet`, `magenta`, readable everywhere as `settings.colors.<key>`. Font settings `type_display_font` and `type_body_font`. CSS custom properties `--color-<key>`, `--color-hairline`, `--font-display`, `--font-body`, `--ease`, `--dur`, output by the css-variables snippet for every later task to use.

- [ ] **Step 1:** Create the branch `feat/homepage-film` in `afterglow/`. Start `shopify theme dev` against the dev store the theme syncs to, and note the preview URL in the task log.
- [ ] **Step 2:** Write the palette check: a Playwright script, `tools/theme_checks/palette.mjs`, that loads the preview homepage and reads the ten `--color-*` properties from the root. Pass means each one equals the hex in Global Constraints, `--color-hairline` resolves to #C0C0C0 at 22%, `--dur` is 450ms and `--ease` is the guide curve.
- [ ] **Step 3:** Run it. Expected: FAIL, because the properties don't exist yet.
- [ ] **Step 4:** Add one `color_palette` setting with the id `colors` and the ten keys, in the order listed, with the guide's hex values. Add two font pickers, Instrument Serif for display and Space Grotesk for body. If either face is missing from Shopify's font library, stop and tell Aaron rather than substituting one. Remove the Skeleton's `type_primary_font`, and output all the properties above from the css-variables snippet.
- [ ] **Step 5:** Run the palette check and `shopify theme check`. Expected: the check passes, and theme check reports no errors.
- [ ] **Step 6:** Commit (when Aaron says): "feat(theme): define the Afterglow palette and type".

### Task 2: Mechanism proof (gate)

The production mechanism, a Liquid section with a real header, differs from the static prototype, so it gets proved before anything else is built.

**Files:**
- Create: `afterglow/sections/film-hero.liquid`
- Create: `afterglow/templates/index.json` (replaces `templates/index.liquid`, which is deleted)
- Test: `tools/theme_checks/shoot.mjs` (screenshots at 1440 × 900 and 390 × 844)

**Interfaces:**
- Consumes: the Task 1 properties.
- Produces: the section type `film-hero`, with settings `video_wide` (video), `video_phone` (video), `poster` (image picker), `darken` (range, 0 to 100, default 60) and `product` (product). It accepts the blocks `@theme` and the section blocks `product_line` and `buy_button`. The section's root element carries the class `film-hero`.

- [ ] **Step 1:** Upload the stand-in film `brand/moodboard-media/gm8x-Nc.mp4` and its poster to Files on the dev store, so the proof uses the same footage as the prototype.
- [ ] **Step 2:** Build the section's layout only: the full-height film with the poster, both darkening gradients at the spec's stops, and the type block at the bottom left. The line, product line and button can be hard-coded text in this proof. Make the existing header float over the section on the homepage only, with Menu and Search on the left, the wordmark in the centre, and Account and Bag on the right, as in the spec.
- [ ] **Step 3:** Screenshot the dev-store homepage and the prototype at both sizes with the shoot script.
- [ ] **Step 4:** Send a fresh blind critic the two pairs, unlabelled and in random order, and ask: "Are these the same design? If not, name the single biggest difference." Pass means the critic says they are the same, or names only a difference caused by the stand-in footage's frame.
- [ ] **Step 5:** If it fails, fix the build toward the prototype and repeat Step 4. Do not carry on to Task 3 until it passes.
- [ ] **Step 6:** Commit (when Aaron says): "feat(home): prove the film hero on the theme".

### Task 3: Header over the film

**Files:**
- Modify: `afterglow/blocks/header.liquid`
- Modify: `afterglow/layout/theme.liquid` (the homepage marker only)
- Test: `tools/theme_checks/header.mjs`

**Interfaces:**
- Consumes: the `film-hero` section.
- Produces: the header overlay, active only when the homepage's first section is `film-hero`. On every other page the header renders as before.

- [ ] **Step 1:** Write the header check. On the homepage at 1440 × 900, the header sits over the film with no ground behind it; the wordmark is centred, set in the display font at 26 px and widened 150%; the four links show. At 390 × 844 only Menu, the wordmark (22 px) and Bag show. On `/collections/all` the header is not overlaid. Every link and the wordmark has a tap area of at least 44 × 44 px.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement the overlay and the phone reduction. Search and Account move into the menu on phones. The bag count reads from the cart.
- [ ] **Step 4:** Run the check. Expected: PASS.
- [ ] **Step 5:** Commit (when Aaron says): "feat(header): float the header over the homepage film".

### Task 4: The three blocks and Add to bag

**Files:**
- Create: `afterglow/blocks/line.liquid` (the reusable theme block, with a preset)
- Modify: `afterglow/sections/film-hero.liquid` (the `product_line` and `buy_button` section blocks, the default preset, and replacing the hard-coded text)
- Create: `afterglow/assets/film-hero-cart.js`, or the section's own script tag
- Modify: `afterglow/locales/en.default.json`
- Test: `tools/theme_checks/blocks.mjs`

**Interfaces:**
- Consumes: the section settings from Task 2 and the bag count element from Task 3.
- Produces: the theme block `line` with settings `text` (default "Breathe in the last of the sun.") and `size` (a select of `xl`, `x3` and `x4`, default `x4`, mapping to the type scale's 31.25 / 48.83 / 61.04 px top sizes, all 39 px on phones). The section preset is named "Film", with the blocks line, product_line and buy_button in that order.

- [ ] **Step 1:** Write the blocks check:
  - The line block appears in the editor's block picker under "Line".
  - The product line reads "Afterglow · Eau de parfum · 50 ml" when built from the picked product's title, product type and the size option.
  - The price shows in the store's money format.
  - Pressing Add to bag adds one item, raises the bag count by one, and goes to `/cart`. The W4 drawer replaces this redirect later.
  - The label reads "Adding" while the request runs, and the button ignores further presses.
  - With a sold-out product the button reads "Sold out", is #2B2B2B with #C0C0C0 text, and cannot be pressed.
  - With no product picked, neither the product line nor the button renders.
  - When the add request fails, the button returns to rest, a muted one-line message shows for 4 seconds, and the count is unchanged.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement the three blocks, the product form and the button states exactly as the spec's States section describes. The button fill goes from #EEECEA at rest to #C0C0C0 on hover and press. Focus is the same darkening plus a 1 px #C0C0C0 ring 4 px outside the button. It is at least 48 px tall.
- [ ] **Step 4:** Run the check. Expected: PASS.
- [ ] **Step 5:** Commit (when Aaron says): "feat(home): line, product line and buy blocks".

### Task 5: The film's behaviour and weight

**Files:**
- Modify: `afterglow/sections/film-hero.liquid`
- Create: `afterglow/assets/film-hero.js`, or the section's own script tag
- Test: `tools/theme_checks/film.mjs`

**Interfaces:**
- Consumes: the `video_wide`, `video_phone` and `poster` settings.
- Produces: a pause control button with the class `film-hero__control`, whose label comes from the locale keys `film_hero.pause` and `film_hero.play`.

- [ ] **Step 1:** Write the film check. Each item runs at the size named:
  - **Rendition, 1440 px:** the video file downloaded comes from the video's list of sources at 1080p or below, not the HD default. One loop of the stand-in transfers under 4 MB.
  - **Rendition, 390 px:** with a phone cut set, the phone cut is what loads, and one loop transfers under 2 MB.
  - **First paint:** the poster is preloaded. The line and button are visible before any video byte arrives.
  - **Reduced motion:** with the system's reduced-motion setting emulated, no video starts and the control is hidden.
  - **Pause:** pressing the control pauses the film and the label reads Play. Pressing it again resumes.
  - **Off screen:** the film pauses when scrolled out of view or when the tab is hidden, and resumes on return, unless the visitor paused it.
  - **Autoplay refused:** with autoplay blocked, the poster stays and no browser play overlay shows.
  - **Nothing uploaded:** with no film and no poster, the #080808 ground shows, the type reads, and no broken-media icon appears.
  - **Darkening slider:** at 0 there's no darkening. At 100 the darkening is at full strength, which is the spec's 50% top and 85% bottom; the slider scales those two.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement. Pick the source from the video's sources list by height instead of using the default video output, and if no source is 1080p or below, use the lowest. Play muted, looping and inline. Do not show native controls.
- [ ] **Step 4:** Run the check. Expected: PASS. Record the measured transfer sizes in the task log.
- [ ] **Step 5:** Commit (when Aaron says): "feat(home): film playback, weight and fallbacks".

### Task 6: Responsive, the one rule, and the editor

**Files:**
- Modify: `afterglow/sections/film-hero.liquid` (layout fixes the checks surface)
- Test: `tools/theme_checks/responsive.mjs`, `tools/theme_checks/one-rule.mjs`

- [ ] **Step 1:** Write the responsive check at 390 × 844, 768 × 1024, 1280 × 800, 1440 × 900, 1920 × 1080 and 844 × 390 (a phone turned sideways):
  - The section is the stable visible height and at least 560 px. The 560 px floor is lifted for 844 × 390.
  - There's no horizontal scroll.
  - The type block sits 20 px in on phones and 32–52 px in above that. The line stays at 61 px from 1440 px up.
  - On phones the button is in the bottom third of the screen and the control is top right under the nav. Above that, the control sits bottom right, level with the button.
  - The safe-area inset is added at the bottom.
  - Review Focus 5: a 60-character line wraps balanced and collides with nothing.
- [ ] **Step 2:** Write the one-rule check. For every link, the button and the control, read the computed colour at rest, on hover, on focus and on press. Pass means none of the other three is lighter in OKLCH lightness than rest.
- [ ] **Step 3:** Run both. Expected: any failures point at layout faults. Fix them in the section.
- [ ] **Step 4:** Run both again. Expected: PASS.
- [ ] **Step 5:** Editor check, the W3 Sunday task. In the theme editor, as a non-technical owner would:
  - change the line's text and size
  - swap the product
  - move the darkening slider
  - upload a new poster
  - reorder the product line and the button
  - add a second Line block from the picker.
  Note anything that needed knowledge of the code. Pass means nothing did.
- [ ] **Step 6:** Commit (when Aaron says): "fix(home): responsive and state checks pass".

### Task 7: Judge against the floor, then bank it

- [ ] **Step 1:** Push to the dev store and look at it cold: Aaron opens it on his phone and laptop.
- [ ] **Step 2:** Run fresh blind critics on the dev-store screenshots: one critic against Byredo, one against Heretic, labels stripped. Pass means the build wins both. With the stand-in film this is expected to fail on "no bottle". Record the result, and do not change the design to chase it.
- [ ] **Step 3:** When Aaron's Higgsfield film exists (see the spec's Footage brief), upload both cuts and the poster in the editor and rerun Step 2. This is the pass that counts.
- [ ] **Step 4:** Capture the homepage for the content bank: a 1440 × 900 and a 390 × 844 still, plus a short screen recording of the film running. Add it to the Notion content bank as a toggle with the status "Banked" ([[shopify-studio-notion-tracker]]), as craft only.
- [ ] **Step 5:** Log the weekend's output on the Weeks row in Notion: "first screen built; judged against Byredo and Heretic".
