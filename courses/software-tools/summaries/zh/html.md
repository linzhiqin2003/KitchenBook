# 第 12 章 — HTML

## 章节概览

HTML（HyperText Markup Language，超文本标记语言）是写现代网页文档用的标记语言。本章默认讨论的是 **HTML5** 这个版本——它在 2014 年正式发布，把过去 HTML/XML 各种历史包袱清理了一波，同时把以前必须靠 JavaScript 或者 Adobe Flash 插件才能实现的功能（比如 `<video>`、原生日期选择器）做成了内置标准标签。

本章从三个角度来讲 HTML：

1. **hypertext 这个概念本身** —— 一种读者可以顺着 hyperlink 跳转的交互式文本。Tim Berners-Lee 当年在 CERN 搞这套东西，就是为了让科研论文里的引用能一键直达；HTML 和 HTTP 里那个 "HT" 都是从这儿来的。
2. **markup 即结构** —— 标签的作用是给文本加注释，描述文档的结构和含义。浏览器（或者屏幕阅读器、搜索引擎之类）解释这些 markup，再渲染成最终呈现。这里有个关键点：**结构应当和 presentation 分离**——视觉上的样式是下一章 CSS 的事。
3. **生成 HTML** —— 手写页面是为了帮你建立心智模型，但实际项目里页面都是生成出来的，要么是静态生成（比如 Markdown 经 GitHub Pages 编译），要么是动态生成（比如服务端模板引擎 **Thymeleaf** 把数据库的数据塞进模板渲染成 HTML）。

实验环节分两部分：先从零手写一个小的合法 HTML5 页面，扔到 W3C validator 里验证；然后扩展一个用 Thymeleaf 模板渲染数据库内容的 Spring Boot 应用。

后续 Web 开发部分会一直拿 MDN HTML 参考文档（`developer.mozilla.org/en-US/docs/Web/HTML`）作为主要查阅手册。

## 核心知识

### HTML 文档骨架

最小的合法 HTML5 文档长这样：

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

要点：

- 所有东西都嵌套在唯一的根元素 `<html>` 里。
- `<head>` 和 `<body>` 是 `<html>` 里的兄弟节点。
- `<head>` 装的是描述 `<body>` 的 *metadata* —— 标题、字符编码、外链样式表等等。它**不会**显示在页面区域里。
- `<body>` 装的是文档*可见*的部分。
- 标签可以嵌套，嵌套关系决定了文档的结构。
- 标签可以带 **attribute** 来调整其语义（比如 `<a>` 上的 `href`、`<html>` 上的 `lang`）。

### DOCTYPE

`<!DOCTYPE html>` 是 HTML5 的 doctype 声明。它必须出现在文档第一行，告诉浏览器用 standards mode 来渲染。早些年 HTML/XHTML 各种版本的 doctype 写起来又长又分版本号，HTML5 故意改成了这种简洁形式。

### `<head>` 与 meta 标签

`<head>` 里常见的内容：

- `<title>` —— 浏览器标签页/窗口标题里显示的文字；搜索引擎也会用，收藏书签时也是默认的标题。
- `<meta charset="utf-8" />` —— 声明字符编码。UTF-8 是现代默认值，让你可以直接在源码里写非 ASCII 字符。
- `<meta name="...">` —— 各种 name/value 形式的元数据，比如 `description`、`author`、`viewport`。
- `<link rel="stylesheet" href="...">` —— 外链一个 CSS stylesheet（下一章会讲）。
- `<script src="..."></script>` —— 外链 JavaScript（之后会讲）。

虽然名字撞车，`<head>` 跟 HTTP header 完全是两码事 —— `<head>` 是响应 body 里被发回来的文档的一部分。

### Semantic 结构元素

HTML5 引入了一批 semantic 结构标签，目的是让大家别再万物皆 `<div>` 了。这些标签的意义是给屏幕阅读器、搜索引擎和大纲工具看的 —— 视觉上没加样式之前就跟普通块元素差不多。

