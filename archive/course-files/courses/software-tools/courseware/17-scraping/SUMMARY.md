# Chapter 17 — Web scraping

## Overview

Web scraping = programmatically fetching web pages and extracting structured
data from them. Roughly half of all web traffic is non-human: search indexers,
news aggregators, security probes, ad-fraud bots, and so on. Crawlers (a.k.a.
"spiders" when their job is indexing) are just automated HTTP clients —
browsers without the GUI.

This chapter covers two complementary halves of the scraping pipeline:

1. **Acquisition** — getting pages off the network. The course teaches `wget`
   as the canonical "good bot" CLI crawler, and points at Python's `requests`
   library as the in-program equivalent.
2. **Extraction** — parsing HTML into a tree you can query. The course uses
   `BeautifulSoup` (`bs4`) for this; an HTML parser plus a navigation/search
   API on top of it.

The course is explicit that scraping is governed by ethics and law, not just
technical capability: respect `robots.txt`, prefer official APIs when
available, beware copyright when republishing, be especially careful with
authenticated content, and rate-limit yourself so you don't overload servers.

The lab uses a small local site `cattax` (a tree of pages about cat taxonomy:
Felidae → Felinae/Pantherinae → individual species) served on
`localhost:8080`, so 200 students aren't all hammering the same real site.

## Core knowledge

### Legality & ethics (heavy emphasis)

- **`robots.txt`** — a plain text file at the root of a site (e.g.
  `https://example.com/robots.txt`) that tells crawlers which paths they may
  or may not access, on a per-User-Agent basis. Format:

  ```
  User-Agent: foobot
  Allow: /example/page/
  Disallow: /example/page/disallowed.gif

  User-Agent: bazbot
  Disallow: /example/page.html
  ```

  Crawlers are expected to look up their own User-Agent string and obey the
  rules. Critical caveat: `robots.txt` does **not** enforce anything — it has
  no security teeth. It is an honour system. Real access control needs real
  authentication. Listing forbidden paths in `robots.txt` actually *advertises*
  their existence, which is itself a minor footgun. `wget` is a "good bot" and
  reads `robots.txt` automatically; you should write good bots too.

- **Copyright & republishing** — being able to *access* public content does
  not give you the right to *republish* it (in original or modified form).
  Copyright applies separately from access.

- **Authenticated content** — scraping behind a login (e.g. social media)
  raises additional ethical and legal concerns. Content posted to a limited
  audience has implicit privacy expectations; reposting it publicly can betray
  confidences and create legal exposure.

- **Polite crawling**:
  - Insert small delays between requests even if the site doesn't ask
    (`wget -w 1` is "1 second between requests").
  - Identify yourself with an honest User-Agent.
  - Cache responses locally so you don't refetch.
  - Aggressive crawls can get your IP blacklisted, and can functionally
    DoS small servers.
  - **Always look for an API first.** If the site has a JSON endpoint,
    use it — easier for you, kinder to the server.

### HTTP client: `wget` (the CLI tool the course actually teaches)

`wget` is presented as a self-contained crawler. The progression of flags:

| Command | What it does |
|---------|--------------|
| `wget <url>` | Download the single resource at `<url>`, nothing else. |
| `wget -p <url>` | Download the page **plus** "page requisites" — CSS, images, etc. — so the local copy renders the same. Also fetches `robots.txt`. Files land under a folder named after the host (e.g. `localhost:8080/`). |
| `wget -r -l N <url>` | Recursive: follow links, up to depth `N` (default 5 if `-l` omitted). Stays on the same domain by default. |
| `wget -m <url>` | Mirror: sensible defaults for full-site offline copy — infinite recursion, timestamp checking, etc. |
| `wget -w 1 ...` | Wait 1 second between requests. Politeness flag. |
| `wget --spider` | Don't actually download — just check that URLs are reachable. Useful as a link checker. |
| `wget -i file --force-html` | Read URLs from `file` (treated as HTML) and download them. Good for batch link checks. |
| `wget -nc` | "No clobber" — don't overwrite files that already exist (avoid re-downloading and silently corrupting your cache). |

