# Afterglow Ember: Design Spec

**Date:** 11 Oct 2026
**Status:** approved by Aaron, 11 Oct 2026 (with option 1 for the guide wiring and a higher-resolution ember). Revised the same day after a blind test against the references: lava-lamp light texture and the statue's stop (approved at v23). The Ember page (§4.1, direction A′, on deep violet) and four feasibility additions (touch stop, 8-bit age range, idle, print) were approved the same day.
**Reference build:** [2026-10-11-afterglow-ember-reference.html](2026-10-11-afterglow-ember-reference.html) (the approved mockup, v23). Every number below is taken from it. Open it over a local server (`python3 -m http.server`), not as a file, because it loads Three.js as a module.

## 1. What it is

A cursor-driven ember that lives behind the content of the Afterglow Shopify homepage and every page of the brand guide. Moving the cursor lays down a hot, saturated body in the colour of the page beneath it. The body has a teardrop head and a thin tapering tail. When the cursor stops, the head coasts on and slows while the tail end runs forward to meet it; they come to rest together and the last of it shrinks to a dot. Cards and text near the ember catch its light.

It is the brand's one accent of contrast. Everywhere else, chroma stays flat at 0.110.

## 2. Behaviour

### 2.1 Input

| Input | Rule |
|---|---|
| Mouse or trackpad | The ember follows the pointer in real time. Speed drives heat: any movement lights it, and faster movement adds heat. |
| Touch devices (`pointer: coarse`) | Scroll speed stands in for cursor speed. The ember sits at the last touch point. A stop is the end of scrolling, momentum included: the same 34 ms with no movement, then the same dissolve (§2.3). |
| `prefers-reduced-motion: reduce` | One ember is held still at the pointer. It has no trail, no ripple and no animation. |

### 2.2 The body

The ember's heat is held in a field with two layers. Its resolution is set in §2.8. Each frame, it is written along the segment from the last pointer position to the current one, so the trail stays continuous at any frame rate. All fading is timed in seconds, not frames.

| Layer | Width (Gaussian variance, screen-aspect units) | Build | Cools while moving | Cools once stopped |
|---|---|---|---|---|
| Head | 0.0022 | Additive (×1.3 per frame), so it swells into a teardrop | 0.935 per 1/60 s | Held (no cooling) until the stop ends, then cleared |
| Tail | 0.00035 (a thin line) | Maximum, never additive, so older trail is cooler and thinner | 0.955 per 1/60 s | Held (no cooling) until the stop ends, then cleared |

- **Age.** A second field records, for each point, the seconds since the ember passed it. It is interpolated along each frame's segment so it runs smoothly down the path, and it also records the point's distance from the path's centre line and the speed at that moment. It is written within 0.081 of the path (screen-aspect units), and only ahead of each segment's start, so a path that curves back never re-ages older trail.

- The body is wherever the hotter of the two layers crosses a threshold of 0.2.
- The shape drifts very slightly in the direction of travel (a 0.003 advection step with velocity damping of 0.9).

### 2.3 Stopping: the statue's dissolve

Taken from the Unicorn Studio statue reference (assets.unicorn.studio/media/inspiration/statue.mp4, in the feature-design standards file): the smear appears and dissolves cleanly, in one continuous motion.

