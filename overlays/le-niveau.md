# LE NIVEAU

## The Movement's Level

**Function:** Measures how complete the instrument is, as one number, deterministically.
**Class:** Meta. Not a member, not a mode, not a voice. A readout about the whole.
**Position:** Outside the cycle. It reports on the instrument; it does not drive it.

A watch movement is graded — jewel count, finish, chronometer certification. ATLAS carries a level in the same spirit, and because Matthew has been building him for a long time, that level is already high. This file is the RPG sheet: modules are the experience, the level is computed from them, and both are read from what is actually in the repository rather than asserted.

The rule that keeps it honest, borrowed from `overlays/le-rouage.md`: **XP is only earned by a module whose file exists.** A module can be listed as planned, but it scores nothing until it is built. `level/level.py` parses the ledger below, verifies each built module's path, sums the XP, and prints the level. Doctrine and score cannot drift.

That rule has a second half, and it went unwritten long enough to leave a hole worth 2500 XP: **a planned module must name a path that does not exist yet.** A path can predate the row that claims it, and three roadmap rows once pointed at files already in the tree — so flipping the word `planned` to `built` would have scored their full tier with no work done and every check passing. The existence test asks *does something live here?*; the invariant needs *did this release produce it?* A roadmap row therefore names the artifact that will **prove** the work, not the artifact that **describes** it: `le-boitier-built` names the build record, not the case spec it is built from. `level/ledger_guard.py` enforces both halves, and rejects two counting rows on one path — one file is evidence for one module.

---

## OPERATIONAL CORE

### Tiers

Every module carries a tier, and the tier fixes its XP. No per-module tuning.

| Tier | XP | Meaning |
|---|---|---|
| S | 1000 | A capability that changes what ATLAS fundamentally is. Rare. |
| A | 500 | A load-bearing system or an always-relevant mode. |
| B | 250 | A working mode, a system component, or a solid knowledge pack. |
| C | 100 | A supporting layer or a small skill. |
| D | 50 | A minor addition. |

### The Curve

Total XP is the sum of built modules. Level is on a fixed 0–100 scale:

```
Level(XP) = floor( 100 · sqrt( XP / XP100 ) ),  capped at 100
XP100     = 13000      # the XP of the design-complete instrument
```

The square root is deliberate: early modules raise the level quickly, late ones slowly. Crossing into the 80s and 90s is meant to be hard, which is why a long-built assistant sits high on the scale without being finished.

Inverse — the XP a level requires:

```
XP(Level) = XP100 · (Level / 100)^2 = 1.3 · Level^2
```

**Calibration.** `XP100 = 13000` is the sum of a design-complete build plus its roadmap (finish Le Rouage, build the case, a barrel adapter, and a shelf of knowledge modules). It is a design constant, stated here and tunable in one place. It is anchored so the launcher milestone — the build that first gained Reincarnation — reads Level 80; modules earned after it raise the level from there.

### Prestige

At Level 100 the movement is design-complete. Further knowledge modules do not raise the level; they add **Grand Complication +N**, where N counts modules earned past `XP100`. Prestige is uncapped. The level is not.

**Which modules are "past".** N is a count of modules, never a quantity of XP, and "past" is read in ledger order: a module is past the line when the running total *before* it has already reached `XP100`. The module that crosses the line is the one that **reached** design-complete, not one earned beyond it, so it scores no prestige. This matters because tiers are coarse — no combination of 50/100/250/500/1000 need land exactly on 13000, so the instrument arrives at design-complete already some XP over it. Under a count of modules that state reads **Level 100**, which is correct and is the whole point of the number. `+0` is therefore not a value the readout can print: prestige is either absent, and the level reads 100, or it is at least +1.

This replaces an earlier rule that computed `round((xp - XP100) / 1000)` — a rounded thousand of XP rather than a count of modules. It disagreed with the sentence above it, and it printed `Grand Complication +0` for any instrument less than 500 XP past the line, so the design-complete readout the whole scale is anchored to was unreachable in the banner. Doctrine and code now say the same thing, which is the only reason either can be trusted.

### Reading the level

```sh
python3 level/level.py            # full readout: XP, level, next level, gap
python3 level/level.py --oneline  # one line, for a boot banner
python3 level/level.py --service  # service points only, for machine parsing
python3 level/level.py --prestige # Grand Complication count only, for machine parsing
```

The script is the source of truth. Any number written in prose in this file is a snapshot and defers to the script.

---

## The Module Ledger

