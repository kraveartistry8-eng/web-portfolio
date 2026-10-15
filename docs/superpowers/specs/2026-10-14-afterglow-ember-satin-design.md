# Afterglow Ember, Satin: Design Spec

**Date:** 14 Oct 2026
**Status:** the design was picked by eye by Aaron on 14 Oct 2026; this document awaits his review. Feature-design Step 6.
**Reference prototype:** [brand/ember-directions/satin-combined.html](../../../brand/ember-directions/satin-combined.html), version P2d with the satin at a third and the raking light at a third (its defaults). Serve it from the repo root (`python3 -m http.server 8765`), because it reads page pixels. Every number below comes from it. Where this spec and the prototype disagree, the prototype wins, and the spec is corrected.
**Supersedes:** the abandoned [2026-10-13-afterglow-ember-light-design.md](2026-10-13-afterglow-ember-light-design.md). Its §3.1 to §3.3 (the touch, the glide, the colour) are carried over unchanged as c3 (§3.2 below).
**Isolation:** the older builds are not affected. The v23 ember stays frozen in `brand/ember/v23/`, and every older guide file stays byte-for-byte unchanged. Only the hour-lite guide (`brand/2026-10-12-guide-hour-lite.html`) takes the new ember.
**Lesson from 13 Oct:** that build failed because it rebuilt the prototype with a different mechanism. Here, the production mechanism has to be proved beside this prototype in a blind side-by-side before any engine work (Step 7).

## 1. Why

Aaron, 13 Oct: the v23 ember "does not match the vibe of this brand. It looks too cartoonish." He wanted it more elegant and speaking the guide's own visual language. In the rerun (13–14 Oct) he chose:
- **c3** as the light;
- **the raking light (A)** from the Savee grazing-light film;
- **a satin ground** from the Symphony of Vines glacier title screen, where "the mountains are shaped by the cursor".

He then tuned all three by eye toward subtlety. Two quotes set the brief: "the effect is just way too intense it should be subtle", and the ripples "should contour the shape of the ember and only radiate a short distance from it".

## 2. What it is

The page ground is a sheet of satin in the page's own colour. Where the ember lies, it presses softly into the satin. Two broad, low swells roll out from its outline, no further than about 75 px. The type, panels, photographs and swatches on the page are printed on that satin: they take the swell's light and shade, and they bend a few px with it. As the ember cools the satin lies flat again, and the elements ease back true over about a second.

Over the satin, the ember is c3: a warm light that follows the cursor and cools down the fall. Over that, the raking light catches the edges of type, panels and photographs on the side facing the oncoming light.

Everything is quiet. Most of the page is still most of the time. Away from the ember, nothing moves.

## 3. Behaviour

### 3.1 Trigger and states

- **Trigger:** pointer movement anywhere on the page.
- **Idle:** the satin is flat, and the page looks exactly as drawn: no shading, no bend, no light.
- **Moving:** c3 lays light along the path (§3.2). The satin is pressed where that light lies (§3.3), and the raking light catches the edges facing it (§3.4).
- **Stop:** c3's head glides to rest over 0.32 s (§3.2). The light fades over 0.9 s.
- **Settling:** the press lingers on and fades over 1.7 s. The swells relax over about 2 s. The elements' bend eases back true over about a second (§3.5).
- **Back to idle:** after about 2.5 s with no movement, everything is flat again.

### 3.2 The ember: c3, unchanged

The ember is exactly c3, as specified in §3.1 to §3.3 of the 13 Oct spec:
- **Touches:** one every 10 px of travel. Each lives 0.9 s, with a radius of (52 + 40 × speed) px that grows 25%, and strength 0.42 × (1 − age)^1.3.
- **The glide:** after a stop of 34 ms the head glides on, starting at up to 0.6 px per ms, and eases to rest over 0.32 s.
- **Colour:** each touch starts as the page colour moved 35% toward #D8B260, lifted in chroma, then cools through after gold, rose and deep violet.
- **Surfaces:** the light is multiplied by the page's own pixels, so surfaces carry the trail.

