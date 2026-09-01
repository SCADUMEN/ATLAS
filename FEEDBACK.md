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

### 2026-09-01 — [workspace] The published sheet had drifted, and neither input was recorded

- **Context:** Republishing the Le Cadran artifact from `rouage/cadran.html`.
  Closes the fix left open by the 2026-08-28 entry below on regenerating a
  committed generated artifact from the wrong input.
- **Observation:** Three findings, one cause. (1) The committed sheet still
  engraved `ATLAS` on the bezel and `LE SAUVEGARDER` on the crown, six commits
  after `le-conseil.md` reassigned both to `LE SAUVEGARDER` and `DELIBERATELY
  NO ONE`. The dial parses ownership from doctrine at render time and is
  correct by construction — but only when it is re-rendered, and nothing had
  re-rendered or compared it. (2) Regenerating to fix that reproduced the
  2026-08-28 failure exactly: a bare `dial.py` re-chose the specimen utterance
  and produced a 26-line diff for a 3-line change. (3) `render()` has carried a
  `standalone` parameter for the wrapper-less form since it was written, and
  nothing ever passed it — the published page had been built by hand-stripping
  the wrapper with `sed`, a step recorded nowhere and repeated from memory.
- **Relevance to build:** The 2026-08-28 entry named one unrecorded input; there
  were two, and the second reached further, because it stood between the repo
  and a surface outside it. A published artifact is the one output no test can
  see. Fixed: `SPECIMEN` records what the sheet depicts, so a bare `dial.py`
  reproduces it rather than replacing it; `--publish` writes the wrapper-less
  twin from the same trace in the same run, so the published page cannot depict
  a turn the committed sheet does not; and `TheSheetIsReproducible` asserts the
  sheet still equals what doctrine renders, which is the guard that would have
  caught (1) on the commit that caused it. The derived file is gitignored — it
  holds nothing `cadran.html` does not, and two blobs that must never disagree
  are the duplication `CONFORMANCE.md` exists to police.

### 2026-08-31 — [workspace] A fourth clone, and two blind spots in "is this tree safe to retire"

- **Context:** The 2026-08-30 untangle collapsed ATLAS to one working tree and
  attic'd three. Reconstructing an unrelated question today surfaced a *fourth*
  redundant tree it never touched, because it was a FORGOTTEN-INDUSTRIES clone
  rather than an ATLAS one: `~/Documents/ChatGPT/FORGOTTEN-INDUSTRIES`, 3.8 GB,
  15 days behind, sitting inside a declared-sensitive directory.
- **Observation:** Two things nearly went wrong while retiring it, and neither
  is caught by the checks the 08-30 untangle used.
  - **`git status` says nothing about linked worktrees.** The clone reported
    clean — 0 dirty, 0 stashes — while `git worktree list` showed a live Codex
    worktree at `~/.codex/worktrees/1cfd/FORGOTTEN-INDUSTRIES` on a detached
    HEAD. Moving the repo would have silently broken it. A clone-level clean
    check is not a tree-level clean check.
  - **`git log --all` does not reach another worktree's detached HEAD.**
    `--all` walks `refs/`, and a detached worktree HEAD is not under `refs/`.
    So the commit that worktree sat on (`e2f2d311`) was outside the
    unique-commit diff entirely. It turned out to be reachable from
    `codex/atlas-dossier-transcription`, which the survivor also has — but that
    was luck, established after the fact, not by the check that was run.
- **Relevance to build:** `bin/atlas-clones` answers "which clone is live, and
  what else shares its remote." Both gaps above sit just outside that question
  and would bite it the same way the renamed-remote gap did on 08-28: a tool
  built to catch a forgotten tree holding the only copy, blind to a *worktree*
  holding one. Two cheap additions would close it — enumerate
  `git worktree list --porcelain` per clone, and fold detached worktree HEADs
  into any reachability comparison rather than trusting `--all`.
