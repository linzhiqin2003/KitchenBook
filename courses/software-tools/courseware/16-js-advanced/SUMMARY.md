# Chapter 16 — JavaScript (JSON, async, CGI)

## Overview

Week 7 of cs-uob/software-tools shifts JavaScript from "scripting buttons on a
page" to "fetching data and reacting to it asynchronously". The chapter is
short on theory and heavy on one practical skill: build a page that loads a
JSON document over HTTP, renders it, and lets the user query a small
server-side script for extra data. Everything else (Promises, `async/await`,
the event loop, JSON's syntax rules) is the supporting machinery you need to
do that without freezing the UI.

The lab — "A JSON Story" — drives the whole chapter. You serve a folder with
Python's `http.server --cgi`, the browser fetches `anabasis.json`, the JS code
walks its `pages` array to render a one-page-at-a-time reader, and a small
form posts a search term to a CGI script (`cgi-bin/whatmeans`) that proxies
`api.dictionaryapi.dev` and returns the JSON definitions. The lecture slides
intentionally focus on `Promise` plumbing and `fetch`; the lab is where you
practise it.

This summary distils the slides, lab brief, the HTML/CSS scaffold, and the
CGI script into a single reference: enough to write `storypage.js` from
scratch and explain why each line is asynchronous.

## Core knowledge

### JSON: format and JS mapping

JSON ("JavaScript Object Notation") is a text serialisation format whose
grammar is a strict subset of JavaScript object literals. It is the
lingua franca of `fetch` because every browser, every backend, and the
chapter's CGI script all speak it.

Allowed value types and their JS equivalents:

| JSON                  | JavaScript                          |
|-----------------------|-------------------------------------|
| `"string"`            | `String` (UTF-16 in memory)         |
| `42`, `3.14`, `-1e3`  | `Number` (double-precision float)   |
| `true` / `false`      | `Boolean`                           |
| `null`                | `null` (note: not `undefined`)      |
| `[ ... ]`             | `Array`                             |
| `{ "k": v, ... }`     | plain object (string keys only)     |

The `anabasis.json` file used in the lab is a single object whose top
level looks like:

```json
{
  "title": "Anabasis",
  "author": "Xenophon",
  "translator": "Henry Graham Dakyns",
  "pages": ["...page 1 text...", "...page 2 text...", "..."]
}
```

So `story.pages` is an `Array<string>` and each entry is the rendered HTML
for one page.

### `JSON.parse` and `JSON.stringify`

Two static helpers convert between a JSON string and a JS value:

```js
const obj = JSON.parse('{"a":1,"b":[true,null]}')   // -> { a: 1, b: [true, null] }
const txt = JSON.stringify(obj)                     // -> '{"a":1,"b":[true,null]}'
JSON.stringify(obj, null, 2)                        // pretty-print with 2-space indent
```

When you call `response.json()` on a `fetch` `Response`, the browser is
running `JSON.parse` on the response body for you (and returning a
Promise for the parsed value).

### JSON pitfalls

JSON is fussier than JS object literals. The parser will throw a
`SyntaxError` on any of:

- Comments (`//` or `/* */`) — not allowed at all.
- Trailing commas: `[1, 2, 3,]` and `{"a":1,}` are invalid.
- Single quotes: only `"double quotes"` are legal for strings and keys.
- Unquoted keys: `{a: 1}` is JS but not JSON.
- `undefined`, `NaN`, `Infinity`: not representable.
- Functions, dates, regexes: not representable.

When `JSON.parse` fails the whole `.then(r => r.json())` Promise rejects,
which is one of the main reasons you always end a `fetch` chain with
`.catch`.

### Synchronous vs asynchronous execution

Most JS you have written so far is synchronous: each statement finishes
before the next runs.

```js
let b = 20
b++
console.log(b)
```

Some operations — network requests, timers, file I/O, animations — take
unpredictable time. Doing them synchronously would freeze the page (the JS
engine is single-threaded per browsing context). The fix is to mark such
work as asynchronous: the call returns immediately with a placeholder, and
the actual result is delivered later via the event loop.

```js
async function doThing() {
    console.log("Task B started")
    console.log("Task B ended")
}

doThing()
console.log("Task A started")
```

Asynchronous is not the same as multithreaded. There is still only one
call stack; switching only happens at well-defined yield points (an
`await`, the resolution of a Promise, the firing of a timer or event).

### The event loop

The interpreter has a call stack, a (macro-) task queue, and a microtask
queue. While the call stack is non-empty, JS just runs. When it empties,
the runtime drains the microtask queue (Promise callbacks) before pulling
the next task (timers, I/O completions, DOM events). That's why a chain
of `.then` handlers can run in a single tick, while a `setTimeout(fn, 0)`
callback waits for the next loop iteration.

The slides note "there are actually two queues with different
priorities" — microtasks beat tasks. You don't need to memorise the
ordering, but you do need to know that `fetch().then(...)` does not block
event handlers and does not run synchronously.

### Promises: states and methods

A `Promise` is the object an async operation returns to stand in for
"the eventual result". It has three states:

- **pending** — work in progress, no value yet.
- **fulfilled** — work succeeded; the promise has a value.
- **rejected** — work failed; the promise has an error reason.

State transitions are one-shot: a settled promise (fulfilled or
rejected) cannot change again.

You consume a promise with `.then`, `.catch`, `.finally`:

```js
promise
  .then(value => { /* fulfilled handler */ },
        error => { /* rejected handler — rarely used here */ })
  .catch(error => { /* equivalent to .then(null, fn) */ })
  .finally(() => { /* runs in either case, no argument */ })
```

Each `.then` returns a *new* promise, so you can chain. Returning a
value from a handler fulfils the next promise with it; throwing or
returning a rejected promise rejects the next one. A single trailing
`.catch` therefore catches errors from anywhere earlier in the chain.

`Promise.all([p1, p2, ...])` aggregates promises: it fulfils with an
array of all results when every input has fulfilled, and rejects as soon
as any input rejects. Useful when you want to issue several `fetch`
calls in parallel and continue once they're all back. Siblings worth
knowing: `Promise.allSettled` (never rejects, returns status objects),
`Promise.race` (settles with the first to settle), `Promise.any`
(fulfils with the first to fulfil).

### `async` / `await`

`async` in front of a function declaration makes the function always
return a `Promise`. Inside such a function, `await` pauses execution
until the awaited promise settles, then unwraps the value (or throws the
rejection reason).

```js
async function load() {
    const resp = await fetch("anabasis.json")
    const data = await resp.json()
    return data
}

load()
  .then(story => console.log(story.title))
  .catch(err => console.error(err))
```

`await` only works inside `async` functions (and at the top level of ES
modules). Errors are caught with normal `try/catch`:

```js
async function load() {
    try {
        const resp = await fetch("anabasis.json")
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
        return await resp.json()
    } catch (err) {
        console.error("load failed", err)
    }
}
```

### The `fetch` API

`fetch(input, init?)` returns a `Promise<Response>`. The first argument
is a URL or `Request`; the optional second argument is an init object:

```js
fetch("/cgi-bin/whatmeans?term=hello", {
    method: "GET",                     // GET is the default
    headers: { "Accept": "application/json" },
    // body: JSON.stringify({...}),    // for POST/PUT
    // mode: "cors",                   // or "same-origin", "no-cors"
    // credentials: "same-origin",     // include cookies?
    // signal: abortController.signal, // for cancellation
})
```

The returned `Response` has the methods and properties you'll actually
use:

- `response.ok` — `true` for status 200–299. `fetch` only rejects on
  network failure; a 404 or 500 still resolves, so always check `ok`.
- `response.status`, `response.statusText` — HTTP status code/text.
- `response.headers` — a `Headers` object (`response.headers.get(...)`).
- `response.json()` — parses body as JSON, returns `Promise<any>`.
- `response.text()` — body as UTF-8 string, returns `Promise<string>`.
- `response.blob()`, `response.arrayBuffer()`, `response.formData()`.

Each body method consumes the body; you can only call one of them, and
only once. If you need both raw text and JSON, call `text()` and run
`JSON.parse` yourself.

### XHR vs fetch

The slides do not introduce `XMLHttpRequest`. Older code uses it; the
Promise-based `fetch` is the modern replacement and the only API you
need to know for this chapter.

### CGI: how it works

The Common Gateway Interface is one of the oldest ways to plug a script
into a web server. The flow:

1. Browser sends `GET /cgi-bin/whatmeans?term=hello HTTP/1.1`.
2. The server recognises the path as a CGI executable, forks a process,
   and runs it.
3. The server passes request data via environment variables and stdin:
   - `REQUEST_METHOD` (`GET`/`POST`),
   - `QUERY_STRING` (the part after `?`, URL-encoded),
   - `CONTENT_LENGTH`, `CONTENT_TYPE` for POST bodies (read from stdin),
   - `HTTP_*` for incoming headers, plus `SCRIPT_NAME`, `PATH_INFO`, ...
4. The script writes a response to stdout: header lines, a blank line,
   then the body. The server forwards that to the client.
5. The process exits. Each request spawns a fresh process — which is why
   CGI is mostly historical: it does not scale.

The lab uses Python's stdlib server in CGI mode:

```sh
python3 -m http.server --cgi
```

Anything in `cgi-bin/` is treated as executable. The `whatmeans` script
is shebanged `#!/bin/python3`, parses `QUERY_STRING` with
`urllib.parse.parse_qs`, calls `api.dictionaryapi.dev` via `requests`,
and writes the upstream JSON straight back:

```python
print("Content-Type: application/json")
print()                         # blank line ends headers
print(r.text)                   # upstream JSON body
```

Why CGI here at all? Two reasons. (a) It demonstrates the
client/server split without bringing in a framework. (b) Browsers'
**same-origin policy** forbids the page (served from `localhost:8000`)
from calling `api.dictionaryapi.dev` directly with a normal `fetch`
unless that API sends CORS headers, so the CGI script acts as a
same-origin proxy. The lab page can call `cgi-bin/whatmeans` freely; the
script does the cross-origin call server-side, where CORS does not
apply.

### Same-origin policy and CORS

Origin = scheme + host + port. By default, scripts may only `fetch`
their own origin's URLs; cross-origin requests succeed only if the
target server returns `Access-Control-Allow-Origin` (and friends) on the
response. The chapter does not teach CORS in depth, but the CGI proxy
exists because the policy applies. If you tried `fetch` to the
dictionary API directly from the browser, you would either see a CORS
error in the console or, worse, an opaque response with no readable
body.

## fetch & Promise cheat sheet

### Minimum-viable fetch with `.then`

```js
fetch("anabasis.json")
  .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()           // returns a Promise
  })
  .then(data => {
      console.log(data.title)          // "Anabasis"
  })
  .catch(err => console.error(err))
```

### Same thing with `async/await`

```js
async function loadStory() {
    const resp = await fetch("anabasis.json")
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return await resp.json()
}

(async () => {
    try {
        const story = await loadStory()
        console.log(story.pages.length, "pages")
    } catch (err) {
        console.error(err)
    }
})()
```

### POST with a JSON body

```js
const resp = await fetch("/api/echo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ msg: "hi" }),
})
const echoed = await resp.json()
```

### Querystring helper (used in the lab)

```js
const term = "thalassa"
const url  = `cgi-bin/whatmeans?term=${encodeURIComponent(term)}`
const resp = await fetch(url)
const defs = await resp.json()
```

`encodeURIComponent` is the right tool to escape values going into a
querystring; it handles spaces, `&`, `?`, non-ASCII characters, etc.

### `Promise.all` for parallel fetches

```js
const [story, glossary] = await Promise.all([
    fetch("anabasis.json").then(r => r.json()),
    fetch("glossary.json").then(r => r.json()),
])
```

Two requests in flight at once; we resume after both complete. If
either rejects, the `await` throws.

### Common shape

```js
fetch(url)
  .then(r => r.json())          // step 1: get the body
  .then(data => render(data))   // step 2: do something with it
  .catch(err => showError(err)) // step 3: catch anything that went wrong
```

The slides recommend exactly this shape: one `.then` that calls
`response.json()`, a chained `.then` that uses the parsed data, and a
trailing `.catch`.

## Lab walkthrough

The lab is the chapter's deliverable: build `storypage.js` so that
`storypage.html` becomes a one-page-at-a-time reader for `anabasis.json`,
with an in-page dictionary lookup that calls the CGI script.

### Files supplied

- `storypage.html` — minimal scaffold. Loads `storypage.css` and
  `storypage.js` (as `type="module"`). Provides:
  - `<h1>` heading,
  - `<div class="infopane">` for metadata + page counter,
  - `<div class="nav" id="prev">` and `id="next"` for the chevrons,
  - `<div class="page">` where story text goes,
  - `<form id="dictform">` containing `#dictbox` (input),
    a submit button, and `#resultbox` (definitions).
- `storypage.css` — three-column grid (`1fr 3fr 1fr`), peach background,
  centred page panel; nothing scripted.
- `anabasis.json` — `{ title, author, translator, pages: [...] }`. Each
  entry of `pages` is an HTML-bearing string (already contains `<br/>`
  tags etc.).
- `cgi-bin/whatmeans` — the dictionary proxy script.

### Step 1: serve the directory

The browser must load `anabasis.json` and `cgi-bin/whatmeans` over
HTTP, not `file://`. Run, from the lab folder:

```sh
python3 -m http.server --cgi
```

Then open `http://localhost:8000/storypage.html`. The `--cgi` flag is
what makes anything under `cgi-bin/` execute instead of being served
verbatim.

### Step 2: load and stash the story

Create `storypage.js`. Declare a module-level `story` variable, then
`fetch` the JSON and chain a render call:

```js
let story            // current story object
let pageIndex = 0    // which page is showing

fetch("anabasis.json")
  .then(resp => resp.json())
  .then(data => {
      story = data
      initialise()
  })
  .catch(err => {
      document.querySelector(".page").textContent =
          "Could not load story: " + err
  })
```

### Step 3: `initialise()`

Pull DOM nodes once, write metadata, render page 0:

```js
function initialise() {
    document.title = story.title
    document.querySelector("h1").textContent = story.title

    const info = document.querySelector(".infopane")
    info.innerHTML = `
        <p>by ${story.author}, translated by ${story.translator}</p>
        <p>Page <span id="pagenum">1</span> of ${story.pages.length}</p>
    `

    renderPage()
    bindNav()
    bindDictForm()
}

function renderPage() {
    document.querySelector(".page").innerHTML = story.pages[pageIndex]
    document.querySelector("#pagenum").textContent = pageIndex + 1
}
```

### Step 4: navigation

`<` and `>` are plain `<div>` elements; bind `click`. Clamp the index
so `prev` on page 0 and `next` on the last page do nothing.

```js
function bindNav() {
    document.querySelector("#prev").addEventListener("click", () => {
        if (pageIndex > 0) { pageIndex--; renderPage() }
    })
    document.querySelector("#next").addEventListener("click", () => {
        if (pageIndex < story.pages.length - 1) { pageIndex++; renderPage() }
    })
}
```

Optional extension from the brief: add `<input type="number">` to the
infopane, listen for `submit` (or `change`), parse the value, validate
it is in `[1, pages.length]`, set `pageIndex = value - 1`, call
`renderPage`.

### Step 5: the dictionary form

The `<form>` would normally reload the page on submit. Two things to do:

1. `event.preventDefault()` to stop that.
2. Build the URL with `encodeURIComponent` and `fetch` it.

```js
function bindDictForm() {
    const form    = document.querySelector("#dictform")
    const input   = document.querySelector("#dictbox")
    const results = document.querySelector("#resultbox")

    form.addEventListener("submit", async (event) => {
        event.preventDefault()
        const term = input.value.trim()
        if (!term) return

        results.textContent = "Looking up..."
        try {
            const resp = await fetch(
                "cgi-bin/whatmeans?term=" + encodeURIComponent(term))
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
            const data = await resp.json()
            renderDefinitions(data, results)
        } catch (err) {
            results.textContent = "Lookup failed: " + err.message
        }
    })
}
```

### Step 6: render the definitions

The dictionary API returns either an `{ "error": "..." }` object (from
the CGI script's failure path or the upstream API's "no match" reply)
or an array of word objects, each with a `meanings` array, each meaning
having `partOfSpeech` and a `definitions` array of
`{ definition, example?, ... }`. Walk it and append to `#resultbox`:

```js
function renderDefinitions(data, target) {
    target.innerHTML = ""
    if (data.error || !Array.isArray(data)) {
        target.textContent = data.error || "No definitions found."
        return
    }
    for (const word of data) {
        const wordHeader = document.createElement("h3")
        wordHeader.textContent = word.word
        target.appendChild(wordHeader)

        for (const m of word.meanings ?? []) {
            const part = document.createElement("p")
            part.innerHTML = `<em>${m.partOfSpeech}</em>`
            target.appendChild(part)

            const ol = document.createElement("ol")
            for (const d of m.definitions ?? []) {
                const li = document.createElement("li")
                li.textContent = d.definition
                ol.appendChild(li)
            }
            target.appendChild(ol)
        }
    }
}
```

The brief explicitly recommends pretty-printing one example response
(`JSON.stringify(data, null, 2)`) in the console first, so you can see
the structure before writing the renderer.

### What the CGI script does, end to end

```
browser  ──GET cgi-bin/whatmeans?term=hello──►  http.server
                                                   │ fork
                                                   ▼
                                   /usr/bin/python3 whatmeans
                                                   │
                              os.environ["QUERY_STRING"] = "term=hello"
                                                   │
                          requests.get("https://api.dictionaryapi.dev
                                        /api/v2/entries/en/hello")
                                                   │
                              prints "Content-Type: application/json"
                              prints ""
                              prints r.text  (upstream JSON)
                                                   ▼
browser  ◄──── 200 OK + JSON body ─── http.server
```

Notes on the script worth knowing:

- It reads `QUERY_STRING` directly from `os.environ`. If `term` is
  missing it returns `{"error":"No term entered"}` — your renderer
  should handle that.
- The very first `print(args['term'])` is a leftover debug line; it
  appears *before* the `Content-Type` header, which technically
  produces a malformed response. In practice `python -m http.server
  --cgi` is forgiving enough that the browser still sees JSON, but if
  you ever hit a parse error in `response.json()`, this is the first
  place to check.
- A real dependency: `requests` must be installed (`sudo apt install
  python3-requests` per the brief).

## Pitfalls & emphasis

- **Always check `response.ok`.** `fetch` only rejects on network-level
  failure (DNS, offline, CORS). HTTP 4xx/5xx fulfil with a `Response`
  whose `ok` is `false`. Forgetting this is the most common bug.
- **Always end a chain with `.catch`** (or wrap `await` in `try/catch`).
  An unhandled rejection silently breaks the page and only shows up in
  DevTools.
- **`response.json()` itself can reject.** If the server returns HTML
  (e.g. a 500 error page) the parse fails. Handle it the same way as a
  network error.
- **The form needs `event.preventDefault()`.** Without it the browser
  does a full page reload on submit and your `fetch` is cancelled.
- **Use `encodeURIComponent` on querystring values.** Spaces, `&`,
  non-ASCII characters and quotes will otherwise corrupt the URL.
- **`fetch` does not send cookies cross-origin by default.** Not
  relevant for this lab (same origin), but a frequent surprise later.
- **`await` only works inside `async` functions.** Top-level `await` is
  allowed in ES modules, which is why the `<script type="module">` tag
  in `storypage.html` matters if you use it.
- **JSON has no comments and no trailing commas.** The chapter's JSON is
  hand-edited; one stray comma will make `response.json()` reject.
- **CGI is one process per request.** Fine for this lab on localhost,
  not how anybody serves real traffic — modern apps use long-lived
  WSGI/ASGI/Node processes. The lecture frames CGI as historical for
  this reason.
- **Same-origin policy is the reason the proxy exists.** You cannot
  call `api.dictionaryapi.dev` directly from page JS without CORS
  cooperation; the CGI script bridges the gap.
- **Each `Response` body can only be consumed once.** Pick `json()` *or*
  `text()`; don't call both.
- **Asynchronous is not parallel.** There is still one JS thread.
  `Promise.all` overlaps I/O waits, not CPU work.
- **Don't forget to update `pageIndex` *before* calling `renderPage`,
  and to clamp it.** Off-by-one and out-of-bounds are the easy mistakes
  in step 4.
