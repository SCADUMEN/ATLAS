"""The activation post-test: one arm's eval run -> calls, all arms -> analysis.

Two steps, because a run's trace lives in a temporary sandbox and is gone once
the runner cleans up (`claude plugin eval --keep-temp` holds it until then):

    python3 evals/analyze.py extract A <aggregate-result.json> <arm-A.calls.json>
    python3 evals/analyze.py report <analysis.json> <arm-A.calls.json> ...

`extract` keeps what the figures need from each run and nothing else: the
council Skill calls the barrel made, in order, with their args, read by the
same council_calls() the settle hook uses. `report` scores those calls against
evals/suite.json and replays every one through the current train - the arm
only changes what the barrel saw, so one admission rule judges all of them.

Every number here is a count of Skill calls. Nothing asks a model whether a
member convened, and nothing reads a reply for meaning.

Stdlib only, like the train it imports.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS.parent / "rouage"))
sys.path.insert(0, str(EVALS))

from hook import slug  # noqa: E402
from rouage import fold, load_ring, nearest, route  # noqa: E402
from settle import council_calls, proposals_for  # noqa: E402
import suite as catalogue  # noqa: E402

STANDING = catalogue.STANDING


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------

def calls_in(trace: Path) -> list[list[str]]:
    out = []
    for line in trace.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        out.extend([name, args] for name, args in council_calls(entry))
    return out


def extract(arm: str, aggregate: Path) -> dict:
    data = json.loads(aggregate.read_text(encoding="utf-8"))
    plugin = (data["suite"].get("plugins") or [{}])[0]
    runs = []
    for case in data["cases"]:
        for i, run in enumerate(case["arms"].get("with", [])):
            trace = Path(run["tracePath"]) if run.get("tracePath") else None
            runs.append({
                "case": case["name"],
                "run": i,
                "error": run.get("error"),
                "turns": run.get("turns"),
                "costUsd": run.get("costUsd"),
                "passed": run.get("passed"),
                # None, not [], when the run errored or the trace is gone:
                # "never called" and "could not look" are different findings.
                # A run cut off by a rate or session limit has a trace with
                # no calls in it, and counting that as silence would read an
                # outage as a member staying dark.
                "calls": (calls_in(trace) if not run.get("error")
                          and trace and trace.exists() else None),
            })
    return {
        "arm": arm,
        "version": plugin.get("version"),
        "model": data["suite"].get("modelOverride"),
        "startedAt": data.get("startedAt"),
        "costUsd": data.get("costUsd"),
        "partial": data.get("partial"),
        "runs": runs,
    }


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def rate(hits: int, n: int) -> float | None:
    return round(hits / n, 4) if n else None


def replay(ring, prompt: str, calls: list[list[str]]):
    """The settle hook's decision on this run, under the current doctrine."""
    return route(ring, prompt, proposals=proposals_for(ring, calls))


def member_slugs(trace) -> set[str]:
    return {slug(c.member.name) for c in trace.admitted()}


