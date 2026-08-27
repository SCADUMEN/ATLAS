#!/usr/bin/env python3
"""Compute ATLAS's grade deterministically from overlays/le-grade.md.

No dependencies. Everything — the tier values, XP100, and the module ledger — is
parsed from the doctrine at runtime, so the number here and the number written in
the doctrine cannot drift. XP is only counted for a built/partial module whose
path actually exists: a grade is a claim about the repository, and the file is
the evidence.

    python3 grade/grade.py            full readout
    python3 grade/grade.py --oneline  one line, for a boot banner
"""

import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTRINE = os.path.join(REPO, "overlays", "le-grade.md")
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
        raise SystemExit("grade: XP100 not found in le-grade.md")
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


def grade_for(xp, xp100):
    if xp <= 0:
        return 0
    return min(100, math.floor(100 * math.sqrt(xp / xp100)))


def xp_for(grade, xp100):
    return xp100 * (grade / 100) ** 2


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

    grade = grade_for(xp, xp100)
    return dict(xp=xp, xp100=xp100, grade=grade, tiers=tiers,
                counted=counted, planned=planned, missing=missing)


def main(argv):
    r = compute()
    xp, xp100, grade = r["xp"], r["xp100"], r["grade"]

    if "--oneline" in argv:
        if xp > xp100:
            over = round((xp - xp100) / 1000)
            print(f"ATLAS — Grand Complication +{over} ({xp} XP)")
        else:
            print(f"ATLAS — Grade {grade} ({xp}/{xp100} XP)")
        return 0

    print(f"ATLAS — Grade {grade}")
    print(f"XP: {xp} / {xp100}")
    if grade < 100:
        nxt = grade + 1
        need = math.ceil(xp_for(nxt, xp100) - xp)
        print(f"Next: Grade {nxt} at {math.ceil(xp_for(nxt, xp100))} XP (+{need})")
    else:
        over = xp - xp100
        print(f"Prestige: Grand Complication +{round(over / 1000)} ({over} XP past 100)")
    print()
    print(f"Modules counted: {len(r['counted'])}  planned: {len(r['planned'])}")
    by_cat = {}
    for m in r["counted"]:
        by_cat.setdefault(m["category"], 0)
        by_cat[m["category"]] += m["xp"]
    for cat in sorted(by_cat):
        print(f"  {cat:12} {by_cat[cat]:>6} XP")
    if r["missing"]:
        print()
        print("WARNING — listed built but file missing (not counted):")
        for m in r["missing"]:
            print(f"  {m['id']}  ->  {m['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
