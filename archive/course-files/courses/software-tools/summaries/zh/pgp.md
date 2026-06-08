# 第 18 章 — PGP / GPG 加密

## 章节概览

这一章是公钥密码学的一次完整漫游，从"它到底解决了什么问题"出发，一直走到"日常该怎么用这套工具"。课程开头举了个很贴近生活的例子：你在网上买一件 T 恤，要在表单里填信用卡号——这背后凭什么安全？讲师用这个场景论证了一件事：基于"事先共享的密码"那一套机制根本撑不起几十亿用户规模的互联网，真正让现代 Web 跑起来的，是**公钥密码学**。从这里出发，章节梳理了公钥密码在三个领域的具体落地：

- **OpenSSH** — 登录认证（密钥 + challenge / `~/.ssh/authorized_keys`）。
- **OpenSSL / TLS** — 服务器身份与加密传输，信任锚定在中心化的根证书体系上（`/etc/ssl/certs/ca-certificates.crt`，大约 150 个 CA，证书链，Let's Encrypt + ACME）。
- **PGP / GnuPG** — 给"人"做认证（邮件、签名的 Git commit、签名的 Debian/Fedora ISO），信任不依赖 CA，而是用去中心化的 **Web of Trust**。

因为本章的考核交付物是 lab，所以重头戏放在 GPG 上：生成密钥、通过 keyserver 分发密钥、加密和签名消息、办 key-signing party、验证下载。两篇论文（Whitten & Tygar 1996，Fahl et al. 2012）是可用性这一面的反题——再优雅的密码学，UI 出错或者开发者配错，都会全军覆没。

## 核心知识

### Symmetric vs asymmetric crypto

- **Symmetric（对称加密）**：一把共享密钥，加密和解密都用它。速度快，但你得先有一条安全通道把这把密钥递过去——这就是经典的"先有鸡还是先有蛋"问题，也正是公钥密码学要破解的死结。
- **Asymmetric（非对称 / 公钥加密）**：是一**对**密钥。**public key** 可以公开发布；**private key（secret key）** 永远不离开主人手里。一把加密的，必须由另一把来解密。课件用比较抽象的语言把背后的数学概括成"难解、易验、不漏信息"。RSA、ElGamal、DSA、Elliptic Curve 是这种思想的不同具体实现。
- 实际系统几乎都是**hybrid（混合加密）**：用公钥密码协商出一把对称的 session key，然后真正的大块数据用对称密钥加密。PGP 内部就是按这个套路工作的。

### Public/private keys, digital signatures, fingerprints, Web of Trust

- **加密方向**：用对方的 *public* key 加密 → 只有持有对应 *private* key 的人能解开。
- **签名方向**：用自己的 *private* key 签名 → 任何持有你 *public* key 的人都能验证这条消息确实出自你手。课件用 RSA 把这件事写得很直白：因为 `(m^e)^d ≡ m (mod n)`，所以你也可以反过来算 `m^d`，然后让别人用 `e` 去验证它——那个被签名后的值就是签名本身。
- **Fingerprint（指纹）**：公钥经过 hash 后得到的一段较短字符串（比如 `7860 0FD9 AF8A 5307 BE9D C633 26BB 2BE0 FD06 DFA9`）。当你从某个渠道下载到一个公钥时，要确认它真的属于那个名字背后的人，办法就是用 out-of-band（带外）的方式去比对指纹——当面、电话里念，都行。
- **Web of Trust**（PGP 对 CA 体系的回答）：你绝对信任你自己；如果你当面核对过某人，你就给他的公钥签名；如果你信任一个人，而那个人又给第三方签了名，那你就可以传递性地建立起对那个第三方的信心。这里没有任何中心权威——信任是一张图，不是一棵树。这张图在实践中靠"key-signing parties"一点一点织出来。

### PGP history & the OpenPGP standard

