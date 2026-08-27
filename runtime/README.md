# ATLAS runtime assembly

`bin/atlas-context` assembles three runtime shapes from ordered source manifests:

- `agent` emits the same core as a Claude Code plugin agent definition and
  writes `agents/atlas.md`. This is the Claude Code path. The core is inline
  because an agent's `skills:` field preloads only for subagents, not for the
  main-thread agent that `settings.json` activates.
- `compact` keeps the council in the canonical repository and loads subroutine
  cores on demand. It remains the inspectable view of what the agent carries.
- `portable` extracts every `OPERATIONAL CORE` and excludes every `DOCTRINE`
  section. This is the Codex and file-less handoff path.

Every output records a deterministic Git object fingerprint over its body, and
generation timestamps are deliberately absent. `compact` and `portable` also
record the source commit; `agent` does not, because it is committed and HEAD
moves the moment it lands — a stamp that goes stale on the next commit attests
to nothing.

A continuity capsule is outside the fingerprinted core and appears only when
selected. `agent` mode refuses one outright: the agent file is committed, and a
capsule is project-private.

Verify without invoking a model:

```sh
./bin/atlas-doctor
python3 -m unittest discover runtime -v
```
