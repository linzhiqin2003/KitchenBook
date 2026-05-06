# Chapter 12 — HTML

## Overview

HTML (HyperText Markup Language) is the markup language used to write modern web documents. The **HTML5** standard was officially introduced in 2014 and is the version assumed throughout this chapter. HTML5 cleaned up many historical inconsistencies inherited from older HTML/XML versions and added native, standardised tags for features that previously required JavaScript or Adobe Flash plug-ins (e.g. `<video>`, native date pickers).

The chapter approaches HTML through three lenses:

1. **The concept of hypertext** — interactive text that the reader can follow via hyperlinks. Tim Berners-Lee built this idea at CERN to make scientific citations instantly traversable; the "HT" in HTML and HTTP both come from this idea.
2. **Markup as structure** — tags annotate text to describe document structure and meaning. Browsers (or screen readers, search engines, etc.) interpret the markup and render a presentation. Crucially, **structure is meant to be separate from presentation** — visual styling is the job of CSS in the next chapter.
3. **Generating HTML** — hand-writing pages teaches you the model, but in practice pages are generated, either statically (e.g. Markdown compiled by GitHub Pages) or dynamically (server-side templates like **Thymeleaf** rendering data from a database into HTML).

The lab portion has two parts: writing a small valid HTML5 page from scratch and validating it against the W3C validator, then extending a Spring Boot application that uses Thymeleaf templates to render database-backed pages.

The MDN HTML reference (`developer.mozilla.org/en-US/docs/Web/HTML`) is positioned as the working reference for the rest of the web-development portion of the unit.

## Core knowledge

### HTML document skeleton

The minimal valid HTML5 document looks like:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>A web page</title>
  </head>
  <body>
    your content here
  </body>
</html>
```

Key points:

- Everything is nested within a single `<html>` root element.
- `<head>` and `<body>` are siblings inside `<html>`.
- `<head>` contains *metadata* describing `<body>` — title, character encoding, links to stylesheets, etc. It is **not** displayed in the page area.
- `<body>` contains the *visible* portion of the document.
- Tags can be nested; nesting structures the document.
- Tags can carry **attributes** that modify their semantics (e.g. `href` on `<a>`, `lang` on `<html>`).

### DOCTYPE

`<!DOCTYPE html>` is the HTML5 doctype declaration. It must appear as the very first line of the document and tells the browser to render in standards mode. Older HTML/XHTML versions had long, version-specific doctypes; HTML5 deliberately uses this short form.

### `<head>` and meta tags

Common contents of `<head>`:

- `<title>` — the text shown in the browser tab / window title; also used by search engines and as the default bookmark name.
- `<meta charset="utf-8" />` — declares the character encoding. UTF-8 is the modern default and lets you write non-ASCII characters directly in the source.
- `<meta name="...">` — name/value metadata such as `description`, `author`, `viewport`.
- `<link rel="stylesheet" href="...">` — attach an external CSS stylesheet (covered next chapter).
- `<script src="..."></script>` — attach JavaScript (also covered later).

`<head>` is unrelated to HTTP headers despite the name collision — `<head>` is part of the document body sent in the response.

### Semantic structural elements

HTML5 introduced semantic structural tags so authors stop using generic `<div>`s for everything. Their meaning is for screen readers, search engines, and outlining tools — visually they behave like generic blocks until styled.

- `<header>` — the header of a page or section (banner, intro, logo, primary nav).
- `<nav>` — a block of navigation links.
- `<main>` — the main content of the document. Should appear at most once and not be inside `<article>`, `<aside>`, `<header>`, `<footer>` or `<nav>`.
- `<section>` — a thematic grouping of content with a heading.
- `<article>` — self-contained, independently distributable content (a blog post, a comment, a forum entry).
- `<aside>` — content tangentially related to the surrounding content (sidebars, pull quotes).
- `<footer>` — footer for a page or section (copyright, contact, related links).
- `<figure>` / `<figcaption>` — a self-contained figure (image, diagram, code listing) with optional caption.

Compared to the older approach of nesting `<div class="header">` etc., the semantic tags carry the meaning intrinsically, which is what assistive technology relies on.

### Text-level elements

Block-level text containers:

- `<h1>` … `<h6>` — six levels of headings. `<h1>` is the highest level; do not skip levels for visual reasons.
- `<p>` — paragraph.
- `<blockquote>` — block-level quotation.
- `<pre>` — preformatted text (preserves whitespace, monospace font by default).

Inline (phrase) elements with semantic meaning, contrasted in the slides with their old presentational counterparts:

| New (semantic) | Meaning | Old (presentational) |
|----------------|---------|----------------------|
| `<em>` | emphasis | `<i>` (italics) |
| `<strong>` | importance | `<b>` (bold) |
| `<q>` | inline quotation | `<u>` (underline) |
| `<cite>` | citation / title of work | `<s>` (strike out) |
| `<var>` | variable name | `<tt>` (teletype/monospace) |
| `<code>` | source code | `<small>` (smaller text) |

Use the semantic forms; visual weight should come from CSS, not the markup.

Other inline tags worth knowing:

- `<a>` — anchor / hyperlink.
- `<span>` — generic inline container with no semantic meaning (a hook for styling/scripting).
- `<br />` — line break (a void element).

### Lists

Three kinds:

- `<ul>` — unordered list, contains `<li>` items, rendered as bullets by default.
- `<ol>` — ordered list, contains `<li>` items, rendered as numbers by default.
- `<dl>` — description list, contains `<dt>` (term) and `<dd>` (description) pairs.

```html
<ul>
  <li>HTML5</li>
  <li>CSS</li>
  <li>JavaScript</li>