### 3.3 The satin

**The cloth.** The satin is a woven sheet of cloth. It is held by an off-screen frame, 30% past every edge of the viewport, so where it is held is never seen. It is anchored so that it springs back flat. It is never dragged by the cursor.

**The press.** The ember's own shape presses into it:
- **The shape:** c3's light, softened by a 76 px blur.
- **Lingering:** the shape lingers after the light has gone, fading over 1.7 s.
- **Depth:** where the shape is at full strength, the cloth sinks by its full press depth. Around the rim, the cloth's stiffness lifts it into a low ridge. Its liveliness lets that ridge roll out as two broad swells.

**The cloth's character:**

| Property | Value |
|---|---|
| Pull back to flat | 0.35% per step, two steps per frame |
| Liveliness | 97% of its motion carried from one step to the next |
| Fold stiffness | 0.32, with a long-range stiffness at a third of that, so it makes a few broad swells and never pleats |
| Press depth | 17 units against a resting weave of about ±0.7 |
| Relief in the shading | × 3 |

**Where it shows:** only inside the ember's softened shape and its rim. The shape's soft edge reaches full strength at 60% of its peak. Outside it, the ground is untouched.

**Shading.** The satin is shaded in the ground's own colour, relative to the flat sheet, so at rest the ground is exactly as drawn:
- **Light:** from the upper left.
- **Sheen:** a low, wide sheen runs along the threads, which run across the page.
- **Crests:** lift toward a pale gold on light grounds, and toward a lighter version of the ground on dark grounds.
- **Troughs:** fall to 66% of the ground on light grounds and 42% on dark grounds.
- **Grain:** a fine grain of ±3% shows only on cloth that has moved.
- **Strength:** the whole shading shows at **a third** of its full strength.

### 3.4 The raking light: A, at a third

Light catches the edges of type, panels, swatches and photographs on the side facing the oncoming light, never the ground beside them.

**Edges:**
- An edge is measured at two widths, 1.5 and 3 device px, so it reads as a soft rim and not a drawn outline.
- Only edges facing the direction of travel take light. The far sides stay dark, so nothing is ringed.
- Thin strokes of small type on light grounds are spared (a stroke is thin if the ground returns within 4 px), so text stays crisp.

**Colour:**
- **On dark grounds:** the light is a warm gold, cooling down the fall as it ages.
- **On gold grounds:** it is paler than the ground, so it still reads as light.
- **Light type** turns gold on its lit edge rather than whiter.

**Timing and strength:**
- Each touch lives 0.9 s, with a radius of (56 + 40 × speed) px that grows 25%, fading as (1 − age)^1.3.
- The whole raking light shows at **a third** of its full strength.

### 3.5 Elements printed on the satin

Type, panels, swatches, the fall band and photographs all take the satin's light and shade, in their own colour, at the same third strength as the ground. Nothing is exempt: Aaron, 14 Oct, "keep the light effect on everything", including the colour swatches.

**The bend:**
- **Size:** each element bends with the slope of the swell under it, up to about 8 px at the steepest slope. That is ×3 the first setting, picked by Aaron.
- **Strength:** the bend is fixed. It does not grow with the satin's strength.
- **Easing:** it is smoothed on its own, through two easing stages in series:
  - **Gathering:** the bend gathers quickly, within about a fifth of a second.
  - **Releasing:** it lets go slowly. It eases back true over about a second, slowing as it settles, with no snap at the end.
- **Limit:** the bend never exceeds what the swell gives at that moment. When the swell is flat and the eased bend has released, every element lies exactly where it is drawn.

### 3.6 Order of the layers

1. The page, with its ground as satin and its elements printed on it (§3.3, §3.5).
2. c3's light over that (§3.2).
3. The raking light over both (§3.4).

The raking light reads the frame that c3 produced, so the edges it finds already carry c3's light.

