# Chapter 11 — HTTP

## Overview

This chapter opens Part 2 of the Software Tools course (TB2), introducing the web by way of its foundational application-layer protocol: HTTP. It covers what a protocol is, how the Internet stack supports HTTP, the anatomy of URLs/URIs, the request/response cycle, HTTP methods, status code families, key headers, content types, cookies/sessions, REST principles, and a high-level view of TLS/HTTPS. The accompanying lab has three exercises: exploring HTTP using `nc` and `wget` (and the C web server `darkhttpd`), researching URL fragments and headers online, and building a simple Java/Spring Boot server. The required reading is RFC 7230 sections 2.1, 2.2, 2.7 and 3.

## Core knowledge

### Internet vs Web

The **Internet** is the global network of interconnected computers (routers, links, hosts) that moves bytes between machines. The **Web** is one application running *on top of* the Internet, defined by HTTP (the protocol), URLs (the addressing scheme), and HTML (the document format). HTTP was developed by Tim Berners-Lee at CERN in 1989; the version still in widespread use is HTTP/1.1, specified by RFCs 7230–7235.

HTTP is an **application-layer** protocol; it sits at the top of a stack:

```
7. Application   (HTTP)               <- you are here
6. Presentation  (TLS)
5. Session       (SOCKS)
4. Transport     (TCP, UDP)
3. Network       (IP)
2. Data Link     (MAC / Ethernet frames)
1. Physical      (Bluetooth, Ethernet PHY)
```

Concretely, an HTTP message is carried inside a **TCP** stream (port 80 for plain HTTP, 443 for HTTPS), which is itself carried inside **IP** packets (e.g. addressed to `137.222.0.38`), which are routed hop-by-hop across physical links. TCP guarantees ordered, reliable delivery: each segment carries a sequence number and checksum and is acknowledged (ACK 101) so out-of-order or lost packets are reassembled / retransmitted. IP provides best-effort routing of packets between source and destination addresses.

A **protocol** is just an agreed plan for how cooperating components interact. A toy example:

> Client: "Give me block #200" — Server: "Here you go: 0A 2F EE …"
> Client: "Give me block #45000" — Server: "Sorry, I couldn't find that block."

HTTP follows the same client–server, request–response shape, but adds rich **metadata** on top of the data: request/response headers and a numeric status code. The metadata is part of the protocol; the data (the hypertext document) is conceptually independent — an HTML page does not *have* to arrive over HTTP.

A typical server is just a loop:

```c
while (1) {
    req  = read();
    resp = serve(req);
    write(resp);
}
```

### URL anatomy

A **URL** (Uniform Resource Locator, a kind of **URI** / Uniform Resource Identifier; RFC 3986) names a resource. Full general form:

```
scheme://userinfo@host:port/path?query#fragment
```

Component meanings:

- **scheme**: the protocol or namespace, e.g. `http`, `https`, `ftp`, `ldap`, `mailto`, `news`, `tel`, `telnet`, `urn`. Examples from RFC 3986: `ftp://ftp.is.co.za/rfc/rfc1808.txt`, `mailto:John.Doe@example.com`, `tel:+1-816-555-1212`, `urn:oasis:names:specification:docbook:dtd:xml:4.1.2`.
- **userinfo** (optional): credentials such as `user:password@` — rarely used and unsafe in plain HTTP.
- **host**: the server, either a DNS name (`bristol.ac.uk`) or an IP literal (`[2001:db8::7]` for IPv6).
- **port** (optional): TCP port. Defaults: 80 for `http`, 443 for `https`. Development servers commonly use 8000 / 8080.
- **path**: the resource location on the server, e.g. `/`, `/files/index.html`, `/user/george/`. Maps to the `request-target` in an HTTP request.
- **query**: starts with `?`, a series of `name=value` parameters separated by `&`, e.g. `?name=welcome&action=view`. The same path can return different content for different queries.
- **fragment**: starts with `#`, identifies a sub-part of the resource (e.g. an HTML element with a matching `id`). The fragment is **never** sent to the server — it is resolved client-side by the browser to scroll/anchor.

Spaces and other "reserved"/non-ASCII characters in the path or query must be **percent-encoded**: a space becomes `%20` (or `+` in form-encoded queries), and characters such as `?`, `#`, `&`, `/`, `:`, `@`, `%`, ` `, `+` and non-ASCII bytes are encoded as `%HH` where `HH` is the byte's hex value.