- **PGP** = Pretty Good Privacy，由 Phil Zimmermann 在 1991 年写成（课件写的是 1996，那是 PGP 5.0 的时代）。早年因为强加密在美国出口管制法里被归类为"军火"，Zimmermann 还因此被调查过。
- 协议和文件格式后来被标准化为 **OpenPGP**（RFC 4880 及其后续版本），**GnuPG（GPG）** 是占据主导地位的免费实现。
- 在某些国家 PGP/GPG 仍是非法或受限的；强加密的出口问题不仅是技术问题，也是非常实际的政治议题。

### End-to-end encrypted email workflow

整条流水线按顺序大致是这样：

1. **Generate** — 在本地生成一对密钥（`gpg --full-generate-key`）。建议选 RSA+RSA、4096 bits、1 年到期。设置好姓名 + 邮箱；用强 passphrase 保护它。
2. **Generate a revocation certificate** — 立刻生成一份 revocation certificate 并离线保存——这是你万一弄丢密钥时的"急停按钮"。
3. **Distribute** — 分发你的公钥——上传到 keyserver（`--send-keys`），或者直接交给联系人。
4. **Acquire** — 拿别人的公钥（`--recv-keys`、`--search-key`），并且在信任之前先用带外方式核对 fingerprint。
5. **Encrypt** — 用对方的公钥加密消息（`gpg --encrypt -r alice@example.com file.txt`）。
6. **Sign** — 用自己的私钥签名（`gpg --sign` / `--clearsign` / `--detach-sign`）。组合起来：先签名再加密，可以同时证明作者身份和保证机密性。
7. **Verify** — 验证收到的签名（`gpg --verify`）。
8. **Decrypt** — 用自己的私钥解密收到的密文（`gpg --decrypt`）。

### Keyservers, revocation, expiry

- **Keyservers**（如 `keyserver.ubuntu.com`）是公开的数据库，把身份映射到公钥。任何人都能上传，任何人都能拉取。注意一点：keyserver 是 append-only 的——你没法把已经发布上去的密钥真正"删掉"，只能标记它已被 revoke。
- **Revocation certificate**：一份签了名的声明，说"这把密钥不再有效"。在生成密钥的当天就把它做出来，存到安全的地方（U 盘、抽屉里的纸质打印件都可以）。如果不做这个东西，万一你弄丢了私钥，你就再也没办法告诉全世界"别再相信这把密钥了"。
- **Expiry**：给密钥设一个有限寿命（比如 1 年）。万一密钥丢了又没有 revocation cert，至少损失被限制在一段时间内。如果密钥还在你手里，你随时可以用 `gpg --edit-key … expire` 把有效期延长。

### Hash functions and signatures

- 数字签名并不是把整条消息都用私钥加密一遍（那样既慢又会让输出膨胀）。实际做法是：先用 cryptographic hash function（SHA-256、SHA-512——新项目里别再用 MD5 或 SHA-1）把消息 hash 一下，然后把这个 hash 用私钥加密。
- 这意味着无论原始消息多长，签名都是固定且较短的长度，验证也很快。
- 这同时也意味着 hash collision 会击溃签名：如果攻击者能找到两条 hash 相同的消息，他就能在合法签名下偷天换日。这就是为什么旧的 hash 算法会被陆续淘汰。

### Usability problems (papers)

两篇指定阅读论文构成了整章的警世故事：

- **Whitten & Tygar (1996)** — 即使按照大众消费软件的标准 PGP 的 GUI 已经算得上打磨过的，给 90 分钟的时间，大部分新手仍然没法正确加密并签名一封邮件。安全软件有一些特殊的可用性属性（unmotivated user、abstraction、lack of feedback、barn door、weakest link），普通 UI 设计经验对付不了它们。
- **Fahl et al. (2012)** — 即便开发者真的去用 TLS，他们也常常配错。在 13,500 个 Android app 里，有 1,074 个被认定为存在 MITM 风险；手动审计的 100 个 app 里有 41 个能在伪造的 TLS 连接下泄露凭据。crypto 的可用性问题不只针对终端用户，对*开发者*也一样致命。

