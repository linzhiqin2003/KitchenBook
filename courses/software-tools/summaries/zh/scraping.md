# 第 17 章 — Web scraping

## 章节概览

所谓 Web scraping，就是用程序去拉网页，再从中抽取出结构化的数据。互联网上大约有一半流量根本不是真人产生的：搜索引擎索引、新闻聚合、安全扫描、广告反作弊机器人，全是自动化客户端。爬虫（如果它的活儿是建索引，也叫 spider）说白了就是没有 GUI 的浏览器，一个会自动发 HTTP 请求的脚本而已。

整章把 scraping 流水线拆成两个互补的部分讲：

1. **Acquisition（获取）** —— 把页面从网络上拿下来。课程把 `wget` 当作"模范爬虫"的命令行代表来教，并提到 Python 里对应的程序内方案是 `requests` 库。
2. **Extraction（解析）** —— 把 HTML 解析成一棵可以查询的树。课程在这部分用的是 `BeautifulSoup`（包名 `bs4`）：它本身不是 parser，而是在 HTML parser 之上叠了一层方便导航和查询的 API。

课程很明确地强调，scraping 是被伦理和法律约束的事情，而不是一句"我能爬到"就完事：要尊重 `robots.txt`、能用官方 API 就别去 scrape、转载时小心版权、登录后内容尤其要谨慎，并给自己加上速率限制别把别人服务器搞垮。

Lab 用的是一个本地小站 `cattax`（一棵关于猫科动物分类的页面树：Felidae → Felinae/Pantherinae → 各物种），跑在 `localhost:8080`，免得 200 个学生同时去捶同一个真实站点。

## 核心知识

### 合法性与伦理（重点强调）

- **`robots.txt`** —— 一个放在站点根目录的纯文本文件（比如 `https://example.com/robots.txt`），按 User-Agent 分组告诉爬虫哪些路径可以爬、哪些不能。格式长这样：

  ```
  User-Agent: foobot
  Allow: /example/page/
  Disallow: /example/page/disallowed.gif

  User-Agent: bazbot
  Disallow: /example/page.html
  ```

  爬虫被期望去查自己的 User-Agent 字符串然后遵守里面的规则。一个关键提醒：`robots.txt` **没有任何强制力**，它没有安全防线，纯粹是君子协定。真正的访问控制必须用真正的认证。把禁止的路径写在 `robots.txt` 里反而等于在公开"这些路径存在"，这本身是个小小的反向自爆。`wget` 是个"好爬虫"，会自动读 `robots.txt`，你写自己的爬虫时也应该照做。

- **版权与转载** —— 能 *访问* 公开内容并不意味着你有 *转载*（无论原样还是修改）的权利。版权是和访问权分开的另一回事。

- **登录后内容** —— 爬登录之后才能看的内容（比如社交媒体），会带来额外的伦理和法律问题。发给小范围受众的内容隐含着隐私期待，你把它公开转载就可能背叛信任、招来法律风险。

- **礼貌爬取**：
  - 即便对方没要求，请求之间也要插点小延迟（`wget -w 1` 表示请求间隔 1 秒）。
  - 用一个诚实的 User-Agent 表明身份。
  - 把响应缓存到本地，别反复重抓。
  - 太凶的爬取会让你 IP 被拉黑，也可能事实上把小服务器打瘫。
  - **永远先找 API**。如果站点有 JSON 接口就直接用，对你更省事，对服务器也更友好。

### HTTP 客户端：`wget`（课程实际教的命令行工具）

`wget` 在课程里被当作一个自包含的爬虫来介绍。常用参数循序渐进是这样：

| 命令 | 作用 |
|---------|--------------|
| `wget <url>` | 只下载 `<url>` 这一个资源，仅此而已。 |
| `wget -p <url>` | 下载页面 **加** "page requisites" —— CSS、图片等等 —— 让本地副本能正常渲染。同时会抓 `robots.txt`。文件落在以主机名命名的子目录里（比如 `localhost:8080/`）。 |
| `wget -r -l N <url>` | 递归：跟着链接走，最深 `N` 层（不指定 `-l` 时默认 5）。默认只在同一域内。 |
| `wget -m <url>` | Mirror：整站离线副本的合理默认 —— 无限递归、时间戳检查等等。 |
| `wget -w 1 ...` | 请求之间等 1 秒，礼貌参数。 |
| `wget --spider` | 不真的下载 —— 只是检查 URL 是否可达。当 link checker 用很方便。 |
| `wget -i file --force-html` | 从 `file`（按 HTML 处理）里读 URL 然后下载，适合批量链接检查。 |
| `wget -nc` | "No clobber" —— 不覆盖已经存在的文件（避免重抓时悄悄把缓存写坏）。 |

