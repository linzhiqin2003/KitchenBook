# Chapter 14 — CSS (layout & responsive)

## Overview

Week 4 of *Software Tools* moves from raw CSS syntax to **page design**: how to lay out elements predictably, how to make layouts adapt to phones/tablets/desktops, and which battle-tested principles to lean on so the result actually looks good.

The chapter is built around three short videos (Design, CSS grids, Responsive Layout) plus two labs (`curriculum`, `trees`). The slides explicitly frame web design as a **craft** that mixes engineering with judgement and taste — there are principles, but not algorithms. Three useful shortcuts are repeated:

- borrow ideas from existing sites,
- use design frameworks others wrote (e.g. Bootstrap, the topic of last week),
- adopt a **grid-based layout** plus **responsive layout** (the focus this week).

The technical core is:

- the **CSS Grid** module (parent declares `display: grid`, children are placed by row/column),
- **media queries** (`@media`) so rules apply only at certain viewport widths,
- supporting concepts: fluid widths (`max-width` + `margin: 0 auto`), `fr` units, `gap`, the viewport meta tag, and mobile-first thinking.

The historical detour in the slides — Tables → Float → Flexbox → Grid — is worth knowing: Grid is the modern answer for 2-D page layout, Flexbox for 1-D component layout. Most real sites use both.

## Core knowledge

### `display` values (the layout switch)

| Value          | Behaviour                                                                                   |
|----------------|---------------------------------------------------------------------------------------------|
| `block`        | Full row, respects `width`/`height`, stacks vertically. Default for `<div>`, `<p>`, `<h1>`. |
| `inline`       | Sits inside a line of text, ignores `width`/`height`/vertical padding-margin. Default for `<span>`, `<a>`, `<b>`. |
| `inline-block` | Flows inline like text, but accepts box dimensions.                                          |
| `none`         | Removed from layout entirely (not just hidden — no space reserved). Compare with `visibility: hidden`. |
| `flex`         | Element becomes a **flex container**; its direct children become flex items (1-D layout).    |
| `grid`         | Element becomes a **grid container**; children placed on a 2-D grid.                         |

The `curriculum` lab uses `<b>` (normally inline) re-declared to `display: block` so the title bar spans the whole grid cell.

### Positioning (`position`)

| Value      | Anchored to                                            | Removed from normal flow? |
|------------|--------------------------------------------------------|----------------------------|
| `static`   | Default — normal flow                                  | No                         |
| `relative` | Its normal-flow position; `top/left` shift visually    | No (still occupies original space) |
| `absolute` | Nearest non-`static` ancestor                          | Yes                        |
| `fixed`    | Viewport (stays in place when scrolling)               | Yes                        |
| `sticky`   | Acts `relative` until scroll crosses a threshold, then `fixed` | No until "stuck" |

The slides emphasise that for whole-page layout you almost never need explicit `position: absolute`; Grid + Flex handle it.

### Flexbox model (1-D layouts)

A **flex container** lays its **direct children** out along a **main axis**; the perpendicular axis is the **cross axis**.

Container properties:

