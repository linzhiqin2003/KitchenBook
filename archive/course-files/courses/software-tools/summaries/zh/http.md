# 第 11 章 — HTTP

## 章节概览

这一章是 Software Tools 课程下半学期（TB2）的开门话题，从 Web 最底层的应用层协议——HTTP——切入，把"网"这件事讲清楚。具体覆盖：什么叫协议、HTTP 在整个 Internet 协议栈里处于什么位置、URL/URI 是怎么拼出来的、请求/响应的来回是什么样、HTTP 的方法、状态码的几个家族、几个绕不开的 header、内容类型、cookie 与 session、REST 的设计理念，最后再从高处俯瞰一下 TLS/HTTPS。配套的 lab 有三个练习：用 `nc` 和 `wget`（再加上 C 写的 `darkhttpd`）亲手玩一把 HTTP；查阅几个关于 URL 和 header 的细节；最后用 Java/Spring Boot 自己写一个简单的服务器。必读材料是 RFC 7230 的 2.1、2.2、2.7 和 3 节。

## 核心知识

### Internet 和 Web 不是一回事

**Internet** 指的是那张全球互联的计算机网络——路由器、链路、主机连成一片，负责把字节从一台机器搬到另一台。而 **Web** 只是跑在 Internet 之上的**一种**应用，它由三件东西定义：HTTP（协议）、URL（地址方案）、HTML（文档格式）。HTTP 是 Tim Berners-Lee 1989 年在 CERN 搞出来的；今天还在大规模使用的版本是 HTTP/1.1，对应的规范是 RFC 7230–7235。

HTTP 是一个**应用层**协议，坐在协议栈最顶上：

```
7. Application   (HTTP)               <- you are here
6. Presentation  (TLS)
5. Session       (SOCKS)
4. Transport     (TCP, UDP)
3. Network       (IP)
2. Data Link     (MAC / Ethernet frames)
1. Physical      (Bluetooth, Ethernet PHY)
```

具体来说，一条 HTTP 消息装在 **TCP** 流里跑（明文 HTTP 用 80 端口，HTTPS 用 443），TCP 再被装进 **IP** 包（比如发往 `137.222.0.38`），IP 包一跳一跳穿过物理链路。TCP 负责保证有序、可靠：每个 segment 带 sequence number 和 checksum，对方要回 ACK（比如 ACK 101），失序或丢失的会重组、重传。IP 只管尽力而为地把包从源地址路由到目标地址，不保证什么。

**协议**的本质就是一份"约定好的合作脚本"。最简单的例子：

> Client: "Give me block #200" — Server: "Here you go: 0A 2F EE …"
> Client: "Give me block #45000" — Server: "Sorry, I couldn't find that block."

HTTP 也是这种 client–server、请求–响应的样子，只是在数据之外多堆了一层丰富的**元信息**：请求/响应的 header，加上一个数字状态码。元信息是协议的一部分；真正的数据（比如那篇 hypertext 文档）跟协议是解耦的——HTML 页面并不一定非得通过 HTTP 才能送到。

服务器骨子里就是一个循环：

```c
while (1) {
    req  = read();
    resp = serve(req);
    write(resp);
}
```

### URL 由哪几块拼起来

**URL**（Uniform Resource Locator）是 **URI**（Uniform Resource Identifier，RFC 3986）的一种，用来给某个资源起名字。完整的通用形态长这样：

```
scheme://userinfo@host:port/path?query#fragment
```

每一段是干什么的：