## GPG 命令速查

密钥生成与查看：

```sh
gpg --full-generate-key                          # interactive wizard (most options)
gpg --gen-key                                    # quick wizard with sane defaults
gpg --list-keys                                  # all public keys you know about
gpg --list-secret-keys                           # private keys you control
gpg --fingerprint <user-or-keyid>                # show the fingerprint
gpg --edit-key <keyid>                           # interactive edit (expire, addphoto, sign, trust, …)
```

进入 `--edit-key` 后常用的子命令：

```text
help        # list everything
expire      # change expiry of primary key
trust       # set how much YOU trust this key as a certifier
sign        # sign this key with yours
addphoto    # embed a JPEG in the key
addrevoker  # designate a revoker
quit        # save & exit
```

生成 revocation certificate 和修改 expiry：

```sh
gpg --output revoke.asc --armor --gen-revoke <keyid>     # do this on day 1, store offline
gpg --edit-key <keyid>                                   # then `expire`, `2y`, `y`, `save`
```

通过 keyserver 分发密钥：

```sh
gpg --keyserver keyserver.ubuntu.com --send-keys <keyid>
gpg --keyserver keyserver.ubuntu.com --recv-keys <keyid>
gpg --keyserver keyserver.ubuntu.com --search-key 'Jo Hallett'
```

导出 / 导入（用于离线传输或备份）：

```sh
gpg --armor --export <keyid> > my-public.asc             # ASCII-armored public key
gpg --armor --export-secret-keys <keyid> > my-secret.asc # PRIVATE — guard this
gpg --import alice-public.asc                            # import someone else's key
```

加密与解密：

```sh
gpg --encrypt --recipient alice@example.com message.txt          # → message.txt.gpg (binary)
gpg --armor --encrypt --recipient alice@example.com message.txt  # → message.txt.asc (base64)
gpg --decrypt message.txt.asc                                    # to stdout
gpg --output plain.txt --decrypt message.txt.asc                 # to file
```

签名的几种变体：

```sh
gpg --sign file.txt                # → file.txt.gpg (binary, file embedded)
gpg --clearsign file.txt           # → file.txt.asc (file readable, signature appended)
gpg --detach-sign file.iso         # → file.iso.sig (signature in a separate file)
gpg --armor --detach-sign file.iso # → file.iso.asc (ASCII-armored detached sig)
```

验证：

```sh
gpg --verify file.txt.asc                # clearsigned/embedded
gpg --verify file.iso.sig file.iso       # detached: signature first, file second
```

Sign-then-encrypt（同时保证身份与机密性）：

```sh
gpg --sign --encrypt --armor -r alice@example.com message.txt
```

为别人的密钥背书（Web of Trust）：

```sh
gpg --sign-key <their-fingerprint>                     # certify their key with yours
gpg --keyserver keyserver.ubuntu.com --send-key <their-fingerprint>  # publish your signature
```

其他几个值得记住的常用选项：

- `--armor` / `-a` — 输出 ASCII-armored（base64）格式而非二进制；适合贴在邮件正文里，但体积更大。
- `-r` — `--recipient` 的简写。
- `--output FILE` / `-o` — 写入文件而不是 stdout。
- `--list-sigs` — 列出每把密钥上挂着哪些签名（也就是 Web of Trust 的连边）。
- `--check-sigs` — 同时验证那些签名是否有效。

Git 集成（用 PGP key 给 commit 签名）：

```sh
git commit -S -a -m "Signed commit"
git log --show-signature -1
```

## 论文要点

### Whitten & Tygar (1996), "Why Johnny Can't Encrypt: A Usability Evaluation of PGP 5.0"

