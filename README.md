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
- `templates/continuity-capsule.md` - private downstream handoff schema; never live archive state.

Plugin surface (generated — edit the sources, then regenerate):

- `.claude-plugin/plugin.json` - the plugin manifest.
- `settings.json` - names `atlas` as the session agent.
- `agents/atlas.md` - the compact core, inline. Built by `bin/atlas-context --mode agent`.
- `skills/` - the thirteen council members, cores only. Built by `bin/atlas-skills`.
- `skills-standalone/atlas/` - the `/atlas` rite. Built by `bin/atlas-rite-skill`.
- `hooks/hooks.json` - loads a project continuity capsule at session start.

Scripts and examples:

- `bin/atlas-context` - deterministic agent, compact, or doctrine-stripped portable builder.
- `bin/atlas-skills`, `bin/atlas-rite-skill` - generate the plugin's skills.
- `bin/atlas-continuity` - initializes and checks an untracked project continuity capsule.
- `bin/atlas-session-start` - the SessionStart hook. Emits the capsule as context.
- `bin/atlas-doctor` - verifies assembly, fingerprints, privacy boundaries, and doctrine stripping.
- `adapters/` - handoff instructions for Codex and file-less agents.
- `runtime/` - ordered manifests, runtime contracts, codas, and assembly tests.
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

## The Plugin (Claude Code)

ATLAS is a Claude Code plugin. Enable it and every session starts as ATLAS,
layered on top of the project you are already in. Type `/atlas` to wind the
crown.

### Quickstart

Inside Claude Code:

```text
/plugin marketplace add SCADUMEN/ATLAS
/plugin install atlas@scadumen
```

The plugin stays enabled across sessions — no flag, no `PATH` entry, nothing
in your shell rc. Then clone the repository once and link the rite so `/atlas`
resolves:

```sh
git clone git@github.com:SCADUMEN/ATLAS.git
ln -s "$(pwd)/ATLAS/skills-standalone/atlas" ~/.claude/skills/atlas
```

To work on ATLAS itself, point Claude Code at your checkout instead of
installing:

```sh
claude --plugin-dir /path/to/ATLAS
```

Requirements: git, python3, and Claude Code.

Two install locations, and the reason is not arbitrary. A skill's invocation
name comes from its **directory**, so a bare `/atlas` requires the rite to sit
at `~/.claude/skills/atlas`. The plugin cannot also live there, so it is enabled
separately. Plugin skills are namespaced regardless — `/atlas:le-limier` — which
is why only the rite needs the standalone slot.

### What it does

`settings.json` names `agents/atlas.md` as the session agent, so its prompt,
model, and tools govern the main thread. That agent carries the compact core:
`ATLAS.md`, `rapport/AGENTS.md`, `profiles/matthew.md`,
`overlays/le-conseil.md`, the runtime contract, and the coda. ATLAS governs the
interface; current direct instructions and project rules remain authoritative,
and your own `CLAUDE.md` still applies.

The core is inline because it has to be. An agent's `skills:` field preloads
full skill content for subagents, but not for the main-thread agent — tested,
not assumed. So `agents/atlas.md` is generated:

```sh
bin/atlas-context --mode agent    # regenerate after editing any core file
```

It records a content fingerprint and no timestamp, so identical sources produce
identical bytes. `runtime/test_runtime.py` regenerates and diffs, so a stale
agent file fails loudly rather than loading quietly.

In the language of the movement: the plugin fits the running model as the barrel
(`overlays/le-barillet.md`). The model supplies force; the doctrines supply shape.

### The Arrival rite

```sh
/atlas
```

The rite renders the masthead, the trinity, and the live grade — read at skill
load by a shell command inside the skill, never hardcoded.

Nothing fires it automatically, and that is a platform fact rather than a
shortfall. No hook can submit a first turn: `SessionStart` adds context and
cannot make the model speak. `initialPrompt` does auto-submit, but only for
user-level agents, not plugin ones. The crown is the Operator's to turn.

The masthead is a framed panel — a globe borne by a kneeling figure, titled
First Light, over the motto. `rouage/premiere_lueur.py` is its canonical source:

