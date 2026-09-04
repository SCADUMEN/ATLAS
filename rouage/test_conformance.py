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
from rouage import load_ring, load_routes, resolve_step, route

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

    def test_both_readouts_surface_every_trace_field(self):
        """The fifth seam. Two readouts, and nothing was comparing them.

        dial.py has one and paint.js has another. They had already diverged -
        the live page was missing Input, Mechanisms and Cycle, so `utterance`
        and `stages` reached the static sheet and nothing on the live one. The
        train -> readout guard only ever looked at Python.

        Presentation may differ; a document and a tool have different jobs.
        What may not differ is which facts reach the reader at all.
        """
        js = (HERE / "paint.js").read_text(encoding="utf-8")
        t = route(self.ring, "run Publish", tiered=["Le Curateur"]).to_dict()
        # camelCase in JS, snake_case in the Python trace.
        alias = {"route_end": "routeEnd", "route_aimed": "routeAimed"}
        for key in t:
            probe = alias.get(key, key)
            self.assertIn(f"t.{probe}", js,
                          f"trace emits {key!r} and the live readout omits it")

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
        # One further documented exception: le_sas()'s held-note is compared
        # verbatim against rouage.py's, which happens to write an activation
        # phrase as doctrine prose ("...did not pass Le Sas") rather than as
        # gate vocabulary the engine reads to route on. Stripped before the
        # scan, so it cannot mask an actual stale copy appearing anywhere else.
        scan_src = src.replace("untiered - did not pass Le Sas", "")
        d = emit.doctrine(self.ring)
        vocabulary = (
            [m["name"] for m in d["members"]]
            + [p for m in d["members"] for p in m["phrases"]]
            + list(d["routes"]) + list(d["precedence"])
        )
        leaked = sorted({v for v in vocabulary if v.lower() in scan_src.lower()})
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


# --------------------------------------------------------------------------
# Stage 6 - COLLECT. The barrel's half, and the second place the trains can
# disagree. Until this matrix existed, train.js implemented the literal half
# only: emit.py shipped `bullets` and `prohibitions` to the browser and the
# browser read neither. A proposal admitted in Python was a council state the
# dial could not reproduce, which is the one thing the instrument exists not
# to do.
# --------------------------------------------------------------------------

def roles(ring):
    """Pick the members the matrix needs, by property rather than by name.

    Derived, not written down: a doctrine rename must not be able to leave a
    stale member name in this file, which is the same rule train.js lives by.
    """
    sealed = next(m for m in ring.members if m.sealed and m.bullets)
    prohibited = next(m for m in ring.members if m.prohibitions)
    plain = next(m for m in ring.members
                 if m.bullets and not m.sealed and not m.standing
                 and m.name not in (sealed.name, prohibited.name))
    return sealed, prohibited, plain


def proposal_cases(ring):
    """Every branch of admit_proposals(), as data both engines can be handed."""
    sealed, prohibited, plain = roles(ring)
    # The utterance that convenes `plain` literally, for the duplicate case.
    convening = plain.phrases[0] if plain.phrases else ""

    def case(name, proposals, utterance="a quiet turn with nothing in it",
             armed=None, resolvable=None, require_evidence=False):
        return dict(name=name, utterance=utterance, armed=armed,
                    proposals=proposals, resolvable=resolvable,
                    requireEvidence=require_evidence)

    return [
        case("admitted on a verbatim citation",
             [[plain.name, plain.bullets[0]]]),
        case("citation with surrounding whitespace is still verbatim",
             [[plain.name, "  " + plain.bullets[0] + "  "]]),
        case("unknown member",
             [["Le Fantome", plain.bullets[0]]]),
        case("citation not found in the activation section",
             [[plain.name, "because it felt right"]]),
        case("a prohibition offered as grounds - the inverted gate",
             [[prohibited.name, prohibited.prohibitions[0]]]),
        case("already convened literally, so not duplicated",
             [[plain.name, plain.bullets[0]]], utterance=convening),
        case("sealed member proposed without authorization",
             [[sealed.name, sealed.bullets[0]]]),
        case("sealed member proposed with the crown armed",
             [[sealed.name, sealed.bullets[0]]], armed=sealed.name),
        case("evidence recorded but explicitly unverified",
             [[plain.name, plain.bullets[0], "deadbeef"]]),
        case("evidence that resolves",
             [[plain.name, plain.bullets[0], "deadbeef"]],
             resolvable=["deadbeef"]),
        case("evidence that does not resolve",
             [[plain.name, plain.bullets[0], "notanobject"]],
             resolvable=["deadbeef"]),
        case("evidence required and none supplied",
             [[plain.name, plain.bullets[0]]], require_evidence=True),
        case("several proposals, mixed outcomes",
             [[plain.name, plain.bullets[0]],
              ["Le Fantome", "nothing"],
              [prohibited.name, prohibited.prohibitions[0]],
              [sealed.name, sealed.bullets[0]]]),
        case("proposals alongside a named route",
             [[plain.name, plain.bullets[0]]], utterance="run Publish"),
        case("no proposals at all routes exactly as an unwired train",
             []),
    ]


