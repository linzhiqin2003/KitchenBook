# 第 14 章 — CSS（布局与响应式）

## 章节概览

*Software Tools* 第 4 周从 CSS 的语法层往上抬一层，进入**页面设计**：怎么把元素摆得可控，怎么让一套布局在手机、平板、桌面上都活得下去，以及哪些被反复验证过的设计原则可以拿来用，让最终的页面真的看着舒服。

整章围绕三段短视频（Design、CSS grids、Responsive Layout）加两个 lab（`curriculum`、`trees`）展开。课件里把 web design 明确定位成一门**手艺**——既是工程，也是判断和品位。它有原则可循，但没有标准算法。课件反复强调三条捷径：

- 借鉴现成的网站；
- 用别人写好的设计框架（比如上周提到的 Bootstrap）；
- 采用**grid-based layout** + **responsive layout**，这也是这周的重点。

技术核心可以归成三块：

- **CSS Grid** 模块（父级声明 `display: grid`，子元素按行/列摆位）；
- **media queries**（`@media`），让某些规则只在特定 viewport 宽度下生效；
- 一堆配套概念：流式宽度（`max-width` + `margin: 0 auto`）、`fr` 单位、`gap`、viewport meta 标签，以及 mobile-first 思路。

课件里还顺手讲了一段历史 —— Tables → Float → Flexbox → Grid。这条进化线值得记住：早期人们用 `<table>` 做版面，后来转向 float 来让元素并排，但 float 是为了文字绕排图片设计的，被强行拿来做整页布局后非常脆弱（要不停清浮动、做垂直居中要靠 hack）。Flexbox 把"一维排布"这件事专门做成了一个模型，Grid 又把"二维页面"这件事独立出来。今天的标准答案是：**Grid 管页面级二维布局，Flexbox 管组件级一维布局**，绝大多数实际站点两者都用。

## 核心知识

### `display` 取值（决定布局模型的开关）

| 取值           | 行为                                                                                       |
|----------------|--------------------------------------------------------------------------------------------|
| `block`        | 占满整行，遵守 `width`/`height`，纵向堆叠。`<div>`、`<p>`、`<h1>` 默认就是这个。           |
| `inline`       | 嵌在文字行内，忽略 `width`/`height` 和上下 padding/margin。`<span>`、`<a>`、`<b>` 默认。   |
| `inline-block` | 像文字一样行内流动，但会接受盒模型尺寸。                                                    |
| `none`         | 完全从布局里移除（不是隐藏 —— 不占空间）。和 `visibility: hidden` 区分。                    |
| `flex`         | 元素变成 **flex container**，直接子元素变成 flex items（一维布局）。                       |
| `grid`         | 元素变成 **grid container**，子元素摆在二维网格上。                                        |

`curriculum` lab 里把默认是 inline 的 `<b>` 重新声明成 `display: block`，让标题条横跨整个 grid cell —— 也提醒你，`display` 是 CSS 属性，不是 HTML 标签的固有属性。

### 定位（`position`）

| 取值       | 参照物                                                | 是否脱离正常流？        |
|------------|-------------------------------------------------------|-------------------------|
| `static`   | 默认，正常流                                          | 否                      |
| `relative` | 自己在正常流里的位置；`top/left` 视觉上偏移            | 否（原位置仍占空间）     |
| `absolute` | 最近的非 `static` 祖先                                | 是                      |
| `fixed`    | viewport（滚动也不动）                                | 是                      |
| `sticky`   | 滚到阈值前像 `relative`，越过后像 `fixed`              | 卡住前不脱离             |

课件强调：做整页布局几乎用不上 `position: absolute`，Grid + Flex 就够了。

### Flexbox 模型（一维布局）

flex container 沿着**主轴（main axis）**排列它的**直接子元素**，垂直方向叫**交叉轴（cross axis）**。

容器属性：

