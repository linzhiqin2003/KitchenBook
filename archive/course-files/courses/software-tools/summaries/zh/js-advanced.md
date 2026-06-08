# Chapter 16 — JavaScript (JSON, async, CGI)

## 章节概览

cs-uob/software-tools 第七周把 JavaScript 的重点从"给页面上的按钮写脚本"挪到了"通过网络拿数据，再异步地对数据做出反应"。这一章理论着墨不多，几乎全在练一件实际的事情：搭一个页面，让它从 HTTP 拉一份 JSON 文档下来、把内容渲染出去，再让用户能去查询服务端的小脚本拿额外数据。其余那些东西——Promise、`async/await`、event loop、JSON 的语法规则——都是为了让这件事能做、而且做的时候不会把 UI 卡死，所配套的支撑机制。

整章是被实验"A JSON Story"驱动起来的。你用 Python 的 `http.server --cgi` 把一个目录起成服务，浏览器把 `anabasis.json` 拉下来，JS 代码沿着它的 `pages` 数组把内容一页一页地渲染成阅读器；再加一个小表单，把搜索词 POST 给一个 CGI 脚本（`cgi-bin/whatmeans`），这个脚本去代理 `api.dictionaryapi.dev`，把 JSON 词条释义返回回来。讲义有意把篇幅花在 `Promise` 的管线和 `fetch` 上；真正的练手放在 lab 里。

这份总结把幻灯片、lab 任务说明、HTML/CSS 脚手架以及 CGI 脚本浓缩成一份参考资料：足够你从零写出 `storypage.js`，并解释清楚每一行为什么是异步的。

## 核心知识

### JSON：格式与到 JS 的映射

JSON（"JavaScript Object Notation"）是一种文本序列化格式，它的语法是 JavaScript 对象字面量的一个严格子集。它之所以是 `fetch` 的通用语言，是因为每一个浏览器、每一个后端、还有这章里的 CGI 脚本都讲它。

允许的值类型以及它们对应的 JS 等价物：

| JSON                  | JavaScript                          |
|-----------------------|-------------------------------------|
| `"string"`            | `String` (UTF-16 in memory)         |
| `42`, `3.14`, `-1e3`  | `Number` (double-precision float)   |
| `true` / `false`      | `Boolean`                           |
| `null`                | `null` (note: not `undefined`)      |
| `[ ... ]`             | `Array`                             |
| `{ "k": v, ... }`     | plain object (string keys only)     |

lab 里用到的 `anabasis.json` 是一个对象，最外层长这样：

```json
{
  "title": "Anabasis",
  "author": "Xenophon",
  "translator": "Henry Graham Dakyns",
  "pages": ["...page 1 text...", "...page 2 text...", "..."]
}
```

所以 `story.pages` 是一个 `Array<string>`，每一项就是一页已经渲染好的 HTML 文本。

### `JSON.parse` 和 `JSON.stringify`

两个静态辅助函数负责在 JSON 字符串和 JS 值之间来回转换：

```js
const obj = JSON.parse('{"a":1,"b":[true,null]}')   // -> { a: 1, b: [true, null] }
const txt = JSON.stringify(obj)                     // -> '{"a":1,"b":[true,null]}'
JSON.stringify(obj, null, 2)                        // pretty-print with 2-space indent
```

当你对 `fetch` 的 `Response` 调用 `response.json()` 时，浏览器其实就是替你跑了一遍 `JSON.parse`（并把解析后的值用一个 Promise 包起来返回给你）。

### JSON 的坑

JSON 比 JS 对象字面量挑剔得多。下面任何一种情况都会让解析器抛 `SyntaxError`：

- 注释（`//` 或 `/* */`）——根本不允许。
- 末尾逗号：`[1, 2, 3,]` 和 `{"a":1,}` 都非法。
- 单引号：字符串和键都只能用 `"双引号"`。
- 不带引号的键：`{a: 1}` 在 JS 里能用，在 JSON 里不行。
- `undefined`、`NaN`、`Infinity`：没法表示。
- 函数、日期、正则：没法表示。

