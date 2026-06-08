# Chapter 13 — CSS (basics)

## Overview

CSS (Cascading Style Sheets) is the language used to describe how an HTML document is presented visually. While HTML defines structure (the DOM), CSS defines appearance: colours, fonts, spacing, layout, and so on. The week's lectures (`CSS_1.pdf`, `CSS_2.pdf`, `slides.md`) introduce CSS syntax, the most common selectors, the box model, units of measurement, and how to use an existing framework. Two labs put it into practice:

- **`text.md`** — typography-first styling: build a "reading mode" stylesheet, learn relative units, then implement a vertical rhythm grid on top of `reset.css`.
- **`framework.md`** — reuse external work: drop `normalize.css` plus a CSS framework (Milligram, Bulma, optionally Bootstrap) into a page and customise via class names.

Course tagline: *"How I Stopped Worrying and Learned to Love the Box Model."*

A CSS rule is always:

```css
selector {
    property: value;
    /* more declarations */
}
```

The browser combines every applicable rule for an element using the **cascade**: later rules of equal specificity override earlier ones, more specific selectors win, and `!important` is the nuclear option.

## Core knowledge

### Ways to attach CSS to a document

| Method | Syntax | Notes |
|--------|--------|-------|
| External stylesheet | `<link rel="stylesheet" href="mystyle.css">` in `<head>` | The standard / preferred way: cacheable, reusable across pages. |
| Internal (`<style>`) | `<style> p { color: red; } </style>` in `<head>` | Useful for one-off pages or critical CSS. |
| Inline | `<p style="color: red;">…</p>` | Highest specificity (after `!important`); avoid for maintainability. |
| `@import` | `@import url("other.css");` at the top of a stylesheet | Pulls another stylesheet in; slower than `<link>` because the import only starts after the importing file is parsed. |
| User stylesheet | Browser-level "custom CSS" | Lets the user override author styles; usually you should respect the author's intent. |

The slides emphasise: the canonical pattern is one or more external `.css` files referenced via `<link>` from `<head>`.

### Selectors

Simple selectors:

```css
p           { /* every <p> */ }
p, div, main{ /* lists: applies to all of them */ }
.important  { /* every element with class="important" */ }
#title      { /* the single element with id="title" */ }
p.important { /* <p class="important"> only */ }
h1#title    { /* <h1 id="title"> only */ }
*           { /* universal: every element */ }
```

Attribute selectors:

```css
p[name=tim]            { color: red; }
p[class='important']   { /* same as p.important */ }
img[title~='flower']   { /* title attribute contains "flower" as a word */ }
a[href^="https://"]    { /* href starts with https:// */ }
a[href$=".pdf"]        { /* href ends with .pdf */ }
input[type="submit"]   { /* exact match */ }
```

Combinators (positional):

```css
.container p     { /* descendant: any <p> inside .container, any depth */ }
.container > p   { /* child: only direct children */ }
.container ~ p   { /* general sibling: any later <p> at the same level */ }
.container + p   { /* adjacent sibling: only the very next <p> */ }
```

Pseudo-classes (state / position) — selectors that match elements based on something not encoded in the document tree:

```css
a:hover            { color: red; }       /* mouse over */
a:focus            { outline: 2px solid; }/* keyboard focus */
a:visited          { color: purple; }
input:checked      { /* checked checkbox / radio */ }
input:disabled     { opacity: 0.5; }
li:first-child     { /* first child of its parent */ }
li:last-child      { }
li:nth-child(2n)   { /* even children */ }
li:nth-child(odd)  { }
p:not(.important)  { }
```

Pseudo-elements (style a virtual sub-part), written with `::`:

```css
p::first-line   { font-weight: bold; }
p::first-letter { font-size: 200%; }
a::before       { content: "→ "; }
a::after        { content: " ↗"; }
::selection     { background: yellow; }
```

Combinators stack and group freely:

```css
div.important > p,
h1#main,
[title=nowred] ~ span {
    color: red;
}
```

