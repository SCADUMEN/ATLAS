# Barrel adapter

The barrel is whichever model is executing Le Conseil. It is the only part of
the instrument that is not version-controlled — rented, finite, replaced — so
`overlays/le-barillet.md` records each one against the work it drove, sealed by
a serial: the SHA-256 of the ordered commit hashes of that work.

That seal was written by hand, which made it a claim. `bin/atlas-barillet`
derives it from git, so it becomes a check.

## Verify the records

Re-derive every serial in the doctrine from the range it names:

```sh
./bin/atlas-barillet verify
```

A recorded serial that no longer reproduces means the range is misquoted or the
history was rewritten. Both are loud, and both exit non-zero.

## Seal a session

```sh
export ATLAS_BARREL='Claude Opus 5 — `claude-opus-5`, via Claude Code'
./bin/atlas-barillet record v1.8.0..HEAD 'LE CLAUDÈ II'
```

That prints a Fitted Barrel block in the doctrine's own field shape — Fitted,
Barrel, Drove, Serial, and the `shasum` line to reproduce it — ready to paste
under `## Fitted Barrels`. What `record` emits, `verify` accepts; a test pins
the round trip so the emitted shape cannot drift from the parsed one.

The serial alone, for scripting:

```sh
./bin/atlas-barillet serial v1.8.0..HEAD
```

## The model is never guessed

`ATLAS_BARREL` is required and has no default. The host is detectable —
`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CODEX_HOME`, `AI_AGENT`, reported by
`./bin/atlas-barillet host` — but **nothing in the environment states which
model is fitted.** A record that inferred it would be the instrument writing
down a guess as evidence, which is the one thing the serial exists to prevent.
An unmarked environment reports `unknown host` rather than a plausible name.

Range arguments are anything `git rev-list` accepts. A range naming no commits,
or one absent from a shallow checkout, is refused rather than sealed empty.

Tests: `python3 -m unittest discover runtime -v`.
