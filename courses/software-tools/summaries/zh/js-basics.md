# 第 15 章 — JavaScript（语言本身 + DOM）

## 章节概览

JavaScript 是 web 的脚本语言。它是解释执行的（带 JIT），动态类型，某些地方有点古怪，但上手容易，每个浏览器都支持。这一章分两半：

1. **语言本身**，通过 Node.js 在命令行里练手。先学变量、数字/字符串、分支、循环、函数、对象、JSON 序列化，把浏览器那一套噪音先撇开。
2. **浏览器里的 JavaScript**，用 **DOM API** 读写一个活的页面。压轴 lab 是写一个扫雷克隆：一个 `<button>` 触发函数清空并重建一个 20×20 的 `<div>` 网格，每个 tile 都用 `addEventListener("click", ...)` 挂上事件。

课程的风格倾向是现代化的：优先 `let`/`const`，少用 `var`；用 `===` 而不是 `==`；事件用 `addEventListener` 挂，不要写 inline 的 `onclick=`；外部脚本用 `type="module"` 或 `defer` 加载，确保 DOM 准备好之后脚本才跑。

## 核心知识

### 变量与类型

写 Python 出身的人会觉得这里挺熟悉，但要先把三种声明搞清楚：

```js
const birthdate = "2005-02-17"   // 不能再赋值
let age = 21                     // 块级作用域，可重新赋值
var legacy = "old"               // 函数作用域，会被 hoist —— 别用
```

- 不变的用 `const`，会变的用 `let`。`var` 只在读老代码时打个照面就行。
- **没有类型声明** —— 类型挂在值上，不挂在变量绑定上（这点和 Python 一样）。
- 原始类型：`Number`、`String`、`Boolean`、`null`、`undefined`，再加上 `BigInt` 和 `Symbol`（lab 里没用）。其他全是 `Object`，包括数组和函数。
- 整数和浮点都共用一个 `Number` 类型（`7`、`7.1`）。其他进制：`0xEF`（十六进制）、`0b01101011`（二进制）。
- `typeof` 返回字符串：`typeof 42 === "number"`、`typeof "hi" === "string"`、`typeof undefined === "undefined"`。

### 数字与运算符

`+ - * /` 行为符合预期。另外：

- `**` 是幂运算，`%` 是取模，`++`/`--` 是自增自减。
- 数字超过 ~`1.79e308` 会溢出成 `Infinity`。除以零也是 `Infinity`（或 `-Infinity`）。`Infinity` 在后续运算里依然存活。
- `Math.random()` 返回 `[0, 1)` 区间的浮点，BMI / FizzBuzz 练习里用到，扫雷布雷也用它。

### 字符串

```js
let bignum = "1001"
console.log(bignum + 3)   // "10013"  —— 字符串拼接，不是加法
```

注意 JS 这里和 Python 不一样：Python 里 `"1001" + 3` 直接抛 TypeError，JS 则会乖乖把 `3` 转成字符串拼上去。

三种引号风格：`'…'`、`"…"`，以及用反引号写的 **template literal**：

```js
const unit = "Software Tools"
const intro = `Welcome to ${unit}`   // 字符串插值
```

常用方法：`.split(" ")`、`.join(" ")`、`.toUpperCase()`、`.toLowerCase()`、`.includes(sub)`、`.length`。

### 相等、真值性、比较

这是 JS 最坑的一段，必须记牢：

- `==` 比较前会做 **类型强制转换** —— `"1" == 1` 是 `true`，`0 == false` 是 `true`。Bug 温床。
- `===` 是严格比较：类型相同 **且** 值相同。基本永远用它。
- "Falsy"（假值）有这几个：`false`、`0`、`""`、`null`、`undefined`、`NaN`。其他全 truthy（包括 `"0"`、`"false"`、`[]`、`{}` —— 注意空数组空对象在 JS 里是真值，跟 Python 不一样）。
- 逻辑运算符短路求值：`a && b`、`a || b`、`!a`。配合 truthy 规则，可以拿来当默认值工具，比如 `name || "Anonymous"`。

### 函数

三种写法，本章都会用到：

```js
// 1. 函数声明 —— 会被 hoist，可以在定义之前调用
function help(topic) {
  console.log(`Sorry, I don't know about ${topic}`)
}

// 2. 函数表达式 —— 赋给变量，不会 hoist
const square = function (x) { return x * x }

// 3. arrow function —— 简洁，且 `this` 继承自外层作用域
const cube = x => x * x * x
const add  = (a, b) => a + b
```

默认参数（`signify` 练习里用到）：

```js
function signify(text, p = 0.3) { /* ... */ }
```

非 arrow function 内部可以拿到 `arguments` 对象，但更干净的写法是 rest 参数：`function f(...args)`。

### 对象

```js
const planet = {}
planet.name = "Earth"        // 点号
planet["rank"] = 3            // 方括号（动态 key 时必用）

