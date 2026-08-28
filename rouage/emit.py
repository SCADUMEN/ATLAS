"""Doctrine -> JSON, for the browser engine.

The interactive dial has to route in the browser, so the stage logic exists
twice: rouage.py and a small JS engine. That is a real cost and this module is
half of what makes it survivable - **no gate vocabulary is ever written in JS.**
The roster, every activation phrase, the precedence ladder, the cap, the named
routes and the invocation verbs are all parsed from markdown here and shipped
as data, exactly as the Python train reads them.

The other half is the conformance test, which runs the same input matrix
through both engines and asserts identical traces. Together: doctrine stays the
single source, the duplication is bounded to the algorithm, and the claim that
they agree is checked rather than asserted.
"""

from __future__ import annotations

import json

from dial import MECHANISMS, load_anatomy, owner_of
from rouage import Ring, load_invocations, load_ring, load_routes


def doctrine(ring: Ring | None = None) -> dict:
    """Everything the browser engine needs, and nothing it could invent."""
    ring = ring or load_ring()
    return {
        "cap": ring.cap,
        "precedence": list(ring.precedence),
        "invoke": list(load_invocations()),
        "routes": {name: list(steps) for name, steps in load_routes().items()},
        # The mechanisms panel, resolved here rather than in JS - ownership is
        # doctrine and the browser must not be able to name an owner the
        # anatomy table never gave it.
        "mechanisms": [
            {"part": part, "owner": owner_of(load_anatomy(), key), "note": note}
            for part, key, note in MECHANISMS
        ],
        "members": [
            {
                "position": m.position,
                "name": m.name,
                "phrases": list(m.phrases),
                "standing": m.standing,
                "sealed": m.sealed,
                "bullets": list(m.bullets),
                # Shipped so the browser cannot be handed a wider menu than
                # the Python train enforces. train.js does not read either
                # list today - it handles the literal half only - but a
                # doctrine field the two engines disagree about is the seam
                # the conformance test exists to keep closed.
                "prohibitions": list(m.prohibitions),
            }
            for m in ring.members
        ],
    }


def as_json(ring: Ring | None = None) -> str:
    return json.dumps(doctrine(ring), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    d = doctrine()
    print(f"members {len(d['members'])}  routes {len(d['routes'])}  "
          f"cap {d['cap']}  verbs {d['invoke']}")
    print(f"phrases {sum(len(m['phrases']) for m in d['members'])}  "
          f"bullets {sum(len(m['bullets']) for m in d['members'])}")
    print(f"{len(as_json())} bytes")