**研究问题**。一般消费软件的 UI 设计原则，足以让安全软件变得"好用"吗？他们挑了 PGP 5.0——当时被公认为设计最好的密码学产品——来当试验对象。

**方法**。两条互补路径：
1. 针对 PGP 5.0 的 UI 做 **cognitive walkthrough**，对照一套针对安全场景的可用性标准。
2. **实验室用户测试**：12 名来自典型邮件用户群的参与者。场景是某个竞选活动协调人，必须在 90 分钟内、用 Eudora + PGP 插件、只有最少的文档支持下，给团队成员发出已签名并加密的更新。

**他们识别出的安全软件特殊属性**（这是论文真正的概念核心）：
1. **Unmotivated user** — 安全只是次要目标；用户真正想做的是发邮件，不是管理密钥。
2. **Abstraction** — 密钥、trust 等级、validity 等级，对非程序员来说都是非常抽象、非常陌生的概念。
3. **Lack of feedback** — 安全状态本来就难以总结成简单的视觉反馈，而且什么算"对的配置"还取决于只有用户自己知道的意图。
4. **Barn door** — 一旦秘密泄露，哪怕只是短短一瞬间，你也无法保证没人趁机抓走它。错误是不可逆的。
5. **Weakest link** — 任何一个环节出错，整套系统就垮了；用户必须被引导着关注*每一个*环节。

**90 分钟用户测试的关键发现**：
- 在规定时间内，只有少数参与者真正成功发出了一封正确签名并加密的邮件。
- 有几个参与者用*自己*的公钥而不是收件人的公钥去加密，结果完全失去意义。
- 参与者把 signing 和 encryption 弄混，把 "validity" 和 "trust" 弄混（论文 4.4 节专门指出这一点的危险性，因为 PGP 会从 trust signatures 自动推导出 validity）。
- 有些人以为自己加密了，结果不小心把明文发了出去——而且没有任何回头的余地。
- 还有些人压根没意识到自己得先拿到对方的公钥才行。

**结论**。即便按一般标准来看 PGP 5.0 已经设计得不错，它的 UI 也仍然达不到有效安全所要求的可用性标准。安全需要*领域专属*的 UI 设计原则。这是 usable-security 这一研究方向的奠基之作；"Why Johnny Can't X" 后来在这个领域里成了反复出现的标题模板。

### Fahl et al. (2012), "Why Eve and Mallory Love Android: An Analysis of Android SSL (In)Security"

**研究问题**。从开发者角度上对 Whitten & Tygar 的一个补充：当开发者*确实*选择用 TLS 时，他们用对了吗？

**方法**。三件事：
1. 对 13,500 个流行的免费 Android app 做**静态分析**，使用一款自研工具（`MalloDroid`，基于 Androguard 的扩展），它会标出非默认的 `TrustManager`、过于宽松的 hostname verifier、自定义 `SSLSocketFactory`。
2. 在受控网络下，对其中挑出来的 100 个 app 做**手动审计 + active MITM attack**。
3. 针对 754 名 Android 用户，做了一份关于证书警告和 HTTPS 视觉指示器的**在线问卷**。

**关键发现**：
- **1,074 / 13,500（8.0%）** 的 app 中包含会接受所有证书或所有 hostname 的 SSL 代码——具备 MITM 风险。
- 手动审计的 100 个 app 里 **41 个可被实际利用**：作者捕获到了 American Express、Diners Club、PayPal、Facebook、Twitter、Google、Yahoo、Microsoft Live ID、银行账户、IBM Sametime、邮箱账户以及远程控制服务器的凭据。
- 一款杀毒 app 被骗去接受了被注入的病毒签名——他们可以把任意 app 标成恶意，或者直接关掉检测。
- 已确认有漏洞的 app 累计安装量在 **3,950 万到 1.85 亿用户**之间。
- **378 / 754（50.1%）** 的问卷参与者无法正确判断一次浏览会话是否处于 SSL 保护下。
- **419 / 754（55.6%）** 的人从来没见过证书警告，并且把它所警告的风险评估为中到低。