- **Stop.** A stop is 34 ms with no pointer movement.
- **One stop time.** Everything is timed to T = 0.25 + 0.75 × c0 seconds, where c0 is the age at which the moving tail visibly ends: 0.58 s for a full trail (where 0.955 per frame meets the 0.2 threshold), or the stroke's length if it is shorter. A full trail gives T ≈ 0.69 s.
- **The head coasts.** From the stop it carries on along its last direction at its last speed (capped at 8 px per frame), and that speed falls steadily to zero at exactly T. It keeps laying down the body as it goes. The card and text light follow it.
- **The tail end runs in.** The shape holds at full width (no cooling) while the tail end runs forward along the path. It leaves from exactly where the moving taper ended, at the pace it had (one second of age per second), and gathers pace evenly so it reaches the head's resting point at exactly T: in age terms, `cut = c0 − t − (c0 ÷ T²) × t²`.
- **They meet and go out.** The head and the tail end come to rest at the same point at T. The last of the body shrinks to a dot, and the field is cleared 60 ms later.
- **The cut.** The cut is its own edge, anti-aliased over at least a pixel, with no marker outline on it. Its sides go a little before the centre line, so the end is a rounded cap (offset = distance² ÷ (2 × 0.07 × speed), at most 0.3 s).
- **The needle.** The thin tail runs slightly ahead of the cap on its centre line, so a short needle shows at the cut end in the first frames after the stop. Aaron likes it; it stays.
- **Nothing pauses, jumps or breaks off.** No frame of the stop holds still, and no piece vanishes ahead of the cut.

### 2.4 Colour

- **Base colour.** The ember takes the colour of the page beneath it at each point (see §3).
- **The ember's colour.** That colour is pushed to high chroma: `hot = L + (base − L) × (1 + 3.4 × max(heat, 0.75))`, where L is Rec. 709 luma. The `max` keeps the tail at the same intensity as the head.

### 2.5 Surface: Aaron's water-button shader

This is taken from `StylizedShadowEngine` (in `Desktop/AGENTS/shader-demo`) and carries three of its four noise layers. The paper grain and the halo are excluded.

| Layer | Original | On the ember |
|---|---|---|
| Liquid | `noise3d(p × 4 + t × 0.8)` | **Lava-lamp light** (revised; it replaced the ink blobs, which read as leopard print). Domain-warped noise at scale 19, drifting upward at 0.49 per second, warp speed 0.22 and 0.3. Small, sparse molten globs (soft cut from 0.60 to 0.74), every tone light: the melt at 0.93 of the ember colour, the globs 26% of the way to white and ×1.06. Internal glow `core × noise³ × 0.9`. The globs also bump the silhouette outward by up to 0.0025 of the screen. |
| Surface jitter | `noise3d(p × 30 + t × 4) × 0.003` | Edge jitter of ±0.0015 of the screen at scale 30, speed 4. Jitter and bumps are measured in screen distance (heat over its slope), so a shallow heat slope can never fragment the edge. |
| Outline jitter | `noise3d(p × 80) × 0.1` | Outline width varies by ±0.03 at scale 80, held still. |

**Shading**
- **Normal:** the heat gradient gives the normal.
- **Light direction:** (2, 4, 5).
- **Cel bands:** as in the original, `step(0.1, diff) × 0.4 + step(0.5, diff) × 0.5 + 0.1`, with each step smoothed over one screen pixel.

**Rim and outline**
- **Rim:** `fresnel³ × 2.5 × 0.6`, plus 0.6 of the rim again after the outline.
- **Marker outline:** dark (0.03), drawn where heat is between the threshold +0.02 and +0.09, offset by the outline jitter. It thickens as the ember cools, so the end of the tail reads as an ink stroke. Aaron chose this over a fixed-width line. It is capped at about 5 px wide (0.0035 to 0.006 of the screen in from the edge); past that it tore into shards.

### 2.6 Edge ripple

**Where it runs**
- Only at the head. After a stop it fades out over T, as (1 − t ÷ T)².
- In a band just outside the silhouette, masked by distance from the pointer (Gaussian variance 0.006).

**What it does**
- Rings run outward (`sin(heat × 90 − t × 9)`).
- They displace the page colour by up to 0.045 of the screen along the heat gradient.
- They shade it by ±26%.
- They raise its chroma by up to 2.4× where the ripple is strongest (`L + (c − L) × (1 + band × 1.4)`).

### 2.7 Light on cards and text

**What gets lit**
- Cards and text opt in by selector.
- Each element is measured against the pointer, using the nearest point of its box.