`JSON.parse` 一旦失败，整条 `.then(r => r.json())` 的 Promise 都会被 reject。这也是为什么 `fetch` 链最后总要挂一个 `.catch` 的主要原因之一。

### 同步执行 vs 异步执行

到目前为止你写的大部分 JS 都是同步的：每一条语句执行完，下一条才开始跑。

```js
let b = 20
b++
console.log(b)
```

但有些操作——网络请求、计时器、文件 I/O、动画——耗时是不可预测的。如果同步去做，整个页面就会被冻住（在一个浏览上下文里 JS 引擎只有一条线程）。修复办法是把这类工作标记为异步：调用立刻返回一个占位符，真正的结果稍后通过 event loop 投递回来。

```js
async function doThing() {
    console.log("Task B started")
    console.log("Task B ended")
}

doThing()
console.log("Task A started")
```

异步并不等于多线程。调用栈仍然只有一条；切换只发生在明确定义好的 yield 点上（一次 `await`、一个 Promise 的兑现、一个计时器或事件的触发）。

### event loop

解释器有一个 call stack、一个（宏）任务队列，以及一个 microtask 队列。只要 call stack 不空，JS 就一直跑。一旦栈空了，运行时会先把 microtask 队列（Promise 的回调）抽干，然后才去捞下一个 task（计时器、I/O 完成、DOM 事件）。这就是为什么一连串 `.then` 的 handler 可以在同一个 tick 内跑完，而 `setTimeout(fn, 0)` 的回调却要等下一轮循环。

幻灯片里提到"实际上有两个不同优先级的队列"——microtask 优先级高于 task。你不必把先后顺序背下来，但你得知道：`fetch().then(...)` 不会阻塞事件 handler，也不是同步执行的。

### Promise：状态与方法

`Promise` 是异步操作返回的一个对象，用来代表"最终会拿到的那个结果"。它有三种状态：

- **pending**——工作进行中，还没有值。
- **fulfilled**——工作成功了；promise 持有一个值。
- **rejected**——工作失败了；promise 持有一个错误原因。

状态转移是一次性的：一个已经 settled 的 promise（fulfilled 或 rejected）不会再变。

你用 `.then`、`.catch`、`.finally` 来消费一个 promise：

```js
promise
  .then(value => { /* fulfilled handler */ },
        error => { /* rejected handler — rarely used here */ })
  .catch(error => { /* equivalent to .then(null, fn) */ })
  .finally(() => { /* runs in either case, no argument */ })
```

每个 `.then` 都会返回一个*新的* promise，所以可以一路链下去。从 handler 里 return 一个值会把下一个 promise 兑现成那个值；抛异常或 return 一个 rejected 的 promise，会让下一个被 reject。也正因如此，链尾上挂一个 `.catch` 就能捕获前面任何环节里冒出来的错误。

`Promise.all([p1, p2, ...])` 把一组 promise 聚合起来：当所有输入都 fulfilled 时，它兑现为一个结果数组；任何一个输入 reject，它就立刻 reject。在你想并行发出几个 `fetch`、等它们都回来再继续的时候很合用。还有几个值得知道的兄弟：`Promise.allSettled`（永远不会 reject，返回一组状态对象）、`Promise.race`（第一个 settle 的就让它整个 settle）、`Promise.any`（第一个 fulfill 的就让它 fulfill）。

### `async` / `await`

在函数声明前面加 `async`，会让这个函数总是返回一个 `Promise`。在这种函数内部，`await` 会暂停执行，直到等待的 promise settle，然后把值取出来（或者把 reject 的原因抛出来）。

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

`await` 只能在 `async` 函数里用（以及 ES module 的顶层）。错误用普通的 `try/catch` 抓：

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

### `fetch` API

