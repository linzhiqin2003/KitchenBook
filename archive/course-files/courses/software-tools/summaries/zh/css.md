# 第 13 章 — CSS（基础）

## 章节概览

CSS（Cascading Style Sheets，层叠样式表）是用来描述 HTML 文档视觉呈现的语言。HTML 负责定义结构（也就是 DOM），CSS 则负责定义外观：颜色、字体、间距、布局等等。本周的讲义（`CSS_1.pdf`、`CSS_2.pdf`、`slides.md`）介绍了 CSS 的语法、最常见的选择器、box model（盒模型）、度量单位，以及如何使用一个现成的框架。两个 lab 把这些知识落到实处：

- **`text.md`** — 以排版为先的样式练习：先做一份"阅读模式"样式表，学习相对单位，再在 `reset.css` 之上实现一套垂直韵律网格。
- **`framework.md`** — 复用别人的成果：把 `normalize.css` 加上一个 CSS 框架（Milligram、Bulma，可选 Bootstrap）引入到页面里，通过类名做定制。

课程标语写得颇为有趣：*"How I Stopped Worrying and Learned to Love the Box Model."*

一条 CSS 规则永远是这样的形态：

```css
selector {
    property: value;
    /* more declarations */
}
```

浏览器会通过 **cascade**（层叠机制）把所有适用于某个元素的规则合并起来：在 specificity 相同的情况下，后写的规则覆盖先写的；selector 越具体则胜出；`!important` 是核选项。

## 核心知识

### 把 CSS 挂到文档上的几种方式

| 方法 | 写法 | 备注 |
|------|------|------|
| 外部样式表 | 在 `<head>` 里写 `<link rel="stylesheet" href="mystyle.css">` | 标准且首选的做法：可缓存、可在多页面间复用。 |
| 内部 (`<style>`) | 在 `<head>` 里写 `<style> p { color: red; } </style>` | 适用于一次性页面或 critical CSS。 |
| 行内 (inline) | `<p style="color: red;">…</p>` | 除了 `!important` 之外 specificity 最高；不利于维护，应避免。 |
| `@import` | 在样式表顶部写 `@import url("other.css");` | 引入另一份样式表；比 `<link>` 慢，因为 import 要等到当前文件解析后才开始。 |
| 用户样式表 | 浏览器层面的"自定义 CSS" | 让用户能覆盖作者的样式；通常你应该尊重作者的意图。 |

讲义反复强调：标准做法是用 `<head>` 中的 `<link>` 引用一份或多份外部 `.css` 文件。

### Selectors（选择器）

简单选择器：

```css
p           { /* every <p> */ }
p, div, main{ /* lists: applies to all of them */ }
.important  { /* every element with class="important" */ }
#title      { /* the single element with id="title" */ }
p.important { /* <p class="important"> only */ }
h1#title    { /* <h1 id="title"> only */ }
*           { /* universal: every element */ }
```

属性选择器：

```css
p[name=tim]            { color: red; }
p[class='important']   { /* same as p.important */ }
img[title~='flower']   { /* title attribute contains "flower" as a word */ }
a[href^="https://"]    { /* href starts with https:// */ }
a[href$=".pdf"]        { /* href ends with .pdf */ }
input[type="submit"]   { /* exact match */ }
```

Combinators（组合器，按位置组合）：

```css
.container p     { /* descendant: any <p> inside .container, any depth */ }
.container > p   { /* child: only direct children */ }
.container ~ p   { /* general sibling: any later <p> at the same level */ }
.container + p   { /* adjacent sibling: only the very next <p> */ }
```

Pseudo-classes（伪类，匹配状态或位置） — 它们根据"文档树里没有显式编码"的某种状态来选择元素：

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

Pseudo-elements（伪元素，给元素的某个虚拟"子部分"加样式），用 `::` 写：

```css
p::first-line   { font-weight: bold; }
p::first-letter { font-size: 200%; }
a::before       { content: "→ "; }
a::after        { content: " ↗"; }
::selection     { background: yellow; }
```

Combinators 可以自由叠加、分组：

```css
div.important > p,
h1#main,
[title=nowred] ~ span {
    color: red;
}
```