| Property        | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| `display: flex` | Turn element into a flex container                                      |
| `flex-direction`| `row` (default) / `row-reverse` / `column` / `column-reverse` — sets main axis |
| `flex-wrap`     | `nowrap` (default) / `wrap` / `wrap-reverse`                            |
| `justify-content`| Distribution along **main** axis: `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `space-evenly` |
| `align-items`   | Alignment of items on **cross** axis: `stretch` (default), `flex-start`, `flex-end`, `center`, `baseline` |
| `align-content` | Distributes wrapped lines on cross axis (only meaningful with `flex-wrap: wrap`) |
| `gap`           | Spacing between items (also valid in Grid)                              |

Item properties:

| Property      | Purpose                                                                           |
|---------------|-----------------------------------------------------------------------------------|
| `flex-grow`   | Share of leftover space this item claims (default `0`)                            |
| `flex-shrink` | How willing this item is to shrink when space is tight (default `1`)              |
| `flex-basis`  | Initial size before grow/shrink (default `auto`)                                  |
| `flex`        | Shorthand: `flex: 1 1 auto;` — grow/shrink/basis                                  |
| `order`       | Reorder visually without touching the HTML (default `0`)                          |
| `align-self`  | Override the container's `align-items` for this one item                          |

### CSS Grid (2-D layouts)

Grid is for **page layout**: rows *and* columns at the same time. The slides walk through the "Holy Grail" layout (header, nav, main, footer) as the motivating example.

Container properties:

| Property                 | Purpose                                                         |
|--------------------------|-----------------------------------------------------------------|
| `display: grid`          | Make the element a grid container                               |
| `grid-template-columns`  | Track sizes for columns, e.g. `200px 1fr` or `repeat(12, 1fr)`  |
| `grid-template-rows`     | Track sizes for rows                                            |
| `grid-template-areas`    | Names rectangular regions for `grid-area`-based placement       |
| `gap` (`row-gap`, `column-gap`) | Space between tracks                                     |
| `justify-items`, `align-items`  | Default placement of cell content within each cell      |
| `justify-content`, `align-content` | Placement of the whole grid inside the container     |

Item placement:

| Property                                   | Purpose                                       |
|--------------------------------------------|-----------------------------------------------|
| `grid-row-start` / `grid-row-end`          | Row span by line numbers                      |
| `grid-column-start` / `grid-column-end`    | Column span by line numbers                   |
| `grid-row: 1 / 3`                          | Shorthand: from line 1 to line 3              |
| `grid-row: span 2`                         | Width-only, no fixed start position           |
| `grid-area: 1 / 2 / 3 / 3`                 | row-start / col-start / row-end / col-end     |

Sizing helpers:

- **`fr` unit** — a *fraction of leftover space* in the container. `1fr 2fr` splits leftover 1:2.
- **`repeat(n, ...)`** — `repeat(12, 1fr)` for a 12-column grid.
- **`minmax(min, max)`** — track is at least `min`, at most `max`. Common: `minmax(200px, 1fr)`.
- **`auto-fill` vs `auto-fit`** — both fill the row with as many `minmax`-sized tracks as fit; `auto-fit` then *collapses* empty tracks (so existing items expand to fill the row), while `auto-fill` keeps the empty tracks reserved.

### Responsive design strategy & mobile-first

Slides position responsive design as **Design Principle 2**: "on the web, use responsive design". The argument: device size varies wildly (phone, tablet, laptop, desktop, TV), so freeze the layout at your peril.

**Mobile-first** means: write your base CSS for the smallest screen (no media query), then progressively enhance with `min-width` media queries as the viewport gets larger. Two reasons:

1. The base case is the simplest layout (single column), which matches the cascade — extra rules layer on top.
2. Forces you to choose what content actually matters: on a 360px screen, you cannot hide behind whitespace.

The opposite (desktop-first) uses `max-width` queries to undo desktop assumptions for small screens.

### Viewport meta tag

For mobile browsers to *honour* your CSS pixel widths instead of zooming out a fake desktop layout, the HTML `<head>` needs:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Without this, a phone reports a virtual 980px viewport and your media queries silently misbehave.

### `@media` queries (typical breakpoints)

Syntax shown in slides:

```css
@media media-type and (media-feature-rule) {
  /* rules */
}
```

`media-type` mostly takes `screen` or `print`. `media-feature-rule` can query `min-width`, `max-width`, `orientation`, pointer presence, colour scheme, etc.

The `trees` lab uses these breakpoints (which line up with common conventions):

| Range             | Meaning            |
|-------------------|--------------------|
| `< 400px`         | small phone        |
| `400–600px`       | large phone        |
| `>= 600px`        | tablet / desktop   |

Other commonly seen breakpoints: 768px (tablet), 1024px (small laptop), 1280px (desktop). The slide deck is explicit that you should not memorise breakpoints — pick them where *your content* breaks.

Combination syntax shown on the slides:

```css
@media screen and (min-width: 600px), screen and (orientation: landscape) { ... }
@media (not (width < 600px)) and (not (width > 1000px)) { ... }
@media (30em <= width <= 50em) { ... }   /* range syntax */
```

### Fluid images

The `trees` lab applies the canonical pattern:

```css
.card-image {
  max-width: 100%;
  height: auto;
}
```

`max-width: 100%` lets the image shrink below its intrinsic size when its container is narrow, and `height: auto` preserves the aspect ratio. Setting a fixed `width` would break responsive behaviour; setting `height` alone would distort the image.

### Design fundamentals (from `Design.pdf`)

The Design slide deck is light on words and heavy on examples; the principles it actually names are:

- **Design is hard, but not thinking about it is disastrous** (Ralph Caplan, slide 2).
- **Design is cultural and fashionable** — what looks "modern" today is dated in five years (slides 3–4).
- **Design Principle 1: test with your intended audience** (slide 5).
- **Gestalt grouping** — proximity, similarity, continuity, closure: viewers see related elements as a group (slides 7–8).
- **Whitespace** is content too — references Knuth's *TeX manual* and the `booktabs` style as exemplars (slide 9). The point: leave room around things; do not fill every pixel.
- **Text width** for readability — "guidelines you may see: 50–60 characters / two full alphabets / 12 words / 30em" per line (slides 10–12). Past about 75 characters the eye has to track too far back to find the next line.
- **Responsive design** — devices vary, design must too (slides 13–15).
- **Design Principle 2: on the web, use responsive design** (slide 16).
- **Grids — "the easy part"**: evenly spaced rectangular grids, with `960.gs` shown as the canonical 960px / 12-column example (slides 17–22).

So the Design.pdf principles actually emphasised are: **whitespace, text width / typography, Gestalt grouping, audience testing, responsive thinking, and grid layout**. (Classical CRAP — Contrast, Repetition, Alignment, Proximity — is implicit in the Gestalt slides but is not the labelling the deck uses.)

## Grid cheat sheet

```css
.holy-grail {
  display: grid;
  grid-template-columns: 200px 1fr;       /* sidebar + flexible main */
  grid-template-rows: auto 1fr auto;      /* header / body / footer */
  grid-template-areas:
    "header header"
    "nav    main"
    "footer footer";
  gap: 16px;
  min-height: 100vh;
}

