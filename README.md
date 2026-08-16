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
- `overlays/le-protocol-de-trois.md` - Le Protocole des Trois Témoins, the three-witness judgment protocol.
- `subroutines/` - twelve operating modes, one file each.

Overlays and templates:

- `overlays/forgotten-industries.md` - public-safe project overlay for Forgotten Industries.
- `templates/repo-AGENTS.md` - starter root instructions for downstream repositories.
- `templates/project-overlay.md` - starter overlay for a new project.

## Le Conseil

Twelve subroutines, gated and routed by `overlays/le-conseil.md`. They are operating modes of one agent, not twelve agents.

| Panel | Subroutine | Function |
|---|---|---|
| Trois Témoins | Le Sauvegarder | Preserves what can still be saved now |
| Trois Témoins | Le Continuant | Maintains continuity across long arcs |
| Trois Témoins | Le Rédempteur | Returns to damaged or abandoned work |
| Quatrième Témoin | Le Sceptique | The airlock — tiers claims, enforces gain, gates output |
| Autorités du Registre | Le Taxonomiste | Classifies records, preserves source language |
| Forces Adverses | Le Vigile | Defends access, custody, and boundaries |
| Forces Adverses | Le Fripon | Authorized red team, under charter |
| Forces Adverses | Le Renégat | Argues against the mission; owns Reduce and Release |
| Opérateurs de Terrain | Le Cartographe | Maps dependencies and provenance |
| Opérateurs de Terrain | Le Limier | Reconstructs what happened, in sequence |
| Opérateurs de Terrain | Le Forgeron | Builds and repairs durable systems |
| Opérateurs de Terrain | Le Messager | Carries findings outward without distortion |

Each file has an `OPERATIONAL CORE` for runtime and a `DOCTRINE` section below it for authoring. A router loads the core alone. The three witnesses predate this structure and are pending retrofit.

The distinctions that keep them separate: Le Sceptique attacks the claim, Le Fripon attacks the defense, Le Renégat attacks the consensus. Le Limier reconstructs the event, Le Cartographe maps the terrain, Le Forgeron changes the system, Le Messager controls the transmission.

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
