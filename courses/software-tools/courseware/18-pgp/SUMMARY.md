# Chapter 18 — PGP / GPG encryption

## Overview

This chapter is a tour of public-key cryptography from "what problem does it solve" to "how do I use the tools day-to-day". The lecture starts with a motivating example (buying a t-shirt online and entering a credit card number) to argue that pre-shared passwords cannot scale to billions of users, and that **public-key cryptography** is what actually makes the modern web work. From there it walks through three concrete uses of public-key crypto:

- **OpenSSH** — login authentication (key + challenge / `~/.ssh/authorized_keys`).
- **OpenSSL / TLS** — server identity & encrypted transport, validated through a centralised root of trust (`/etc/ssl/certs/ca-certificates.crt`, ~150 CAs, certificate chains, Let's Encrypt + ACME).
- **PGP / GnuPG** — authenticating *people* (email, signed Git commits, signed Debian/Fedora ISOs), validated through a decentralised **Web of Trust** instead of CAs.

Because the lab is the assessed deliverable, the bulk of this chapter is GPG: generating a key, distributing it via keyservers, encrypting and signing messages, key-signing parties, verifying downloads. The two papers (Whitten & Tygar 1996, Fahl et al. 2012) are the usability counterweight: even excellent crypto fails if the UI is wrong or the developers configure it wrong.

## Core knowledge

### Symmetric vs asymmetric crypto

- **Symmetric**: one shared secret encrypts and decrypts. Fast, but you need a secure channel to share the key first — which is the chicken-and-egg problem public-key crypto solves.
- **Asymmetric (public-key)**: a *pair* of keys. The **public key** can be published; the **private (secret) key** never leaves the owner. What one encrypts the other decrypts. Slides describe the maths abstractly as a problem that is "Hard to solve, Easy to check, Doesn't leak". RSA, ElGamal, DSA, Elliptic Curve are different concrete instances.
- In practice systems are **hybrid**: public-key crypto is used to exchange a symmetric session key, and the symmetric key encrypts the bulk data. PGP works exactly like this internally.

### Public/private keys, digital signatures, fingerprints, Web of Trust

- **Encryption direction**: encrypt with the recipient's *public* key → only the holder of the matching *private* key can decrypt.
- **Signature direction**: sign with your own *private* key → anyone with your *public* key can verify it was you. The slides express it via RSA: since `(m^e)^d ≡ m (mod n)`, you can equally compute `m^d` and let anyone check it via `e` — that signed value is the signature.
- **Fingerprint**: a short hash of the public key (e.g. `7860 0FD9 AF8A 5307 BE9D C633 26BB 2BE0 FD06 DFA9`). Comparing fingerprints out-of-band (face-to-face, phone) is how you establish that a downloaded key really belongs to the named person.
- **Web of Trust** (PGP's answer to CAs): you trust yourself; if you've checked someone in person you sign their key; if you trust someone who has signed a third party's key, you can transitively gain confidence in that third party. There is no central authority — trust is a graph, not a tree. Built up in practice through "key-signing parties".

### PGP history & the OpenPGP standard

- **PGP** = Pretty Good Privacy, written by Phil Zimmermann in 1991 (slides say 1996, which is the era of PGP 5.0). Originally got Zimmermann investigated under US export-control laws because strong crypto counted as a munition.
- The format and protocols were standardised as **OpenPGP** (RFC 4880 and successors), and **GnuPG (GPG)** is the dominant free implementation.
- PGP/GPG is still illegal or restricted in some countries; export of strong crypto is a real-world political issue, not just a technical one.

### End-to-end encrypted email workflow

The whole pipeline, in order:

1. **Generate** a keypair locally (`gpg --full-generate-key`). Choose RSA+RSA, 4096 bits, 1-year expiry. Set name + email; protect with a strong passphrase.
2. **Generate a revocation certificate** immediately and store it offline — this is your "kill switch" if you lose the key.
3. **Distribute** your public key — upload to a keyserver (`--send-keys`) and/or hand it directly to correspondents.
4. **Acquire** other people's public keys (`--recv-keys`, `--search-key`) and **verify their fingerprints** out-of-band before trusting them.
5. **Encrypt** messages with the recipient's public key (`gpg --encrypt -r alice@example.com file.txt`).
6. **Sign** messages with your own private key (`gpg --sign` / `--clearsign` / `--detach-sign`). Combine: sign-then-encrypt to prove authorship + ensure secrecy.
7. **Verify** received signatures (`gpg --verify`).
8. **Decrypt** received ciphertext with your private key (`gpg --decrypt`).

### Keyservers, revocation, expiry

- **Keyservers** (e.g. `keyserver.ubuntu.com`) are public databases mapping identities → public keys. Anyone can publish, anyone can fetch. Note: keyservers are append-only — you cannot remove a key once published, only mark it revoked.
- **Revocation certificate**: a signed statement saying "this key is no longer valid". Generate it the same day you generate the key, store it somewhere safe (USB stick, printout in a drawer). Without it, if you lose your private key you have no way to tell the world to stop trusting it.
- **Expiry**: set a finite lifetime (e.g. 1 year). If you lose the key and have no revocation cert, at least the damage is bounded. You can always extend the expiry of a key you still control via `gpg --edit-key … expire`.

### Hash functions and signatures

- A digital signature does not encrypt the whole message with the private key (which would be slow and bloat the output). Instead the message is **hashed** with a cryptographic hash function (SHA-256, SHA-512 — never MD5 or SHA-1 for new work) and the hash is what gets encrypted with the private key.
- This means signatures are short and fixed-length regardless of message size, and verification is fast.
- It also means hash collisions break signatures: if an attacker can find two messages with the same hash, they can substitute one for the other under a valid signature. This is why old hash algorithms get retired.

### Usability problems (papers)

The two assigned papers form the cautionary tale around all this:

- **Whitten & Tygar (1996)** — even when PGP's GUI was polished by general consumer-software standards, most novices given 90 minutes could not encrypt and sign an email correctly. Security has special usability properties (unmotivated users, abstraction, lack of feedback, the "barn door", weakest link) that ordinary UI design heuristics don't address.
- **Fahl et al. (2012)** — even when developers do reach for TLS, they routinely misconfigure it. 1,074 of 13,500 Android apps were found to be MITM-vulnerable, 41 of 100 manually audited apps leaked credentials over a forged TLS connection. Crypto has usability problems for *developers*, not just end users.

## GPG command cheat sheet

Key generation and inspection:

```sh
gpg --full-generate-key                          # interactive wizard (most options)
gpg --gen-key                                    # quick wizard with sane defaults
gpg --list-keys                                  # all public keys you know about
gpg --list-secret-keys                           # private keys you control
gpg --fingerprint <user-or-keyid>                # show the fingerprint
gpg --edit-key <keyid>                           # interactive edit (expire, addphoto, sign, trust, …)
```

Inside `--edit-key` the useful subcommands are:

```text
help        # list everything
expire      # change expiry of primary key
trust       # set how much YOU trust this key as a certifier
sign        # sign this key with yours
addphoto    # embed a JPEG in the key
addrevoker  # designate a revoker
quit        # save & exit
```

Generating a revocation certificate and changing expiry:

```sh
gpg --output revoke.asc --armor --gen-revoke <keyid>     # do this on day 1, store offline
gpg --edit-key <keyid>                                   # then `expire`, `2y`, `y`, `save`
```

Distributing keys (keyservers):

```sh
gpg --keyserver keyserver.ubuntu.com --send-keys <keyid>
gpg --keyserver keyserver.ubuntu.com --recv-keys <keyid>
gpg --keyserver keyserver.ubuntu.com --search-key 'Jo Hallett'
```

Exporting / importing (offline transfer or backup):

```sh
gpg --armor --export <keyid> > my-public.asc             # ASCII-armored public key
gpg --armor --export-secret-keys <keyid> > my-secret.asc # PRIVATE — guard this
gpg --import alice-public.asc                            # import someone else's key
```

Encrypting and decrypting:

```sh
gpg --encrypt --recipient alice@example.com message.txt          # → message.txt.gpg (binary)
gpg --armor --encrypt --recipient alice@example.com message.txt  # → message.txt.asc (base64)
gpg --decrypt message.txt.asc                                    # to stdout
gpg --output plain.txt --decrypt message.txt.asc                 # to file
```

Signing variants:

```sh
gpg --sign file.txt                # → file.txt.gpg (binary, file embedded)
gpg --clearsign file.txt           # → file.txt.asc (file readable, signature appended)
gpg --detach-sign file.iso         # → file.iso.sig (signature in a separate file)
gpg --armor --detach-sign file.iso # → file.iso.asc (ASCII-armored detached sig)
```

Verifying:

```sh
gpg --verify file.txt.asc                # clearsigned/embedded
gpg --verify file.iso.sig file.iso       # detached: signature first, file second
```

Sign-then-encrypt (authenticity + confidentiality):

```sh
gpg --sign --encrypt --armor -r alice@example.com message.txt
```

Endorsing someone else's key (Web of Trust):

```sh
gpg --sign-key <their-fingerprint>                     # certify their key with yours
gpg --keyserver keyserver.ubuntu.com --send-key <their-fingerprint>  # publish your signature
```

Other useful flags worth remembering:

- `--armor` / `-a` — output ASCII-armored (base64) instead of binary; safe for email body, larger.
- `-r` — short for `--recipient`.
- `--output FILE` / `-o` — write to file instead of stdout.
- `--list-sigs` — show signatures on each key (the Web of Trust links).
- `--check-sigs` — also verify those signatures.

Git integration (signs commits with your PGP key):

```sh
git commit -S -a -m "Signed commit"
git log --show-signature -1
```

## Paper takeaways

### Whitten & Tygar (1996), "Why Johnny Can't Encrypt: A Usability Evaluation of PGP 5.0"

**Research question.** Are general consumer-software UI principles sufficient to make security software usable? They picked PGP 5.0 — generally regarded as the best-designed crypto product of the day — as the test case.

**Method.** Two complementary techniques:
1. **Cognitive walkthrough** of the PGP 5.0 UI against a security-specific usability standard.
2. **Laboratory user test**: 12 participants representative of typical email users. Scenario: campaign coordinator who must send signed-and-encrypted updates to team members within 90 minutes, given Eudora + the PGP plug-in and minimal documentation.

**Security-specific properties they identified** (these are the conceptual core of the paper):
1. **Unmotivated user** — security is a secondary goal; users are trying to send email, not to manage keys.
2. **Abstraction** — keys, trust ratings, validity ratings are abstract concepts non-programmers find alien.
3. **Lack of feedback** — security state is hard to summarise and the "right" configuration depends on intent only the user knows.
4. **Barn door** — once a secret leaks, even briefly, you can never be sure no attacker grabbed it. Errors are unrecoverable.
5. **Weakest link** — one mistake anywhere breaks the whole system; users must be guided to attend to *every* aspect.

**Headline findings from the user test (90 minutes):**
- Only a minority of participants successfully sent a correctly signed and encrypted message in the time available.
- Several participants encrypted a message with their *own* public key instead of the recipient's, defeating the point.
- Participants confused signing with encryption, "validity" with "trust" (the paper's section 4.4 calls this dangerous because PGP auto-derives validity from trust signatures).
- Some accidentally emailed unencrypted plaintext after thinking they'd encrypted it — and there was no way to recover.
- Some never figured out that they had to obtain the recipient's public key first.

**Conclusion.** PGP 5.0's UI does not meet the usability standard required for effective security, despite being well-designed by general standards. Security needs *domain-specific* UI design principles. This is the foundational paper of usable-security research; "Why Johnny Can't X" became a recurring title pattern in the field.

### Fahl et al. (2012), "Why Eve and Mallory Love Android: An Analysis of Android SSL (In)Security"

**Research question.** A complement to Whitten & Tygar from the developer side: when developers *do* reach for TLS, are they using it correctly?

**Method.** Three pieces:
1. **Static analysis** of 13,500 popular free Android apps, using a custom tool (`MalloDroid`, an Androguard extension) that flags non-default `TrustManager`s, permissive hostname verifiers, custom `SSLSocketFactory`s.
2. **Manual audit + active MITM attacks** against 100 selected apps on a controlled network.
3. **Online survey** of 754 Android users about certificate warnings and HTTPS visual indicators.

**Headline findings:**
- **1,074 / 13,500 (8.0%)** apps contain SSL code that accepts all certificates or all hostnames — potentially MITM-vulnerable.
- **41 of 100** manually audited apps were exploitable: the authors captured credentials for American Express, Diners Club, PayPal, Facebook, Twitter, Google, Yahoo, Microsoft Live ID, bank accounts, IBM Sametime, email accounts, and remote-control servers.
- One antivirus app was tricked into accepting injected virus signatures — they could mark arbitrary apps as malware or disable detection.
- Cumulative install base of confirmed-vulnerable apps: between 39.5 and 185 million users.
- **378 / 754 (50.1%)** survey participants could not correctly judge whether a browser session was protected by SSL.
- **419 / 754 (55.6%)** had never seen a certificate warning before, and rated the risk it warns against as medium-to-low.

**Why this matters.** TLS is in principle strong, but the API surface lets developers silently disable validation (commonly to make self-signed dev certs work) and never re-enable it for release. The lesson echoes Whitten: cryptography is only as good as the people configuring it, and the configuration UX — for both users *and* developers — is the bottleneck.

## Lab walkthrough

The lab targets the lab machines directly (no VM). Replace François Dupressoir / Jo Hallett in the examples with a friend and yourself.

### 1. Generate a key

Check you don't already have one:

```sh
gpg --list-secret-keys
```

If empty, generate a new keypair:

```sh
gpg --full-generate-key
```

Recommended answers:
- Kind: **RSA and RSA** (default)
- Size: **4096 bits**
- Expiry: **1 year** (`1y`)
- Real name + your default email
- Comment: a common username if you have one, otherwise blank
- Strong passphrase, stored in a password manager

Confirm:

```sh
gpg --list-secret-keys
```

The 40-hex-character string is the **fingerprint** / key id — note it down, you'll need it.

**Why these defaults?** 2048 bits is currently believed safe; 4096 bits is the cautious default; 8192 is overkill except for the most paranoid. 1-year expiry bounds damage if the key is lost; you can always extend it later if it's still under your control.

### 2. Make a revocation certificate

Do this immediately. Store the output file somewhere offline (USB stick, encrypted backup) — if you ever lose your key, this is the only way to tell the world.

```sh
gpg --output revoke.asc --armor --gen-revoke '<your fingerprint>'
```

Read what GPG prints during this step — it explains exactly why you need it and how to use it.

### 3. Update expiry on an existing key

If a key is about to expire and you still control it:

```sh
gpg --edit-key '<your fingerprint>'
```

Then inside the prompt:

```text
gpg> expire
… answer: 2y …
gpg> save
```

Other things worth poking at inside `--edit-key`: type `help` to list commands, try `addphoto` to embed a JPEG of yourself.

### 4. Distribute your key

Push to a keyserver:

```sh
gpg --keyserver keyserver.ubuntu.com --send-keys '<your fingerprint>'
```

Pull a friend's key by fingerprint:

```sh
gpg --keyserver keyserver.ubuntu.com --recv-keys '<their fingerprint>'
```

Search by name (note: search results are NOT verified — anyone could have uploaded a fake key in someone else's name):

```sh
gpg --keyserver keyserver.ubuntu.com --search-key 'Jo Hallett'
```

**Deliverable**: talk to the people next to you, exchange fingerprints in person, and import each other's keys. You need them for everything that follows.

### 5. Send an encrypted message

Write a plaintext file `~/message.txt`. Encrypt it:

```sh
gpg --encrypt --recipient 'friend@example.com' ~/message.txt
# → ~/message.txt.gpg (binary)
```

GPG will warn `There is no assurance this key belongs to the named user` because you haven't signed your friend's key yet — answer `y` for now, you'll fix this in the next step.

For an email-friendly ASCII-armored version:

```sh
gpg --armor --encrypt --recipient 'friend@example.com' ~/message.txt
# → ~/message.txt.asc
```

Confirm sizes (the armored version is bigger but pasteable):

```sh
du -b ~/message.*
```

Try to decrypt your own message — it will fail because it's encrypted to your friend's public key, not yours:

```sh
gpg --decrypt ~/message.txt.asc
# gpg: decryption failed: No secret key
```

Copy the `.asc` body into an email and send it (the `hello-françois.png` screenshot in the lab folder shows what this looks like in a mail client).

**Exercise**: send the person next to you an encrypted message or file; check they can decrypt it.

### 6. Key-signing party

After your friend replies, prove your key really belongs to you so they can sign it. Show them the public key you have for them:

```sh
gpg --list-key friend@example.com
```

Compare the fingerprint shown against the one your friend reads out loud / shows on their screen. **The fingerprints must match exactly**, character for character. If they do, sign the key:

```sh
gpg --sign-key '<their fingerprint>'
```

Confirm `Really sign all user IDs? (y/N) y` and `Really sign? (y/N) y`. Then push your signature back to the keyserver so others benefit from your endorsement:

```sh
gpg --send-key '<their fingerprint>'
```

Now anyone who already trusts you will, transitively, trust your friend's key.

**Exercise**: go round the room verifying fingerprints and signing each other's keys — the key-signing party.

### 7. Sign-then-encrypt email

Encrypting alone proves *secrecy* but not *authorship* — anyone with the recipient's public key could have written it. To prove you wrote it, sign with your private key as well:

```sh
gpg --output message.sig --clearsign message.txt
gpg --output message.gpg --armor --encrypt --recipient friend@example.com message.txt
```

Verify the clearsigned message contains its signature inline:

```sh
gpg --verify message.sig
```

A `Good signature from "Your Name …"` line means the message has not been altered since you signed it.

**Exercise**: edit `message.txt` after signing it without resigning, and run `gpg --verify` again. You should now get `BAD signature` — the signature catches tampering.

**Exercise**: send each other signed *and* encrypted email and decrypt + verify it.

### 8. `--clearsign` vs `--sign` vs `--detach-sign`

- `--clearsign` — wraps the original text + signature in one ASCII file. Good for forum posts and email.
- `--sign` — writes a binary file containing the original document and the signature, embedded together.
- `--detach-sign` — writes only the signature, in a separate file. This is what's used for things like ISO downloads, where you want the original artefact untouched.

### 9. Verify a real-world signed download (Debian ISO)

Walk through the official process at `https://www.debian.org/CD/verify`:

1. Download the ISO image you want.
2. Download the matching `SHA512SUMS` and `SHA512SUMS.sign` files.
3. Import the Debian signing keys (instructions on that page).
4. Verify the signature on the checksums file:

```sh
gpg --verify SHA512SUMS.sign SHA512SUMS
```

5. Verify your downloaded ISO matches the expected hash:

```sh
sha512sum -c SHA512SUMS 2>&1 | grep OK
```

You don't have to actually install Debian — going through the verification flow is the deliverable. Same idea applies to Fedora, Arch, signed Git tags, etc.

### 10. Optional further exploration

- `Enigmail` (Thunderbird) or `Mutt` + `offlineimap` for transparent encrypted email.
- `pass` (`https://www.passwordstore.org`) — store passwords as small GPG-encrypted files in a Git repo.
- `gpg-agent` — caches your passphrase so you don't retype it constantly; can also manage SSH keys (see the GnuPG manual on `Invoking GPG-AGENT`).

## Pitfalls & emphasis

**Protect the private key above all else.**
- Never copy it to shared drives, never paste it into chat, never email it.
- The exported file from `gpg --export-secret-keys` is the crown jewels; if someone else gets it, they can impersonate you and decrypt everything ever sent to you.
- Keep an offline backup (USB drive in a safe), separate from the revocation certificate.

**The passphrase is not "the encryption".**
- Your passphrase only protects the on-disk private key file from someone who steals your laptop.
- It does *not* protect your ciphertext. If an attacker gets the private key file *and* the passphrase, every message ever encrypted to you can be decrypted.
- Choose a passphrase strong enough to resist offline cracking; then store it in a password manager.

**Trust levels are not validity.**
- *Validity*: am I sure this key really belongs to that person? (Set by signing the key after checking the fingerprint.)
- *Trust*: do I believe this person signs other people's keys carefully? (Used to derive validity for *third-party* keys via the Web of Trust.)
- Whitten & Tygar specifically called out PGP 5.0 for blurring these — users mis-set "trust" while looking at "validity" and ended up trusting bad keys. Read the dialogs.

**Signing vs encrypting confusion.**
- Encrypt = use *recipient's public* key → only they can read it.
- Sign = use *your private* key → anyone can verify you wrote it.
- "Encrypt for myself" is a real footgun: if you `-r` your own address you've protected the message from everyone *except yourself*, which is the opposite of useful when you wanted to email Alice.
- For confidential AND attributable email: `--sign --encrypt --recipient alice@…`. Both flags.

**Always verify fingerprints out-of-band before signing a key.**
- Receiving a key from a keyserver tells you nothing about who actually controls it.
- Fingerprints must match in person, by phone, on a printed business card, on Twitter under a verified account — *not* via the same email/website you got the key from (the MITM could have substituted both).
- The lab's poem ("There was a young man with a key, who didn't check others keys carefully…") is the entire point.

**Generate the revocation certificate on day one.**
- If you lose your private key (laptop dies, passphrase forgotten) and you have no revocation cert, your key sits on keyservers forever, and people will keep encrypting messages to it that you can no longer read.
- Print the revocation cert and put it in a drawer if you have to. It's small.

**Set an expiry.**
- Even with a revocation cert, finite expiry is belt-and-braces. If you ever drop off the face of the earth, the key automatically stops being trusted.
- Extending an active key is a one-line `--edit-key` operation, costs nothing.

**Remember: keyservers are append-only.**
- Once you `--send-keys`, the key is on multiple mirrors forever.
- Don't experiment by uploading throwaway keys — those entries are permanent.
- Revocation marks them dead but does not remove them.

**The big-picture lesson from the papers.**
- Whitten: a beautiful UI is not enough — security demands *domain-specific* design or users will silently make catastrophic errors.
- Fahl: even technically correct primitives (TLS) are routinely defeated by misconfiguration; library APIs that make it easy to disable validation are part of the attack surface.
- Whenever you're building or using crypto, assume the human (developer or end user) is the weakest link, and design or behave accordingly.
