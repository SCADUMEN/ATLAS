# Contributors

ATLAS is the work of two people and the models they worked with. The git history
carries six author identities for those two people, which makes `git log` a poor
place to learn who built what. This file is the readable version.

Figures below are from the commit record as of 2026-08-31: 56 commits,
2026-06-05 through 2026-08-31.

## Matthew Marx

**34 commits · 2026-06-05 → 2026-08-31 · the doctrine and the instruments**

Founded the repository and wrote the council: the subroutines, the routing
manifest, the operating overlays, and the field instruments that exercise them.

Principal areas: `overlays/le-conseil.md`, `ATLAS.md`, `subroutines/`,
`rouage/`, `hardware/le-boitier.md`, `FEEDBACK.md`.

Commits appear under four identity strings, all his:

| Identity | Commits | Window |
|---|---|---|
| `Matthew Taylor Marx <matthewmarx@users.noreply.github.com>` | 6 | 06-05 → 06-14 |
| `JOHN JUICESTER <jjammocan@JOHNs-MacBook-Pro.local>` | 9 | 08-15 → 08-16 |
| `Matthew T. Marx <bagelmanrichard@icloud.com>` | 18 | 08-16 → 08-31 |
| `Matthew Marx <lesauvegarder@gmail.com>` | 1 | 08-31 |

`JOHN JUICESTER <...@JOHNs-MacBook-Pro.local>` is not a separate contributor. It
is git's fallback identity — the account's full-name field plus `username@hostname`
— written into commits made before `user.name` was configured on that machine.
Left in place rather than rewritten: the history is the record.

## Tyler Etters

**22 commits · 2026-08-26 → 2026-08-29 · the case, the crown, and the release train**

Turned ATLAS from a private operating layer into a distributable Claude Code
plugin, and generalized it off its author's name so that anyone could be the
Operator.

His arc, in order:

- the `atlas` launcher, Le Grade, and the continuity runtime (#3)
- Le Cadran as an ASCII terminal panel (#5) and the Arrival rite on boot (#6)
- abstracting the load-bearing operator identity from Matthew to Operator, and
  dispersing the subroutine activation lines to match
- the Arrival masthead and the hand-wound crown (#7, #8, #9)
- **rebuilding ATLAS as a Claude Code plugin** (#10)
- operator-agnostic per-user config, `grade` → `level`, XP in the rite, and CI
  semver releases (#17–#23)
- release-on-wind update checks, level scoring enforced at release, and the
  `git-cleanup` skill (#26–#28, #30, #31)

Principal areas: `bin/atlas-*`, `.claude-plugin/`, `.github/workflows/`,
`install.sh`, `runtime/`, `README.md`.

Named as `author` in `.claude-plugin/plugin.json` and as `owner` of the
`scadumen` marketplace.

| Identity | Commits | Window |
|---|---|---|
| `Tyler Etters <tyleretters@users.noreply.github.com>` | 19 | 08-26 → 08-29 |
| `Tyler Etters <tyler@etters.co>` | 3 | 08-26 |

## The working relationship

Tyler is actively building on ATLAS, not merely credited on it. The launcher, the
plugin packaging, the release train, and the Arrival rite are his, and remain his
to extend.

Matthew and Tyler hold full mutual access to each other's GitHub organizations.
The SCADUMEN org exists as the umbrella that shared work sits under; the
`Forgotten-Industries` → `SCADUMEN` rename is the trace of that arrangement being
set up.

## Machine collaboration

49 of the 56 commits carry at least one `Co-Authored-By` trailer naming the
model that worked on them. The raw trailer count is higher — 99 — because a
squash merge concatenates the trailers of every commit it absorbs; `#2` alone
carries 32. By occurrence: 65 Claude Opus 5, 11 Claude Opus 5 (1M context),
22 Claude Opus 4.8 (1M context), 1 Claude Sonnet 5.

The trailers are kept deliberately. A masthead that reads
**HUMAN JUDGEMENT // MACHINE COLLABORATION // CONTRE L'OUBLI** should be able to
say which was which.

---

A thing documented is a thing not yet lost.