header { grid-area: header; }
nav    { grid-area: nav; }
main   { grid-area: main; }
footer { grid-area: footer; }

/* Or position by line numbers instead of areas */
.sidebar { grid-row: 2 / 3; grid-column: 1 / 2; }
.banner  { grid-column: 1 / -1; }          /* span all columns */
.spe     { grid-row: span 2; }              /* tall card */

/* Auto-flowing card grid with no media queries */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
```

Key tricks:

- `1fr` = "one share of leftover space" — combine with fixed tracks (`200px 1fr`) for sidebars.
- `repeat(auto-fit, minmax(220px, 1fr))` is the one-liner responsive card grid (no `@media` needed).
- `grid-column: 1 / -1` spans every column (the `-1` line is "last line").
- `grid-row: span 2` claims height without pinning the start row — handy for the SPE unit in the curriculum lab.

## Flexbox cheat sheet

```css
/* Horizontal nav with logo left, links right */
.navbar {
  display: flex;
  align-items: center;          /* vertical centring on cross axis */
  justify-content: space-between;
  gap: 1rem;
  padding: 0 1rem;
}

/* Centred call-to-action box */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;          /* horizontal centring */
  justify-content: center;      /* vertical centring */
  min-height: 60vh;
  text-align: center;
}

/* Card row that wraps and grows */
.card-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
.card-row > .card {
  flex: 1 1 240px;              /* grow, shrink, basis */
}

/* Push the last item to the right */
.toolbar > .spacer {
  margin-left: auto;
}
```

Rules of thumb:

- Flex when the layout is one direction at a time (a row of buttons, a column of form fields).
- Grid when you need rows *and* columns to align (page layout, dashboards).
- `gap` works in both.
- `margin: auto` on a flex item absorbs leftover space — the classic "push to the end" trick.

## Media query patterns

Mobile-first scaffold:

```css
/* Base styles: small screens */
.layout { display: block; }

/* Tablet and up */
@media (min-width: 600px) {
  .layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}

/* Desktop and up */
@media (min-width: 960px) {
  .layout {
    grid-template-columns: 200px 1fr 1fr;
  }
}
```

Useful patterns:

```css
/* Hide on small screens */
@media (max-width: 599px) {
  .sidebar { display: none; }
}

/* Print stylesheet — strip nav, make text black */
@media print {
  nav, .ad { display: none; }
  body { color: black; background: white; }
}