### Cascade、specificity、inheritance、`!important`

当多条规则同时命中同一个元素时，浏览器按以下顺序决定胜者：

1. **Origin & importance（来源与重要级别）** — user agent < user < author；`!important` 会反转这个顺序。
2. **Specificity（特异性）** — 一个四元打分 `(inline, IDs, classes/attrs/pseudo-classes, types/pseudo-elements)`，分数高者胜。
3. **Source order（源顺序）** — 在 specificity 相同的规则里，后写的胜出。

Specificity 的具体算例：

| 选择器 | Inline | IDs | Classes / attrs / pseudo-class | Types / pseudo-element | 得分 |
|--------|-------:|----:|-------------------------------:|-----------------------:|-----:|
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
| 任何带 `!important` 的规则 | — | — | — | — | 胜出（凌驾于 origin 顺序） |

为什么要这样算？因为这套机制天然地反映了"具体优先于宽泛"的直觉：你写的 `#login-button` 显然是在精确锁定一个东西，比通用的 `button` 意图更明确，所以理应胜出。四元组也保证了 ID 的权重永远盖过任意多个 class（`0,1,0,0` 永远大于 `0,0,99,0`），不会互相溢出。

**Inheritance（继承）** — 有些属性（例如 `color`、`font-family`、`font-size`、`line-height`、`letter-spacing`）会自动从父元素流到所有后代上。和布局相关的属性（`margin`、`padding`、`border`、`width`……）则**不**继承。你可以用 `inherit` 强制继承，用 `initial` 重置成默认值，也可以用 `unset`。

**`!important`** — 把它附加在某个声明后面，可以让这条规则压过普通的 author 规则：

```css
p { color: red !important; }
```

省着用。一旦泛滥就会演变成 `!important` 军备竞赛，每个选择器都不得不互相加码。

### Box model（盒模型）

页面上渲染出来的每一个元素都是一个矩形盒子，由四层同心结构组成：

```
┌─────────── margin ────────────┐
│ ┌───────── border ──────────┐ │
│ │ ┌──────── padding ──────┐ │ │
│ │ │      content          │ │ │
│ │ └───────────────────────┘ │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

- **content** — 实际的文字 / 图片区域。
- **padding** — border 内侧的留白。
- **border** — 元素周围的（往往不可见的）边框线。
- **margin** — border 外侧应保持的留白。

简写按"从顶部开始顺时针"的顺序排列各边：

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

`box-sizing` 决定 `width` 和 `height` 到底量的是哪一块：

```css
*, *::before, *::after { box-sizing: border-box; }
```

- `content-box`（默认）— `width` 只算 content 区域，padding 和 border 会"额外"加到渲染出来的宽度上。
- `border-box` — `width` 包含 content + padding + border。心算起来友好得多，绝大多数 reset 和框架都会全局把它打开。

按 F12 打开开发者工具，随便选中一个元素，就能看到这四层被可视化出来。

### Units（单位）

**绝对单位**（试图对应到现实世界尺寸）：

| 单位 | 含义 |
|------|------|
| `px` | 1 CSS pixel ≈ 1/96 in |
| `pt` | 1 point = 1/72 in |
| `cm` / `mm` | 厘米 / 毫米 |
| `in` | 英寸 |

Mac 默认 ≈ 72 dpi，Windows ≈ 96 dpi；现代手机普遍 200+ dpi（iPhone 12 Pro ≈ 460），所以一个固定 `px` 的字号在手机上看起来会非常小。

**相对单位**（随上下文缩放）：

| 单位 | 相对于 |
|------|--------|
| `em` | 当前元素的 font-size（≈ 一个 "m" 的宽度） |
| `ex` | 当前字体的 x-height |
| `ch` | 当前字体里 "0" 字形的宽度 |
| `lh` | 当前元素的 line-height |
| `rem` | 文档根元素 `<html>` 的 font-size |
| `%` | 父元素对应维度的百分比 |
| `vw` / `vh` | viewport 宽 / 高的 1% |
| `vmin` / `vmax` | viewport 较短 / 较长那一边的 1% |

经验法则：全局尺寸（排版、断点）优先用 `rem`，组件内部成比例的局部间距用 `em`，流式布局用 `%` 和 viewport units，只有在你真的就是想锁死像素（1px 的 border、细节修饰）时才用 `px`。

```css
html { font-size: 12pt; }
p    { font-size: 1rem; }
h1   { font-size: 1.8rem; margin-top: 2ex; margin-bottom: 1ex; }
h2   { font-size: 1.4rem; }
```

### 颜色取值

颜色会出现在很多地方：`color`、`background-color`、`border-color`、`outline-color`、渐变、阴影等等。

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

`red` 和 `#FF0000` 是同一个颜色；`#FF0001` 或 `#FF1111` 在肉眼看来仍然是红色。手动调色板时 HSL 通常更直观（"同一个色相，亮一点"）。