**为什么这件事重要**。TLS 在原理上是非常强的，但 API 表面允许开发者悄悄地把 validation 关掉（最常见的理由是为了让自签证书在开发环境跑得起来），然后在发布版里再也没把它打开。这条教训和 Whitten 是一脉相承的：密码学的安全性归根结底取决于配置它的人；而配置环节的 UX——对*用户*和*开发者*都一样——才是真正的瓶颈。

## Lab 实操

Lab 直接在实验室机器上做（不用 VM）。下面例子里的 François Dupressoir / Jo Hallett 替换成你的同伴和你自己即可。

### 1. Generate a key

先看看你是不是已经有一把了：

```sh
gpg --list-secret-keys
```

如果是空的，就生成一对新密钥：

```sh
gpg --full-generate-key
```

推荐回答：
- Kind：**RSA and RSA**（默认）
- Size：**4096 bits**
- Expiry：**1 year**（`1y`）
- Real name + 你的常用邮箱
- Comment：常用的用户名（如果有），没有就留空
- 用强 passphrase，存到密码管理器里

确认一下：

```sh
gpg --list-secret-keys
```

那串 40 位十六进制字符就是 **fingerprint** / key id——记下来，后面要用。

**为什么是这些默认值？** 2048 bits 目前仍被认为安全；4096 bits 是更稳妥的默认；8192 除了最偏执的人之外都属于杀鸡用牛刀。1 年到期可以把丢失密钥的损失锁在一年内；只要密钥还在你手里，随时能延期。

### 2. Make a revocation certificate

立刻做这一步。把生成出的文件存到一个离线的地方（U 盘、加密备份）——如果哪天你弄丢了密钥，这是你唯一能告诉全世界"别再用了"的方式。

```sh
gpg --output revoke.asc --armor --gen-revoke '<your fingerprint>'
```

执行的过程中 GPG 会打印一段说明，认真读一遍——它把"为什么需要"和"该怎么用"都讲得很清楚。

### 3. Update expiry on an existing key

如果一把密钥快到期了而它还在你手里：

```sh
gpg --edit-key '<your fingerprint>'
```

然后在交互提示里：

```text
gpg> expire
… answer: 2y …
gpg> save
```

`--edit-key` 里还有一些值得玩玩的东西：输入 `help` 列出所有命令，`addphoto` 可以把你自己的 JPEG 照片嵌进密钥里。

### 4. Distribute your key

推送到 keyserver：

```sh
gpg --keyserver keyserver.ubuntu.com --send-keys '<your fingerprint>'
```

通过 fingerprint 拉一个朋友的公钥下来：

```sh
gpg --keyserver keyserver.ubuntu.com --recv-keys '<their fingerprint>'
```

按名字搜索（注意：搜索结果**完全没有经过验证**——任何人都可以以别人的名义上传一把假密钥）：

```sh
gpg --keyserver keyserver.ubuntu.com --search-key 'Jo Hallett'
```

**交付物**：和身边的人当面交换 fingerprint，互相导入对方的公钥。后面的所有步骤都要靠它。

### 5. Send an encrypted message

写一个明文文件 `~/message.txt`，加密它：

```sh
gpg --encrypt --recipient 'friend@example.com' ~/message.txt
# → ~/message.txt.gpg (binary)
```

GPG 会提示 `There is no assurance this key belongs to the named user`，因为你还没给朋友的密钥签过名——目前先回 `y`，下一步会修复这件事。

如果想要邮件里能直接贴的 ASCII-armored 版本：

```sh
gpg --armor --encrypt --recipient 'friend@example.com' ~/message.txt
# → ~/message.txt.asc
```

对比一下大小（armored 版本更大但是可以粘贴）：

```sh
du -b ~/message.*
```