def js_proposal_traces(cases) -> list[dict]:
    script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
const D = {emit.as_json()};
const cases = {json.dumps(cases, ensure_ascii=False)};
console.log(JSON.stringify(cases.map((c) => route(D, c.utterance, c.armed, null, {{
  proposals: c.proposals,
  resolvable: c.resolvable,
  requireEvidence: c.requireEvidence,
}}))));
"""
    out = subprocess.run([NODE, "--input-type=module", "-e", script],
                         capture_output=True, text=True, cwd=HERE)
    if out.returncode:
        raise AssertionError(out.stderr[:2000])
    return json.loads(out.stdout)


def verifier_for(resolvable):
    """`None` is no verifier at all; a list is a verifier that resolves it."""
    if resolvable is None:
        return None
    allowed = set(resolvable)
    return lambda ref: ref in allowed


@unittest.skipUnless(NODE, "node not available")
class TheTwoTrainsAgreeOnTheBarrelsHalf(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.cases = proposal_cases(cls.ring)
        cls.js = js_proposal_traces(cls.cases)

    def _py(self, c):
        return route(self.ring, c["utterance"], c["armed"],
                     proposals=[tuple(p) for p in c["proposals"]],
                     verify=verifier_for(c["resolvable"]),
                     require_evidence=c["requireEvidence"]).to_dict()

    def test_positions_and_states_match(self):
        for c, j in zip(self.cases, self.js):
            p = self._py(c)
            self.assertEqual(
                [(x["position"], x["state"]) for x in p["positions"]],
                [(x["position"], x["state"]) for x in j["positions"]],
                c["name"])

    def test_the_reason_and_note_each_member_carries_match(self):
        # `reason` is "proposed:<citation>" and `note` carries the evidence
        # string. Both are rendered on the dial, so a divergence here is the
        # browser attributing a member's presence to something else.
        for c, j in zip(self.cases, self.js):
            p = self._py(c)
            self.assertEqual([(x["reason"], x["note"]) for x in p["positions"]],
                             [(x["reason"], x["note"]) for x in j["positions"]],
                             c["name"])

    def test_every_rejection_reads_identically(self):
        # The rejection strings are duplicated in train.js by hand. This is
        # what makes that duplication survivable.
        for c, j in zip(self.cases, self.js):
            self.assertEqual(self._py(c)["failures"], j["failures"], c["name"])

    def test_notices_and_stages_match(self):
        for c, j in zip(self.cases, self.js):
            p = self._py(c)
            self.assertEqual(p["notices"], j["notices"], c["name"])
            self.assertEqual(p["stages"], j["stages"], c["name"])

    def test_the_precedence_ordering_matches(self):
        for c, j in zip(self.cases, self.js):
            self.assertEqual(self._py(c)["admitted"], j["admitted"], c["name"])

    def test_the_matrix_actually_exercises_every_branch(self):
        # A matrix that silently stopped covering a branch would keep passing.
        seen = set()
        for c in self.cases:
            for f in self._py(c)["failures"]:
                if "unknown member" in f: seen.add("unknown")
                elif "cited a prohibition" in f: seen.add("prohibition")
                elif "cited text not found" in f: seen.add("not-found")
                elif "does not resolve" in f: seen.add("bad-evidence")
                elif "supplied no evidence" in f: seen.add("no-evidence")
        self.assertEqual(
            seen, {"unknown", "prohibition", "not-found", "bad-evidence",
                   "no-evidence"},
            "the admission matrix stopped covering a rejection branch")

    def test_a_proposal_can_actually_convene_someone(self):
        # The positive case, stated separately: if this ever silently stopped
        # admitting, every "they agree" test above would still pass on two
        # engines agreeing to do nothing.
        c = self.cases[0]
        p = self._py(c)
        self.assertTrue(
            any(x["reason"].startswith("proposed:") and x["state"] == "active"
                for x in p["positions"]),
            "no proposal was admitted in the admission case")


# --------------------------------------------------------------------------
# Stage 8 - RELEASE. Le Sas's Tiered condition, the third place the trains
# can disagree. Until this matrix existed, train.js had no tiering mechanic
# at all - a browser visitor could never see the escapement hold anyone,
# unlike the CLI's --tier and the committed sheet's specimen 8.
# --------------------------------------------------------------------------

def tier_cases(ring):
    """Every branch of le_sas()/leSas(), as data both engines can be handed.

    The standing witness and the crown are picked by property, matching
    roles(). The tiered member is read off the Publish route's own sequence
    rather than written down, so a doctrine rename cannot leave a stale name
    here either - the same discipline roles() keeps for the barrel matrix.
    """
    standing = next(m for m in ring.members if m.standing)
    crown = next(m for m in ring.members if m.position == "crown")
    first = resolve_step(ring, load_routes()["Publish"][0])

    def case(name, tiered, utterance="run Publish", armed=None):
        return dict(name=name, utterance=utterance, armed=armed, tiered=tiered)

    return [
        case("no tiering supplied - transparent, holds no one", None),
        case("tiering supplied empty - holds every admitted field operator", []),
        case(f"only {first.name} tiered - route cut short, others held",
             [first.name]),
        case("standing witness is exempt from tiering", [],
             utterance="a quiet turn with nothing in it"),
        case("the crown is exempt from tiering", [], utterance="archive first"),
    ]


def js_tier_traces(cases) -> list[dict]:
    script = f"""
