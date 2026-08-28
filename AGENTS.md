# AGENTS.md

Before making changes in this repository, read:

- `ATLAS.md` for the core ATLAS operating layer.
- `rapport/AGENTS.md` for conversational rapport, cadence, and signoff style.
- `overlays/le-conseil.md` for the council roster, gate conditions, routing, and precedence. Read this before adding, removing, or redefining any subroutine.
- `overlays/le-protocol-de-trois.md` when Matthew invokes Le Protocol or Les Trois Témoins.
- the relevant file in `subroutines/` when Matthew invokes a council member by name or when changing that mode's guidance.
- `profiles/matthew.md` as an example operator profile. Per-user operator identity lives in `~/.claude/atlas/operator.md` via `bin/atlas-operator`, not the core.

Subroutine files have two sections. `OPERATIONAL CORE` is loaded at runtime and must stay compact and behavioral. `DOCTRINE` is the authoring layer and is not loaded during ordinary work. Keep new material in the correct section.

The core ships no operator. Identity is per-user config: `bin/atlas-operator init` scaffolds `~/.claude/atlas/operator.md`, which the `SessionStart` hook loads for every session. Absent one, ATLAS addresses the Operator generically as "Operator". Never bake a name or personal profile into the core files (`runtime/core-files.txt`); keep those operator-agnostic.

Versioning is semantic, and `.claude-plugin/plugin.json` is the single source of truth. PR titles follow Conventional Commits — `.github/workflows/lint-pr-title.yml` enforces them: `feat` → minor, `fix`/`chore`/`docs`/`refactor`/`ci` → patch, and a trailing `!` (or a `BREAKING CHANGE:` footer) → major. The version bump must land in the PR's own diff: `.github/workflows/release.yml` reads the version on `main` and skips when `atlas--v<version>` already exists, so a merge without a bump ships nothing — one version per releasable PR. Record changes under `[Unreleased]` in `CHANGELOG.md`, and rename that heading to the version when you bump.

This repository is the canonical source for reusable ATLAS instructions and templates. Keep it portable, precise, and easy to copy into downstream projects.

Use repository instructions first, then ATLAS voice and rapport second. Technical correctness, safety, and preservation of useful context override tone.
