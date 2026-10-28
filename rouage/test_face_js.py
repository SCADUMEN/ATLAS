"""The browser face must be the terminal face, byte for byte.

face.js assembles Le Cadran's face in the live page from face_kit(), so the
geometry is never written twice. The assembly is - markers, bands, hand order,
footer wrapping - and a second assembler that drifted would put a hand or a
glyph on the page that the terminal never drew. So both are run on the same
turns, each through its own train, and the plain text compared whole.

Each engine routes for itself: the trains are already held equal by
test_conformance.py, so a difference here is the face, not the routing.
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest

import emit
from cadran_face import face, face_kit
from rouage import load_ring, route
from test_conformance import ARMED, HERE, NODE, UTTERANCES, proposal_cases

TAG = re.compile(r"<[^>]+>")


def js_faces(cases) -> list[dict]:
    script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
import {{ face }} from {json.dumps(str(HERE / 'face.js'))};
const D = {emit.as_json()};
const K = {json.dumps(face_kit(), ensure_ascii=False)};
const cases = {json.dumps(cases, ensure_ascii=False)};
console.log(JSON.stringify(cases.map((c) => face(K, route(D, c.utterance, c.armed,
  null, {{ proposals: c.proposals, tiered: c.tiered }})))));
"""
    out = subprocess.run([NODE, "--input-type=module", "-e", script],
                         capture_output=True, text=True, cwd=HERE)
    if out.returncode:
        raise AssertionError(out.stderr[:2000])
    return json.loads(out.stdout)


def unescape(html: str) -> str:
    return (TAG.sub("", html).replace("&lt;", "<").replace("&gt;", ">")
            .replace("&amp;", "&"))


@unittest.skipUnless(NODE, "node not available")
class TheBrowserFaceIsTheTerminalFace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cases = [dict(utterance=u, armed=a, proposals=None, tiered=None)
                 for u in UTTERANCES for a in ARMED]
        cases += [dict(utterance=c["utterance"], armed=c["armed"],
                       proposals=c["proposals"], tiered=None)
                  for c in proposal_cases(cls.ring)
                  if c["resolvable"] is None and not c["requireEvidence"]]
        cases += [dict(utterance="run Publish", armed=None, proposals=None,
                       tiered=["Le Curateur"]),
                  dict(utterance="run Publish, security check", armed=None,
                       proposals=None, tiered=[]),
                  dict(utterance="", armed=None, proposals=None, tiered=None)]
        cls.cases = cases
        cls.js = js_faces(cases)

    def _py(self, c) -> str:
        return face(route(self.ring, c["utterance"], c["armed"],
                          proposals=c["proposals"], tiered=c["tiered"]),
                    ring=self.ring)

    def test_every_turn_draws_the_same_face(self):
        for c, j in zip(self.cases, self.js):
            self.assertEqual(j["text"], self._py(c), c)

    def test_the_painted_face_is_the_plain_face(self):
        # Colour rides beside the glyphs. Strip it and nothing may move.
        for c, j in zip(self.cases, self.js):
            self.assertEqual(unescape(j["html"]), j["text"], c)

    def test_the_browser_paints_what_the_terminal_paints(self):
        # Glyph parity alone let the two faces differ in colour. A seat's plate
        # is carried by colour, so the markup is held whole: the sheet's
        # translation of the terminal's escapes against face.js's spans.
        from dial import ansi_html
        for c, j in zip(self.cases, self.js):
            painted = face(route(self.ring, c["utterance"], c["armed"],
                                 proposals=c["proposals"], tiered=c["tiered"]),
                           ring=self.ring, color=True)
            self.assertEqual(j["html"], ansi_html(painted), c)

    def test_the_matrix_lights_more_than_the_standing_watch(self):
        # A matrix of quiet turns would pass while never drawing a hand.
        self.assertTrue(any("split →" in j["text"] for j in self.js))
        self.assertTrue(any("FAULT" in j["text"] for j in self.js))
        self.assertTrue(any("08●" in j["text"] or "08◆" in j["text"]
                            for j in self.js))


if __name__ == "__main__":
    unittest.main()
