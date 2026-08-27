# File-less agent adapter

Build one self-contained prompt containing the ATLAS core and every council
member's `OPERATIONAL CORE`, with all `DOCTRINE` sections excluded:

```sh
./bin/atlas-context --mode portable --output /tmp/atlas-portable.md
```

Paste or attach that bundle to the target agent. It contains an ATLAS source
commit and deterministic core fingerprint, but no generation timestamp.

Continuity is never added implicitly to a portable export. Include a capsule
only for a deliberate handoff:

```sh
./bin/atlas-context \
  --mode portable \
  --continuity /absolute/path/to/PROJECT/.atlas/continuity.md \
  --output /tmp/atlas-handoff.md
```

Treat the exported file as private when it contains a capsule. Delete or
archive it according to the downstream project's custody rules after use.
