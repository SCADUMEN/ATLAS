"""The live dial may move, but only through states the train produced.

rouage/tui/cadran.mjs animates every winding as a sequence of traces handed to
face(). hardware/le-boitier.md forbids a display showing a state the router
did not produce, so each frame must be a prefix of the real trace - a subset
of its seats, its admitted, its failures, a prefix of its stages, a hand
either absent or where the train put it - and the last frame must be the
trace itself, so the dial always comes to rest on what happened.

Skipped unless rouage/tui has been installed (npm ci in rouage/tui): the
Python side stays stdlib-only and CI does not need Ink to route.
"""

from __future__ import annotations

import json
import subprocess
import unittest

import emit
from test_conformance import ARMED, HERE, NODE, UTTERANCES

TUI = HERE / "tui"
INSTALLED = (TUI / "node_modules" / "ink").is_dir()


def js_frames(cases) -> list[dict]:
    script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
import {{ frames }} from {json.dumps(str(TUI / 'cadran.mjs'))};
const D = {emit.as_json()};
const cases = {json.dumps(cases, ensure_ascii=False)};
console.log(JSON.stringify(cases.map((c) => {{
  const t = route(D, c.utterance, c.armed, null, {{}});
  return {{ t, seq: frames(t) }};
}})));
"""
    out = subprocess.run([NODE, "--input-type=module", "-e", script],
                         capture_output=True, text=True, cwd=TUI)
    if out.returncode:
        raise AssertionError(out.stderr[:2000])
    return json.loads(out.stdout)


def seats(t) -> set:
    return {(p["position"], p["state"]) for p in t["positions"]}


@unittest.skipUnless(NODE and INSTALLED, "node or rouage/tui not installed")
class TheDialMovesOnlyThroughTheTrace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.runs = js_frames([dict(utterance=u, armed=a)
                              for u in UTTERANCES for a in ARMED])

    def test_the_dial_comes_to_rest_on_the_trace(self):
        for r in self.runs:
            self.assertTrue(r["seq"], r["t"]["utterance"])
            self.assertEqual(r["seq"][-1], r["t"], r["t"]["utterance"])

    def test_no_frame_shows_what_the_train_did_not_produce(self):
        for r in self.runs:
            t = r["t"]
            for f in r["seq"]:
                u = t["utterance"]
                self.assertLessEqual(seats(f), seats(t), u)
                self.assertLessEqual(set(f["admitted"]), set(t["admitted"]), u)
                self.assertLessEqual(set(f["failures"]), set(t["failures"]), u)
                self.assertEqual(f["stages"], t["stages"][:len(f["stages"])], u)
                self.assertIn(f["routeEnd"], (None, t["routeEnd"]), u)
                self.assertIn(f["routeAimed"], (None, t["routeAimed"]), u)
                # The hour hand is admitted[0]; a frame may withhold it, never
                # point it at someone else.
                if f["admitted"]:
                    self.assertEqual(f["admitted"][0], t["admitted"][0], u)


if __name__ == "__main__":
    unittest.main()