/* Range syntax (modern) */
@media (600px <= width <= 1024px) { ... }

/* Combine with comma = OR */
@media (min-width: 600px), (orientation: landscape) { ... }

/* Respect reduced-motion preference */
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

Container width pattern from the Responsive Layout slides:

```css
/* Bad: locks at 800px even on a phone */
main { width: 800px; }

/* Good: caps at 800px but shrinks on small screens, centred */
main { max-width: 800px; margin: 0 auto; }
```

## Lab walkthrough

### Lab 1 — `curriculum.md` (CV / degree-grid)

**Goal.** Style a CS BSc curriculum (provided `curriculum.html`) into a 12-column grid where each unit's width comes from its credit-point class.

**Given styles.** Body sans-serif on a pale University-of-Bristol green background; each `.unit` has a darker box with a `<b>` title bar (re-declared to `display: block`) and a paragraph. Padding `5px` everywhere keeps text off the edges. Background colour goes on the `.unit` container, not the `<p>`, so the paragraph's default margin is *inside* the coloured area.

**Required behaviour.**

- Apply the grid to `<main>` with **12 equal columns**, `max-width: 1500px`, `margin: 0 auto;` for centring, `gap: 15px`.
- Width of each unit by class:
  - `.cp10` → 2 columns
  - `.cp15` → 3 columns
  - `.cp20` → 4 columns
  - `.cp40` (the project) → 8 columns
  - SPE (`y2-tb4`, no `cp` class) → 4 columns wide and **2 rows tall**
- Goal is the *fewest* rules — one rule per class, ideally.

**Why the naming `cp20` not `20cp`?** Because CSS class selectors cannot start with a digit (`.20cp` is invalid; you would have to escape it). Putting letters first makes the class selector legal.

**Implementation sketch.**

```css
main {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 15px;
  max-width: 1500px;
  margin: 0 auto;
}
.cp10 { grid-column: span 2; }
.cp15 { grid-column: span 3; }
.cp20 { grid-column: span 4; }
.cp40 { grid-column: span 8; }
.y2-tb4 { grid-column: span 4; grid-row: span 2; }
```

**Tricky bit.** SPE is two rows tall, which disrupts the auto-flow of subsequent units. Either pin SPE explicitly with `grid-column-start` / `grid-row-start`, or use `grid-auto-flow: dense` so later items backfill, or let the explicit row/col placement of subsequent year-3 rows resolve it.

**Extra challenge — bigger gap between academic years.** Two equally valid approaches:

1. Leave an empty row of height 0 between year blocks; the two `gap`s on either side double the visual separation.
2. Add `margin-bottom` (not `padding-bottom` — padding would extend the coloured background) to the bottom of TB2/TB4 units of each year.

**Expected result.** Three "rows of rows" — Year 1, Year 2, Year 3 — each made of teaching-block sub-rows, with units ordered left-to-right within each TB, the SPE block straddling year 2, and the 40CP individual project taking up two-thirds of the year-3 TB2 row.

### Lab 2 — `trees.md` (responsive image gallery)

**Goal.** Lay out a deck of tree cards (Westonbirt arboretum) that re-flow at three breakpoints. Some cards have an extra `.featured` class.

**Provided styles.** Body uses Open Sans, header is dark green with white text, each `.card` is mid-green with white text. Critically, `.card-image { max-width: 100%; height: auto; }` makes images fluid.

**Container rules (always-on).**

- `margin: 0 auto;` for horizontal centring (must come before `padding`).
- `margin: 20px 0;` for top/bottom breathing room.
- `padding: 0 10px;` for side breathing room (padding, not margin, otherwise centring breaks).
- `gap: 20px;`.

**Breakpoints.**

| Width range  | Columns | Featured cards | Other cards |
|--------------|---------|----------------|-------------|
| `< 400px`    | 1       | 1×1            | 1×1         |
| `400–599px`  | 2       | 2×2            | 1×1         |
| `>= 600px`   | 4 (max-width 960px) | 2×2 | 1×1         |

**Implementation sketch (mobile-first).**

