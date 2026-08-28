# Changelog

All notable changes to ATLAS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and ATLAS uses semantic
versioning. The version is declared once, in `.claude-plugin/plugin.json`. On
merge to `main`, the Release workflow tags `atlas--v<version>`, cuts a GitHub
Release, and publishes the movement's Level.

## [Unreleased]

### Fixed
- Release workflow: pass changelog notes to `gh release create` via `--notes-file`
  instead of a `${{ }}` shell interpolation (the changelog's backticks/parens were
  executed by the runner), and create the tag and release atomically so a failure
  can't strand a tag without a release.

## [1.1.0] - 2026-08-28

### Added
- Per-user operator profile (`bin/atlas-operator`), loaded by the SessionStart
  hook, so ATLAS greets you by name. Absent one, it addresses you as "Operator".
- CI semver releases: `.github/workflows/release.yml` tags `atlas--v<version>`
  and cuts a GitHub Release on a version bump, publishing the current Level.
- The Arrival rite now shows the XP fraction: `ATLAS online — Level N (XP/XP100 XP).`
- Ledger module `versioning` (A, +500 XP) for the release discipline — Level 87 → 89.

### Changed
- The leveling system is renamed Grade → Level ("Le Grade" → "Le Niveau"):
  `grade/` → `level/`, `overlays/le-grade.md` → `overlays/le-niveau.md`, and every
  readout now says "Level". The `/atlas` boot script is `skills/atlas/level`.
- The core is operator-agnostic — no specific operator ships in it.

## [1.0.0] - 2026-08-26

### Added
- Initial ATLAS plugin: the session agent, the thirteen council skills, the
  `/atlas` rite, the continuity capsule, and the deterministic level/XP ledger.