| 属性             | 用途                                                                                           |
|------------------|------------------------------------------------------------------------------------------------|
| `display: flex`  | 把元素变成 flex container                                                                      |
| `flex-direction` | `row`（默认）/ `row-reverse` / `column` / `column-reverse` —— 决定主轴方向                      |
| `flex-wrap`      | `nowrap`（默认）/ `wrap` / `wrap-reverse`                                                      |
| `justify-content`| **主轴**上的分布：`flex-start`、`flex-end`、`center`、`space-between`、`space-around`、`space-evenly` |
| `align-items`    | 子元素在**交叉轴**上的对齐：`stretch`（默认）、`flex-start`、`flex-end`、`center`、`baseline`   |
| `align-content`  | 多行换行后整体在交叉轴的分布（仅在 `flex-wrap: wrap` 时有意义）                                 |
| `gap`            | 子元素之间的间距（Grid 里同样可用）                                                            |

子元素属性：

| 属性          | 用途                                                                       |
|---------------|----------------------------------------------------------------------------|
| `flex-grow`   | 分剩余空间的份数（默认 `0`）                                               |
| `flex-shrink` | 空间不够时收缩的意愿度（默认 `1`）                                          |
| `flex-basis`  | grow/shrink 之前的初始尺寸（默认 `auto`）                                   |
| `flex`        | 简写：`flex: 1 1 auto;` —— grow / shrink / basis                           |
| `order`       | 不动 HTML 改视觉顺序（默认 `0`）                                            |
| `align-self`  | 单独覆盖容器的 `align-items`                                               |

### CSS Grid（二维布局）

Grid 是为**页面布局**生的：行和列同时存在。课件用 "Holy Grail" 布局（header / nav / main / footer）做引子。

容器属性：

| 属性                         | 用途                                                                |
|------------------------------|---------------------------------------------------------------------|
| `display: grid`              | 把元素变成 grid container                                           |
| `grid-template-columns`      | 列的轨道尺寸，例如 `200px 1fr` 或 `repeat(12, 1fr)`                  |
| `grid-template-rows`         | 行的轨道尺寸                                                        |
| `grid-template-areas`        | 给矩形区域命名，配合 `grid-area` 摆位                                |
| `gap`（`row-gap`、`column-gap`）| 轨道间距                                                          |
| `justify-items`、`align-items`  | 单元格内默认的内容摆位                                            |
| `justify-content`、`align-content` | 整张 grid 在容器里的位置                                       |

子元素摆位：

| 属性                                         | 用途                                       |
|----------------------------------------------|--------------------------------------------|
| `grid-row-start` / `grid-row-end`            | 按线号指定行跨度                            |
| `grid-column-start` / `grid-column-end`      | 按线号指定列跨度                            |
| `grid-row: 1 / 3`                            | 简写：从第 1 条线到第 3 条线                |
| `grid-row: span 2`                           | 只指定跨度，不固定起点                      |
| `grid-area: 1 / 2 / 3 / 3`                   | row-start / col-start / row-end / col-end  |

尺寸辅助：

- **`fr` 单位** —— 容器内"剩余空间的一份"。`1fr 2fr` 把剩余空间按 1:2 切。
- **`repeat(n, ...)`** —— 比如 `repeat(12, 1fr)` 写一个 12 列网格。
- **`minmax(min, max)`** —— 轨道至少 `min`、至多 `max`。常见写法 `minmax(200px, 1fr)`。
- **`auto-fill` vs `auto-fit`** —— 两者都按 `minmax` 尺寸尽量在一行里塞轨道；`auto-fit` 会**塌缩**空轨道，让现有 item 撑满整行；`auto-fill` 把空轨道**保留**着。想"内容少时也撑满整行"用 `auto-fit`，想"留位以备后用"用 `auto-fill`。

### 响应式策略与 mobile-first

课件把响应式提升到了 **Design Principle 2**："on the web, use responsive design"。理由很直白：设备尺寸差距太大（手机、平板、笔电、台式机、电视），把布局写死等于自找麻烦。

**mobile-first** 的写法是：基础 CSS 先按最小屏幕写（不放任何 media query），然后用 `min-width` 媒体查询逐级增强。两个好处：

1. 基础情况就是最简单的布局（单列），刚好和 cascade 对齐 —— 后续规则只需要在上面叠加；
2. 逼你想清楚什么内容才是真正重要的：360px 的屏幕上，你没法靠留白蒙混过关。

反过来 desktop-first 是先写桌面布局，再用 `max-width` 一层层"撤销"以适配小屏，写起来繁琐。

### viewport meta 标签

要让手机浏览器**老老实实**按你的 CSS 像素去渲染，而不是先伪装成桌面再缩放，HTML `<head>` 必须有这一行：

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

