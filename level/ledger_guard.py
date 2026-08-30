#!/usr/bin/env python3
"""Check that the module ledger's evidence rule can actually be violated.

`level.py` earns XP only from a module whose path exists, and `release_guard.py`
leans on that: it treats rising XP as proof that a release added something,
"because a row pointing at a missing file scores nothing and would not move the
number." Both statements are true. Neither is sufficient.

The gap is that a path can exist *before* the row claims it. Three planned rows
in `overlays/le-niveau.md` name paths that are already in the tree, and two of
those paths are already counted by a different built row:

    le-rouage-complete  rouage/                  S = 1000 XP
    le-boitier-built    hardware/le-boitier.md   S = 1000 XP   (dup of le-boitier)
    barrel-adapter      overlays/le-barillet.md  A =  500 XP   (dup of le-barillet)

So 2500 XP — nearly a fifth of XP100, and enough to satisfy the release guard on
a minor bump — is reachable by changing the word `planned` to `built` three
times, with no work done and every existing check passing. The existence test
asks "does something live here?" when the invariant needs "did this release
produce it?" A path that predates its row is evidence of the past, not of the
claim being made.

This module is the pure half, in the shape of `latest.py` and `release_guard.py`:
it reads the ledger, reports what it finds, and decides nothing about severity
on its own — `verdict()` owns that, and it is doctrine, not code.

    python3 level/ledger_guard.py            check the repo's own ledger
    python3 level/ledger_guard.py --list     report findings, always exit 0

Exit 0 when the ledger is sound, 1 when `verdict()` says a finding must block.
"""

import os
import sys

from level import COUNTED, REPO, parse_ledger, parse_tiers, DOCTRINE


def duplicates(modules):
    """Rows that share a path, as [(path, [module, ...]), ...], ledger order.

    The rows themselves, not just their ids: `verdict()` needs each row's status
    to tell a double count from a roadmap pair, and rebuilding that association
    from a second pass over the ledger would be a copy that can drift.

    A path is the only evidence a row has. Two rows on one path means one file
    can be counted twice — and because tiers are summed blind, the second count
    is worth as much as the first.
    """
    order, by_path = [], {}
    for m in modules:
        if m["path"] not in by_path:
            order.append(m["path"])
            by_path[m["path"]] = []
        by_path[m["path"]].append(m)
    return [(p, by_path[p]) for p in order if len(by_path[p]) > 1]


def premature(modules, repo=REPO):
    """Planned rows whose path already exists — the ones that score on a word.

    Checked against `repo` rather than the cwd so this behaves the same from a
    worktree, the plugin cache, or CI, exactly as `level.compute()` does.
    """
    return [m for m in modules
            if m["status"] == "planned"
            and os.path.exists(os.path.join(repo, m["path"]))]


def unearned_xp(pre, tiers):
    """Total XP obtainable by flipping every premature row to `built`.

    Takes the rows `premature()` already found rather than finding them again:
    re-deriving them here would silently bind to the default repo and report the
    real ledger's number while judging someone else's — which is exactly the
    doctrine-and-code drift the ledger is built to prevent.

    Not a judgement — a magnitude. It is what makes the finding worth blocking
    on rather than noting, and it belongs in the message either way.
    """
    return sum(tiers.get(m["tier"], 0) for m in pre)


# ---------------------------------------------------------------------------
# THE POLICY — L'Opérateur's call, decided: block premature, tolerate the pair.
# ---------------------------------------------------------------------------

def verdict(dups, pre, tiers, modules):
    """Return a list of blocking messages; an empty list means the ledger passes.

    Two rules, and they are deliberately asymmetric.

    A PREMATURE ROW BLOCKS. A planned row whose file is already on disk scores
    its full tier the moment someone edits one word, with every existing check
    passing — that is the hole, and it is worth 2500 XP at the time of writing.
    The cost of blocking is that a roadmap row must name the artifact that will
    prove the work, not the artifact that describes it. That cost is the point:
    naming the evidence in advance is the part that makes the claim falsifiable.

    A ROADMAP DUPLICATE DOES NOT BLOCK. One built row and one planned row on the
    same path is honest bookkeeping — a spec and the intention to complete it —
    and it cannot inflate the score, because the planned half earns nothing until
    it is flipped, at which point the premature rule catches it. Any other shape
    blocks: two rows that both count are a double count of one file, and three
    rows on a path are not a pair by any reading.

    Note the two rules compose. Tolerating the roadmap pair is only safe because
    the premature rule is strict; if that one were ever softened to a warning,
    this one would have to harden in the same commit.
    """
    problems = []

    for path, rows in dups:
        planned = [m for m in rows if m["status"] == "planned"]
        counted = [m for m in rows if m["status"] in COUNTED]
        if len(rows) == 2 and len(planned) == 1 and len(counted) == 1:
            continue  # spec + its completion: cannot score twice, so let it stand
        ids = ", ".join(m["id"] for m in rows)
        problems.append(
            f"Duplicate path {path!r} claimed by {len(rows)} rows ({ids}). One file "
            f"is evidence for one module; rows that both count double-count it. "
            f"Give each row the path of the artifact that proves it."
        )

    if pre:
        total = unearned_xp(pre, tiers)
        listed = ", ".join(f"{m['id']} -> {m['path']}" for m in pre)
        problems.append(
            f"{len(pre)} planned row(s) name a path that already exists: {listed}. "
            f"Flipping them to `built` would score {total} XP with no work done and "
            f"every other check passing. A planned row must name an artifact that "
            f"does not exist yet — that is what makes finishing it provable."
        )

    return problems


def main(argv):
    with open(DOCTRINE, encoding="utf-8") as fh:
        md = fh.read()
    modules = parse_ledger(md)
    tiers = parse_tiers(md)

    dups = duplicates(modules)
    pre = premature(modules)

    if dups:
        print("Duplicate paths — one file, more than one row:")
        for path, rows in dups:
            ids = ", ".join(f"{m['id']} ({m['status']})" for m in rows)
            print(f"  {path:28} {ids}")
    if pre:
        print("Planned rows whose path already exists — these score on a word:")
        for m in pre:
            print(f"  {m['id']:22} {m['path']:28} tier {m['tier']}"
                  f" = {tiers.get(m['tier'], 0)} XP")
        print(f"  unearned XP reachable: {unearned_xp(pre, tiers)}")
    if not dups and not pre:
        print("Ledger sound: no duplicate paths, no planned row already on disk.")

    # --list reports without judging, for a human reading the ledger. The guard
    # proper is the default, so CI gets the strict behaviour without a flag.
    if "--list" in argv:
        return 0

    problems = verdict(dups, pre, tiers, modules)
    for message in problems:
        print(f"::error::{message}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
