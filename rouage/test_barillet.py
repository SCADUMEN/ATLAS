"""The barrel boundary: shape at the seam, and the generated surfaces.

barillet.py validates what the barrel hands back. The line it must hold is
narrow and easy to get wrong in the generous direction: it checks SHAPE, never
meaning. A citation that is not real is admit_proposals()' business, and it
records the rejection to the trace. Filtering those out here would tidy the
audit surface by deleting the signal.

    python3 -m unittest discover rouage -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import barillet
import conformance
from rouage import load_ring

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


class TheBrief(unittest.TestCase):
    """What the train hands out at COLLECT."""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.b = barillet.brief(cls.ring, "what happened here")

    def test_it_offers_the_activation_bullets_verbatim(self):
        # The barrel is required to cite verbatim, which is only fair if it can
        # see exactly what it is quoting.
        for m in self.ring.members:
            if m.bullets:
                self.assertEqual(self.b["citations"][m.name], list(m.bullets))

    def test_it_never_offers_a_prohibition(self):
        # A guard is never valid grounds. Offering one would make the menu the
        # trap it exists to prevent.
        offered = {c for bullets in self.b["citations"].values() for c in bullets}
        for m in self.ring.members:
            for p in m.prohibitions:
                self.assertNotIn(p, offered,
                                 f"{m.name}'s prohibition was offered as citable")

    def test_it_does_not_reimplement_the_train(self):
        # The brief must not carry stage output. Computing it here would be a
        # third implementation of the thing the conformance test keeps at two.
        for forbidden in ("candidates", "admitted", "positions", "stages"):
            self.assertNotIn(forbidden, self.b)

    def test_it_serialises(self):
        json.loads(barillet.brief_json(self.ring, "x", armed="Le Fripon"))


class TheReturnPath(unittest.TestCase):
    """read_proposals(): shape only, and every refusal explains itself."""

    def parse(self, payload):
        return barillet.read_proposals(payload)

    def test_nothing_is_not_an_error(self):
        for empty in (None, "", "   ", [], "[]"):
            got, rejected = self.parse(empty)
            self.assertEqual((got, rejected), ([], []), repr(empty))

    def test_a_well_formed_pair_and_triple(self):
        got, rejected = self.parse(
            '[{"member":"A","citation":"b"},'
            ' {"member":"C","citation":"d","evidence":"e"}]')
        self.assertEqual(got, [("A", "b"), ("C", "d", "e")])
        self.assertEqual(rejected, [])

    def test_the_proposals_key_wrapper_is_accepted(self):
        got, _ = self.parse('{"proposals":[{"member":"A","citation":"b"}]}')
        self.assertEqual(got, [("A", "b")])

    def test_an_object_without_that_key_is_refused(self):
        _, rejected = self.parse('{"members":[]}')
        self.assertIn("no 'proposals' key", rejected[0])

    def test_broken_json_costs_the_payload_not_the_turn(self):
        got, rejected = self.parse("{not json")
        self.assertEqual(got, [])
        self.assertIn("not JSON", rejected[0])

    def test_a_scalar_payload_is_refused(self):
        _, rejected = self.parse("42")
        self.assertIn("expected a list", rejected[0])

    def test_an_unknown_field_is_refused_rather_than_ignored(self):
        # A barrel inventing `confidence` is claiming an interface that does
        # not exist. Dropping it silently lets it go on believing it landed.
        got, rejected = self.parse(
            '[{"member":"A","citation":"b","confidence":0.9}]')
        self.assertEqual(got, [])
        self.assertIn("'confidence'", rejected[0])

    def test_missing_and_empty_required_fields_are_refused(self):
        for payload in ('[{"member":"A"}]', '[{"citation":"b"}]',
                        '[{"member":"","citation":"b"}]',
                        '[{"member":"A","citation":"   "}]',
                        '[{"member":1,"citation":"b"}]'):
            got, rejected = self.parse(payload)
            self.assertEqual(got, [], payload)
            self.assertTrue(rejected, payload)

    def test_evidence_must_be_a_non_empty_string_when_present(self):
        for payload in ('[{"member":"A","citation":"b","evidence":""}]',
                        '[{"member":"A","citation":"b","evidence":7}]'):
            got, rejected = self.parse(payload)
            self.assertEqual(got, [], payload)
            self.assertIn("evidence", rejected[0])

    def test_one_bad_item_does_not_cost_the_good_ones(self):
        got, rejected = self.parse(
            '[{"member":"A","citation":"b"}, 7, {"member":"C","citation":"d"}]')
        self.assertEqual(got, [("A", "b"), ("C", "d")])
        self.assertEqual(len(rejected), 1)

    def test_shape_validation_does_not_judge_the_citation(self):
        # The line this module must hold. 'not a real bullet' is well-shaped
        # and passes here; the train rejects it, into the trace, where a
        # barrel repeatedly citing text that is not there stays visible.
        got, rejected = self.parse(
            '[{"member":"Le Limier","citation":"not a real bullet"}]')
        self.assertEqual(got, [("Le Limier", "not a real bullet")])
        self.assertEqual(rejected, [])


class TheWiredTurn(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.plain = next(m for m in cls.ring.members
                         if m.bullets and not m.sealed and not m.standing)

    def test_a_cited_proposal_convenes_through_the_seam(self):
        payload = json.dumps([{"member": self.plain.name,
                               "citation": self.plain.bullets[0]}])
        trace = barillet.turn(self.ring, "a quiet turn", payload)
        self.assertIn(self.plain.position, trace.to_dict()["admitted"])

    def test_malformed_items_land_in_failures_beside_the_trains_own(self):
        payload = json.dumps([{"member": self.plain.name, "citation": "nope"},
                              {"member": "X", "citation": "y", "extra": 1}])
        trace = barillet.turn(self.ring, "a quiet turn", payload)
        joined = " ".join(trace.failures)
        self.assertIn("cited text not found", joined)   # the train's rejection
        self.assertIn("unknown field", joined)          # the seam's rejection

    def test_an_all_malformed_payload_routes_as_an_unwired_train(self):
        import rouage
        bare = rouage.route(self.ring, "a quiet turn").to_dict()
        wired = barillet.turn(self.ring, "a quiet turn", "{not json}").to_dict()
        self.assertEqual(bare["admitted"], wired["admitted"])
        self.assertEqual(bare["positions"], wired["positions"])
        self.assertTrue(wired["failures"], "the trace did not say why")

    def test_no_payload_is_identical_to_no_barrel(self):
        import rouage
        self.assertEqual(rouage.route(self.ring, "run Publish").to_dict(),
                         barillet.turn(self.ring, "run Publish").to_dict())


def dump(name: str, text: str) -> str:
    """Write a generated artifact somewhere diffable and return the path.

    A guard over a 70KB generated file must not print the file. unittest's
    assertIn on two strings that size emits both in full, which buries the one
    line that says what to do. So the fresh render is written down, the message
    says where it went, and the evidence outlives the test run for diffing.
    """
    fd, path = tempfile.mkstemp(prefix=f"atlas-{name}-", suffix=".dump")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class TheGeneratedSurfaces(unittest.TestCase):
    """A generated file that has drifted still loads, so nothing else reports it.

    atlas-doctor already applies this rule to agents/atlas.md and the council
    skills. Two surfaces generated out of rouage/ were never enrolled: the
    conformance record, and the live dial - which inlines train.js verbatim, so
    an edit to the browser train leaves the shipped dial running the old one
    with nothing at all to say so.

    Two guards on the dial, deliberately. The first is cheap and names the
    likely cause; the second is exact and catches everything the first cannot
    see. A single guard here would either be too narrow to trust or too
    expensive to read.
    """

    @unittest.skipUnless(NODE, "node not available")
    def test_the_conformance_record_matches_a_live_run(self):
        fresh = conformance.render()
        committed = conformance.OUT.read_text(encoding="utf-8")
        if fresh != committed:
            self.fail(
                "CONFORMANCE.md no longer matches a live run of both engines. "
                "Regenerate: python3 rouage/conformance.py\n"
                f"Fresh record written to: {dump('conformance', fresh)}")

    def test_the_live_dial_carries_the_current_browser_train(self):
        """Guard 1 - cheap, and names the likely cause.

        The common drift is editing train.js and forgetting the dial. Checking
        containment says exactly that, without rendering anything.
        """
        dial = (HERE / "cadran-live.html").read_text(encoding="utf-8")
        train = (HERE / "train.js").read_text(encoding="utf-8").replace("export ", "")
        # assertTrue, not assertIn: the operands are 7KB and 70KB, and a
        # failure printing both is a guard nobody reads twice.
        self.assertTrue(
            train in dial,
            "cadran-live.html does not contain the current train.js — "
            "regenerate it: python3 rouage/live.py")

    def test_the_live_dial_is_byte_for_byte_what_live_py_emits(self):
        """Guard 2 - exact, and sees what guard 1 structurally cannot.

        Containment only proves the train got in. The dial also carries the
        doctrine JSON from emit.py, paint.js, the SVG geometry from dial.py and
        the page template itself; any of those can drift with train.js
        perfectly intact. Rendering fresh and comparing bytes covers all of it.

        Safe to do in a test because page() is pure - it returns the text and
        only main() writes the file, so this never touches the committed one.
        """
        import live
        fresh = live.page()
        committed = (HERE / "cadran-live.html").read_text(encoding="utf-8")
        if fresh != committed:
            self.fail(
                f"cadran-live.html is stale ({len(committed)} bytes committed, "
                f"{len(fresh)} fresh). Regenerate: python3 rouage/live.py\n"
                f"Fresh render written to: {dump('cadran-live', fresh)}")

    def test_the_render_is_deterministic(self):
        # Guard 2 is only meaningful if two renders of the same tree agree. A
        # timestamp or a set iteration in the page would make it flap, and a
        # flapping guard gets deleted rather than fixed.
        import live
        self.assertEqual(live.page(), live.page())


if __name__ == "__main__":
    unittest.main()