没有它，手机会假装自己是 980px 的虚拟桌面，你的 media query 就会安静地失灵。

### `@media` 查询（常见 breakpoint）

课件给出的语法：

```css
@media media-type and (media-feature-rule) {
  /* rules */
}
```

`media-type` 通常是 `screen` 或 `print`。`media-feature-rule` 可以查 `min-width`、`max-width`、`orientation`、是否有指针设备、配色偏好等等。

`trees` lab 用的 breakpoint 是这样划的（也和业界惯例对得上）：

| 范围              | 含义                |
|-------------------|---------------------|
| `< 400px`         | 小屏手机             |
| `400–600px`       | 大屏手机             |
| `>= 600px`        | 平板 / 桌面          |

其他常见 breakpoint：768px（平板）、1024px（小笔电）、1280px（桌面）。课件特别说：**不要去背 breakpoint —— 在你的内容自己崩掉的位置加断点就好**。

课件展示的组合写法：

```css
@media screen and (min-width: 600px), screen and (orientation: landscape) { ... }
@media (not (width < 600px)) and (not (width > 1000px)) { ... }
@media (30em <= width <= 50em) { ... }   /* range syntax */
```

### 流式图片

`trees` lab 用的就是教科书式套路：

```css
.card-image {
  max-width: 100%;
  height: auto;
}
```

`max-width: 100%` 让图片在容器变窄时缩到容器以下，`height: auto` 保留宽高比。如果写成固定 `width` 就把响应式打死了；只设 `height` 又会把图片拉变形。

### 设计基本功（来自 `Design.pdf`）

Design 那份课件文字不多、案例很多，明确点名的原则有：

- **Design is hard, but not thinking about it is disastrous**（Ralph Caplan，slide 2）；
- **设计是文化与时尚** —— 今天看着"现代"的东西五年后就过时了（slides 3–4）；
- **Design Principle 1**：找你真正的目标受众做测试（slide 5）；
- **Gestalt grouping** —— proximity（接近）、similarity（相似）、continuity（连续）、closure（闭合）：人会自动把相关元素当成一组（slides 7–8）；
- **whitespace 也是内容** —— 课件以 Knuth 的 *TeX manual* 和 `booktabs` 表格风格作为典范（slide 9），意思是：在元素四周留出空间，别把每个像素都填满；
- **文本宽度**对可读性的影响 —— "常见参考：每行 50–60 个字符 / 两个完整字母表 / 12 个单词 / 30em"（slides 10–12）。超过 75 字符之后，眼睛要折回去找下一行就开始累；
- **响应式设计** —— 设备百花齐放，设计也得跟着变（slides 13–15）；
- **Design Principle 2**：在 web 上用响应式设计（slide 16）；
- **网格 —— "简单的那一半"**：均匀划分的矩形网格，`960.gs` 是经典的 960px / 12 列示例（slides 17–22）。

所以 Design.pdf 里真正反复强调的，是 **whitespace、文本宽度 / 排版、Gestalt grouping、面向受众做测试、响应式思维、网格布局**。经典的 **CRAP**（Contrast 对比 / Repetition 重复 / Alignment 对齐 / Proximity 接近）四项 在 Gestalt 这部分其实是隐含着的，只是课件没用 CRAP 这套术语。值得顺带提一下这四个的实际含义：Contrast 是用反差告诉用户"这两件事不一样"；Repetition 是把字号、间距、配色这些样式语言在全站重复，让用户感知到一致性；Alignment 是同一类元素守同一根隐形参考线，杂乱感会立刻消失；Proximity 是"相关的东西靠近、不相关的东西离开"，比 Gestalt 那一段说的更直接。

## Grid 速查

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

要点：

- `1fr` 是"剩余空间的一份"——和固定轨道（`200px 1fr`）配合做侧栏特别顺手；
- `repeat(auto-fit, minmax(220px, 1fr))` 是不写任何 `@media` 就能响应式的"卡片网格一行流"；
- `grid-column: 1 / -1` 跨满所有列（`-1` 表示"最后一条线"）；
- `grid-row: span 2` 只声明高度、不锁起点，curriculum lab 里的 SPE 单元就靠它。

## Flexbox 速查

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

经验：