Status is `built`, `partial`, or `planned`. Built and partial modules score their tier's XP if their path exists; planned modules score nothing and are the roadmap. Le Rouage is `partial` and already scored one tier below its finished value.

| ID | Module | Category | Tier | Status | Path |
|---|---|---|---|---|---|
| atlas-core | ATLAS Core — the bezel | core | A | built | ATLAS.md |
| rapport | Rapport layer | core | B | built | rapport/AGENTS.md |
| operator-profile | Operator profile — per-user config | core | B | built | bin/atlas-operator |
| agents-entry | AGENTS.md entrypoint | core | C | built | AGENTS.md |
| le-sceptique | Le Sceptique (01) | council | A | built | subroutines/le-sceptique.md |
| le-sauvegarder | Le Sauvegarder — the crown | council | A | built | subroutines/le-sauvegarder.md |
| le-curateur | Le Curateur (02) | council | B | built | subroutines/le-curateur.md |
| le-taxonomiste | Le Taxonomiste (03) | council | B | built | subroutines/le-taxonomiste.md |
| le-vigile | Le Vigile (04) | council | B | built | subroutines/le-vigile.md |
| le-fripon | Le Fripon (05) | council | B | built | subroutines/le-fripon.md |
| le-renegat | Le Renégat (06) | council | B | built | subroutines/le-renegat.md |
| le-cartographe | Le Cartographe (07) | council | B | built | subroutines/le-cartographe.md |
| le-limier | Le Limier (08) | council | B | built | subroutines/le-limier.md |
| le-forgeron | Le Forgeron (09) | council | B | built | subroutines/le-forgeron.md |
| le-messager | Le Messager (10) | council | B | built | subroutines/le-messager.md |
| le-continuant | Le Continuant (11) | council | B | built | subroutines/le-continuant.md |
| le-redempteur | Le Rédempteur (12) | council | B | built | subroutines/le-redempteur.md |
| le-conseil | Le Conseil — the manifest | system | A | built | overlays/le-conseil.md |
| le-sas | Le Sas — the escapement | system | B | built | overlays/le-sas.md |
| le-barillet | Le Barillet — the barrel | system | B | built | overlays/le-barillet.md |
| le-protocol-de-trois | Le Protocole des Trois Témoins | system | B | built | overlays/le-protocol-de-trois.md |
| le-boitier | Le Boîtier — the case spec | system | B | built | hardware/le-boitier.md |
| le-rouage | Le Rouage — the going train | system | A | partial | overlays/le-rouage.md |
| runtime-contract | Runtime session contract | system | B | built | runtime/session-contract.md |
| atlas-doctor | Runtime diagnostic — atlas-doctor | system | B | built | bin/atlas-doctor |
| versioning | Semver release discipline (CI) | system | A | built | .github/workflows/release.yml |
| pr-title-lint | Conventional Commits PR-title gate | system | B | built | .github/workflows/lint-pr-title.yml |
| update-check | Update check — newer-release banner | system | A | built | level/latest.py |
| worktree-discovery | Worktree discovery + clone_kind() classifier | system | A | built | bin/atlas-clones |
| git-cleanup | Git cleanup — merged branches and worktrees | system | C | built | skills/git-cleanup/SKILL.md |
| ledger-guard | Ledger integrity guard | system | C | built | level/ledger_guard.py |
| service-record | Service record — the upkeep axis | system | C | built | level/service.py |
| larchive-accession | L'Archive accession practice | knowledge | B | built | examples/larchive |
| authenticating-people | Authenticating people — Schneider CS513 | knowledge | B | built | modules/authenticating-people.md |
| reincarnation | Reincarnation — the fitted plugin | meta | S | built | agents/atlas.md |
| multi-agent-bundle | Doctrine-stripped portable bundle | meta | A | built | bin/atlas-context |
| continuity-capsule | Continuity capsule — cross-barrel handoff | meta | A | built | bin/atlas-continuity |
| le-rouage-complete | Le Rouage completed (barrel wired) | system | S | planned | rouage/CONFORMANCE.md |
| le-boitier-built | Le Boîtier — physical instrument | system | S | planned | hardware/le-boitier-build.md |
| barrel-adapter | Barrel adapter / fitted-barrel automation | system | A | planned | adapters/barillet/README.md |

---

## The Service Record

**Maintenance prevents loss of integrity.** A repair builds no module, so it moves no level — the instrument is no more complete than it was the day before. But an instrument that is not maintained loses the integrity the level already claims for it, and that loss is silent. `git-cleanup` carried its full tier XP from 1.6.0 while the check its own text called *the reliable check* returned the wrong answer on nearly every branch. The evidence rule verified that a path exists. A path is not a behaviour.