- **scheme**：协议或命名空间。常见的有 `http`、`https`、`ftp`、`ldap`、`mailto`、`news`、`tel`、`telnet`、`urn`。RFC 3986 给的几个例子：`ftp://ftp.is.co.za/rfc/rfc1808.txt`、`mailto:John.Doe@example.com`、`tel:+1-816-555-1212`、`urn:oasis:names:specification:docbook:dtd:xml:4.1.2`。
- **userinfo**（可选）：`user:password@` 这种凭据。明文 HTTP 里几乎不用，因为不安全。
- **host**：服务器地址。可以是 DNS 名（`bristol.ac.uk`），也可以是 IP 字面量（IPv6 写成 `[2001:db8::7]`）。
- **port**（可选）：TCP 端口。`http` 默认 80，`https` 默认 443，开发服务器常用 8000 或 8080。
- **path**：资源在服务器上的位置，比如 `/`、`/files/index.html`、`/user/george/`。它对应 HTTP 请求里的 `request-target`。
- **query**：以 `?` 起头，一串 `name=value` 用 `&` 拼起来，比如 `?name=welcome&action=view`。同一个 path 配不同的 query 可以返回不同的内容。
- **fragment**：以 `#` 起头，指向资源内部的某一小块（比如 HTML 里某个 `id` 的元素）。**关键点**：fragment **从不**发给服务器，浏览器拿到后自己在客户端处理，用来滚动到锚点。

path 或 query 里如果出现空格或者其他"reserved"/非 ASCII 字符，就要做 **percent-encoding**：空格变 `%20`（在 form-encoded 的 query 里也可以写成 `+`），而 `?`、`#`、`&`、`/`、`:`、`@`、`%`、空格、`+` 以及任何非 ASCII 字节，都得编码成 `%HH` 的形式（`HH` 是这个字节的十六进制值）。

### 请求/响应的来回是什么样

按照 RFC 7230 的定义，一条 HTTP 消息长这样：

```
HTTP-message = start-line
               *( header-field CRLF )
               CRLF
               [ message-body ]
```

- `start-line` 在请求里叫 **request-line**，在响应里叫 **status-line**。
- 中间是零到多个 `field-name: field-value` 的 header。
- 一个空行（光秃秃的 `CRLF`）把 header 和可选的 body 隔开。
- 所有的行结束符必须是 `CRLF`（`\r\n`）——只用 Unix 风格的 `\n` 协议就不认。

**request-line** 的格式：

```
method SP request-target SP HTTP-version CRLF
```

请求示例：

```http
GET /index.html HTTP/1.1
Host: www.bristol.ac.uk
Connection: close
```

**status-line** 的格式：

```
HTTP-version SP status-code SP reason-phrase CRLF
```

响应示例：

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 1009

