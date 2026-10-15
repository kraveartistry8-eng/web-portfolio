# Afterglow Ember, Light Revision: Design Spec

> **Abandoned, 13 Oct 2026.** Aaron: the build "looks and behaves nothing like what we prototyped". The hour-lite guide was reverted to v23. Why it failed: the prototype's look comes from light multiplied by the page's own pixels across the whole trail, but this design split it into a faint WebGL ground plus per-element CSS gradients at the cursor only, so surfaces never carried the trail. The prototype's numbers were carried into that different model, a brightness cap the prototype never had was added and bent the look, and no blind side-by-side against the prototype was run before building. The feature-design workflow is being rerun from Step 1. This file is a record, not a spec to build from. The code is archived outside the repo.


**Date:** 13 Oct 2026
**Status:** design approved by Aaron, 13 Oct 2026 (direction "4 + 5, stronger"; keep WebGL, option B). Revised the same day after his review: photographs light at the edge facing the light, and the head glides to rest after a stop (§3.2). This document awaits his review.
**Supersedes:** §2.2 to §2.7 and §2.9 of [2026-10-11-afterglow-ember-design.md](2026-10-11-afterglow-ember-design.md). Every other section of that spec stands: input (§2.1, with the changes below), resolution (§2.8), integration (§3) and the guide wiring.
**Reference prototype:** [brand/ember-directions/a2-family.html](../../../brand/ember-directions/a2-family.html), button "4 + 5, stronger + glide" (`c3`). Open it over a local server (`python3 -m http.server`), because it reads page pixels. Every number below comes from it.
**Frozen:** the v23 ember stays as it is in `brand/ember/v23/` for reuse elsewhere. Nothing here changes it.
**Isolation (Aaron, 13 Oct):** this has no effect on the older builds. The light revision is a separate engine in `brand/ember/light/`, with its own maths, tests and bundle. Only the hour-lite guide (`build_lite()`) swaps it in. The current engine in `brand/ember/`, `tools/density_b_family.py` and every older guide file stay byte-for-byte unchanged. Where §4 says "stays" or "changes", it describes the new engine relative to the v23 engine it was copied from, not edits to that engine.

## 1. Why

Aaron, 13 Oct: the v23 ember "does not match the vibe of this brand. It looks too cartoonish." It was built from cartoon parts: cel bands, a dark marker outline that thickens into an ink stroke, chroma pushed 3.4 times, a glossy rim and molten globs. It read as a sticker on top of the page. The brand is light on skin and a soft-focus figure on the cover, so the ember becomes light rather than an object.

## 2. What it is

The ember is light that touches what is already on the page. Where the cursor moves, the type, photographs, swatches and cards nearest it catch a small, warm light on the side facing it. The ground under it warms only faintly. Each touch lasts 0.9 s. It is warm when fresh and cools down the fall as it fades, through rose to deep violet: warm to cool, never back.

It has no edge, outline, shading band, highlight, ripple, grain or texture. When the cursor stops, the head of the light glides on and slows smoothly to rest, so it never halts dead; then everything laid down finishes fading.

## 3. Behaviour

### 3.1 A touch of light

Each pointer movement lays down touches along the segment from the last position to the current one, one every 10 px, so the light stays continuous at any speed and frame rate.

| Property | Value (from the prototype) |
|---|---|
| Life | 0.9 s from the moment it is laid down |
| Radius | (52 + 40 × speed) px, growing to 1.25 times that over its life. Speed is in px per ms, capped at 1.5. |
| Profile | Radial: full strength at the centre, 0.4 of it at half the radius, nothing at the radius |
| Strength | 0.42 × (1 − age)^1.3, where age runs from 0 to 1 over the life. Touches add together. |

### 3.2 The glide: coming to rest

Aaron, 13 Oct: a light that halts the instant the cursor does reads as robotic. The stop is gradual, even though the whole sequence is fast.

- **Stop.** A stop is 34 ms with no pointer movement.
- **Direction and speed.** The head's velocity is smoothed over the last movements (each new reading weighted by half). At the stop, the head carries on in that direction, starting at that speed, capped at 0.6 px per ms.
- **Slowing.** Its speed falls as `v0 × (1 − t ÷ T)²` over T = 0.32 s, so it eases to rest with no step. The furthest it can travel is `v0 × T ÷ 3`, about 64 px.
- **Light.** It keeps laying touches every 10 px as it goes. Their size follows its falling speed (§3.1), so the light narrows as it settles.
- **Interrupted.** Any new movement ends the glide at once, and the light carries on from the pointer.
- **Slow stops.** A head moving slower than 0.02 px per ms when the cursor stops does not glide.
- **Reduced motion.** No glide.

### 3.3 Colour: warm, then cooling