const moon = { name: "Moon", rank: 3.1 }   // 对象字面量
planet.moon = moon                          // 对象是引用类型
```

- 方法可以作为属性挂上去：`obn.countdown = function () { return 40 - this.target.age }`。
- 普通函数里 `this` 指向调用它的那个对象。**arrow function** 里的 `this` 是定义它的外层作用域里的 `this`。
- `JSON.stringify(obj)` 序列化成字符串；`JSON.parse(str)` 反序列化。函数不属于 JSON，所以 stringify 时方法会被悄悄丢掉。parse 出来的对象是值的深拷贝 —— 之后改原对象是不会反映过来的。

### 数组

```js
const list = []
list.push(6); list.push(4); list.push(5)
list.sort()             // 修改 list 本身 -> [4, 5, 6]
const sortedCopy = list.toSorted()   // 不修改原数组
list.includes(5)        // true
const i = list.indexOf(4)
list.splice(i, 1)       // 在 index i 处删除 1 个元素（修改原数组）
```

数组字面量（`[1, 2, 3]`）、`.length`、`arr[0]` 索引都是常规操作。很多操作都有「修改原数组」和「不修改」两种版本 —— `sort/toSorted`、`reverse/toReversed`、`splice/slice`。Lab 重点用 `push`、`pop`、`includes`、`indexOf`、`splice`、`length`。

### 控制流

```js
if (a === b && b === c) { /* … */ }
else if (a === b || b === c) { /* … */ }
else { /* … */ }

switch (input) {
  case "hello": console.log("Hi"); break
  case "bye":   console.log("Wait"); break
  default:      console.log("Tell me more")
}

for (let i = 0; i < 10; i++) { /* C 风格 */ }

const list = ["cat", "dog", "pony"]
for (const item of list) { /* 遍历值 */ }
for (const key  of Object.keys(obj)) { /* 遍历对象 key */ }

while (playing) { /* … */ }
do { /* … */ } while (playing)

const label = score > 0 ? "win" : "loss"   // 三元运算符
```

`break` 跳出循环，`continue` 跳到下一轮。`for...in` 也存在，但它遍历的是 **key**（包括继承来的），数组上基本不是你想要的 —— 用 `for...of` 或 `forEach`。

### 模块

扫雷的 HTML 用 `<script type="module" src="minesweeper.js">` 加载脚本。Module script 默认是 deferred 的（DOM 解析完才执行），并且有自己独立的作用域（不会污染全局）。需要 `export`/`import` 时，ES module 的写法是：

```js
// helpers.js
export function bmi(w, h) { /* … */ }
export const PI = 3.14159

// main.js
import { bmi, PI } from "./helpers.js"
```

讲义在这上面没多展开，但 `type="module"` 是当下推荐的现代加载方式。

## DOM API 速查

DOM 是表示页面的活的对象树。`document` 是入口。

```js
// 选择
document.getElementById("tile_1")            // 按 id 拿单个元素
document.querySelector(".board")             // CSS 选择器的第一个匹配
document.querySelector("button")             // 第一个 <button>
document.querySelectorAll("div.board > div") // 所有匹配的 NodeList

// 创建、插入、删除
const div  = document.createElement("div")
div.id = "tile_1"
div.textContent = "*"
parent.appendChild(div)                      // 追加到末尾
parent.insertBefore(newNode, refNode)        // 插到 refNode 前
oldNode.remove()                             // 从树上摘掉

// 读写内容
el.textContent = "hello"        // 安全 —— 纯文本
el.innerHTML  = "<b>hi</b>"     // 解析 HTML；如果内容来自用户就有风险

// 属性 & class
el.setAttribute("data-id", "42")
el.getAttribute("data-id")
el.dataset.id                   // 简写：读写 data-* 属性
el.classList.add("clear")
el.classList.remove("bomb")
el.classList.toggle("flagged")
el.classList.contains("clear")
el.className = "bomb"           // 整个 class 列表覆写

// 事件
btn.addEventListener("click", handler)
btn.addEventListener("contextmenu", e => { e.preventDefault(); /* 右键 */ })

function handler(event) {
  console.log(event.target)   // 触发事件的元素
  console.log(event.type)     // "click", "contextmenu", …
  event.preventDefault()      // 抑制浏览器默认行为
  event.stopPropagation()     // 阻止冒泡到祖先
}

