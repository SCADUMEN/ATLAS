"""The turn read again after the barrel acted: one dial, from what convened.

Specification: overlays/le-rouage.md (The Barrel's Contract)
Entrypoint:    bin/atlas-settle (the Stop hook)

bin/atlas-route winds the train when the prompt arrives, which is before the
barrel has read it. It can see the named half of every gate and nothing else,
so a dial drawn there could only ever show a member the Operator typed the name
of. The automatic half is the barrel's, and in a live session the barrel's
proposal is the skill call itself: invoking `atlas:le-limier` with the reason
as `args` is the `(member, citation)` pair admit_proposals() takes.

So this runs when the turn ends. It finds the turn's prompt in the transcript,
collects the council skill calls made after it, routes the prompt again with
those calls as proposals, and draws the face of what actually convened. One
face per turn, named and automatic together; nothing when nothing convened.

What it reads is the transcript's record of tool calls - which skill, which
args. It does not read the reply or the work for meaning: the barrel already
did that, and its decision is the skill call.

The hook never blocks the turn. Every failure ends in exit 0, and a fault in
the train is reported on the dial's channel, as hook.py does.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from hook import dial_for, slug, speaks, utterance_of, winding_log  # noqa: E402
from rouage import Ring, load_ring, record_winding, route  # noqa: E402

# The council's skills answer to atlas:<slug>. The displays and the git
# helper share the namespace and are not members.
SKILL_PREFIX = "atlas:"
NOT_MEMBERS = ("le-cadran", "le-conseil", "git-cleanup")

# A reason is a sentence or two. Args can be a whole task description - the
# one live proposal on record was - and the dial has no room for that.
REASON_LIMIT = 240

COMMAND = re.compile(r"<command-name>\s*([^<]+?)\s*</command-name>")
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def prompt_text(entry: dict) -> str | None:
    """The words of a user entry, or None if it is not a prompt.

    Tool results, skill bodies and other meta entries are not prompts. A slash
    command is recorded as markup; it comes back as the command line the
    Operator typed, which is the form hook.py's utterance_of() reads.
    """
    if entry.get("type") != "user" or entry.get("isMeta"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result"
               for b in content):
            return None
        content = "\n".join(b.get("text", "") for b in content
                            if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(content, str):
        return None
    name = COMMAND.search(content)
    if name:
        args = COMMAND_ARGS.search(content)
        return f"{name.group(1)} {args.group(1).strip() if args else ''}".strip()
    return content


def is_human(entry: dict) -> bool | None:
    """True/False where the transcript marks origin; None where it does not."""
    origin = entry.get("origin")
    if isinstance(origin, dict) and "kind" in origin:
        return origin["kind"] == "human"
    return None


def council_calls(entry: dict) -> list[tuple[str, str]]:
    """(skill slug, args) for each council skill call in an assistant entry."""
    if entry.get("type") != "assistant":
        return []
    calls = []
    for block in (entry.get("message") or {}).get("content") or []:
        if not (isinstance(block, dict) and block.get("type") == "tool_use"
                and block.get("name") == "Skill"):
            continue
        given = block.get("input") or {}
        skill = str(given.get("skill") or "")
        if not skill.startswith(SKILL_PREFIX):
            continue
        name = skill[len(SKILL_PREFIX):]
        if name in NOT_MEMBERS:
            continue
        calls.append((name, str(given.get("args") or "")))
    return calls


def last_turn(lines: list[str]) -> tuple[str | None, list[tuple[str, str]]]:
    """The last prompt and the council calls made after it.

    Walks backwards and stops at the first prompt. Where the transcript marks
    origin, only a human prompt ends the walk - a task notification or a hook's
    injected message is not the turn's prompt.
    """
    calls: list[tuple[str, str]] = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        calls[:0] = council_calls(entry)
        text = prompt_text(entry)
        if text is None or is_human(entry) is False:
            continue
        return text, calls
    return None, calls


def proposals_for(ring: Ring, calls: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Skill calls as proposals: the member the slug names, the args as reason."""
    by_slug = {slug(m.name): m.name for m in ring.members}
    out = []
    for name, args in calls:
        member = by_slug.get(name)
        if member is None:
            continue    # an atlas skill that is not on the ring
        reason = " ".join(args.split())[:REASON_LIMIT]
        out.append((member, reason))
    return out


def respond(event: dict, env: dict[str, str], when: str) -> dict | None:
    """One Stop event in, the hook payload out - or None to stay silent."""
    if env.get("ATLAS_NO_ROUTE") == "1" or event.get("stop_hook_active"):
        return None
    path = event.get("transcript_path")
    if not isinstance(path, str):
        return None
    try:
        lines = Path(path).read_text(encoding="utf-8",
                                     errors="replace").splitlines()
    except OSError:
        return None

    prompt, calls = last_turn(lines)
    if prompt is None:
        return None
    utterance, wound = utterance_of(prompt)
    # The rite has its own panel and the displays draw their own face.
    if utterance is None or wound:
        return None

    try:
        ring = load_ring()
        proposals = proposals_for(ring, calls)
        trace = route(ring, utterance, proposals=proposals)
    except Exception as exc:  # the hook must never take a turn down with it
        return {"systemMessage":
                f"Le Cadran — the train faulted and drew nothing: "
                f"{type(exc).__name__}: {exc}"}

    messages = []
    # hook.py already recorded this prompt. A settle entry is written only
    # when the barrel proposed something, so a quiet turn is logged once.
    log = winding_log(env)
    if proposals and log is not None:
        try:
            record_winding(trace, log, when, kind="settle",
                           proposals=proposals)
        except OSError as exc:
            messages.append(f"settle not recorded: {exc}")

    if speaks(trace):
        try:
            messages.insert(0, dial_for(trace))
        except Exception as exc:
            messages.insert(0, f"Le Cadran — the face faulted: "
                               f"{type(exc).__name__}: {exc}")
    return {"systemMessage": "\n".join(messages)} if messages else None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(event, dict):
        return 0
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = respond(event, dict(os.environ), when)
    if payload:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