- `<header>` —— 一个页面或 section 的头部（banner、介绍、logo、主导航）。
- `<nav>` —— 一组导航链接。
- `<main>` —— 文档主内容区。整个页面最多一个，且不能嵌在 `<article>`、`<aside>`、`<header>`、`<footer>` 或 `<nav>` 里。
- `<section>` —— 带标题的主题分组。
- `<article>` —— 自包含、可独立分发的内容（一篇博客、一条评论、一个论坛帖子）。
- `<aside>` —— 跟周围内容只是间接相关的内容（侧边栏、引文）。
- `<footer>` —— 一个页面或 section 的页脚（版权、联系方式、相关链接）。
- `<figure>` / `<figcaption>` —— 一个自包含的图表（图片、示意图、代码段）外加可选的说明文字。

跟以前 `<div class="header">` 之类的写法比，semantic 标签把含义本身就写在了标签里，这正是 assistive technology 所依赖的东西。

### 文本级元素

block-level 的文本容器：

- `<h1>` … `<h6>` —— 六级标题。`<h1>` 是最高级别；不要为了视觉效果跳级。
- `<p>` —— 段落。
- `<blockquote>` —— 块级引用。
- `<pre>` —— 预格式化文本（保留空白，默认等宽字体）。

幻灯片里把带语义的 inline 元素和老的纯样式元素做了对比：

| 新（semantic） | 含义 | 老（presentational） |
|----------------|---------|----------------------|
| `<em>` | 强调 | `<i>`（斜体） |
| `<strong>` | 重要 | `<b>`（粗体） |
| `<q>` | 行内引用 | `<u>`（下划线） |
| `<cite>` | 引用 / 作品标题 | `<s>`（删除线） |
| `<var>` | 变量名 | `<tt>`（电传打字机/等宽） |
| `<code>` | 源代码 | `<small>`（小字） |

用 semantic 形式；视觉粗细应该交给 CSS，而不是写在 markup 里。

其他几个值得记住的 inline 标签：

- `<a>` —— anchor / hyperlink。
- `<span>` —— 没有任何语义的通用 inline 容器（给样式或脚本用的钩子）。
- `<br />` —— 换行（一个 void element）。

### 列表

三种：

- `<ul>` —— 无序列表，里面装 `<li>`，默认渲染成圆点。
- `<ol>` —— 有序列表，里面装 `<li>`，默认渲染成数字。
- `<dl>` —— description list，里面装 `<dt>`（term）和 `<dd>`（description）成对出现。

```html
<ul>
  <li>HTML5</li>
  <li>CSS</li>
  <li>JavaScript</li>
</ul>
```

### 链接和链接类型

`<a href="...">` 是 anchor 标签。`href` 属性正是让页面成为 "hypertext" 的关键。幻灯片专门讲了 URL 解析规则，这套规则跟 HTTP 用的是一致的：

假设当前页面在 `bristol.ac.uk/students/info.html`：

| `href` 值 | 解析为 |
|--------------|-------------|
| `/courses` | `bristol.ac.uk/courses`（root-relative） |
| `courses` | `bristol.ac.uk/students/courses`（相对当前路径） |
| `../courses` | `bristol.ac.uk/courses`（相对上一级） |
| `https://example.com/x` | 绝对地址 |

`<a>` 上其他常用属性：

- `target` —— 链接打开方式，比如 `_blank` 表示新标签页。
- `rel` —— 关系，比如 `rel="noopener noreferrer"`（搭配 `target="_blank"` 推荐使用），`rel="nofollow"` 给 SEO 用。
- `download` —— 让浏览器把资源当下载来处理，而不是导航过去。

### 图片、`<picture>` 和 `srcset`

- `<img src="..." alt="...">` 是 void element。`alt` 属性出于 accessibility 是**必填**的 —— 屏幕阅读器读的就是它，图片加载失败时显示的也是它。
- `width` / `height` 属性给的是固有尺寸；提前写上能避免图片加载完之后页面发生 reflow。
- `srcset` 配合 `sizes` 提示，让你能给 `<img>` 提供多个分辨率的版本，浏览器会根据设备像素比和视口大小挑合适的：

  ```html
  <img src="cat-800.jpg"
       srcset="cat-400.jpg 400w, cat-800.jpg 800w, cat-1600.jpg 1600w"
       sizes="(max-width: 600px) 400px, 800px"
       alt="A black cat sitting on a windowsill" />
  ```