// 事件委托：一个 handler 处理一堆子元素
board.addEventListener("click", e => {
  const tile = e.target.closest("div")
  if (tile && tile.parentElement === board) touchTile(tile.id)
})
```

只要是写文本，`textContent` 优于 `innerHTML` —— 避免误触 HTML 注入。`appendChild` 返回被追加的节点，可以链式调用。`addEventListener` 优于 inline 的 `onclick=`，因为它支持挂多个监听器，也能把行为从 markup 里剥离出去。

## 常用 Array 方法

| 方法 | 返回 | 是否修改原数组？ | 备注 |
|---|---|---|---|
| `arr.forEach(fn)` | `undefined` | 否 | 副作用循环，不能 `break` |
| `arr.map(fn)` | 新数组 | 否 | 对每一项做变换 |
| `arr.filter(fn)` | 新数组 | 否 | 留下 `fn` 为真值的项 |
| `arr.reduce(fn, init)` | 标量 | 否 | 折叠成单个值 |
| `arr.find(fn)` | 元素或 `undefined` | 否 | 第一个匹配 |
| `arr.includes(v)` | `Boolean` | 否 | 严格相等的成员判断 |
| `arr.indexOf(v)` | 索引或 `-1` | 否 | 第一个位置 |
| `arr.push(v)` / `arr.pop()` | 新长度 / 弹出值 | 是 | 数组末尾 |
| `arr.splice(i, n)` | 被删除的项 | 是 | 在 `i` 处删（也能插入） |
| `arr.sort(cmp)` / `arr.toSorted(cmp)` | 数组 | 是 / 否 | 数字排序记得传 `cmp` |

```js
const nums = [1, 2, 3, 4]
nums.map(n => n * n)            // [1, 4, 9, 16]
nums.filter(n => n % 2 === 0)   // [2, 4]
nums.reduce((s, n) => s + n, 0) // 10
nums.find(n => n > 2)           // 3
```

## Lab 实操

### Lab 1 — 命令行 JavaScript（`commandline.md`）

目标：先抛开浏览器，认识语言本身。装 Node（`sudo apt-get install nodejs`），然后 `node` 进 REPL，`node fib.js` 跑文件。

Lab 演示的内容：

- `console.log/info/warn/error/debug` —— REPL 里效果一样，浏览器开发者工具里能区分。
- 算术边界：`10012 ** 85 === Infinity`（溢出）、`1 / 0 === Infinity`、`-1 / 0 === -Infinity`。
- 数组的副作用：`.sort()` 修改原数组，`.toSorted()` 不修改；`.splice(idx, 1)` 原地删除。
- 对象的引用语义 —— 一个属性持有另一个对象时存的是引用，之后改原对象会反映过来。`JSON.stringify`/`JSON.parse` 给你一份值拷贝，但 **会丢掉函数**。
- `fib.js` 里的递归函数和 `for` 循环：

```js
function fib(num) {
  if (num == 0) return 0
  if (num == 1) return 1
  return fib(num - 1) + fib(num - 2)
}
for (let i = 0; i < 10; i++) console.log(i + ": " + fib(i))
```

三个练习：

1. **`bmi(weight, height)`** —— 返回 weight / height² 保留 1 位小数（`Math.round(x * 10) / 10`）；然后扩展成同时返回类别字符串（Underweight < 18.5、Normal 18.5–24.9、…、Severely Obese ≥ 40）。
2. **`fizzbuzz(n)`** —— 打印 1..n，3 的倍数换成 `"fizz"`，5 的倍数换成 `"buzz"`，两者公倍数换成 `"fizzbuzz"`。判断顺序要把组合情况放在最前面。
3. **`signify(text, p = 0.3)`** —— 按空格分词，每个词以概率 `p` 用 `Math.random() < p` 和 `.toUpperCase()` 做大写转换，再 `.join(" ")`。这题的实际考点是默认参数。

### Lab 2 — 扫雷（`minesweeper.md`）

提供文件：`minesweeper.html`（一个 `<button>New Game</button>` 加一个 `<div class="board">`）和 `minesweeper.css`（`grid-template: repeat(20, 1fr) / repeat(20, 1fr)` 做 20×20 网格，附带 `.clear` 和 `.bomb` 样式）。你来写 `minesweeper.js`，并用 `python -m http.server` 起服务，因为 module script 不能从 `file://` 加载。

HTML 里用 `<script type='module' src='minesweeper.js'></script>` 引入脚本，意味着脚本在 DOM 解析完成 **之后** 才执行。

解题骨架，分阶段来：