**How strongly**
- Intensity is `min(1, 1.3 × heat ÷ (1 + (distance ÷ 140 px)²))`.
- It is eased at 0.12 per frame, so it rises and falls like light rather than switching.
- The light colour is the ember's colour at the pointer.

| Element | Treatment |
|---|---|
| Card rim | A 2 px border lit by a radial gradient centred on the ember's position, with stops at 100%, 45%, 10% and 0% across its radius. The radius is 156 + 156 × heat px. The rim is brightest at the edge point nearest the ember and falls off around the card. |
| Card glow | A soft radial wash inside the card from the same point (screen blend: 0.2, then 0.05, then nothing), plus a 24 px outer glow at 0.32 × intensity. |
| Text | Each glyph's edge facing the ember takes a 1.5 px text-shadow in the ember colour at 0.9 × intensity, plus a 10 px glow at 0.35 × intensity. |

Nothing is cast onto cards or text: no shadows, no darkening.

### 2.8 Resolution: never pixelated

The reference build's 160 × 100 field and 1.5× pixel cap showed steps on the edges, which is not acceptable.

- **Field size.** The field is a quarter of the viewport's CSS size on each axis, at least 360 × 225 (225 × 360 on a portrait screen, so a phone's texels stay square). At 1440 × 900 that is 360 × 225; at 1920 × 1080 it is 480 × 270; at 390 × 844 it is 225 × 360. It is reallocated only when that size changes, so a phone toolbar showing or hiding keeps the trail.
- **Field precision and filtering.** Half-float (WebGL2 filters these linearly as standard). If half-float targets are unavailable, the engine falls back to 8-bit targets and samples the field with a 4-tap bilinear blend in the shader, so filtering never drops to nearest.
- **Canvas.** Rendered at the device pixel ratio, capped at 2.
- **Edges.** The body edge, the cut and the cel bands are each anti-aliased over at least one screen pixel, using `fwidth`. The heat-based outline keeps its behaviour (§2.5) within its 5 px cap.
- **Age field.** The same size and precision as the heat field. On the 8-bit fallback, age is stored over a 0–2 s range, which covers the longest stop (T = 1 s).
- **Check.** At 1440, 1920 and 390 px on a 2× display, no stair-stepping is visible on the head, the tail tip, the outline, the cut or the cel bands, including the last frames of a stop.

### 2.9 What it must not do

- **No shadows** of any kind. The dark pocket and cast shadows were tried and removed.
- **No ripple or frosted grain** across the body or trail. Ripple appears at the head only.
- **No paper grain and no halo** from the original shader.
- **No round head.** The head is the teardrop built along the path.
- **No head that freezes, or fades separately** from the tail. It shrinks to a dot only as the tail meets it.
- **No hold after a stop.** The head never sits still while the tail runs in, and the tail end never waits before it leaves.
- **No pop.** Nothing vanishes ahead of the cut, and the tail end never jumps.
- **No pattern that reads as print.** The liquid is light (globs brighter than the melt), never dark spots.
- **No flat or full-card wash on cards.** Their light is a rim and a faint glow only.
- **No dependence on the ember for the page to render.**

## 3. Integration

### 3.1 One engine, two hosts

`EmberEngine` keeps `StylizedShadowEngine`'s shape:
- `constructor(container, options)`
- `init`
- `setupListeners`
- `onWindowResize`
- `animate`
- `dispose`
- `getFragmentShader`

It runs on Three.js 0.160.0.

Options that differ by host:

| Option | Shopify homepage | Brand guide (option 1, chosen) |
|---|---|---|
| `colourAt(x, y)` | The fall over the whole document: gold 0%, after gold 30%, rose 60%, deep violet 84%, #080808 95–97.2%, magenta #BF15B7 99.4%. | The ground of the sheet under the point, read from that sheet's own gradient. |
| `lit` | Product cards, section headings, body copy and prices. | Everything on every sheet but the cover (Aaron, 11 Oct): panels, tiles, colour swatches, product mockups, the fall band and photographs take the rim and glow; every piece of text takes the edge light. |
| `stops` and timing | Shared defaults (§2). | Shared defaults (§2). |

