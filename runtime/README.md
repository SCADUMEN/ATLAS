# ATLAS runtime assembly

`bin/atlas-context` assembles two runtime shapes from ordered source manifests:

- `compact` keeps the council in the canonical repository and loads subroutine
  cores on demand. This is the Claude Code launcher path.
- `portable` extracts every `OPERATIONAL CORE` and excludes every `DOCTRINE`
  section. This is the Codex and file-less handoff path.

Both outputs record the source commit and a deterministic Git object
fingerprint. Generation timestamps are deliberately absent. A continuity
capsule is outside the fingerprinted core and appears only when selected.

Verify without invoking a model:

```sh
./bin/atlas-doctor
python3 -m unittest discover runtime -v
```