递归的 Accept/Reject 选项用来控制跟到哪些域和路径。默认情况下 `-r` 只待在原域内，正因如此 `-r -l 2` 在小站点上还能 hold 住，但一旦放它跳到 Wikipedia 就会爆炸。

### HTTP 客户端：`requests`（Python，"further reading"里提到）

幻灯片和 lab 抓页面都用 `wget`，但是 lab 的 *Further reading* 里明确建议：等你开始写 Python 工具的时候，就该转向 `requests`，免得在 Python 里再去 shell out 调一个外部二进制。

课程没有深挖 `requests` 本身，标准用法跟你预期的一样：`requests.get(url, params=..., headers=..., timeout=...)`，先看 `response.status_code`，再读 `response.text`、`response.content` 或 `response.json()`。具体见下面的速查表。

### 解析：`BeautifulSoup`（本章主角 Python 工具）

> "Python library for extracting data from HTML files. Not a HTML parser itself, but can use many parsers."

当前版本是 BeautifulSoup 4，包名 `bs4`。安装用 `sudo apt install python3-bs4`，或者在 venv 里 `pip install beautifulsoup4`。

Lab 里的基础用法：

```python
from bs4 import BeautifulSoup

filename = "news.html"
handle = open(filename, 'r')
text = handle.read()
soup = BeautifulSoup(text)             # slides version (no parser specified)
# or, more correctly:
soup = BeautifulSoup(open(file, 'r'), features='html.parser')
```

`soup` 是一棵由 `Tag` 对象组成的、可以导航的树。Lab 里展示的关键操作：

- `soup.title` —— `<title>` 标签（一个 `Tag` 对象，不是字符串）。
- `soup.title.text` —— 标签内的文本内容（`str`）。
- `soup.head` —— `<head>` 子树。
- `soup.head.findChildren()` —— `<head>` 的直接子节点列表。
- `soup.head.meta['charset']` —— 标签上的属性访问（`<head>` 里 `<meta>` 的 `charset` 属性）。
- `soup.get_text()` —— 整页可见文本拼成一个字符串，适合喂进 NLP 流水线。
- `soup.find_all('strong')` —— 全树所有 `<strong>` 标签的列表。
- `soup.find_all('div', class_='container')` —— 按标签 + 属性查找。`class_` 末尾的下划线是为了避开 Python 的 `class` 关键字。（对 `<div class="container highlight">` 也能匹配上，因为 BS4 把多 class 属性当成 token 列表处理。）
- `soup.h1.text` —— 便捷写法：`.h1` 返回树里 *第一个* `<h1>`。

`Tag` 和 `str` 的区别非常重要：`Tag` 对象有 BS4 的方法（`find_all`、属性查找等等），字符串就只有字符串方法。

### 静态页 vs JS 渲染页

幻灯片只覆盖静态 HTML。Lab 的 *Further reading* 明确划了边界：

> "We've also been dealing with the content of static websites... Scraping dynamic sites gets trickier, as your scraper needs to have a browser-like context to execute Javascript within."

它把这种情况指向 **Selenium**（`https://www.selenium.dev/documentation/`）。本章里 *没有* 提 Playwright。一句话总结：如果 `requests` + BeautifulSoup 拿回来的页面接近空的，那内容八成是浏览器端 JS 渲染出来的，你需要一个 headless browser。

### 站点发现

- **`robots.txt`** 兼具发现作用：被禁的路径明明白白列在里面，并且按定义就是存在的。
- **递归跟链接** 是最家常的发现方式，也就是 `wget -r -l N`。本质上是对链接图做 BFS，深度 N，默认只在同域。Sitemap、BFS vs DFS、分页模式这些本章没有正式覆盖 —— 幻灯片讨论的爬取策略杠杆只有"递归深度"和"域名范围"两个。

### 数据清洗与存储

Lab 把你从"全打印出来"推到"全存进一个 Python `dict`"，以页面标题为 key、'info' 段落文本为 value。这是本章关于结构化存储的唯一一处提及。CSV、SQLite、JSON 文件这些都没有明讲；按你的使用场景挑合适的就行。

### 编码

Lab 演示了通过 `soup.head.meta['charset']` 拿到文档声明的编码（一般是 `UTF-8`）。BeautifulSoup 自己内部会做编码检测，把所有东西归一化成 Unicode 字符串，所以等你调到 `.text` 的时候，编码问题已经在你身后了。

