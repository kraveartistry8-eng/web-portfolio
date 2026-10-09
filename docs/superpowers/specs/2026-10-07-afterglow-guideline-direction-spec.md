# Afterglow guideline document, design spec

Date: 2026-10-07
Direction: The Descent, with measured specimens, in the Margin form. Confirmed by Aaron 7 Oct 2026.
Form chosen from three iterations in `brand/2026-10-07-guideline-directions-combined.html`.
Content spec: `2026-10-07-afterglow-brand-guidelines-design.md`
Floor: Frame.io Brand Style Guide. Stretch: Uber brand system. Both pinned under `references/`.

This spec covers the document's form. What it says is fixed by the content spec above.

## Overview

A brand guideline document for Afterglow that demonstrates the brand while describing it. It is
one continuous fall from the gold of last light to deep violet. The ground deepens across the
whole document and never resets, so how far through the reader is can be read from how dark the
page has become. Every rule in it is proved where it is stated, on a field of the colour being
specified, carrying its own measured numbers.

The descent gives the document its structure. The specimens are how any claim is proved. The
crossover line is both at once, which is why these two combine rather than merely sit together.

**Nothing is laid on the fall.** The ground is the swatch. A rule about a stage colour is proved at
the position where the descent passes through that colour, and the reading is printed in a void
ledger beside it, connected by a leader rule. This was chosen over an inset panel for a measured
reason: the fall passes through the stages, so a panel of a stage colour placed on the ground
measures about 1.15:1 against it and has no edge of its own. An inset needs a hairline to exist,
and a border the document requires in order to work is a rule the brand never asked for.

## Trigger

Scroll position, and nothing else. There is no entry animation, no reveal on load, no scroll
hijack. The document's one behaviour is that its ground value is a function of how far down the
reader has moved. A reader who loads the page halfway through, from a deep link or a restored
scroll position, sees the correct ground value for that position immediately.

Print and PDF export resolve the ground to its value at each page's own position, so the
printed artifact carries the same fall as the screen one.

## States

The document has three, and they are positions rather than modes.

**Above the crossover.** Ground lightness is above the point where primary text reaches 4.5:1.
Only display sizes are set here. Running text does not appear.

**At the crossover.** A single measured rule drawn where the fall first carries body copy at
4.5:1. It is labelled with that ratio. This is the only horizontal rule in the document that is
not a section boundary.

**Below the crossover.** Ground lightness carries body copy for the rest of the document, and
continues deepening. Nothing after this point returns to a lighter value.

The ledger is not a state. It is a fixed void column that runs the full height of every spread,
and its rows are anchored to positions in the fall rather than to the flow of the copy.

## Motion breakdown

Motion personality is locked by the brand: deepening, never snapping. The document is close to
motionless by design, and the restraint is the point.

**Ground value on scroll.** Continuous, linear with scroll position, no easing. It is a
mapping, not an animation. There is no transition duration because there is no transition; the
value is wherever the reader is.

**The rail's active marker.** Moves with scroll on the same linear mapping.

**Interactive states on links and controls.** 450ms, ease-out, settling rather than arriving.
Colour deepens or shifts hue. No overshoot, no spring, no bounce.

**Reduced motion.** Nothing here is motion in the vestibular sense, so the reduced-motion
preference changes nothing structural. The ground mapping stays. This is stated so no one later
adds a scroll-linked animation and assumes it is covered.

## Colour and visual details

**Ground.** The fall runs from the stage 1 value at the document's top to the stage 4 value at
its end, passing through stages 2 and 3 at their positions. Lightness falls monotonically in
OKLCH. The void `#080808` is not the document ground here; it is the colour of the rail strip
and of any surface that must sit outside the fall.

**The inversion point.** Display type above the crossover is set in the void `#080808`, not in
primary, and flips to primary at t 0.4560. This was missing from the spec and the measurements
forced it: on the gold end primary text reads 1.70:1 against the ground and fails even the 3:1
large-text floor, so the only legible display type up there is dark.

The flip is placed where the two are exactly equal. Dark text holds 3:1 until t 0.6069 and light
text reaches 3:1 at t 0.2960, so they overlap across the middle third; inside that overlap the two
curves cross at t 0.4560, where both read 4.12:1. Inverting anywhere else in the band would mean
accepting a worse ratio than the document has to.

