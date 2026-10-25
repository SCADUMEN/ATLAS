"""The crown's log, read back as counts. Never as text.

windings.jsonl holds every routed prompt verbatim, which is why it lives in the
Operator's config home and never in a repository. This reads it for one
question - who convened, how, and how often - and prints numbers only. No
utterance, reason, or proposal text leaves this module; a report that quoted
the log would carry it wherever the report went.

Two kinds of entry share the log. The prompt-time entry (bin/atlas-route) sees
only what was typed, so anything it admits past Le Sceptique was named. The
settle entry (bin/atlas-settle, kind "settle") is the same turn read again
after the barrel acted, so a member it admits that the prompt entry did not is
one the barrel convened unnamed.

    python3 rouage/windings.py [--since YYYY-MM-DD] [--json] [LOG]
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from hook import winding_log  # noqa: E402
from rouage import load_ring  # noqa: E402

STANDING_POSITION = "01"

# A bare continuation: "ok", "yes", "do it", "shoot ropes". It carries no gate
# of its own, so a dark dial on it is the known limit of drawing per turn -
# measured here rather than patched. Word count is a proxy and says so.
CONTINUATION_WORDS = 3


def entries(log: Path, since: str | None = None) -> list[dict]:
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or "when" not in entry:
            continue
        if since and entry["when"][:10] < since:
            continue
        out.append(entry)
    return out


def summarize(log_entries: list[dict], names: dict[str, str]) -> dict:
    """Counts only. `names` maps a dial position to its member's name."""
    prompts = settles = continuations = continuations_lit = 0
    named, automatic, proposed = Counter(), Counter(), Counter()
    failures = Counter()
    per_day: dict[str, Counter] = defaultdict(Counter)
    days = set()

    # A settle entry follows its own prompt entry, so a turn is the prompt
    # entry plus any settle entry before the next prompt.
    turns: list[tuple[dict, dict | None]] = []
    for entry in log_entries:
        if entry.get("kind") == "settle":
            if turns and turns[-1][1] is None:
                turns[-1] = (turns[-1][0], entry)
            continue
        turns.append((entry, None))

    for prompt, settle in turns:
        prompts += 1
        day = prompt["when"][:10]
        days.add(day)
        at_prompt = set(prompt.get("admitted", [])) - {STANDING_POSITION}
        for pos in at_prompt:
            named[names.get(pos, pos)] += 1
        unnamed = set()
        if settle is not None:
            settles += 1
            unnamed = set(settle.get("admitted", [])) - at_prompt - {STANDING_POSITION}
            for pos in unnamed:
                automatic[names.get(pos, pos)] += 1
                per_day[day][names.get(pos, pos)] += 1
            for name, _reason in settle.get("proposals", []):
                proposed[name] += 1
            for failure in settle.get("failures", []):
                failures["inverted" if "prohibition" in failure
                         else "rejected"] += 1
        # Short is not enough: "release the hound" is three words and names
        # Le Limier, so a prompt that named anyone is not a bare continuation.
        if (not at_prompt
                and len(str(prompt.get("utterance", "")).split()) <= CONTINUATION_WORDS):
            continuations += 1
            continuations_lit += bool(unnamed)

    return {
        "first": min(days) if days else None,
        "last": max(days) if days else None,
        "prompts": prompts,
        "settles": settles,
        "lit": sum(1 for p, s in turns
                   if set(p.get("admitted", [])) - {STANDING_POSITION}
                   or (s and set(s.get("admitted", [])) - {STANDING_POSITION})),
        "named": dict(named.most_common()),
        "automatic": dict(automatic.most_common()),
        "proposed": dict(proposed.most_common()),
        "failures": dict(failures),
        "continuations": continuations,
        "continuationsDark": continuations - continuations_lit,
        "perDay": {d: dict(c) for d, c in sorted(per_day.items())},
    }


def render(s: dict) -> str:
    if not s["prompts"]:
        return "atlas-windings: no windings in range"
    lines = [
        f"windings {s['first']} .. {s['last']}",
        f"  prompts {s['prompts']}   lit past Le Sceptique {s['lit']}   "
        f"settle entries {s['settles']}",
        f"  continuations {s['continuations']}   dark "
        f"{s['continuationsDark']}",
    ]
    members = sorted(set(s["named"]) | set(s["automatic"]) | set(s["proposed"]))
    if members:
        lines.append("")
        lines.append(f"  {'member':<18}{'named':>7}{'auto':>7}{'proposed':>10}")
        for m in members:
            lines.append(f"  {m:<18}{s['named'].get(m, 0):>7}"
                         f"{s['automatic'].get(m, 0):>7}{s['proposed'].get(m, 0):>10}")
    if s["failures"]:
        lines.append("")
        lines.append("  refused " + ", ".join(f"{k} {v}" for k, v in s["failures"].items()))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    since = None
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if "--since" in args:
        i = args.index("--since")
        since = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    log = Path(args[0]) if args else winding_log(dict(os.environ))
    if log is None or not log.exists():
        print("atlas-windings: no winding log", file=sys.stderr)
        return 1
    names = {m.position: m.name for m in load_ring().members}
    summary = summarize(entries(log, since), names)
    print(json.dumps(summary, ensure_ascii=False, indent=1) if as_json
          else render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
