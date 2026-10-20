# Afterglow homepage, first screen: The film

Feature-design spec, Step 6. Direction A5, picked by Aaron on 20 October 2026.
Storyboard: `.superpowers/brainstorm/homepage-1792523959/a5-the-film.html` (served at
`http://localhost:59965/homepage-1792523959/index.html`).
Floor: Byredo and Rick Owens; Heretic is the minimum (`references/design-standards.md`).

## Overview

The first screen of the Afterglow storefront is one film, full bleed, with almost nothing on it.
A single line in Instrument Serif, the product line and a solid buy button sit at the bottom left.
The nav is one thin row with the wordmark small in the middle.

It communicates one thing: this is a fragrance sold by its light and its hour, and you can buy it
from here. Everything that is not the film, the line or the button is quieter than all three.

It is built as a Shopify theme section that a non-technical owner can change in the editor, and
it is the W3 roadmap piece: "a first screen that does not look like Horizon".

## Content

| Element | Content |
|---|---|
| Line | Breathe in the last of the sun. |
| Product line | Afterglow · Eau de parfum · 50 ml |
| Button | Add to bag |
| Price | $180, beside the button, read from the product |
| Nav, left | Menu, Search |
| Nav, centre | The wordmark, linking home |
| Nav, right | Account, Bag (count) |
| Motion control | Pause; reads Play while paused |

The product line, button and price come from a product the owner picks, so the name, size and
price stay true if the product changes.

## Trigger

The section is the first thing on the homepage. The film starts on load, muted and looping, as
soon as enough has arrived to play smoothly. Until then the poster frame shows, and the type and
button are on screen from the first paint; nothing waits for the film.

## States

