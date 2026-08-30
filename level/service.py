#!/usr/bin/env python3
"""The service axis: upkeep recorded without touching the level.

A repair builds no module, so it moves no level — the instrument is no more
complete than it was. But an instrument that is not maintained loses the
integrity the level already claims for it, and that loss is silent: a module
keeps its full tier XP while the behaviour behind it rots, because the evidence
rule verifies that a path exists and a path is not a behaviour.

So service is a second axis. It never enters XP and never raises the Level.

The scale is derived from the module tiers rather than tuned separately: a
repair is worth a tenth of what it protects, so repairing the core counts for
more than repairing a convenience. One scale to keep honest, not two.

See "The Service Record" in overlays/le-niveau.md, which this module parses.
"""

import re

# A repair is worth a tenth of what it protects.
SERVICE_DIVISOR = 10


def credit(tier, tiers):
    """The service points earned by repairing a module of `tier`."""
    return tiers.get(tier, 0) // SERVICE_DIVISOR


def parse_credits(md, rows):
    """The credit table as written in the doctrine — a snapshot, not the truth.

    `credit()` derives the real value from the tier. A test asserts the two
    agree, the same way the level defers to the script rather than to prose.
    """
    out = {}
    for cells in rows(md, "Service credit"):
        if len(cells) >= 3 and re.fullmatch(r"[SABCD]", cells[0]) and cells[2].isdigit():
            out[cells[0]] = int(cells[2])
    return out


def parse_ledger(md, rows):
    """Service rows from the doctrine's Service Ledger.

    Only a patch release can be a service row: the evidence rule says a minor or
    major release is a module, and modules score XP, not service.
    """
    out = []
    for cells in rows(md, "The Service Ledger"):
        if len(cells) < 3:
            continue
        version, repaired, note = cells[:3]
        m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
        if not m or m.group(3) == "0":
            continue
        out.append(dict(version=version, repaired=repaired, note=note))
    return out


def account(md, rows, modules, tiers):
    """Score the service ledger against the module ledger.

    A row naming no ledgered module is not scored. That surfaces a gap in the
    ledger rather than inventing credit for it — the ledger being incomplete is
    a finding, not a licence.
    """
    by_id = {m["id"]: m for m in modules}
    scored, unledgered = [], []
    for row in parse_ledger(md, rows):
        mod = by_id.get(row["repaired"])
        if mod is None:
            unledgered.append(row)
            continue
        row["tier"] = mod["tier"]
        row["credit"] = credit(mod["tier"], tiers)
        scored.append(row)
    return scored, unledgered, sum(r["credit"] for r in scored)
