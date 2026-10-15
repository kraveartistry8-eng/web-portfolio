# Afterglow brand guidelines, design spec

Date: 2026-10-07
Status: approved in brainstorming, not yet implemented

## What this is for

A visual brand guideline document for Afterglow that both **demonstrates and describes** the
brand. It states the rules and is itself an example of them. A guideline for this brand that
looked like a plain spec would disprove its own argument.

It serves two readers without compromising for either. It is the document the Afterglow Shopify
theme gets built from, so every value in it is real and decided. It is also the artifact that
shows what the studio delivers, so it is designed rather than typed.

Because it is the build's source, it has to decide the items currently marked Week 2. You
cannot build a theme against `null`.

## Scope

Tokens plus usage rules. Specifically:

- **In:** the four stage colours, both type faces and the scale, spacing, radius, shadow,
  motion values, and the rules for how each is applied.
- **Out:** page-level guidance for home, collection, product and cart. That is guesswork until
  the theme exists to react to, and `voice-tone.md` already carries the tone half of it.

## Constraints taken from the source material

From `brand/2026-10-03-afterglow-brief.md`, `brand/BRAND-IDENTITY.md` and
`brand/resources/design-tokens.json`:

- Six neutral tokens are locked and do not move: ground `#080808`, surface-deep `#141414`,
  surface `#2B2B2B`, text `#EEECEA`, muted `#C0C0C0`, border `rgba(192,192,192,0.22)`.
- The dark ground is required by the deepening-light rule, not borrowed from elsewhere.
- Four stages, named gold of last light, [unnamed], rose, deep violet.
- Motion personality is locked: deepening, never snapping.
- Elevation reads through surface steps rather than shadow on a void ground.
- `voice-tone.md` is complete and is not touched by this work.

### Two corrections to the source material

**"Each room runs warmer than the last" is not a colour rule.** The brief's full sentence is
about air temperature for scent diffusion: "each room runs warmer than the last, so the
deepening scent lifts and blooms." It was also scoped event-only on 7 Oct. The stages are
therefore not required to warm in hue, which matters because gold to violet travels cooler.

**The gotchas do not bind the site.** Settled by Aaron on 7 Oct 2026. The bottle-reveal rule,
the no-stamped-wordmark rule, the four-stages-are-not-four-SKUs rule and the tracker-accent
rule are event art direction, despite the source documents wording them as storefront rules.
Site art direction is the six neutrals, the deepening-light rule, the motion personality, and
`voice-tone.md`.

## Deliverables

| File | Change |
|---|---|
| `brand/2026-10-07-afterglow-guidelines.html` | **The deliverable.** The visual guideline document. Authored in HTML, following the pattern already used across `design/` and `archive/colour/` |
| `brand/2026-10-07-afterglow-guidelines.pdf` | Rendered from the HTML by `tools/render.py`, the same Playwright pipeline the roadmap uses |
| `brand/resources/design-tokens.json` | Every `null` replaced. The machine-readable half the theme build consumes, and the source the document renders from |
| `brand/BRAND-IDENTITY.md` | Quick Reference updated from "Week 2" to real values; the guideline document added to Resource Files |
| `brand/2026-10-07-stage-palette-pass-N.html` | Working artifacts, **one file per pass, never overwritten**. Ramp exploration. Each pass carries what produced it and what it led to, so the decision trail is itself a deliverable rather than something only git remembers |
| `brand/2026-10-09-type-specimen-pass-N.html` | Working artifacts, one file per pass, same convention as the palette |

`usage.md` is not a separate file. Its content is a section of the guideline document, because
usage rules shown against real colour are clearer than usage rules described in prose.

No new source-of-truth file. `BRAND-IDENTITY.md` stays the router; this fills the structure
that already exists rather than competing with it.

## Form requirements

The document obeys the rules it states. These are requirements, not styling preferences, and
each is checkable:

- **It sits on the void ground.** `#080808`, with the surface steps carrying elevation. No
  light mode, no white page.
- **The stages are shown, not listed.** A reader moves through gold to violet in order and sees
  the deepening happen. A table of hex values alone would describe the brand without
  demonstrating it.
- **Nothing in it brightens on interaction.** The document's own hover and focus states deepen
  or shift hue. If the guideline brightens on hover it has broken its own central rule in the
  act of stating it.
- **It is set in the chosen faces**, at the chosen scale, with the chosen spacing. The type
  section is a specimen of itself.
- **It works at phone width.** 390px, no horizontal scroll.
- **Motion, if any, deepens rather than snaps**, per the locked personality.

What the document contains is specified below. How it is laid out is a design task for
implementation, where `graphic-designer` and `storyboard-designer` apply.

## Colour system

### Method: rule-derived, validated by eye

Approach A of three considered. The alternatives were sampling from sundown photography
(truer to the concept, but irregular and hard to extend) and picking candidates by eye and
describing them afterwards (fastest, but leaves no principle, so the next decision is guesswork
again).

Rule-derived was chosen so the document carries the rule and not just the values. When the
theme later needs a hover state or a fifth value, the rule answers it.

### The space is OKLCH

"The light only ever deepens" has to be measurable. In HSL it is not: `#FFFF00` and `#0000FF`
are both 50% lightness. OKLCH lightness is perceptual, so a monotonically falling L is the
brand rule expressed directly.

### The rule, numerically

