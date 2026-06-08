# 第 19 章 — 网络协议

> 主讲：Jo Hallett。这一讲故意带几分玩世不恭的味道：它要传递的核心想法是
> "互联网协议不过就是 sockets 上跑的纯文本，由 IETF 的 RFC 来规定"，
> 然后带你走一遍 socket 编程和 `inetd`，再来一段"那个没成真的 web"的考古
> 之旅——Finger 与 Gopher——最后落到 smolweb 的安利（Gemini 协议）。Lab
> 部分让你亲手实现 Finger。

## 章节概览

整组幻灯片其实只回答了一个问题：**"那 HTTP 到底*是*个啥？"**——并以此为
切口，把整个应用层协议的盖子掀开给你看。

论证脉络是这样的：

1. 协议（HTTP、HTCPCP、Finger、Gopher、WebFinger）说穿了就是**写在 IETF
   RFC 里的纯文本对话**。只要你能读懂 RFC、能往 TCP socket 上写字节，你
   就能"说"这个协议。
2. 但要真把字节*发*出去，你需要一个 **socket**——POSIX 提供的那个抽象，
   长得像文件描述符，但是数据走网络。幻灯片把 C 语言的客户端 + 服务器
   骨架完整走了一遍（`getaddrinfo`、`socket`、`connect`、`bind`、`listen`、
   `accept`、`send`、`recv`）。
3. 大多数时候你并不想从头写这套骨架。**`inetd`**（"互联网超级服务器"）会替你
   接管端口监听，把 socket 直接挂在你程序的 stdin/stdout 上——于是 Finger
   或 Gopher 的服务器可以是一个 shell 脚本。
4. 历史插曲：在 HTTP+HTML+社交媒体一统江湖之前，web 是一片由更小的协议
   拼成的马赛克。其中两个——**Finger**（RFC 1288）和 **Gopher**（RFC
   1436）——会被完整演示一遍，外加它们各自的现代后继者：**WebFinger**
   （RFC 7033，被 Mastodon/ActivityPub 所用）和 **Gemini**（smolweb）。
5. Lab 里你要把 Finger 实现一遍——客户端和服务器都写。

这一章*不*涉及：TLS、DNS 内部机制、OSI 分层、抓包分析、SSH、邮件协议、
PKI。这些幻灯片里一个都没有。

## 核心知识

### IETF 与 RFC——协议的栖息地

- **互联网工程任务组（Internet Engineering Task Force, IETF）**是互联网的
  标准化组织。非营利性质，任何人都能通过参与的方式加入，但**公司不能以
  公司的名义加入**——只接受个人。
- 决策机制叫做 **rough consensus**（大致共识）和 **running code**（能跑的
  代码）。
- 他们发布的文档叫 **Requests for Comments（RFC）**——纯文本（用一种"看
  起来有点凑合"的等宽字体排版），描述某个协议应当怎么做。
- 文化上：对变化偏保守，偶尔也喜欢恶搞一下。

走过的例子：**RFC 1945 — HTTP/1.0**（Berners-Lee、Fielding、Frystyk，
1996 年 5 月）。注意连 IESG 自己都在开篇打了个预防针：他们预期这份信息
性备忘录很快会被一份走标准化轨道的文档替代掉。

### RFC 也可以是个玩笑——HTCPCP（RFC 2324）

Hyper Text Coffee Pot Control Protocol，1998 年。表面上是个愚人节玩笑；
但放到今天这个智能水壶遍地走的时代再回头看，竟有几分先见之明。

- 构建**在 HTTP 之上**，添了新方法、新 header、新返回码。
- 新的 URI scheme：`coffee:`
- 新方法：**`BREW`**（以及 `WHEN`，用法就像别人给你倒牛奶时你说的那个
  "好了"）。
- 新 header：**`Accept-Additions`**，里面带 `addition-type` 枚举值——
  奶类（`Cream`、`Half-and-half`、`Whole-milk`、`Part-Skim`、`Skim`、
  `Non-Dairy`），糖浆（`Vanilla`、`Almond`、`Raspberry`、`Chocolate`），
  酒（`Whisky`、`Rum`、`Kahlua`、`Aquavit`），等等。