**Guide wiring (option 1, chosen).** The sheets become transparent, and the engine draws every sheet's ground from its colour source. Each sheet's gradient is read once from the page at start-up and on resize, and the canvas draws it under the content. The page is still complete without the engine: when the engine has not started, has failed, or WebGL is unavailable, the sheets keep their own CSS grounds. Grounds are only made transparent after the engine's first frame has been drawn.

### 3.2 Files

**Engine**
- `brand/ember/ember-engine.js`: the engine, an ES module. It is shared, and both hosts copy it at build time. (`site/` is the portfolio site, so the engine stays out of it.)

**Shopify, in the `afterglow/` theme**
- `assets/ember-engine.js`: a copy of the shared engine.
- `snippets/ember.liquid`: the container and the deferred loader. It loads Three.js and the engine only after first paint, and only when WebGL is available.
- `layout/theme.liquid`: renders the snippet once, before `</body>`.
- `snippets/css-variables.liquid`: gains the fall as a CSS gradient, so the page is complete without the ember.

**Brand guide**
- `tools/density_b_family.py`: inlines the engine, adds the new Ember page, and applies the rule changes (§4).

### 3.3 First paint, performance, fallbacks

**First paint**
- The page is complete in HTML and CSS: the fall background, all content and all colour.
- The ember is an enhancement added after first paint. It never hides content, and it uses no opacity-zero start state.

**Performance**
- Three.js is about 150 KB compressed. It loads deferred and is never render-blocking.
- The device pixel ratio is capped at 2 (§2.8).
- Rendering pauses when the tab is hidden.
- Rendering idles once the field is empty after a stop, and resumes on the next pointer or scroll movement.

**Fallbacks**
- **No WebGL, or the engine throws:** nothing is added and the page is unchanged.
- **Reduced motion:** the still ember described in §2.1.
- **Print:** no canvas is printed, and every sheet prints on its own CSS ground.

## 4. Brand guide changes

| Where | Change |
|---|---|
| The one rule (page 06, art direction, page 13 hover note) | **"The light only brightens where the ember is."** Hover, focus and active states still deepen and never lighten. Photographs are still never brightened in post. |
| Shadow (page 06) | Unchanged: none. The ember casts no shadow. |
| Chroma (page 03) | Add: chroma is flat at 0.110 on every stage. The ember is the one exception, an accent of contrast that raises the chroma of the colour it sits on. |
| New page: The ember | Page 12, after the four stage spreads and before Use and misuse, on the deep violet slice. Laid out as in §4.1. |

### 4.1 The Ember page (direction A′, approved 11 Oct 2026)

**Mockup:** `ember-page-directions.html`, sheet A′, in the brainstorm session. Held to Frame.io and to Bob Beauté by Kurppa Hosk (`design-standards.md`).

**What it does.** The page teaches the ember by letting the reader use it. The ember is the page's picture: there is no diagram, video or still of it. How it plays with the guide is shown on the page itself: the wordmark and the label line catch its light.

**Ground and place (chosen by Aaron, 11 Oct 2026).** Deep violet. The page is page 12, after the four stage spreads and before Use and misuse. With 13 sheets on the fall, that slice runs from #321C5B at the top to #1D1231 at the bottom, and the ember here is #5304E4. This was chosen over the rose slice after Grid, which the blind critic faulted for low contrast against Frame.io and Bob Beauté.

**Layout.** This is the guide's two-column sheet: a title column on the left and a field on the right.