### 反爬

没有直接覆盖。幻灯片高层提示：暴力爬取 → 服务器拉黑；爬登录后内容在伦理上很微妙；User-Agent 字符串是可以设置的（`crawl.md` 的 further-exercise 2 让你用 `wget` 发一个自定义 User-Agent，再到服务器端观察）。Cookies、session、登录流程、CSRF token、隐藏表单字段这些，本章不在范围内。

## requests 速查

（Lab 本身没用，但被标记为推荐的下一步。）

```python
import requests

# --- GET ---
r = requests.get("https://example.com/api/items",
                 params={"page": 2, "limit": 50},
                 headers={"User-Agent": "my-crawler/0.1 (you@example.com)"},
                 timeout=10)

r.status_code        # int, e.g. 200, 404
r.ok                 # bool: True for 2xx
r.raise_for_status() # raise on 4xx/5xx
r.headers            # dict-like response headers
r.encoding           # detected text encoding
r.text               # decoded body as str
r.content            # raw bytes (use for images, PDFs, ...)
r.json()             # parse JSON body -> dict/list

# --- POST ---
r = requests.post("https://example.com/login",
                  data={"user": "alice", "pw": "secret"})   # form-encoded
r = requests.post("https://example.com/api",
                  json={"q": "felidae"})                    # JSON body

# --- Sessions: keep cookies across requests, reuse TCP connection ---
with requests.Session() as s:
    s.headers.update({"User-Agent": "my-crawler/0.1"})
    s.get("https://example.com/login")          # collects cookies
    s.post("https://example.com/login", data={...})
    page = s.get("https://example.com/private") # cookies sent automatically

# --- Politeness ---
import time
for url in urls:
    r = requests.get(url, timeout=10)
    time.sleep(1)                                # 1s rate limit
```

本章暗示但没有点破的几条要点：永远显式设 `timeout`（默认是 *没有 timeout*，挂死的连接会让你的脚本永远卡住）；永远设一个诚实的 `User-Agent`；如果反复打同一台主机，复用一个 `Session`。

## BeautifulSoup 速查

```python
from bs4 import BeautifulSoup

# --- Construct ---
# Specify the parser explicitly to avoid a UserWarning and ensure consistent
# behaviour across machines. 'html.parser' is built-in; 'lxml' is faster but
# external; 'html5lib' is most lenient.
soup = BeautifulSoup(open("page.html", "r"), features="html.parser")
soup = BeautifulSoup(html_string, "html.parser")
soup = BeautifulSoup(response.content, "html.parser")  # bytes from requests

# --- Whole-page text ---
soup.get_text()            # everything visible, one big string
soup.get_text(separator="\n", strip=True)   # cleaner

# --- First match by tag name ---
soup.title                 # <title>...</title>  (Tag)
soup.title.text            # text inside title    (str)
soup.h1                    # first <h1>
soup.head.meta             # first <meta> inside <head>

# --- Attribute access on a Tag ---
soup.head.meta['charset']      # value of charset attribute
soup.a.get('href')             # safer; returns None if missing
soup.a.attrs                   # full dict of attributes

# --- Tree walking ---
soup.head.findChildren()       # all descendants of <head> (BS4 also has
                                # .children, .descendants, .parent, .parents,
                                # .next_sibling, .previous_sibling)

# --- find / find_all ---
soup.find('div')                            # first <div> anywhere
soup.find_all('strong')                     # all <strong>
soup.find_all('div', class_='container')    # by tag + class
soup.find_all('a', href=True)               # all <a> that HAVE an href
soup.find_all(['h1', 'h2', 'h3'])           # multiple tag names
soup.find_all(id='main')                    # by id
soup.find_all(attrs={'data-role': 'card'})  # arbitrary attribute

# --- CSS selectors (often the most concise) ---
soup.select('div.container')                # all <div class="container">
soup.select('div.container > p.info')       # direct-child combinator
soup.select_one('#main h1')                 # first match

# --- Iterating results ---
for s in soup.find_all('strong'):
    print(s.text)             # just the text inside each <strong>

# --- Filtering by class when an element has multiple classes ---
# BS4 treats the class attribute as a list, so class_='container' will match
# <div class="container highlight"> just fine.
```

## Lab 实操