- `<picture>` 让你可以根据 media query 或者格式去切换图片源 —— 用来做艺术指导式的裁剪，或者新格式带 JPEG 兜底特别合适：

  ```html
  <picture>
    <source srcset="banner.avif" type="image/avif" />
    <source srcset="banner.webp" type="image/webp" />
    <img src="banner.jpg" alt="Sunset over the Avon Gorge" />
  </picture>
  ```

### 表格

表格是用来放*表格数据*的，**不是**用来做页面布局的（布局用 CSS Grid / Flexbox）。结构：

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

- `<table>` —— 表格本身。
- `<thead>` / `<tbody>` / `<tfoot>` —— 行分组；样式和打印时重复表头都用得上。
- `<tr>` —— 表格行。
- `<th>` —— 表头单元格（默认加粗居中；对辅助技术来说有语义意义，特别是配合 `scope="col"` 或 `scope="row"`）。
- `<td>` —— 数据单元格。
- `<caption>` —— 表格标题（要放在 `<table>` 的第一个子节点位置）。
- `colspan` / `rowspan` 属性用来合并单元格。

幻灯片还提到了 `datatables.net` 这个 JavaScript 库，它能把一个普通的 `<table>` 包装成可排序、可筛选的交互式表格 —— 是 progressive enhancement 的好例子。

### 表单

表单负责收集用户输入并提交给服务器。骨架：

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

关键元素：

- `<form action="..." method="get|post">` —— 包住所有控件。`action` 是数据提交到的 URL，`method` 是 HTTP 方法。
- `<label for="id">…</label>` —— 把一段说明文字跟某个控件关联起来。点击 label 会聚焦控件；这是 accessibility 必备。
- `<input>` —— 单行输入框（void element）。`type` 属性决定行为（下面会列）。`name` 是提交时该值用的 key；`id` 是 `<label for>` 指向的钩子。
- `<textarea>` —— 多行文本。跟 `<input>` 不同，它有闭合标签，初始值就是它的内部文本。
- `<select>` 里装 `<option value="...">` —— 下拉框：

  ```html
  <select name="animal">
    <option value="dog">Dog</option>
    <option value="cat">Cat</option>
  </select>
  ```

- `<button type="submit|reset|button">` —— 按钮。在 form 里 `type="submit"` 是默认值。
- `<fieldset>` + `<legend>` —— 把一组相关控件用一个带说明的框圈起来。

幻灯片里列出的 HTML5 `<input type="...">` 取值：

```
button, checkbox, color, date, datetime-local, email,
file, hidden, image, month, number, password, radio,
range, reset, search, submit, tel, text, time, url, week
```

再加上 `<textarea>` 用于多行。挑对类型可以让移动用户得到对的键盘，让浏览器免费帮你做 validation，也让 accessibility 工具拿到正确提示。

input 上的 validation 提示：

- `required` —— 必填。
- `min`、`max`、`step` —— 数值/日期约束。
- `pattern="regex"` —— 正则校验。
- `maxlength`、`minlength` —— 字符串长度。
- `autocomplete="name|email|address-line1|country|tel|cc-name|cc-number|…"` —— 告诉浏览器/密码管理器拿什么去自动填充。

```html
<input required type="number" />
<input type="text" autocomplete="name" />
```

### HTML5 新增内容

具体来说，本章把下面这些列为 HTML5 相对于以前版本的改进：

- 简短的 `<!DOCTYPE html>` 声明。
- `<meta charset="utf-8" />` 简写形式。
- semantic 结构标签：`<header>`、`<nav>`、`<main>`、`<section>`、`<article>`、`<aside>`、`<footer>`、`<figure>`、`<figcaption>`。
- 新的 `<input>` 类型：`email`、`url`、`tel`、`number`、`range`、`color`、`date`、`time`、`datetime-local`、`month`、`week`、`search`。
- 通过 `required`、`pattern`、`min`、`max`，以及 `email`/`url`/`number` 的类型检查来做原生表单 validation。
- 原生 `<video>` 和 `<audio>` 标签（替代 Flash）。
- 新元素和 API（`<canvas>`、drag-and-drop、geolocation、web storage），不用插件就能"白嫖"。
- 自闭合规则放宽：void element 像 `<br>`、`<img>`、`<input>`、`<meta>` 不再强制要求带末尾的 `/`，不过 `<br />` 也仍然合法。