### The request/response cycle

An HTTP message has the structure (RFC 7230):

```
HTTP-message = start-line
               *( header-field CRLF )
               CRLF
               [ message-body ]
```

- `start-line` is a **request-line** for requests or a **status-line** for responses.
- Headers are zero or more `field-name: field-value` lines.
- A blank line (`CRLF` on its own) separates headers from the optional body.
- All line terminators are `CRLF` (`\r\n`) — Unix-style `\n` alone breaks the protocol.

**Request-line** format:

```
method SP request-target SP HTTP-version CRLF
```

Example request:

```http
GET /index.html HTTP/1.1
Host: www.bristol.ac.uk
Connection: close
```

**Status-line** format:

```
HTTP-version SP status-code SP reason-phrase CRLF
```

Example response:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 1009

<!DOCTYPE html>
<html lang="en">
...
```

### HTTP methods

The verb tells the server what action to perform on the targeted resource.

- **GET** — Retrieve a copy of the target resource. Safe and idempotent; should have no body.
- **POST** — Submit payload data to a target resource (form submission, creating sub-resources, or invoking actions). Not idempotent.
- **PUT** — Replace the target resource with the request payload. Idempotent.
- **DELETE** — Delete the target resource. Idempotent.
- **HEAD** — Like GET but the server returns only the headers, no body. Used to fetch metadata (e.g. `Content-Length`, `Last-Modified`) cheaply.
- **OPTIONS** — Ask the server which methods/features are supported for a resource (commonly used for CORS preflight).
- **PATCH** — Apply a partial modification to the resource (as opposed to PUT's full replacement).

In practice many servers ignore `PUT`/`DELETE` and instead expose custom semantics over `POST`, e.g. `POST /files/README.txt?action=delete`.

### Status code families

The first digit groups responses by meaning:

- **1xx — informational**: provisional response, processing continues. Example: `100 Continue` (the server has received the request headers and the client should send the body).
- **2xx — success**: the request was received, understood and accepted. Examples: `200 OK`, `201 Created` (resource created by POST/PUT), `204 No Content` (success but no body).
- **3xx — redirection**: further action needed by the client. Examples: `301 Moved Permanently`, `302 Found`, `304 Not Modified` (cache still valid). The new location is supplied in the `Location` header.
- **4xx — client error**: the request is bad. Examples: `400 Bad Request`, `401 Unauthorized` (auth needed), `403 Forbidden` (auth not enough), `404 Not Found`, `405 Method Not Allowed`, `429 Too Many Requests`.
- **5xx — server error**: the server failed even though the request looked fine. Examples: `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`.

### Key headers

Headers carry the metadata. Names are case-insensitive.

- **Host** — The target host (and optional port). Mandatory in HTTP/1.1; lets one IP serve many virtual hosts.
- **Content-Type** — MIME type of the body, e.g. `text/html; charset=UTF-8`, `text/plain`, `image/jpeg`, `application/pdf`, `video/mp4`, `application/json`. For browsers this is the **first priority** when deciding how to interpret the body — a `.html` file served with `Content-Type: text/plain` will be displayed as raw text, not rendered.
- **Content-Length** — Size of the body in bytes. Lets the receiver know when the message ends.
- **Accept** — Sent by the client to advertise which content types it can handle (e.g. `Accept: text/html, application/json;q=0.9`). Drives content negotiation.
- **User-Agent** — Identifies the client software (browser, version, OS). Used by servers for stats, feature detection, blocking bots etc.
- **Authorization** — Carries credentials, e.g. `Authorization: Basic dXNlcjpwYXNz` or `Authorization: Bearer <token>`.
- **Set-Cookie** — Sent by the server to deposit a cookie in the client (`Set-Cookie: sid=1x33ad4; HttpOnly; Secure`).
- **Cookie** — Sent by the client on subsequent requests with previously stored cookies for that origin.
- **Cache-Control** — Caching directives (`no-cache`, `max-age=3600`, `public`, `private`).
- **Location** — Used in 3xx redirects (and `201 Created`) to give the new/created URL.
- **Connection** — Connection management, e.g. `Connection: close` to terminate after this exchange, or `keep-alive`.
- **Last-Modified** — Timestamp of the resource; lets the browser do conditional requests / cache validation.
- **Server** — Identifies the server software (e.g. `Server: Apache/2.4.41`). The lab's research exercise asks you to inspect this for `www.bristol.ac.uk`.

### Cookies and sessions

HTTP is **stateless** — every request stands alone, the server doesn't intrinsically remember earlier requests from the same client. Cookies (RFC 6265) bolt state on top:

```
client -> GET /             ->  server
client <- 200 OK; Set-Cookie: sid=1x33ad4
client -> GET /next; Cookie: sid=1x33ad4
```

A typical **session** flow:

```
POST /login?name=david&pass=****
200 OK; Set-Cookie: sid=1x33ad4
GET /view; Cookie: sid=1x33ad4
200 OK; (page tailored to david)
```

The server keeps a `sessions` table mapping cookie value → user. Cookies are also the basis for **tracking** when shared across third-party requests on many sites.

### HTTPS / TLS at a high level

HTTPS = HTTP carried over **TLS** (sitting at the Presentation layer, between TCP and HTTP) on TCP port 443. TLS provides:

- **Confidentiality** — symmetric encryption of the byte stream after handshake.
- **Integrity** — MACs detect tampering.
- **Authentication** — the server presents an X.509 certificate signed by a **CA** (Certificate Authority) the client trusts. The certificate binds a hostname (e.g. `bristol.ac.uk`) to a public key, so a man-in-the-middle can't impersonate the server without a valid cert.

Common TCP ports referenced in the slides: `80` HTTP, `443` TLS/HTTPS, `22` SSH, `8000` / `8080` for unofficial development servers.

### REST

**REST** = Representational State Transfer. Architectural style for web APIs that leans on HTTP being stateless:

- State of the interaction belongs in the request, not in hidden server-side per-connection state.
- Resources have stable names (URLs).
- Use the HTTP verbs as intended.

So a RESTful API prefers:

```
GET    /files/README.txt
DELETE /files/README.txt
GET    /files?name=README.txt
```

over folding everything into POSTs like `POST /files/README.txt?action=delete`.

### HTTP/1.1 vs newer versions

The chapter focuses on **HTTP/1.1** (RFC 7230 etc.), a textual protocol over a single TCP connection. The optional reading on MDN covers the evolution to HTTP/2 (binary framing, multiplexing many requests over one TCP connection, header compression) and HTTP/3 (over QUIC/UDP). The semantics — methods, status codes, headers — carry over.

## Command & tool cheat sheet

```bash
# Check whether something is already listening on port 8000 (run on the
# machine where you intend to run the SERVER).
wget localhost:8000              # should fail/time out if port is free

