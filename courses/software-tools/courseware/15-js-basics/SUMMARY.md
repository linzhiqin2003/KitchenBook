# Chapter 15 — JavaScript (language & DOM)

## Overview

JavaScript is the scripting language of the web. It is interpreted (with JIT compilation), dynamically typed, and quirky in places, but easy to start with and supported by every browser. The chapter has two halves:

1. **The language itself**, practised at the command line through Node.js. You learn variables, numbers/strings, branching, loops, functions, objects, and JSON serialisation without any of the browser noise.
2. **JavaScript in the browser**, where you use the **DOM API** to read and modify a live page. The headline lab builds a Minesweeper clone: a `<button>` triggers a function that wipes and rebuilds a 20×20 grid of `<div>` tiles, each wired with `addEventListener("click", ...)`.

The course's stylistic line is modern: prefer `let`/`const` over `var`; use `===` over `==`; attach handlers with `addEventListener` instead of inline `onclick=`; and load external scripts with `type="module"` or `defer` so the DOM is ready before the script runs.

## Core knowledge

### Variables and types

```js
const birthdate = "2005-02-17"   // cannot be reassigned
let age = 21                     // block-scoped, reassignable
var legacy = "old"               // function-scoped, hoisted — avoid
```

- `const` for things that don't get reassigned, `let` otherwise. Reach for `var` only to read old code.
- **No type declarations** — types live on values, not bindings.
- Primitives: `Number`, `String`, `Boolean`, `null`, `undefined`, plus `BigInt` and `Symbol` (not used in the lab). Everything else is an `Object` (arrays and functions included).
- A single `Number` type covers integers and floats (`7`, `7.1`). Other bases: `0xEF` (hex), `0b01101011` (binary).
- `typeof` gives a string: `typeof 42 === "number"`, `typeof "hi" === "string"`, `typeof undefined === "undefined"`.

### Numbers and operators

`+ - * /` work as expected. Plus:

- `**` exponentiation, `%` modulo, `++`/`--` increment/decrement.
- Numbers above ~`1.79e308` overflow to `Infinity`. Division by zero also gives `Infinity` (or `-Infinity`). `Infinity` survives further arithmetic.
- `Math.random()` returns a float in `[0, 1)`. Used both in the BMI/FizzBuzz exercises and for placing mines.

### Strings

```js
let bignum = "1001"
console.log(bignum + 3)   // "10013"  — concatenation, not addition
```

Three quoting styles: `'…'`, `"…"`, and **template literals** with backticks:

```js
const unit = "Software Tools"
const intro = `Welcome to ${unit}`   // string interpolation
```

Useful methods: `.split(" ")`, `.join(" ")`, `.toUpperCase()`, `.toLowerCase()`, `.includes(sub)`, `.length`.

### Equality, truthiness, comparisons

- `==` does **type coercion** before comparing — `"1" == 1` is `true`, `0 == false` is `true`. Source of subtle bugs.
- `===` is strict: same type **and** same value. Prefer it almost always.
- "Falsy" values: `false`, `0`, `""`, `null`, `undefined`, `NaN`. Everything else is truthy (including `"0"`, `"false"`, `[]`, `{}`).
- Logical operators short-circuit: `a && b`, `a || b`, `!a`. Combined with the truthiness rules they double as default-value tools (e.g. `name || "Anonymous"`).

### Functions

Three flavours, all useful in this chapter:

```js
// 1. Function declaration — hoisted, can be called above its definition
function help(topic) {
  console.log(`Sorry, I don't know about ${topic}`)
}

// 2. Function expression — assigned to a variable, not hoisted
const square = function (x) { return x * x }

// 3. Arrow function — concise, inherits `this` from enclosing scope
const cube = x => x * x * x
const add  = (a, b) => a + b
```

Default parameters (used in the `signify` exercise):

```js
function signify(text, p = 0.3) { /* ... */ }
```

The `arguments` object is available inside non-arrow functions, but rest parameters are cleaner: `function f(...args)`.

### Objects

```js
const planet = {}
planet.name = "Earth"        // dot notation
planet["rank"] = 3            // bracket notation (needed for dynamic keys)