### The cascade, specificity, inheritance, `!important`

When multiple rules target the same element, the browser picks a winner in this order:

1. **Origin & importance** — user agent < user < author; `!important` flips that order.
2. **Specificity** — a four-part score `(inline, IDs, classes/attrs/pseudo-classes, types/pseudo-elements)`. Higher wins.
3. **Source order** — among equally specific rules, the one declared later wins.

Specificity examples:

| Selector | Inline | IDs | Classes / attrs / pseudo-class | Types / pseudo-element | Score |
|----------|-------:|----:|-------------------------------:|-----------------------:|------:|
| `*` | 0 | 0 | 0 | 0 | `0,0,0,0` |
| `p` | 0 | 0 | 0 | 1 | `0,0,0,1` |
| `p span` | 0 | 0 | 0 | 2 | `0,0,0,2` |
| `.important` | 0 | 0 | 1 | 0 | `0,0,1,0` |
| `p.important` | 0 | 0 | 1 | 1 | `0,0,1,1` |
| `ul li.todo` | 0 | 0 | 1 | 2 | `0,0,1,2` |
| `[type="text"]` | 0 | 0 | 1 | 0 | `0,0,1,0` |
| `a:hover` | 0 | 0 | 1 | 1 | `0,0,1,1` |
| `#title` | 0 | 1 | 0 | 0 | `0,1,0,0` |
| `h1#title` | 0 | 1 | 0 | 1 | `0,1,0,1` |
| `style="…"` (inline) | 1 | 0 | 0 | 0 | `1,0,0,0` |
| any rule with `!important` | — | — | — | — | wins (above origin order) |

**Inheritance** — some properties (e.g. `color`, `font-family`, `font-size`, `line-height`, `letter-spacing`) flow down from a parent to descendants automatically. Layout-related properties (`margin`, `padding`, `border`, `width`, …) do **not** inherit. You can force inheritance with `inherit`, reset to default with `initial`, or use `unset`.

**`!important`** — appended to a declaration, it bumps it above normal author rules:

```css
p { color: red !important; }
```

Use sparingly; overuse leads to `!important` arms races where every selector escalates.

### The box model

Every element rendered on the page is a rectangular box made of four concentric layers:

```
┌─────────── margin ────────────┐
│ ┌───────── border ──────────┐ │
│ │ ┌──────── padding ──────┐ │ │
│ │ │      content          │ │ │
│ │ └───────────────────────┘ │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

- **content** — the actual text / image area.
- **padding** — clear space inside the border.
- **border** — the (often invisible) line around the element.
- **margin** — required clear space outside the border.

Shorthand orders sides clockwise from top:

```css
margin-top: 10px;
margin-right: 20px;
margin-bottom: 10px;
margin-left: 5px;

/* same as: */
margin: 10px 20px 10px 5px;