<!DOCTYPE html>
<html lang="en">
...
```

### HTTP 的方法

动词告诉服务器：你要拿这个资源**干嘛**。

- **GET** — 取回目标资源的副本。安全且 idempotent，不应该带 body。
- **POST** — 把 payload 提交到目标资源（提表单、创建子资源、触发某个动作）。不 idempotent。
- **PUT** — 用请求的 payload 把目标资源**整个**替换掉。Idempotent。
- **DELETE** — 删掉目标资源。Idempotent。
- **HEAD** — 跟 GET 一样，但服务器只回 header、不带 body。用来便宜地拿元信息（比如 `Content-Length`、`Last-Modified`）。
- **OPTIONS** — 问服务器：这个资源支持哪些方法/特性？常用于 CORS 预检。
- **PATCH** — 对资源做**部分**修改（区别于 PUT 的整体替换）。

实际工程里，很多服务器懒得理 `PUT`/`DELETE`，统一拿 `POST` 套自定义语义，比如 `POST /files/README.txt?action=delete`。

### 状态码的几个家族

第一位数字定调子：

- **1xx — informational**：暂态响应，处理还在继续。例：`100 Continue`（服务器收到了 header，客户端可以接着把 body 发过来）。
- **2xx — success**：请求收到了、看懂了、接受了。例：`200 OK`、`201 Created`（POST/PUT 创建了新资源）、`204 No Content`（成功但没 body）。
- **3xx — redirection**：还得请客户端再做点事。例：`301 Moved Permanently`、`302 Found`、`304 Not Modified`（缓存还有效）。新地址放在 `Location` header 里。
- **4xx — client error**：你这请求有毛病。例：`400 Bad Request`、`401 Unauthorized`（要认证）、`403 Forbidden`（认了证也不让进）、`404 Not Found`、`405 Method Not Allowed`、`429 Too Many Requests`。
- **5xx — server error**：请求看着没问题，但服务器自己崩了。例：`500 Internal Server Error`、`502 Bad Gateway`、`503 Service Unavailable`、`504 Gateway Timeout`。

### 几个关键 header

header 装的是元信息。名字大小写不敏感。

- **Host** — 目标主机（可选带端口）。HTTP/1.1 里**必填**；它让一个 IP 上能跑多个 virtual host。
- **Content-Type** — body 的 MIME 类型，比如 `text/html; charset=UTF-8`、`text/plain`、`image/jpeg`、`application/pdf`、`video/mp4`、`application/json`。对浏览器来说，这是它决定怎么解读 body 时的**第一优先级**——一个 `.html` 文件如果被服务器声明成 `Content-Type: text/plain`，浏览器就把它当原始文本显示，不会渲染。
- **Content-Length** — body 的字节数。让接收方知道消息在哪里结束。
- **Accept** — 客户端发的，告诉服务器自己能消化哪些 content type（比如 `Accept: text/html, application/json;q=0.9`）。这是 content negotiation 的依据。
- **User-Agent** — 标识客户端软件（浏览器、版本、操作系统）。服务器拿它做统计、特性探测、屏蔽爬虫等。
- **Authorization** — 装凭据，比如 `Authorization: Basic dXNlcjpwYXNz` 或 `Authorization: Bearer <token>`。
- **Set-Cookie** — 服务器用它在客户端**种**一个 cookie：`Set-Cookie: sid=1x33ad4; HttpOnly; Secure`。
- **Cookie** — 客户端在后续请求里把已经存下来的、属于同一 origin 的 cookie 带回去。
- **Cache-Control** — 缓存指令（`no-cache`、`max-age=3600`、`public`、`private`）。
- **Location** — 用在 3xx 跳转里（以及 `201 Created`），给出新的/刚创建的 URL。
- **Connection** — 连接管理，比如 `Connection: close` 表示这次交换完就断，或者 `keep-alive` 留着复用。
- **Last-Modified** — 资源的时间戳，让浏览器能做条件请求/缓存校验。
- **Server** — 标识服务器软件（比如 `Server: Apache/2.4.41`）。lab 里那道 research 题就让你查 `www.bristol.ac.uk` 的这个值。

### Cookie 和 session

HTTP 是**无状态**的——每个请求各管各的，服务器天然不会记得这个客户端之前来过。Cookie（RFC 6265）就是给它硬贴上一层状态：

```
client -> GET /             ->  server
client <- 200 OK; Set-Cookie: sid=1x33ad4
client -> GET /next; Cookie: sid=1x33ad4
```

典型的 **session** 流程：

```
POST /login?name=david&pass=****
200 OK; Set-Cookie: sid=1x33ad4
GET /view; Cookie: sid=1x33ad4
200 OK; (page tailored to david)
```

服务器自己存一张 `sessions` 表，把 cookie 值映射回用户。Cookie 同时也是各种**追踪**的根基——只要这个 cookie 在很多站点的第三方请求里被共享，就能跨站把你串起来。

### 高处看一眼 HTTPS / TLS

HTTPS = HTTP 跑在 **TLS** 之上（TLS 在 Presentation 层，夹在 TCP 和 HTTP 中间），TCP 端口 443。TLS 提供三件事：

- **Confidentiality** — 握手之后，对字节流做对称加密。
- **Integrity** — 用 MAC 检测篡改。
- **Authentication** — 服务器出示一张 X.509 certificate，由客户端信任的某个 **CA**（Certificate Authority）签名。这张 cert 把一个 hostname（比如 `bristol.ac.uk`）和一个 public key 绑在一起，所以中间人没有合法 cert 就没法假冒服务器。

幻灯片里出现过的几个常见 TCP 端口：`80` HTTP、`443` TLS/HTTPS、`22` SSH、`8000` 和 `8080` 是非官方的开发服务器常用端口。

### REST

**REST** = Representational State Transfer。是给 web API 用的一种架构风格，立足点就是 HTTP 的无状态：

- 交互的状态应该装在请求里，而不是藏在服务器端按连接保留的隐式状态。
- 资源要有稳定的名字（URL）。
- HTTP 的动词该怎么用就怎么用。

所以一个 RESTful 的 API 倾向于这样写：

```
GET    /files/README.txt
DELETE /files/README.txt
GET    /files?name=README.txt
```

而不是把所有动作都塞进 POST 里，比如 `POST /files/README.txt?action=delete`。

### HTTP/1.1 和后续版本

这一章主要讲 **HTTP/1.1**（RFC 7230 等），它是基于单条 TCP 连接的文本协议。MDN 上的选读材料讲了往后的演化：HTTP/2（二进制 framing、在一条 TCP 连接上 multiplex 多个请求、header 压缩）和 HTTP/3（跑在 QUIC/UDP 之上）。但语义层面——方法、状态码、header——是一脉相承的。

## 命令与工具速查

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

配合 `nc` 用的那份 `http-response` 文件：

```
HTTP/1.1 200 OK
Content-type: text/plain
Content-length: 16
Connection: close