# More precise check: list TCP listeners and ESTABLISHED sockets.
netstat -tan
netstat -tan | grep 8000         # narrow it down

# Run a primitive HTTP server: have netcat listen on TCP 8000 and pipe
# the contents of `http-response` to whoever connects, then exit.
nc -l -p 8000 < http-response    # Linux
nc -l 8000   < http-response     # macOS variant (different flag set)

# Make a request from a client, printing server response to stdout (-O -)
# quietly (-q) but with the server's response headers (-S).
wget -q -S -O - localhost:8000

# Download a file (e.g. the http-response sample) into the current dir.
wget https://github.com/cs-uob/software-tools/raw/refs/heads/main/11-http/lab/http-response

# Build the darkhttpd C web server (under 3000 lines of C).
git clone https://github.com/emikulic/darkhttpd
cd darkhttpd
make                             # or: gcc darkhttpd.c -o darkhttpd
mkdir web
./darkhttpd web --port 8000      # serves files in ./web on port 8000
# Stop with Ctrl+C.

# Run the Spring Boot sample server in lab/server01.
cd software-tools/11-http/server01
mvn spring-boot:run              # listens on port 8000
```

The `http-response` file used with `nc`:

```
HTTP/1.1 200 OK
Content-type: text/plain
Content-length: 16
Connection: close