/* 1 value = all sides; 2 = vertical / horizontal; 3 = top / horiz / bottom */
margin: 0 auto;       /* 0 vertical, auto horizontal — the centring trick */
border: 1px solid black;
padding: 0.5em 1em;
```

`box-sizing` controls what `width` and `height` measure:

```css
*, *::before, *::after { box-sizing: border-box; }
```

- `content-box` (default) — `width` is the content area only; padding and border add to the rendered width.
- `border-box` — `width` includes content + padding + border. Easier to reason about; most resets and frameworks set it globally.

Open the dev tools (F12) and inspect any element to see the four layers visualised.

### Units

**Absolute** (try to map to a real-world size):

| Unit | Meaning |
|------|---------|
| `px` | 1 CSS pixel ≈ 1/96 in |
| `pt` | 1 point = 1/72 in |
| `cm` / `mm` | centimetres / millimetres |
| `in` | inch |

Mac defaults ≈ 72 dpi, Windows ≈ 96 dpi; modern phones are 200+ dpi (iPhone 12 Pro ≈ 460), which is why a fixed `px` size can look tiny on mobile.

**Relative** (resize with context):

| Unit | Relative to |
|------|-------------|
| `em` | font-size of the current element (≈ width of an "m") |
| `ex` | x-height of the current font |
| `ch` | width of the "0" glyph in the current font |
| `lh` | line-height of the current element |
| `rem` | font-size of the document root (`<html>`) |
| `%` | the corresponding dimension of the parent element |
| `vw` / `vh` | 1% of viewport width / height |
| `vmin` / `vmax` | 1% of the smaller / larger viewport dimension |

Rule of thumb: prefer `rem` for global sizes (typography, breakpoints), `em` for local proportional spacing inside a component, `%` and viewport units for fluid layout, `px` only when you really mean pixels (1px borders, fine details).

```css
html { font-size: 12pt; }
p    { font-size: 1rem; }
h1   { font-size: 1.8rem; margin-top: 2ex; margin-bottom: 1ex; }
h2   { font-size: 1.4rem; }
```

### Colour values

Where colours appear: `color`, `background-color`, `border-color`, `outline-color`, gradients, shadows, etc.

```css
color: red;                       /* named keyword */
color: #ff0000;                   /* 6-digit hex: rr gg bb */
color: #f00;                      /* short hex: r g b */
color: #ff0000aa;                 /* hex with alpha */
color: rgb(255, 0, 0);            /* 0–255 per channel */
color: rgba(255, 0, 0, 0.5);      /* alpha 0–1 */
color: hsl(0, 100%, 50%);         /* hue 0–360, sat %, light % */
color: hsla(0, 100%, 50%, 0.5);
```

`red` and `#FF0000` are the same; `#FF0001` or `#FF1111` will still look red to the eye. HSL is often easier to reason about for hand-tuned palettes ("same hue, lighter").

### Typography

```css
body {
    font-family: "Helvetica Neue", Arial, sans-serif; /* fallback chain */
    font-size: 16px;          /* default base */
    font-weight: 400;         /* 100–900; or normal/bold */
    font-style: italic;       /* normal | italic | oblique */
    line-height: 1.5;         /* unitless = 1.5 × current font-size */
    letter-spacing: 0.02em;   /* tracking */
    word-spacing: 0.1em;
}
```

Generic family fallbacks (`serif`, `sans-serif`, `monospace`, `cursive`, `system-ui`) are guaranteed to resolve. Loading a web font (e.g. Roboto from Google Fonts) makes the design portable across operating systems:

```html
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
```

### Text properties

```css
text-align: left | right | center | justify;
text-decoration: none | underline | line-through | overline;
text-transform: none | uppercase | lowercase | capitalize;
text-indent: 1em;
white-space: normal | nowrap | pre | pre-wrap;
word-break: normal | break-all | keep-all;
overflow-wrap: normal | break-word | anywhere;
```

### Backgrounds

```css
background-color: #fafafa;
background-image: url("baseline.png");
background-repeat: repeat | repeat-x | no-repeat;
background-position: center top;
background-size: cover | contain | 100% auto;
background-attachment: scroll | fixed;

/* shorthand */
background: #fff url("hero.jpg") no-repeat center / cover;
```

The vertical-rhythm exercise uses `background-image: url("baseline.png")` on `body`, where the image is a 1×20 pixel strip with a coloured last row, repeated to draw a baseline grid behind every element.

### The role of a reset / normalise stylesheet

Browsers ship with their own user-agent stylesheet. Defaults for `<h1>`, `<ul>`, `<button>`, form inputs, etc. differ between Chrome, Firefox, Safari and others — building on top of them is unreliable.

Two common starting points:

- **`reset.css`** (Eric Meyer's `meyerweb.com/eric/tools/css/reset/`) — aggressively zeroes everything: `margin: 0; padding: 0; border: 0; font-size: 100%; font: inherit; vertical-align: baseline;` for almost every element, removes list bullets, sets `display: block` on HTML5 elements for older browsers, kills default quotes, sets `border-collapse: collapse` on tables. After loading, *nothing* looks styled, and you build everything yourself.
- **`normalize.css`** — keeps useful defaults but smooths over inter-browser inconsistencies. Used by Milligram in the lab.

Include the reset/normalise *first*, then your own stylesheet:

```html
<link rel="stylesheet" href="reset.css">
<link rel="stylesheet" href="mystyle.css">
```

### CSS framework concepts

A framework is just a stylesheet (and sometimes a small JS file) that ships a coherent set of rules and utility classes. Three covered:

- **Milligram** — minimalist; styles the entire page by default; pairs with `normalize.css`; provides a `container` class for max-width content.
- **Bulma** — class-based; only the parts you tag get styled. Title + level: `class="title is-1"`. Hero pattern: outer `.hero` with `.hero-body` child. Layout helpers: `.section`, `.container`, `.content`. Source is in SASS and compiled to CSS. Two distribution variants: `bulma.css` (readable) and `bulma.min.css` (minified, smaller download).
- **Bootstrap** — the most popular; component-rich; needs a JS bundle for some interactive components (tabs, modals).

Class-based frameworks deliberately split structure (HTML tags) from styling (class names): `<h1 class="title is-1">` may look redundant, but it lets you change visual hierarchy without changing semantics.

The mobile viewport meta tag is essential when working with any framework on phones:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

## Selector & specificity cheat sheet

| Selector | What it matches | Specificity | Example |
|----------|----------------|-------------|---------|
| `*` | every element | `0,0,0,0` | `* { box-sizing: border-box; }` |
| `p` | every `<p>` | `0,0,0,1` | `p { margin-bottom: 1em; }` |
| `h1, h2, h3` | grouping | each = `0,0,0,1` | `h1, h2 { font-weight: bold; }` |
| `.note` | class | `0,0,1,0` | `.note { color: gray; }` |
| `p.note` | type + class | `0,0,1,1` | `p.note { font-style: italic; }` |
| `[type="text"]` | attribute | `0,0,1,0` | `[type="text"] { border: 1px solid; }` |
| `input[required]` | type + attribute | `0,0,1,1` | |
| `:hover` | pseudo-class | `0,0,1,0` | `a:hover { color: red; }` |
| `:nth-child(2n)` | pseudo-class | `0,0,1,0` | `tr:nth-child(odd) { background: #f7f7f7; }` |
| `::before` | pseudo-element | `0,0,0,1` | `q::before { content: '"'; }` |
| `#main` | id | `0,1,0,0` | `#main { max-width: 60em; }` |
| `h1#main` | type + id | `0,1,0,1` | |
| `nav .item.active` | descendant + 2 classes | `0,0,2,1` | |
| `style="…"` (inline) | inline | `1,0,0,0` | `<p style="color:red">` |
| `… !important` | any + flag | beats normal order | `color: red !important;` |

Combinators (do **not** add to specificity, they only narrow what is matched):

| Combinator | Meaning |
|-----------|---------|
| `A B` (space) | `B` is a descendant of `A` (any depth) |
| `A > B` | `B` is a direct child of `A` |
| `A + B` | `B` is the immediately following sibling of `A` |
| `A ~ B` | `B` is any later sibling of `A` |

## Lab walkthrough

### Lab 1 — Styling Text (`lab/text.md`)

**Goal:** practise typography, relative units, and reset stylesheets on a basic text page (`sometext.html`, a description of the degree).

**Step 1 — "Reading mode" stylesheet.** Create `sometext.css` and link it from the head:

```css
body {
    margin: 0 auto;     /* center horizontally given a fixed width */
    max-width: 40em;    /* limit line length to ~60–70 characters */
    line-height: 125%;  /* room to breathe between lines */
}
```

Why these knobs:

- **`max-width`** in `em` (not `px`) keeps the line length tied to the font, ~40 "m"-widths ≈ 60 characters of average prose, a research-backed sweet spot for readability.
- **`margin: 0 auto`** centres a fixed-width block and keeps text away from the window edge.
- **`line-height: 125%`** opens the lines without going to dissertation-style double-spacing.

Optional further tweaks: `font-size`, `font-family` (`serif`, `sans-serif`, or a system font like `Calibri` knowing it won't exist on every OS), `background-color` for warm-paper or dark-mode looks.

**Step 2 — Reset and rebuild.** Uncomment the `<!-- … -->` line that loads `reset.css`. The page now looks "naked": headings, lists and paragraphs all render as plain text. In your own stylesheet (loaded **after** `reset.css`) rebuild the look. Key principles taught:

- A heading needs whitespace, not just a bigger font: extra `padding`/`margin` above the heading is part of what makes it stand out. More space *above* than *below* — a heading belongs to the text it introduces.
- Use **relative** sizing so user / browser font-size changes still scale: `h1 { font-size: 150%; }` or `h1 { font-size: 1.5rem; }`, never `h1 { font-size: 24px; }`. Test by running `document.body.style.fontSize="24px"` in the dev tools console — relative-sized headings keep their proportion; absolute ones shrink relative to the body.

**Step 3 — Vertical rhythm.** Imagine a 20px grid; lay everything out so paragraph baselines sit on grid lines and headings + spacing are an exact multiple of the grid height.

```css
body {
    background-image: url("baseline.png"); /* 1×20 strip with a pink last row */
}
```

The image tiles, drawing horizontal grid lines you align text against. Constraints:

- Every paragraph baseline sits on a grid line (tune `line-height`, e.g. `1.25` of 16px = 20px exactly).
- Every heading's *total* height (font + padding + margin) is a whole multiple of 20px — even though the heading text itself need not sit on a line.
- All sizes (margins, padding, font-size) must be in relative units (`em` / `rem` / `%`).
- Use `background-color: rgba(0, 0, 255, 0.25)` on headings while debugging to see they fit the grid; if you want a real coloured background later, add `padding-left: 0.5em` so text doesn't kiss the box edge.
- Restore list bullets after the reset:
  ```css
  ul {
      padding-left: 2em;        /* bullets sit in the padding */
      list-style-type: disc;
      list-style-position: outside;
  }
  ```
- Style the link, e.g. `a { text-decoration: underline; }`, optionally distinguishing `:visited`.

**Expected output:** a clean reading page where headings stand out via whitespace, paragraphs have comfortable line length and rhythm, and resizing the body font scales everything proportionally.

### Lab 2 — Frameworks (`lab/framework.md`)

**Goal:** wire third-party stylesheets into a page (`page1.html`, `page2.html`) and customise via class names.

**Milligram (`page1.html`):**

```html
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css">
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.css">
```

Order matters: web font, then `normalize.css`, then `milligram.css`. Loading just the first two leaves margins normalised but typography unchanged (no rule has set `font-family` yet); adding Milligram restyles the whole page (purple Register button, vertical form layout).

Then:

- Add `class="container"` to `<main>` to constrain the content's max width.
- In dev tools, toggle device emulation — text looks tiny on mobile because of pixel density. Fix it with the viewport meta tag (often missing from skeletons):
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  ```
- Inspect Milligram's rules to learn how it sets heading sizes, full-width form fields, vertical label/input stacks, and centred container layout. This is the real exercise — *read the framework's CSS*.

**Bulma (`page2.html`):**

```html
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.css">
```

Bulma is opt-in, class-based:

- Add `class="title"` to the `h1`; refine to `class="title is-1"` for level-1 size, `is-2` for level-2.
- Build a **hero** banner: outer `<header class="hero">` with a child `<div class="hero-body">` wrapping the `<h1 class="title is-1">`.
- Use `<main class="content">` to style descendants by tag, then a child `<div class="container">` for centred fixed width, and `<section class="section">` blocks inside it for spacing:
  ```html
  <main class="content">
      <div class="container">
          <section class="section">
              ... content ...
          </section>
      </div>
  </main>
  ```
- Style the form per Bulma's form docs: full-width fields, labels above fields, primary button (`is-primary` for blue) — same look as the Milligram form, achieved by labelling rather than writing CSS.
- Finally, drop in any other Bulma component (card, navbar, panel, etc.).

**Bootstrap.** Mentioned as the largest and most popular option (built by Twitter); ships JS too for things like tabs and modals; explore in spare time.

**Expected output:** two pages that look professionally styled with no hand-written CSS — only a few class names and one or two `<link>` tags — plus an understanding of two design philosophies (style-everything vs. opt-in classes) and the SASS / CSS / minified CSS distribution chain.

## Pitfalls & emphasis

- **Collapsing margins.** Adjacent vertical margins between block elements *collapse* to the larger of the two, not the sum. A `<p>` with `margin-bottom: 20px` followed by an `<h2>` with `margin-top: 30px` produces 30px of gap, not 50px. Doesn't happen across borders/padding, on inline-block / flex / grid items, or across floated elements. Bites you when you tune spacing in isolation and find it doesn't add up live.
- **Inheritance gotchas.** Typography (`color`, `font-*`, `line-height`, `letter-spacing`) inherits; layout (`margin`, `padding`, `border`, `width`, `background`) does **not**. Setting `color` on `body` styles all descendants; setting `border` on `body` borders only the body. Form controls are notorious for *not* inheriting fonts — set `font: inherit` on `input, button, select, textarea` if you want them to match (this is what `reset.css` does).
- **Specificity wars.** Each rule that loses to a more specific one tempts you to climb up: add an id, then `!important`, then a more nested selector. The fix is to keep selectors *flat and consistent* (a single class per concern, BEM-ish naming, avoid id selectors for styling) — not to escalate. `!important` is a last resort, not a tool.
- **Class vs. id.** Both attach metadata to elements, but they behave differently:
  - `class` is for **styling many things**: many elements can share it, one element can have many. Specificity `0,0,1,0`. Use it for almost everything in CSS.
  - `id` is for **identifying one thing**: must be unique on the page; primarily for in-page links (`#section-3`), JS hooks, and form `for=`/`id=` pairing. Specificity `0,1,0,0` makes it a specificity hammer that creates the wars above. The slides explicitly contrast `<p id='uniquebox'>` (matched by `#uniquebox`) with `<p class='uniquebox'>` (which is **not**) to drive this home.
- **When `reset.css` matters.** Whenever you need pixel-perfect, cross-browser consistent output (frameworks, design systems, anything with a baseline grid). The vertical-rhythm exercise *only works* on a reset because default user-agent margins/padding on `h1`, `p`, `ul` are different per browser. For a quick personal page, browser defaults are fine; for production CSS, start from a reset or normalise.
- **Units muddles.** `em` compounds (a `2em` font inside a `2em` element renders at 4× the root); `rem` doesn't. `%` on `width` is parent-width but on `line-height` is the element's own font-size. `vh`/`vw` ignore scrollbars and can cause horizontal scrolling on mobile if you use `100vw` for full-width sections. The slides' verdict: *"Very easy to get muddled about units."*
- **Hex colour foot-gun.** `#FF0000` and `#FF0001` look identical; tiny typos won't be caught visually. Use named keywords or HSL for hand-typed colours when you can.
- **Mobile pixel density.** On a phone, "16px" is far smaller than on a laptop. Always include `<meta name="viewport" content="width=device-width, initial-scale=1">` on any HTML5 page that targets mobile, *before* you blame the framework.
- **Loading order.** `reset.css` / `normalize.css` first, framework next, your own stylesheet last — otherwise the framework will overwrite your customisations because of source-order tie-breaking.
- **Don't double-space.** `line-height: 200%` is a typewriter-era artefact; nowadays it screams "I copied a dissertation template." `1.4`–`1.6` is the modern range for body copy.