Hello over HTTP!
```

注意：这个文件**必须**用 CRLF 行结束符，body 后面还要留两个换行，否则浏览器/客户端解析不了。

如果是用 Vagrant 跑虚拟机，需要在 `Vagrantfile` 里加端口转发，让宿主机能访问到 VM 里的服务器：

```ruby
config.vm.network "forwarded_port", guest: 8000, host: 8000
```

浏览器侧的工具：按 **F12** 打开 DevTools，切到 **Network** 标签页，每一个请求、响应码、完整的请求/响应 header 都看得到——网页层面的怪事，第一时间往这里查就对了。这个标签页上还有个 "Disable cache" 复选框，开发的时候简直救命。

## Lab 实操

### Lab 1 — `lab/explore.md`（亲手玩 HTTP）

**目标**：客户端、服务器两边都扮演一遍；通过手写 HTTP 报文 + 在浏览器 DevTools 里观察，把 wire format 真正搞懂。

**步骤和命令**：

1. （只针对 Vagrant 用户）在 `Vagrantfile` 里加上 `config.vm.network "forwarded_port", guest: 8000, host: 8000`，重启 VM。
2. **在打算跑服务器的那台机器上**确认 8000 端口是空的：
   ```bash
   wget localhost:8000          # should time out / fail
   netstat -tan | grep 8000     # no LISTEN/ESTABLISHED on 8000
   ```
   如果 8000 被占了，下面所有步骤都换成 8001/8002/…。
3. 把示例响应下载下来，启一个一次性的服务器：
   ```bash
   wget https://github.com/cs-uob/software-tools/raw/refs/heads/main/11-http/lab/http-response
   nc -l -p 8000 < http-response      # blocks until a client connects
   ```
4. 在客户端那边：
   ```bash
   wget -q -S -O - localhost:8000
   ```
   服务器那个终端里会打印出 `wget` 发过来的请求；客户端这边打印出响应。`nc` 处理完一次连接就退出。
5. 重新跑 `nc -l -p 8000 < http-response`，浏览器打开 `localhost:8000`，开 DevTools（F12）→ Network → 点击 `localhost` → Headers。看一下 `200 OK` 这个 status line，以及来回两个方向上的 header 都长什么样。
6. 把 **darkhttpd** 编出来跑：
   ```bash
   git clone https://github.com/emikulic/darkhttpd
   cd darkhttpd
   make                # or gcc darkhttpd.c -o darkhttpd
   mkdir web
   ./darkhttpd web --port 8000
   ```
   往 `web/` 里丢 `.txt`、`.html`、图片之类的文件，再用 `localhost:8000/FILENAME` 取回来，看服务器是怎么从文件后缀挑出 `Content-Type` 的（参考 `darkhttpd.c` 大约 320 行附近的 `default_extension_map`）。访问 `localhost:8000/` 会列出目录。
7. 围绕 `Content-Type` 做一个小实验：
   - 在 `web/` 里建一个 `one.html5`。浏览器要么直接下载它，要么显示原始文本——因为服务器不认这个后缀，所以根本没发 `Content-Type`。
   - 把源码里 `text/html` 那一行改成 `" html htm html5"`（开头那个空格要保留），重新编译。
   - 改名成 `two.html5`，重启服务器，刷新。这下页面就按 HTML 渲染出来了——因为现在服务器会发 `Content-Type: text/html`。之所以要改名，是因为浏览器缓存的 key 是 URL + `Last-Modified`，不改名你拿到的还是之前下载过的那份。

**要注意/要回答的**：
- 浏览器或者 `wget` 实际发出去的 HTTP 请求字节是什么样（注意必填的 `Host` header）。
- 状态码、`Content-Type`、`Content-Length`、`Last-Modified` 在 DevTools 里怎么显示。
- 为什么 `nc` 不能当真正的长跑服务器用——它处理完一次就退出。
- 缓存这个坑：你改了东西没看到生效，多半是浏览器缓存——勾上 "Disable cache"，或者把文件改个名。

### Lab 2 — `lab/research.md`（线上查资料）

**目标**：补几个课堂上没细讲的 HTTP/URL 细节。

**要回答的几个问题**：

1. URL 里的 **fragment** 部分（`#` 之后那一截）——干嘛用的？*在客户端标识资源的某个子部分（比如 HTML 里某个 element 的 id）；从来不会发给服务器。*
2. **`Accept`** header——客户端拿它干嘛？*告诉服务器自己能处理哪些 media type，可以带 `q=` 质量权重，用来做 content negotiation。*
3. **`User-Agent`** header——它是干啥的？你**自己**的浏览器发的是什么？*标识客户端软件/版本/操作系统；自己的可以从 DevTools → Network → request headers 看，或者用 `wget -S -O- localhost:8000` 打自己的服务器，从 `nc` 打印出来的请求里看。*
4. URL path 里**怎么编码空格**——空格是 `%20`。其他在 path 里需要 percent-encoding 的 reserved/特殊字符还有：`?`、`#`、`%`、`&`、`/`、`:`、`@`、`+`、`<`、`>`、`"`、`{`、`}`、`|`、`\`、`^`、`~`、`[`、`]`、反引号，以及任何非 ASCII 字节（每个字节一个 `%HH`）。
5. **`www.bristol.ac.uk` 跑的是哪个 web server？** 看响应里的 `Server` header（比如 `curl -I https://www.bristol.ac.uk`，或者 DevTools → Network → Headers）。然后顺便去了解一下这个服务器软件、以及它背后的组织。