**The dead zone, and why it is not a defect.** Between t 0.4119 and t 0.5000 nothing clears 4.5:1
on the fall in either colour: dark text has fallen to 4.48:1 and light text has not yet reached
4.52:1. At the worst point, t 0.4560, both read 4.12:1. That band is 8.8 per cent of the document
and it carries no running text, which the spec already required for a different reason, since it
sits above the crossover where only display sizes are set. The two rules agree, but they agree by
arithmetic rather than by luck, and a later change to the ramp could pull them apart. If the ramp
moves, recompute both before assuming body copy still has somewhere to go.

**Banding.** No mitigation. Settled by a throwaway spike on 9 October 2026 and recorded here
because it is the one risk that could have invalidated this direction.

The arithmetic says it should band. Rounded to 8 bits, the four-stage fall over a 16000px
document resolves to 346 distinct tones, and the longest run of a single tone is 101px, around
`#A3554E` near the crossover. A 101px band of one colour on a quiet page is visible.

It does not band, because the browser does not round. Chromium dithers the gradient: the same
regions measure a median run of 1px, 35 to 46 distinct tones per 1000px, and 2 to 4 distinct
tones across a single horizontal row, which is the dither noise. Inspected by eye at the violet
end, the darkest and therefore the worst case, the fall is smooth.

Two limits on that answer. It was verified on screen in Chromium, which is the render target for
the HTML but not for the PDF, so Task 9 re-checks the printed artifact rather than assuming the
dithering survives rasterisation. And it holds at a document height of 16000px; a substantially
longer document lengthens every run and the spike would need rerunning.

**The ledger.** A void column at the right edge of the measure, carrying the document's readings.
Each row sits at the exact height where the fall equals the value it describes, with a leader rule
joining the row to the ground it was taken from. A row carries the hex, the OKLCH triple, the ratio
against the void, and the ratio of primary text set on that colour. Failing ratios are printed, not
hidden, and are the stated reason for a restriction. Labels are set on the void, so they measure
11.01:1 and 17.00:1 rather than fighting a ground that is moving underneath them.

The ledger is the document's measurement column throughout, not a colour device. Type sizes, the
spacing scale, radius and motion durations are recorded in it the same way, so the document has one
place where it says what it measured. Without this the colour section has a form and the rest of the
document does not.

**Each stage is specified in exactly one place**, because the fall passes through each value once.
This constrains the running order: the colour section's sequence is fixed by the ramp, not by
editorial preference. That is a cost of the form and is accepted.

**Colours the fall never reaches.** The six locked neutrals are not on the ramp, so they cannot be
read off the ground. They are specified in the ledger itself, which is the void: the ledger's own
background steps to `#141414` and `#2B2B2B` across the surface-map rows, so the neutral family is
demonstrated by the column that reports it. The fall specifies the stages, the ledger specifies the
void family, and each ground proves its own.

**Text.** Primary `#EEECEA` and muted `#C0C0C0`, except where a specimen field requires dark
text to demonstrate a point, in which case the void value is used and the ratio is printed.

**Rail.** A void strip outside the ledger carrying the OKLCH lightness at the top, the crossover,
and the end of the fall. The rail is the folio. There is no page number.

**Rail and ledger do not compete, because they answer different questions.** The rail carries
position and no values; the ledger carries values and makes no claim about position of its own,
since each row inherits its position from the ground it points at. They are never merged. A single
column doing both would have to choose which of the two it is scaled to.

**Slug.** A fixed top-left line carrying section and document title, on the void, outside the
fall. It replaces Frame.io's four-field footer, because the rail already carries position and
two position indicators would compete.

**Hairlines.** `rgba(192,192,192,0.22)` for section boundaries only.

## Typography

Faces and scale are chosen on the type specimen page and are not pre-empted here; the content
spec owns that decision. What this spec fixes is how type behaves in the fall.

- **Display** carries the wordmark and section openers, and is the only type permitted above
  the crossover. Set large, tight, with negative tracking.
- **Body** is set at the document's base size and never appears above the crossover.
- **Ledger data** is set small, tabular-numeric so columns of ratios align, with labels in
  uppercase at wide tracking and values in the body face. It never exceeds the body size, because a
  reading is an annotation of the page and not a voice in it.
- **Measure** is capped so running text never exceeds a comfortable line length regardless of
  viewport.

Every size is set in `rem` so browser font-size preferences are respected, and fluid between a
floor and a ceiling rather than jumping at breakpoints.

## Responsive notes

Built mobile-first: the 390px layout is the base and complexity is added upward. Breakpoints go
where the content breaks, not at device names.