- **Also worth recording:** nine of that clone's ten branches existed on no
  remote, so unlike the ATLAS attic there is no ~90-day GitHub backstop behind
  it. A 24 KB `git bundle` of the only two commits absent from the survivor now
  sits *outside* the attic at `~/fi-unique-2026-08-31.bundle`, so the
  2026-09-30 expiry deletion stays reversible without keeping 3.9 GB to do it.
  Absorption was verified per-commit by path-scoped diff, not
  `git branch --merged`, which under-reports on a squash-merging repo.

### 2026-08-28 — [behavior] A gate that inverted: prohibitions parsed as activations

- **Context:** Starting work on the barrel's proposal side — the semantic half
  of every gate, which hands `(member, citation)` pairs to
  `admit_proposals()`. Read the admission boundary before building against it,
  on the principle that a receiving socket should be understood before
  anything is wired into it.
- **Observation:** `parse_activation()` collected bullets with
  `^-\s+(.+)$` across the entire Activation section.
  `subroutines/le-redempteur.md` is the only file in the council carrying a
  gate-level prohibition list — a `**Do not fire on:**` block — so all five of
  its guards landed in `member.bullets` alongside the five real activations.
  `citations()` then offered them to the barrel as quotable, and
  `admit_proposals()` admitted one verbatim:
  `route(ring, '', proposals=[('Le Rédempteur', 'Matthew being tired, terse,
  or frustrated')])` returned position 12 **active** with `failures: []`, and
  engraved the guard on the dial as the reason it convened. Two facts make it
  structural rather than a typo. First, every member carries a
  `### Prohibitions` section, but those are *behavioural* — what a member must
  not do once convened; Le Rédempteur's block is *gate-level* — what must not
  convene him, and the schema had a home for the first kind and none for the
  second. Second, chronology: `git log --diff-filter=A` puts
  `le-redempteur.md` at 2026-06-13, two months before the burst of nine on
  08-15, so the one member who needed a negative gate invented one inline
  before a convention existed to follow.
- **Relevance to build:** This is the trust boundary of the instrument. The
  admission policy is recorded as L'Opérateur's own decision (Cited,
  2026-08-16), and the Cited policy was doing precisely what it promised —
  the *data* under it was wrong, not the check. It is the fifth instance of
  the family the four seam guards already cover, on a new axis: not surface
  behind mechanism, but **parser behind prose**. `bin/atlas-doctor` could not
  have caught it; nothing in the repo asserted the shape of a doctrine file.
  Closed by giving the negative gate a sanctioned section
  (`### Do Not Fire On`) rather than deleting the block to fit the schema —
  deleting it was considered and rejected, because the five guards are the
  most discriminating sentences in that gate and the proposal side will want
  them as negative guidance. Worth recording that the doctrine edit *alone*
  closed the leak, since the Activation regex already terminates on any
  `###`; the parser change is what turned eviction into classification rather
  than into silent discard. A cited prohibition now rejects with its own
  failure string, distinct from the generic "text not found", because a barrel
  quoting sloppily and a barrel inverting a gate are different faults and the
  louder one must not become the quieter one. Five of the nine new tests fail
  when the doctrine is mutated back to the inline form; the remaining four are
  vacuous under that mutation by design and guard the code axis instead.

### 2026-08-28 — [workspace] A committed generated artifact regenerated from the wrong input

- **Context:** `rouage/cadran.html` is generated by `dial.py` and committed.
  The Phase 2 change added one row to the mechanisms panel, so the sheet
  needed regenerating.
- **Observation:** Regenerating with an arbitrary utterance produced a 46-line
  diff rather than the expected one. The committed sheet had been rendered
  from `run Publish, security check` — positions 02, 04 and 10 lit, the
  Publish route — and the new render used `what happened here`, lighting 08.
  The panel row was in there, but so was a wholesale replacement of the
  specimen trace. Caught by asking why a one-row addition produced 46 lines,
  not by reading the diff. The original utterance was recoverable from the
  committed HTML itself (`>run Publish, security check<`), and re-rendering
  from it reduced the diff to the single intended line.
