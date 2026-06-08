# Chapter 19 — Network protocols

> Lecturer: Jo Hallett. The lecture is deliberately a bit silly: it sells the
> idea that internet protocols are just text-over-sockets specified by IETF
> RFCs, walks you through socket programming and `inetd`, then takes a tour of
> the "web that wasn't" — Finger and Gopher — and ends with a smolweb pitch
> (Gemini protocol). The lab makes you implement Finger.

## Overview

The slides answer a single question: **"OK but what *actually* is HTTP?"** —
and use that to pull the lid off application-layer protocols in general.

The argument runs:

1. Protocols (HTTP, HTCPCP, Finger, Gopher, WebFinger) are **just plaintext
   conversations** documented in IETF RFCs. If you can read the RFC and write
   bytes onto a TCP socket, you can speak the protocol.
2. To actually *send* those bytes you need a **socket** — the POSIX abstraction
   that looks like a file descriptor but talks over the network. The slides
   walk through the C client + server skeleton (`getaddrinfo`, `socket`,
   `connect`, `bind`, `listen`, `accept`, `send`, `recv`).
3. You usually don't want to write that skeleton. **`inetd`** ("the internet
   super-server") will accept connections for you and hand your program a
   socket on stdin/stdout, so a Finger or Gopher server can be a shellscript.
4. History detour: before HTTP+HTML+social-media won, the web was a mosaic of
   smaller protocols. Two of them — **Finger** (RFC 1288) and **Gopher** (RFC
   1436) — get a full demo, plus their modern descendants **WebFinger** (RFC
   7033, used by Mastodon/ActivityPub) and **Gemini** (the smolweb).
5. In the lab you implement Finger — both client and server.

This chapter is *not* about: TLS, DNS internals, OSI layering, packet
inspection, SSH, mail protocols, or PKI. None of those appear in the slides.

## Core knowledge

### IETF and RFCs — where protocols live

- The **Internet Engineering Task Force (IETF)** is the standards body for
  the internet. Non-profit, anyone can join by participating, **companies
  cannot join as companies** — only individuals.
- Decisions are made by **rough consensus** and **running code**.
- They publish **Requests for Comments (RFCs)** — plaintext documents (in
  monospace fonts that "look a bit sketchy") that describe what a protocol
  should do.
- Culture: conservative towards change, occasionally trolly.

Walked-through example: **RFC 1945 — HTTP/1.0** (Berners-Lee, Fielding,
Frystyk, May 1996). Note the IESG even hedges in the opening: it expects the
informational memo to be replaced by a standards-track document soon.

### RFCs can be jokes too — HTCPCP (RFC 2324)

The Hyper Text Coffee Pot Control Protocol, 1998. Ostensibly a joke; in the
era of smart kettles, oddly prescient.

- Built **on top of HTTP** with new methods, headers, return codes.
- New URI scheme: `coffee:`
- New method: **`BREW`** (and `WHEN`, used the way you say "when" while milk
  is being poured).
- New header: **`Accept-Additions`** with `addition-type` enums for milk
  (`Cream`, `Half-and-half`, `Whole-milk`, `Part-Skim`, `Skim`, `Non-Dairy`),
  syrup (`Vanilla`, `Almond`, `Raspberry`, `Chocolate`), alcohol (`Whisky`,
  `Rum`, `Kahlua`, `Aquavit`), etc.
- New status code: **`418 I'm a teapot`** — returned if you try to brew
  coffee with a teapot.

The takeaway: an RFC is just an agreement. Read it and you can speak the
protocol; implement it and others can speak to you.

### Sockets — the POSIX way to send bytes

A socket is like a file descriptor, but reads and writes go via the network.
Same primitives you'd use for a file (`read`/`write`) but with a connection-
setup dance up front, and `send`/`recv` instead.

**High-level plan:**

| Step | Client | Server |
|------|--------|--------|
| 1 | Set up connection details (`hints`) | Set up connection details (`AI_PASSIVE`) |
| 2 | `getaddrinfo` (resolves via DNS) | `getaddrinfo` (own IP) |
| 3 | `socket()` | `socket()`, `setsockopt(SO_REUSEADDR)` |
| 4 | `connect()` | `bind()` then `listen()` |
| 5 | `send()` / `recv()` | `accept()`, `fork()`, then `send()` / `recv()` |
| 6 | `close()` | `close(new_fd)` per child |

#### Client skeleton (C, no error handling)

