# ATLAS

> **HUMAN JUDGEMENT // MACHINE COLLABORATION // CONTRE L'OUBLI**

ATLAS is Matthew Marx's reusable operating interface for technical recovery, archive work, project planning, and calm execution.

It is not a mascot, brand voice, or roleplay layer. It is a portable instruction system for Codex and related agents: steady communication, practical momentum, durable documentation, and clear handoffs across projects.

## Structure

Core layer:

- `AGENTS.md` - root entrypoint for agents working inside this repository.
- `ATLAS.md` - core ATLAS operating layer.
- `rapport/AGENTS.md` - conversational cadence, tactical-radio rapport, and signoff behavior.
- `profiles/matthew.md` - Matthew-specific collaboration guidance.

Council:

- `overlays/le-conseil.md` - the routing manifest: roster, gate conditions, handoff graph, panel limits, precedence.
- `overlays/le-sas.md` - the airlock. A complication, not a member: admission control between the ring and ATLAS.
- `overlays/le-barillet.md` - the barrel. The fitted model, its power reserve, and the record of barrels that have run.
- `overlays/le-rouage.md` - the going train. The router specification. **Half built** — see `rouage/`.
- `rouage/` - the train in code. Python, stdlib only, 24 tests.
- `overlays/le-protocol-de-trois.md` - Le Protocole des Trois Témoins, the three-witness judgment protocol.
- `hardware/le-boitier.md` - the case. Enclosure and control specification for the physical instrument.
- `subroutines/` - twelve operating modes, one file each.

Overlays and templates:

- `overlays/forgotten-industries.md` - public-safe project overlay for Forgotten Industries.
- `templates/repo-AGENTS.md` - starter root instructions for downstream repositories.
- `templates/project-overlay.md` - starter overlay for a new project.

Portable launcher and examples:

- `install.sh` - one-command install for the launcher. See below.
- `bin/atlas` - launches Claude Code fitted as the barrel, with the compact ATLAS core injected. See below.
- `examples/larchive/` - a worked example of ATLAS operating as L'Archive: an accession log plus its project-context file.

Grade and modules:

- `overlays/le-grade.md` - the leveling system: tiers, XP curve, and the module ledger.
- `grade/` - the grade computed in code. Python, stdlib only, parses the ledger, 8 tests.
- `modules/` - knowledge and skill modules that raise the grade, one file each.

## Le Conseil

Thirteen subroutines, gated and routed by `overlays/le-conseil.md`. They are operating modes of one agent, not thirteen agents.

The council is built as a diver's chronograph, and each part carries a real constraint:

| Part | Council | Position |
|---|---|---|
| The wearer | L'Opérateur — MTM | Not a part. Outside the case. He decides. |
| Bezel | ATLAS | The interface. Set before you go under, read against ever after. |
| Crown | Le Sauvegarder | The only input path. Nothing enters except by saving something. |
| Dial plate | L'Archive | The ground the whole council is printed on. |
| Hours | The twelve | 11, 12, 01–10 |
| Registers | Signal · Noise · Gain | Le Sceptique's readout, driven from 01 |
| Barrel | Le Barillet | The fitted model. Power reserve = context window. |
| Going train | Le Rouage | The router. Carries everything, decides nothing. **Half built.** |
| Escapement | Le Sas | Internal. Regulates release. Not a member. |
| Hands | — | The answer. Deliberately no one. |

| Pos | Subroutine | Function |
|---|---|---|
| 11 | Le Continuant | Maintains continuity across long arcs |
| 12 | Le Rédempteur | Returns to damaged or abandoned work |
| 01 | Le Sceptique | Tiers every claim; drives signal, noise, gain |
| 02 | Le Curateur | Decides what the collection is, not what is in it |
| 03 | Le Taxonomiste | Classifies records, preserves source language |
| 04 | Le Vigile | Defends access, custody, and boundaries |
| 05 | Le Fripon | Authorized red team, under charter |
| 06 | Le Renégat | Argues against the mission; owns Reduce and Release |
| 07 | Le Cartographe | Maps dependencies and provenance |
| 08 | Le Limier | Reconstructs what happened, in sequence |
| 09 | Le Forgeron | Builds and repairs durable systems |
| 10 | Le Messager | Carries findings outward without distortion |

