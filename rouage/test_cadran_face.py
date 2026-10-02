"""Guards for the fifth display surface.

The face is a readout like the panel, so it is held to the same two failures:
a state it cannot render, and a trace field it drops or invents. It adds one
failure of its own, because it is a drawing - a frame that stops being square.
Every guard here asks the trace what should be shown and then looks for it,
rather than comparing against a stored picture that would bless whatever the
renderer last happened to draw.
"""

from __future__ import annotations

import re
import unittest

from cadran_ascii import MARKER
from cadran_face import HAND_TIP, face, hand_glyph
from premiere_lueur import WIDTH, dwidth
from rouage import load_ring, route

ANSI = re.compile(r"\033\[[0-9;]*m")


def framed_rows(text: str) -> list[str]:
    # The INPUT line sits outside the case on purpose; everything above it is
    # the instrument.
    return text.splitlines()[:-1]


class TheFaceIsSquare(unittest.TestCase):

    def test_every_row_is_the_frame_width(self):
        ring = load_ring()
        for utt in ("run Publish", "", "what happened here",
                    "preserve this, map this, security check, argue against this"):
            for color in (False, True):
                out = ANSI.sub("", face(route(ring, utt), ring=ring, color=color))
                widths = {dwidth(row) for row in framed_rows(out)}
                self.assertEqual(widths, {WIDTH}, f"{utt!r} color={color}")


class TheSeatsComeFromTheTrace(unittest.TestCase):

    def test_every_seat_shows_the_state_the_train_gave_it(self):
        ring = load_ring()
        for utt, kw in (("run Publish", {}),
                        ("run Publish", {"tiered": ["Le Curateur"]}),
                        ("red team my backups", {}),
                        ("argue against this, map this",
                         {"verdicts": [("Le Renégat", "Archive")]})):
            trace = route(ring, utt, **kw)
            state = {p["position"]: p["state"] for p in trace.to_dict()["positions"]}
            out = face(trace, ring=ring)
            for m in ring.hours:
                want = MARKER[state.get(m.position, "dark")]
                self.assertIn(f"{m.position}{want}", out,
                              f"{utt!r}: seat {m.position} should read {want}")

    def test_a_dark_turn_lights_only_what_the_train_lit(self):
        ring = load_ring()
        trace = route(ring, "publish this")
        lit = {p["position"] for p in trace.to_dict()["positions"]
               if p["state"] != "dark"}
        out = face(trace, ring=ring)
        for m in ring.hours:
            if m.position not in lit:
                self.assertIn(f"{m.position}{MARKER['dark']}", out)


class TheBandsSayWhatHappened(unittest.TestCase):

    def test_le_sas_reads_fault_exactly_when_the_trace_has_faults(self):
        ring = load_ring()
        for utt, kw in (("run Publish", {}),
                        ("run Publish", {"tiered": ["Le Curateur"]})):
            trace = route(ring, utt, **kw)
            out = face(trace, ring=ring)
            self.assertEqual("LE SAS · FAULT" in out,
                             bool(trace.to_dict()["failures"]), utt)

    def test_the_brake_appears_only_when_something_was_halted(self):
        ring = load_ring()
        calm = face(route(ring, "run Publish"), ring=ring)
        self.assertNotIn("LE FREIN", calm)
        trace = route(ring, "argue against this, map this",
                      verdicts=[("Le Renégat", "Archive")])
        # Asserted, not assumed: a guard on the brake that never sees the brake
        # engage would pass for a renderer that cannot draw it.
        self.assertTrue(trace.halted, "specimen no longer engages the brake")
        self.assertIn(f"LE FREIN · {len(trace.halted)} HELD",
                      face(trace, ring=ring))

    def test_the_undriven_complications_say_so(self):
        out = face(route(load_ring(), "run Publish"))
        self.assertIn("UNDRIVEN", out)


class TheHandsFollowTheTrace(unittest.TestCase):

    def test_no_route_means_no_minute_hand(self):
        ring = load_ring()
        trace = route(ring, "what happened here")
        self.assertIsNone(trace.to_dict()["route_end"])
        self.assertIn("minute → —", face(trace, ring=ring))

    def test_the_hands_name_the_seats_the_panel_names(self):
        ring = load_ring()
        trace = route(ring, "run Publish")
        d = trace.to_dict()
        out = face(trace, ring=ring)
        self.assertIn(f"hour → {d['admitted'][0]}", out)
        self.assertIn(f"minute → {d['route_end']}", out)


class TheHandsCannotBeReadAsSeats(unittest.TestCase):
    """A hand is drawn beside the seats it passes. If any cell of it shared a
    glyph with a state marker, a reader could take the hand for a reading -
    the same failure the distinct-marker guard in test_cadran_ascii.py stops
    between two states."""

    def test_no_hand_glyph_is_a_state_glyph(self):
        markers = set(MARKER.values())
        for h in range(12):
            for tip in (False, True):
                g = hand_glyph(h * 30.0, tip=tip)
                self.assertNotIn(g, markers,
                                 f"angle {h * 30} tip={tip} draws {g!r}")

    def test_opposite_seats_share_a_stroke(self):
        # One line through the pivot, whichever end the hand is on.
        for h in range(6):
            self.assertEqual(hand_glyph(h * 30.0), hand_glyph(h * 30.0 + 180))

    def test_every_hand_ends_in_its_tip(self):
        out = face(route(load_ring(), "run Exhibit"))
        self.assertEqual(out.count(HAND_TIP), 2, "hour and minute, one tip each")


class TheFaceIsDeterministic(unittest.TestCase):

    def test_same_turn_same_face(self):
        ring = load_ring()
        a = face(route(ring, "run Publish"), ring=ring)
        b = face(route(ring, "run Publish"), ring=ring)
        self.assertEqual(a, b)

    def test_colour_only_adds_escapes(self):
        # Colour may decorate the face, never change it: strip the escapes and
        # what remains must be the uncoloured face, character for character.
        trace = route(load_ring(), "argue against this, run Build",
                      verdicts=[("Le Renégat", "Archive")])
        self.assertEqual(ANSI.sub("", face(trace, color=True)),
                         face(trace, color=False))

    def test_no_colour_means_no_escapes(self):
        out = face(route(load_ring(), "run Publish"), color=False)
        self.assertIsNone(ANSI.search(out))


if __name__ == "__main__":
    unittest.main()