Recursive Accept/Reject options control which domains/paths are followed; by
default `-r` stays on the original domain, which is what makes `-r -l 2`
manageable on a small site but explosively bad if you let it follow links to
Wikipedia.

### HTTP client: `requests` (Python, mentioned in "further reading")

The slides and lab use `wget` for fetching, but the lab's *Further reading*
section explicitly recommends moving to `requests` once you're writing a
Python tool, so you don't shell out to a second binary.

The course doesn't drill into `requests` itself, but standard usage is what
you'd expect: `requests.get(url, params=..., headers=..., timeout=...)`,
inspect `response.status_code`, then read `response.text`,
`response.content`, or `response.json()`. See the cheat sheet below.

### Parsing: `BeautifulSoup` (the chapter's main Python tool)

> "Python library for extracting data from HTML files. Not a HTML parser
> itself, but can use many parsers."

Current version is BeautifulSoup 4, package name `bs4`. Install via
`sudo apt install python3-bs4` or `pip install beautifulsoup4` in a venv.

Basic usage from the lab:

```python
from bs4 import BeautifulSoup

filename = "news.html"
handle = open(filename, 'r')
text = handle.read()
soup = BeautifulSoup(text)             # slides version (no parser specified)
# or, more correctly:
soup = BeautifulSoup(open(file, 'r'), features='html.parser')
```

A `soup` object is a navigable tree of `Tag` objects. Key navigation moves
the lab demonstrates:

- `soup.title` — the `<title>` tag (a `Tag` object, not a string).
- `soup.title.text` — the textual content inside that tag (a `str`).
- `soup.head` — the `<head>` subtree.
- `soup.head.findChildren()` — list of immediate children of `<head>`.
- `soup.head.meta['charset']` — attribute access on a tag (the `charset`
  attribute of the `<meta>` tag inside `<head>`).
- `soup.get_text()` — the entire visible text of the page as one string. Good
  for feeding pages into NLP pipelines.
- `soup.find_all('strong')` — list of all `<strong>` tags anywhere.
- `soup.find_all('div', class_='container')` — find by tag + attribute. The
  trailing underscore on `class_` avoids a clash with Python's `class`
  keyword. (For `<div class="container highlight">` this still matches,
  because BS4 treats the multi-class attribute as a list.)
- `soup.h1.text` — convenience: `.h1` returns the *first* `<h1>` in the tree.

The distinction between a `Tag` and a `str` is load-bearing: `Tag` objects
have BS4 methods (`find_all`, attribute lookup, etc.); strings only have
string methods.

### Static vs JS-rendered pages

The slides cover static HTML only. The lab's *Further reading* explicitly
flags the limit:

> "We've also been dealing with the content of static websites... Scraping
> dynamic sites gets trickier, as your scraper needs to have a browser-like
> context to execute Javascript within."

It points readers at **Selenium** (`https://www.selenium.dev/documentation/`)
for those cases. Playwright is *not* mentioned in this chapter. The takeaway:
if `requests` + BeautifulSoup returns a near-empty page, the content is
probably rendered client-side in JS and you need a headless browser.

### Site discovery

- **`robots.txt`** doubles as a discovery aid: forbidden paths are listed
  there and exist by definition.
- **Recursive link following** is the bread-and-butter discovery method, as
  shown by `wget -r -l N`. This is essentially BFS over the link graph, with
  depth N and a stay-on-domain default. Sitemaps, BFS vs DFS, and pagination
  patterns are not formally covered in this chapter — recursion depth and
  domain scoping are the only crawling-strategy levers the slides discuss.

### Data cleaning & storage