```c
struct addrinfo *servinfo, hints;
memset(&hints, 0, sizeof hints);
hints.ai_family   = AF_UNSPEC;   // IPv4 or IPv6, don't care
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

A real `getaddrinfo` returns a **linked list** of candidates — IPv4 vs IPv6,
multiple network interfaces, etc. The loop tries them in order.

Sample response from `bristol.ac.uk:80`:

```
HTTP/1.0 302 Moved Temporarily
Location: https:///
Server: BigIP
Connection: close
Content-Length: 0
```

#### Server skeleton (C, no error handling)

```c
struct addrinfo hints, *servinfo;
memset(&hints, 0, sizeof hints);
hints.ai_family   = AF_UNSPEC;
hints.ai_socktype = SOCK_STREAM;
hints.ai_flags    = AI_PASSIVE;  // listen on my IP
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
listen(sockfd, 10);   // backlog of 10

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

Why each call:

- `setsockopt(..., SO_REUSEADDR, ...)` — avoid "port in use" errors when
  restarting the server.
- `bind` — attach the program to the socket without committing to a peer.
- `listen` — start queueing incoming connections, with a backlog of 10.
- `accept` — pop one queued connection, return a new fd to talk to it on.
- `fork` — let the child handle the connection so the parent can keep
  accepting new ones.

Caveats Jo flags explicitly:

- "Please don't actually write network code like this!" — no error handling,
  and dead forks need reaping or you fill the process table.
