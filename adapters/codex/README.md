# Codex adapter

Codex can read this repository directly when it is in the workspace. For a
downstream project or a barrel without access to the canonical checkout,
generate a doctrine-stripped runtime:

```sh
/absolute/path/to/ATLAS/bin/atlas-context \
  --mode portable \
  --output /absolute/path/to/PROJECT/atlas/AGENTS.md
```

The downstream root `AGENTS.md` should say to read project rules first, then
`atlas/AGENTS.md`. Review before replacing any existing file. The generated
header records both the ATLAS commit and the core fingerprint, so
`bin/atlas-doctor` can distinguish a reproducible bundle from remembered state.

Continuity remains downstream and private. To include it for one generated
handoff, pass `--continuity /absolute/path/to/PROJECT/.atlas/continuity.md`.