</ul>
```

### Links and link types

`<a href="...">` is the anchor tag. The `href` attribute is what makes the page "hypertext". The slides explicitly cover URL resolution, which is the same model used by HTTP:

Given the page is at `bristol.ac.uk/students/info.html`:

| `href` value | Resolves to |
|--------------|-------------|
| `/courses` | `bristol.ac.uk/courses` (root-relative) |
| `courses` | `bristol.ac.uk/students/courses` (relative to current path) |
| `../courses` | `bristol.ac.uk/courses` (parent-relative) |
| `https://example.com/x` | absolute |

Other useful attributes on `<a>`:

- `target` — where to open the link, e.g. `_blank` for a new tab.
- `rel` — relationship, e.g. `rel="noopener noreferrer"` (recommended with `target="_blank"`), `rel="nofollow"` for SEO.
- `download` — prompts the browser to download the resource rather than navigate to it.

### Images, `<picture>` and `srcset`

- `<img src="..." alt="...">` is a void element. `alt` is **mandatory** for accessibility — it is the text read by screen readers and shown if the image fails to load.
- `width` / `height` attributes give intrinsic dimensions; setting them prevents layout reflow when the image loads.
- `srcset` on `<img>` lets you supply multiple resolutions and a `sizes` hint so the browser picks the right asset for the device pixel ratio and viewport size:

  ```html
  <img src="cat-800.jpg"
       srcset="cat-400.jpg 400w, cat-800.jpg 800w, cat-1600.jpg 1600w"
       sizes="(max-width: 600px) 400px, 800px"
       alt="A black cat sitting on a windowsill" />
  ```

- `<picture>` lets you switch the source by media query or format — useful for art-direction crops or modern formats with a JPEG fallback:

  ```html
  <picture>
    <source srcset="banner.avif" type="image/avif" />
    <source srcset="banner.webp" type="image/webp" />
    <img src="banner.jpg" alt="Sunset over the Avon Gorge" />
  </picture>
  ```

### Tables

Tables are for *tabular data*, not for page layout (use CSS Grid / Flexbox for layout). Structure:

```html
<table>
  <thead>
    <tr><th>Name</th><th>ID</th></tr>
  </thead>
  <tbody>
    <tr><td>Sarah</td><td>100</td></tr>
    <tr><td>Jon</td><td>101</td></tr>
  </tbody>
</table>
```

- `<table>` — the table itself.
- `<thead>` / `<tbody>` / `<tfoot>` — row groups; helps with styling and printing repeated headers.
- `<tr>` — table row.
- `<th>` — header cell (bold and centred by default; carries semantic meaning for assistive tech, particularly with `scope="col"` or `scope="row"`).
- `<td>` — data cell.
- `<caption>` — table caption (placed as the first child of `<table>`).
- `colspan` / `rowspan` attributes merge cells.

The slides also mention `datatables.net` as a JavaScript library that turns a plain `<table>` into an interactive sortable/filterable data table — a good example of progressive enhancement.

### Forms

Forms collect user input and submit it to the server. Skeleton:

```html
<form method="post" action="/comment">
  <p>
    <label for="name">Name:</label>
    <input id="name" name="name" />
  </p>
  <p>
    <button type="submit">OK</button>
  </p>
</form>
```

Key elements:

- `<form action="..." method="get|post">` — wraps the controls. `action` is the URL the data is submitted to, `method` is the HTTP method.
- `<label for="id">…</label>` — associates a caption with a control. Clicking the label focuses the control; required for accessibility.
- `<input>` — single-line input (void element). The `type` attribute controls behaviour (see below). `name` is the key under which the value is sent; `id` is the hook that `<label for>` points to.
- `<textarea>` — multi-line text. Unlike `<input>`, it has a closing tag, and its initial value is its inner text.
- `<select>` containing `<option value="...">` — dropdown:

  ```html
  <select name="animal">
    <option value="dog">Dog</option>
    <option value="cat">Cat</option>
  </select>
  ```

- `<button type="submit|reset|button">` — buttons. `type="submit"` is the default inside a form.
- `<fieldset>` + `<legend>` — group related controls with a caption (renders as a labelled box).

HTML5 `<input type="...">` values covered in the slides:

```
button, checkbox, color, date, datetime-local, email,
file, hidden, image, month, number, password, radio,
range, reset, search, submit, tel, text, time, url, week
```

Plus `<textarea>` for multi-line. Choosing the right type gives mobile users the right keyboard, gives the browser free validation, and gives accessibility tools the right cues.

Validation hints on inputs:

- `required` — must be filled.
- `min`, `max`, `step` — numeric/date constraints.
- `pattern="regex"` — regex validation.
- `maxlength`, `minlength` — string length.
- `autocomplete="name|email|address-line1|country|tel|cc-name|cc-number|…"` — tells the browser/password-manager what to autofill.

```html
<input required type="number" />
<input type="text" autocomplete="name" />
```

### HTML5 additions

Concretely, the chapter highlights the following as HTML5 improvements over previous versions:

- The short `<!DOCTYPE html>` declaration.
- `<meta charset="utf-8" />` short form.
- Semantic structural tags: `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, `<footer>`, `<figure>`, `<figcaption>`.
- New `<input>` types: `email`, `url`, `tel`, `number`, `range`, `color`, `date`, `time`, `datetime-local`, `month`, `week`, `search`.
- Native form validation via `required`, `pattern`, `min`, `max`, type-checking on `email`/`url`/`number`.
- Native `<video>` and `<audio>` tags (replacing Flash).
- New element types and APIs (`<canvas>`, drag-and-drop, geolocation, web storage) that come "for free" without plug-ins.
- Self-closing rules relaxed: void elements like `<br>`, `<img>`, `<input>`, `<meta>` no longer require the trailing `/`, though `<br />` remains valid.

### Character encoding and entities

- Declare encoding in the `<head>` with `<meta charset="utf-8" />` and save the file as UTF-8.
- Some characters must be written as **entities** because they are syntactically significant in HTML, or because they are easier to spell out:
  - `&lt;` for `<`
  - `&gt;` for `>`
  - `&amp;` for `&`
  - `&quot;` for `"`
  - `&apos;` for `'`
  - `&nbsp;` for a non-breaking space
  - Numeric entities like `&#8364;` or `&#x20AC;` for `€` if you cannot type the character directly.
- With UTF-8 declared, you can usually paste characters directly (`€`, `é`, `中`) instead of using entities.

### W3C validation

The lab introduces the **W3C Markup Validator** at `validator.w3.org` as the canonical way to check that a page is valid HTML5. You can submit a URL, upload a file, or paste source. The validator reports errors (e.g. unclosed tags, missing required attributes, misplaced elements) and warnings.

Browser developer tools also surface validation problems:

- Chrome/Edge: the **Console** tab shows an *Issues* counter; clicking it opens the *Issues* tab with descriptions.

Validation is not just pedantic — invalid HTML is parsed in implementation-defined ways and behaves inconsistently across browsers and assistive tech.

### Accessibility basics

Accessibility (a11y) is woven into the markup, not bolted on:

- `lang` attribute on `<html>` so screen readers pick the right pronunciation: `<html lang="en">`.
- Always provide `alt` text on `<img>`. For purely decorative images use `alt=""` (empty string) so screen readers skip them.
- Use heading levels (`<h1>` … `<h6>`) in order — they form the document outline assistive tech uses for navigation.
- Use semantic tags (`<nav>`, `<main>`, `<button>`, `<a>`) instead of generic `<div>` with click handlers — built-in keyboard handling and ARIA roles come for free.
- Always pair form controls with `<label for="...">`.
- Where semantic HTML is insufficient, ARIA roles/attributes (`role="navigation"`, `aria-label`, `aria-hidden`) can supplement — but **prefer the right HTML element first**, since most semantic elements imply the correct ARIA role automatically.
- Optional reading on the GOV.UK site about *progressive enhancement* reinforces this: build a usable HTML baseline first, then layer CSS and JavaScript on top so users on limited devices/networks still get a working page.

## Element cheat sheet

Every tag/attribute that appears in the chapter materials, grouped by purpose.

### Document structure

| Tag | Purpose | Example |
|-----|---------|---------|
| `<!DOCTYPE html>` | HTML5 doctype, must be first line. | `<!DOCTYPE html>` |
| `<html lang="...">` | Root element; `lang` aids screen readers and search. | `<html lang="en">` |
| `<head>` | Container for metadata. | `<head>…</head>` |
| `<body>` | Container for visible content. | `<body>…</body>` |
| `<title>` | Tab/window title. | `<title>A web page</title>` |
| `<meta>` | Metadata key/value (void). | `<meta charset="utf-8" />` |
| `<link>` | External resource, e.g. stylesheet (void). | `<link rel="stylesheet" href="style.css" />` |
| `<script>` | Inline or external JavaScript. | `<script src="app.js"></script>` |

### Semantic structure (HTML5)

| Tag | Purpose | Example |
|-----|---------|---------|
| `<header>` | Page/section header. | `<header><h1>Site</h1></header>` |
| `<nav>` | Navigation block. | `<nav><a href="/">Home</a></nav>` |
| `<main>` | Main content (one per page). | `<main>…</main>` |
| `<section>` | Thematic grouping with a heading. | `<section><h2>Intro</h2>…</section>` |
| `<article>` | Self-contained content. | `<article>…blog post…</article>` |
| `<aside>` | Tangentially related content. | `<aside>related links</aside>` |
| `<footer>` | Page/section footer. | `<footer>© 2025</footer>` |
| `<figure>` / `<figcaption>` | Figure with caption. | `<figure><img …/><figcaption>Fig 1</figcaption></figure>` |

### Generic containers

| Tag | Purpose | Example |
|-----|---------|---------|
| `<div>` | Generic block container, no semantics. | `<div class="card">…</div>` |
| `<span>` | Generic inline container, no semantics. | `<span class="hl">word</span>` |

### Headings and text-level

| Tag | Purpose | Example |
|-----|---------|---------|
| `<h1>` … `<h6>` | Headings, level 1–6. | `<h1>Title</h1>` |
| `<p>` | Paragraph. | `<p>Text.</p>` |
| `<br />` | Line break (void). | `line one<br />line two` |
| `<em>` | Emphasis. | `it is <em>very</em> hot` |
| `<strong>` | Strong importance. | `<strong>Warning</strong>` |
| `<q>` | Inline quotation. | `<q>To be or not to be</q>` |
| `<cite>` | Title of a work. | `<cite>Hamlet</cite>` |
| `<var>` | Variable name. | `<var>x</var>` |
| `<code>` | Source code (inline). | `<code>print(x)</code>` |
| `<pre>` | Preformatted block. | `<pre>text  with   spaces</pre>` |
| `<small>` | Side comments / fine print. | `<small>terms apply</small>` |
| `<blockquote>` | Block quotation. | `<blockquote>…</blockquote>` |

### Lists

| Tag | Purpose | Example |
|-----|---------|---------|
| `<ul>` | Unordered list. | `<ul><li>A</li></ul>` |
| `<ol>` | Ordered list. | `<ol><li>Step 1</li></ol>` |
| `<li>` | List item (in `<ul>` or `<ol>`). | `<li>Item</li>` |
| `<dl>` | Description list. | `<dl><dt>Term</dt><dd>Definition</dd></dl>` |
| `<dt>` | Term in a description list. | `<dt>HTML</dt>` |
| `<dd>` | Description in a description list. | `<dd>Markup language</dd>` |

### Links and media