- 一次只关心一个方向时（一排按钮、一列表单字段），用 Flex；
- 行和列要同时对齐时（页面布局、dashboard），用 Grid；
- `gap` 在 Flex 和 Grid 里都好使；
- 给 flex item 加 `margin: auto` 会吃掉剩余空间 —— "把这个元素推到尽头"的经典写法。

## 媒体查询常用写法

mobile-first 的脚手架：

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

几个常用模式：

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

Responsive Layout 那段课件里反复出现的容器宽度套路：

```css
/* Bad: locks at 800px even on a phone */
main { width: 800px; }

/* Good: caps at 800px but shrinks on small screens, centred */
main { max-width: 800px; margin: 0 auto; }
```

## Lab 实操

### Lab 1 — `curriculum.md`（CV / 课程表网格）

**目标**：把一份 CS BSc 课程表（给定的 `curriculum.html`）排成 12 列的网格，每个单元的宽度由它的学分类名决定。

**已给样式**：body 用无衬线字体，背景是 University of Bristol 的浅绿色；每个 `.unit` 是更深一档的色块，标题条 `<b>` 被重新声明成 `display: block`，下面一段说明文字。所有元素 `padding: 5px` 让文字不贴边。背景色加在 `.unit` 容器上，**不是**加在内部 `<p>` 上 —— 这样段落自身的默认 margin 落在色块**内部**。

**要做到的行为**：

- 在 `<main>` 上用 grid，**12 列等宽**，`max-width: 1500px`、`margin: 0 auto;` 居中、`gap: 15px`；
- 各类宽度：
  - `.cp10` → 跨 2 列
  - `.cp15` → 跨 3 列
  - `.cp20` → 跨 4 列
  - `.cp40`（毕业项目）→ 跨 8 列
  - SPE（`y2-tb4`，没有 `cp` 类）→ 4 列宽且**跨 2 行**
- 目标是规则**最少** —— 一个类一条规则最理想。

**为什么类名是 `cp20` 而不是 `20cp`？** 因为 CSS 类选择器不能以数字开头（`.20cp` 是非法的，需要转义）。把字母放前面就合法了。

**实现草图**：

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

**坑点**：SPE 跨两行，会打乱后续单元的 auto-flow。三种应对：用 `grid-column-start` / `grid-row-start` 把 SPE 钉死、用 `grid-auto-flow: dense` 让后面的 item 回填，或者后续 year-3 的行/列摆位写死、让它自己解决。

**进阶挑战 —— 学年之间留更大间距**。两条都成立的做法：

1. 在两个学年之间留一行高度为 0 的空行 —— 上下两道 `gap` 加在一起就是双倍视觉间距；
2. 给每个学年最后的 TB2/TB4 单元加 `margin-bottom`（**不是** `padding-bottom` —— padding 会把彩色背景一起拉长）。

**预期结果**：三组"行的行" —— Year 1、Year 2、Year 3 —— 每组里再分 teaching-block 子行，单元在 TB 内从左到右排，SPE 块跨着 Year 2 的两个 TB，40CP 的毕业项目占掉 Year 3 TB2 行的三分之二。

### Lab 2 — `trees.md`（响应式图片画廊）

**目标**：给一组 Westonbirt 树木卡片（Westonbirt arboretum）做布局，让它们在三个 breakpoint 上重新排列。其中部分卡片带 `.featured` 类。

**已给样式**：body 用 Open Sans，header 是深绿配白字，每张 `.card` 是中绿配白字。最关键的一条是 `.card-image { max-width: 100%; height: auto; }`，让图片自适应宽度。

**容器始终生效的规则**：

- `margin: 0 auto;` 用来横向居中（必须写在 `padding` 前面）；
- `margin: 20px 0;` 留上下呼吸；
- `padding: 0 10px;` 留左右呼吸（必须用 padding，不能改成 margin，否则居中就失效）；
- `gap: 20px;`。

**Breakpoint 一览**：

| 宽度区间       | 列数    | featured 卡   | 普通卡  |
|----------------|---------|----------------|---------|
| `< 400px`      | 1       | 1×1            | 1×1     |
| `400–599px`    | 2       | 2×2            | 1×1     |
| `>= 600px`     | 4（max-width 960px）| 2×2 | 1×1     |

**实现草图（mobile-first）**：

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

**各 breakpoint 的预期表现**：