So service is its own axis. It never enters XP, never raises the Level, and never fills the gap to design-complete. It records that the modules already counted are still true.

### Service credit

**A repair is worth a tenth of what it protects.** The scale is derived from the module tiers rather than tuned separately: repairing the core matters more than repairing a convenience because more integrity stands behind it. No per-repair tuning, the same rule the tier table enforces.

| Tier repaired | Module XP | Service credit |
|---|---|---|
| S | 1000 | 100 |
| A | 500 | 50 |
| B | 250 | 25 |
| C | 100 | 10 |
| D | 50 | 5 |

The credits above are a snapshot; `level/level.py` derives them as one tenth of the tier's XP and is the source of truth. A test asserts the two agree.

**Evidence rule.** A service row names a released patch version that appears in `CHANGELOG.md`, and a module ID that appears in the Module Ledger. A repair to something the ledger does not name cannot be recorded — that is a signal the ledger is incomplete, not licence to invent a row. Only the patch component may advance: a minor or major release is a module, and modules score XP, not service.

### The Service Ledger

| Version | Repaired | Note |
|---|---|---|
| 1.2.1 | le-redempteur | The gate-level prohibition list was parsed into the activation bullets, so a prohibition could convene the very member it was written to keep dark. |
| 1.2.2 | reincarnation | The level resolver globbed one directory short of the marketplace cache, so a released install silently fell through to a hardcoded checkout. |
| 1.4.1 | runtime-contract | The Arrival rite fired on only one grip of the crown; the `/atlas` skill is itself a winding and was not accepted as one. |
| 1.4.2 | reincarnation | The plugin shipped a root `settings.json` naming `atlas` as the main-thread agent, so every bare `claude` launch came up fitted, with no way to opt out. |
| 1.7.1 | git-cleanup | Merge detection compared whole trees, so the check documented as reliable called nearly every branch unmerged. Scoped the diff to the files the branch touched. |
| 1.8.1 | le-limier | The countersign was reachable only from inside the file it opens. Its trigger sat in the automatic-invocation list, which the harness reads after loading, while the router matches the description built from the Activation line alone — so "Who is X?" asked cold never convened the member written to answer it. |
| 1.8.2 | le-rouage | The sign was parsed as two names. Doctrine wrote the gate as a form with an illustration, and the phrase parser takes every quoted string in the Activation section literally — so the gate fired for the placeholder and the one example printed beside it, and for no one else. The placeholder is now read as a placeholder.

Three patch releases are deliberately absent. 1.3.1 added a README Requirements section and 1.4.3 corrected documentation left stale by 1.4.2 — both repaired surfaces the Module Ledger does not name, so the evidence rule refuses them. That refusal is the mechanism reporting a gap in the ledger, and it is left standing rather than papered over with a row.

1.8.4 is the third, and it names the largest gap of the three: it repaired the prestige rule in `level/level.py` against the doctrine in this file, and **neither of those paths is a module in the ledger below.** The scoring system does not score itself. The temptation is to add a row and close the gap, and it must be refused for the reason the ledger guard exists — both files already sit on disk, so a row claiming them would score XP for work that was done long ago and is already reflected in every module the ledger does name. A path that predates its row is evidence of the past. The gap is recorded here instead, where it stays visible.

## The Leveling Schedule

Near the top of the scale each level costs `1.3·(2·Level − 1)` XP, which is roughly:

- **B module (250 XP) ≈ one level**
- **A module (500 XP) ≈ two levels**
- **S module (1000 XP) ≈ four levels**

XP required, by level:

| Level | XP | Reached by |
|---|---|---|
| 80 | 8,320 | the launcher milestone — Reincarnation |
| 85 | 9,393 | the portable bundle, continuity, and diagnostic — built |
| 89 | 10,298 | operator config + CI versioning — built |
| 94 | 11,487 | the PR-title gate, update check, and worktree discovery — built |
| 95 | 11,733 | current build — the ledger integrity guard — built |
| 96 | 11,981 | + any B module |
| 99 | 12,742 | + finish Le Rouage (S) |
| 100 | 13,000 | design-complete instrument |

To level ATLAS: build a module, list it in the ledger as `built` with a real path, and rerun `level/level.py`. Core-system work (finishing Le Rouage, building the case) and knowledge modules both count. That is the whole loop — preserve, build, score, preserve.

A thing documented is a thing not yet lost.
