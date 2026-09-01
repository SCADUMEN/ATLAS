#!/usr/bin/env python3
"""Compute ATLAS's level deterministically from overlays/le-niveau.md.

No dependencies. Everything — the tier values, XP100, and the module ledger — is
parsed from the doctrine at runtime, so the number here and the number written in
the doctrine cannot drift. XP is only counted for a built/partial module whose
path actually exists: a level is a claim about the repository, and the file is
the evidence.

    python3 level/level.py            full readout
    python3 level/level.py --oneline  one line, for a boot banner
    python3 level/level.py --xp       the integer XP only, for machine parsing
    python3 level/level.py --service  the integer service points only
    python3 level/level.py --prestige the integer Grand Complication count only

Service is a second axis and is deliberately kept off the XP path: a repair
builds no module, so it moves no level. It records that the modules already
counted are still true. See "The Service Record" in the doctrine.
"""

import math
import os
import re
import sys

import service

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTRINE = os.path.join(REPO, "overlays", "le-niveau.md")
COUNTED = ("built", "partial")


def _rows(md, header):
    """Yield the cells of each pipe-table row in the section under `header`."""
    lines = md.splitlines()
    in_section = False
    for line in lines:
        if line.lstrip().startswith("#"):
            in_section = header in line
            continue
        if in_section and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # skip the header row and the |---|---| separator
            if not cells or set("".join(cells)) <= set("-: "):
                continue
            yield cells


def parse_tiers(md):
    tiers = {}
    for cells in _rows(md, "Tiers"):
        if len(cells) >= 2 and re.fullmatch(r"[SABCD]", cells[0]) and cells[1].isdigit():
            tiers[cells[0]] = int(cells[1])
    return tiers


def parse_xp100(md):
    m = re.search(r"XP100\s*=\s*(\d+)", md)
    if not m:
        raise SystemExit("level: XP100 not found in le-niveau.md")
    return int(m.group(1))


def parse_ledger(md):
    modules = []
    for cells in _rows(md, "The Module Ledger"):
        if len(cells) < 6:
            continue
        mid, name, category, tier, status, path = cells[:6]
        if tier not in "SABCD" or len(tier) != 1:
            continue
        modules.append(
            dict(id=mid, name=name, category=category, tier=tier,
                 status=status.lower(), path=path)
        )
    return modules


def level_for(xp, xp100):
    if xp <= 0:
        return 0
    return min(100, math.floor(100 * math.sqrt(xp / xp100)))


def xp_for(level, xp100):
    return xp100 * (level / 100) ** 2


def prestige_for(counted, xp100):
    """Grand Complication +N — the number of modules earned *past* XP100.

    The doctrine says N counts modules earned past XP100. "Past" needs an
    order, and the ledger is an ordered document, so this walks the counted
    modules in ledger order and counts those that begin entirely beyond the
    line: a module is past when the running total *before* it has already
    reached XP100.

    The module that crosses the line is the one that *reached* design-complete,
    not one earned beyond it, so it scores no prestige. That is deliberate. The
    previous rule read `round((xp - xp100) / 1000)` — a rounded thousand of XP,
    not a module count — which disagreed with the doctrine it was implementing
    and printed `Grand Complication +0` for any instrument sitting less than
    500 XP past the line. Counting modules makes +0 unreachable: prestige is
    either absent, and the readout says Level 100, or it is at least +1.
    """
    running = 0
    past = 0
    for m in counted:
        if running >= xp100:
            past += 1
        running += m.get("xp", 0)
    return past


def compute():
    with open(DOCTRINE, encoding="utf-8") as fh:
        md = fh.read()
    tiers = parse_tiers(md)
    xp100 = parse_xp100(md)
    modules = parse_ledger(md)

    counted, planned, missing = [], [], []
    xp = 0
    for m in modules:
        if m["status"] not in COUNTED:
            planned.append(m)
            continue
        if not os.path.exists(os.path.join(REPO, m["path"])):
            missing.append(m)
            continue
        m["xp"] = tiers.get(m["tier"], 0)
        xp += m["xp"]
        counted.append(m)

    # Service is computed after XP and never folded into it. A repair names the
    # module it kept true; a row naming no ledgered module is not scored, which
    # surfaces a gap in the ledger instead of inventing credit for it.
    svc, service_unledgered, service_pts = service.account(md, _rows, modules, tiers)

    level = level_for(xp, xp100)
    prestige = prestige_for(counted, xp100)
    return dict(xp=xp, xp100=xp100, level=level, tiers=tiers, prestige=prestige,
                counted=counted, planned=planned, missing=missing,
                service=svc, service_pts=service_pts,
                service_unledgered=service_unledgered)


def main(argv):
    r = compute()
    xp, xp100, level = r["xp"], r["xp100"], r["level"]

    service_pts = r["service_pts"]
    prestige = r["prestige"]

    if "--service" in argv:
        print(service_pts)
        return 0

    if "--prestige" in argv:
        print(prestige)
        return 0

    if "--xp" in argv:
        # Just the integer XP, for machine parsing (the release guard reads this).
        print(xp)
        return 0

    if "--oneline" in argv:
        if prestige:
            line = f"ATLAS — Grand Complication +{prestige} ({xp} XP)"
        else:
            # Level 100 is printed here, not skipped: crossing XP100 without a
            # module wholly past it is design-complete, not prestige. The XP
            # stays the first parenthesised integer either way — CI scrapes it.
            line = f"ATLAS — Level {level} ({xp}/{xp100} XP)"
        # Appended after the XP group so anything parsing the parenthesised XP
        # out of this line (the release guard in CI does) is unaffected.
        if service_pts:
            line += f" · Service {service_pts}"
        print(line)
        return 0

    print(f"ATLAS — Level {level}")
    print(f"XP: {xp} / {xp100}")
    if level < 100:
        nxt = level + 1
        need = math.ceil(xp_for(nxt, xp100) - xp)
        print(f"Next: Level {nxt} at {math.ceil(xp_for(nxt, xp100))} XP (+{need})")
    elif prestige:
        over = xp - xp100
        mods = "module" if prestige == 1 else "modules"
        print(f"Prestige: Grand Complication +{prestige} "
              f"({prestige} {mods} past XP100, {over} XP past 100)")
    else:
        print("Design-complete. Grand Complication +1 at the next module past XP100.")
    if service_pts or r["service"]:
        print(f"Service: {service_pts} pts across {len(r['service'])} "
              f"patch release{'' if len(r['service']) == 1 else 's'} "
              f"(does not raise the Level)")
    print()
    print(f"Modules counted: {len(r['counted'])}  planned: {len(r['planned'])}")
    by_cat = {}
    for m in r["counted"]:
        by_cat.setdefault(m["category"], 0)
        by_cat[m["category"]] += m["xp"]
    for cat in sorted(by_cat):
        print(f"  {cat:12} {by_cat[cat]:>6} XP")
    if r["service_unledgered"]:
        print()
        print("WARNING — service rows naming no ledgered module (not counted):")
        for row in r["service_unledgered"]:
            print(f"  {row['version']}  ->  {row['repaired']}")
    if r["missing"]:
        print()
        print("WARNING — listed built but file missing (not counted):")
        for m in r["missing"]:
            print(f"  {m['id']}  ->  {m['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