Hello over HTTP!
```

Note: this file **must** use CRLF line endings and end with two newlines after the body, otherwise browsers/clients won't parse it.

Vagrant port-forwarding snippet for the `Vagrantfile` (so a server inside the VM is reachable from the host):

```ruby
config.vm.network "forwarded_port", guest: 8000, host: 8000
```

Browser tooling: open DevTools with **F12**, go to the **Network** tab to see every request, response code, and the full request/response headers — usually the first place to look when something web-based misbehaves. There is also a "Disable cache" checkbox on that tab which is invaluable when developing.

## Lab walkthrough

### Lab 1 — `lab/explore.md` (Exploring HTTP)

**Goal:** play both client and server roles; understand the HTTP wire format by sending it by hand and observing it in browser DevTools.

**Steps and commands:**

1. (Vagrant only) Add `config.vm.network "forwarded_port", guest: 8000, host: 8000` to the Vagrantfile and restart the VM.
2. Verify port 8000 is free **on the server machine**:
   ```bash
   wget localhost:8000          # should time out / fail
   netstat -tan | grep 8000     # no LISTEN/ESTABLISHED on 8000
   ```
   If port 8000 is taken, switch to 8001/8002/… everywhere below.
3. Download the sample response and start a one-shot server:
   ```bash
   wget https://github.com/cs-uob/software-tools/raw/refs/heads/main/11-http/lab/http-response
   nc -l -p 8000 < http-response      # blocks until a client connects
   ```
4. From the client machine:
   ```bash
   wget -q -S -O - localhost:8000
   ```
   The server terminal shows the request `wget` sent; the client prints the response. `nc` exits after one connection.
5. Restart `nc -l -p 8000 < http-response`, open a browser at `localhost:8000` with DevTools (F12) → Network → click `localhost` → Headers. Observe the `200 OK` status line and the headers in both directions.
6. Build and run **darkhttpd**:
   ```bash
   git clone https://github.com/emikulic/darkhttpd
   cd darkhttpd
   make                # or gcc darkhttpd.c -o darkhttpd
   mkdir web
   ./darkhttpd web --port 8000
   ```
   Drop `.txt`, `.html`, image files etc. into `web/`, fetch them via `localhost:8000/FILENAME`, and watch how `Content-Type` is chosen from the file extension (see `default_extension_map` near line 320 of `darkhttpd.c`). Browsing `localhost:8000/` lists the directory.
7. Mini experiment with `Content-Type`:
   - Create `one.html5` in `web/`. The browser either downloads it or shows raw text because the server doesn't recognise the extension and sends no `Content-Type`.
   - Edit the source's `text/html` row to `" html htm html5"` (keep the leading space), recompile.
   - Rename to `two.html5`, restart server, reload. Now the page renders as HTML — because the server now sends `Content-Type: text/html`. The rename is needed so the browser's cache (keyed on URL + `Last-Modified`) doesn't hand you the previously-downloaded copy.

**What to observe / answer:**
- The exact HTTP request bytes the browser/`wget` sends (note the mandatory `Host` header).
- How status codes, `Content-Type`, `Content-Length`, `Last-Modified` appear in DevTools.
- Why `nc` is a terrible long-running server (it serves one request and quits).
- The cache pitfall: changes that don't appear may be the browser's cache; tick "Disable cache" or rename the file.

### Lab 2 — `lab/research.md` (Online research)

**Goal:** look up things HTTP/URL specs that the lectures don't cover in depth.

**Questions to answer:**

1. The **fragment** part of a URL (after `#`) — what is it for? *Identifies a sub-resource client-side (e.g. HTML element id); never sent to the server.*
2. The **`Accept`** header — what does the client use it for? *Advertises the media types the client can handle, optionally with `q=` quality weights, enabling content negotiation.*
3. The **`User-Agent`** header — what does it do, and what does *your* browser send? *Identifies the client software/version/OS; check yours via DevTools → Network → request headers, or by running `wget -S -O- localhost:8000` against your own server and reading the request `nc` printed.*
4. **Encoding spaces in URL paths** — a space is `%20`. Other reserved/special characters that need percent-encoding in paths include `?`, `#`, `%`, `&`, `/`, `:`, `@`, `+`, `<`, `>`, `"`, `{`, `}`, `|`, `\`, `^`, `~`, `[`, `]`, the back-tick, and any non-ASCII byte (each byte → `%HH`).
5. **Which web server runs `www.bristol.ac.uk`?** Check the `Server` response header (e.g. `curl -I https://www.bristol.ac.uk` or DevTools → Network → Headers). Then read up on that server software and the organisation behind it.