- **L falls monotonically** across the four stages, in even steps. This is the deepening rule
  and it is the one parameter that cannot be bent.
- **H rotates one direction** along the sundown arc, gold through amber and rose into violet.
  No doubling back.
- **C is shaped, not constant.** Sunset is most saturated in the middle: gold is bright but not
  intense, rose is the peak, violet must hold chroma as L falls or it reads grey rather than
  deep.

L is fixed by the brief. The exploration varies H spacing and C shaping.

### Stage 2 gets a name

It is `null` in the tokens file and unnamed in the original material, so it is ours to name. It
sits between gold and rose, in the amber or ember register. The name comes from the Afterglow
vocabulary in `voice-tone.md`.

### Stage roles, which follow from the rule

A monotonically deepening ramp means the later stages cannot carry text on the void ground.
Stage 4 at low L against `#080808` lands near 2 to 3:1, the same failure as the Krave tracker's
`#7B2CBF` at 2.8:1. This is not a flaw in the rule, it is what the rule implies.

| Stage | Role |
|---|---|
| 1, gold of last light | Light enough for text or an accent mark on void |
| 2 | Borderline. Large text only, or fills |
| 3, rose | Fills, grounds, large shapes. Never text |
| 4, deep violet | Fills, grounds, large shapes. Never text |

The usage section must state this plainly, or someone sets violet body copy and the page looks
broken with no one able to say why.

### How values get chosen

`brand/2026-10-07-stage-palette-pass-1.html` renders three candidate ramps sharing the L rule and
differing in C shaping. Each stage is shown on the real `#080808` ground as a fill, as large
text and as a mark, with contrast computed against void and both surface steps. Aaron picks by
eye. The rule is then restated to match what was chosen, and those values go in the JSON.

This follows the pattern already in `archive/colour/`.

## Type, spacing, radius, shadow, motion

### Type is constrained by the theme

`afterglow/config/settings_schema.json` has exactly one font picker, `type_primary_font`,
defaulting to `work_sans_n4`. There are no fonts in `afterglow/assets/`. The brand model wants
two faces, display for wordmark and hero, body for everything else.

Two options, with build cost:

- **Both from Shopify's library.** No assets, merchant-swappable, needs a second `font_picker`
  in the schema. Limited to what Shopify serves.
- **Self-hosted display, library body.** The display face can be anything; costs a webfont in
  `assets/`, an `@font-face` rule and a schema change.

Decided on the specimen page, same method as colour: candidates set as the wordmark and a hero
line on the void ground, picked by eye.

### The rest

- **Scale.** One stated ratio, one base size, every step derived. The tokens file already
  requires this: "set the scale measured, not eyeballed."
- **Spacing.** A base unit and a scale derived from it.
- **Radius.** Near-zero. Restraint and a void ground point there, and nothing in the source
  argues otherwise.
- **Shadow.** Absent or a hairline. Already settled in substance by the tokens file: "on a void
  ground, elevation reads through surface steps more than shadow."
- **Motion.** Personality is locked, so only two numbers are missing: a duration band and an
  easing curve that settles rather than arrives. Overshoot, spring and bounce are ruled out by
  "deepening, never snapping."

### One assumption in the brief that is not true yet

The brief says the four stages "are exactly what Shopify's `color_palette` setting type is
for." The theme has no `color_palette` and no `color_scheme` in `config/` at all. That is a
schema addition during the build, not a slot waiting to be filled.

## Usage rules

The usage section of the document contains four things.

**The surface map.** Void is the page ground, `#141414` recessed, `#2B2B2B` raised, border the
hairline between them. Shadow is absent from this list on purpose.

**Stage roles and contrast floors.** The role table above, each entry carrying its measured
ratio against void and both surface steps, so a later change can be checked rather than argued.

**The deepening rule in testable form.** "The light only ever deepens" is a sentence about mood
that a developer cannot act on and a reviewer cannot check. The usable form is an interaction
rule: **no state change brightens.** Hover, focus and active deepen or shift hue, never lighten.
Nothing fades up to a brighter value. This converts the brand's central idea into something
verifiable in a diff, and is the main reason the document is worth having.

**Where the rules stop.** `voice-tone.md` sets the precedent: "Cart and checkout: plain and
fast. The atmosphere stops here on purpose." The visual rules stop in the same place. The
deepening discipline serves browsing and gets out of the way at checkout, where clarity beats
atmosphere. Without this line someone applies the rule to a payment form and makes it worse.

## Verification

- Every `null` in `design-tokens.json` has a value.
- Every stage colour carries a measured contrast ratio against `#080808`, `#141414` and
  `#2B2B2B`, recorded in the usage section.
- L falls monotonically across the four stages when converted to OKLCH. This is checkable by
  script and should be, since it is the one rule that cannot be bent.
- No token value is `#39FF14` or `#FF00BD`.
- `BRAND-IDENTITY.md` Quick Reference contains no remaining "Week 2" rows.
- The document renders to PDF through `tools/render.py` with no console errors.
- The document's own background is `#080808` and no rule in it sets a lighter value on `:hover`,
  `:focus` or `:active` than the resting state. This is the brand's central rule applied to the
  artifact that states it, so it is checked rather than assumed.
- The document is legible at 390px wide with no horizontal scroll.

## Open questions

None blocking. Two decisions are deferred to the exploration artifacts by design: which colour
ramp, and which type pairing. Both are visual picks that text cannot settle.
