# LE GRADE

## The Movement's Grade

**Function:** Measures how complete the instrument is, as one number, deterministically.
**Class:** Meta. Not a member, not a mode, not a voice. A readout about the whole.
**Position:** Outside the cycle. It reports on the instrument; it does not drive it.

A watch movement is graded — jewel count, finish, chronometer certification. ATLAS is graded the same way, and because Matthew has been building him for a long time, the grade is already high. This file is the RPG sheet: modules are the experience, the grade is the level, and both are computed from what is actually in the repository rather than asserted.

The rule that keeps it honest, borrowed from `overlays/le-rouage.md`: **XP is only earned by a module whose file exists.** A module can be listed as planned, but it scores nothing until it is built. `grade/grade.py` parses the ledger below, verifies each built module's path, sums the XP, and prints the grade. Doctrine and score cannot drift.

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

Total XP is the sum of built modules. Grade is on a fixed 0–100 scale:

```
Grade(XP) = floor( 100 · sqrt( XP / XP100 ) ),  capped at 100
XP100     = 13000      # the XP of the design-complete instrument
```

The square root is deliberate: early modules raise the grade quickly, late ones slowly. Crossing into the 80s and 90s is meant to be hard, which is why a long-built assistant sits high on the scale without being finished.

Inverse — the XP a grade requires:

```
XP(Grade) = XP100 · (Grade / 100)^2 = 1.3 · Grade^2
```

**Calibration.** `XP100 = 13000` is the sum of a design-complete build plus its roadmap (finish Le Rouage, build the case, a barrel adapter, and a shelf of knowledge modules). It is a design constant, stated here and tunable in one place. It is anchored so the launcher milestone — the build that first gained Reincarnation — reads Grade 80; modules earned after it raise the grade from there.

### Prestige

At Grade 100 the movement is design-complete. Further knowledge modules do not raise the grade; they add **Grand Complication +N**, where N counts modules earned past `XP100`. Prestige is uncapped. The grade is not.

### Reading the grade

```sh
python3 grade/grade.py            # full readout: XP, grade, next grade, gap
python3 grade/grade.py --oneline  # one line, for a boot banner
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
| larchive-accession | L'Archive accession practice | knowledge | B | built | examples/larchive |
| authenticating-people | Authenticating people — Schneider CS513 | knowledge | B | built | modules/authenticating-people.md |
| reincarnation | Reincarnation — the fitted plugin | meta | S | built | agents/atlas.md |
| multi-agent-bundle | Doctrine-stripped portable bundle | meta | A | built | bin/atlas-context |
| continuity-capsule | Continuity capsule — cross-barrel handoff | meta | A | built | bin/atlas-continuity |
| le-rouage-complete | Le Rouage completed (barrel wired) | system | S | planned | rouage/ |
| le-boitier-built | Le Boîtier — physical instrument | system | S | planned | hardware/le-boitier.md |
| barrel-adapter | Barrel adapter / fitted-barrel automation | system | A | planned | overlays/le-barillet.md |

---

## The Leveling Schedule

Near the top of the scale each grade costs `1.3·(2·Grade − 1)` XP, which is roughly:

- **B module (250 XP) ≈ one grade**
- **A module (500 XP) ≈ two grades**
- **S module (1000 XP) ≈ four grades**

XP required, by grade:

| Grade | XP | Reached by |
|---|---|---|
| 80 | 8,320 | the launcher milestone — Reincarnation |
| 85 | 9,393 | the portable bundle, continuity, and diagnostic — built |
| 87 | 9,840 | current build |
| 90 | 10,530 | + finish Le Rouage (S) |
| 95 | 11,733 | + the case built (S) and the barrel adapter (A) |
| 100 | 13,000 | design-complete instrument |

To level ATLAS: build a module, list it in the ledger as `built` with a real path, and rerun `grade/grade.py`. Core-system work (finishing Le Rouage, building the case) and knowledge modules both count. That is the whole loop — preserve, build, score, preserve.

A thing documented is a thing not yet lost.