### 字符编码与实体

- 在 `<head>` 里用 `<meta charset="utf-8" />` 声明编码，并把文件保存为 UTF-8。
- 有些字符必须写成 **entity**，要么是因为它们在 HTML 里有语法意义，要么是因为这样写更省事：
  - `&lt;` 表示 `<`
  - `&gt;` 表示 `>`
  - `&amp;` 表示 `&`
  - `&quot;` 表示 `"`
  - `&apos;` 表示 `'`
  - `&nbsp;` 表示不换行空格
  - 数字实体如 `&#8364;` 或 `&#x20AC;` 表示 `€`，在没法直接打出该字符时使用。
- 声明了 UTF-8 之后，一般直接粘贴字符就行（`€`、`é`、`中`），不必非用实体。

### W3C validation

实验里介绍了 `validator.w3.org` 上的 **W3C Markup Validator**，作为检查页面是否合法 HTML5 的权威方式。可以提交 URL、上传文件，或直接粘贴源码。validator 会报告错误（比如未闭合的标签、缺少必填属性、元素位置错误）以及警告。

浏览器 DevTools 里也能看到 validation 问题：

- Chrome/Edge：**Console** 标签上会有一个 *Issues* 计数器；点开会进入 *Issues* 标签看详细描述。

validation 不是吹毛求疵 —— 不合法的 HTML 解析方式由实现自定义，跨浏览器和辅助技术行为会不一致。

### Accessibility 基础

Accessibility（a11y）是融在 markup 里的，不是事后补的：

- `<html>` 上加 `lang` 属性，屏幕阅读器才能选对发音：`<html lang="en">`。
- `<img>` 永远要写 `alt`。纯装饰性图片用 `alt=""`（空字符串），让屏幕阅读器跳过去。
- 标题级别 (`<h1>` … `<h6>`) 按顺序用 —— 它们组成的文档大纲是辅助技术导航的依据。
- 用 semantic 标签 (`<nav>`、`<main>`、`<button>`、`<a>`)，别用 `<div>` 加 click handler —— 内置的键盘处理和 ARIA role 都是免费送的。
- 表单控件永远配 `<label for="...">`。
- 当 semantic HTML 不够用时，可以用 ARIA role/属性 (`role="navigation"`、`aria-label`、`aria-hidden`) 来补充 —— 但**优先选对的 HTML 元素**，因为大部分 semantic 元素本身就自带正确的 ARIA role。
- 选读 GOV.UK 网站上关于 *progressive enhancement* 的资料强化了这一点：先做出能用的 HTML 基线，再分层加 CSS 和 JavaScript，这样设备/网络受限的用户也能用。

## 元素速查

把章节材料里出现的标签/属性按用途分组列在这里。

### 文档结构

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<!DOCTYPE html>` | HTML5 doctype，必须在第一行。 | `<!DOCTYPE html>` |
| `<html lang="...">` | 根元素；`lang` 帮助屏幕阅读器和搜索。 | `<html lang="en">` |
| `<head>` | metadata 容器。 | `<head>…</head>` |
| `<body>` | 可见内容容器。 | `<body>…</body>` |
| `<title>` | 标签页/窗口标题。 | `<title>A web page</title>` |
| `<meta>` | metadata 键值对（void）。 | `<meta charset="utf-8" />` |
| `<link>` | 外部资源，比如 stylesheet（void）。 | `<link rel="stylesheet" href="style.css" />` |
| `<script>` | 内联或外部 JavaScript。 | `<script src="app.js"></script>` |

### Semantic 结构（HTML5）

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<header>` | 页面/section 的头部。 | `<header><h1>Site</h1></header>` |
| `<nav>` | 导航块。 | `<nav><a href="/">Home</a></nav>` |
| `<main>` | 主内容（每页一个）。 | `<main>…</main>` |
| `<section>` | 带标题的主题分组。 | `<section><h2>Intro</h2>…</section>` |
| `<article>` | 自包含内容。 | `<article>…blog post…</article>` |
| `<aside>` | 间接相关内容。 | `<aside>related links</aside>` |
| `<footer>` | 页面/section 的页脚。 | `<footer>© 2025</footer>` |
| `<figure>` / `<figcaption>` | 带说明的图。 | `<figure><img …/><figcaption>Fig 1</figcaption></figure>` |