Lab 分两部分。第一部分（`crawl.md`）完全是用 `wget` 去打本地服务器；第二部分（`soup.md`）是用 BeautifulSoup 去解析同一个站点的 HTML。两者共用同一份 `cattax` 数据集（关于猫科动物分类的小页面树）。

### Part 1 — `crawl.md`（多页爬取）

准备：

```bash
tar -xzf cattax.tar.gz                       # extract the demo site
cd cattax && python -m http.server 8080      # serve it locally
# (or use darkhttpd; either works)

# in a sibling directory, work as the "client"
mkdir client && cd client
```

需要内化的 `wget` 命令演进：

```bash
wget localhost:8080/index.html
# Just the HTML. Opens locally without CSS/images, looks "wrong".

wget -p localhost:8080/index.html
# -p = page requisites. Pulls catstyle.css, images, AND robots.txt.
# Files end up in a localhost:8080/ subdir, mirroring the host name.

wget -r -l 1 localhost:8080/index.html
# Recursive, depth 1. Pulls index.html + the 2 pages it links to (Felinae,
# Pantherinae). Wikipedia link in the footer is NOT followed because it's
# off-domain. Newly downloaded pages still have dead internal links because
# their children weren't fetched.

wget -r -l 2 localhost:8080/index.html
# Goes one hop further. On this small site the file count balloons.
# Lesson: recursion depth grows roughly geometrically; on a real site
# (try this on Wikipedia) -l 2 would download hundreds of resources.

rm -r localhost:8080
wget -m localhost:8080/index.html
# -m = mirror. Sensible defaults for a full offline copy: infinite recursion,
# timestamping, etc. Pair with `-w 1` to be polite on real servers.
```

`crawl.md` 里几个值得记住答案的延伸题：

- `--spider` 让 `wget` 只检查 URL 不下载 —— 完美的链接检查器。配合 `-i page.html --force-html`，`wget` 会从那个 HTML 文件里读出链接来检查。
- 自定义 User-Agent 用 `wget --user-agent="MyBot/1.0" ...`。在服务器端的访问日志里你会看到这个名字而不是默认的 `Wget/1.x`。
- `wget -r -l 1 http://example.com` 在 `example.com` 域内顺链接走一跳。`wget -p http://example.com` 只抓首页，但会把渲染所需的所有 requisite 一起拉过来（包括 CDN 图片之类的跨域资源）。两件不同的事情。
- 递归的 Accept/Reject 选项（`-D domain-list`、`--span-hosts`）让你可以有意识地越过域边界。
- `-nc` = "no clobber"，拒绝覆盖。Clobbering 就是覆盖已存在文件的动作；恢复一个未完成的 mirror 时你不想要它，刷新一份快照时你又想要它。

### Part 2 — `soup.md`（单页抽取 → 存进 dict）

交互式过一遍（在 `cattax` 的父目录里跑 `python3`）：

```python
from bs4 import BeautifulSoup
file = "cattax/index.html"
soup = BeautifulSoup(open(file, 'r'))

# Inspect the whole document
soup                       # prints the source HTML
soup.get_text()            # visible text only
print(soup.get_text())     # roughly how the page looks visually

# Targeted access
soup.title                 # <title>...</title>     (Tag)
soup.title.text            # contents               (str)

# Tree walking
soup.head                              # <head> subtree
soup.head.findChildren()               # immediate kids
soup.head.meta['charset']              # attribute lookup -> 'utf-8'
```

`soup.md` 的练习：

1. *列出所有 `<strong>` 元素并打印其中文本。*

   ```python
   for s in soup.find_all('strong'):
       print(s.text)
   ```

2. *找出所有 class 为 `container` 的 `<div>`，包括那些挂了多个 class 的。*

   ```python
   soup.find_all('div', class_='container')
   # works even for <div class="container highlight"> because BS4 treats
   # the class attribute as a list of class tokens.
   ```

### `scrape.py` 注释版

Lab 给了这个最小脚本。把它放到 `cattax/` 的同级目录（不是放进去），然后跑 `python3 scrape.py`：

```python
from bs4 import BeautifulSoup
import os

for file in os.listdir('cattax'):                  # every name in cattax/
    if file[-4:] == 'html':                        # crude .html filter
        soup = BeautifulSoup(open('cattax/'+file, 'r'),
                             features='html.parser')
        print(soup.title.text + " : " + soup.h1.text)
```

逐行干了什么：