- 新状态码：**`418 I'm a teapot`**——当你试图用茶壶煮咖啡时返回。

启示是：一份 RFC 不过是一份君子协议。读懂它你就会说这个协议；实现它别
人就能跟你说话。

### Sockets——POSIX 风格的字节传输方式

socket 看上去就像一个文件描述符，只不过读写都走网络。你用文件那一套
原语（`read`/`write`）也能用，但前面要先做一段"建立连接"的动作，而且
通常用 `send`/`recv` 替代。

**整体流程：**

| 步骤 | 客户端 | 服务器 |
|------|--------|--------|
| 1 | 准备连接信息 (`hints`) | 准备连接信息 (`AI_PASSIVE`) |
| 2 | `getaddrinfo`（走 DNS 解析） | `getaddrinfo`（自己的 IP） |
| 3 | `socket()` | `socket()`、`setsockopt(SO_REUSEADDR)` |
| 4 | `connect()` | `bind()` 然后 `listen()` |
| 5 | `send()` / `recv()` | `accept()`、`fork()`，然后 `send()` / `recv()` |
| 6 | `close()` | 每个子进程各自 `close(new_fd)` |

#### 客户端骨架（C，未做错误处理）

```c
struct addrinfo *servinfo, hints;
memset(&hints, 0, sizeof hints);
hints.ai_family   = AF_UNSPEC;   // IPv4 或 IPv6 都行
hints.ai_socktype = SOCK_STREAM; // TCP
getaddrinfo("bristol.ac.uk", "80", &hints, &servinfo);

int sockfd;
for (; servinfo != NULL; servinfo = servinfo->ai_next) {
    sockfd = socket(servinfo->ai_family,
                    servinfo->ai_socktype,
                    servinfo->ai_protocol);
    connect(sockfd, servinfo->ai_addr, servinfo->ai_addrlen);
    break;
}

char buf[BUFSIZ];
send(sockfd, "GET /\n\n", 7, 0);
int n = recv(sockfd, buf, BUFSIZ, 0);
for (int i = 0; i < n; i++) putchar(buf[i]);
```

真实的 `getaddrinfo` 会返回一个**候选项链表**——IPv4 和 IPv6 各有、多
块网卡各有，等等。上面的循环就是依次试过去。

`bristol.ac.uk:80` 给出的样例响应：

```
HTTP/1.0 302 Moved Temporarily
Location: https:///
Server: BigIP
Connection: close
Content-Length: 0
```

#### 服务器骨架（C，未做错误处理）

```c
struct addrinfo hints, *servinfo;
memset(&hints, 0, sizeof hints);
hints.ai_family   = AF_UNSPEC;
hints.ai_socktype = SOCK_STREAM;
hints.ai_flags    = AI_PASSIVE;  // 监听本机 IP
getaddrinfo(NULL, "8080", &hints, &servinfo);

int sockfd, yes = 1;
for (; servinfo != NULL; servinfo = servinfo->ai_next) {
    sockfd = socket(servinfo->ai_family,
                    servinfo->ai_socktype,
                    servinfo->ai_protocol);
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int));
    bind(sockfd, servinfo->ai_addr, servinfo->ai_addrlen);
    break;
}
listen(sockfd, 10);   // backlog 为 10

int new_fd;
struct sockaddr_storage their_addr;
while (1) {
    new_fd = accept(sockfd, &their_addr, sizeof their_addr);
    if (!fork()) {
        send(new_fd, "PING", 4, 0);
    }
    close(new_fd);
}
```

每一步为什么这么写：

- `setsockopt(..., SO_REUSEADDR, ...)`——避免服务器重启时报"port in use"。
- `bind`——把程序挂到这个 socket 上，但还没指定要跟谁通信。
- `listen`——开始把进来的连接排队，队列长度 10。
- `accept`——从队列里拿一个出来，返回一个新的 fd 用来跟它说话。
- `fork`——让子进程去处理这个连接，父进程能继续 accept 新的。

Jo 特别提醒了几点要小心：

- "千万别真的照这个写网络代码！"——错误处理全都被砍掉了，再加上 fork
  出来的死进程不收尸的话，进程表会被填满。
