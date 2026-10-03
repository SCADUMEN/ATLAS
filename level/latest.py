#!/usr/bin/env python3
"""Decide whether a newer ATLAS release exists — the pure half of the check.

The network lives in the shell `level` script, which runs `git ls-remote` and
pipes its output here. This module never touches the network: it reads the
installed version as its first argument and the ls-remote lines on stdin, and
prints a single UPDATE line if — and only if — a strictly newer release tag is
published. Anything it cannot parse is skipped, and any shortfall of evidence is
silence. A launch must render whether or not this has anything to say.

    git ls-remote --tags --refs URL 'atlas--v*' | python3 level/latest.py 1.2.0

Releases are tagged `atlas--v<major>.<minor>.<patch>` (see the Release
workflow), so versions compare as integer triples — 1.10.0 is newer than 1.2.0,
which a string compare would get wrong.
"""

import re
import sys

# Matches a version anywhere in a token: bare "1.2.0", "v1.2.0", or the tag form
# "atlas--v1.2.0" / "refs/tags/atlas--v1.2.0".
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")
TAG = re.compile(r"atlas--v(\d+)\.(\d+)\.(\d+)")


def parse_version(text):
    """Return (major, minor, patch) from an installed version string, or None."""
    if not text:
        return None
    m = VERSION.search(text)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def latest_from_tags(lines):
    """Return the highest atlas--v<x.y.z> version across ls-remote lines, or None."""
    best = None
    for line in lines:
        for m in TAG.finditer(line):
            v = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if best is None or v > best:
                best = v
    return best


def update_line(current, tags_text):
    """The notice to print if a newer release exists, else None.

    `current` is the installed version string; `tags_text` is raw ls-remote
    output. Returns None whenever the current version is unknown, no valid tag is
    found, or nothing published is strictly newer.
    """
    cur = parse_version(current)
    if cur is None:
        return None
    latest = latest_from_tags(tags_text.splitlines())
    if latest is None or latest <= cur:
        return None
    return f"UPDATE: v{latest[0]}.{latest[1]}.{latest[2]} available — run /plugin to update"


def lag_line(installed, source):
    """The notice to print if the installed plugin trails the readout's tree.

    The readout reads its version from ATLAS_REPO when it is set, which is the
    source checkout - and the update check then compares that checkout, not
    what Claude Code is running, against the published tags. A source already
    at the newest tag over a stale install reads as current. This names the
    gap. Silence when either version is unknown or the install has caught up.
    """
    inst, src = parse_version(installed), parse_version(source)
    if inst is None or src is None or inst >= src:
        return None
    return (f"LAG: installed v{inst[0]}.{inst[1]}.{inst[2]} lags "
            f"source v{src[0]}.{src[1]}.{src[2]} — run /plugin to update")


def main(argv, stdin):
    # --lag INSTALLED SOURCE: compare two known versions; reads no stdin.
    if len(argv) > 1 and argv[1] == "--lag":
        line = lag_line(argv[2] if len(argv) > 2 else "",
                        argv[3] if len(argv) > 3 else "")
        if line:
            print(line)
        return 0
    current = argv[1] if len(argv) > 1 else ""
    line = update_line(current, stdin.read())
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv, sys.stdin))