| Element | Content and type |
|---|---|
| Title | "The ember", in the guide's sheet-title size. |
| Lead, two sentences | "The one accent of contrast. It follows the cursor in the colour of the page beneath it, and goes out when the cursor stops." Then: "Panels and type catch its light on the side facing it. Nothing is cast." In the guide's lead style. |
| Photograph | R6euaYP, a hand lit by one streak of warm light. It fills the rest of the title column, cropped from 40% down. It is used nowhere else in the guide. |
| Never line | "Never a shadow, a dark pattern, a piece that breaks off, a stepped edge, or a page that needs it to render." In small muted text under the photograph. |
| Field | The open right column with no panel or plate on it. The stretched wordmark "Afterglow" is set in #EEECEA, centred vertically, 4% in from the left, fluid from 44 px to 200 px. It is the page's one hero. |
| Label line | Across the foot of the field, under a hairline rule of #EEECEA at 22%. It has three parts. Left: "Live", in 11 px uppercase tracked at 0.14 em. Centre: "Move, and it lights. Stop, and in 0.7 seconds it goes out.", in the display serif at 20 px. Right: two 10 px chips with "#321C5B → #5304E4", in 11 px uppercase. |
| Footer | The guide's standard footer: Motion, with the page number. |

**What catches the light.** Everything: the title, the leads, the wordmark, the three parts of the label line, and the photograph (Aaron, 11 Oct). The photograph file itself is still never brightened in post (§4).

**Hierarchy.** The eye goes to the wordmark first, then the label line, then the title column. The page uses three type sizes: the wordmark, the title and the 20 px line, with everything else at body or label size.

**Responsive** (the guide's own breakpoints)

| Width | Behaviour |
|---|---|
| 993 px and up | A fixed-height sheet as on every other page. Two columns. The label line sits on the foot of the field. |
| 577–992 px | One column, with the sheet at its natural height. The title, two leads, photograph (4:3) and Never line come first, then the field. The field is at least 300 px tall with the wordmark centred in it, and the label line stays on its foot. |
| 576 px and down | As above, at the guide's phone padding. The title follows the guide's phone size. The wordmark's floor of 44 px keeps it inside a 390 px screen with no sideways scroll. The label line stacks into three left-aligned lines under the wordmark instead of sitting on the field's foot. |
| Touch | There is no cursor, so scrolling drives the ember (§2.1). The page reads in full without it: the label line says what it does. Nothing on the page is a control, so there are no touch targets. |
| Print | The page prints on its CSS ground, with no ember. The label line and the Never line carry the rules on paper. |

**What it must not do**
- Add a second display element in the field (a black slab, a reading plate, a second heading).
- Use more than one kicker or label line.
- Show the rules as a Do and Don't grid.
- Reuse the photograph elsewhere in the guide, or brighten the file in post.
- Depend on the ember to explain itself. With the ember off, the page still says what it does.

Adding the page renumbers every later page. Cross-references ("page 03", "page 07") and `tools/check_b1.py` are updated to match.

## 5. Testing

**Automated (Playwright, at 1440, 768 and 390 px)**
- The guide's existing `check_b1.py` passes.
- The Shopify homepage and the guide render fully with JavaScript disabled.
- With `prefers-reduced-motion`, the canvas holds one still ember and draws no trail.
- With no WebGL, no canvas is added and there are no console errors.
- Nothing scrolls sideways, and the canvas never captures pointer events.
- **Stop, frame by frame** (on a GPU, in a hidden browser, with a scripted sweep at a fixed speed): the tail end advances in every frame from the last movement until it meets the head; the head moves in every frame until T; nothing vanishes ahead of the cut; the field is empty by T + 60 ms.

**Theme**
- `shopify theme check` passes.
- The section and snippet validate in the theme editor.

**By eye, on Aaron's screen**
- The look and timing match the reference build.
- My test browser renders without a GPU, so it cannot judge smoothness or timing.

## 6. Open items

- **Wordmark export:** separately, the stretched wordmark should be exported as outlined SVG before production. This is noted in the guide work and is not part of the ember.