## 4. Colour and visual details

| Thing | Value |
|---|---|
| The fall | gold of last light #D8B260 → after gold #BC6F4C → rose #893A50 → deep violet #341D5E |
| Satin crest on light grounds | the ground screened with (0.40, 0.34, 0.24) |
| Satin crest on dark grounds | the ground screened with 0.9 × itself + 0.08 |
| Light and dark grounds | dark below luma 0.22, light above 0.42, blended between |
| Raking light, warm | gold of last light screened with (0.18, 0.12, 0.05) |
| Raking light, pale (gold grounds) | gold of last light screened with (0.62, 0.55, 0.42) |
| Strengths | satin a third, raking light a third, bend about 8 px at most, c3 unchanged |

## 5. Typography

There's no new type. Type is never redrawn, recoloured or blurred by the satin: it only takes the satin's light and bends a few px, both eased. Small text must stay legible at every moment.

## 6. Responsive notes

**Viewport:**
- The satin, c3 and the raking light share one fixed layer covering the viewport.
- It is sized to the stable viewport height, so the mobile browser bar showing and hiding never rebuilds the cloth.
- The cloth is rebuilt only when the width changes or the device rotates, after the size has been still for 150 ms.

**Input:**
- **Mouse and pen:** as specified.
- **Touch:** a finger dragging across the page is the cursor while it is down. The ember never blocks scrolling: scroll gestures pass straight through, and the light simply follows the finger.
- **Taps:** a tap lays a single touch, so one press and its swells roll out from the tap.
- **Lifting the finger:** this is a stop, so the glide and the settle run as usual.
- **Hover:** nothing on the page depends on hover.

**Scrolling:**
- The satin is fixed to the viewport, not to the page.
- Scrolling does not press the satin.
- A swell that is still settling stays where it is on screen while the content scrolls under it. Its light and bend apply to whatever element is under it now.

**Sizes at 390 px wide (phones):**
- **Touch radii:** c3 and the raking light keep their sizes in CSS px. A touch is 52–112 px across at rest, since a finger moves slower than a mouse.
- **The press:** its rim blur drops from 76 to 56 px.
- **The bend:** its maximum drops from about 8 to 6 px, so a phone's smaller type stays legible.

**Performance tiers:**

| Tier | Cloth grid | Steps per frame | Device pixel ratio cap |
|---|---|---|---|
| Desktop | 120 × 72 | 2 | 2 |
| Tablet | 90 × 54 | 2 | 2 |
| Phone | 60 × 36 | 1 | 1.5 |

- **Precision:** shaders run at medium precision on phones.
- **Hidden tab:** all rendering and simulation pause.
- **Frame budget:** if the frame rate stays below 45 fps for 2 s, the ember steps down in this order:
  1. The elements' bend goes first.
  2. Then the satin's shading.
  3. That leaves c3 and the raking light, which are the floor.

  It never steps back up within the same visit.
- **No WebGL2:** c3 alone, as the 2D canvas it already is.

**Reduced motion:**
- No satin motion and no bend.
- No glide.
- c3's light still follows the pointer and fades. The raking light stays, because it is light, not movement.

## 7. What it must not do

- **No whole-page effect:** the satin moves only within about 75 px of the ember, and the rest of the page stays exactly as drawn.
- **No procedural pattern:** no stripes, rings drawn as rings, swirls, corduroy or ribbons. The folds come only from the cloth.
- **No cursor drag:** the cursor does not drag the cloth; the ember presses it.
- **No snapping:** nothing snaps back. The bend eases out, and the satin relaxes.
- **No harm to type:** no blur, smear or warp of type beyond the eased bend of about 8 px at most.
- **No more than a third:** neither the satin nor the raking light goes past a third of its prototype strength.
- **Nothing on the ground from the raking light:** it lands only on the edges of objects, never on the ground beside them, and no element is ringed.
- **No brightness flash:** nothing appears or disappears in a single frame.
- **No hold-up:** the ember never delays scrolling, clicks or text selection.
- **No harm to older builds:** no older guide file, and not the v23 ember.