- **Relevance to build:** A generated artifact under version control carries
  an input that is not recorded anywhere except inside its own output. Nothing
  names the utterance `cadran.html` is supposed to demonstrate, so any
  regeneration silently re-chooses it, and the loss hides inside a diff that
  is expected to be large because the file is generated. The same hazard
  applies to `cadran-live.html`. Not fixed here. The cheap fix is to record
  the specimen utterance where `dial.py` can default to it, so regenerating
  without an argument reproduces the committed sheet instead of replacing it.

### 2026-08-28 — [bug] Discovery missed every linked worktree; `.git` is not always a directory

- **Context:** Immediately after #14 merged, `bin/atlas-clones` was run against
  this machine as verification. It reported 5 clones, verdict `ok`. A separate
  `find` for `ATLAS.md` performed earlier in the same session had surfaced
  `~/.codex/worktrees/atlas-continuity-95`, which the tool did not list.
- **Observation:** That path is a real ATLAS checkout on branch
  `codex/atlas-continuity-95`, origin `SCADUMEN/ATLAS`, not shallow, at scan
  depth 4 against `DEPTH=6` — so neither the depth limit, the prune list, nor
  the shallow-clone gap documented in #14 explains the miss. The cause is the
  discovery predicate itself: the scan tested `-type d -name .git`, and in a
  linked worktree `.git` is an 87-byte text file holding
  `gitdir: /Users/…/FORGOTTEN-INDUSTRIES/ATLAS/.git/worktrees/atlas-continuity-95`.
  Every linked worktree on the machine was therefore invisible. Harmless this
  instance: tree clean, and that branch is PR #4, merged. Widening the
  predicate to `\( -type d -o -type f \) -name .git` raises the count 5 → 6.
- **Relevance to build:** Third instance of one pattern in this tool. #13
  assumed a clone is identified by its origin URL; #14 corrected identity but
  kept the URL as one arm; this assumed a repository is identified by its
  on-disk layout. Each time the discovery predicate was narrower than the
  category being discovered, and each time the failure was silent — a `clean,
  in sync` report rather than an error. Worth treating "ask git rather than
  pattern-match the filesystem" as the default: `rev-parse --git-common-dir`
  answers "what repository is this" across clones, worktrees, and submodules in
  one call. Risk ranking also runs the wrong way here — a worktree is likelier
  than a clone to hold uncommitted work, since that is what worktrees are for,
  so the blind spot pointed at the highest-value target. Classification of
  worktrees as their own report entries (rather than folded into the parent) is
  the Operator's call, recorded in the second `OPERATOR DECISION` block:
  listing is information-preserving, folding is lossy, fold later if the noise
  earns it.

### 2026-08-28 — [behavior] Arrival rite did not fire; two trigger statements disagreed

- **Context:** Operator ran `/clear` followed by `/atlas` in sequence,
  deliberately and repeatedly, to reproduce boot behavior — a cold context is
  the only way to test the Arrival path, so `/clear` + `/atlas` is the repro
  procedure, not operator error. Third occurrence in the sequence.
- **Observation:** The rite did not fire at all. The model acknowledged the
  skill had loaded and declined the rite in one line, citing the absence of the
  boot signal, then proceeded into ordinary work. Both trigger statements were
  live in the session and they disagree. `runtime/compact-coda.md` gated the
  rite on the operator's first message being exactly `⟨wind the crown⟩` and
  added "Never perform the rite for any other message"; the generated
  `SKILL.md` contains zero occurrences of the boot signal and instructs
  "Perform the Arrival rite once" unconditionally. Neither is wrong on its own.
  `bin/atlas-rite-skill:5` states the skill exists "so the Operator can wind
  the crown by typing `/atlas`", the generator writes its own preamble at line
  104, and it lifts only the fenced panel from the coda — so the two triggers
  are intentionally different signals for the same act. The coda's prohibition
  was written absolutely and never carved out the skill path, so a session
  holding both artifacts can resolve either way.
