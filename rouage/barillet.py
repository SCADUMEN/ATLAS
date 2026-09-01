"""LE BARILLET - the barrel boundary.

Specification: overlays/le-rouage.md, overlays/le-barillet.md
Train:         rouage.py (Python), train.js (browser)

Stage 6 is COLLECT, and it is the one stage the train cannot perform. Every
activation block has two halves: quoted phrases, which are matchable, and prose
bullets - "an artifact shows modification whose cause is unknown" - which are
not matchable without reading for meaning. The train is forbidden that reading.
So the barrel proposes and the train disposes.

`route()` has accepted `proposals` for some time and `admit_proposals()` has
enforced the Cited policy against them. What did not exist was the seam: a
defined thing the train hands out at COLLECT, and a defined thing it accepts
back. Until it existed, the automatic half of every gate was a model reading
markdown and cooperating - which works, and is not a mechanism.

This module is that seam, and it is deliberately thin:

  - It does not read the artifact. That is the barrel's whole job.
  - It does not re-run the train to enrich the brief. Duplicating stage logic
    here would make a third implementation of the thing the conformance test
    exists to keep at two.
  - It does not judge a citation. `read_proposals()` validates SHAPE only.
    Whether a citation is real is admit_proposals()' decision, and it records
    every rejection to the trace. Filtering bad citations out here would hide
    them from the audit surface - and a barrel that keeps citing text that is
    not there is precisely the signal worth keeping.

Stdlib only, like the train.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Optional, Tuple, Union

import rouage
from rouage import Proposal, Ring, Trace

# The keys a proposal object may carry. Anything else is a malformed proposal
# rather than an ignored field: a barrel inventing `confidence` or `because` is
# claiming an interface that does not exist, and silently dropping it would let
# it go on believing the claim landed.
KEYS = ("member", "citation", "evidence")


def brief(ring: Ring, utterance: str, armed: Optional[str] = None) -> dict:
    """What the train hands the barrel at COLLECT.

    The citation menu is `citations()` - positives only, because a prohibition
    is never valid grounds and offering one would make the menu the trap it
    exists to prevent.

    Deliberately absent: who the literal half already convened. Computing that
    means running evaluate() and take_route() here, which is stage logic, and
    stage logic in this file is the third implementation le-rouage.md refuses.
    A proposal naming an already-convened member is skipped by
    admit_proposals() anyway, so the cost of not saying is a wasted proposal,
    and the cost of saying is a train that exists three times.
    """
    return {
        "utterance": utterance,
        "armed": armed,
        "cap": ring.cap,
        "keys": list(KEYS),
        "citations": {name: list(bullets)
                      for name, bullets in rouage.citations(ring).items()},
    }


def brief_json(ring: Ring, utterance: str, armed: Optional[str] = None) -> str:
    return json.dumps(brief(ring, utterance, armed), ensure_ascii=False, indent=2)


def read_proposals(payload: Any) -> Tuple[list, list]:
    """Parse the barrel's return. Returns (proposals, rejections).

    Shape only - see the module docstring. A rejection here reads like a
    rejection from admit_proposals() because it belongs in the same list: both
    are the seam reporting that the barrel handed over something it should not
    have, and a caller should not have to look in two places for that.

    Accepts a JSON string, a list, or {"proposals": [...]}. `None` and empty
    input mean the barrel found nothing, which is not an error - most turns
    have no semantic half at all.
    """
    rejections: list = []

    if payload is None:
        return [], rejections

    data: Any = payload
    if isinstance(data, (str, bytes)):
        text = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
        if not text.strip():
            return [], rejections
        try:
            data = json.loads(text)
        except ValueError as exc:
            return [], [f"malformed proposals: not JSON ({exc})"]

    if isinstance(data, dict):
        if "proposals" not in data:
            return [], ["malformed proposals: object has no 'proposals' key"]
        data = data["proposals"]

    if not isinstance(data, list):
        kind = type(data).__name__
        return [], [f"malformed proposals: expected a list, got {kind}"]

    out: list = []
    for i, item in enumerate(data):
        where = f"proposal {i}"
        if not isinstance(item, dict):
            rejections.append(
                f"malformed {where}: expected an object, got {type(item).__name__}")
            continue

        unknown = sorted(k for k in item if k not in KEYS)
        if unknown:
            rejections.append(
                f"malformed {where}: unknown field(s) {', '.join(repr(k) for k in unknown)}"
                f" - the interface is {', '.join(KEYS)}")
            continue

        bad = False
        for required in ("member", "citation"):
            value = item.get(required)
            if not isinstance(value, str) or not value.strip():
                rejections.append(
                    f"malformed {where}: {required!r} must be a non-empty string")
                bad = True
        if bad:
            continue

        evidence = item.get("evidence")
        if evidence is not None and (not isinstance(evidence, str) or not evidence.strip()):
            rejections.append(
                f"malformed {where}: 'evidence' must be a non-empty string when present")
            continue

        if evidence is None:
            out.append((item["member"], item["citation"]))
        else:
            out.append((item["member"], item["citation"], evidence))

    return out, rejections


def turn(
    ring: Ring,
    utterance: str,
    payload: Any = None,
    armed: Optional[str] = None,
    verify: Optional[Callable[[str], bool]] = None,
    require_evidence: bool = False,
    **kwargs: Any,
) -> Trace:
    """One turn of the train with the barrel's half wired in.

    Malformed proposals are appended to `trace.failures` after the train's own
    rejections. They are not raised: one badly shaped item should cost that
    item, not the turn. A turn whose every proposal was malformed routes
    exactly as a turn with no barrel at all, and the trace says why.
    """
    proposals, rejections = read_proposals(payload)
    trace = rouage.route(
        ring, utterance, armed=armed, proposals=proposals,
        verify=verify, require_evidence=require_evidence, **kwargs)
    trace.failures.extend(rejections)
    return trace
