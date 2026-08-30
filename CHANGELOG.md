# Changelog

All notable changes to ATLAS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and ATLAS uses semantic
versioning. The version is declared once, in `.claude-plugin/plugin.json`. On
merge to `main`, the Release workflow tags `atlas--v<version>`, cuts a GitHub
Release, and publishes the movement's Level.

## [Unreleased]

## [1.7.0] - 2026-08-30

### Added
- A ledger integrity guard (`level/ledger_guard.py`), run by the level suite:
  it rejects a planned row whose path already exists, and two counting rows on
  one path. The evidence rule in `overlays/le-niveau.md` verified that a built
  module's file exists, which a path predating its row satisfies for free —
  three roadmap rows pointed at files already in the tree (`rouage/`,
  `hardware/le-boitier.md`, `overlays/le-barillet.md`), so changing the word
  `planned` to `built` three times would have scored 2500 XP with no work done
  and `release_guard.py` passing, since the XP it watches would really have
  risen. A spec row paired with one planned completion row is still allowed: it
  cannot score twice, and the premature rule catches the flip.
- Ledger module `ledger-guard` (C, `level/ledger_guard.py`); +100 XP.

### Changed
- The three planned ledger rows now name the artifact that will **prove** the
  work rather than the one that describes it: `le-rouage-complete` →
  `rouage/CONFORMANCE.md`, `le-boitier-built` → `hardware/le-boitier-build.md`
  (the build record, not the case spec), `barrel-adapter` →
  `adapters/barillet/README.md`. No XP moved — planned rows score nothing —
  but the roadmap is now falsifiable.
- `overlays/le-niveau.md` states the second half of the evidence rule: a planned
  module must name a path that does not exist yet.

## [1.6.0] - 2026-08-29

### Added
- A `git-cleanup` skill (`skills/git-cleanup/SKILL.md`), invocable as
  `/atlas:git-cleanup`: remove merged worktrees, delete merged branches, prune
  remote refs, and pull the latest main. It is hand-authored, not generated from
  a subroutine — the first plugin skill outside the council. Its merge test adds
  a tree-diff check (`git diff --quiet main <branch>`) so a squash-merged branch
  whose remote head GitHub left in place is still recognized; the earlier
  "upstream is gone" heuristic alone missed those and left the worktree behind.
- Ledger module `git-cleanup` (C, `skills/git-cleanup/SKILL.md`); +100 XP.

## [1.5.0] - 2026-08-29

### Added
- The Module Ledger in `overlays/le-niveau.md` now scores three capabilities
  that shipped since v1.1.0 but were never listed, so they earned nothing: the
  update check (`update-check`, A, `level/latest.py`, from 1.3.0), worktree
  discovery and the `clone_kind()` classifier (`worktree-discovery`, A,
  `bin/atlas-clones`, from 1.4.0), and the Conventional Commits PR-title gate
  (`pr-title-lint`, B, `.github/workflows/lint-pr-title.yml`, from 1.2.0). The
  loop — build a module, list it as built with a real path, rerun the score —
  had simply not been run for those releases. Level moves 89 → 94 (+1250 XP).
- A release failproof: a minor or major version bump must raise the computed
  level, or CI fails the PR. `level/release_guard.py` (pure, unit-tested,
  reusing `parse_version()` from `latest.py`) decides; the `Test` workflow
  scores the PR base tree in a detached worktree and compares. A patch bump
  (fix/chore/docs) is exempt. This is why the level silently stalled for nine
  releases after v1.1.0; it can no longer.
- `level/level.py --xp` prints just the integer XP, for machine parsing.

## [1.4.3] - 2026-08-29

### Fixed
- Documentation that still described the `agent` key dropped in 1.4.2 as live
  behaviour. `settings.json` is now `{}`, but the repository map said it "names
  `atlas` as the session agent", the "What it does" paragraph had it naming
  `agents/atlas.md` so that "its prompt, model, and tools govern the main
  thread", `runtime/README.md` referred to "the main-thread agent that
  `settings.json` activates", and a comment in `bin/atlas-context` said the same.
  All four now describe the agent as opt-in, selected with
  `claude --agent atlas:atlas` or from `/agents`.
- The note at the foot of the permissions section is deliberately unchanged: that
  ATLAS's own `settings.json` honours only `agent` and `subagentStatusLine` and
  silently drops everything else is still true, and is still the reason a
  permission rule cannot ship with the plugin.

## [1.4.2] - 2026-08-29

### Fixed
- The plugin shipped a root `settings.json` with `"agent": "atlas"`, which Claude
  Code applies as the main-thread agent whenever the plugin is enabled. Every bare
  `claude` launch came up as `atlas:atlas` instead of the built-in `claude` agent,
  with no way to opt out short of disabling the plugin. Dropped the `agent` key so
  default launches fall back to the built-in agent; ATLAS stays available on demand
  via `claude --agent atlas:atlas` or `/agents`.

## [1.4.1] - 2026-08-29

### Fixed
- The Arrival rite now fires on either grip of the crown. The compact runtime
  required the operator's first message to be exactly `⟨wind the crown⟩`, but
  the `/atlas` skill is itself a winding - it sets `disable-model-invocation:
  true`, so its invocation is proof the operator reached for the crown by hand.
  The two paths state deliberately different signals for the same act, and
  neither cancels the other. The prohibition on performing the rite unbidden now
  says explicitly that it covers unsignalled messages only: a rite that silently
  fails to fire is a failure in the same way a rite that fires unbidden is.

## [1.4.0] - 2026-08-29

### Added
- `bin/atlas-clones` now finds and labels linked worktrees. Discovery tested
  `-type d -name .git`, which encodes "a repository is a directory holding a
  `.git` directory" - true of clones, false of worktrees, where `.git` is an
  87-byte file holding a `gitdir:` pointer. Every worktree on the machine was
  invisible, and a worktree is likelier than a clone to hold uncommitted work,
  because holding in-progress work is what worktrees are for.
- `clone_kind()` classifies each checkout by comparing `--absolute-git-dir`
  against `--git-common-dir`; equal means clone, different means worktree and
  the parent is the directory holding the common dir. The common dir is
  resolved before comparing, because git answers it relative to the invocation
  directory - commonly bare `.git` - and comparing raw reports every ordinary
  clone as a worktree. Worktrees are listed as their own entries rather than
  folded into the parent, on the grounds that listing is information-preserving
  and folding is lossy.

## [1.3.1] - 2026-08-29

### Added
- A Requirements section in the README, naming the POSIX tools ATLAS actually
  shells out to and stating that network access is optional - the update check
  added in 1.3.0 is the only outbound call, and ATLAS runs fully offline without
  it. Replaces the one-line "git, python3, and Claude Code" note further down.

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