| Tag | Purpose | Example |
|-----|---------|---------|
| `<a>` | Anchor / hyperlink. | `<a href="/courses">Our Courses</a>` |
| `<img>` | Image (void). | `<img src="cat.jpg" alt="A cat" />` |
| `<picture>` | Responsive/art-directed image wrapper. | `<picture><source …/><img …/></picture>` |
| `<source>` | Alt source for `<picture>`/`<video>`/`<audio>` (void). | `<source srcset="x.webp" type="image/webp" />` |
| `<video>` | Native video player. | `<video src="m.mp4" controls></video>` |
| `<audio>` | Native audio player. | `<audio src="s.mp3" controls></audio>` |

### Tables

| Tag | Purpose | Example |
|-----|---------|---------|
| `<table>` | Table root. | `<table>…</table>` |
| `<caption>` | Table caption. | `<caption>Marks</caption>` |
| `<thead>` | Header row group. | `<thead><tr><th>…</th></tr></thead>` |
| `<tbody>` | Body row group. | `<tbody>…</tbody>` |
| `<tfoot>` | Footer row group. | `<tfoot>…</tfoot>` |
| `<tr>` | Table row. | `<tr>…</tr>` |
| `<th>` | Header cell. | `<th scope="col">Name</th>` |
| `<td>` | Data cell. | `<td>Sarah</td>` |

### Forms

| Tag | Purpose | Example |
|-----|---------|---------|
| `<form>` | Form container. | `<form method="post" action="/comment">…</form>` |
| `<label>` | Caption for a control. | `<label for="name">Name:</label>` |
| `<input>` | Single-line input (void). | `<input id="name" name="name" type="text" />` |
| `<textarea>` | Multi-line input. | `<textarea name="comment"></textarea>` |
| `<select>` | Dropdown. | `<select name="animal">…</select>` |
| `<option>` | Choice in `<select>`. | `<option value="dog">Dog</option>` |
| `<button>` | Button. | `<button type="submit">OK</button>` |
| `<fieldset>` | Group related controls. | `<fieldset><legend>Address</legend>…</fieldset>` |
| `<legend>` | Caption for a `<fieldset>`. | `<legend>Address</legend>` |

### Common attributes

| Attribute | Where | Purpose |
|-----------|-------|---------|
| `id` | Any element | Unique identifier, hook for CSS / JS / `<label for>`. |
| `class` | Any element | Space-separated class names, primary CSS hook. |
| `lang` | Any element (most often `<html>`) | Language of the content. |
| `href` | `<a>`, `<link>` | Target URL. |
| `target` | `<a>` | Where to open the link (`_blank`, `_self`…). |
| `rel` | `<a>`, `<link>` | Relationship (e.g. `stylesheet`, `noopener`). |
| `src` | `<img>`, `<script>`, `<video>`, `<audio>`, `<source>` | Resource URL. |
| `alt` | `<img>` | Text alternative. |
| `srcset`, `sizes` | `<img>`, `<source>` | Responsive image sources. |
| `type` | `<input>`, `<button>`, `<script>`, `<source>` | Specifies kind. |
| `name` | Form controls | Key under which value is submitted. |
| `value` | `<input>`, `<option>`, `<button>` | Submitted/displayed value. |
| `placeholder` | `<input>`, `<textarea>` | Hint text. |
| `required`, `min`, `max`, `step`, `pattern`, `maxlength` | `<input>` | Built-in validation. |
| `autocomplete` | `<input>` | Browser autofill hint. |
| `for` | `<label>` | Associates with the input whose `id` matches. |
| `action`, `method` | `<form>` | Submission URL and HTTP method. |
| `colspan`, `rowspan` | `<th>`, `<td>` | Cell spanning. |
| `scope` | `<th>` | `col` or `row`, for accessibility. |
| `charset` | `<meta>` | Document encoding. |

## Lab walkthrough

### Lab 1 — Basic HTML5 (`lab/basic.md`)

**Objective.** Hand-write a small valid HTML5 page and validate it. Practice the document skeleton, headings, paragraphs, emphasis, links and an unordered list.

**Steps.**

1. Create a file called `index.html`. The name matters: most web servers, when given a URL like `example.com/pages` or `example.com/pages/`, serve `index.html` from inside that folder by convention.
2. Start from the HTML5 template (`<!DOCTYPE html>` + `<html lang="en">` + `<head>`/`<body>`).
3. Reproduce the screenshot in the lab. All body text (except the bullet list) must live inside `<p>` tags. Use `<h1>`/`<h2>` for headings, `<strong>` and `<em>` for inline emphasis, `<a href="…">` for the link, and `<ul>`/`<li>` for the list of learning outcomes.
4. Open the file in your browser to check it renders.
5. Validate the page at `validator.w3.org` (paste, upload, or supply a URL). Also check the browser DevTools *Issues* tab.
6. Compare with the provided sample solution `lab/examplepage.html` — your version may differ but still be valid.