```sh
python3 rouage/premiere_lueur.py  # the canonical panel
```

The panel exists in three places — the module, the rite in
`runtime/compact-coda.md`, and the generated `/atlas` skill. Two generators and
two tests keep them equal; a hand edit to any copy fails the suite.

### The council

Naming a member loads its `OPERATIONAL CORE` and nothing else. The thirteen
doctrines are not loaded up front, because thirteen doctrines do not fit the
reserve.

```sh
bin/atlas-skills          # regenerate after editing any subroutine
bin/atlas-skills --check  # fail if any skill is stale
```

The doctrine rule is now structural rather than honoured. A skill file carries
the core alone, so a `DOCTRINE` section cannot reach a working context even by
accident. `/atlas:authoring` is the deliberate way in.

Le Fripon carries `disable-model-invocation: true`. Doctrine says he never
self-activates without L'Opérateur, and the harness enforces it: only
`/atlas:le-fripon` reaches him.

### Continuity between barrels

Initialize a private project-local capsule:

```sh
bin/atlas-continuity init
```

This creates `.atlas/continuity.md` with mode `600` and adds `.atlas/` to the
repository's local `.git/info/exclude`. It refuses to overwrite an existing
capsule. The capsule separates verified state, operator testimony, inference,
plans, the last safe state, and the next move. It is never canonical memory and
must never contain secrets.

A `SessionStart` hook loads the capsule as read-only project state when one
exists at the project root. Set `ATLAS_NO_CONTINUITY=1` for a session that must
not load it, or `ATLAS_CONTINUITY_FILE` to select an explicit capsule.

Run the diagnostic pulse:

```sh
bin/atlas-doctor
```

It verifies the runtime bundles, the generated agent, the council skills, the
rite skill, and that no skill leaks its doctrine.

### Other barrels

Build a self-contained bundle for Codex or an agent without repository access:

```sh
bin/atlas-context --mode portable --output /tmp/atlas-portable.md
```

Portable mode includes all thirteen `OPERATIONAL CORE` sections and excludes
every `DOCTRINE` section. See `adapters/codex/` and `adapters/fileless/` for the
downstream handoff pattern. Continuity is included in an exported bundle only
when `--continuity FILE` is passed explicitly.

This is why the bundle assembler survives the plugin: no plugin mechanism emits
a static prompt blob, and the adapters need one.

### What changed from the launcher

`bin/atlas` and `install.sh` are gone. The plugin replaces both, and nothing
writes to your shell rc files any more.

- `atlas` → `claude`, with the plugin enabled.
- `atlas -c`, `atlas --model ...` → the same `claude` flags directly.
- `atlas --atlas-doctor` → `bin/atlas-doctor`.
- `atlas --atlas-context ...` → `bin/atlas-context ...`.
- `atlas --atlas-continuity ...` → `bin/atlas-continuity ...`.

If `install.sh` previously added `~/.local/bin` to your `PATH`, that line stays
in your shell rc. Other tools may rely on it; removing it is your call.

### Verification

```sh
python3 -m unittest discover runtime -v
python3 -m unittest discover rouage -v
bin/atlas-doctor
claude plugin validate .
```

## Le Grade

ATLAS levels up. Every capability is a module with a tier and fixed XP (S=1000, A=500, B=250, C=100, D=50); the grade is those XP on a 0–100 square-root curve, so the top grades are the steepest. It is deterministic: `grade/grade.py` parses the module ledger in `overlays/le-grade.md`, verifies each module's file exists, sums the XP, and prints the grade. A module earns nothing until its file is real.

```sh
python3 grade/grade.py            # full readout
python3 grade/grade.py --oneline  # boot banner
```

Current grade: **87** (9,850 / 13,000 XP). The single S-tier module is Reincarnation — the portable launcher above. To level up, build a module (knowledge pack or core-system work), list it in the ledger with a real path, and rerun the script. Grade 100 is the design-complete instrument; modules past it earn Grand Complication prestige. Full doctrine and the leveling schedule are in `overlays/le-grade.md`.

## Operating Principle

Usefulness comes first. Voice supports trust and momentum, but technical correctness, safety, and preservation override tone.

A thing documented is a thing not yet lost.