- 真正要参考的资料：**Beej's Guide to Network Programming**——
  [https://beej.us/guide/bgnet/](https://beej.us/guide/bgnet/)——每次需要
  写网络代码都强烈推荐看一眼。
- 现代语言里都有更高层的封装；`send`/`recv` 是 C 这一层的下限。再往下
  一层就是内核里的 TCP/IP 协议栈了。

### Inetd——把样板代码抽象掉

引出 `inetd` 的问题是：如果一个服务器要做的事情就是"在某个端口上听着，
把每个进来的连接交给某个会读 stdin、写 stdout 的服务程序处理"，那么这
个服务程序为什么还要知道 socket 是个什么东西？

**`inetd`**（"Internet Services Daemon"）：

- 一个统一的超级服务，替你在好多端口上监听。
- 每来一个连接，它就把对应的程序拉起来，并把 **stdin 和 stdout 直接连
  到 socket 上**。
- 1978 年首次出现。如今基本被遗忘：主要是因为它攻击面又大又显眼，被
  认为不够安全。
- 现代等价物：Linux 上的 `xinetd`、`systemd` 里类似功能的部分、macOS
  上的 `launchd` 也有类似机制。它们默认大多什么都不开——具体要查你自
  己系统的手册。

Jo 给的例子，来自一台 OpenBSD 服务器，用的是经典的 `/etc/inetd.conf`
格式：

```
# Service  Kind        Conn    Options  User           Process
finger     stream tcp  nowait           _fingerd       /usr/libexec/fingerd
finger     stream tcp6 nowait           _fingerd       /usr/libexec/fingerd
gopher     stream tcp  nowait           _gophernicus   /usr/local/libexec/in.gophernicus
```

- `nowait`——允许同时跑多个实例。
- 每个服务都以一个**独立的、专门的低权限用户**运行（`_fingerd`、
  `_gophernicus`）。这就是权限分离。
- 程序按惯例放在 `/libexec/` 下而不是 `/bin/`——它们不是给人手动执行
  的。
- `/etc/services` 把符号名映射到端口：

```
gopher  70/tcp
gopher  70/udp
finger  79/tcp
```

因为 stdin/stdout 已经替你接到 socket 上了，**任何能读 stdin、写 stdout
的程序都能拿来当服务**——Jo 自己用的 `fingerd` 就是字面意义上的一个
shell 脚本。换成 C 用 `scanf`/`printf`、Python 用 `read`/`print` 也都行。

> "我可以在一台便宜的 VPS 上欢欢喜喜地跑我的 Gopherhole 和 Finger 服务器。"

### 顺带说说 OpenBSD

Jo 是在 OpenBSD 上做这些服务器演示的。她对它的评价是：简单到有点慢、
有点烦人，但好调试、基本能跑、攻击面小，所以"姑且算是有点安全的"。

### 那个没成真的 web——Finger（RFC 1288）

起源故事：早期 UNIX 时代，你是从一台哑终端登入一台共享的大型机的。
互联网出现之前，全球大概也就十来台联网的电脑。如果有谁在猛吃系统资
源，或者从外面拨号进来了，能**把手指头戳到他身上、查清楚他是谁**就
很有用——这就是这个协议名字的由来，也解释了为什么用户注册时要填真
名、电话、办公室房间号。

线协议规则：

- 发一条 TCP 消息到 **79 端口**。
- 请求体的几种形式（带可选的详细程度 flag）：
  - `username`——查这个本地用户。
  - `@host`——列出该主机上所有用户。
  - `username@host`——类似 SSH 里的跳板：让该主机把 finger 请求转发
    到别处。
- 服务器以纯文本形式想回什么回什么。

样例响应（`finger fishfinger@tilde.club`）：

```
[tilde.club]
Login: fishfinger
Name:
Directory: /home/fishfinger
Shell: /bin/bash
Login sessions:
  fishfing  15:22  12:07m  0.00s  0.14s sshd-session: fishfinger [priv]
  fishfing  15:22  12:07m  0.00s  0.26s /usr/lib/systemd/systemd --user
No mail found.
Plan:
  Teaching my students about the old ways on the web!
```

响应里展示的那个 **`.plan`** 文件（放在用户的家目录下），早年被人当
作原始版的 Twitter 来用。

**John Carmack 的 `.plan`**（1996–2010）就是经典案例：每天一篇日志，
内容覆盖 DOOM/Quake 的开发、引擎里的小聪明、移植时的各种抓狂。归档
在 <https://github.com/ESWAT/john-carmack-plan-archive>。配套推荐读物：
Fabien Sanglard 的 *Game Engine Black Book: DOOM*。

为什么有人觉得 `.plan` 比博客或 Twitter 更好（看个人口味）：没有数据
分析、没有广告、几乎没有额外开销。代价：发不了图片（不算转义码和 ASCII
art 的话）。

### WebFinger（RFC 7033）——Finger 在 ActivityPub 时代的转世

Mastodon 是一个去中心化的 Twitter 替代品——任何人都能跑自己的服务器，
toot（推文）通过 **ActivityPub** 协议在服务器之间流转。这就带来一个发
现问题：`@gargron@mastodon.social` 这个账号到底在哪台服务器上？这就由
**WebFinger** 来解决。

它无非就是对一个约定俗成的 URL 发一个 HTTPS GET，回来一份 JSON：

```sh
curl 'https://mastodon.social/.well-known/webfinger?resource=acct:Gargron@mastodon.social'
```

```json
{
  "subject": "acct:Gargron@mastodon.social",
  "aliases": [
    "https://mastodon.social/@Gargron",
    "https://mastodon.social/users/Gargron"
  ],
  "links": [
    { "rel": "http://webfinger.net/rel/profile-page",
      "type": "text/html",
      "href": "https://mastodon.social/@Gargron" },
    { "rel": "self",
      "type": "application/activity+json",
      "href": "https://mastodon.social/users/Gargron" }
  ]
}
```

跟 Finger 是一个思路，只是现代化了：HTTP + JSON 取代了 79 端口 + 纯
文本。要自己搭 Mastodon 风格的服务，Jo 推荐看 **Grunfink 的 SNAC2**。

### 那个没成真的 web——Gopher（RFC 1436）

- 1991 年诞生于明尼苏达大学（University of Minnesota）。
- 设计初衷是**目录列举与文件检索**——比 HTML 结构化得多。
- 服务端软件至今仍在（Jo 用的是 **Gophernicus**）。

一个站点本质上就是一份 **gophermap**——纯文本，里面是固定类型的链接。
每一行以一个单字符的类型码开头：

```
1Folder of blogs    /blogs               gopher.server  70
0Notes              /notes.txt           gopher.server  70
IMy cat             /pictures/nigel.png  gopher.server  70
hGoogle             URL:http://www.google.com
gThis is fine       /pictures/this-is-fine.gif  gopher.server  70
0Finger my user jo                       gopher.server  79
```

幻灯片里出现过的类型码：`0` 文本、`1` 目录、`g` GIF、`I` 图像、`h`
HTML 或外部 URL。

**Gopher 为什么输给了 HTML/HTTP：**

- 1993 年试图商业化——UMN 想对协议本身收费。一下子把势头掐死了。
- HTML 那套开放的 **MIME types** 完胜 Gopher 那种固定枚举的链接类型。
- 没有样式、没有加密、没有任何能撑起现代 web 的故事。
- 如今还活着的服务器只剩约 300 个左右。

它在 **tilde** 社区里活得还行——`tilde.club`、`tilde.town`、`sdf.org`
都能给你开一个 gopherhole。现代 Gopher 浏览器：**Castor**、**Chawan**、
**Links2**。Firefox 以前自带支持 Gopher，现在没了。

### Gemini 协议与 smolweb

它是对 web 的臃肿、广告以及那些充满敌意的社交平台的一次反弹。

- 把焦点更彻底地放回内容本身——**没有 CSS，没有 JavaScript**。
- 保留 Gopher 那种纯文本的简朴气质，又借鉴了 HTML 的一些好点子。
- 主页：<https://geminiprotocol.net>
- 现有几千台服务器；不少同时也以 gopherhole 形式镜像了一份给"老古板们"。

这一章在结尾给出的社会主张是：让自己变得"可被 finger"，跑一个
gopherhole，把 web 从分析跟踪和广告手里夺回来。

## 工具速查

幻灯片和 lab 里点名的具体工具其实不多。

```sh
# ----- 手动跟服务器对话 -----
nc bristol.ac.uk 80                # netcat：开一个原始 TCP 连接
                                   # 自己敲请求，看回复
# 最简版 Finger 客户端（lab 注脚里的小作弊）：
nc "${1:?URL}" <<<"${2:?Who}"      # 把 "who" 通过 TCP 发到 URL

# 用真正的 Finger 客户端读别人的 .plan
finger fishfinger@tilde.club
finger bristol@graph.no            # 天气预报（lab 里有提）
finger @graph.no                   # 列出 graph.no 上可用的"用户"

# ----- WebFinger（HTTP + JSON） -----
curl 'https://mastodon.social/.well-known/webfinger?resource=acct:Gargron@mastodon.social'

# ----- 在 inetd 风格的超级服务器下跑协议处理程序 -----
# Linux:    xinetd、systemd socket activation
# OpenBSD:  /etc/inetd.conf  +  /etc/services
# macOS:    launchd
```

幻灯片里用到的 C socket API 表面：

```
getaddrinfo  socket  connect  send  recv  close            # 客户端
getaddrinfo  socket  setsockopt  bind  listen  accept  fork  send  recv  close   # 服务器
```

这就是这一讲明确点到的全部工具集。（没有 `openssl`、`dig`、`nslookup`、
`host`、`traceroute`、`telnet`、`ssh`、`scp`、`gpg`——这些幻灯片里都没
出现。）

## Lab 实操

来源：`lab/README.org`。主题：**RFC 1288 — Finger**。

你要把 Finger 的**客户端和服务器**都实现一遍；客户端更容易，先从那里
入手。语言随你挑，但 TA 只能调试他们熟的那些。

### Step 0 — 读 RFC

> 读 IETF RFC 1288：<https://datatracker.ietf.org/doc/html/rfc1288>

只有 12 页。重点关注：

- **第 2 节**——协议定义（线格式）。
- **第 4 节**——会话样例。

边读边做笔记。

### Part 1 — 客户端

实现一个 Finger 客户端，要做的事情：

1. 跟 Finger 服务器开一个 TCP 连接（按惯例是 79 端口）。
2. 发一行查询（一个用户名、`@host`，或者 `username@host`，可带可选
   flag），按 RFC 规定的方式终止。
3. 把服务器返回的内容读出来打印。

README 给出的语言指南：

- C / 汇编：Beej's Guide to Network Programming——
  <https://beej.us/guide/bgnet/>。
- Python：<https://docs.python.org/3/howto/sockets.html>。
- Java：<https://docs.oracle.com/javase/tutorial/networking/sockets/index.html>。
- Uiua（一种数组式的隐式栈语言）：<https://www.uiua.org/docs>。

**测试装置：**

- 先用 `netcat` 在某个端口上监听，看你客户端发出去的字节是不是原样到
  达：
  ```sh
  nc -l 7979            # 一个终端
  ./your-finger-client localhost 7979 some-user   # 另一个终端
  ```
- 然后把客户端指向真实服务器：
  - `bristol@graph.no`——天气预报。
  - `@graph.no`——graph.no 上可用的"用户"/选项列表。
  - <https://plan.cat>——公开的 finger 服务器，看看大家都贴了点啥。

**作弊版——一行的最简实现**（这算作弊，写完什么也学不到）：

```sh
nc "${1:?URL}" <<<"${2:?Who}"
```

### Part 2 — 服务器

实现一个 Finger 服务器，要做的事情：

1. 在某个 TCP 端口上监听（如果你在 lab 机器上，请用一个非标准端口——
   79 是特权端口）。
2. 读取查询。
3. 解析它：典型做法是查找请求里的用户、然后**读他的 `.plan` 文件**
   （README 把这一步明确丢给学生当练习题：
   "How do you read user's `.plan` files?"）。
4. 写回响应、关闭连接。

README 里关于部署的说明：如果你想在 lab 机器上测试，需要做端口转发——
参见 HTTP labs 里的 Vagrant 配置。

### `message.pgp` 是干嘛用的

值得提一句：`19-protocols/` 目录里在幻灯片和 lab 旁边还附带了一个
`message.pgp` 文件。lab 的 `README.org` 里**没**提到它，幻灯片里也
**完全没**提到 PGP、GPG 或者加密。最合理的解释是它是一个额外/选修的
小彩蛋——一封 PGP 加密的留言，扔在这一章里让学生自己注意到，跟整讲
"线上跑的就是字节而已；协议和格式都只是君子协议"的主题挺契合。

不要去尝试解密它（这一章范围里没有发过对应的密钥）。注意到它的存在
然后过吧。文件大小 `706 bytes`，`file(1)` 把它识别为 `PGP message`。

### 交付物

按 README 的要求：

- 一个能跑的 Finger **客户端**，已经在 `netcat` 上以及在真实公开的
  Finger 服务器（如 `graph.no` 或 `plan.cat`）上测过。
- 一个能跑的 Finger **服务器**，能返回点像样的东西——至少在被 finger
  时返回该用户的 `.plan` 文件。

## 易错点与重点

Jo 强调过的（或藏在字里行间的）那些容易咬到学生的点：

- **不要照幻灯片那样写网络代码。** 它们为了可读性把所有错误处理都剥
  掉了。真实代码里：每一个返回值都要检查、`addrinfo` 链表要用
  `freeaddrinfo` 释放、子进程要回收（`waitpid` / `SIGCHLD` 处理函数）、
  每条出错路径都要 close。
- **`getaddrinfo` 返回的是一个*链表*。** 要循环遍历，别假设第一个就
  能用。可能 IPv4 跟 IPv6 都有，可能多块网卡，等等。
- **`SO_REUSEADDR` 很关键。** 不设的话，服务器刚崩完想立刻重启，
  `EADDRINUSE` 能拦你最多一分钟。
- **`fork()` 不收尸 = 僵尸进程。** 一个长期运行、不依赖 `inetd` 的服
  务器要是没处理 `SIGCHLD`，进程表迟早被填爆。
- **`send`/`recv` 不是 `write`/`read` 的免费替身**——TCP 上短读短写
  是常态。要循环直到收/发够你预期的字节，或者直到对端关闭连接。
- **特权端口。** 任何小于 1024 的端口（Finger=79、Gopher=70、HTTP=80）
  都需要 root、capabilities 或端口转发。lab 机器上你绑不上 79，用一个
  高位端口然后转发过去。
- **`inetd` 不是现代的做法。** 它作为教学工具非常好用，因为它把"写一个
  服务器"压缩成"写一个 stdin/stdout 过滤器"，但它的攻击面正是大家迁
  到 `systemd` socket activation / `launchd` 的原因。生产服务别用经典
  的 `inetd` 上线。
- **`inetd.conf` 里的权限分离。** 注意每个服务都跑在它专属的低权限用
  户下（`_fingerd`、`_gophernicus`）。你自己写服务时也照搬这个纪律。
- **写代码前先读 RFC。** lab 里专门点了 RFC 1288 的 §2（线格式）和
  §4（会话样例）。学生 Finger 实现里大多数 bug 都是"我从幻灯片猜了
  一下线格式"导致的。
- **先在 `nc` 上测，再上真服务。** 当你掌握线两端时调试客户端要容易
  得多。
- **小心处理换行。** 按 RFC，Finger 的查询行是 `<CRLF>` 结尾的；从
  Linux 客户端发出去的孤立 `\n` 在某些服务器上不一定能用。
- **协议层面的现实主义。** Gopher 失败的方式（试图商业化）是个警世
  寓言：开放协议一旦有人想收过路费，就会输给那个一直保持自由的对手。
- **这一章不讲什么。** 没有 TLS 握手、没有 DNS 内部、没有 SSH 配置、
  没有 PKI、没有邮件协议——如果你冲着这些来，走错地方了；它们（如果
  课程里有的话）在课程的别处。