## 8. Known gap

There were two blind rounds against the glacier title screen, on 14 Oct: rounds 10 and 11. P2d lost both, 3–0 each time.

**What the critics said:**
- **Ours:** at this strength the swell reads as "a soft blurred smear rather than folded, lit cloth". It has no fold crest and no shadow side.
- **The title screen:** its folds smear the headline. Its settle dissolves into fog. In one pair it reads as sand or ice rather than satin.
- **On legibility and settling,** they put ours ahead.

**Aaron's choice:** he saw the crisper alternative (P2e, a narrow crest with a firmer trough), found it "too crisp", and chose P2d's softness knowingly. So the bar for this feature is the reference's behaviour rather than its intensity: a cursor that shapes the ground, a press that follows the ember's outline, and a calm settle. Judged that way, the gap the critics name is a deliberate choice, not a defect.

## 9. Feasibility (Step 7, 14 Oct 2026)

**The mechanism.** The live guide is rasterised in the browser, one sheet at a time. Each sheet is serialised with the page's own stylesheet into an SVG foreignObject, with its Google fonts and photographs inlined. Viewport-height units are pinned to the window, so the browser lays it out exactly as the page.
- **Pipeline:** the prototype's pipeline then runs unchanged on a page view and a ground view of the window, built from those images.
- **The real HTML:** it stays in the page, invisible, for links, selection and screen readers.
- **Proof:** [brand/ember-directions/satin-live.html](../../../brand/ember-directions/satin-live.html), with the rasteriser in `brand/ember-directions/proof/raster.js`.

**Rasteriser fidelity against native captures** (mean difference out of 255):

| Engine | Pixel ratio | Mean difference | Cost per sheet |
|---|---|---|---|
| Chromium | 1× | 0.04–0.66 | 12–35 ms; the first sheet is about 0.7 s, including fonts |
| Chromium | 2× | 0.04–0.52 | similar |
| WebKit | 2× | 0.5–1.1, mostly text anti-aliasing | no canvas lock-out. Photographs needed a second draw after a short wait. |

Off-the-shelf libraries failed. html2canvas made body text bold. html-to-image lost the fonts, then the layout heights, until fixed as above.

**Blind side-by-side, live proof against prototype** (critic round 12; pages 03, 11 and 16; same stroke):
- **Picks:** the live proof was picked in 2 of 3 pairs, every difference "negligible".
- **Verdict:** "a careful viewer could not reliably tell X from Y".
- **Result:** the mechanism passes.

**Open risks for the plan:**
- **Frame rate:** about 35 fps headless on an M2 Pro with everything running. The cloth simulation is on the main thread.
- **GPU memory:** only sheets near the viewport are kept.
- **Re-rasterising:** needed on resize and on font load.
- **Firefox:** not yet tested.
- **Stand-in:** the proof's invisible-HTML approach shows no selection highlight.

## 10. Change after review: the ember on dark pages (15 Oct 2026)

**The problem.** On review, Aaron found c3's glow invisible on the dark pages. c3 multiplies its light by the page's brightness cubed, so on near-black ground nothing is left.

**What he asked for:** "literally just keep it as is. only increase the intensity of the ember glow in the darker areas of the guide."

**The change.** Inside c3's surfaces step, the page the glow multiplies by is lifted where the ground is dark. Darkness is measured on the ground view, with the satin's dark curve (luma 0.42 → 0.22).
- **Off content:** the lift never touches type, photographs or panels.
- **Strength:** lift 0.4, picked by eye. A URL parameter `lift` overrides it, for comparisons.
- **Unchanged:** the light pages. Page 11's darker lower half takes some of the lift.
- **Result:** on page 17 a stroke changes the screen by 1.11 (it was 0.53; the gold page is 2.19).