### 通用容器

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<div>` | 通用块容器，无语义。 | `<div class="card">…</div>` |
| `<span>` | 通用 inline 容器，无语义。 | `<span class="hl">word</span>` |

### 标题与文本级

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<h1>` … `<h6>` | 1–6 级标题。 | `<h1>Title</h1>` |
| `<p>` | 段落。 | `<p>Text.</p>` |
| `<br />` | 换行（void）。 | `line one<br />line two` |
| `<em>` | 强调。 | `it is <em>very</em> hot` |
| `<strong>` | 重要性。 | `<strong>Warning</strong>` |
| `<q>` | 行内引用。 | `<q>To be or not to be</q>` |
| `<cite>` | 作品标题。 | `<cite>Hamlet</cite>` |
| `<var>` | 变量名。 | `<var>x</var>` |
| `<code>` | 源代码（行内）。 | `<code>print(x)</code>` |
| `<pre>` | 预格式化块。 | `<pre>text  with   spaces</pre>` |
| `<small>` | 旁注 / 小字提示。 | `<small>terms apply</small>` |
| `<blockquote>` | 块级引用。 | `<blockquote>…</blockquote>` |

### 列表

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<ul>` | 无序列表。 | `<ul><li>A</li></ul>` |
| `<ol>` | 有序列表。 | `<ol><li>Step 1</li></ol>` |
| `<li>` | 列表项（在 `<ul>` 或 `<ol>` 里）。 | `<li>Item</li>` |
| `<dl>` | description list。 | `<dl><dt>Term</dt><dd>Definition</dd></dl>` |
| `<dt>` | description list 中的 term。 | `<dt>HTML</dt>` |
| `<dd>` | description list 中的描述。 | `<dd>Markup language</dd>` |

### 链接和媒体

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<a>` | anchor / hyperlink。 | `<a href="/courses">Our Courses</a>` |
| `<img>` | 图片（void）。 | `<img src="cat.jpg" alt="A cat" />` |
| `<picture>` | 响应式/艺术指导式图片包装器。 | `<picture><source …/><img …/></picture>` |
| `<source>` | `<picture>`/`<video>`/`<audio>` 的备选源（void）。 | `<source srcset="x.webp" type="image/webp" />` |
| `<video>` | 原生视频播放器。 | `<video src="m.mp4" controls></video>` |
| `<audio>` | 原生音频播放器。 | `<audio src="s.mp3" controls></audio>` |