### Typography（排版）

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

通用 family fallback（`serif`、`sans-serif`、`monospace`、`cursive`、`system-ui`）一定能解析出某个字体。如果想让设计在不同操作系统之间保持一致，可以加载一个 web font（例如 Google Fonts 上的 Roboto）：

```html
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
```

### 文本相关属性

```css
text-align: left | right | center | justify;
text-decoration: none | underline | line-through | overline;
text-transform: none | uppercase | lowercase | capitalize;
text-indent: 1em;
white-space: normal | nowrap | pre | pre-wrap;
word-break: normal | break-all | keep-all;
overflow-wrap: normal | break-word | anywhere;
```

### 背景

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

垂直韵律的练习就是在 `body` 上用 `background-image: url("baseline.png")`，那张图是一条 1×20 像素的细长条、最后一行带颜色，平铺之后就在每个元素背后画出了一张基线网格。

### Reset / normalise 样式表的作用

每款浏览器都自带一份 user-agent 样式表。`<h1>`、`<ul>`、`<button>`、表单控件等的默认样式在 Chrome、Firefox、Safari 之间都不完全一样——直接在它们之上叠样式很不可靠。

为什么 `reset.css` 有用？因为它把这些"看不见的差异"统一抹平，让每个浏览器从同一条起跑线开始，你写的每一行 CSS 才会得到可预测的结果。两个常见的起点：

- **`reset.css`**（Eric Meyer 的 `meyerweb.com/eric/tools/css/reset/`）— 激进地把一切都归零：几乎对每一个元素都设 `margin: 0; padding: 0; border: 0; font-size: 100%; font: inherit; vertical-align: baseline;`，去掉列表项目符号，给老浏览器里的 HTML5 元素加 `display: block`，去掉默认引号，给表格设 `border-collapse: collapse`。加载之后，*什么都看不出样式*，所有外观都要你自己重新搭。
- **`normalize.css`** — 保留有用的默认值，只把浏览器之间不一致的地方抹平。Lab 里 Milligram 就配它一起用。

reset/normalise 要*先*加载，然后再加载你自己的样式表：

```html
<link rel="stylesheet" href="reset.css">
<link rel="stylesheet" href="mystyle.css">
```

### CSS 框架的概念

所谓框架，其实就是一份样式表（有时再带一个小的 JS 文件），它给你打包了一整套连贯的规则和工具类。课上覆盖了三个：

- **Milligram** — 极简风；默认就给整页应用样式；和 `normalize.css` 配合使用；提供一个 `container` 类来限制内容最大宽度。
- **Bulma** — 基于 class 的；只有你打了类名的部分才会被它接管。Title + level 的组合：`class="title is-1"`。Hero 模式：外层 `.hero`，里面再套 `.hero-body`。布局辅助类：`.section`、`.container`、`.content`。源代码用 SASS 写、再编译成 CSS。两种发行版本：`bulma.css`（可读）和 `bulma.min.css`（压缩、体积更小）。
- **Bootstrap** — 最流行的一个；组件丰富；某些交互组件（tabs、modal）需要带上一个 JS bundle。

基于 class 的框架刻意把结构（HTML 标签）和样式（class 名）分开：`<h1 class="title is-1">` 看上去有些冗余，但好处是改视觉层级时不会动到语义。

