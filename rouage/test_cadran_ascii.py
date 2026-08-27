"""Guards for the third display surface.

cadran_ascii.py is a readout, like dial.py and paint.js, and the same two
failures that stalk the other two stalk it: a state the surface cannot render,
and a trace field the surface silently drops. The rest of this build catches
those by asking the code what it covers rather than by reading it, so this does
the same for the panel.

Two of these mirror named guards elsewhere:

  - the marker-completeness test is dial.py's `_UNMAPPED` assert as a test;
  - the field-surfacing test is the fifth seam from test_conformance.py
    (`test_both_readouts_surface_every_trace_field`), pointed at the panel.
"""

from __future__ import annotations

import re
import unittest

from cadran_ascii import MARKER, dial_ascii
from dial import load_anatomy, owner_of
from rouage import STATES, load_ring, route


def flatten(panel: str) -> str:
    """Drop ANSI and collapse the wrapping. Word-wrap and colour are layout;
    what a guard checks is which facts reached the reader, and those survive as
    words in order once the frame and the escapes are removed."""
    plain = re.sub(r"\033\[[0-9;]*m", "", panel)
    # Drop the frame too: a wrapped field's continuation carries border glyphs
    # that would otherwise land between two fragments of one sentence. The box
    # rule (─) is distinct from the content em dash (—), so this loses nothing.
    plain = re.sub(r"[│┌┐└┘─]", " ", plain)
    return " ".join(plain.split())


class TheMarkersCoverEveryState(unittest.TestCase):

    def test_every_emittable_state_has_a_distinct_marker(self):
        # A missing glyph would fall through to `dark` and render as its own
        # opposite - the exact bug dial.py's assert was written against.
        need = set(STATES) | {"dark"}
        self.assertLessEqual(need, set(MARKER),
                             f"unmapped states: {need - set(MARKER)}")
        self.assertEqual(len(set(MARKER.values())), len(MARKER),
                         "two states share a glyph")


class ThePanelSurfacesEveryTraceField(unittest.TestCase):
    """One rich specimen exercises route, a split, held members, faults and
    notices at once, so every trace field carries content to look for."""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.trace = route(cls.ring, "run Publish", tiered=["Le Curateur"])
        cls.panel = dial_ascii(cls.trace, ring=cls.ring)
        cls.flat = flatten(cls.panel)
        cls.d = cls.trace.to_dict()

    def test_no_trace_field_is_silently_dropped(self):
        # Iterate the trace's OWN keys, so a field added to to_dict() later has
        # to be given a home in the panel or this fails - the property the
        # conformance suite asserts for paint.js, here for the panel.
        d = self.d
        checks = {
            "utterance": d["utterance"] in self.flat,
            "armed": "armed" in self.flat,
            "stages": all(s in self.flat for s in d["stages"]),
            "failures": all(" ".join(f.split()) in self.flat
                            for f in d["failures"]),
            "notices": all(" ".join(n.split()) in self.flat
                           for n in d["notices"]),
            "route": (d["route"] or "—") in self.flat,
            "route_end": (d["route_end"] or "—") in self.flat,
            "route_aimed": (d["route_aimed"] or "—") in self.flat,
            "admitted": (not d["admitted"])
            or f"hour → {d['admitted'][0]}" in self.flat,
            "positions": all(p["name"] in self.flat for p in d["positions"]
                             if p["state"] != "dark"),
        }
        uncovered = set(d) - set(checks)
        self.assertEqual(uncovered, set(),
                         f"trace field with no panel check: {uncovered}")
        for field, ok in checks.items():
            self.assertTrue(ok, f"trace field {field!r} did not reach the panel")

    def test_the_split_reads_where_the_route_was_aimed(self):
        # This specimen is cut short - tiering only Le Curateur holds the later
        # steps - so aimed and ended differ and the split hand must show it.
        self.assertNotEqual(self.d["route_aimed"], self.d["route_end"])
        self.assertIn(f"split → {self.d['route_aimed']}", self.flat)


class TheHonestyConstraintHolds(unittest.TestCase):

    def test_dark_positions_render_dark(self):
        # A routine convenes only the standing member; every other gate did not
        # fire and must read dark. No invented state.
        ring = load_ring()
        trace = route(ring, "rename this file")
        panel = dial_ascii(trace, ring=ring)
        lit = {p["position"] for p in trace.to_dict()["positions"]
               if p["state"] != "dark"}
        self.assertEqual(lit, {"01"}, f"unexpected lit seats: {lit}")

        for m in ring.hours:
            row = next(ln for ln in panel.splitlines()
                       if ln.lstrip("│ ").startswith(m.position + " "))
            if m.position in lit:
                self.assertIn(f"{MARKER['active']} active", row)
            else:
                self.assertIn(f"{MARKER['dark']} dark", row)


class TheBrakeIsASentence(unittest.TestCase):

    def test_the_brake_band_names_the_held_count(self):
        # A halt is a sentence, not a colour: the band states the count in words.
        ring = load_ring()
        trace = route(
            ring,
            "preserve this, map this, security check, argue against this",
            verdicts=[("Le Renégat", "Archive")],
        )
        panel = dial_ascii(trace, ring=ring)
        held = len(trace.halted)
        self.assertGreater(held, 0, "specimen did not engage the brake")
        # Ownership is parsed, not restated, even in the test.
        brake = owner_of(load_anatomy(), "brake")
        self.assertIn(f"{brake} · {held} held", panel)


if __name__ == "__main__":
    unittest.main()