试着解密自己刚加密出来的消息——你会失败，因为它是用朋友的公钥加密的，不是你的：

```sh
gpg --decrypt ~/message.txt.asc
# gpg: decryption failed: No secret key
```

把 `.asc` 的内容贴到邮件里发出去（lab 文件夹里的 `hello-françois.png` 截图就是它在邮件客户端里大致的样子）。

**练习**：给你身边的人发一封加密邮件或文件；让对方解密看看。

### 6. Key-signing party

朋友回信之后，你需要证明那把密钥真的是你的，他才能放心给你签名。先给对方看你这边持有的、属于他的那把公钥：

```sh
gpg --list-key friend@example.com
```

把屏幕上显示的 fingerprint 和朋友亲口念出来 / 自己屏幕上显示的那一串做对比。**两边的指纹必须一字不差地完全一致**。如果一致，就给对方签名：

```sh
gpg --sign-key '<their fingerprint>'
```

依次回答 `Really sign all user IDs? (y/N) y` 和 `Really sign? (y/N) y`。然后把你的签名推回 keyserver，让其他人也能从你的背书中受益：

```sh
gpg --send-key '<their fingerprint>'
```

这样一来，所有原本就信任你的人，都会传递性地也信任你这位朋友的密钥。

**练习**：在房间里走一圈，挨个核对 fingerprint 并互相给对方密钥签名——这就是 key-signing party。

### 7. Sign-then-encrypt email

光加密只能证明*机密性*，不能证明*作者身份*——任何持有收件人公钥的人都能写出这样一封密文。要证明是你写的，就得再用自己的私钥签个名：

```sh
gpg --output message.sig --clearsign message.txt
gpg --output message.gpg --armor --encrypt --recipient friend@example.com message.txt
```

确认 clearsigned 文件里嵌着签名：

```sh
gpg --verify message.sig
```

看到 `Good signature from "Your Name …"` 就说明：自从你签名之后这条消息没有被改动过。

**练习**：签完名之后再去改 `message.txt`，但不要重新签名，再次运行 `gpg --verify`。这次你应该会看到 `BAD signature`——签名机制能抓出篡改。

**练习**：互相发签名*并*加密的邮件，并完成解密 + 验证。

### 8. `--clearsign` vs `--sign` vs `--detach-sign`

- `--clearsign` — 把原文 + 签名包成一份 ASCII 文件。适合贴在论坛帖、邮件里。
- `--sign` — 输出一份二进制文件，把原文档和签名嵌在一起。
- `--detach-sign` — 只输出签名，单独成一个文件。这是 ISO 这类下载场景常用的方式：你希望原文件本身保持不动。

### 9. Verify a real-world signed download (Debian ISO)

按 `https://www.debian.org/CD/verify` 上的官方流程走一遍：

1. 下载你想要的 ISO 镜像。
2. 下载对应的 `SHA512SUMS` 和 `SHA512SUMS.sign`。
3. 导入 Debian 的签名密钥（页面上有说明）。
4. 验证 checksums 文件上的签名：

```sh
gpg --verify SHA512SUMS.sign SHA512SUMS
```

5. 验证你下载的 ISO 是不是和预期 hash 一致：

```sh
sha512sum -c SHA512SUMS 2>&1 | grep OK
```

你不用真去装 Debian——把验证流程跑一遍才是交付物。Fedora、Arch、签了名的 Git tag 也都是同一个套路。

### 10. Optional further exploration

- `Enigmail`（Thunderbird）或 `Mutt` + `offlineimap` 实现透明的加密邮件。
- `pass`（`https://www.passwordstore.org`）—— 把密码存成一个 Git repo 里的小型 GPG 加密文件。
- `gpg-agent` —— 缓存 passphrase，让你不用反复输入；还能顺手管理 SSH 密钥（详见 GnuPG 手册的 `Invoking GPG-AGENT` 一节）。

## 易错点与重点