### 表格

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<table>` | 表格根元素。 | `<table>…</table>` |
| `<caption>` | 表格标题。 | `<caption>Marks</caption>` |
| `<thead>` | 表头行分组。 | `<thead><tr><th>…</th></tr></thead>` |
| `<tbody>` | 表体行分组。 | `<tbody>…</tbody>` |
| `<tfoot>` | 表脚行分组。 | `<tfoot>…</tfoot>` |
| `<tr>` | 表格行。 | `<tr>…</tr>` |
| `<th>` | 表头单元格。 | `<th scope="col">Name</th>` |
| `<td>` | 数据单元格。 | `<td>Sarah</td>` |

### 表单

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `<form>` | 表单容器。 | `<form method="post" action="/comment">…</form>` |
| `<label>` | 控件说明。 | `<label for="name">Name:</label>` |
| `<input>` | 单行输入（void）。 | `<input id="name" name="name" type="text" />` |
| `<textarea>` | 多行输入。 | `<textarea name="comment"></textarea>` |
| `<select>` | 下拉框。 | `<select name="animal">…</select>` |
| `<option>` | `<select>` 中的选项。 | `<option value="dog">Dog</option>` |
| `<button>` | 按钮。 | `<button type="submit">OK</button>` |
| `<fieldset>` | 把相关控件分组。 | `<fieldset><legend>Address</legend>…</fieldset>` |
| `<legend>` | `<fieldset>` 的说明。 | `<legend>Address</legend>` |

### 常用属性

| 属性 | 用在 | 用途 |
|-----------|-------|---------|
| `id` | 任意元素 | 唯一标识，给 CSS / JS / `<label for>` 用的钩子。 |
| `class` | 任意元素 | 空格分隔的类名，CSS 主要钩子。 |
| `lang` | 任意元素（最常见在 `<html>` 上） | 内容的语言。 |
| `href` | `<a>`、`<link>` | 目标 URL。 |
| `target` | `<a>` | 链接打开位置（`_blank`、`_self`…）。 |
| `rel` | `<a>`、`<link>` | 关系（比如 `stylesheet`、`noopener`）。 |
| `src` | `<img>`、`<script>`、`<video>`、`<audio>`、`<source>` | 资源 URL。 |
| `alt` | `<img>` | 文本替代。 |
| `srcset`、`sizes` | `<img>`、`<source>` | 响应式图片源。 |
| `type` | `<input>`、`<button>`、`<script>`、`<source>` | 指定种类。 |
| `name` | 表单控件 | 提交时该值的 key。 |
| `value` | `<input>`、`<option>`、`<button>` | 提交/显示的值。 |
| `placeholder` | `<input>`、`<textarea>` | 提示文字。 |
| `required`、`min`、`max`、`step`、`pattern`、`maxlength` | `<input>` | 内置 validation。 |
| `autocomplete` | `<input>` | 浏览器自动填充提示。 |
| `for` | `<label>` | 关联 `id` 匹配的 input。 |
| `action`、`method` | `<form>` | 提交 URL 和 HTTP 方法。 |
| `colspan`、`rowspan` | `<th>`、`<td>` | 单元格跨越。 |
| `scope` | `<th>` | `col` 或 `row`，给 accessibility 用。 |
| `charset` | `<meta>` | 文档编码。 |

## Lab 实操

### Lab 1 — 基础 HTML5（`lab/basic.md`）

**目标。** 手写一个小的合法 HTML5 页面并做 validation。练习文档骨架、标题、段落、强调、链接和无序列表。

**步骤。**

1. 新建文件 `index.html`。文件名很重要：大多数 web server 在收到 `example.com/pages` 或 `example.com/pages/` 这种 URL 时，按惯例会返回该目录里的 `index.html`。
2. 从 HTML5 模板开始（`<!DOCTYPE html>` + `<html lang="en">` + `<head>`/`<body>`）。
3. 还原 lab 里给的截图。除了那个无序列表外，body 文本必须都放在 `<p>` 里。标题用 `<h1>`/`<h2>`，行内强调用 `<strong>` 和 `<em>`，链接用 `<a href="…">`，learning outcomes 列表用 `<ul>`/`<li>`。
4. 在浏览器里打开文件，确认渲染没问题。
5. 在 `validator.w3.org` 上验证页面（粘贴、上传或者填 URL 都行）。也看看浏览器 DevTools 的 *Issues* 标签。
6. 跟提供的样例答案 `lab/examplepage.html` 对比 —— 你的版本可以不同但同样合法。

**参考答案。**

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

**交付物。** 一个跟截图对得上、且通过 validation 的 `index.html`。

### Lab 2 — Thymeleaf 模板（`lab/templates.md`）

**目标。** 从手写静态 HTML 进阶到*服务端渲染* HTML，用 Spring Boot 应用里的 Thymeleaf 模板引擎。理解后端数据是怎么被插值进模板，按需生成 HTML 的。从模板加数据生成具体页面这一过程的术语叫 **rendering**。

**准备。** 实验应用是这门课 git 仓库里的 `server02`。用 `mvn spring-boot:run` 构建并运行，然后访问 `localhost:8000`。

**应用结构。**

- `model/` 里有 `Database` 接口加上 `Student`、`Unit` 类 —— 一个简易的内存版大学数据库。
- `Templates.java` 配置 Thymeleaf 引擎；`@Component` 注解让 Spring 来管理它。其他类用 `@Autowired` 注入它。
- `Controller.java` 定义 HTTP 路由。
- `src/main/resources/web/` 放静态 HTML。
- `src/main/resources/` 放 Thymeleaf 模板，比如 `units.html` 和 `unit.html`。

**`/units` 的请求流程。**

1. `unitsPage` 控制器方法从数据库加载 unit 列表。
2. 它创建一个 Thymeleaf `Context`，加入一个 key 为 `units` 的值（即列表）。
3. 它用这个 context 渲染 `units.html` 模板，返回结果字符串。Spring 看到返回值是 `String`，就把它当作响应的 HTML body。

**示例模板里的 Thymeleaf 语法。**

```html
<ul th:each="unit : ${units}">
    <li>
        <a th:href="'/unit/' + ${unit.code}" th:text="${unit.code}"></a>
        <span th:text="${unit.title}"></span>
    </li>