- For a real reference: **Beej's Guide to Network Programming** —
  [https://beej.us/guide/bgnet/](https://beej.us/guide/bgnet/) — recommended
  every time you have to do this.
- Higher-level wrappers exist in every modern language; `send`/`recv` is the
  C-level minimum. Going the other way, the kernel's TCP/IP stack lives one
  level below.

### Inetd — abstract the boilerplate away

Question motivating `inetd`: if all a server is doing is "listen on a port,
hand each connection to a service that reads stdin and writes stdout", why
should the service program have to know about sockets at all?

**`inetd`** ("Internet Services Daemon"):

- A single super-service that listens on many ports on your behalf.
- For each incoming connection it spawns the right program with **stdin and
  stdout wired to the socket**.
- First appeared in 1978. Largely forgotten now: considered insecure mostly
  because of its large, prominent attack surface.
- Modern equivalents: `xinetd` on Linux, similar functionality in `systemd`,
  similar functionality in `launchd` on macOS. They mostly do nothing by
  default — consult your OS manual.

Jo's example, from an OpenBSD server using the classic `/etc/inetd.conf`
format:

```
# Service  Kind        Conn    Options  User           Process
finger     stream tcp  nowait           _fingerd       /usr/libexec/fingerd
finger     stream tcp6 nowait           _fingerd       /usr/libexec/fingerd
gopher     stream tcp  nowait           _gophernicus   /usr/local/libexec/in.gophernicus
```

- `nowait` — allow more than one instance to run concurrently.
- Each service runs as a **separate, dedicated user** (`_fingerd`,
  `_gophernicus`). Privilege separation.
- Programs live in `/libexec/`, not `/bin/`, by convention — they're not
  meant to be run by humans.
- `/etc/services` maps the symbolic names to ports:

```
gopher  70/tcp
gopher  70/udp
finger  79/tcp
```

Because stdin/stdout are already wired to the socket, the service can be
**anything that reads stdin and writes stdout** — Jo's actual `fingerd` is
literally a shell script. Could equally be C with `scanf`/`printf`, or
Python with `read`/`print`.

> "I can run my Gopherhole and Finger server happily on a cheap VPS."

### OpenBSD aside

Jo runs the server demos on OpenBSD. Characterisation: simple to the point
of being slow and annoying, but debuggable, mostly just works, and a small
attack surface so "maybe secure-ish".

### The web that wasn't — Finger (RFC 1288)

Origin story: in early UNIX you logged into a shared mainframe from a dumb
terminal. A dozen-ish networked computers existed pre-internet. If somebody
was hammering the system or had dialled in from outside, it was useful to be
able to **put your finger on who they were** — hence the protocol's name and
the user-creation prompt asking for real name, phone, room.

Wire protocol:

- Send a TCP message over **port 79**.
- Body forms (with optional flags for verbosity):
  - `username` — finger that local user.
  - `@host` — list all the users on that host.
  - `username@host` — like a jump host in SSH: ask the host to forward the
    finger request elsewhere.
- Server returns whatever it likes as plaintext.

Example response (`finger fishfinger@tilde.club`):

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

The **`.plan`** file (placed in the user's home directory) is shown in the
response. It was used as an early proto-Twitter.

**John Carmack's `.plan`** (1996–2010) is the canonical example: daily logs
covering DOOM/Quake development, engine tricks, porting frustrations.
Archived at <https://github.com/ESWAT/john-carmack-plan-archive>. Companion
recommendation: Fabien Sanglard's *Game Engine Black Book: DOOM*.

Why a `.plan` beats a blog/Twitter, depending on taste: no analytics, no
ads, almost no overhead. Trade-off: no images (escape codes and ASCII art
notwithstanding).

### WebFinger (RFC 7033) — Finger reborn for ActivityPub

Mastodon is a decentralised Twitter alternative — anyone can run a server,
**ActivityPub** carries toots between servers. The discovery problem (which
server is `@gargron@mastodon.social` actually on?) is solved by **WebFinger**.

It's just an HTTPS GET to a well-known URL, returning JSON:

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

Same idea as Finger, modernised: HTTP + JSON instead of port 79 + plaintext.
For self-hosting Mastodon-style services, Jo flags **Grunfink's SNAC2**.

### The web that wasn't — Gopher (RFC 1436)

- Developed at the University of Minnesota in 1991.
- Designed for **directory listing and file retrieval** — much more
  structured than HTML.
- Server software still around (Jo uses **Gophernicus**).

A site is a **gophermap** — plaintext with links of fixed link types. Each
line begins with a single-character type code:

```
1Folder of blogs    /blogs               gopher.server  70
0Notes              /notes.txt           gopher.server  70
IMy cat             /pictures/nigel.png  gopher.server  70
hGoogle             URL:http://www.google.com
gThis is fine       /pictures/this-is-fine.gif  gopher.server  70
0Finger my user jo                       gopher.server  79
```

Type codes seen in the slides: `0` text, `1` directory, `g` GIF, `I` image,
`h` HTML/external URL.

**Why Gopher lost to HTML/HTTP:**

- Attempted commercialisation in 1993 — UMN tried to charge for the
  protocol. Killed momentum.
- HTML's open **MIME types** beat Gopher's fixed enum of link types.
- No styling. No encryption. No story for the modern web.
- Only ~300 servers still live.

Survives in the **tilde** community — `tilde.club`, `tilde.town`, `sdf.org`
will give you a gopherhole. Modern Gopher browsers: **Castor**, **Chawan**,
**Links2**. Firefox used to support Gopher natively but doesn't any more.

### Gemini protocol and the smolweb

A reaction to bloat, ads, and hostile social platforms.

- Much more focus on content — **no CSS, no JavaScript**.
- The simple text feel of Gopher, but with some good ideas from HTML.
- Home: <https://geminiprotocol.net>
- A few thousand servers; many are mirrored as gopherholes for the
  curmudgeonly.

The chapter's social pitch: "make yourself fingerable", run a gopherhole,
take the web back from analytics and ads.

## Tool cheat sheet

The slides + lab only call out a small set of concrete tools.

```sh
# ----- Talk to a server by hand -----
nc bristol.ac.uk 80                # netcat: open a raw TCP connection
                                   # type the request, see the reply
# Minimal Finger client (the cheat in the lab footnote):
nc "${1:?URL}" <<<"${2:?Who}"      # send "who" over TCP to URL

# Read someone's .plan with a real Finger client
finger fishfinger@tilde.club
finger bristol@graph.no            # weather forecast (per the lab)
finger @graph.no                   # list available "users" on graph.no

# ----- WebFinger (HTTP + JSON) -----
curl 'https://mastodon.social/.well-known/webfinger?resource=acct:Gargron@mastodon.social'

# ----- Run protocol handlers under inetd-style supervisors -----
# Linux:    xinetd, systemd socket activation
# OpenBSD:  /etc/inetd.conf  +  /etc/services
# macOS:    launchd
```

C socket API surface used in the slides:

```
getaddrinfo  socket  connect  send  recv  close            # client
getaddrinfo  socket  setsockopt  bind  listen  accept  fork  send  recv  close   # server
```

That's the entire toolset the lecture mentions explicitly. (No `openssl`,
`dig`, `nslookup`, `host`, `traceroute`, `telnet`, `ssh`, `scp`, `gpg` —
they don't appear in these slides.)

## Lab walkthrough

Source: `lab/README.org`. Topic: **RFC 1288 — Finger**.

You implement **both a client and a server** for Finger; the client is
easier, so start with that. Pick whatever language you like, but the TAs can
only debug the ones they know.

### Step 0 — Read the RFC

> Read IETF RFC 1288: <https://datatracker.ietf.org/doc/html/rfc1288>

Only 12 pages. Pay special attention to:

- **Section 2** — protocol definition (the wire format).
- **Section 4** — example sessions.

Take notes.

### Part 1 — Client

Implement a Finger client that:

1. Opens a TCP connection to a Finger server (port 79 by convention).
2. Sends a query line (a username, `@host`, or `username@host`, with
   optional flags) terminated per the RFC.
3. Reads and prints whatever the server returns.

Language pointers from the README:

- C / assembly: Beej's Guide to Network Programming —
  <https://beej.us/guide/bgnet/>.
- Python: <https://docs.python.org/3/howto/sockets.html>.
- Java: <https://docs.oracle.com/javase/tutorial/networking/sockets/index.html>.
- Uiua (array-oriented tacit stack): <https://www.uiua.org/docs>.

**Test rig:**

- Start with `netcat` listening on a port and check your client's bytes
  arrive verbatim:
  ```sh
  nc -l 7979            # in one terminal
  ./your-finger-client localhost 7979 some-user   # in another
  ```
- Then point your client at real servers:
  - `bristol@graph.no` — weather forecast.
  - `@graph.no` — list of available "users"/options on graph.no.
  - <https://plan.cat> — public finger server, browse what people post.

**Cheat — the trivial implementation** (counts as cheating; you'll learn
nothing):

```sh
nc "${1:?URL}" <<<"${2:?Who}"
```

### Part 2 — Server

Implement a Finger server that:

1. Listens on a TCP port (use a non-standard one if you're on a lab
   machine — port 79 is privileged).
2. Reads the query.
3. Resolves it: typically by looking up the requested user and **reading
   their `.plan` file** (the README explicitly poses this as an exercise:
   "How do you read user's `.plan` files?").
4. Writes the response and closes.

Deployment note from the README: if you want to test on a lab machine,
you'll need port forwarding — see the HTTP labs Vagrant configuration.

### What `message.pgp` is for

Worth flagging: the `19-protocols/` directory ships a `message.pgp` file
alongside the slides and lab. The lab `README.org` does **not** mention it
and the slides do **not** mention PGP, GPG, or encryption. It is most
plausibly an extra/optional stunt — a PGP-encrypted message left in the
chapter for students to notice, in keeping with the lecture's "everything
on the wire is just bytes; protocols and formats are agreements" theme.

Don't try to decrypt it (no key has been issued for it in scope of this
chapter). Note its existence and move on. The file is `706 bytes`,
recognised by `file(1)` as `PGP message`.

### Deliverables

Per the README:

- A working Finger **client** that you've tested against `netcat` and
  against a real public Finger server (e.g. `graph.no` or `plan.cat`).
- A working Finger **server** that serves something sensible — at minimum,
  return a user's `.plan` file when fingered.

## Pitfalls & emphasis

Things Jo emphasises (or hides between the lines) that bite students:

- **Don't write network code like the slides do.** They strip out all error
  handling for legibility. Real code: check every return value, free the
  `addrinfo` linked list (`freeaddrinfo`), reap children (`waitpid` /
  `SIGCHLD` handler), close on every error path.
- **`getaddrinfo` returns a *list*.** Loop through it; don't assume the
  first entry works. IPv4/IPv6, multiple NICs, etc.
- **`SO_REUSEADDR` matters.** Without it, restarting your server right
  after a crash gives you `EADDRINUSE` for up to a minute.
- **`fork()` without reaping creates zombies.** A long-running `inetd`-less
  server that doesn't handle `SIGCHLD` will fill the process table.
- **`send`/`recv` are not `write`/`read` lookalikes for free** — short
  reads/writes are normal on TCP. Loop until you've sent/received what you
  expect, or until the peer closes.
- **Privileged ports.** Anything below 1024 (Finger=79, Gopher=70, HTTP=80)
  needs root, capabilities, or port forwarding. On lab machines you can't
  bind to 79 — use a high port and forward.
- **`inetd` is not the modern way.** It's a great teaching tool because it
  collapses "write a server" to "write a stdin/stdout filter", but its
  attack surface is why people moved to `systemd` socket activation /
  `launchd`. Don't ship a production service via classic `inetd`.
- **Privilege separation in `inetd.conf`.** Notice each service runs as its
  own dedicated underprivileged user (`_fingerd`, `_gophernicus`). Copy
  this discipline if you build your own.
- **Read the RFC before you code.** The lab specifically calls out RFC
  1288 §2 (wire format) and §4 (example sessions). Most bugs in student
  Finger implementations are "I guessed the wire format from the slides".
- **Test against `nc` first, then go live.** It's much easier to debug your
  client when you control both ends of the wire.
- **Strip line endings carefully.** Finger uses `<CRLF>`-terminated query
  lines per the RFC; lone `\n` from a Linux client may or may not work
  depending on the server.
- **Copyright/protocol pragmatics.** Gopher's failure mode (commercialisation
  attempt) is a cautionary tale: an open protocol that someone tries to
  toll loses to one that stays free.
- **What this chapter is not.** No TLS handshake, no DNS internals, no SSH
  config, no PKI, no mail protocols — if you came expecting those, this is
  the wrong chapter; they're (if anywhere) elsewhere in the course.