The lab nudges you from "print everything" to "store everything in a Python
`dict`" with page titles as keys and 'info'-paragraph text as values. This is
the chapter's only mention of structured storage. CSV, SQLite, JSON files —
none are explicitly covered here; pick the right one for your use case.

### Encoding

The lab demonstrates pulling the document's declared encoding via
`soup.head.meta['charset']` (typically `UTF-8`). BeautifulSoup itself does
encoding detection internally — it normalises everything to Unicode strings,
so by the time you call `.text` you're already past the encoding question.

### Anti-scraping

Not directly covered. The slides flag at a high level that aggressive
scraping → server blacklisting, that scraping authenticated content is
ethically fraught, and that User-Agent strings can be set (further-exercise
2 in `crawl.md` asks you to send a custom User-Agent via `wget` and observe
it server-side). Cookies, sessions, login flows, CSRF tokens, and hidden
form fields are out of scope for this chapter.

## requests cheat sheet

(Not used in the lab itself, but flagged as the recommended next step.)

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

Key points the chapter implies but doesn't spell out: always set a `timeout`
(default is *no timeout* and a hung connection will hang your script
forever); always set an honest `User-Agent`; reuse a `Session` if you're
hitting the same host repeatedly.

## BeautifulSoup cheat sheet

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

## Lab walkthrough

The lab has two parts. Part 1 (`crawl.md`) is purely about `wget` against a
local server. Part 2 (`soup.md`) is about parsing the same site's HTML with
BeautifulSoup. They share the same `cattax` dataset (a small tree of pages
about cat taxonomy).

### Part 1 — `crawl.md` (multi-page crawl)

Setup:

```bash
tar -xzf cattax.tar.gz                       # extract the demo site
cd cattax && python -m http.server 8080      # serve it locally
# (or use darkhttpd; either works)

# in a sibling directory, work as the "client"
mkdir client && cd client
```

Progression of `wget` invocations to internalise:

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

Further-exercise prompts in `crawl.md` worth knowing answers to:

- `--spider` makes `wget` check URLs without downloading — perfect link
  checker. Combined with `-i page.html --force-html`, `wget` reads URLs
  from the HTML file's links.
- A custom User-Agent is set with `wget --user-agent="MyBot/1.0" ...`. On
  the server side you'll see it in the access log instead of the default
  `Wget/1.x`.
- `wget -r -l 1 http://example.com` crawls links one hop deep on
  `example.com` only. `wget -p http://example.com` fetches just the index
  but pulls every requisite needed to render it (including off-domain
  ones like CDN-hosted images). Different jobs.
- Recursive Accept/Reject options (`-D domain-list`, `--span-hosts`) let
  you cross domain boundaries deliberately.
- `-nc` = "no clobber" — refuse to overwrite. Clobbering is the act of
  overwriting an existing file; you don't want it when you're resuming a
  partial mirror, you do want it when you're refreshing a snapshot.

### Part 2 — `soup.md` (single-page extraction → store as dict)

Interactive walkthrough (run `python3` in the parent of `cattax`):

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

`soup.md` exercises:

1. *List all `<strong>` elements and print their text.*

   ```python
   for s in soup.find_all('strong'):
       print(s.text)
   ```

2. *Find all `<div>` with class `container`, including divs that have multiple classes.*

   ```python
   soup.find_all('div', class_='container')
   # works even for <div class="container highlight"> because BS4 treats
   # the class attribute as a list of class tokens.
   ```

### `scrape.py` annotated

The lab ships this minimal script. Put it in the directory containing
`cattax/` (not inside) and run `python3 scrape.py`:

```python
from bs4 import BeautifulSoup
import os

for file in os.listdir('cattax'):                  # every name in cattax/
    if file[-4:] == 'html':                        # crude .html filter
        soup = BeautifulSoup(open('cattax/'+file, 'r'),
                             features='html.parser')
        print(soup.title.text + " : " + soup.h1.text)
```

What it does, line by line:

