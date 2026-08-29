#!/usr/bin/env python3
"""Fail a release that bumps the level's version without moving the level.

The doctrine in overlays/le-niveau.md earns XP only from a built module whose
file exists. A feature release is supposed to add such a module — but nothing
forced it, so nine releases shipped after v1.1.0 without the level ever moving.
This is the failproof: when a PR raises the major or minor version, the computed
XP must strictly increase. A patch bump is exempt (bug fixes need not level up),
and a version we cannot parse is never a reason to block a merge.

XP going *up* is a stronger signal than "a ledger row was added": level.py only
counts a module whose file exists, so a row pointing at a missing file scores
nothing and would not move the number. The shell gathers the four values (git
plumbing lives there); this module only decides. It mirrors latest.py, which is
the pure half of the update check and owns the semver parse reused here.

    python3 level/release_guard.py <base_ver> <head_ver> <base_xp> <head_xp>

Exit 0 and silent when the release is fine; exit 1 with a message when a
major/minor bump failed to raise the level.
"""

import sys

from latest import parse_version


def guard(base_version, head_version, base_xp, head_xp):
    """The violation message if the release must be blocked, else None.

    A block happens only when the (major, minor) pair strictly increased and the
    XP did not strictly increase. Everything else — patch-only bumps, no bump,
    a version that will not parse — returns None.
    """
    base = parse_version(base_version)
    head = parse_version(head_version)
    if base is None or head is None:
        return None
    # (major, minor) — a patch bump does not need to move the level.
    if head[:2] <= base[:2]:
        return None
    if head_xp > base_xp:
        return None
    return (
        f"Version bumped {base_version} -> {head_version} (minor or major), but the "
        f"level did not move: XP is still {head_xp}.\n"
        "A feature release must add a built module to overlays/le-niveau.md whose "
        "file exists, so `python3 level/level.py --xp` rises. See le-niveau.md — "
        "the loop is: build a module, list it as built with a real path, rerun the "
        "score. (A patch bump — fix/chore/docs/etc. — is exempt.)"
    )


def main(argv):
    if len(argv) != 5:
        print(
            "usage: release_guard.py <base_ver> <head_ver> <base_xp> <head_xp>",
            file=sys.stderr,
        )
        return 2
    base_version, head_version = argv[1], argv[2]
    try:
        base_xp, head_xp = int(argv[3]), int(argv[4])
    except ValueError:
        print(f"release_guard: XP arguments must be integers: {argv[3]!r} {argv[4]!r}",
              file=sys.stderr)
        return 2
    message = guard(base_version, head_version, base_xp, head_xp)
    if message:
        print(f"::error::{message}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