只要在手机上跑任何框架，mobile viewport meta tag 都是必需的：

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

## 选择器与特异性速查

| 选择器 | 匹配什么 | Specificity | 例子 |
|--------|---------|-------------|------|
| `*` | 所有元素 | `0,0,0,0` | `* { box-sizing: border-box; }` |
| `p` | 所有 `<p>` | `0,0,0,1` | `p { margin-bottom: 1em; }` |
| `h1, h2, h3` | 分组 | each = `0,0,0,1` | `h1, h2 { font-weight: bold; }` |
| `.note` | 类 | `0,0,1,0` | `.note { color: gray; }` |
| `p.note` | 类型 + 类 | `0,0,1,1` | `p.note { font-style: italic; }` |
| `[type="text"]` | 属性 | `0,0,1,0` | `[type="text"] { border: 1px solid; }` |
| `input[required]` | 类型 + 属性 | `0,0,1,1` | |
| `:hover` | 伪类 | `0,0,1,0` | `a:hover { color: red; }` |
| `:nth-child(2n)` | 伪类 | `0,0,1,0` | `tr:nth-child(odd) { background: #f7f7f7; }` |
| `::before` | 伪元素 | `0,0,0,1` | `q::before { content: '"'; }` |
| `#main` | id | `0,1,0,0` | `#main { max-width: 60em; }` |
| `h1#main` | 类型 + id | `0,1,0,1` | |
| `nav .item.active` | descendant + 2 个类 | `0,0,2,1` | |
| `style="…"` (inline) | inline | `1,0,0,0` | `<p style="color:red">` |
| `… !important` | 任意 + 标志 | 凌驾普通顺序 | `color: red !important;` |

Combinators **不**会增加 specificity，它们只负责缩小匹配范围：

| Combinator | 含义 |
|-----------|------|
| `A B`（空格） | `B` 是 `A` 的 descendant（任意深度） |
| `A > B` | `B` 是 `A` 的直接子元素 |
| `A + B` | `B` 是紧跟在 `A` 后面的下一个兄弟 |
| `A ~ B` | `B` 是 `A` 后面任意位置的兄弟 |

## Lab 实操

### Lab 1 — Styling Text (`lab/text.md`)

**目标：** 在一个朴素的文本页面（`sometext.html`，介绍专业本身）上练习排版、相对单位和 reset 样式表。

**Step 1 — "阅读模式"样式表。** 新建 `sometext.css` 并在 head 里链上：

```css
body {
    margin: 0 auto;     /* center horizontally given a fixed width */
    max-width: 40em;    /* limit line length to ~60–70 characters */
    line-height: 125%;  /* room to breathe between lines */
}
```

为什么调这几个旋钮：

- **`max-width`** 用 `em`（不是 `px`）写，能让行宽和字体绑定在一起：~40 个 "m" 宽 ≈ 60 个普通字符，正好落在被研究反复验证过的可读性甜点区。
- **`margin: 0 auto`** 把固定宽度的块水平居中，让正文和窗口边缘之间留出呼吸空间。
- **`line-height: 125%`** 让行与行之间松一些，但又不像论文那样夸张地双倍行距。

可选的进一步微调：`font-size`、`font-family`（`serif`、`sans-serif` 或者像 `Calibri` 这样的系统字体——心知它不会在每个操作系统上都存在）、`background-color` 调成温暖的纸色或者暗色调。

**Step 2 — Reset 之后从零搭起。** 把那行加载 `reset.css` 的 `<!-- … -->` 注释取消掉。页面立刻变得"赤裸"：标题、列表、段落都成了纯文本。在你自己的样式表里（要在 `reset.css` **之后**加载）重新搭起视觉层级。这一步的关键原则：

- 标题需要的是空白，而不只是更大的字号：标题上下加 `padding`/`margin` 才是让它脱颖而出的关键。而且标题*上方*要比*下方*留得多——标题归属于它所引领的那段正文。
- 用**相对**尺寸，这样用户/浏览器调字号时所有元素仍能等比缩放：写 `h1 { font-size: 150%; }` 或 `h1 { font-size: 1.5rem; }`，绝不要写 `h1 { font-size: 24px; }`。验证方法：在 dev tools 控制台里跑 `document.body.style.fontSize="24px"`——用相对单位的标题会保持原比例，用绝对单位的标题反而会显得"小"。