Each file has an `OPERATIONAL CORE` for runtime and a `DOCTRINE` section below it for authoring. A router loads the core alone.

The distinctions that keep them separate: Le Sceptique attacks the claim, Le Fripon attacks the defence, Le Renégat attacks the consensus. Le Limier reconstructs the event, Le Cartographe maps the terrain, Le Forgeron changes the system, Le Messager controls the transmission.

The door is machinery and the last word is human: structural refusal happens at the escapement, where it needs no judgement, and what survives reaches Le Sceptique, where it needs a person.

## Use In A Project

Each downstream project should keep its own local `AGENTS.md`. That file should point to local project rules first, then to any ATLAS overlay or copied ATLAS guidance.

Recommended project pattern:

```text
PROJECT/
  AGENTS.md
  ATLAS.md
  atlas/AGENTS.md
  atlas/subroutines/
```

For larger projects, keep the project-specific instructions local and use this repository as the source of truth for shared ATLAS behavior.

## Portable Launcher (Claude Code)

Type `atlas` in any directory and Claude Code starts as ATLAS, layered on top of the project you are already in.

### Quickstart

```sh
git clone git@github.com:SCADUMEN/ATLAS.git
cd ATLAS
eval "$(./install.sh)"
atlas
```

`eval "$(./install.sh)"` symlinks `bin/atlas` into `~/.local/bin`, makes sure that directory is on your `PATH` — now and in future shells — and leaves `atlas` usable in the same shell, no reload. Running `./install.sh` without the `eval` installs just as durably; you open a new terminal to pick it up.

Requirements: a POSIX shell, git, and Claude Code (`claude`) on your `PATH`.

### What it does

It assembles the compact core — `ATLAS.md`, `rapport/AGENTS.md`, `profiles/matthew.md`, `overlays/le-conseil.md` — plus a runtime coda, and passes it to Claude with `--append-system-prompt-file`. It also runs `--add-dir` on this repository, so the subroutine cores are read on demand per `overlays/le-rouage.md` rather than all loaded up front. ATLAS voice governs; the current directory's own context still loads beneath it.

In the language of the movement: the launcher fits the running model as the barrel (`overlays/le-barillet.md`). The model supplies force; the doctrines supply shape.

### Usage

```sh
atlas                 # interactive, in the current directory
atlas -c              # resume the last conversation here
atlas "quick question"
atlas --model ...     # any claude flag passes straight through
```

### Manual install

If you would rather not run the script, and `~/.local/bin` is on your `PATH`:

```sh
ln -s "$(pwd)/bin/atlas" ~/.local/bin/atlas
```

The twelve subroutine doctrines are not loaded up front, because thirteen doctrines do not fit the reserve. When a council member is named, its `OPERATIONAL CORE` is read from `subroutines/` on demand.

This is the Claude Code path. A doctrine-stripped bundle for agents without file access is a planned follow-up; Codex reads the repository files natively through `AGENTS.md`.

## Le Grade

ATLAS levels up. Every capability is a module with a tier and fixed XP (S=1000, A=500, B=250, C=100, D=50); the grade is those XP on a 0–100 square-root curve, so the top grades are the steepest. It is deterministic: `grade/grade.py` parses the module ledger in `overlays/le-grade.md`, verifies each module's file exists, sums the XP, and prints the grade. A module earns nothing until its file is real.

```sh
python3 grade/grade.py            # full readout
python3 grade/grade.py --oneline  # boot banner
```

Current grade: **80** (8,350 / 13,000 XP). The single S-tier module is Reincarnation — the portable launcher above. To level up, build a module (knowledge pack or core-system work), list it in the ledger with a real path, and rerun the script. Grade 100 is the design-complete instrument; modules past it earn Grand Complication prestige. Full doctrine and the leveling schedule are in `overlays/le-grade.md`.

## Operating Principle

Usefulness comes first. Voice supports trust and momentum, but technical correctness, safety, and preservation override tone.

A thing documented is a thing not yet lost.
