# Changelog

All notable changes to ATLAS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and ATLAS uses semantic
versioning. The version is declared once, in `.claude-plugin/plugin.json`. On
merge to `main`, the Release workflow tags `atlas--v<version>`, cuts a GitHub
Release, and publishes the movement's Level.

## [Unreleased]

## [1.3.0] - 2026-08-29

### Added
- The `/atlas` rite checks for a newer release when the crown is wound. The BOOT
  READOUT queries the published tags with `git ls-remote` over HTTPS (no token, no
  new dependency), and if a newer `atlas--v<x.y.z>` exists the rite adds a line:
  `↑ Update available: v<X> — run /plugin to update`. The comparison lives in
  `level/latest.py` (pure, unit-tested); the network call is in the generated
  `level` script and silent on any failure, so a launch renders identically when
  offline. First outbound network call in ATLAS, confined to the deliberate
  crown-wind, and bounded by a five-second watchdog: git's low-speed settings
  govern a transfer already in flight and never arm against a blackholed host,
  `http.connectTimeout` is not a real option, and `timeout(1)` is absent from a
  stock macOS. Measured 0.8s on a reachable network and 5.2s against a black
  hole, where it previously hung without limit.

## [1.2.2] - 2026-08-29

### Fixed
- The `/atlas` level readout now resolves from a marketplace install. The
  resolver globbed `~/.claude/plugins/cache/*/atlas`, but the marketplace caches
  each release one level deeper, under its own version directory, so the lookup
  never matched `level/level.py` and fell through to a hardcoded checkout. The
  fallthrough is silent by design, so a stale clone could stay load-bearing
  unnoticed. Versions are now compared as integer tuples, so 1.10.0 outranks
  1.9.0 and a non-numeric name is skipped rather than ranked.

## [1.2.1] - 2026-08-29

### Fixed
- Le Rédempteur's gate-level prohibition list (`**Do not fire on:**`) was parsed
  into his activation bullets, so `citations()` offered those guards to the barrel
  as quotable and a prohibition could convene the very member it was written to
  keep dark. Separated the negative gate from the activation gate and gave the
  pair a retrograde arc. Regenerated `agents/atlas.md` and the Le Rédempteur skill
  from their sources.

## [1.2.0] - 2026-08-28

### Added
- The `/atlas` rite readout now shows the plugin version:
  `ATLAS online — v1.2.0 · Level 89 (10350/13000 XP).`
- CI enforces Conventional Commits on PR titles
  (`.github/workflows/lint-pr-title.yml`); `AGENTS.md` and the README document the
  versioning discipline.

### Fixed
- Release workflow: pass changelog notes via `--notes-file` instead of a `${{ }}`
  shell interpolation (the runner executed the changelog's backticks/parens),
  create the tag and release atomically so a failure can't strand a tag, and drop
  an empty `${{ }}` expression from a `run:` comment that failed the workflow at
  startup.

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