const moon = { name: "Moon", rank: 3.1 }   // object literal
planet.moon = moon                          // objects are reference types
```

- Methods can be attached as properties: `obn.countdown = function () { return 40 - this.target.age }`.
- Inside a regular function, `this` is the object the method was called on. Inside an **arrow function** it is whatever `this` was in the enclosing scope.
- `JSON.stringify(obj)` serialises to a string; `JSON.parse(str)` deserialises. Functions are not part of JSON, so methods are silently dropped during stringify. The parsed object is a deep copy of values — later mutations to the original are not reflected.

### Arrays

```js
const list = []
list.push(6); list.push(4); list.push(5)
list.sort()             // mutates list -> [4, 5, 6]
const sortedCopy = list.toSorted()   // non-mutating
list.includes(5)        // true
const i = list.indexOf(4)
list.splice(i, 1)       // remove 1 element at index i (mutating)
```

Array literals (`[1, 2, 3]`), `.length`, and indexing with `arr[0]` work as expected. Many operations have both mutating and non-mutating variants — `sort/toSorted`, `reverse/toReversed`, `splice/slice`. The lab leans on `push`, `pop`, `includes`, `indexOf`, `splice`, and `length`.

### Control flow

```js
if (a === b && b === c) { /* … */ }
else if (a === b || b === c) { /* … */ }
else { /* … */ }

switch (input) {
  case "hello": console.log("Hi"); break
  case "bye":   console.log("Wait"); break
  default:      console.log("Tell me more")
}

for (let i = 0; i < 10; i++) { /* C-style */ }

const list = ["cat", "dog", "pony"]
for (const item of list) { /* values */ }
for (const key  of Object.keys(obj)) { /* iterate object keys */ }

while (playing) { /* … */ }
do { /* … */ } while (playing)

const label = score > 0 ? "win" : "loss"   // ternary
```

`break` exits a loop, `continue` skips to the next iteration. `for...in` exists too but iterates **keys** (including inherited ones) and is rarely what you want for arrays — prefer `for...of` or `forEach`.

### Modules

The Minesweeper HTML loads its script with `<script type="module" src="minesweeper.js">`. Module scripts are deferred by default (run after the DOM is parsed) and have their own scope (no leaking globals). When you need `export`/`import`, the ES module syntax is:

```js
// helpers.js
export function bmi(w, h) { /* … */ }
export const PI = 3.14159

// main.js
import { bmi, PI } from "./helpers.js"
```

The slides keep this light, but `type="module"` is the recommended modern loader.

## DOM API cheat sheet

The DOM is the live tree of objects representing the page. `document` is the entry point.

```js
// Selection
document.getElementById("tile_1")            // one element by id
document.querySelector(".board")             // first match for a CSS selector
document.querySelector("button")             // first <button>
document.querySelectorAll("div.board > div") // NodeList of every match

// Creation, insertion, removal
const div  = document.createElement("div")
div.id = "tile_1"
div.textContent = "*"
parent.appendChild(div)                      // append at end
parent.insertBefore(newNode, refNode)        // before refNode
oldNode.remove()                             // detach from tree

// Reading / writing content
el.textContent = "hello"        // safe — text only
el.innerHTML  = "<b>hi</b>"     // parses HTML; risky if content is user-supplied

// Attributes & classes
el.setAttribute("data-id", "42")
el.getAttribute("data-id")
el.dataset.id                   // shortcut: reads/writes data-* attributes
el.classList.add("clear")
el.classList.remove("bomb")
el.classList.toggle("flagged")
el.classList.contains("clear")
el.className = "bomb"           // overwrites the whole class list

// Events
btn.addEventListener("click", handler)
btn.addEventListener("contextmenu", e => { e.preventDefault(); /* right-click */ })

function handler(event) {
  console.log(event.target)   // element that fired the event
  console.log(event.type)     // "click", "contextmenu", …
  event.preventDefault()      // suppress default browser behaviour
  event.stopPropagation()     // stop bubbling to ancestors
}