**The film**
- Loading: the poster frame, full bleed, with the same darkening as the film.
- Playing: the film loops with no visible seam.
- Paused: the film holds on its current frame. The control reads Play.
- Reduced motion (the visitor's system asks for less motion): the film never starts. The poster
  frame shows and the control is hidden.
- Failed or blocked (data saver, autoplay refused): the poster frame stays. Nothing reports an
  error.
- Off screen: the film pauses when the section is scrolled out of view or the tab is hidden, and
  resumes on return unless the visitor paused it.

**The buy button**
- Rest: solid #EEECEA, label in #080808.
- Hover and press: the fill darkens to #C0C0C0.
- Focus (keyboard): the same darkening as hover, plus a 1 px #C0C0C0 ring 4 px outside the button.
- Adding: the label reads Adding and the button ignores further presses.
- Added: the bag count in the nav goes up by one, the cart drawer opens (W4 builds the drawer;
  until then the visitor goes to the cart page), and the label returns to Add to bag.
- Sold out: the button is #2B2B2B with the label in #C0C0C0, reads Sold out, and cannot be
  pressed.

**Nav links and the motion control**
- Rest: #EEECEA. Hover and press: #C0C0C0. Focus: the same, plus the 1 px #C0C0C0 ring.

Every state is darker than, or equal to, the state it comes from. That is the guide's one rule,
and a developer can check it: no hover, focus or press colour is lighter than its rest colour.

## Motion breakdown

- Film: plays at its own pace. No zoom, pan, parallax or scroll effect is added on top.
- Colour changes on every control: 450 ms, ease in and out (the guide's curve, 0.2, 0, 0.2, 1),
  stopping where they land, no bounce.
- Pause and play: the film stops or starts at once; only the control's label changes.
- No entrance animation. The line, product line and button do not fade, slide or stagger in.

## Colour and visual details

- Ground behind everything: #080808.
- Darkening over the film, always darkening and never lifting:
  - top edge: #080808 at 50%, fading to nothing by 20% of the screen height, so the nav reads
  - bottom: nothing at the middle of the screen, rising to #080808 at 85% at the bottom edge,
    so the type reads
- Line and wordmark: #EEECEA.
- Product line and price: #C0C0C0 for the product line, #EEECEA for the price.
- Button: as in States.
- No borders, no shadows, square corners everywhere, no radius on the button.
- Colours come from the theme's colour palette setting, not from values typed into the section,
  so the stages and neutrals are defined once.

## Typography

| Element | Face | Size | Leading | Tracking | Case |
|---|---|---|---|---|---|
| Line | Instrument Serif 400 | 39 px on phones, growing with the screen to 61 px | 1.02 | −0.015 em | Sentence |
| Product line | Space Grotesk 400 | 12.8 px | 1.3 | 0.12 em | Upper |
| Button label | Space Grotesk 400 | 12.8 px | 1.3 | 0.12 em | Upper |
| Price | Space Grotesk 400 | 20 px | 1 | 0 | — |
| Nav and control | Space Grotesk 400 | 12.8 px | 1.3 | 0.12 em | Upper |
| Wordmark | Instrument Serif 400, widened to 150% | 26 px on desktop, 22 px on phones | 1 | 0 | As set |

The line is balanced across two lines, never leaving one word alone: "Breathe in the / last of the
sun." It is held to about 13 characters wide. Both faces load from Shopify's font library.

## Responsive notes

Built small screen first; complexity is added as the screen grows.

**Height.** The section fills the stable visible height of the screen (the small-viewport unit), so
it never runs under the phone's browser bars and does not jump when they hide. It never goes
below 560 px tall; on shorter screens it scrolls rather than squashing. The bottom padding adds
the phone's safe area so nothing sits under the home indicator.

**Phone (up to 576 px)**
- Film: a separate 9:16 or 4:5 cut, chosen in the editor, so the bottle is framed for a tall
  screen rather than cropped from the wide cut. If no phone cut is given, the wide cut is centred
  on its focal point.
- Nav: Menu, wordmark, Bag. Search and Account move into the menu.
- Type block: 20 px from both sides and the bottom. Line at 39 px.
- Button: runs the width of the type block less the price, at least 48 px tall, in the bottom
  third of the screen where the thumb rests.
- Motion control: top right, under the nav, so it never competes with the button. Its tap area is
  at least 44 × 44 px.

**Tablet (577 to 992 px)**
- Film: the wide cut, centred on its focal point.
- Nav: all four links and the wordmark.
- Type block: bottom left, 32 px in, line scaling with the screen. Button at its natural width.
- Motion control: bottom right, level with the button.

**Desktop (993 to 1440 px)**
- As tablet, with margins growing from 32 to 52 px and the line reaching 61 px.
- Type block held to the left four of twelve columns.

**Wide (over 1440 px)**
- The film keeps filling the screen; the type block, margins and line stop growing at their
  1440 px values, so the type gets relatively smaller and the film takes more of the screen.

**Orientation.** A phone turned sideways uses the wide cut and the tablet layout, with the
560 px minimum height lifted so the screen is not forced to scroll.

**Touch.** Nothing depends on hover. Every hover state is also the press state, and every control
works by tap and by keyboard.

**Performance on phones.** The phone cut is a smaller file than the wide cut. The poster frame
is the only thing the first paint waits for.

## Editor settings (the owner's controls)

The section's settings, in the order the owner sees them:
1. Film, wide cut (video)
2. Film, phone cut (video, optional)
3. Poster frame (image)
4. Darkening strength (a slider, from light to strong; it only ever darkens)
5. Product (product picker): drives the product line, price, sold-out state and the button

Blocks inside the section, which the owner can reorder or remove:
- **Line**: the text, and its size (three steps from the type scale). This is the reusable theme
  block, in the theme's blocks folder with a preset, so it appears in the block picker and can be
  used in other sections.
- **Product line**
- **Buy button**

Theme-wide: colours come from the colour palette setting, defined once with the guide's values.

## Footage brief (for the Higgsfield film)

The direction was judged with stand-in footage. The critics' one complaint was that no bottle was
visible, so the film carries the product.
- The bottle is the whole mark: the A triangle, the middle triangle and the G triangle together,
  with the cap. It is clearly legible for at least a third of the loop.
- One low, warm light source, falling. The brightest quarter of any frame sits at or below gold of
  last light (L 0.781). Nothing is lifted in post.
- Shadows and highlights land on the stage colours, not on grey. If the loop moves through
  stages, it runs warm to cool and never back.
- The bottom-left third of the frame stays calm and dark enough for the line to read, at both
  cuts. The bottle sits right of centre on the wide cut and in the upper half on the phone cut.
- 6 to 12 seconds, looping without a visible seam. No text, no logo burned in, no sound.
- Wide cut 16:9; phone cut 9:16 or 4:5. Poster frame: a still from the loop in which the bottle
  reads.
- File size: the wide cut under 4 MB, the phone cut under 2 MB.

When the footage exists, the first screen is judged again by a blind critic against Byredo and
Heretic before any build is called done.

## What it must not do

- No state lighter than its rest state. No glow, flash or brightening on hover, focus or press.
- No entrance animation, parallax, scroll effect or zoom over the film.
- No sound, ever. No unmute control.
- No promo bar, discount pop-up or newsletter modal over the first screen. The critics marked
  Heretic down for exactly this.
- Nothing composed to make room for the ember. The site-wide ember runs over this section like
  any other surface; this section does nothing special for it.
- No type over the bottle. The footage brief keeps the bottom left clear; the darkening is not a
  licence to set type on the product.
- No hours (19:12 and the like) on this screen.
- No borders, shadows or rounded corners.
- The film never autoplays with motion for a visitor who asked their system for reduced motion.