- **Fresh colour.** The page colour under the touch, moved 35% toward gold of last light (#D8B260), then lifted in chroma: `L + (c − L) × 1.5`, where L is Rec. 709 luma. On dark grounds it is also lifted in lightness (× 1.1, then + 8 of 255). On light grounds (luma over 140) it is not.
- **Cooling.** As the touch ages it walks down the fall: gold of last light, after gold, rose, deep violet, in equal thirds of its life. Its colour is the fresh colour mixed toward that cooled colour by `min(1, 1.4 × age)`, so it has fully cooled by 71% of its life, with the last 29% fading in deep violet.

### 3.4 Where it shows

**Surfaces carry it.** Type, photographs, colour swatches, product mockups, the fall band, panels and tiles catch the light. Each is lit faintly by the touches near it, at the point nearest the light:

| Element | Treatment |
|---|---|
| Type | The light is clipped to the letters: a radial gradient in the touch colour, centred on the light's position inside the element, painted through the glyphs (`background-clip: text`) over the text's own colour, which is kept in a variable so unlit text is unchanged. Only the strokes near the light warm. No text-shadow and no glow outside the glyphs. |
| Photographs | Light on the edge facing it (Aaron, 13 Oct): a soft band along the side of the photograph nearest the light, at the point nearest the light, fading into the image over 18% of its shorter side. Soft-light blended, so the image's own light areas take it most. The rest of the photograph is untouched. |
| Swatches, panels, tiles, mockups, the fall band | The same soft wash inside the box. No rim, no border light and no outer glow. |

**The ground hardly does.** In the WebGL field the same light is drawn at 40% of the surface strength, so the ground warms faintly and never reads as a shape. (Tuned 13 Oct by measurement against the prototype on page 11. Along the same stroke, the prototype raises the ground's OKLab L by 0.031 on average (0.045 at most). The starting 6% gave 0.004, and 40% gives about 0.030.)

**On light grounds** (gold and after gold) the ground is pale enough to catch the light as a surface would, as in the prototype on page 03. There it blends as soft light, which deepens colour rather than whitening it.

### 3.5 Never brighter than gold

No surface is lifted past gold of last light's lightness (L 0.781). The one rule still holds: the light only brightens where the ember is. Type is held tighter: its light takes the text's own OKLab lightness (the light's hue, with as much chroma as fits), so letters warm and never brighten. (Measured 13 Oct: clipping light to letters renders their edges with slightly more coverage. Edge pixels can then move toward their own letter's colour, never beyond it.)

### 3.6 Input

| Input | Rule |
|---|---|
| Mouse or trackpad | As §3.1. Any movement lights; faster movement makes larger touches. |
| Touch devices (`pointer: coarse`) | A touch at the touch point while the finger moves, and along the scroll while it scrolls. Each fades as usual. |
| `prefers-reduced-motion: reduce` | One still, faint light at the pointer at 40% strength in the fresh colour. No trail, no cooling, no growth. |
| Print | Nothing. Every sheet prints on its own CSS ground (unchanged). |

### 3.7 Idle

When the last touch has faded, rendering idles and resumes on the next pointer or scroll movement (unchanged from §3.3 of the v23 spec).

### 3.8 Responsive (responsive-design pass, 13 Oct)

| Range | Touch radius scale | Notes |
|---|---|---|
| 993 px and wider | 1 | As §3.1. |
| 577 to 992 px | 0.85 | Tablets: 44 to 95 px touches, at most 119 px grown. |
| 576 px and narrower | 0.75 | Phones: 39 to 84 px touches, at most 105 px grown, so a touch never covers more than about a quarter of a 390 px screen. |

- **The scale applies to everything measured in px:** the radius and its growth, element reach (twice a still touch), the age field's write reach, and the glide cap. On a phone the glide starts at most at 0.45 px per ms and travels at most 48 px. The 0.9 s life and the 0.32 s glide time do not scale.
- **Viewport height.** The canvas is held at the large viewport height, so a phone's toolbar showing or hiding never resizes it, and the light survives the scroll that hides the toolbar. Orientation change resizes it as before.
- **Pixel ratio.** The canvas is capped at 2 on fine pointers and 1.5 on coarse pointers. The ground and its faint light hold at 1.5, because nothing in them is a hard edge.
- **Cost.** The display shader returns the ground at once wherever the light is zero, and runs the colour and ceiling maths only where light falls. Most of the screen costs one texture read.
- **Surfaces on phones.** Light clipped to letters is applied only to elements lit at that moment, never to all text, so mobile Safari repaints only what is lit. The type, photograph and box treatments are the same as on desktop.
- **Input.** There is no hover on touch: a tap with no movement lights nothing. Moving a finger lays light along its path. Scrolling lays it at the last touch point (§3.6). There is no control to tap, so the light needs no touch target.

## 4. The engine

### 4.1 What stays

- `EmberEngine`'s shape, Three.js 0.160.0, the bundle step (`brand/ember/build.sh`) and the guide wiring that draws each sheet's ground from `groundAt`.
- The field size, precision, half-float targets with the 8-bit fallback, and the device-pixel-ratio cap (§2.8 of the v23 spec).
- The age field and its writing along each frame's segment, written out to the widest a touch grows (140 px).
- `lightElements()`'s measuring (nearest point of each box, all reads before all writes) and the `--li`, `--px`, `--py`, `--ec` variables.
- The failure path: no WebGL, or the engine throws, leaves the page unchanged.

### 4.2 What changes

| Part | v23 | Light revision |
|---|---|---|
| Field writes | Head (additive, ×1.3) and tail (maximum) layers | One field: the age field, which already records each texel's age, distance from the path and speed. The display shader draws the §3.1 profile from it, growing and cooling with age. The heat field and its pass are removed. Where paths cross, the newest light wins rather than adding (planning note, 13 Oct). |
| Cooling | 0.935 and 0.955 per frame, held during a stop | Strength from age (§3.1); no hold |
| Stop | Coast, tail runs in, cut, needle, dot (§2.3) | The glide of §3.2: the head slows smoothly to rest over 0.32 s, then the light fades on its own life. No cut, needle or dot. |
| Colour | Pushed chroma (`push`) or matched lightness (`match`, 1.2) | §3.3, from the page colour and the age field |
| Shader surface | Lava-lamp globs, edge jitter, outline jitter, cel bands, rim, marker outline | Removed. The fragment shader draws the ground plus the faint light only. |
| Edge ripple | At the head | Removed |
| Element light | Card rim, card glow, text edge shadow and glow | §3.4: light clipped to glyphs; a soft-light band on the near edge of photographs; a soft-light wash in boxes |
| Element colour | The ember colour at the pointer | The touch colour, cooling with that element's own fading light |
| Element fade | Eased at 0.12 per frame | Eased in at 0.12 per frame; out along the 0.9 s life, so its colour cools as its light falls |
| Options | `chroma`, `chromaScale`, `stopDetect`, `coastMax` | `chroma` and `chromaScale` removed; `stopDetect` kept (0.034 s); `coastMax` becomes `glideMax` (0.6 px per ms). Added: `glideTime` (0.32 s), `life` (0.9 s), `strength` (0.42), `groundGain` (0.4, measured; see §3.4). |

### 4.3 Maths to test (in `ember-math.js`)

`touchRadius(speed, age)`, `touchStrength(age)`, `freshColour(rgb, light)`, `cooledColour(fresh, age)`, `glideSpeed(v0, t)`, `glideDistance(v0, t)` and `lightTarget()` revised to the new radius. Each is tested in `ember-math.test.mjs` against values read from the prototype. The v23 functions the engine no longer uses are removed from the module, not left beside the new ones.

## 5. Guide changes

| Where | Change |
|---|---|
| The ember page (11), lead | "The one accent of contrast: a small warm light wherever the cursor moves, cooling down the fall as it fades." Second paragraph unchanged: "Type, panels, colour and photographs catch its light on the side facing it. Nothing is cast." |
| The ember page (11), label line | "Move, and it lights. Stop, and in 0.9 seconds it is gone." |
| The ember page (11), never line | "Never an object, an edge, a shadow, or a page that needs it to render." This also settles the open question about "a dark pattern". |
| The ember page (11), chips | The fresh colour and the deep violet it cools to on that page. |
| Colour reference (15) | "The ember is the one exception: a small warm light that raises the chroma of what it touches, then cools down the fall." |
| CSS | The v23 rim, card glow and text-shadow rules (`EMBER_CARDS`, `EMBER_TEXT` in `tools/density_b_family.py`) are replaced by the §3.4 treatments. |

## 6. Checks

- **Feel.** Side by side with the prototype's `c3` on pages 11, 06 and 03, at 1440 and 1920 wide: the same size, strength, life, cooling and glide, by eye. Aaron signs this off.
- **No dead stop.** Recorded at 60 fps, the head's speed after a stop falls over at least 15 frames with no frame-to-frame jump larger than the one before it.
- **Nothing drawn.** Mid-stroke and in the last frames of a fade, no edge, outline, band, highlight or step is visible at 1440, 1920 and 390 px on a 2× display.
- **Ceiling.** No lit pixel of type or ground exceeds L 0.781 unless it was already above it, measured from screenshots.
- **Cost.** Lighting the elements stays under 2 ms a frame on page 11 (`lightMs`), and the guide holds 60 fps while moving on a 2020 MacBook Air.
- **Responsive.** At 390 × 844 (coarse pointer, 3× display, emulated): touches measure 39 to 84 px, the canvas holds its size when the viewport height changes by 80 px, lighting the elements stays under 4 ms a frame, and only lit text carries the letter-clipped light.
- **Fallbacks.** No WebGL, reduced motion and print each behave as §3.6, and the guide is complete without the engine.
- **Tests.** `ember-math.test.mjs` passes, and the guide's tests pass.