// One handler for many children — event delegation
board.addEventListener("click", e => {
  const tile = e.target.closest("div")
  if (tile && tile.parentElement === board) touchTile(tile.id)
})
```

`textContent` is preferred over `innerHTML` whenever you only need text — it avoids accidental HTML injection. `appendChild` returns the appended node, so you can chain. `addEventListener` is preferred over inline `onclick=` because it allows multiple listeners and keeps behaviour out of the markup.

## Useful Array methods

| Method | Returns | Mutates? | Notes |
|---|---|---|---|
| `arr.forEach(fn)` | `undefined` | no | side-effect loop, can't `break` out |
| `arr.map(fn)` | new array | no | transform every item |
| `arr.filter(fn)` | new array | no | keep items where `fn` is truthy |
| `arr.reduce(fn, init)` | scalar | no | fold to a single value |
| `arr.find(fn)` | element or `undefined` | no | first match |
| `arr.includes(v)` | `Boolean` | no | strict-equality membership test |
| `arr.indexOf(v)` | index or `-1` | no | first position |
| `arr.push(v)` / `arr.pop()` | length / popped value | yes | end of array |
| `arr.splice(i, n)` | removed items | yes | remove (and/or insert) at `i` |
| `arr.sort(cmp)` / `arr.toSorted(cmp)` | array | yes / no | provide `cmp` for numeric sort |

```js
const nums = [1, 2, 3, 4]
nums.map(n => n * n)            // [1, 4, 9, 16]
nums.filter(n => n % 2 === 0)   // [2, 4]
nums.reduce((s, n) => s + n, 0) // 10
nums.find(n => n > 2)           // 3
```

## Lab walkthrough

### Lab 1 — Commandline JavaScript (`commandline.md`)

Goal: meet the language without browsers. Install Node (`sudo apt-get install nodejs`), then `node` for a REPL and `node fib.js` to run a file.

Demonstrated in the lab:

- `console.log/info/warn/error/debug` — same effect at the REPL, distinct in browser dev tools.
- Arithmetic edge cases: `10012 ** 85 === Infinity` (overflow), `1 / 0 === Infinity`, `-1 / 0 === -Infinity`.
- Array side effects: `.sort()` mutates, `.toSorted()` doesn't; `.splice(idx, 1)` removes in place.
- Object reference semantics — a property holding another object stores a reference, so later mutations show through. `JSON.stringify`/`JSON.parse` give you a value-copy, but **drop functions**.
- Recursive function and a `for` loop in `fib.js`:

```js
function fib(num) {
  if (num == 0) return 0
  if (num == 1) return 1
  return fib(num - 1) + fib(num - 2)
}
for (let i = 0; i < 10; i++) console.log(i + ": " + fib(i))
```

Three exercises:

1. **`bmi(weight, height)`** — return weight / height² rounded to 1 dp (`Math.round(x * 10) / 10`); then extend to also return a category string from the table (Underweight < 18.5, Normal 18.5–24.9, …, Severely Obese ≥ 40).
2. **`fizzbuzz(n)`** — print 1..n, replacing multiples of 3 with `"fizz"`, multiples of 5 with `"buzz"`, multiples of both with `"fizzbuzz"`. Order the checks so the combined case is tested first.
3. **`signify(text, p = 0.3)`** — split on spaces, capitalise each word with probability `p` using `Math.random() < p` and `.toUpperCase()`, then `.join(" ")`. The default-parameter trick is the actual learning point.

### Lab 2 — Minesweeper (`minesweeper.md`)

Provided files: `minesweeper.html` (a `<button>New Game</button>` and a `<div class="board">`) and `minesweeper.css` (a 20×20 grid via `grid-template: repeat(20, 1fr) / repeat(20, 1fr)`, with `.clear` and `.bomb` styling). You write `minesweeper.js`, served via `python -m http.server` because module scripts can't be loaded from `file://`.

The HTML imports the script as `<script type='module' src='minesweeper.js'></script>`, which means it runs **after** the DOM is parsed.

Skeleton of the solution, stage by stage:

```js
const mines    = []   // ids of tiles that hide a bomb
const untouched = []  // ids of tiles the player hasn't clicked yet
let playable   = true
const ROWS = 20, COLS = 20, TOTAL = ROWS * COLS

const board = document.querySelector("div.board")
document.querySelector("button").addEventListener("click", newGame)

function newGame() {
  // 1. Reset state — board, mines, untouched
  while (board.firstChild) board.firstChild.remove()
  while (mines.length)    mines.pop()
  while (untouched.length) untouched.pop()
  playable = true

  // 2. Build 400 tiles, randomly mark mines
  for (let i = 0; i < TOTAL; i++) {
    const tile = document.createElement("div")
    tile.id = `tile_${i}`
    if (Math.random() < 0.10) mines.push(tile.id)
    untouched.push(tile.id)
    tile.addEventListener("click", () => touchTile(tile.id))
    board.appendChild(tile)
  }
}

function touchTile(id) {
  if (!playable) return
  const tile = document.getElementById(id)
  if (!untouched.includes(id)) return            // already revealed

  if (mines.includes(id)) {                      // 3a. Lose
    tile.className   = "bomb"
    tile.textContent = "*"
    playable = false
    return
  }

  // 3b. Safe tile — reveal, count neighbours, maybe cascade
  tile.className = "clear"
  untouched.splice(untouched.indexOf(id), 1)

  const n = mineNeighbours(id)
  if (n > 0) {
    tile.textContent = String(n)
  } else {
    for (const neighbourId of getNeighbours(id)) {
      if (untouched.includes(neighbourId)) touchTile(neighbourId)
    }
  }

  // 4. Win check — only mines remain untouched
  if (untouched.length === mines.length &&
      untouched.every(t => mines.includes(t))) {
    alert("You won!")
    playable = false
  }
}

function getNeighbours(id) {
  const idx = Number(id.split("_")[1])
  const row = Math.floor(idx / COLS)
  const col = idx % COLS
  const result = []
  for (let dr = -1; dr <= 1; dr++) {
    for (let dc = -1; dc <= 1; dc++) {
      if (dr === 0 && dc === 0) continue
      const r = row + dr, c = col + dc
      if (r < 0 || r >= ROWS || c < 0 || c >= COLS) continue
      result.push(`tile_${r * COLS + c}`)
    }
  }
  return result
}

function mineNeighbours(id) {
  return getNeighbours(id).filter(n => mines.includes(n)).length
}
```