### Lab 3 — `lab/server.md` (A server in Java with Spring Boot)

**Goal:** stand up a real (small) web server in Java/Spring Boot, understand the file/annotation layout, and add a new endpoint.

**Steps and commands:**

1. From the cloned `software-tools` repo:
   ```bash
   cd 11-http/server01
   mvn spring-boot:run     # downloads dependencies on first run, then listens on :8000
   ```
2. Visit `localhost:8000` and `localhost:8000/html` in the browser; watch DevTools headers and the Spring log lines per request.

**Project layout to know:**

- `pom.xml` — Maven config, declares this as a Spring Boot project named `softwaretools.server01`.
- `src/main/resources/application.properties` — Spring config; sets the listen port to 8000 (Spring's default would be 8080).
- `src/main/resources/<page>.html` — static HTML asset to serve.
- `src/main/java/.../Server01Application.java` — entry point, marked `@SpringBootApplication`.
- `src/main/java/.../Controller.java` — the interesting one (the **C** in MVC). Annotations:
  - `@RestController` — class contains HTTP-handling methods (REST-friendly defaults).
  - `@Autowired` on a `ResourceLoader` field — Spring injects it; lets the controller load files from `src/main/resources` via the classpath.
  - `@GetMapping("/path")` — bind a method to GET requests for that path. Companions exist for the other verbs (`@PostMapping`, `@PutMapping`, …).
- `mainPage()` (handles `/`) builds a `ResponseEntity<>(body, headers, HttpStatus.OK)` — explicit body, headers (e.g. `Content-Type`), and 200 status.
- `htmlPage()` (handles `/html`) demonstrates the **builder pattern**: load the HTML resource off the classpath, then `ResponseEntity.ok().header(...).body(...)`.

**Exercise to complete:**
- Add a method that responds to `GET /bad` with HTTP `404 NOT FOUND` and a short string body. Restart `mvn spring-boot:run` and verify in the browser/DevTools that the response status is `404` and the body matches. Sketch:
  ```java
  @GetMapping("/bad")
  public ResponseEntity<String> badPage() {
      return ResponseEntity
          .status(HttpStatus.NOT_FOUND)
          .body("That resource was not found.");
  }
  ```

## Pitfalls & emphasis

- **CRLF line endings matter.** Any HTTP message you write by hand (e.g. the `http-response` file) must use `\r\n`, not bare `\n`, and end with the right number of newlines, or clients will hang or reject it.
- **Run `wget localhost:8000` on the server machine before starting `nc`.** If port 8000 is already in use, every later step will misbehave. The lab notes flag this as the single biggest source of student confusion.
- **`nc` serves exactly one client and exits.** It is a debugging convenience, not a real server — restart it between requests.
- **macOS vs Linux `nc` flags differ.** Use `nc -l 8000 < http-response` on macOS rather than `-l -p 8000`.
- **`Content-Type` is the browser's first priority.** A misconfigured type can silently break a page (HTML rendered as plain text, scripts/stylesheets ignored, files downloaded instead of displayed).
- **Caching can mask changes during development.** If a server-side edit doesn't appear, suspect the browser cache: tick *Disable cache* in DevTools' Network tab, rename the file, or hard-reload. The `Last-Modified` header is what the browser keys off.
- **Vagrant port forwarding is required** if you want to run the server inside the VM and the browser on the host; otherwise `localhost:8000` from the host won't reach the VM.
- **The `Host` header is mandatory in HTTP/1.1.** Forgetting it (in a hand-typed request) gives a `400 Bad Request`.
- **HTTP is stateless.** Anything resembling a session has to be reconstructed from cookies (or tokens) on every request.
- **The fragment is never sent to the server.** Don't try to read `#section` server-side; it stays in the browser.
- **Use HTTP verbs as intended (REST).** Don't pile every action onto `POST … ?action=delete` when `DELETE` exists; servers, caches and intermediaries rely on the verb's semantics (idempotency, safety).
- **TLS provides confidentiality, integrity, and authentication, in that order of common assumption** — but only if certificate validation is honoured. The CA chain is what makes "you really are talking to bristol.ac.uk" trustworthy.
- **Read RFC 7230 sections 2.1, 2.2, 2.7 and 3** — examinable; the message grammar in §3 is what the rest of the chapter is grounded in.