**保护私钥这件事胜过一切**。
- 永远不要把它复制到共享盘，永远不要粘贴到聊天里，永远不要邮件发送。
- `gpg --export-secret-keys` 导出来的文件就是皇冠上的明珠；一旦落入他人之手，对方就能冒充你，并解密所有曾经发给你的消息。
- 留一份离线备份（保险柜里的 U 盘），并且要和 revocation certificate 分开存放。

**Passphrase 不等于"加密本身"**。
- 你的 passphrase 只保护硬盘上的私钥文件，让偷你笔记本的人解不开。
- 它*不会*保护你的密文。如果攻击者同时拿到了私钥文件*和* passphrase，那么所有曾经加密给你的消息都能被解开。
- 选一个能扛住 offline cracking 的强 passphrase；然后存到密码管理器里。

**Trust 和 validity 是两回事**。
- *Validity*：我能不能确定这把密钥真的属于那个人？（在核对 fingerprint 之后通过给密钥签名来设置。）
- *Trust*：我相不相信这个人在给别人的密钥签名时是认真的？（用于通过 Web of Trust 间接推导出*第三方*密钥的 validity。）
- Whitten & Tygar 专门点了 PGP 5.0 把这两个概念混在一起的名——用户在看 "validity" 时把 "trust" 设错了，结果信任了不该信任的密钥。把对话框看清楚。

**Signing 和 encrypting 容易混淆**。
- Encrypt = 用*对方的 public* key → 只有对方能读。
- Sign = 用*自己的 private* key → 任何人都能验证是你写的。
- "给自己加密" 是个非常真实的脚踩雷区：如果你 `-r` 自己邮箱，相当于把这条消息保护起来不让任何人读——*除了你自己*——而当你想发给 Alice 时，这恰恰是反效果。
- 想要既保密又可归因：`--sign --encrypt --recipient alice@…`。两个 flag 都加上。

**给别人密钥签名前一定要 out-of-band 核对 fingerprint**。
- 从 keyserver 上拿到的密钥本身没有任何关于"它实际属于谁"的信息。
- Fingerprint 必须当面核对、电话里念、印在名片上、贴在已认证的 Twitter 账号下——*绝对不能*通过你拿到密钥的同一封邮件 / 网站去核对（MITM 完全可以两边都给你换掉）。
- Lab 里那首小诗（"There was a young man with a key, who didn't check others keys carefully…"）讲的就是这件事。

**Revocation certificate 第一天就生成**。
- 如果你弄丢了私钥（笔记本坏了、passphrase 忘了）又没有 revocation cert，那把密钥就会永远挂在 keyserver 上，别人会继续用它加密消息发给你——而你再也读不了。
- 如果实在不放心电子存储，把 revocation cert 打印出来塞抽屉里也行。它就那么点儿大。

**记得设 expiry**。
- 即便有 revocation cert，有限的有效期也是一道额外保险。要是哪天你彻底从地球上消失了，那把密钥也会自动失去信任。
- 给一把还活着的密钥延长有效期就是 `--edit-key` 的一行操作，零成本。

**记住：keyserver 是 append-only 的**。
- 一旦 `--send-keys` 出去，这把密钥就会永远存在多个镜像上。
- 不要拿一次性密钥上去做实验——那些条目是抹不掉的。
- Revocation 只能把它们标记为"已死"，但不会把它们删掉。

**两篇论文给出的整体启示**。
- Whitten：UI 漂亮远远不够——安全软件需要*领域专属*的设计，否则用户会在悄无声息中犯下灾难性的错误。
- Fahl：哪怕底层 primitive 本身是正确的（TLS），实际部署时也常常被错误配置毁掉；一个让你"轻易关掉 validation"的库 API，本身就是攻击面的一部分。
- 不论是构建还是使用 crypto，都要假设那个人（开发者也好、终端用户也好）是最薄弱的一环，照着这个前提去设计或行事。
