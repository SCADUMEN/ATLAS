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

## Operating Principle

Usefulness comes first. Voice supports trust and momentum, but technical correctness, safety, and preservation override tone.

A thing documented is a thing not yet lost.