def score_arm(arm: dict, cases: dict, ring, members: list[str]) -> dict:
    runs = [r for r in arm["runs"] if r["calls"] is not None and r["case"] in cases]
    by_index = sorted({r["run"] for r in runs})
    seen = {r["run"]: Counter() for r in runs}           # run index -> member -> runs
    total = Counter(r["run"] for r in runs)
    stats = {m: Counter() for m in members}
    panel, invariants, kinds = Counter(), Counter(), {}
    citations, per_case = [], {}

    for r in runs:
        case = cases[r["case"]]
        called = {name for name, _ in r["calls"]}
        required, allowed = set(case["required"]), set(case["allowed"])
        forbidden = set(catalogue.forbidden_of(case, members))
        for m in called & set(members):
            seen[r["run"]][m] += 1
        for m in members:
            on = m in called
            stats[m]["calls"] += on
            if m in required:
                stats[m]["req_n"] += 1
                stats[m]["req_hit"] += on
                stats[m][f"req_n_{r['run']}"] += 1
                stats[m][f"req_hit_{r['run']}"] += on
            elif m in forbidden:
                stats[m]["forb_n"] += 1
                stats[m]["forb_hit"] += on
            elif m not in allowed and m != STANDING:
                stats[m]["theatre_n"] += 1
                stats[m]["theatre_hit"] += on

        k = kinds.setdefault(case["kind"], Counter())
        k["runs"] += 1
        k["any"] += bool(called - {STANDING})
        k["passed"] += bool(r["passed"])

        trace = replay(ring, case["prompt"], r["calls"])
        on_dial = member_slugs(trace) - {STANDING}
        panel[len(called - {STANDING})] += 1
        invariants["over_cap"] += any(c.state == "held" for c in trace.candidates)
        invariants["fripon_unarmed"] += ("le-fripon" in called
                                         and "le-fripon" not in required)
        invariants["fripon_on_dial_unarmed"] += ("le-fripon" in on_dial
                                                 and "le-fripon" not in required)
        invariants["inverted"] += sum("cited a prohibition" in f for f in trace.failures)
        invariants["calls"] += len(r["calls"])
        invariants["uncited"] += sum(1 for _, a in r["calls"] if not a.strip())

        by_slug = {slug(m.name): m for m in ring.members}
        for name, args in r["calls"]:
            member = by_slug.get(name)
            reason = " ".join(args.split())
            if member is None or not reason:
                continue
            _, activation = nearest(ring, reason, member.bullets)
            _, prohibition = nearest(ring, reason, member.prohibitions)
            refused = any(member.name in f and "prohibition" in f for f in trace.failures)
            citations.append({
                "member": name,
                "activation": activation,
                "prohibition": prohibition,
                "outcome": ("strict" if fold(member.name) in ring.strict
                            else "inverted" if refused else "admitted"),
            })

        pc = per_case.setdefault(r["case"], {"runs": 0, "passed": 0, "convened": Counter()})
        pc["runs"] += 1
        pc["passed"] += bool(r["passed"])
        pc["convened"].update(called)

    out_members = {}
    for m in members:
        s = stats[m]
        out_members[m] = {
            "calls": s["calls"],
            "activation": rate(sum(seen[i][m] for i in by_index), sum(total.values())),
            "activationRuns": [rate(seen[i][m], total[i]) for i in by_index],
            "recall": rate(s["req_hit"], s["req_n"]),
            "recallN": s["req_n"],
            "recallRuns": [rate(s[f"req_hit_{i}"], s[f"req_n_{i}"]) for i in by_index],
            "falseFire": rate(s["forb_hit"], s["forb_n"]),
            "falseFireN": s["forb_n"],
            "theatre": rate(s["theatre_hit"], s["theatre_n"]),
            "theatreN": s["theatre_n"],
        }
    return {
        "arm": arm["arm"],
        "version": arm["version"],
        "model": arm["model"],
        "costUsd": arm["costUsd"],
        "partial": arm["partial"],
        "runs": len(runs),
        "missingTraces": sum(1 for r in arm["runs"] if r["calls"] is None and not r["error"]),
        "errors": sum(1 for r in arm["runs"] if r["error"]),
        "members": out_members,
        "kinds": {k: {"runs": v["runs"], "anyMember": rate(v["any"], v["runs"]),
                      "casePass": rate(v["passed"], v["runs"])}
                  for k, v in sorted(kinds.items())},
        "panel": {str(k): v for k, v in sorted(panel.items())},
        "invariants": dict(invariants),
        "citations": citations,
        "cases": {name: {"runs": v["runs"], "passed": v["passed"],
                         "convened": dict(v["convened"])}
                  for name, v in per_case.items()},
    }


def matrix(arm: dict, cases: dict, members: list[str]) -> dict:
    """Required member (row) x convened member (column), as run fractions."""
    rows = [m for m in members if any(m in c["required"] for c in cases.values())]
    cells = []
    for row in rows:
        mine = [c for c in cases.values() if row in c["required"]]
        n = sum(arm["cases"].get(c["name"], {}).get("runs", 0) for c in mine)
        cells.append([rate(sum(arm["cases"].get(c["name"], {}).get("convened", {}).get(col, 0)
                               for c in mine), n) for col in members])
    return {"arm": arm["arm"], "rows": rows, "cols": members, "cells": cells}


def report(calls_files: list[Path]) -> dict:
    suite, ring = catalogue.load(), load_ring()
    members = catalogue.members()
    cases = {c["name"]: c for c in suite["cases"]}
    arms = [score_arm(json.loads(p.read_text(encoding="utf-8")), cases, ring, members)
            for p in calls_files]
    return {
        "cap": ring.cap,
        "threshold": ring.threshold,
        "members": members,
        "cases": [{"name": c["name"], "kind": c["kind"], "source": c["source"],
                   "required": c["required"], "allowed": c["allowed"],
                   "forbidden": catalogue.forbidden_of(c, members)}
                  for c in suite["cases"]],
        "arms": arms,
        "matrix": matrix(arms[-1], cases, members) if arms else None,
    }


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[0] == "extract":
        out = extract(argv[1], Path(argv[2]))
        Path(argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
        missing = sum(1 for r in out["runs"] if r["calls"] is None)
        print(f"analyze.py: arm {argv[1]}: {len(out['runs'])} runs, "
              f"{missing} without a trace -> {argv[3]}")
        return 0
    if len(argv) >= 3 and argv[0] == "report":
        out = report([Path(p) for p in argv[2:]])
        Path(argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
        print(f"analyze.py: {len(out['arms'])} arms -> {argv[1]}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
