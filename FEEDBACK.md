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

### 2026-08-28 — [workspace] Clone drift continued past the 2026-08-27 resolution

- **Context:** While appending the arrival-panel entry, resolved which clone
  was live before writing, specifically because the 2026-08-27 workspace entry
  warned about this hazard.
- **Observation:** That entry records the canonical clone being re-cloned to
  `~/Documents/ChatGPT/FORGOTTEN-INDUSTRIES/atlas` with `~/.claude/skills/atlas`
  repointed there. That path does not exist on this machine. The symlink now
  resolves to `~/projects/ATLAS/skills-standalone/atlas`. Four clones of the
  same remote are present: `~/ATLAS`, `~/projects/ATLAS`,
  `~/FORGOTTEN-INDUSTRIES/ATLAS`, and `~/Documents/Codex/2026-08-06/atlas`.
  `~/projects/ATLAS` is the only one with `FEEDBACK.md`, and the only one
  carrying the plugin layout (`.claude-plugin/`, `skills-standalone/`).
- **Relevance to build:** The recorded fix did not hold, and the count went up
  rather than down. Confirms the `bin/` helper proposed in the 2026-08-27 entry
  is worth building: resolve the live symlink, enumerate other local clones of
  the same remote, and report divergence. Note also that a feedback entry
  naming a canonical path goes stale silently — the helper's output is the
  durable answer, not a path written into prose.

### 2026-08-28 — [behavior] Arrival rite rendered without its ASCII panel

- **Context:** Session opened with `/atlas`. The generated `SKILL.md` supplied
  the full rite — BOOT READOUT, the FIRST LIGHT panel, and the greeting — with
  the instruction to reproduce it verbatim.
- **Observation:** The model emitted the greeting block (operator name, grade,
  the four-line council formula, the signoff) but silently dropped the FIRST
  LIGHT ASCII panel above it. Operator caught it with a one-word correction:
  `ascii`. Source files were verified intact afterward — the panel is present
  in `runtime/compact-coda.md` and in the generated skill text. The loss was in
  the model's reproduction, not in the repo.
- **Relevance to build:** This is the inverse of the 2026-08-27 entry above.
  That one was the rite firing too often; this is the rite firing incompletely.
  Both share a root: nothing verifies that the rite actually rendered as
  specified. A large verbatim ASCII block is exactly the content a model is
  most prone to abridge, and "reproduce verbatim" is an instruction with no
  enforcement behind it. If the panel is load-bearing, the durable fix is
  emitting it from outside the model — a hook or `bin/` helper that prints the
  masthead — rather than asking generation to be faithful to a block it can
  summarize away.

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