- **宽屏（`>= 600px`）**：4 等列、`max-width: 960px`、居中。两张 featured 各占一个 2×2 超级单元，其余 8 张 1×1 围着排；
- **平板 / 大屏手机（`400–600px`）**：只剩 2 列；featured 仍是 2×2（也就是占满两行的两列），普通卡 1×1；
- **小屏手机（`< 400px`）**：单列，每张卡都 1×1 —— featured 没有特殊待遇。这是**默认**情况（不在 media query 里），关键是把 `featured { span 2 / span 2 }` 包在 `@media (min-width: 400px)` 里，别让它泄漏到小屏。

**lab 给的调试小技巧**：Chrome / Edge 的普通窗口拖不到 400px 以下。按 F12 打开 DevTools，把它停靠到右侧，然后拖分隔条把可视区缩窄；或者用 device-emulation 工具栏（DevTools 左上第二个图标），挑一个手机预设。

**收尾的一个补充**：实际产品里每张卡通常会链到详情页。lab 建议改成 `<a class="card" href="...">`，把 `display: block` 加上，让整张卡（包括图片）都成为点击区，比包一层 `<div>` 更顺手。

## 易错点与重点

- **类名不能以数字开头**。`cp20` 而不是 `20cp` —— curriculum lab 明说过。ID 选择器同理。
- **背景色要加在对的元素上**。curriculum lab 里背景色加在 `.unit` 而不是 `.unit p`，否则段落默认 margin 会在每张卡里戳出一块 body 颜色的"洞"。
- **`<b>` 默认是 inline**。curriculum lab 把它重新声明成 `display: block`，标题条才会撑满整格。再次提醒：`display` 是 CSS 属性，不是 HTML 标签的固有事实。
- **先 `margin: 0 auto`，再 `padding: 0 10px`，顺序不能反**。trees lab 里如果改成 `margin: 0 10px;`，居中就丢了 —— padding 是写在已经居中的盒子内部的。
- **用 `max-width`，别用 `width`**。`width: 800px` 把布局焊死了，到手机上必崩；`max-width: 800px; margin: 0 auto;` 在桌面有上限，在小屏会优雅缩水。Responsive Layout 那段课件反复砸这条。
- **流式图片要 `max-width: 100%` 和 `height: auto` 一起用**。只设一个，要么变形、要么不缩。
- **mobile-first 优于 desktop-first**。把不带 `@media` 的默认状态当成最小屏布局，再用 `min-width` 增强 —— CSS 更短，cascade 也站在你这边。
- **别忘了 viewport meta 标签**。少了 `<meta name="viewport" content="width=device-width, initial-scale=1">`，手机浏览器会假装自己是桌面，你写的 `min-width: 600px` 永远在不该命中的时候命中。
- **`display: none` 与 `visibility: hidden` 不一样**。`none` 把元素从布局里完全拿掉（不占空间）；`hidden` 保留盒子但不可见。两者不能互换。
- **`auto-fill` vs `auto-fit`**。两者都按 `minmax` 尺寸尽量塞满轨道；`auto-fit` 之后会**塌缩**剩余空轨道，让现有 item 撑开；`auto-fill` 把空轨道**保留**。想让单卡也撑满整行，就用 `auto-fit`。
- **Grid 会打乱正常流**。curriculum lab 里 SPE 比别人高一截，需要 `grid-auto-flow: dense` 或写死 `grid-row-start` 才能让后续 item 排得干净。
- **breakpoint 由内容决定，不是从清单里抄**。课件给 `min-width: 600px` 这些是**举例**，不是教条。把窗口拖到**你自己的**布局崩掉的位置，那就是你的 breakpoint。
- **whitespace 也是内容**。Design 课件搬出 Knuth 的 *TeX manual* 和 `booktabs` 当佐证：留白是用来组织视觉的，不要"有空就填"。
- **每行 50–60 字符**。再宽，眼睛回扫到下一行就开始费劲，过 75 字符之后可读性断崖式下跌。文本容器加一条 `max-width: 60ch` 就好。
- **设计是品位 + 原则**。Design.pdf 开篇那句 "thinking about design is hard, but not thinking about it can be disastrous" 给整章定了调：原则帮你缩小搜索空间，但最后还是要靠你看一眼、做判断。