1. 导入 `BeautifulSoup` 和 `os`（用于列目录）。
2. `os.listdir('cattax')` 返回 `cattax/` 下的每一个条目。
3. `file[-4:] == 'html'` 只保留以 `html` 结尾的项（注意：这个切片把 `.html` 当作末尾 4 个字符来抓，是个糙的 hack，不是严谨的扩展名校验）。
4. 对每个 HTML 文件解析成 `soup`，显式指定 `features='html.parser'`（消掉幻灯片版本里那个"未指定 parser"的 BS4 警告）。
5. 把页面的 `<title>` 文本和 `<h1>` 文本用 `" : "` 拼起来打印。

`soup.md` 接下来让你扩展这个脚本：

1. **打印每页的 'info' 段落文本**。cattax 页面里有一个 `<p class="info">...</p>` 块；在循环里加一行 `print(soup.find('p', class_='info').text)` 就行。

2. **只对叶子节点打印** —— 也就是页面本身没有 `container` div 的那些（即物种页，不是分类页）。用这个跳过：

   ```python
   if soup.find('div', class_='container') is None:
       # only species pages reach here
       ...
   ```

3. **存进 dict 而不是直接打印**，这样数据可以复用。Key = 页面标题，value = info 块的文本：

   ```python
   from bs4 import BeautifulSoup
   import os

   leaves = {}
   for file in os.listdir('cattax'):
       if file[-4:] == 'html':
           soup = BeautifulSoup(open('cattax/'+file, 'r'),
                                features='html.parser')
           if soup.find('div', class_='container') is None:
               leaves[soup.title.text] = soup.find('p', class_='info').text
   ```

   用 `python3 -i scrape.py` 跑，跑完会留在 REPL 里，可以交互地玩 `leaves`。这就是本章关于"我爬完东西了，接下来想用它"的标准动作 —— 先装进 dict，交互式看看，等真有需要再升级到 CSV/JSON/SQLite。

## 易错点与重点

- **永远先看 `robots.txt`**，并尊重它。它是君子协定，但君子才是重点。`wget` 会替你读；如果你用 `requests` 自己写爬虫，那就得自己读。
- **能用官方 API 就别 scrape**。为程序化访问设计的 JSON 端点更好用、更稳定，对服务器也更友好。Scraping 是没有 API 时的退路。
- **就算对方没要求你也要给自己加速率限制**。CLI 用 `wget -w 1`；`requests` 用 `time.sleep(1)`。粗暴爬取会让你被拉黑，更糟的是把小服务器搞瘫。
- **设一个诚实的 User-Agent**。撒谎说自己是谁，既不礼貌，在某些司法管辖区还会被视为恶意访问的迹象。
- **递归深度涨得很快**。在真实站点上 `wget -r -l 2` 可以拉下几百 MB。永远从 `-l 1` 起步再往上加。`wget -m` 是给你"我真的就要全部"的时候用的。
- **别不小心跨域**。`wget -r` 默认只在原域内；`--span-hosts` 会把这个限制解掉。链接顺到 Wikipedia 或者 CDN，你的爬取就要指数爆炸。
- **`wget -p` 抓 requisites；`-r` 抓被链接到的页面**。两件不同的事，lab 也在考你是不是真的理解了这个区别（`crawl.md` 里的延伸题 3）。
- **构造 `BeautifulSoup` 时显式指定 parser**。省掉 `features=` 也能跑，但会警告，而且 BS4 选哪个 parser 取决于你装了什么 —— 不可移植。
- **`Tag` ≠ `str`**。`soup.title` 是 `Tag`，支持 BS4 方法；`soup.title.text` 是 `str`，只支持字符串方法。把这两个搞混是 BS4 新手最常见的 bug。
- **`class_=` 而不是 `class=`**。Python 关键字冲突；`find` / `find_all` 的 `class_` 参数能正确处理多 class 属性（BS4 把 `class` 当成 token 列表）。
- **版权和访问权是两回事**。能下载不等于有权转载。对登录后/私有内容尤其要小心，那里用户是有隐私期待的。
- **静态页 vs JavaScript 渲染**。BS4 只能看到服务器发回来的那份 HTML。如果页面是浏览器里靠 JS 把自己拼起来的，BS4 拿到的结果会接近空 —— 升级到 Selenium（lab 的推荐）或者类似的 headless browser 工具。
- **`requests.get` 永远要设 timeout**。默认是没有 timeout 的，挂死的 TCP 连接会把你的脚本永远冻住。
- **隐含的目录命名约定**。`wget` 把文件存在以主机名命名的目录下（比如 `localhost:8080/`），不是按 URL path。爬多个主机时这一点很有用，但第一次见会有点意外。