1. Imports `BeautifulSoup` and `os` (for filesystem listing).
2. `os.listdir('cattax')` returns every entry in the `cattax/` directory.
3. `file[-4:] == 'html'` keeps only entries ending in `html` (note: the
   slice catches `.html` as the last 4 chars; it's a quick hack, not a
   robust extension check).
4. For each HTML file, parse it into a `soup`, explicitly using
   `features='html.parser'` (silences the BS4 "no parser specified" warning
   the slides version triggers).
5. Print the page's `<title>` text and `<h1>` text, joined by `" : "`.

`soup.md` then asks you to extend this script:

1. **Print the 'info' paragraph text** for each page. The cattax pages have
   a `<p class="info">...</p>` block; add `print(soup.find('p', class_='info').text)`
   inside the loop.

2. **Only print for leaf nodes** — pages that don't themselves contain a
   `container` div (i.e. species pages, not category pages). Skip with:

   ```python
   if soup.find('div', class_='container') is None:
       # only species pages reach here
       ...
   ```

3. **Store in a dict instead of printing** so the data is reusable. Keys =
   page titles, values = info-box text:

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

   Run with `python3 -i scrape.py` to drop into the REPL afterwards and
   poke at `leaves` interactively. This is the chapter's canonical move
   for "I scraped something, now I want to use it" — load into a dict,
   inspect interactively, then graduate to CSV/JSON/SQLite when needed.

## Pitfalls & emphasis

- **Always check `robots.txt` first**, and respect it. It's an honour
  system, but the honour is the point. `wget` reads it for you; if you
  write your own crawler in `requests`, you have to read it yourself.
- **Prefer official APIs over scraping**. JSON endpoints designed for
  programmatic access are easier, more stable, and politer to the server.
  Scraping is the fallback when no API exists.
- **Rate-limit yourself** even when not asked. `wget -w 1` for CLI;
  `time.sleep(1)` for `requests`. Aggressive crawling gets you blacklisted
  or, worse, takes down a small server.
- **Set an honest User-Agent.** Lying about who you are is rude and, in
  some jurisdictions, a sign of bad-faith access.
- **Recursion depth grows fast.** `wget -r -l 2` on a real site can pull
  hundreds of MB. Always start with `-l 1` and scale up. `wget -m` is for
  when you really do want everything.
- **Don't cross domains accidentally.** `wget -r` stays on-domain by
  default; `--span-hosts` undoes that. Following links to Wikipedia or a
  CDN can blow up your crawl exponentially.
- **`wget -p` fetches requisites; `-r` fetches linked pages.** They're
  different jobs and the lab tests that you understand the difference
  (further exercise 3 in `crawl.md`).
- **Specify a parser** when constructing `BeautifulSoup`. Omitting
  `features=` works but warns, and which parser BS4 picks depends on what
  you have installed — non-portable.
- **`Tag` ≠ `str`.** `soup.title` is a `Tag` and supports BS4 methods;
  `soup.title.text` is a `str` and only supports string methods. Mixing
  these up is the most common BS4 beginner bug.
- **`class_=` not `class=`.** Python keyword clash; the `class_` argument
  to `find`/`find_all` correctly handles multi-class attributes (BS4
  treats `class` as a list of tokens).
- **Copyright is separate from access.** Being able to download something
  doesn't grant the right to republish it. Be especially careful with
  authenticated/private content where users have privacy expectations.
- **Static vs JavaScript-rendered.** BS4 sees only the HTML the server
  sent. If the page builds itself in the browser via JS, BS4 will return
  near-empty results — graduate to Selenium (the lab's recommendation) or
  similar headless-browser tooling.
- **Always set a timeout** on `requests.get` — the default is no timeout,
  and a hung TCP connection will freeze your script forever.
- **Hidden-file convention.** `wget` saves under directories named after
  the host (e.g. `localhost:8080/`), not the URL path. Useful when
  scraping multiple hosts; surprising the first time you see it.