**Reference solution.**

```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>COMS10012 Software Tools</title>
    </head>
    <body>
        <h1>COMS10012 Software Tools</h1>
        <p>
            <strong>This unit teaches you the basics of web development.</strong>
        </p>
        <h2>Content</h2>
        <p>
            Content is a combination of video lectures and reading assignments from the <em>Mozilla Developer Network</em>.
        </p>
        <p>
            You can find the unit page <a href="cs-uob.github.io/COMS10012">on github</a>.
        </p>
        <h2>Learning Outcomes</h2>
        <p>
            After completing this unit, you will be able to use the following:
        </p>
        <ul>
            <li>HTML5</li>
            <li>CSS</li>
            <li>JavaScript</li>
        </ul>
    </body>
</html>
```

**Deliverable.** A validated `index.html` matching the screenshot.

### Lab 2 — Templating with Thymeleaf (`lab/templates.md`)

**Objective.** Move from hand-written static HTML to *server-side rendered* HTML, using the Thymeleaf templating engine inside a Spring Boot application. Understand how data from a back-end is interpolated into templates to produce HTML on demand. The general term for producing a particular page from a template plus data is **rendering**.

**Setup.** The lab application is `server02` in the unit's git repository. Build and run with `mvn spring-boot:run`, then visit `localhost:8000`.

**Application anatomy.**

- `model/` contains a `Database` interface plus `Student` and `Unit` classes — a tiny in-memory university database.
- `Templates.java` configures the Thymeleaf engine; the `@Component` annotation makes Spring manage it. Other classes inject it via `@Autowired`.
- `Controller.java` defines HTTP routes.
- `src/main/resources/web/` holds static HTML.
- `src/main/resources/` holds Thymeleaf templates such as `units.html` and `unit.html`.

**Request flow for `/units`.**

1. The `unitsPage` controller method loads the list of units from the database.
2. It creates a Thymeleaf `Context` and adds a value with key `units` (the list).
3. It renders the `units.html` template with that context and returns the resulting string. Spring sees a `String` return and treats it as the HTML body of the response.

**Thymeleaf syntax in the example template.**

```html
<ul th:each="unit : ${units}">
    <li>
        <a th:href="'/unit/' + ${unit.code}" th:text="${unit.code}"></a>
        <span th:text="${unit.title}"></span>
    </li>
</ul>
```

- Anything prefixed `th:` is processed by Thymeleaf and stripped from the output.
- `th:each="unit : ${units}"` is a `for (Unit unit : units)` loop. The loop variable does not need a type. The tag carrying the `th:each` is rendered once per iteration along with its children, so this produces one `<li>` per unit.
- `th:href` and `th:text` produce the `href` attribute and the inner text of a tag respectively. `${...}` reads from the context. Strings use single quotes; `+` concatenates.
- `${unit.code}` uses *property access* — Thymeleaf calls `getCode()` rather than touching the field directly.
- Thymeleaf only resolves `${...}` *inside attributes*. To inject a plain text value, wrap it in a `<span>` and use `th:text` (this is unlike some engines that allow `${var}` anywhere in the body).

**Routing with path variables.** Clicking a unit goes to `/unit/COMS10012`, handled by `unitDetailPage`. The mapping `/unit/{code}` declares a path variable; the method parameter is annotated with `@PathVariable` so Spring fills it from the URL. The method looks up the unit, returns a 404 page if missing, otherwise renders `unit.html`.

**Exercises.**

- *Basic.* Rewrite the units list page to use a `<table>` instead of a `<ul>`. One row per unit, three columns (code, title, link), plus a header row (`code`, `title`, `link`). The third column is a link with text "details" pointing to `/unit/{code}`. Pure HTML/Thymeleaf change — no Java edits.
- *Intermediate (1).* Add controller methods and templates to list all students and view an individual student. Mirror the unit endpoints (`/students`, `/student/{id}` — note the id is an `int`). Show only id and name for now. Copy-paste from the unit code is fine but understand each change. The `Student` class lives in `src/main/java/softwaretools/server02/model`.
- *Intermediate (2).* `Student.getGrades()` returns a list of (unit, grade) pairs (the unit being a `Unit` object, the grade an `int`). On the student detail page, render a table of unit code, unit title and grade for each pair.

