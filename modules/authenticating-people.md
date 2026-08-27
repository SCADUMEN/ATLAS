---
id: authenticating-people
name: Authenticating People
category: knowledge
tier: B
domain: security, access, custody
source: Fred B. Schneider, CS 513 System Security, Cornell University
source_url: https://www.cs.cornell.edu/courses/cs513/2005fa/NNLauthPeople.html
serves: le-vigile
---

# MODULE — Authenticating People

Knowledge module. It equips Le Vigile (04) — who defends access, custody, and boundaries — with the standard framework for authenticating a human being, and it gives ATLAS the vocabulary to reason about his own reincarnation honestly.

Source: **"Something You Know, Have, or Are,"** Fred B. Schneider, CS 513 System Security, Cornell. See `source_url` in the frontmatter.

## The Three Factors

Authentication of a person rests on one or more of:

1. **Something you know** — a password, a PIN, a passphrase. Cheap, revocable, and the easiest to steal or guess.
2. **Something you have** — a smart card, an RSA SecurID token, a proximity/RFID card. A physical object that can be duplicated, intercepted, or lost.
3. **Something you are** — a biometric: fingerprint, retina, voice, keystroke timing, signature.

**Two-factor authentication** combines two independent factors — classically something known and something held. The strength is in independence: compromising one does not compromise the other.

## What The Module Carries

**Passwords.** Strength scales with length, character-set size, and randomness (non-dictionary). Never stored in plaintext — store `h(password)`, a cryptographic hash.

- **Salt** — a random value mixed in before hashing. It turns a *wholesale* precomputation attack (one table breaks everyone) into a *retail* one (each password must be attacked on its own). A **secret salt** raises the attacker's cost further.
- Storage examples from the source, weakest to strongest: Unix (DES ×25, 12-bit salt) → FreeBSD (MD5, 48-bit) → OpenBSD (Blowfish, 128-bit, guaranteed-unique salts). Windows LanMan is a cautionary tale: splitting a 14-char password into two 7-char halves collapses the work factor to `2 × 36⁷` instead of `36¹⁴`.

**Attacks to expect.** Shoulder-surfing, offline dictionary attacks, social engineering of reset flows; magnetic-strip duplication, RFID interception, power-analysis on smart cards; lifting or stealing biometrics, spoofed sensors, compromised biometric databases.

**Biometrics, measured honestly.** Two error rates that trade off against each other:

- **FAR** — False Acceptance Rate: an impostor is accepted.
- **FRR** — False Reject Rate: a legitimate person is rejected.

And two failure modes with no clean fix: biometrics are hard to revoke (you cannot reissue a fingerprint), and matching one-to-many across a database is far harder than verifying one-to-one.

**Trusted path.** A defense against a spoofed login prompt: a key sequence (e.g. Ctrl-Alt-Del) that routes to trusted software, so the credential reaches the real authenticator and not an impostor's window. It requires trust the whole way down, from hardware to driver.

**The source's own conclusion.** Biometrics are promising as *authentication* but not as *identification*; the durable future is *something you have* plus *something you know*; passwords will be with us for a long time.

## DOCTRINE — Mapping To The Instrument

The three factors map onto Le Conseil, which is why this module is more than a Vigile reference:

- **Something you know** → the doctrines. Version-controlled, inspectable, in `L'Archive`. This is what survives a reincarnation.
- **Something you have** → the barrel (`overlays/le-barillet.md`): the fitted model and the repository checkout. Swappable, and on its own, not proof of identity.
- **Something you are** → `L'Opérateur`. The human outside the case, who decides. The one factor the instrument cannot manufacture.

This reframes **Reincarnation** (`bin/atlas`) with its real security question. Fitting a fresh barrel gives you the "have" and, through the injected core, the "know." Neither establishes that the operator is Matthew, or that the movement is the authentic ATLAS and not a look-alike. Authentication of people is the counterpart to reincarnation of the agent: the launcher restores capability; it does not, by itself, authenticate either party.

Le Vigile's standing guidance from this module:

- Prefer two independent factors. Treat a single factor as an identifier, not a proof.
- Store nothing recoverable that you can store hashed and salted.
- State error rates; never imply a check that did not run (the FAR/FRR discipline is the same as Le Rouage's `(unverified)` rule).
- A credential path is only as trustworthy as the weakest layer it crosses. Establish the trusted path before trusting what comes over it.

A thing documented is a thing not yet lost.