### Lab 3 — `lab/server.md`（用 Java + Spring Boot 写一个服务器）

**目标**：用 Java/Spring Boot 把一个真正的（虽然小）web server 跑起来，理清楚文件和注解的布局，然后加一个新的 endpoint。

**步骤和命令**：

1. 在 clone 下来的 `software-tools` 仓库里：
   ```bash
   cd 11-http/server01
   mvn spring-boot:run     # downloads dependencies on first run, then listens on :8000
   ```
2. 浏览器访问 `localhost:8000` 和 `localhost:8000/html`，看 DevTools 里的 header，以及 Spring 每次请求打的日志行。

**要弄懂的项目布局**：

- `pom.xml` — Maven 配置，把这个项目声明成名字叫 `softwaretools.server01` 的 Spring Boot 项目。
- `src/main/resources/application.properties` — Spring 配置；把监听端口设成 8000（Spring 默认是 8080）。
- `src/main/resources/<page>.html` — 拿来直接服务的静态 HTML 文件。
- `src/main/java/.../Server01Application.java` — 入口类，标了 `@SpringBootApplication`。
- `src/main/java/.../Controller.java` — 真正有意思的就是这个（MVC 里的 **C**）。注解：
  - `@RestController` — 标在类上，表示里面是 HTTP 处理方法（默认行为偏 REST）。
  - `@Autowired` 标在 `ResourceLoader` 字段上 — Spring 会注入它，让 controller 能通过 classpath 从 `src/main/resources` 加载文件。
  - `@GetMapping("/path")` — 把方法绑到对应 path 的 GET 请求上。其他动词也有对应的（`@PostMapping`、`@PutMapping`……）。