**The fall is the thing that must survive.** A reader on a phone must experience the same
continuous deepening, because it is the document's entire structure. It does not reduce to a
static dark background on small screens.

**390px base.**
- Single column. The ledger stops being a column and its rows move inline, each one directly under
  the passage it annotates, in document order. They never reflow into a grid, because a grid
  destroys the sequence the document is built on.
- An inline row cannot sit at the height of the value it describes, so at this width a leader rule
  would point at nothing and is dropped. The row names its own position instead, and its ratio is
  recomputed against the ground the row actually sits on. A reading that was true at 1180px and is
  reprinted unchanged at 390px is a false number, which is the one failure this document cannot
  afford.
- The rail moves from the right edge to a 3px bar at the very top, fixed, filling left to right
  as the reader descends. It keeps its job and loses its labels; the labels move inline to each
  section opener.
- The slug collapses to the section name alone and stops being fixed, so it does not eat
  vertical space on a short viewport.
- Specimen data stacks label-above-value rather than in columns.

**Above 760px.** The ledger returns as a column with its leader rules, and the rail returns to the
right edge with its labels.

**Above 1180px.** Measure is capped and the remaining width becomes margin. The document does
not grow wider, it grows quieter.

**Viewport units.** Any full-height element uses `svh`, never `vh`. `vh` measures against the
browser with its UI retracted and will overflow on load on every mobile browser. `dvh` is
rejected here because it resizes as the browser chrome toggles, and on a document whose ground
is a function of scroll position that reflow would visibly shift the colour.

**Touch.** Any interactive target is at least 44 by 44px. Nothing in the document reveals
content or meaning on hover alone, since hover does not exist on touch; hover states are
decoration only, and every one has a focus-visible equivalent.

**Orientation.** The fall is mapped to document progress, not to viewport height, so rotating
the device changes layout but not the reader's position in the ramp.

## What it must not do

- **It must not brighten.** No state, no hover, no focus, no section, no print stylesheet may
  produce a lighter value than the one before it. This is the brand's central rule and the
  document is the first thing that has to obey it.
- **It must not reset the fall.** No section returns to the top of the ramp.
- **It must not print a number it has not measured.** Every ratio and every value in the
  document is computed from the real colour, not asserted.
- **It must not hide a failing ratio.** A restriction is justified by the number that causes it.
- **It must not reflow ledger rows into a grid on small screens.** Sequence is the structure.
- **It must not lay a panel of a stage colour on the fall.** Measured at about 1.15:1, it has no
  edge of its own, and the hairline needed to give it one is a rule the brand did not ask for.
- **It must not reprint a position-dependent reading unchanged at another viewport.** Every ratio is
  a function of where its element actually sits.
- **It must not carry a page number.** The rail is the folio.
- **It must not use `#39FF14` or `#FF00BD`.** Those belong to the Krave production tracker.
- **It must not stamp a wordmark on every spread.** Once, at the opening.
- **It must not use em-dashes.** Repo convention for anything printed.
- **It must not add a scroll-hijack, a loader, or an entry animation.** The brand is met
  unhurried, and the document opens where it opens.

## Measured constants

Computed from the provisional ramp used in the directions artifact, with the method the build
repeats rather than the values it keeps. The real ramp is chosen in Task 2 and every number here is
recomputed against it then.

| Quantity | Provisional value |
|---|---|
| Crossover, where `#EEECEA` first clears 4.5:1 on the ground | t 0.4803, ground `#B9452B`, 4.51:1 |
| Ground above the crossover, display only | 3.46:1 at t 0.360, clears the 3:1 large-text floor |
| A stage panel laid on the fall | about 1.15:1, the reason the Margin was chosen |
| Ledger labels on the void | 11.01:1 muted, 17.00:1 primary |
| Monotonic lightness | verified at 120 sampled positions per spread, rules excluded |

Gradients interpolate in sRGB unless told otherwise, so the fall's intermediate values are sRGB
interpolations of the stage colours and the audit must compute them the same way. Measuring the
ramp in OKLCH while the browser paints it in sRGB would compare two different gradients.

## Note on justification

No part of this spec is justified by a claim about attention, trust, scanning behaviour or what
reads as premium. The reasoning is brand logic and measured contrast throughout. If a later
revision introduces a perceptual claim, it needs checking before it goes in, because a spec is
where a claim stops being conversation and starts determining what gets built.