`fetch(input, init?)` 返回一个 `Promise<Response>`。第一个参数是 URL 或者 `Request`；可选的第二个参数是 init 对象：

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

返回的 `Response` 上你真正会用到的方法和属性是：

- `response.ok`——状态码 200–299 时为 `true`。`fetch` 只会在网络故障时 reject；404 或 500 仍然算 resolve，所以一定要检查 `ok`。
- `response.status`、`response.statusText`——HTTP 状态码和文本。
- `response.headers`——一个 `Headers` 对象（`response.headers.get(...)`）。
- `response.json()`——把 body 当 JSON 解析，返回 `Promise<any>`。
- `response.text()`——把 body 当 UTF-8 字符串，返回 `Promise<string>`。
- `response.blob()`、`response.arrayBuffer()`、`response.formData()`。

每个 body 方法都会消费掉 body；你只能挑其中一个调用，而且只能调一次。如果你既要原始文本又要 JSON，那就调 `text()`，自己再去 `JSON.parse`。

### XHR vs fetch

幻灯片里没有讲 `XMLHttpRequest`。老代码会用它；基于 Promise 的 `fetch` 是它的现代替代品，本章你只需要知道这一个 API 就够了。

### CGI：是怎么跑的

Common Gateway Interface 是把脚本接到 web server 上的最古老方式之一。流程是这样：

1. 浏览器发出 `GET /cgi-bin/whatmeans?term=hello HTTP/1.1`。
2. 服务器认出这条路径对应一个 CGI 可执行文件，fork 出一个进程，把它跑起来。
3. 服务器通过环境变量和 stdin 把请求数据传过去：
   - `REQUEST_METHOD`（`GET`/`POST`），
   - `QUERY_STRING`（`?` 后面那段，已 URL-encode），
   - `CONTENT_LENGTH`、`CONTENT_TYPE` 用于 POST body（从 stdin 读），
   - `HTTP_*` 对应进来的请求头，再加上 `SCRIPT_NAME`、`PATH_INFO`、……
4. 脚本把响应写到 stdout：先是几行响应头，一个空行，然后是 body。服务器把它转发给客户端。
5. 进程退出。每一个请求都会拉起一个全新进程——这也是为什么 CGI 基本上属于历史遗物：它扛不住量。

lab 用的是 Python 标准库自带的服务器开 CGI 模式：

```sh
python3 -m http.server --cgi
```

放在 `cgi-bin/` 里的东西都会被当成可执行文件。`whatmeans` 脚本头部是 `#!/bin/python3`，用 `urllib.parse.parse_qs` 解析 `QUERY_STRING`，通过 `requests` 调 `api.dictionaryapi.dev`，再把上游的 JSON 直接原封不动写回去：

```python
print("Content-Type: application/json")
print()                         # blank line ends headers
print(r.text)                   # upstream JSON body
```

这里为什么要用 CGI？两个原因。(a) 它在不引入框架的前提下演示了客户端/服务端的分离。(b) 浏览器的 **same-origin policy** 不允许从 `localhost:8000` 上的页面用普通 `fetch` 直接调 `api.dictionaryapi.dev`，除非那个 API 主动发回 CORS 响应头；所以这个 CGI 脚本就充当了一个同源代理。lab 页面调 `cgi-bin/whatmeans` 是畅通无阻的；跨域调用由脚本在服务端去做，那一头不走 CORS。

### Same-origin policy 与 CORS

Origin = scheme + host + port。默认情况下，脚本只能 `fetch` 自己 origin 下的 URL；跨域请求只在目标服务器在响应里返回 `Access-Control-Allow-Origin`（以及相关头）的时候才能成功。本章不会深讲 CORS，但 CGI 代理之所以存在，就是因为这条策略真的会生效。如果你尝试从浏览器直接 `fetch` dictionary API，要么会在 console 里看到一条 CORS error，要么更糟——拿到一个不可读 body 的 opaque response。