- `mainPage()`（处理 `/`）构造的是 `ResponseEntity<>(body, headers, HttpStatus.OK)`——显式给出 body、header（比如 `Content-Type`）和 200 状态。
- `htmlPage()`（处理 `/html`）演示了 **builder 模式**：从 classpath 加载 HTML 资源，然后 `ResponseEntity.ok().header(...).body(...)` 链式拼出来。

**要做的练习**：
- 加一个方法：响应 `GET /bad`，返回 HTTP `404 NOT FOUND` 加一个简短的字符串 body。重启 `mvn spring-boot:run`，在浏览器/DevTools 里确认状态是 `404`、body 也对得上。骨架：
  ```java
  @GetMapping("/bad")
  public ResponseEntity<String> badPage() {
      return ResponseEntity
          .status(HttpStatus.NOT_FOUND)
          .body("That resource was not found.");
  }
  ```

## 易错点与重点

- **CRLF 行结束符是认真的。** 任何你手写的 HTTP 报文（比如 `http-response` 那个文件）必须用 `\r\n`，不能用裸 `\n`，结尾的换行数也要对，否则客户端要么挂着不动要么直接拒掉。
- **跑 `nc` 之前先在服务器那台机器上 `wget localhost:8000` 探一下。** 如果 8000 已经被占用，后面每一步都会出岔子。lab 笔记把这条标成了学生最常掉进去的坑。
- **`nc` 只服务一个客户端就退出。** 它是个调试用的小玩意儿，不是真服务器——每次请求之间得重新拉起来。
- **macOS 和 Linux 的 `nc` flag 不一样。** macOS 上写 `nc -l 8000 < http-response`，不要写 `-l -p 8000`。
- **`Content-Type` 是浏览器的第一优先级。** 类型配错了能悄无声息地把页面整坏（HTML 显示成纯文本、script/stylesheet 被忽略、文件被下载而不是显示出来）。
- **开发期间，缓存会让你看不到改动。** 服务器明明改了你却没看到效果，先怀疑浏览器缓存：勾上 DevTools Network 标签里的 *Disable cache*，或者把文件改个名，或者强制刷新。浏览器走的是 `Last-Modified` 这个 key。
- **Vagrant 端口转发是必须配的**，如果你想把服务器跑在 VM 里、浏览器开在宿主机上；不配的话宿主机的 `localhost:8000` 根本到不了 VM。
- **HTTP/1.1 里 `Host` header 是必填的。** 手敲请求时漏了这个，就是 `400 Bad Request`。
- **HTTP 是无状态的。** 任何看上去像 session 的东西，每次请求都得靠 cookie（或 token）重新拼出来。
- **fragment 永远不会发给服务器。** 别想着在服务端读 `#section`，它就留在浏览器里。
- **HTTP 动词该怎么用就怎么用（REST）。** 别动不动就 `POST … ?action=delete`，明明有 `DELETE`。服务器、缓存、各种中间设备都依赖动词的语义（idempotency、safety）来做事。
- **TLS 提供 confidentiality、integrity、authentication，按照大家通常默认的优先级排**——但前提是 certificate 校验真的执行了。CA 链才是"你确实在跟 bristol.ac.uk 说话"这件事可信的根基。
- **去读 RFC 7230 的 2.1、2.2、2.7 和 3 节**——会考；这一章讲的所有东西都建立在 §3 那份消息 grammar 之上。