**Deliverable.** A modified `server02` application where `/units` shows a table, `/students` and `/student/{id}` are implemented, and the student page lists grades.

## Pitfalls and emphasis

### Self-closing rules in HTML5

- HTML5 does **not** require the trailing slash on void elements. `<br>`, `<img src="x.jpg" alt="x">`, `<meta charset="utf-8">`, `<input type="text" name="q">` are all valid.
- The `<br />` style is also accepted (XHTML-compatible) and is what the slides use; pick a style and be consistent.
- Non-void elements, in contrast, **must** have a closing tag. `<p>foo<p>bar` does not nest paragraphs — the browser auto-closes the first `<p>` because `<p>` cannot contain another `<p>`.

### Void elements

A void element has no content and no closing tag. The set you will meet in this chapter:

```
<area>, <base>, <br>, <col>, <embed>, <hr>, <img>, <input>,
<link>, <meta>, <param>, <source>, <track>, <wbr>
```

Writing `<br></br>` is invalid. Writing `<img …></img>` is invalid. Use `<br>`/`<br />` and `<img … />` only.

### Nesting rules

The HTML parser has specific rules about which elements may contain which. Common gotchas:

- `<p>` cannot contain block elements like `<div>`, `<ul>`, `<table>` — the parser will silently close your `<p>` early and you will get unexpected DOM.
- `<a>` may contain block-level elements in HTML5 (e.g. you can wrap a whole card), but `<a>` may **not** contain another `<a>` (no nested links) and may not contain `<button>` or interactive controls.
- `<li>` must be a child of `<ul>`, `<ol>` or `<menu>`. `<dt>`/`<dd>` only inside `<dl>`.
- `<tr>` only inside `<table>`/`<thead>`/`<tbody>`/`<tfoot>`. `<th>`/`<td>` only inside `<tr>`.
- `<option>` only inside `<select>`, `<optgroup>` or `<datalist>`.
- A document should have exactly one `<title>`, one `<main>` (visible), one `<h1>` recommended, etc.
- `<head>` and `<body>` are siblings inside `<html>` — `<body>` cannot live inside `<head>` and vice versa.

### Block vs inline confusion

The slides illustrate that `<p>` is a *block* element while `<em>` is *inline*. You can put inline elements inside block elements (`<p>… <em>example</em> …</p>`) but you cannot put a block element inside an inline one. CSS can change visual flow but the HTML parser still applies the structural rules at parse time.

### Common validation errors

When you run your page through `validator.w3.org` you will most often see:

- Missing `alt` on `<img>`.
- Missing `<title>` in `<head>`.
- Missing `<!DOCTYPE html>` or wrong doctype (legacy HTML4/XHTML).
- Missing `lang` attribute on `<html>`.
- Stray block-level elements inside `<p>`.
- Duplicate `id` values on the same page (must be unique).
- `for` on a `<label>` not matching any `id`.
- Closing the wrong tag (`<ul>…</ol>`).
- Using an attribute that is not allowed on that element (e.g. `href` on `<div>`).
- Mismatched character encoding — file saved as Windows-1252 but declared as UTF-8 (or vice versa). Save as UTF-8.

### Emphasis from the chapter

- **Structure first, presentation second.** Choose tags for meaning; CSS comes next chapter for visual styling. A blind user's screen reader depends on you using `<h1>`/`<nav>`/`<button>` correctly, not `<div class="button">`.
- **Use the new semantic tags** (`<em>`, `<strong>`, `<cite>`, `<code>`) instead of the old presentational ones (`<i>`, `<b>`, `<u>`, `<tt>`).
- **`<head>` is not the same thing as an HTTP header** — the slides flag this directly. Don't confuse them.
- **Hand-writing is for learning.** In real systems pages are *generated* — statically (Markdown to HTML, like the unit website itself) or dynamically (Thymeleaf, Jinja, etc.). Lab 2 makes the static-vs-dynamic distinction concrete.
- **Validate.** Browsers are very forgiving and will render almost anything, hiding bugs. Run the W3C validator and check the DevTools *Issues* tab regularly.
- **Progressive enhancement** (linked optional reading) — start with a working HTML baseline, then layer on CSS and JS so users on poor networks or assistive devices still get a usable page.