## fetch 与 Promise 速查

### 用 `.then` 写最小可用 fetch

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

### 同样的事用 `async/await` 写

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

### 带 JSON body 的 POST

```js
const resp = await fetch("/api/echo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ msg: "hi" }),
})
const echoed = await resp.json()
```

### 拼 querystring 的小工具（lab 里用到）

```js
const term = "thalassa"
const url  = `cgi-bin/whatmeans?term=${encodeURIComponent(term)}`
const resp = await fetch(url)
const defs = await resp.json()
```

`encodeURIComponent` 是把值塞进 querystring 时的正确转义工具；空格、`&`、`?`、非 ASCII 字符等等它都能处理。

### 用 `Promise.all` 并行 fetch

```js
const [story, glossary] = await Promise.all([
    fetch("anabasis.json").then(r => r.json()),
    fetch("glossary.json").then(r => r.json()),
])
```

两个请求同时在路上跑；两边都回来后才往下走。任何一边 reject，这条 `await` 都会抛出。

### 常见结构

```js
fetch(url)
  .then(r => r.json())          // step 1: get the body
  .then(data => render(data))   // step 2: do something with it
  .catch(err => showError(err)) // step 3: catch anything that went wrong
```

幻灯片明确推荐就这个结构：一个 `.then` 调 `response.json()`，一个链上去的 `.then` 用解析后的数据，链尾再挂一个 `.catch`。

## Lab 实操

这次 lab 是本章的交付物：写一个 `storypage.js`，让 `storypage.html` 变成针对 `anabasis.json` 的"一次一页"阅读器，并且在页面上能查词典——通过 CGI 脚本去查。

### 已经给你的文件

- `storypage.html`——最小脚手架。引入 `storypage.css` 和 `storypage.js`（用 `type="module"` 加载）。提供：
  - `<h1>` 标题，
  - `<div class="infopane">` 用来放元数据 + 页码，
  - `<div class="nav" id="prev">` 和 `id="next"` 用来放左右箭头，
  - `<div class="page">` 用来放正文，
  - `<form id="dictform">` 里放着 `#dictbox`（输入框）、一个 submit 按钮、还有 `#resultbox`（释义展示区）。
- `storypage.css`——三列网格（`1fr 3fr 1fr`），桃色背景，正文面板居中；没有任何脚本逻辑。
- `anabasis.json`——`{ title, author, translator, pages: [...] }`。`pages` 的每一项都是一段带 HTML 的字符串（已经包含 `<br/>` 之类的标签）。
- `cgi-bin/whatmeans`——查词典的代理脚本。

### Step 1：把目录起成服务

浏览器必须通过 HTTP 加载 `anabasis.json` 和 `cgi-bin/whatmeans`，不能用 `file://`。在 lab 文件夹里跑：

```sh
python3 -m http.server --cgi
```

然后打开 `http://localhost:8000/storypage.html`。`--cgi` 这个 flag 就是让 `cgi-bin/` 下面的东西被执行而不是被当成文件原样发出去的关键。

### Step 2：把 story 加载下来存住

新建 `storypage.js`。声明一个模块级的 `story` 变量，再 `fetch` 那份 JSON，链上一个渲染调用：

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

### Step 3：`initialise()`

把 DOM 节点取出来一次、写元数据、渲染第 0 页：

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

### Step 4：翻页

`<` 和 `>` 是普通 `<div>`；给它们绑 `click`。把 index clamp 一下，让第 0 页上的 `prev` 和最后一页上的 `next` 都什么都不做。

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

任务说明里给的可选扩展：在 infopane 里加一个 `<input type="number">`，监听 `submit`（或 `change`），解析输入值，校验它是否落在 `[1, pages.length]` 区间内，把 `pageIndex = value - 1`，再调 `renderPage`。

### Step 5：词典表单

`<form>` 默认在 submit 时会重新加载页面。要做两件事：