- **Relevance to build:** This completes a set of three distinct failure modes
  of one mechanism: 2026-08-27 fired too often, the entry above fired
  incompletely, and this did not fire at all. The first and third share a
  single root — two authoritative trigger statements that contradict, making
  the outcome depend on which artifact a given session weights rather than on
  anything testable. `bin/atlas-doctor` passed throughout and was right to:
  it verifies the skill matches its source, and cannot detect that the two
  triggers are incompatible, because they are deliberately not identical.
  Nothing in the repo asserts a relationship between them. Closed here by
  carving the skill path into the coda's gate and stating explicitly that the
  prohibition covers unsignalled messages only, that the absence of one grip is
  not the absence of both, and that a rite silently failing to fire is a
  failure in the same way as one firing unbidden. Verified by regeneration:
  only `runtime/compact-coda.md` and `agents/atlas.md` change and `SKILL.md`
  stays byte-identical, so the skill path cannot regress from this edit. The
  incomplete-render mode is untouched and still needs the durable fix already
  recorded on 2026-08-28 — emit the masthead from outside the model, since
  "reproduce verbatim" has no enforcement behind it.

### 2026-08-28 — [workspace] The fifth clone was ours all along; ATLAS was renamed

- **Context:** The `[correction]` entry below records
  `~/Documents/Codex/2026-08-06/atlas` as belonging to a different repository,
  `Forgotten-Industries/ATLAS`, on the strength of its `remote.origin.url`.
  The Operator identified that as wrong: he owns both orgs.
- **Observation:** `gh api repos/Forgotten-Industries/ATLAS -q .full_name`
  returns `SCADUMEN/ATLAS`. It is not a second repository — it is the former
  name, and GitHub redirects it silently, so a clone left pointing at the old
  URL keeps fetching and pushing correctly while reporting an identity that no
  longer exists. Both share root commit `c8adac3`. The clone itself is a
  2026-06-14 snapshot, 24 commits behind, and every one of its commits is an
  ancestor of current `main` — verified with `git merge-base --is-ancestor`.
  Nothing is stranded there. Operator context for the record: the SCADUMEN org
  was created as an umbrella for the FI and ATLAS work so Tyler Etters could
  pick it up at his leisure; the transfer is the cause of the rename.
- **Relevance to build:** `bin/atlas-clones` matched clones on origin URL
  alone, so this one was skipped in silence. Harmless this time because nothing
  was at risk in it — but the tool exists precisely to catch a forgotten clone
  holding the only copy of something, and a renamed remote was a blind spot
  straight through the middle of that. Fixed by also matching on shared root
  commit, tested against a fixture where the old matcher reported
  `0 clones, verdict ok` on a dirty clone the new one flags `warn`. Remaining
  known gap, documented in the script: a shallow clone has no root object and
  is still missed.

### 2026-08-28 — [correction] The clone count in the entry below was wrong

- **Context:** Built `bin/atlas-clones` to answer "which clone is live, and what
  else shares its remote" mechanically. Ran it against the same disk the
  2026-08-28 `[workspace]` entry below describes.
- **Observation:** The entry is wrong in both directions. It names
  `~/Documents/Codex/2026-08-06/atlas` as a clone of this remote; its origin is
  actually `Forgotten-Industries/ATLAS`, a different repository. And it misses
  `~/.claude/plugins/marketplaces/scadumen`, the plugin marketplace checkout,
  which is a real clone of `SCADUMEN/ATLAS`. Corrected list, by tool: the
  marketplace checkout, `~/ATLAS`, `~/FORGOTTEN-INDUSTRIES/ATLAS`, and
  `~/projects/ATLAS` (live). None currently holds work that exists nowhere
  else.
- **Relevance to build:** Both errors came from eyeballing `find` output and
  reading directory names as identity. Neither would have survived checking
  `remote.origin.url`. This is the argument for the tool existing, made by the
  entry that prompted it: a path written into prose goes stale and cannot
  correct itself, which is why the original entry is annotated here rather than
  edited in place.

### 2026-08-28 — [workspace] Clone drift continued past the 2026-08-27 resolution

> **Superseded in part.** The clone list in this entry is inaccurate; see
> the `[correction]` entry above. The drift observation itself still holds.

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
