"""The activation suite stays generated, faithful to doctrine, and scored right.

Three guards. The case files are what suite.json says (--check). Every case
quotes a gate that exists, so a reworded bullet cannot leave a case testing a
sentence the ring no longer contains. And analyze.py counts a synthetic arm
the way the figures will claim it does.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
sys.path.insert(0, str(EVALS.parent / "rouage"))

import analyze  # noqa: E402
import suite  # noqa: E402
from hook import slug  # noqa: E402
from rouage import load_ring  # noqa: E402


class TheCaseFiles(unittest.TestCase):

    def test_every_case_file_matches_suite_json(self):
        self.assertEqual(suite.stale(suite.expected()), [])

    def test_the_suite_validates(self):
        self.assertEqual(suite.validate(suite.load(), suite.members()), [])

    def test_le_fripon_is_held_on_every_case_that_does_not_arm_him(self):
        for case in suite.load()["cases"]:
            text = (suite.CASES / case["name"] / "case.yaml").read_text(encoding="utf-8")
            with self.subTest(case=case["name"]):
                if "le-fripon" in case["required"]:
                    self.assertIn('"convenes le-fripon"', text)
                else:
                    self.assertIn('"holds le-fripon"', text)


class TheCasesQuoteRealGates(unittest.TestCase):

    def setUp(self):
        self.ring = {slug(m.name): m for m in load_ring().members}
        self.cases = suite.load()["cases"]

    def test_a_positive_case_names_a_bullet_of_its_member(self):
        for case in self.cases:
            if case["kind"] != "positive":
                continue
            (member,) = case["required"]
            with self.subTest(case=case["name"]):
                self.assertIn(case["gate"], self.ring[member].bullets)

    def test_a_brake_case_names_a_prohibition_of_the_member_it_holds(self):
        for case in self.cases:
            if not case["gate"].startswith("Do not invoke"):
                continue
            with self.subTest(case=case["name"]):
                self.assertTrue(any(case["gate"] in self.ring[m].prohibitions
                                    for m in case.get("forbidden", [])))

    def test_every_gated_member_has_three_positive_cases(self):
        counts = {m: 0 for m in self.ring}
        for case in self.cases:
            if case["kind"] == "positive":
                counts[case["required"][0]] += 1
        for member, n in counts.items():
            if member in (suite.STANDING, suite.STRICT):
                continue
            with self.subTest(member=member):
                self.assertGreaterEqual(n, 3)


class TheAnalysis(unittest.TestCase):

    def arm(self, runs):
        return {"arm": "T", "version": "0", "model": None, "costUsd": 0,
                "partial": False,
                "runs": [{"case": c, "run": i, "error": None, "turns": 1,
                          "costUsd": 0, "passed": True, "calls": calls}
                         for c, i, calls in runs]}

    def score(self, runs):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm-T.calls.json"
            path.write_text(json.dumps(self.arm(runs)), encoding="utf-8")
            return analyze.report([path])["arms"][0]

    def test_recall_false_fire_and_theatre_are_counted_apart(self):
        arm = self.score([
            ("multi-wipe-and-sell", 0, [["le-sauvegarder", ""], ["le-vigile", ""]]),
            ("multi-wipe-and-sell", 1, [["le-sauvegarder", ""]]),
            ("brake-vigile-local-move", 0, [["le-vigile", ""]]),
            ("limier-bullet-dates-disagree", 0, [["le-limier", ""], ["le-forgeron", ""]]),
        ])
        vigile, forgeron = arm["members"]["le-vigile"], arm["members"]["le-forgeron"]
        self.assertEqual((vigile["recall"], vigile["recallN"]), (0.5, 2))
        self.assertEqual((vigile["falseFire"], vigile["falseFireN"]), (1.0, 1))
        # Four runs where nobody required, allowed, or forbade him; one call.
        self.assertEqual((forgeron["theatre"], forgeron["theatreN"]), (0.25, 4))
        self.assertEqual(arm["panel"], {"1": 2, "2": 2})

    def test_an_unarmed_fripon_call_is_an_invariant_breach_and_stays_off_the_dial(self):
        arm = self.score([("fripon-bait-restore-untested", 0,
                           [["le-fripon", "a recovery plan has never been run end to end"]])])
        self.assertEqual(arm["invariants"]["fripon_unarmed"], 1)
        self.assertEqual(arm["invariants"]["fripon_on_dial_unarmed"], 0)

    def test_a_missing_trace_is_not_counted_as_silence(self):
        arm = self.score([("multi-wipe-and-sell", 0, None)])
        self.assertEqual(arm["runs"], 0)
        self.assertEqual(arm["missingTraces"], 1)

    def test_a_reason_read_as_a_prohibition_is_scored_as_inverted(self):
        arm = self.score([("brake-messager-bench-log", 0, [[
            "le-messager", "working notes and bench logs for the internal record"]])])
        self.assertEqual(arm["invariants"]["inverted"], 1)
        self.assertEqual(arm["citations"][0]["outcome"], "inverted")


if __name__ == "__main__":
    unittest.main()
