---
name: afterglow-brand-identity
description: "Single source of truth for Afterglow brand tokens, voice and art-direction rules. Consult before generating any UI, styling, copy or motion for the Afterglow storefront. Never guess brand elements, look them up here."
---

# Afterglow brand identity

**Brand:** Afterglow, a signature fragrance. Fictional, built for Demo 01.
**Project type:** Custom Shopify theme on Skeleton, Phase 1 of the six-month plan.
**Narrative source:** [`../2026-10-03-afterglow-brief.md`](../2026-10-03-afterglow-brief.md)

> Afterglow is one fragrance told in four stages, from the gold of last light to deep
> violet, and you do not see the bottle until the end.

Do not guess or infer brand elements. Reference the resource files below.

---

## Where the rules come from, and what they bind

Every rule below originates in the launch-night event, which is the only source material
that exists. Origin is not scope: the brief and the tokens file say which of them were
written forward into the storefront, and that is what the Scope column records. Do not
infer a site rule from an event rule the sources did not carry over.

| Rule | Scope | Stated where |
|---|---|---|
| **The bottle is revealed last.** No layout leads with packaging | Event only | `design-tokens.json` `reveal-rule`: "Nothing in the storefront leads with packaging" |
| **No wordmark stamped on things.** "Felt in the world, never stamped on it" | Event only | The brief heads this "The brand rule, which is the storefront brief" |
| **Four stages are not four SKUs.** One fragrance, told in four parts | Event only | Named against collection and product templates |
| **The tracker accents do not transfer.** `#39FF14` and `#FF00BD` are Krave's "system online" and "blocked" | Event only | The brief: "Does not transfer" |
| **The light only ever deepens, never brightens.** Gold through rose to violet, and holds | Both | The brief calls this art direction; the dark ground is "required by the deepening-light rule, not borrowed" |
| **Motion deepens, it does not snap.** Met as a journey, not a cloud | Both | `design-tokens.json` motion personality, marked locked |
| **Each room runs warmer than the last** | Event only | A staging instruction about physical rooms and diffusion heat. Nothing carries it to the site |

**Resolved 7 Oct 2026 by Aaron:** those four do not bind the site. They are event
art direction, whatever the source wording suggests, and the sources were written from the
event config before a storefront existed. The storefront is free to lead with packaging, use a
wordmark, present the stages however it likes, and is not bound by the tracker-accent rule.

What that leaves as site art direction: the six locked neutral tokens, the deepening-light
rule, the motion personality, and `resources/voice-tone.md`, which has its own tone-by-context
table written for storefront pages and is unaffected by this. Everything else for the site is
undecided rather than constrained.

## Resource Files

### Visual Design & Tokens
[`resources/design-tokens.json`](resources/design-tokens.json)
Colour, typography scale, spacing, radius, shadow, motion.

### Copy & Voice
[`resources/voice-tone.md`](resources/voice-tone.md)
Voice, vocabulary, what Afterglow never says.

### The guideline document
[`2026-10-07-afterglow-guidelines.html`](2026-10-07-afterglow-guidelines.html) and its
[PDF](2026-10-07-afterglow-guidelines.pdf)
The visual brand guideline. It states the rules and is an example of them: one continuous fall
from gold to deep violet that never resets, with every claim proved at the position where the
ground reaches the value being specified. Rendered from `resources/design-tokens.json` by
`tools/build_guidelines.py`, so it cannot drift from the tokens. Verified by
`tools/brand_audit.py`.

### How the decisions were reached
[`2026-10-07-stage-palette-pass-1.html`](2026-10-07-stage-palette-pass-1.html) and
[pass 2](2026-10-07-stage-palette-pass-2.html), then
[stage two names](2026-10-09-stage-two-names.html), then
[type pass 1](2026-10-09-type-specimen-pass-1.html) and
[pass 2](2026-10-09-type-specimen-pass-2.html).
One artifact per pass, never overwritten, each saying what produced it and what it led to.

---

## Quick Reference

| Token | Value | Status |
|---|---|---|
| Ground | `#080808` | Locked |
| Surface deep | `#141414` | Locked |
| Surface | `#2B2B2B` | Locked |
| Text | `#EEECEA` | Locked |
| Muted | `#C0C0C0` | Locked |
| Border | `rgba(192,192,192,0.22)` | Locked |
| Stage 1, gold of last light | `#D8B260` | Locked, 9.97:1 on void |
| Stage 2, after gold | `#BC6F4C` | Locked, 5.26:1 on void |
| Stage 3, rose | `#893A50` | Locked, 2.66:1 on void |
| Stage 4, deep violet | `#341D5E` | Locked, 1.41:1 on void |
| Display font | Instrument Serif | Locked, Shopify font library |
| Body font | Space Grotesk | Locked, Shopify font library |
| Type scale | 1.25 from 16 px | Locked, every step derived |
| Spacing | 8 px base, whole multiples | Locked |
| Radius | 0 px | Locked |
| Shadow | none | Locked, elevation is the surface steps |
| Motion | 450 ms, `cubic-bezier(0.2, 0, 0.2, 1)` | Locked, settles without overshoot |

Nothing here is outstanding. The stages are ramp E, picked 9 October 2026: lightness falls in
even steps of 0.16 in OKLCH, chroma is held flat at 0.110, and the hue rotates one direction
along the sundown arc. Stages 3 and 4 fail 3:1 on the void and are never letterforms; the
measured reason is printed in the guideline document rather than argued here.

The brief says the four stages are what Shopify's `color_palette` setting type is for. The theme
has no `color_palette` and no `color_scheme` in `config/` at all, so these become a schema
addition during the build rather than values dropped into a slot that is waiting for them.

---

## Instructions

1. **Identify** which resource files bear on the task
2. **Cross-reference** planned decisions against them
3. **Execute** on the locked tokens. Every one of them is set; anything that still looks
   open is a decision to make, not to guess
