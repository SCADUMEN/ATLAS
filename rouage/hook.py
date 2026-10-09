"""The train in a live session: one winding per prompt, and the dial it drew.

Specification: overlays/le-rouage.md
Entrypoint:    bin/atlas-route (the UserPromptSubmit hook)

Until this existed the train ran only for the dial pages and the tests. In a
real conversation, which member convened was the barrel reading skill
descriptions and cooperating - the exact arrangement barillet.py calls "works,
and is not a mechanism". This module is the caller the train was waiting for:
every prompt the Operator submits is routed through route(), recorded through
record_winding(), and - when the train has something to show - drawn as
Le Cadran's face.

Two surfaces leave here, and they are the two the Trace docstring separates:

  - systemMessage is the dial. Claude Code shows it to the Operator directly,
    so the face is drawn by the router and never transcribed by the model.
    hardware/le-boitier.md: the display never shows a state the router did not
    produce. A dial the model redrew would be one.
  - additionalContext is what the barrel needs: the seats, in precedence order,
    and where each one's core lives. Held members are counted, never named -
    le-sas.md keeps them out of the prose, and the barrel writes the prose.

The hook never blocks a prompt. Every failure ends in exit 0; a fault in the
train is reported on the dial's channel instead of drawing a dial the train did
not produce.

    echo '{"prompt": "release the hound"}' | bin/atlas-route
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from rouage import REPO, Trace, fold, load_ring, record_winding, route  # noqa: E402

# The rite's own command. `/atlas` with or without words after it winds the
# crown, and a wound crown always shows the train it set going.
RITE = "/atlas"

# Skills that already draw the dial for the utterance they were given. Drawing
# it again from the hook would put two faces on one turn.
SELF_DRAWING = ("/atlas:le-cadran", "/atlas:le-conseil")


def utterance_of(prompt: str) -> tuple[str | None, bool]:
    """What the train should route, and whether this prompt winds the crown.

    Returns (None, False) for a prompt the hook must leave alone.
    """
    text = prompt.strip()
    head, _, rest = text.partition(" ")
    if head in SELF_DRAWING:
        return None, False
    if head == RITE:
        return rest.strip(), True
    return text, False


def speaks(trace: Trace) -> bool:
    """Whether the train did anything beyond Le Sceptique's standing watch.

    A sealed or held member still matched, and a failure or a notice is the
    train reporting on itself - all of it is shown. Only the bare standing turn
    is silent, because it is every turn.
    """
    if trace.failures or trace.notices or trace.route:
        return True
    return any(not c.member.standing for c in trace.candidates)


def slug(name: str) -> str:
    """'Le Rédempteur' -> 'le-redempteur', the name its files go by."""
    return "-".join(fold(name).split())


def where(name: str) -> str:
    s = slug(name)
    if (REPO / "skills" / s / "SKILL.md").exists():
        return f"skill `atlas:{s}`"
    return f"`subroutines/{s}.md`, OPERATIONAL CORE"


def gate(reason: str) -> str:
    kind, _, detail = reason.partition(":")
    return f'{kind}: "{detail}"' if detail else kind


def context_for(trace: Trace, wound: bool) -> str:
    """The barrel's half. Seats by name; held members by count only."""
    lines = [
        "# Le Rouage — this prompt's winding",
        "",
        "The going train routed this prompt against every member's named gate, "
        "literally. It read nothing for meaning: the automatic half of each "
        "gate is still yours to weigh.",
        "",
        "Le Cadran has already been drawn for the Operator by the hook. Do not "
        "redraw it, transcribe it, or compose one.",
    ]
    if wound:
        lines += ["", "This prompt winds the crown. The Arrival rite governs "
                  "the reply; the seats below are what the train set going."]

    active = [c for c in trace.candidates
              if c.state == "active" and not c.member.standing]
    if active:
        lines += ["", "Convened, in precedence order. Load each one's "
                  "OPERATIONAL CORE and follow its output contract:"]
        lines += [f"- {c.member.name} ({c.member.position}) — {gate(c.reason)}"
                  f" → {where(c.member.name)}" for c in active]

    sealed = [c for c in trace.candidates if c.state == "sealed"]
    if sealed:
        lines += ["", "Sealed — named, not armed. Stays dark unless "
                  "L'Opérateur arms it for a turn:"]
        lines += [f"- {c.member.name} ({c.member.position}) — {gate(c.reason)}"
                  for c in sealed]

    held = sum(1 for c in trace.candidates if c.state == "held")
    if held:
        lines += ["", f"Held by Le Sas: {held}. Held members are not loaded and "
                  "are not named, listed, or marked absent in the reply."]

    if trace.route:
        lines += ["", f"Route {trace.route}: aimed at "
                  f"{trace.route_aimed or '—'}, ended at {trace.route_end or '—'}."]
    for note in trace.notices:
        lines.append(f"Notice: {note}")
    for fault in trace.failures:
        lines.append(f"Recorded failure: {fault}")
    return "\n".join(lines)


def dial_for(trace: Trace) -> str:
    """The Operator's half: the face, uncoloured.

    Plain text, because a hook message is not guaranteed to be a terminal and
    the escape codes would show as noise - the same reason the skills leave
    --color off the panel they reproduce.
    """
    # Imported here, as cadran_ascii does: the face pulls in the dial geometry,
    # and a turn that draws nothing should not pay for it.
    from cadran_face import face
    return face(trace)


def winding_log(env: dict[str, str]) -> Path | None:
    """Where the crown's log lives. Per-user, beside the operator profile."""
    if env.get("ATLAS_NO_WINDING") == "1":
        return None
    if env.get("ATLAS_WINDING_LOG"):
        return Path(env["ATLAS_WINDING_LOG"])
    home = env.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(home) / "atlas" / "windings.jsonl"


def respond(prompt: str, env: dict[str, str], when: str) -> dict | None:
    """One prompt in, the hook payload out - or None to stay silent."""
    if env.get("ATLAS_NO_ROUTE") == "1":
        return None
    utterance, wound = utterance_of(prompt)
    if utterance is None:
        return None

    try:
        trace = route(load_ring(), utterance)
    except Exception as exc:  # the hook must never take a prompt down with it
        return {"systemMessage":
                f"Le Cadran — the train faulted and drew nothing: "
                f"{type(exc).__name__}: {exc}"}

    unrecorded = None
    log = winding_log(env)
    if log is not None:
        try:
            record_winding(trace, log, when)
        except OSError as exc:
            unrecorded = f"winding not recorded: {exc}"

    shown = wound or speaks(trace)
    messages = []
    if shown:
        try:
            messages.append(dial_for(trace))
        except Exception as exc:
            messages.append(f"Le Cadran — the face faulted: "
                            f"{type(exc).__name__}: {exc}")
    if unrecorded:
        messages.append(unrecorded)

    payload: dict = {}
    if messages:
        payload["systemMessage"] = "\n".join(messages)
    if shown:
        payload["hookSpecificOutput"] = {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context_for(trace, wound),
        }
    return payload or None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
        prompt = event.get("prompt")
    except (ValueError, AttributeError):
        return 0
    if not isinstance(prompt, str):
        return 0
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = respond(prompt, dict(os.environ), when)
    if payload:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