import {{ route }} from {json.dumps(str(HERE / 'train.js'))};
const D = {emit.as_json()};
const cases = {json.dumps(cases, ensure_ascii=False)};
console.log(JSON.stringify(cases.map((c) => route(D, c.utterance, c.armed, null, {{
  tiered: c.tiered,
}}))));
"""
    out = subprocess.run([NODE, "--input-type=module", "-e", script],
                         capture_output=True, text=True, cwd=HERE)
    if out.returncode:
        raise AssertionError(out.stderr[:2000])
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "node not available")
class TheTwoTrainsAgreeOnLeSas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()
        cls.cases = tier_cases(cls.ring)
        cls.js = js_tier_traces(cls.cases)

    def _py(self, c):
        return route(self.ring, c["utterance"], c["armed"],
                     tiered=c["tiered"]).to_dict()

    def test_positions_states_and_notes_match(self):
        for c, j in zip(self.cases, self.js):
            p = self._py(c)
            self.assertEqual(
                [(x["position"], x["state"], x["note"]) for x in p["positions"]],
                [(x["position"], x["state"], x["note"]) for x in j["positions"]],
                c["name"])

    def test_the_untiered_fault_reads_identically(self):
        for c, j in zip(self.cases, self.js):
            self.assertEqual(self._py(c)["failures"], j["failures"], c["name"])

    def test_route_readings_match(self):
        # settle_route_end() re-resolves after le_sas() holds someone, so a
        # divergence here is the split hand landing somewhere the council
        # never actually stopped.
        for c, j in zip(self.cases, self.js):
            p = self._py(c)
            self.assertEqual(p["route_end"], j["routeEnd"], c["name"])
            self.assertEqual(p["route_aimed"], j["routeAimed"], c["name"])

    def test_a_tiering_supplied_empty_can_actually_hold_someone(self):
        # Stated separately, same reason as the barrel matrix's positive
        # case: two engines can agree perfectly by both holding no one.
        c = next(c for c in self.cases if "route cut short" in c["name"])
        p = self._py(c)
        self.assertTrue(
            any(x["note"] == "untiered - did not pass Le Sas"
                for x in p["positions"]),
            "no one was held as untiered in the positive case")

    def test_the_standing_witness_and_the_crown_are_never_held(self):
        # The two exemptions le_sas() carries, checked positively - an
        # "agree" test could pass on both engines wrongly holding the same
        # exempt member.
        for label in ("standing witness", "crown"):
            c = next(c for c in self.cases if label in c["name"])
            p = self._py(c)
            self.assertTrue(
                any(x["state"] == "active" for x in p["positions"]),
                f"{c['name']}: exemption did not hold in Python")
            j = self.js[self.cases.index(c)]
            self.assertTrue(
                any(x["state"] == "active" for x in j["positions"]),
                f"{c['name']}: exemption did not hold in JS")


if __name__ == "__main__":
    unittest.main()