**Key event flow**: button click → `newGame` rebuilds the grid → each tile's click listener calls `touchTile(id)` → `touchTile` reads/writes the DOM, mutates `mines`/`untouched`, and recurses through `getNeighbours` for empty regions.

**Edge cases the lab specifically calls out:**

- "New Game" pressed twice — must wipe both DOM children **and** the `mines`/`untouched` arrays.
- Right and left columns when computing neighbours — `idx % COLS` tells you the column; without a bounds check you'd wrap around to the next/previous row.
- Cascading reveal when `mineNeighbours(id) === 0` — recurse only on **previously un-touched** neighbours, otherwise you ping-pong forever.
- Win condition — JavaScript has no built-in array equality, so you compare lengths and check `every` element of `untouched` is in `mines`.
- Closures inside the loop — `addEventListener("click", () => touchTile(tile.id))` works because `tile` is `let`-scoped per iteration. With `var` you'd capture the same binding 400 times.

**Nice-to-haves** suggested at the end: colour-code numbers by danger level, reveal every bomb when one explodes, right-click flagging via the `contextmenu` event (remember `e.preventDefault()`), a timer using `Date.now()` or `performance.now()`, and a scoreboard kept in `localStorage`.

## Pitfalls & emphasis

- **`==` vs `===`**: `==` coerces, with results that look reasonable until they don't (`[] == false` is `true`, `null == undefined` is `true`, `"" == 0` is `true`). Stick to `===` and `!==`. If the lab tells you to compare `n == 0`, prefer `n === 0`.
- **Hoisting**: `function` declarations and `var` bindings are hoisted to the top of their scope; `let` and `const` are not (they sit in a "temporal dead zone" and throw if used early). This is the practical reason to avoid `var`.
- **`this` binding**: in a regular function, `this` is whatever object you called it on — `obn.countdown()` sets `this = obn`. **Arrow functions** capture `this` from where they were defined, which is exactly what you want for callbacks. The arrow form `() => touchTile(tile.id)` in Minesweeper is doubly useful: it freezes `this` and lets each iteration close over its own `tile`.
- **Closures**: `() => touchTile(tile.id)` is a closure over the loop's `tile` and the module's `touchTile`. Each tile gets its own bound id because `let` creates a fresh binding per iteration. The `mines`/`untouched`/`playable` module-level variables are also captured by every handler — there's no global state, just shared lexical state.
- **Reference vs value**: assigning an object stores a reference. `obn.target = obj` then `obj.age = 33` shows up via `obn.target.age`. JSON round-trips break the reference and drop functions.
- **Script timing**: if your script runs before the DOM is built, `document.querySelector("button")` returns `null` and you crash. Fixes: put the `<script>` at the end of `<body>`, use `defer`, use `type="module"` (deferred by default), or wire up inside a `DOMContentLoaded`/`document.body.onload` listener.
- **`textContent` over `innerHTML`** when the value isn't trusted HTML — avoids both XSS and surprise re-parsing.
- **Inline event attributes** (`<button onclick="...">`) are discouraged. Use `addEventListener`; it composes, separates concerns, and supports options like `{ once: true }` and `{ passive: true }`.
- **Same-Origin / `file://`**: ES modules can't be loaded from `file://`, which is why the Minesweeper lab insists on serving via `python -m http.server` or `darkhttpd`.
- **Debugging**: `console.log` for general traces, `console.error` for problems (often shown red and with a stack trace), `console.warn` for less serious issues, `console.table(arr)` for arrays/objects of similar shape, plus the browser DevTools — Sources panel for breakpoints, Elements for live DOM, Network for requests.