**Step 3 — Vertical rhythm（垂直韵律）。** 想象一张 20px 的网格，把页面上所有内容都布置成：段落 baseline 落在网格线上，标题加上间距的总高度刚好是网格高度的整数倍。

```css
body {
    background-image: url("baseline.png"); /* 1×20 strip with a pink last row */
}
```

这张图会平铺，给你画出可对齐的水平网格线。约束如下：

- 每个段落 baseline 都落在网格线上（调 `line-height`，比如 16px 字号下用 `1.25` 正好是 20px）。
- 每个标题的*总高度*（font + padding + margin）都是 20px 的整数倍——即便标题文字本身不一定要落在某条线上。
- 所有尺寸（margin、padding、font-size）必须用相对单位（`em` / `rem` / `%`）。
- 调试时给标题加 `background-color: rgba(0, 0, 255, 0.25)` 能直观看到它是不是嵌进网格里；如果之后想保留一个真的有色背景，再加 `padding-left: 0.5em` 让文字不要紧贴边。
- 把 reset 抹掉的列表项目符号补回来：
  ```css
  ul {
      padding-left: 2em;        /* bullets sit in the padding */
      list-style-type: disc;
      list-style-position: outside;
  }
  ```
- 给链接加点样式，比如 `a { text-decoration: underline; }`，可以的话再区分一下 `:visited`。

**预期效果：** 一个干净的阅读页面——标题靠空白凸显出来，段落有舒服的行宽和韵律，调节 body 字号时一切都按比例缩放。

### Lab 2 — Frameworks (`lab/framework.md`)

**目标：** 把第三方样式表接到页面（`page1.html`、`page2.html`）里，并通过类名做定制。

**Milligram (`page1.html`):**

```html
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css">
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.css">
```

顺序很重要：先 web font，再 `normalize.css`，最后 `milligram.css`。如果只加载前两个，外边距会被 normalise 掉，但排版毫无变化（还没有任何规则设过 `font-family`）；加上 Milligram 之后整页就会被重新装饰一遍（紫色的 Register 按钮、纵向排布的表单）。

接下来：