```js
const mines    = []   // 藏雷的 tile id
const untouched = []  // 玩家还没点过的 tile id
let playable   = true
const ROWS = 20, COLS = 20, TOTAL = ROWS * COLS

const board = document.querySelector("div.board")
document.querySelector("button").addEventListener("click", newGame)

function newGame() {
  // 1. 重置状态 —— board、mines、untouched
  while (board.firstChild) board.firstChild.remove()
  while (mines.length)    mines.pop()
  while (untouched.length) untouched.pop()
  playable = true

  // 2. 创建 400 个 tile，随机布雷
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
  if (!untouched.includes(id)) return            // 已经翻开过

  if (mines.includes(id)) {                      // 3a. 输
    tile.className   = "bomb"
    tile.textContent = "*"
    playable = false
    return
  }

  // 3b. 安全 tile —— 翻开、数邻居、可能扩散
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

  // 4. 胜负判断 —— 剩下没翻的全是雷
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

**关键事件流**：按钮点击 → `newGame` 重建网格 → 每个 tile 的 click 监听器调用 `touchTile(id)` → `touchTile` 读写 DOM、修改 `mines`/`untouched`，并通过 `getNeighbours` 对空白区做递归扩散。

**Lab 特别强调的边界情况：**

- "New Game" 按两次 —— 必须既清掉 DOM 子节点，**也** 清掉 `mines`/`untouched` 数组。
- 算邻居时左右两列的边界 —— `idx % COLS` 给你列号；不做边界检查就会跨行环回到上/下行。
- `mineNeighbours(id) === 0` 时的级联翻开 —— 只对 **之前没翻过** 的邻居递归，否则会无限来回。
- 胜利条件 —— JS 没有内置的数组相等判断，所以比长度，再用 `every` 检查 `untouched` 中的每一项都在 `mines` 里。
- 循环里的闭包 —— `addEventListener("click", () => touchTile(tile.id))` 能正常工作是因为 `tile` 是 `let` 作用域的，每轮一个新绑定。如果用 `var`，400 次就全捕获到同一个绑定上了。

**结尾建议的「锦上添花」**：按危险等级给数字上色、踩雷时显示所有炸弹、用 `contextmenu` 事件实现右键插旗（记得 `e.preventDefault()`）、用 `Date.now()` 或 `performance.now()` 加计时器、用 `localStorage` 存排行榜。

## 易错点与重点

- **`==` vs `===`**：`==` 会强制转换，结果看着合理直到突然不合理（`[] == false` 是 `true`，`null == undefined` 是 `true`，`"" == 0` 是 `true`）。坚持用 `===` 和 `!==`。即便 lab 里写的是 `n == 0`，你也最好用 `n === 0`。
- **Hoisting**：`function` 声明和 `var` 绑定会被 hoist 到所在作用域顶部；`let` 和 `const` 不会（它们处在「temporal dead zone」里，提前用就抛错）。这就是不用 `var` 的实际原因。
- **`this` 绑定**：普通函数里 `this` 取决于你用哪个对象调用 —— `obn.countdown()` 让 `this = obn`。**arrow function** 则在定义处捕获 `this`，这正是回调里想要的行为。扫雷里 `() => touchTile(tile.id)` 的 arrow 形式有双重好处：既冻结 `this`，又让每轮迭代闭包到自己那个 `tile`。
- **闭包**：`() => touchTile(tile.id)` 是一个闭包，闭住了循环里的 `tile` 和模块里的 `touchTile`。每个 tile 都拿到自己绑定的 id，因为 `let` 每轮都创建新绑定。`mines`/`untouched`/`playable` 这些模块级变量也被每个 handler 捕获 —— 没有全局状态，只有共享的词法状态。
- **引用 vs 值**：把对象赋给一个属性时存的是引用。`obn.target = obj` 之后 `obj.age = 33`，通过 `obn.target.age` 也能看到改动。JSON 来回一趟会切断引用并丢掉函数。
- **脚本时机**：脚本在 DOM 构建之前跑，`document.querySelector("button")` 会返回 `null` 然后崩。修法：把 `<script>` 放在 `<body>` 末尾，用 `defer`，用 `type="module"`（默认 deferred），或者把代码放到 `DOMContentLoaded`/`document.body.onload` 监听器里。
- **`textContent` 优于 `innerHTML`**：当值不是受信 HTML 时，避免 XSS 和意外重解析。
- **不要写 inline 事件属性**（`<button onclick="...">`），用 `addEventListener`；可组合，关注点分离，还支持 `{ once: true }`、`{ passive: true }` 这类选项。
- **Same-Origin / `file://`**：ES module 不能从 `file://` 加载，所以扫雷 lab 坚持要用 `python -m http.server` 或 `darkhttpd` 起服务。
- **调试**：`console.log` 做常规追踪，`console.error` 报错（往往会标红并附堆栈），`console.warn` 处理次要问题，`console.table(arr)` 适合形状一致的数组/对象，再加上浏览器 DevTools —— Sources 面板下断点、Elements 看实时 DOM、Network 看请求。