</ul>
```

- 凡是带 `th:` 前缀的属性都会被 Thymeleaf 处理掉，输出里看不到。
- `th:each="unit : ${units}"` 相当于 `for (Unit unit : units)` 循环。循环变量不需要写类型。带 `th:each` 的标签连同它的子元素会按迭代次数渲染一遍，所以这里每个 unit 输出一个 `<li>`。
- `th:href` 和 `th:text` 分别生成标签的 `href` 属性和内部文本。`${...}` 从 context 里取值。字符串用单引号；`+` 用来拼接。
- `${unit.code}` 用的是*属性访问* —— Thymeleaf 调的是 `getCode()`，而不是直接取字段。
- Thymeleaf 只在*属性内部*解析 `${...}`。要在文本里塞个值，就用 `<span>` 包一下，再用 `th:text`（这跟某些允许在 body 任意位置写 `${var}` 的模板引擎不一样）。

**带 path variable 的路由。** 点击某个 unit 进入 `/unit/COMS10012`，由 `unitDetailPage` 处理。映射 `/unit/{code}` 声明了一个 path variable；方法参数加 `@PathVariable` 注解，Spring 就会从 URL 里取值填进去。方法去查这个 unit，找不到就返回 404 页面，找到就渲染 `unit.html`。

**练习。**

- *基础。* 把 units 列表页改成用 `<table>` 替代 `<ul>`。每个 unit 一行三列（code、title、link），加一个表头行（`code`、`title`、`link`）。第三列是链接，文字写 "details"，指向 `/unit/{code}`。纯 HTML/Thymeleaf 改动 —— Java 不动。
- *进阶 (1)。* 加上控制器方法和模板，实现列出所有 student 和查看单个 student。模仿 unit 那两个端点（`/students`、`/student/{id}` —— 注意 id 是 `int`）。先只显示 id 和 name 就行。从 unit 那边复制粘贴没问题，但要理解每一处改动。`Student` 类在 `src/main/java/softwaretools/server02/model` 下。
- *进阶 (2)。* `Student.getGrades()` 返回一个 (unit, grade) 对的列表（unit 是 `Unit` 对象，grade 是 `int`）。在 student 详情页里，渲染一个表格，每一对显示 unit code、unit title 和 grade。

**交付物。** 一个改过的 `server02` 应用，`/units` 显示成表格，`/students` 和 `/student/{id}` 已实现，student 页面会列出 grade。

## 易错点与重点

### HTML5 自闭合规则

- HTML5 **不**强制 void element 末尾加斜杠。`<br>`、`<img src="x.jpg" alt="x">`、`<meta charset="utf-8">`、`<input type="text" name="q">` 都合法。
- `<br />` 这种写法也接受（XHTML 兼容），幻灯片里用的就是这种；选一种风格，保持一致。
- 反之，非 void element**必须**有闭合标签。`<p>foo<p>bar` 不会嵌套段落 —— 浏览器会自动把第一个 `<p>` 闭掉，因为 `<p>` 不能嵌 `<p>`。

### Void element

void element 没有内容，也没有闭合标签。本章会碰到的这一组：

```
<area>, <base>, <br>, <col>, <embed>, <hr>, <img>, <input>,
<link>, <meta>, <param>, <source>, <track>, <wbr>
```

写 `<br></br>` 不合法。写 `<img …></img>` 不合法。只能写 `<br>`/`<br />` 和 `<img … />`。

### 嵌套规则

HTML 解析器对哪些元素能装哪些有特定规则。常见的坑：

- `<p>` 不能装 `<div>`、`<ul>`、`<table>` 这种块级元素 —— 解析器会悄悄提前关掉你的 `<p>`，最终 DOM 跟你想的不一样。
- `<a>` 在 HTML5 里可以装块级元素（比如可以包整个卡片），但 `<a>` **不能**嵌另一个 `<a>`（不能套链接），也不能装 `<button>` 或交互控件。
- `<li>` 必须是 `<ul>`、`<ol>` 或 `<menu>` 的子元素。`<dt>`/`<dd>` 只能在 `<dl>` 里。
- `<tr>` 只能在 `<table>`/`<thead>`/`<tbody>`/`<tfoot>` 里。`<th>`/`<td>` 只能在 `<tr>` 里。
- `<option>` 只能在 `<select>`、`<optgroup>` 或 `<datalist>` 里。
- 一个文档应该有且仅有一个 `<title>`、一个（可见的）`<main>`，建议只有一个 `<h1>`，等等。
- `<head>` 和 `<body>` 是 `<html>` 里的兄弟节点 —— `<body>` 不能装在 `<head>` 里，反之亦然。

### Block 与 inline 的混淆

幻灯片说明 `<p>` 是*块级*元素，`<em>` 是*inline*。可以把 inline 元素塞进块级元素里 (`<p>… <em>example</em> …</p>`)，但不能把块级元素塞进 inline 元素。CSS 可以改视觉布局，但 HTML 解析器在 parse 时仍然按结构规则来。

### 常见 validation 错误

把页面扔到 `validator.w3.org` 跑一下，最常见到的是：

- `<img>` 缺 `alt`。
- `<head>` 缺 `<title>`。
- 缺 `<!DOCTYPE html>` 或者 doctype 写错（用了老的 HTML4/XHTML）。
- `<html>` 缺 `lang`。
- `<p>` 里冒出块级元素。
- 同一页有重复的 `id`（必须唯一）。
- `<label>` 上的 `for` 没有对应的 `id`。
- 闭错了标签（`<ul>…</ol>`）。
- 在某元素上用了不允许的属性（比如 `<div>` 上的 `href`）。
- 字符编码不对 —— 文件存成了 Windows-1252 但声明的是 UTF-8（或反过来）。一律存成 UTF-8。

### 本章重点

- **结构第一，呈现第二。** 标签按含义选；视觉样式留给下一章 CSS。盲人用户的屏幕阅读器靠的是你正确使用 `<h1>`/`<nav>`/`<button>`，而不是 `<div class="button">`。
- **用新的 semantic 标签** (`<em>`、`<strong>`、`<cite>`、`<code>`)，别用老的 presentational 标签 (`<i>`、`<b>`、`<u>`、`<tt>`)。
- **`<head>` 不等于 HTTP header** —— 幻灯片专门点出了这一点。别混。
- **手写是为了学习。** 真实系统里页面都是*生成*出来的 —— 静态的（Markdown 转 HTML，比如这门课的网站本身）或动态的（Thymeleaf、Jinja 之类）。Lab 2 把静态 vs 动态的区别讲得很具体。
- **要 validation。** 浏览器宽容得过分，几乎啥都能渲染出来，反而把 bug 藏住了。常跑 W3C validator，常看 DevTools 的 *Issues* 标签。
- **Progressive enhancement**（链接里那篇选读资料） —— 先做出可用的 HTML 基线，再分层叠 CSS 和 JS，让网络差或用辅助设备的用户也能用上。
