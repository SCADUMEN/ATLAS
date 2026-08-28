# ATLAS Field Notes

Local, org-internal feedback log. This is separate from Claude Code's
`/feedback` command, which sends reports to Anthropic — nothing in this file
leaves the repo unless someone deliberately shares it.

Purpose: capture real usage friction, ideas, and use cases as they happen, for
Tyler (built the ATLAS binary) and anyone else working on the movement. A
running record of what the instrument does in practice, not just in spec.

## How to use

- Add an entry whenever something is worth remembering: a rough edge, an
  idea, a real use case, a decision and why it was made.
- Facts first. What happened, what was said, what it implies for the build.
  Keep observation separate from interpretation, same discipline as the
  continuity capsule.
- This file is meant to be committed and read by others. No secrets, no
  credentials, no private correspondence.
- Newest entries on top.

---

## Log

### 2026-08-27 — [use-case] Novice-operator onboarding via narrated shell

- **Context:** Operator (Matthew) has only used Claude/Codex GUI desktop apps
  before this session — first time driving ATLAS through Claude Code /
  iTerm directly.
- **Observation:** The gap that mattered wasn't ATLAS's behavior, it was not
  knowing that terminal output represents real filesystem changes (not a
  sandboxed chat reply). Once that was named explicitly, the rest of the
  session (git clone, symlink repointing) tracked fine just by reading
  commands as they ran.
- **Relevance to build:** Worth considering a short "what a terminal session
  actually is" aside baked into first-run/Arrival flow for operators coming
  from GUI-only tools, rather than assuming shell literacy.

### 2026-08-27 — [workspace] Three diverged local clones of SCADUMEN/ATLAS

- **Context:** Investigated "wrong workspace" report from operator. Found
  three separate local clones of the same repo at different commits/branches
  (`~/ATLAS`, `~/projects/ATLAS`, `~/FORGOTTEN-INDUSTRIES/ATLAS`), plus a
  stray non-git partial copy sitting inside the FORGOTTEN-INDUSTRIES website
  repo (`AGENTS.md` + `subroutines/` only, no `runtime/`).
- **Observation:** The live `/atlas` skill symlink pointed at whichever clone
  was most recently rebuilt, with no signal to the operator about which
  filesystem location was actually authoritative. Resolved by cloning fresh
  from `SCADUMEN/ATLAS` into the operator's intended location
  (`~/Documents/ChatGPT/FORGOTTEN-INDUSTRIES/atlas`) and repointing
  `~/.claude/skills/atlas` there. Older clones left on disk, untouched.
- **Relevance to build:** Multi-clone drift is easy to accumulate across
  sessions/machines with no built-in "which clone is canonical" signal.
  Might be worth a `bin/` helper that reports the live symlink target and
  flags other local clones of the same remote.

### 2026-08-27 — [behavior] Arrival rite re-fires on every `/atlas` invocation

- **Context:** Operator invoked `/atlas` multiple times in one session
  (initially not realizing repeated invocation would re-trigger it). Each
  invocation reproduced the full Arrival rite (ASCII panel + greeting),
  though the rite's own spec says "perform once... never for any other
  message."
- **Observation:** Operator confirmed after the fact this was his own
  repeated invocation, not an unprompted bug — but the underlying mechanism
  is real: the skill's generated `SKILL.md` re-supplies the full rite text
  and the "once per session" instruction on every call, with no session
  state to know it already fired. Anthropic feedback drafted separately
  (queued locally via `/feedback`, not yet sent).
- **Relevance to build:** If "once per session" is the actual intent,
  enforcing it needs either session-local state the skill can check, or
  accepting that repeated explicit invocation is a deliberate re-arm and
  documenting it as such rather than as a one-shot guarantee.

---

## Entry template

```
### YYYY-MM-DD — [category] Title

- **Context:**
- **Observation:**
- **Relevance to build:**
```

Categories in use so far: `use-case`, `workspace`, `behavior`, `idea`, `bug`.
Add new ones as needed — this list isn't fixed.