1. `event.preventDefault()` 阻止默认行为。
2. 用 `encodeURIComponent` 拼出 URL，再 `fetch` 它。

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

### Step 6：把释义渲染出来

dictionary API 要么返回一个 `{ "error": "..." }` 对象（来自 CGI 脚本的失败分支或者上游 API 的"查无此词"回复），要么返回一个 word 对象数组——每个 word 有一个 `meanings` 数组，每个 meaning 有 `partOfSpeech` 和一个 `definitions` 数组，里头是 `{ definition, example?, ... }`。沿着这棵结构走一遍，往 `#resultbox` 里 append：

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

任务说明特别建议你先在 console 里把一份样例响应 pretty-print 出来（`JSON.stringify(data, null, 2)`），看清楚结构，再去写 renderer。

### CGI 脚本端到端到底干了什么

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

关于这个脚本，有几点值得知道：

- 它直接从 `os.environ` 读 `QUERY_STRING`。如果没有 `term`，它返回 `{"error":"No term entered"}`——你的 renderer 应该处理这种情况。
- 脚本最开头那行 `print(args['term'])` 是个残留的 debug 输出；它出现在 `Content-Type` 响应头*之前*，从严格意义上讲会产生一条格式错误的响应。实际上 `python -m http.server --cgi` 容错够好，浏览器仍然能拿到 JSON；不过哪天你在 `response.json()` 上踩到解析错误，第一个该查的就是这里。
- 真正的依赖：必须装 `requests`（按任务说明里 `sudo apt install python3-requests`）。

## 易错点与重点

- **永远要检查 `response.ok`。** `fetch` 只在网络层失败时（DNS、断网、CORS）才 reject。HTTP 4xx/5xx 仍然会 fulfill，给你一个 `ok` 为 `false` 的 `Response`。忘记这一点是最常见的 bug。
- **链尾永远挂 `.catch`**（或者把 `await` 包进 `try/catch`）。一个未处理的 rejection 会悄无声息地把页面搞坏，只在 DevTools 里露面。
- **`response.json()` 自己也会 reject。** 如果服务器返回的是 HTML（比如 500 错误页），解析就会失败。处理方式跟网络错误一样。
- **表单需要 `event.preventDefault()`。** 不加的话浏览器会在 submit 时整页刷新，你的 `fetch` 直接被取消。
- **querystring 里的值要用 `encodeURIComponent`。** 否则空格、`&`、非 ASCII 字符、引号都会把 URL 弄坏。
- **`fetch` 默认不会跨域带 cookie。** 本 lab 里无关（同源），但以后经常会让人吃惊。
- **`await` 只能在 `async` 函数里用。** 顶层 `await` 在 ES module 里可以，所以如果你打算用顶层 `await`，`storypage.html` 里那个 `<script type="module">` 就有意义。
- **JSON 没有注释，也没有末尾逗号。** 本章的 JSON 是手工编辑的；多出一个逗号就会让 `response.json()` reject。
- **CGI 是一请求一进程。** 在 localhost 上做 lab 没问题，但没人真用这个跑生产流量——现代应用都用长寿命的 WSGI/ASGI/Node 进程。讲义之所以把 CGI 框成历史，原因就在这。
- **same-origin policy 是这个 proxy 存在的原因。** 在没有 CORS 配合的情况下，你没法直接从页面 JS 调 `api.dictionaryapi.dev`；CGI 脚本搭桥跨过去。
- **每一个 `Response` 的 body 只能消费一次。** 在 `json()` 和 `text()` 里挑一个；别两个都调。
- **异步不等于并行。** JS 仍然只有一条线程。`Promise.all` 重叠的是 I/O 等待时间，而不是 CPU 工作。
- **别忘了在调 `renderPage` *之前*先更新 `pageIndex`，并且把它 clamp 住。** Step 4 里最容易犯的错就是 off-by-one 和越界。
