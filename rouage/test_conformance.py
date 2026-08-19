"""The two trains must agree, and this is where that is checked.

rouage.py routes in Python; rouage/train.js routes in the browser. That is a
second implementation of the stage logic, which is exactly the duplication the
rest of this build refuses - the roster, the ladder, the cap and every phrase
are parsed from markdown precisely so nothing is written twice.

The duplication is survivable on two conditions, and both are mechanical:

  1. **No gate vocabulary in JS.** emit.py generates all of it from doctrine.
     train.js contains the algorithm and nothing a doctrine edit could stale.
  2. **The engines are shown to agree**, not asserted to. This runs the same
     matrix through both and compares traces field by field.

If these fail, the browser dial is lying about what the council did, which is
the one thing the instrument exists not to do.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

import emit
from rouage import load_ring, route

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")

UTTERANCES = [
    "what happened here",
    "run Publish",
    "run Harden",
    "run Judgement",
    "rename this file",
    "red team my backups",
    "preserve this, map this, security check, argue against this",
    "preserve this, map this, security check, argue against this, classify this",
    "I need to build a shelf this weekend",
    "a build, repair, or project has more than three interacting parts",
    "build this",
    "take Recover",
    "route Exhibit",
    "run Publish, security check",
]
ARMED = [None, "Le Fripon"]


def js_traces(cases) -> list[dict]:
    script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
const D = {emit.as_json()};
const cases = {json.dumps(cases, ensure_ascii=False)};
console.log(JSON.stringify(cases.map(([u, a]) => route(D, u, a))));
"""
    out = subprocess.run([NODE, "--input-type=module", "-e", script],
                         capture_output=True, text=True, cwd=HERE)
    if out.returncode:
        raise AssertionError(out.stderr[:2000])
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "node not available")
class TheTwoTrainsAgree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.cases = [(u, a) for u in UTTERANCES for a in ARMED]
        cls.js = js_traces(cls.cases)

    def _py(self, u, a):
        return route(self.ring, u, a).to_dict()

    def test_positions_and_states_match(self):
        for (u, a), j in zip(self.cases, self.js):
            p = self._py(u, a)
            self.assertEqual(
                [(x["position"], x["state"]) for x in p["positions"]],
                [(x["position"], x["state"]) for x in j["positions"]],
                f"{u!r} armed={a}")

    def test_the_reason_each_member_convened_matches(self):
        for (u, a), j in zip(self.cases, self.js):
            p = self._py(u, a)
            self.assertEqual([x["reason"] for x in p["positions"]],
                             [x["reason"] for x in j["positions"]],
                             f"{u!r} armed={a}")

    def test_route_readings_match(self):
        # The three hands read from these, so a disagreement here is the
        # browser dial pointing somewhere the council never went.
        for (u, a), j in zip(self.cases, self.js):
            p = self._py(u, a)
            self.assertEqual(p["route"], j["route"], f"{u!r}")
            self.assertEqual(p["route_end"], j["routeEnd"], f"{u!r}")
            self.assertEqual(p["route_aimed"], j["routeAimed"], f"{u!r}")

    def test_the_precedence_ordering_matches(self):
        # The hour hand reads from this. Deriving it from display order gives
        # the lowest hour number instead of the least reversible member, which
        # is a different claim entirely.
        for (u, a), j in zip(self.cases, self.js):
            self.assertEqual(self._py(u, a)["admitted"], j["admitted"],
                             f"{u!r} armed={a}")

    def test_faults_and_notices_match(self):
        for (u, a), j in zip(self.cases, self.js):
            p = self._py(u, a)
            self.assertEqual(p["failures"], j["failures"], f"{u!r} armed={a}")
            self.assertEqual(p["notices"], j["notices"], f"{u!r} armed={a}")

    def test_the_stage_sequence_matches(self):
        for (u, a), j in zip(self.cases, self.js):
            self.assertEqual(self._py(u, a)["stages"], j["stages"], f"{u!r}")

    def test_the_js_engine_hardcodes_no_member_or_route_vocabulary(self):
        # The condition that keeps one implementation authoritative: a doctrine
        # edit must not leave a stale copy behind in train.js.
        #
        # Scoped to vocabulary that cannot appear incidentally - member names,
        # activation phrases, route names, precedence entries. The invocation
        # verbs are excluded from the SCAN because they are bare common words
        # that collide with identifiers and message text ("route" appears in
        # `takeRoute` and in a notice string), and a substring check on common
        # words is exactly the bug this build just spent a commit removing from
        # take_route(). They get a behavioural test instead, below, which is
        # the stronger check anyway.
        src = (HERE / "train.js").read_text(encoding="utf-8")
        d = emit.doctrine(self.ring)
        vocabulary = (
            [m["name"] for m in d["members"]]
            + [p for m in d["members"] for p in m["phrases"]]
            + list(d["routes"]) + list(d["precedence"])
        )
        leaked = sorted({v for v in vocabulary if v.lower() in src.lower()})
        self.assertEqual(leaked, [],
                         f"train.js contains doctrine vocabulary: {leaked}")

    def test_the_js_engine_takes_its_invocation_verbs_from_the_data(self):
        # Behavioural, not textual: hand the engine a doctrine that says
        # `engage` and it must route on "engage Publish" - which it can only do
        # if it never hardcoded the verbs.
        d = emit.doctrine(self.ring)
        d["invoke"] = ["engage"]
        script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
const D = {json.dumps(d, ensure_ascii=False)};
console.log(JSON.stringify([
  route(D, "engage Publish").route,
  route(D, "run Publish").route,
]));
"""
        out = subprocess.run([NODE, "--input-type=module", "-e", script],
                             capture_output=True, text=True, cwd=HERE)
        self.assertEqual(out.returncode, 0, out.stderr[:800])
        engaged, ran = json.loads(out.stdout)
        self.assertEqual(engaged, "Publish", "engine ignored the doctrine verb")
        self.assertIsNone(ran, "engine kept a hardcoded verb")

    def test_the_js_engine_takes_its_cap_from_the_data(self):
        d = emit.doctrine(self.ring)
        d["cap"] = 2
        script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
const D = {json.dumps(d, ensure_ascii=False)};
const t = route(D, "preserve this, map this, security check, argue against this");
console.log(JSON.stringify(t.failures));
"""
        out = subprocess.run([NODE, "--input-type=module", "-e", script],
                             capture_output=True, text=True, cwd=HERE)
        self.assertEqual(out.returncode, 0, out.stderr[:800])
        self.assertTrue(any("cap 2" in f for f in json.loads(out.stdout)),
                        "engine ignored the doctrine cap")


if __name__ == "__main__":
    unittest.main()