```css
.container {
  display: grid;
  grid-template-columns: 1fr;        /* default: single column */
  gap: 20px;
  margin: 20px auto;
  padding: 0 10px;
}

@media (min-width: 400px) {
  .container { grid-template-columns: repeat(2, 1fr); }
  .featured  { grid-column: span 2; grid-row: span 2; }
}

@media (min-width: 600px) {
  .container {
    grid-template-columns: repeat(4, 1fr);
    max-width: 960px;
  }
  /* .featured rule still applies (2×2) */
}
```

**Expected behaviour at each breakpoint.**

- **Widescreen (`>= 600px`)**: 4 equal columns, `max-width: 960px`, centred. Two featured cards each occupy a 2×2 super-cell; the other 8 cards fill 1×1 cells around them.
- **Tablet/large phone (`400–600px`)**: only 2 columns; featured cards are still 2×2 (so they fill a whole row pair), regular cards are 1×1.
- **Small phone (`< 400px`)**: 1 column, every card 1×1 — featured cards are no different. This is the *default* (no media query); the trick is to make sure the `featured { span 2 / span 2 }` rule is wrapped in `@media (min-width: 400px)` so it does not leak into the small-screen case.

**Testing tip from the lab.** Chrome/Edge will not let a normal window go below 400px wide. Open DevTools (F12), dock it to the right, and drag the divider to shrink the page area; or use the device-emulation toolbar (the second icon in the top-left of DevTools) and pick a phone preset.

**Closing aside.** In production each card would link to a detail page. The lab suggests using `<a class="card" href="...">` with `display: block` instead of `<div>`, so the entire card (image included) becomes the click target.

## Pitfalls & emphasis

- **Class names cannot start with a digit.** `cp20`, not `20cp` — explicitly called out in the curriculum lab. Same applies to ID selectors.
- **Background colour goes on the right element.** In the curriculum lab the background goes on `.unit`, not on `.unit p`, otherwise the paragraph's default margin punches a hole of body colour through every card.
- **`<b>` is inline by default.** The curriculum lab re-declares `display: block` on it so the title bar fills the cell. This is legal CSS and a good reminder that `display` is a property, not an HTML-tag fact.
- **`margin: 0 auto` then `padding: 0 10px`, not the other way around.** In the trees lab, swapping to `margin: 0 10px;` would lose the centring; padding lives inside the centred box.
- **`max-width`, not `width`.** `width: 800px` freezes the layout and breaks on phones; `max-width: 800px; margin: 0 auto;` caps the desktop case while shrinking gracefully. The Responsive Layout slides hammer this point.
- **Fluid images need both `max-width: 100%` and `height: auto`.** Setting only one distorts the aspect ratio or prevents shrinking.
- **Mobile-first beats desktop-first.** Make the default (no `@media`) the smallest layout and add `min-width` queries to enhance — your CSS is shorter and the cascade is on your side.
- **Do not forget the viewport meta tag.** Without `<meta name="viewport" content="width=device-width, initial-scale=1">`, mobile browsers fake a desktop viewport and your `min-width: 600px` query never matches when you want it to.
- **`display: none` vs `visibility: hidden`.** `none` removes the element from layout entirely (no space reserved); `hidden` keeps the box but makes it invisible. They are not interchangeable.
- **`auto-fill` vs `auto-fit`.** Both create as many `minmax`-sized tracks as fit; `auto-fit` then *collapses* the empty leftover tracks so existing items stretch, while `auto-fill` keeps them. Use `auto-fit` when you want one card to fill the whole row at large widths.
- **Grid wrecks normal flow.** The SPE block in the curriculum lab makes one item taller than the others; `grid-auto-flow: dense` or explicit `grid-row-start` is needed to reorder later items cleanly.
- **Pick breakpoints from your content, not from a list.** The slides list `min-width: 600px` etc. as examples, not as canon. Resize the window until *your* layout breaks, then put the breakpoint there.
- **Whitespace is content.** The Design slides reference Knuth's *TeX manual* and `booktabs` to make the point: empty space organises the eye. Do not fill it just because you can.
- **Text width: 50–60 characters per line.** Wider columns force the eye to track back further; readability falls off a cliff past ~75 chars. Cap with `max-width: 60ch` on text containers.
- **Design is taste plus principles.** The Design.pdf opening quote ("thinking about design is hard, but not thinking about it can be disastrous") frames the chapter: the principles narrow the search space, but you still have to look at it and judge.