- 给 `<main>` 加上 `class="container"`，把内容的最大宽度收住。
- 在 dev tools 里打开设备模拟，文字在手机上会看起来非常小，原因是像素密度。修法是补上 viewport meta tag（骨架文件里经常缺）：
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  ```
- 检查 Milligram 自己的规则，看它是怎么设置标题字号、铺满宽度的表单字段、纵向 label/input 堆叠和居中容器的。这才是真正的练习——*去读框架的 CSS*。

**Bulma (`page2.html`):**

```html
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.css">
```

Bulma 是 opt-in、基于 class 的：

- 给 `h1` 加上 `class="title"`，再细化成 `class="title is-1"` 表示一级标题尺寸，`is-2` 表示二级。
- 搭一个 **hero** 横幅：外层 `<header class="hero">`，内含一个 `<div class="hero-body">` 包住 `<h1 class="title is-1">`。
- 用 `<main class="content">` 让后代按标签自动应用样式，里面再放一个 `<div class="container">` 做居中固定宽度，再嵌 `<section class="section">` 块来撑出间距：
  ```html
  <main class="content">
      <div class="container">
          <section class="section">
              ... content ...
          </section>
      </div>
  </main>
  ```
- 按 Bulma 的 form 文档给表单上样式：铺满宽度的字段、label 在字段上方、主按钮（`is-primary` 表示蓝色）——视觉效果跟 Milligram 那个表单一样，但实现方式只是打类名而非写 CSS。
- 最后再随便丢一个 Bulma 组件进去玩玩（card、navbar、panel 等等）。

**Bootstrap。** 提到一句：体量最大、最流行（Twitter 出品）；同样有 JS bundle 用来支持 tabs、modals 这类组件；课余时间自行探索。

**预期效果：** 两个页面几乎不写一行 CSS、只靠几个类名和一两个 `<link>` 标签就显得相当专业。同时你也会感受到两种设计哲学（一切由框架包办 vs. 类名按需启用）以及 SASS / CSS / 压缩 CSS 这条发行链。

## 易错点与重点

- **Collapsing margins（外边距合并）。** 相邻两个块级元素的垂直 margin 会*合并*成两者中较大的那个，而不是相加。一个 `<p>` 设了 `margin-bottom: 20px`、紧跟着的 `<h2>` 设了 `margin-top: 30px`，最终的间距是 30px，不是 50px。在跨越 border/padding、inline-block / flex / grid item 之间或浮动元素之间不会发生。坑常出现在你单独调试间距时——切到真实页面上一看，数字对不上。
- **继承的小坑。** 排版相关的属性（`color`、`font-*`、`line-height`、`letter-spacing`）会继承；布局相关的（`margin`、`padding`、`border`、`width`、`background`）则**不**会。在 `body` 上设 `color` 会顺延到所有后代；在 `body` 上设 `border` 只会给 body 自己描边。表单控件出了名地*不*继承字体——想让它们和正文一致，要在 `input, button, select, textarea` 上设 `font: inherit`（这正是 `reset.css` 干的事）。
- **Specificity wars（特异性军备竞赛）。** 每次有规则被更具体的对手压下去，你都会忍不住往上加码：先加个 id，再加 `!important`，再嵌得更深。正确的解法是让选择器*保持扁平、保持一致*（每件事一个 class、采用类似 BEM 的命名、避免用 id 做样式钩子），而不是不断升级。`!important` 是最后的退路，不是日常工具。
- **Class vs. id。** 二者都能给元素挂元数据，但行为差别明显：
  - `class` 是用来**给一组东西上样式**的：很多元素可以共享同一个，一个元素也可以挂很多个。Specificity `0,0,1,0`。CSS 里几乎所有事情都用它。
  - `id` 是用来**唯一标识一个东西**的：必须在页面里唯一；主要用于页内跳转锚点（`#section-3`）、JS 钩子，以及表单的 `for=`/`id=` 配对。Specificity `0,1,0,0` 让它成了一把 specificity 大锤，正是上面那种军备竞赛的源头。讲义专门用 `<p id='uniquebox'>`（能被 `#uniquebox` 命中）和 `<p class='uniquebox'>`（**不会**被命中）做对照来强化这一点。
- **什么时候真的需要 `reset.css`。** 任何需要像素级、跨浏览器一致输出的场景（框架、设计系统、有 baseline grid 的项目）。垂直韵律那个练习*必须*建立在 reset 之上，因为 `h1`、`p`、`ul` 的默认 margin/padding 在每个浏览器里都不一样。一个临时的个人页面用浏览器默认值无所谓；正经的生产 CSS 应该从 reset 或 normalise 起步。
- **单位别用混。** `em` 会复合（一个 `2em` 字号的元素里再放一个 `2em` 的子元素，相对根字号就是 4 倍）；`rem` 不会。`%` 用在 `width` 上是父宽度的百分比，用在 `line-height` 上却是元素自己 font-size 的百分比。`vh`/`vw` 不算滚动条的宽度，所以在手机上用 `100vw` 做满屏区块时容易蹦出横向滚动条。讲义的结论：*"Very easy to get muddled about units."*
- **Hex 颜色的小陷阱。** `#FF0000` 和 `#FF0001` 看起来完全一样，肉眼根本抓不到这种笔误。手敲颜色时尽量用命名关键字或 HSL。
- **手机像素密度。** 在手机上 "16px" 比在笔记本上小得多。任何面向移动端的 HTML5 页面都先把 `<meta name="viewport" content="width=device-width, initial-scale=1">` 加上，再来怪框架。
- **加载顺序。** `reset.css` / `normalize.css` 最先，框架第二，你自己的样式表最后——否则框架会因为 source-order tie-breaking 而盖掉你的定制。
- **不要双倍行距。** `line-height: 200%` 是打字机时代的遗物，今天看上去就像在喊"我刚抄了一份论文模板"。正文的现代区间是 `1.4`–`1.6`。
