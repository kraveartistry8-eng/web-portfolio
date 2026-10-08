# Frequency Alignment Tracker

The design system behind Frequency Alignment Tracker, Aaron Streets' custom live-production tracker for event producers. It looks like a dark control room: a near-black void ground with a faint green signal grid, and three loud accent colors (signal green, purple, hot pink) used sparingly against it.

> Built from the live site's `:root` variables and its `body` and `h1` rules. Every value here is copied exactly from that source. Anything not yet captured is listed under **Not yet captured**.

## Content fundamentals

The voice comes from someone who has worked the floor ("Stagehand, AV tech, scenic painter, editor") and talks to producers in production language.

- **Second person, the producer's event first.** "A live production tracker, custom-built around the vision of your event."
- **Rhythm through repetition.** "Every crew, every deliverable, tuned to your vision, in real time."
- **Name the real pain plainly**: finding problems late, information scattered everywhere, generic tools, accountability for crew leads.
- **Concrete numbers over adjectives**: "up to 4 crews", "seven-day deployment", "3 builds a season", "single-tap clearance".
- Use the domain's words: crews, team leads, deliverables, clearance, call times, client view, archive.

## Visual foundations

**Ground.** Every page sits on `void` (#080808). Over it runs a 1px grid in `grid-line` (green at 2.8%), repeated every `grid-64`. Keep it quiet: it should feel like a monitor's graticule, not a pattern.

```css
background-color: var(--void);
background-image:
  linear-gradient(var(--grid-line) 1px, transparent 1px),
  linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
background-size: var(--grid-64) var(--grid-64);
```

**Surfaces.** Use `card` (#2B2B2B) for raised cards and `card-deep` (#141414) for recessed areas inside them. Separate them with `border` hairlines (silver at 10%), not shadows.

**Color roles.**

| Role | Solid | Tint bg | Ring |
| --- | --- | --- | --- |
| Signal: live, cleared, go | `green` | `green-dim` | `green-ring` |
| Brand secondary: fills, large shapes | `purple` | `purple-dim` | `purple-mid` |
| Attention: alerts, emphasis | `pink` | `pink-dim` | `pink-ring` |

The rule for tints is a solid accent inside a tinted background with a matching ring. For example, a green status pill uses `green` text on `green-dim` with a `green-ring` outline.

**Contrast rules (checked):**

- `text` and `silver` pass on every surface: at least 7.8:1.
- `green` passes as text anywhere: at least 10:1.
- `pink` as text is fine on `void` and `card-deep`. On `card` it is 4.0:1, so use it there for large text or marks only.
- **Never use `purple` as text.** It is 2.8:1 on `void`. Use it as a fill instead; `text` on a purple fill reads 6:1.

**Type.** Inter is used throughout. Load it from Google Fonts at weights 400 and 900.

- `h1`: weight 900, line-height 1.07, tracking −0.036em, `text-wrap: balance`, max width `h1-measure` (840px). It is fluid on the site at `clamp(28px, 4.2vw, 52px)`; 52px is the cap.
- `body`: 16px with line-height 1.65.
- Headlines are heavy and tight; body text is airy. That contrast in weight carries the hierarchy.

**Spacing.** The base module is `grid-64`. Space below an h1 is `hero-h1-gap` (26px) in the hero and `h1-gap` (52px) elsewhere.

## Iconography

No icons or logos have been captured yet. Until the real mark arrives, set the name in Inter 900 rather than drawing a substitute logo.

## Not yet captured

To finish the system, the remaining CSS rules are needed: buttons, nav, cards, pricing tiers, badges, the demo views (producer, team lead, crew, client), the guided tour, plus border-radius and shadow values. The quickest way to supply them is to share the full stylesheet or the repo.
