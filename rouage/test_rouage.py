"""Tests for Le Rouage.

le-rouage.md: 'Determinism is testable. The same input and the same archive
state must select the same modes. If it does not, the train is reasoning,
and it should not be.'

These are that test, plus one per prohibition. Stdlib unittest - no test
dependency to install on the board in the case.

    python3 -m unittest discover rouage -v
"""

import itertools
import json
import pathlib
import tempfile
import unittest
from pathlib import Path

from rouage import (
    CORE_HEADING,
    PLACEHOLDER,
    phrase_pattern,
    DOCTRINE_HEADING,
    NEGATIVE_SECTION,
    Ring,
    Trace,
    admit_proposals,
    evaluate,
    git_evidence,
    load_routes,
    load_invocations,
    STATES,
    citations,
    record_winding,
    resolve_step,
    roue_a_colonnes,
    fold,
    load_core,
    load_ring,
    order,
    route,
)


class RingParses(unittest.TestCase):
    """The manifest is the single source of truth and must survive parsing."""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_twelve_hours_and_the_crown(self):
        self.assertEqual(len(self.ring.hours), 12)
        self.assertEqual(len(self.ring.members), 13)

    def test_every_hour_position_is_occupied(self):
        positions = {m.position for m in self.ring.hours}
        expected = {f"{i:02d}" for i in range(1, 13)}
        self.assertEqual(positions, expected)

    def test_every_member_has_at_least_one_phrase(self):
        for m in self.ring.members:
            self.assertTrue(m.phrases, f"{m.name} has no invocation phrase")

    def test_precedence_is_the_ladder_not_the_membership_criteria(self):
        # '## Adding Or Removing A Member' also holds a numbered bold list.
        # An unscoped parse ranks the ring behind 'Distinct output'.
        self.assertEqual(self.ring.precedence[0], "Le Sauvegarder")
        self.assertIn("Le Vigile", self.ring.precedence)
        self.assertNotIn("Distinct output", self.ring.precedence)

    def test_cap_comes_from_the_manifest(self):
        self.assertEqual(self.ring.cap, 4)

    def test_sceptique_is_the_only_standing_member(self):
        standing = [m.name for m in self.ring.members if m.standing]
        self.assertEqual(standing, ["Le Sceptique"])

    def test_fripon_is_the_only_sealed_member(self):
        sealed = [m.name for m in self.ring.members if m.sealed]
        self.assertEqual(sealed, ["Le Fripon"])


class Determinism(unittest.TestCase):
    """The train reasons about nothing, so it cannot drift."""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_same_input_same_trace(self):
        utterance = "reconstruct this, and check what's exposed"
        first = route(self.ring, utterance).to_json()
        for _ in range(20):
            self.assertEqual(route(self.ring, utterance).to_json(), first)

    def test_no_memory_between_turns(self):
        # Arming Le Fripon must not survive into the next turn.
        # le-boitier.md: 'Arming must expire.'
        armed = route(self.ring, "red team this", armed="Le Fripon")
        self.assertEqual(self._state(armed, "Le Fripon"), "active")

        after = route(self.ring, "red team this")
        self.assertEqual(self._state(after, "Le Fripon"), "sealed")

    def test_accents_fold(self):
        # le-renegat.md lists both spellings; folding means it need not.
        with_accent = route(self.ring, "argue against this").to_json()
        self.assertIn("Le Renégat", with_accent)
        self.assertEqual(fold("Le Renégat"), fold("Le Renegat"))

    @staticmethod
    def _state(trace, name):
        for c in trace.candidates:
            if c.member.name == name:
                return c.state
        return "dark"


class TheSeal(unittest.TestCase):
    """le-conseil.md: 'Le Fripon never self-activates.'"""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_named_but_unarmed_is_sealed_not_active(self):
        trace = route(self.ring, "red team my backup procedure")
        fripon = [c for c in trace.candidates if c.member.name == "Le Fripon"]
        self.assertEqual(len(fripon), 1)
        self.assertEqual(fripon[0].state, "sealed")

    def test_sealed_is_distinct_from_dark(self):
        # A sealed member was named and refused. A dark one never fired.
        # Collapsing them would lose exactly the information the dial shows.
        named = route(self.ring, "red team this")
        unnamed = route(self.ring, "rename this file")
        self.assertIn("Le Fripon", named.to_json())
        self.assertNotIn("Le Fripon", unnamed.to_json())

    def test_arming_another_mode_does_not_unseal_fripon(self):
        trace = route(self.ring, "red team this", armed="Le Vigile")
        self.assertEqual(
            [c.state for c in trace.candidates if c.member.name == "Le Fripon"],
            ["sealed"],
        )


class TheCap(unittest.TestCase):
    """Le Sas enforces the cap and reports. It does not trim quietly."""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_sceptique_is_not_counted_against_the_cap(self):
        trace = route(
            self.ring,
            "preserve this, security check, argue against this, classify this",
        )
        admitted = [c.member.name for c in trace.admitted()]
        self.assertIn("Le Sceptique", admitted)
        self.assertEqual(len(admitted), self.ring.cap + 1)
        self.assertEqual(trace.failures, [])

    def test_over_cap_is_reported_not_silently_truncated(self):
        # le-rouage.md: 'No silent truncation.'
        trace = route(
            self.ring,
            "preserve this, map this, security check, argue against this, "
            "classify this",
        )
        held = [c for c in trace.candidates if c.state == "held"]
        self.assertTrue(held)
        self.assertTrue(any("over-cap" in f for f in trace.failures))

    def test_held_members_survive_in_the_trace(self):
        # The trace records them for inspection; the prose must not name them.
        # Two surfaces. This asserts the first one.
        trace = route(
            self.ring,
            "preserve this, map this, security check, argue against this, "
            "classify this",
        )
        held = [c.member.name for c in trace.candidates if c.state == "held"]
        self.assertTrue(held)
        for name in held:
            self.assertIn(name, trace.to_json())

    def test_full_ring_is_a_reported_defect(self):
        # le-conseil.md: 'Every register lit at once is an error state,
        # not a climax.'
        every_phrase = " ".join(m.phrases[0] for m in self.ring.hours)
        trace = route(self.ring, every_phrase)
        self.assertTrue(any("full ring" in f for f in trace.failures))


class ProposalAdmission(unittest.TestCase):
    """admit_proposals(): the barrel proposes, the train disposes.

    Policy is Cited - le-rouage.md: a proposal is admitted only if its
    citation is a verbatim line among the bullets in that member's own
    Activation section.
    """

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_verbatim_citation_is_admitted(self):
        trace = route(
            self.ring, "no phrase here",
            proposals=[("Le Limier", "provenance is broken and must be "
                                      "reasoned across a gap")],
        )
        limier = [c for c in trace.candidates if c.member.name == "Le Limier"]
        self.assertEqual(len(limier), 1)
        self.assertEqual(limier[0].state, "active")
        self.assertTrue(limier[0].reason.startswith("proposed:"))

    def test_non_verbatim_citation_is_rejected_and_reported(self):
        trace = route(
            self.ring, "no phrase here",
            proposals=[("Le Limier", "something that sounds close but isn't "
                                      "the actual bullet text")],
        )
        self.assertFalse(
            [c for c in trace.candidates if c.member.name == "Le Limier"]
        )
        self.assertTrue(any("Le Limier" in f and "not found verbatim" in f
                             for f in trace.failures))

    def test_unknown_member_is_rejected_and_reported(self):
        trace = route(
            self.ring, "no phrase here",
            proposals=[("Le Fantome", "anything at all")],
        )
        self.assertTrue(any("unknown member" in f for f in trace.failures))

    def test_cited_but_unarmed_seal_stays_sealed(self):
        trace = route(
            self.ring, "no phrase here",
            proposals=[("Le Fripon",
                        "a recovery plan has never been run end to end")],
        )
        fripon = [c for c in trace.candidates if c.member.name == "Le Fripon"]
        self.assertEqual(len(fripon), 1)
        self.assertEqual(fripon[0].state, "sealed")

    def test_cited_and_armed_seal_admits(self):
        trace = route(
            self.ring, "no phrase here", armed="Le Fripon",
            proposals=[("Le Fripon",
                        "a recovery plan has never been run end to end")],
        )
        fripon = [c for c in trace.candidates if c.member.name == "Le Fripon"]
        self.assertEqual(len(fripon), 1)
        self.assertEqual(fripon[0].state, "active")

    def test_proposal_does_not_duplicate_a_named_match(self):
        # 'reconstruct this' already names Le Limier; a proposal for the
        # same member must not put him on the ring twice.
        trace = route(
            self.ring, "reconstruct this",
            proposals=[("Le Limier", "provenance is broken and must be "
                                      "reasoned across a gap")],
        )
        limier = [c for c in trace.candidates if c.member.name == "Le Limier"]
        self.assertEqual(len(limier), 1)
        self.assertTrue(limier[0].reason.startswith("named:"))

    def test_called_directly_returns_only_admitted_candidates(self):
        # admit_proposals() in isolation, without route()'s pipeline - the
        # rejected proposal never becomes a Candidate at all.
        trace = Trace(utterance="")
        result = admit_proposals(self.ring, trace, [
            ("Le Limier", "provenance is broken and must be "
                          "reasoned across a gap"),
            ("Le Limier", "not real bullet text"),
        ])
        self.assertEqual([c.member.name for c in result], ["Le Limier"])

    def test_admitted_proposal_still_passes_through_the_cap(self):
        # Cited candidates are not exempt from meter() - order() and the
        # cap still apply, which is the whole point of 'the barrel proposes
        # and the train disposes.'
        trace = route(
            self.ring,
            "preserve this, map this, security check, argue against this, "
            "classify this",
            proposals=[("Le Limier", "provenance is broken and must be "
                                      "reasoned across a gap")],
        )
        self.assertTrue(any("over-cap" in f for f in trace.failures))


class EvidenceNarrowsTheGap(unittest.TestCase):
    """A citation proves the gate is real; evidence is about the premise.

    Cited catches a barrel that invents an activation condition. It cannot
    catch one that quotes a real condition about a thing that never happened.
    These cover the second field and, as much as the tests can, its limits.
    """

    def setUp(self):
        self.ring = load_ring()
        self.member = next(m for m in self.ring.members if m.bullets)
        self.cite = self.member.bullets[0]

    def _trace(self):
        return Trace(utterance="")

    def test_evidence_is_recorded_as_unverified_when_no_verifier(self):
        # The trace must not imply a check that never ran.
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(self.member.name, self.cite, "deadbeef")])
        self.assertEqual(len(got), 1)
        self.assertIn("unverified", got[0].note)
        self.assertIn("deadbeef", got[0].note)
        self.assertEqual(t.failures, [])

    def test_resolving_evidence_is_admitted_and_not_marked_unverified(self):
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(self.member.name, self.cite, "abc123")],
            verify=lambda ref: ref == "abc123")
        self.assertEqual(len(got), 1)
        self.assertIn("abc123", got[0].note)
        self.assertNotIn("unverified", got[0].note)

    def test_unresolvable_evidence_is_rejected_and_reported(self):
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(self.member.name, self.cite, "nope")],
            verify=lambda ref: False)
        self.assertEqual(got, [])
        self.assertTrue(any("does not resolve" in f for f in t.failures))

    def test_two_tuple_still_works_and_stays_unannotated(self):
        # Most gates have no artifact. Evidence must stay optional or the
        # ring goes dark for every member whose condition is not a change.
        t = self._trace()
        got = admit_proposals(self.ring, t, [(self.member.name, self.cite)])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].note, "")
        self.assertEqual(t.failures, [])

    def test_require_evidence_rejects_a_bare_proposal(self):
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(self.member.name, self.cite)],
            require_evidence=True)
        self.assertEqual(got, [])
        self.assertTrue(any("no evidence" in f for f in t.failures))

    def test_evidence_does_not_rescue_a_bad_citation(self):
        # Order matters: the gate is checked before the premise. Good evidence
        # must never buy admission for a condition that is not in doctrine.
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(self.member.name, "invented condition", "abc123")],
            verify=lambda ref: True)
        self.assertEqual(got, [])
        self.assertTrue(any("verbatim" in f for f in t.failures))

    def test_evidence_does_not_unseal_le_fripon(self):
        fripon = next(m for m in self.ring.members if m.sealed and m.bullets)
        t = self._trace()
        got = admit_proposals(
            self.ring, t, [(fripon.name, fripon.bullets[0], "abc123")],
            verify=lambda ref: True)
        self.assertEqual(got[0].state, "sealed")
        self.assertIn("without authorization", got[0].note)

    def test_route_threads_evidence_through(self):
        t = route(self.ring, "", proposals=[
            (self.member.name, self.cite, "abc123")],
            verify=lambda ref: True)
        admitted = [c for c in t.candidates if c.reason.startswith("proposed:")]
        self.assertIn("abc123", admitted[0].note)

    def test_git_verifier_resolves_head_and_rejects_nonsense(self):
        verify = git_evidence()
        self.assertTrue(verify("HEAD"))
        self.assertFalse(verify("0000000000000000000000000000000000000000"))


class TheColumnWheel(unittest.TestCase):
    """La roue a colonnes: verdicts, dissent, and le frein.

    The train could represent whether a member convened but never what it
    concluded. le-conseil.md names two standing rules that override ordering
    and only one - the Fripon seal - was enforced anywhere.
    """

    UTT = "preserve this, map this, security check, argue against this"

    def setUp(self):
        self.ring = load_ring()

    def test_halting_verdict_marks_dissent(self):
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Archive")])
        seat = next(c for c in t.candidates if c.member.position == "06")
        self.assertEqual(seat.state, "dissent")

    def test_halting_verdict_engages_the_brake(self):
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Release")])
        self.assertTrue(t.halted)
        self.assertTrue(any("brake engaged" in n for n in t.notices))

    def test_reduce_is_a_verdict_but_does_not_halt(self):
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Reduce")])
        self.assertEqual(t.verdicts, [("Le Renégat", "Reduce")])
        self.assertEqual(t.halted, [])

    def test_the_brake_never_stops_the_crown(self):
        # Precedence #1: evidence loss cannot be undone. A brake that can stop
        # preservation is a brake that can lose the archive.
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Archive")])
        crown = next(c for c in t.candidates if c.member.position == "crown")
        self.assertEqual(crown.state, "active")
        self.assertNotIn("Le Sauvegarder", t.halted)

    def test_the_dissenter_stays_lit(self):
        # Otherwise the halt erases its own cause from the dial.
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Archive")])
        self.assertNotIn("Le Renégat", t.halted)

    def test_standing_witness_is_not_a_field_operator(self):
        t = route(self.ring, self.UTT, verdicts=[("Le Renégat", "Archive")])
        sceptique = next(c for c in t.candidates if c.member.position == "01")
        self.assertEqual(sceptique.state, "active")

    def test_verdict_from_a_member_that_did_not_convene_is_rejected(self):
        t = route(self.ring, "rename this file", verdicts=[("Le Renégat", "Archive")])
        self.assertEqual(t.verdicts, [])
        self.assertTrue(any("did not convene" in f for f in t.failures))

    def test_unknown_member_verdict_is_rejected(self):
        t = route(self.ring, self.UTT, verdicts=[("Le Fantome", "Archive")])
        self.assertTrue(any("unknown member" in f for f in t.failures))

    def test_no_verdicts_leaves_the_stage_out_entirely(self):
        t = route(self.ring, self.UTT)
        self.assertNotIn("VERDICT->colonnes", t.stages)
        self.assertEqual(t.verdicts, [])


class TheCapIsADefaultNotAnAbsolute(unittest.TestCase):
    """Complex turns may need more than four. Theatre may not widen itself."""

    UTT = "preserve this, map this, security check, argue against this, red team this"

    def setUp(self):
        self.ring = load_ring()

    def test_unauthorized_fifth_member_is_still_held(self):
        t = route(self.ring, self.UTT, armed="Le Fripon")
        counted = [c for c in t.candidates
                   if not c.member.standing and c.member.position != "crown"]
        self.assertTrue(any(c.state == "held" for c in counted))

    def test_authorization_widens_the_cap_and_is_recorded(self):
        t = route(self.ring, self.UTT, armed="Le Fripon", authorize_cap=6)
        self.assertTrue(any("cap widened by authorization" in n
                            for n in t.notices))
        over = [c for c in t.candidates if "over cap" in c.note]
        self.assertEqual(over, [])

    def test_authorization_below_the_default_does_not_narrow_it(self):
        # Widening is the only direction. A caller cannot quietly shrink the
        # ring to suppress a member the gates admitted.
        wide = route(self.ring, self.UTT, armed="Le Fripon")
        narrow = route(self.ring, self.UTT, armed="Le Fripon", authorize_cap=1)
        self.assertEqual([c.state for c in wide.candidates],
                         [c.state for c in narrow.candidates])


class NamedRoutes(unittest.TestCase):
    """Nine routes in doctrine. The named half is matchable, like a gate."""

    def setUp(self):
        self.ring = load_ring()
        self.routes = load_routes()

    def test_every_route_in_doctrine_parses(self):
        self.assertEqual(len(self.routes), 9)

    def test_every_step_resolves_to_a_member(self):
        for name, steps in self.routes.items():
            for step in steps:
                self.assertIsNotNone(resolve_step(self.ring, step),
                                     f"{name}: {step!r} matches no member")

    def test_a_named_route_admits_its_sequence(self):
        t = route(self.ring, "run Publish")
        names = {c.member.name for c in t.candidates}
        self.assertLessEqual({"Le Curateur", "Le Vigile", "Le Messager"}, names)
        self.assertEqual(t.route, "Publish")

    def test_the_hand_ends_where_the_route_ends(self):
        self.assertEqual(route(self.ring, "run Publish").route_end, "10")

    def test_a_repeated_step_lights_one_seat_but_still_ends_there(self):
        # Harden is Vigile -> Fripon -> Vigile. A seat cannot be occupied
        # twice, but the route still ends at Vigile.
        t = route(self.ring, "run Harden")
        vigiles = [c for c in t.candidates if c.member.name == "Le Vigile"]
        self.assertEqual(len(vigiles), 1)
        self.assertEqual(t.route_end, "04")

    def test_a_route_does_not_unseal_le_fripon(self):
        t = route(self.ring, "run Harden")
        fripon = next(c for c in t.candidates if c.member.name == "Le Fripon")
        self.assertEqual(fripon.state, "sealed")

    def test_an_armed_route_step_is_admitted(self):
        t = route(self.ring, "run Harden", armed="Le Fripon")
        fripon = next(c for c in t.candidates if c.member.name == "Le Fripon")
        self.assertEqual(fripon.state, "active")

    def test_judgement_delegates_and_admits_no_one(self):
        # Its sequence cell is a protocol file, not members. Inventing a
        # sequence it does not have would be the train deciding something.
        t = route(self.ring, "run Judgement")
        self.assertEqual(self.routes["Judgement"], ())
        self.assertEqual(t.route, "Judgement")
        self.assertIsNone(t.route_end)
        self.assertTrue(any("delegated to protocol" in n for n in t.notices))

    def test_no_route_named_leaves_the_trace_unrouted(self):
        t = route(self.ring, "what happened here")
        self.assertIsNone(t.route)
        self.assertNotIn("ROUTE->named", t.stages)


class TheBarrelContract(unittest.TestCase):
    """citations() is what makes 'verbatim' a fair requirement."""

    def test_every_citation_offered_is_actually_admissible(self):
        # The menu must be exactly what admit_proposals accepts. If these ever
        # diverge, the barrel is being asked to quote something that will be
        # rejected, which is a trap rather than a check.
        ring = load_ring()
        for name, bullets in citations(ring).items():
            for bullet in bullets:
                t = Trace(utterance="")
                got = admit_proposals(ring, t, [(name, bullet)])
                self.assertEqual(len(got), 1, f"{name}: {bullet[:40]!r}")
                self.assertEqual(t.failures, [])

    def test_the_menu_covers_the_whole_ring(self):
        self.assertEqual(len(citations(load_ring())), 12)

    def test_the_menu_offers_no_prohibition(self):
        # The other direction, and the one that was broken: a guard must
        # never appear on the menu of things it is valid to cite. While it
        # did, a barrel quoting the menu faithfully could convene Le
        # Redempteur on the sentence written to keep him dark.
        ring = load_ring()
        offered = citations(ring)
        for m in ring.members:
            for guard in m.prohibitions:
                self.assertNotIn(guard, offered.get(m.name, ()),
                                 f"{m.name} offers a guard as quotable")


class TheNegativeGate(unittest.TestCase):
    """Gate-level prohibitions: what must not CONVENE a member.

    Distinct from the '### Prohibitions' section every member carries, which
    is behavioural - what a member must not DO once convened. The schema had
    a home for the second kind and none for the first, so the one member who
    needed one wrote it inline as bold text and parse_activation() collected
    it as activation.
    """

    def setUp(self):
        self.ring = load_ring()
        self.member = self.ring.by_name("Le Rédempteur")
        self.guard = "Matthew being tired, terse, or frustrated"

    def test_the_reference_implementation_parses(self):
        self.assertIn(self.guard, self.member.prohibitions)
        self.assertNotIn(self.guard, self.member.bullets)

    def test_a_cited_prohibition_leaves_the_position_dark(self):
        # The exploit, verbatim. Before the split this returned 12 ACTIVE
        # with failures == [] and engraved the guard on the dial as the
        # reason it convened.
        t = route(self.ring, "", proposals=[(self.member.name, self.guard)])
        lit = [p["position"] for p in t.to_dict()["positions"]
               if p["state"] != "dark"]
        self.assertEqual(lit, ["01"])       # Le Sceptique, standing. Nobody else.

    def test_the_failure_is_not_the_typo_failure(self):
        # A barrel quoting sloppily and a barrel inverting a gate are
        # different faults and the trace has to tell them apart.
        inverted = Trace(utterance="")
        admit_proposals(self.ring, inverted, [(self.member.name, self.guard)])
        typo = Trace(utterance="")
        admit_proposals(self.ring, typo, [(self.member.name, "not in any list")])

        self.assertEqual(len(inverted.failures), 1)
        self.assertEqual(len(typo.failures), 1)
        self.assertIn("cited a prohibition", inverted.failures[0])
        self.assertNotIn("cited a prohibition", typo.failures[0])

    def test_a_cited_prohibition_admits_nothing(self):
        t = Trace(utterance="")
        got = admit_proposals(self.ring, t, [(self.member.name, self.guard)])
        self.assertEqual(got, [])           # not held, not sealed - absent

    def test_every_prohibition_of_every_member_is_refused(self):
        for m in self.ring.members:
            for guard in m.prohibitions:
                t = Trace(utterance="")
                got = admit_proposals(self.ring, t, [(m.name, guard)])
                self.assertEqual(got, [], f"{m.name}: {guard[:40]!r}")
                self.assertEqual(len(t.failures), 1)

    def test_no_line_is_both_a_trigger_and_a_guard(self):
        # The seam. A line that is both would be admissible and refused by
        # the same check, and which one won would depend on statement order.
        for m in self.ring.members:
            both = set(m.bullets) & set(m.prohibitions)
            self.assertEqual(both, set(), f"{m.name}: {both}")

    def test_no_gate_still_carries_the_inline_form(self):
        # The parser keys on a heading now, so an inline '**Do not fire on:**'
        # would be silently collected as activation again - the original bug,
        # reintroduced by prose rather than by code. Nothing asserts the shape
        # of doctrine except this.
        for m in self.ring.members:
            body = m.path.read_text(encoding="utf-8")
            body = body.split(CORE_HEADING, 1)[1].split(DOCTRINE_HEADING, 1)[0]
            self.assertNotIn("**Do not fire on", body,
                             f"{m.name}: inline negative gate, needs a heading")

    def test_a_member_without_a_negative_gate_parses_empty(self):
        # Most members have none. Absent section must be empty, never an error.
        bare = [m for m in self.ring.members if not m.prohibitions]
        self.assertTrue(bare)
        for m in bare:
            self.assertEqual(m.prohibitions, ())
            self.assertIsNone(NEGATIVE_SECTION.search(
                m.path.read_text(encoding="utf-8")
                 .split(CORE_HEADING, 1)[1].split(DOCTRINE_HEADING, 1)[0]))


class TheWindingLog(unittest.TestCase):
    """Le Sauvegarder's mechanism. The caller invokes it; the train does not."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "nested" / "winding.jsonl"

    def test_a_winding_is_appended_not_rewritten(self):
        ring = load_ring()
        record_winding(route(ring, "run Publish"), self.tmp, "2026-08-16T10:00:00Z")
        record_winding(route(ring, "what happened here"), self.tmp, "2026-08-16T11:00:00Z")
        lines = self.tmp.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["route"], "Publish")

    def test_the_time_is_an_input_so_the_turn_stays_reproducible(self):
        ring = load_ring()
        record_winding(route(ring, "run Publish"), self.tmp, "FIXED")
        self.assertEqual(json.loads(self.tmp.read_text())["when"], "FIXED")

    def test_a_halt_is_recorded(self):
        ring = load_ring()
        t = route(ring, "preserve this, map this, security check, argue against this",
                  verdicts=[("Le Renégat", "Archive")])
        record_winding(t, self.tmp, "FIXED")
        entry = json.loads(self.tmp.read_text())
        self.assertTrue(entry["halted"])
        self.assertEqual(entry["verdicts"], [["Le Renégat", "Archive"]])


class LeSasChecksTiersExist(unittest.TestCase):
    """Condition 1. Le Sas checks that tiers exist, never what they say."""

    U = "preserve this, map this, security check"

    def setUp(self):
        self.ring = load_ring()

    def _untiered(self, t):
        return [c.member.name for c in t.candidates
                if c.note.startswith("untiered")]

    def test_none_is_not_the_same_as_empty(self):
        # None means no tiering was supplied and the train cannot know, so it
        # holds nothing and claims nothing. Empty means tiering was supplied
        # and nothing qualified.
        self.assertEqual(self._untiered(route(self.ring, self.U, tiered=None)), [])
        self.assertNotEqual(self._untiered(route(self.ring, self.U, tiered=[])), [])

    def test_untiered_material_does_not_pass(self):
        t = route(self.ring, self.U, tiered=["Le Vigile"])
        self.assertIn("Le Cartographe", self._untiered(t))
        self.assertTrue(any("untiered" in f for f in t.failures))

    def test_tiered_material_passes(self):
        t = route(self.ring, self.U,
                  tiered=["Le Vigile", "Le Cartographe", "Le Sauvegarder"])
        self.assertEqual(self._untiered(t), [])

    def test_the_crown_is_never_held_for_want_of_a_tier(self):
        # Untiered material must not block preservation. You preserve, then
        # you tier. A gate that can hold the crown can lose the archive.
        t = route(self.ring, self.U, tiered=[])
        crown = next(c for c in t.candidates if c.member.position == "crown")
        self.assertEqual(crown.state, "active")

    def test_the_standing_witness_is_not_held(self):
        # Le Sceptique assigns the tiers. Holding him for not having one
        # would be circular.
        t = route(self.ring, self.U, tiered=[])
        sceptique = next(c for c in t.candidates if c.member.position == "01")
        self.assertEqual(sceptique.state, "active")


class MechanismsInCombination(unittest.TestCase):
    """Every mechanism is correct alone. These test them together.

    route() takes nine parameters and each was covered in isolation, which is
    exactly how the route_end bug survived: take_route() sets the terminus
    before the cap, the brake or Le Sas have run, so a held last step still
    drew the hand.
    """

    def setUp(self):
        self.ring = load_ring()

    def test_the_hand_never_indicates_a_member_that_was_held(self):
        for kw in ({"tiered": ["Le Curateur"]},
                   {"verdicts": [("Le Renégat", "Archive")]},
                   {"authorize_cap": None}):
            t = route(self.ring, "run Publish, argue against this", **kw)
            if t.route_end is None:
                continue
            seat = next(c for c in t.candidates
                        if c.member.position == t.route_end)
            self.assertEqual(seat.state, "active",
                             f"hand points at a {seat.state} member with {kw}")

    def test_a_route_cut_short_says_so(self):
        t = route(self.ring, "run Publish", tiered=["Le Curateur"])
        self.assertNotEqual(t.route_end, "10")
        self.assertTrue(any("cut short" in n for n in t.notices))

    def test_a_fully_halted_route_indicates_nothing(self):
        # Better a hand that points nowhere than one that points at a member
        # the brake stopped.
        t = route(self.ring, "run Publish, argue against this",
                  verdicts=[("Le Renégat", "Archive")])
        self.assertIsNone(t.route_end)
        self.assertTrue(any("no step survived" in n for n in t.notices))

    def test_an_unobstructed_route_still_ends_where_it_ends(self):
        self.assertEqual(route(self.ring, "run Publish").route_end, "10")

    def test_all_nine_parameters_together_produce_a_coherent_trace(self):
        m = next(x for x in self.ring.members if x.bullets)
        t = route(self.ring, "run Harden",
                  armed="Le Fripon",
                  proposals=[(m.name, m.bullets[0], "HEAD")],
                  verify=git_evidence(),
                  require_evidence=False,
                  verdicts=[("Le Vigile", "Reduce")],
                  authorize_cap=6,
                  tiered=["Le Vigile", "Le Fripon", m.name])
        self.assertEqual(t.failures, [])
        self.assertEqual(t.route, "Harden")
        # Nothing may be in a state the dial cannot render.
        for c in t.candidates:
            self.assertIn(c.state, STATES)


class TheRattrapante(unittest.TestCase):
    """Two hands, superimposed until something splits them."""

    U = "run Publish, argue against this"

    def setUp(self):
        self.ring = load_ring()

    def test_an_unobstructed_route_does_not_split(self):
        t = route(self.ring, "run Publish")
        self.assertEqual(t.route_aimed, t.route_end)

    def test_a_cut_short_route_splits(self):
        t = route(self.ring, "run Publish", tiered=["Le Curateur"])
        self.assertEqual(t.route_aimed, "10")
        self.assertNotEqual(t.route_end, "10")

    def test_an_arrested_route_keeps_its_aim_with_nothing_to_indicate(self):
        # The main hand indicates nothing; the split hand still records where
        # the route was pointed, which is the whole reading.
        t = route(self.ring, self.U, verdicts=[("Le Renégat", "Archive")])
        self.assertIsNone(t.route_end)
        self.assertEqual(t.route_aimed, "10")

    def test_no_route_means_no_split(self):
        t = route(self.ring, "what happened here")
        self.assertIsNone(t.route_aimed)


class TheSheetDemonstratesTheInstrument(unittest.TestCase):
    """Plate 2 must keep up with what the dial can render.

    The specimen sheet is the instrument's showcase, and it silently stopped
    covering the instrument as the instrument grew - routes and the split hand
    were both renderable and absent. The old specimen form was a 3-or-4 tuple
    unpacked by length, so it could not have expressed them anyway. This is the
    guard that makes the omission fail loudly rather than go unnoticed.
    """

    def setUp(self):
        from dial import SPECIMENS, specimen_trace, STATE_INK
        self.ring = load_ring()
        self.traces = [specimen_trace(self.ring, sp) for sp in SPECIMENS]
        self.inks = STATE_INK

    def test_every_state_with_an_ink_is_demonstrated(self):
        shown = {c.state for t in self.traces for c in t.candidates}
        # `consulted` is the one exception and it is honest: nothing emits it,
        # because deciding a member was weighed-but-not-surfaced is semantic
        # and belongs to the barrel. It keeps its ink so the dial cannot
        # mistranslate it the day it arrives.
        # Two exemptions, both structural rather than convenient.
        #
        # `dark` is not a state a candidate carries - it is the ABSENCE of a
        # candidate. states.get(pos) returns None for an unlit hour and the
        # dial falls back to its ink. It needs a colour and can never appear
        # here; covered separately below.
        #
        # `consulted` nothing emits, honestly: deciding a member was weighed
        # but not surfaced is semantic and belongs to the barrel. It keeps its
        # ink so the dial cannot mistranslate it the day it arrives.
        missing = set(self.inks) - shown - {"consulted", "dark"}
        self.assertEqual(missing, set(),
                         f"dial can render {missing} but no specimen shows it")

    def test_dark_positions_are_demonstrated(self):
        # Absence is signal, so the sheet has to show absence.
        self.assertTrue(any(
            len([c for c in t.candidates if c.member.position != "crown"]) < 12
            for t in self.traces))

    def test_a_route_is_demonstrated(self):
        self.assertTrue(any(t.route for t in self.traces))

    def test_the_split_hand_is_demonstrated(self):
        self.assertTrue(any(t.route_aimed and t.route_aimed != t.route_end
                            for t in self.traces))

    def test_the_brake_is_demonstrated(self):
        self.assertTrue(any(t.halted for t in self.traces))

    def test_a_turn_that_convenes_no_one_is_demonstrated(self):
        # The most common case in practice, and the easiest to forget to show.
        self.assertTrue(any(
            not [c for c in t.candidates
                 if c.member.position not in ("crown", "01")]
            for t in self.traces))


class TheReadoutSurfacesTheTrace(unittest.TestCase):
    """Every field the trace emits has to reach the sheet.

    Third instance of one drift: the train grows a field, and the surface
    beside it does not. The dial drew three hands from route, route_aimed and
    route_end while the panel named none of them, so a reader saw three hands
    with no key. This is the guard at that end.
    """

    def test_every_trace_field_reaches_the_readout(self):
        import inspect
        import dial
        src = inspect.getsource(dial.readout)
        t = route(load_ring(), "run Publish", tiered=["Le Curateur"])
        for key in t.to_dict():
            self.assertTrue(f'd["{key}"]' in src or f"d['{key}']" in src,
                            f"trace emits {key!r} and the readout never shows it")

    def test_the_key_names_all_three_hands(self):
        import inspect
        import dial
        src = inspect.getsource(dial.readout)
        for hand in ("precedence", "route ended", "route aimed"):
            self.assertIn(hand, src)


class ThePanelCoversTheAnatomy(unittest.TestCase):
    """Every mechanism doctrine names has to reach the panel.

    Fourth seam of the same failure. The split-seconds hand was added to
    le-conseil.md's anatomy table and the mechanisms panel never picked it up,
    so the sheet listed eleven parts for a movement doctrine said had twelve.
    """

    def test_every_mechanism_in_doctrine_is_on_the_panel(self):
        from dial import load_anatomy, MECHANISMS, NOT_MECHANISMS
        listed = {key for _, key, _ in MECHANISMS}
        missing = set(load_anatomy()) - listed - set(NOT_MECHANISMS)
        self.assertEqual(missing, set(),
                         f"doctrine names {missing} and the panel omits it")

    def test_the_panel_invents_nothing(self):
        # The other direction: a panel row for a part doctrine does not name
        # would render as UNASSIGNED IN DOCTRINE, which is honest but means
        # someone is listing a mechanism that does not exist.
        from dial import load_anatomy, MECHANISMS
        anat = load_anatomy()
        for _, key, _ in MECHANISMS:
            self.assertIn(key, anat, f"panel lists {key!r}, doctrine does not")


class TheSheetIsReproducible(unittest.TestCase):
    """The committed sheet and the page that gets published must be one thing.

    Fifth seam of the same failure, and the first where the surface is outside
    the repository. `cadran.html` is generated and committed; the artifact that
    is published is that sheet with its document wrapper removed. Both steps had
    an input recorded nowhere - the utterance lived only inside the output it
    produced, and the wrapper was stripped by hand at publish time. So the sheet
    could be regenerated from the wrong turn, and the published page could
    depict a turn the committed sheet did not, with nothing failing either way.
    Both inputs are named in dial.py now, and these are the guards on that.
    """

    def test_the_fragment_is_the_sheet_without_its_wrapper(self):
        # The fragment path shipped unexercised for its whole life: `standalone`
        # was never passed, so nothing had ever run the branch the published
        # page is built from.
        from dial import render
        trace = route(load_ring(), "run Publish, security check")
        standalone, fragment = render(trace), render(trace, standalone=False)
        stripped = standalone
        for wrapper in ('<!doctype html>\n',
                        '<html lang="en"><head><meta charset="utf-8">\n',
                        '<meta name="viewport" '
                        'content="width=device-width,initial-scale=1">\n',
                        '</head>\n<body>', '</body></html>'):
            self.assertIn(wrapper, stripped,
                          f"standalone render no longer contains {wrapper!r}; "
                          "the fragment is stripping something else")
            stripped = stripped.replace(wrapper, "", 1)
        self.assertEqual(stripped, fragment,
                         "the fragment differs from the sheet by more than its "
                         "wrapper - two renders of one page have diverged")

    def test_the_fragment_carries_no_document_wrapper(self):
        # A host supplies its own shell, so a stray <body> would nest inside it.
        from dial import render
        fragment = render(route(load_ring(), "run Publish"), standalone=False)
        for tag in ("<!doctype", "<html", "<head>", "<body>", "</body>",
                    "</html>"):
            self.assertNotIn(tag, fragment.lower(),
                             f"fragment still carries {tag!r}")
        # <header class="masthead"> must survive - it is content, not wrapper.
        self.assertIn('<header class="masthead">', fragment)

    def test_the_committed_sheet_is_what_the_default_renders(self):
        # The drift this catches is real and went unnoticed for six commits: the
        # bezel and the crown were reassigned in le-conseil.md and the sheet
        # kept engraving the old owners, because nothing re-rendered it and
        # nothing compared it. Regenerate with `python3 rouage/dial.py` after
        # any doctrine change; that command now reproduces this file exactly.
        from dial import OUT, SPECIMEN, render
        if not OUT.exists():                    # pragma: no cover
            self.skipTest(f"{OUT} not present")
        self.assertEqual(
            OUT.read_text(encoding="utf-8"),
            render(route(load_ring(), SPECIMEN)),
            f"{OUT.name} no longer matches what doctrine renders - "
            "regenerate it with: python3 rouage/dial.py --publish")


class InvariantsUnderComposition(unittest.TestCase):
    """Properties that must hold for every combination of inputs.

    The route_end bug was found by composing parameters by hand and looking.
    This is that method made systematic: a matrix of utterances, arming,
    verdicts, tiers and cap authorizations, with the invariants asserted on
    every resulting trace. Hand-picked cases test the paths someone thought of;
    this tests the ones nobody did.
    """

    UTTERANCES = ("what happened here", "run Publish", "run Harden",
                  "rename this file", "run Publish, argue against this",
                  "run Judgement", "run Exhibit, red team my backups",
                  "preserve this, map this, security check, "
                  "argue against this, classify this")
    ARMED = (None, "Le Fripon")
    VERDICTS = (None, [("Le Renégat", "Archive")], [("Le Renégat", "Reduce")],
                [("Le Vigile", "Release")])
    TIERED = (None, [], ["Le Curateur"],
              ["Le Vigile", "Le Curateur", "Le Messager", "Le Fripon"])
    CAPS = (None, 6)

    def setUp(self):
        self.ring = load_ring()

    def _matrix(self):
        for u, a, v, ti, c in itertools.product(
                self.UTTERANCES, self.ARMED, self.VERDICTS,
                self.TIERED, self.CAPS):
            kw = dict(verdicts=v, tiered=ti, authorize_cap=c)
            yield (f"{u!r} armed={a} verdicts={v} tiered={ti} cap={c}",
                   route(self.ring, u, a, **kw), u, a, kw)

    def test_no_candidate_ends_in_a_state_the_dial_cannot_render(self):
        for ctx, t, *_ in self._matrix():
            for c in t.candidates:
                self.assertIn(c.state, STATES, ctx)

    def test_le_fripon_is_never_active_without_the_crown(self):
        # The seal is the older of the two standing rules and the one thing no
        # route, proposal or verdict may reach around.
        for ctx, t, _, armed, _ in self._matrix():
            seat = next((c for c in t.candidates
                         if c.member.position == "05"), None)
            if seat and seat.state == "active":
                self.assertEqual(armed, "Le Fripon", ctx)

    def test_nothing_ever_stops_the_crown(self):
        # Neither le frein nor Le Sas may hold Le Sauvegarder. A mechanism that
        # can stop the crown is a mechanism that can lose the archive.
        for ctx, t, *_ in self._matrix():
            seat = next((c for c in t.candidates
                         if c.member.position == "crown"), None)
            if seat:
                self.assertNotIn(seat.state, ("held", "dissent"), ctx)

    def test_the_hand_never_indicates_a_member_that_is_not_standing(self):
        for ctx, t, *_ in self._matrix():
            if not t.route_end:
                continue
            seat = next((c for c in t.candidates
                         if c.member.position == t.route_end), None)
            if seat:
                self.assertEqual(seat.state, "active", ctx)

    def test_route_end_is_always_a_step_of_the_route(self):
        for ctx, t, *_ in self._matrix():
            if t.route_end and t.route_positions:
                self.assertIn(t.route_end, t.route_positions, ctx)

    def test_a_halt_always_has_a_dissenter_on_the_dial(self):
        # Otherwise the brake band reports a halt with no visible cause.
        for ctx, t, *_ in self._matrix():
            if t.halted:
                self.assertTrue(any(c.state == "dissent" for c in t.candidates),
                                ctx)

    def test_every_combination_is_reproducible(self):
        for ctx, t, u, armed, kw in self._matrix():
            self.assertEqual(route(self.ring, u, armed, **kw).to_dict(),
                             t.to_dict(), ctx)


class TheBarrelBoundaryIsWhereItSays(unittest.TestCase):
    """The train matches names. It does not read for meaning.

    This is a characterization test, not a wish. le-rouage.md forbids the train
    from interpreting, so a situation that plainly satisfies a gate's written
    condition must NOT fire it - only the quoted invocation phrases do. If
    someone later teaches evaluate() to understand the prose bullets, these
    fail, and that is the point: the boundary moves by decision, not by drift.

    The third test is the one that matters. It shows the boundary is a seam
    rather than a wall - the same situation IS admissible the moment something
    cites the bullet it satisfies. The mechanism is complete and unwired.
    """

    def setUp(self):
        self.ring = load_ring()
        self.limier = self.ring.by_name("Le Limier")
        # "an artifact shows modification, damage, or repair whose cause is
        # unknown" - Le Limier's first automatic condition, verbatim.
        self.bullet = self.limier.bullets[0]

    def _fired(self, utterance):
        t = route(self.ring, utterance)
        return any(c.member.name == "Le Limier" for c in t.candidates)

    def test_a_situation_that_satisfies_the_gate_does_not_fire_it(self):
        # Every one of these is squarely inside Le Limier's written condition.
        # None of them contain an invocation phrase, so none of them convene
        # him. This is the automatic half of the gate, and it does not run.
        for described in (
            "this file changed and I do not know why",
            "the pump failed and I cannot establish the sequence",
            "provenance is broken across a gap in the record",
        ):
            self.assertFalse(self._fired(described),
                             f"train read for meaning: {described!r}")

    def test_the_named_half_does_fire(self):
        for phrase in self.limier.phrases:
            self.assertTrue(self._fired(phrase), f"named gate missed {phrase!r}")

    def test_the_same_situation_is_admissible_once_something_cites_it(self):
        # The seam. The barrel reads the situation, recognises the condition,
        # and hands in the bullet verbatim; the train admits it without ever
        # having interpreted anything.
        t = Trace(utterance="this file changed and I do not know why")
        admitted = admit_proposals(
            self.ring, t, [("Le Limier", self.bullet)])
        self.assertEqual(len(admitted), 1)
        self.assertEqual(admitted[0].member.name, "Le Limier")
        self.assertEqual(t.failures, [])

    def test_and_a_paraphrase_of_that_same_condition_is_refused(self):
        # Which is what keeps the seam honest: the barrel may not soften a
        # condition to make a situation fit it.
        t = Trace(utterance="")
        admitted = admit_proposals(
            self.ring, t,
            [("Le Limier", "an artifact was modified and nobody knows why")])
        self.assertEqual(admitted, [])
        self.assertTrue(any("verbatim" in f for f in t.failures))

    def test_no_member_fires_on_a_plain_description_of_its_own_condition(self):
        # Generalised across the whole ring: every member's first bullet, fed
        # in as an utterance, must not convene that member. The bullets are
        # prose about when to convene, not invocations.
        for m in self.ring.members:
            if not m.bullets:
                continue
            t = route(self.ring, m.bullets[0])
            fired = [c for c in t.candidates
                     if c.member.name == m.name and not m.standing]
            self.assertEqual(fired, [],
                             f"{m.name} fired on its own bullet as prose")


class TheSignIsAFormNotTwoNames(unittest.TestCase):
    """Le Limier's gate is a sign, and a sign has to work for anyone's name.

    Doctrine writes it as a form with an illustration: `asks "Who is X?" of
    any name, handle, or maker's mark, as in "Who is JJ Ammo Can?"`.
    parse_activation() takes every quoted string in the section, so both
    landed as literals and containment fired the sign for exactly two inputs -
    the placeholder, and the single example doctrine happened to print. Asked
    of any other name it convened nobody, and a sign nobody else can give is
    not a sign. That is what these tests hold open.

    The first is the report as it arrived: another person tried the exchange
    with their own name and got nothing back.
    """

    def setUp(self):
        self.ring = load_ring()
        self.limier = self.ring.by_name("Le Limier")

    def _fired(self, utterance):
        t = route(self.ring, utterance)
        return any(c.member.name == "Le Limier" for c in t.candidates)

    def test_the_sign_fires_for_a_name_doctrine_never_printed(self):
        for name in ("Who is Tyler Etters?",
                     "Who is John Galt?",
                     "Who is this maker's mark?",
                     "who is JOHN JUICESTER?"):
            self.assertTrue(self._fired(name), f"the sign died on {name!r}")

    def test_the_printed_examples_still_fire(self):
        for phrase in self.limier.phrases:
            self.assertTrue(self._fired(phrase), f"named gate missed {phrase!r}")

    def test_the_question_mark_is_optional(self):
        # Decided with the width: a phrase ending in `?` takes the mark or the
        # end of the utterance, because the Operator types the sign faster
        # than he punctuates it.
        self.assertTrue(self._fired("who is jj ammo can"))

    def test_the_gate_reports_the_form_it_matched(self):
        # The compiled pattern is an implementation detail. What comes back is
        # the doctrine string, so the trace cites the gate as written.
        self.assertEqual(self.limier.matches("Who is Tyler Etters?"),
                         "Who is X?")

    def test_only_a_placeholder_widens_a_phrase(self):
        # The mechanism is general but it is not loose: every other phrase in
        # the ring stays literal containment, because none of them carry an X.
        widened = [(m.name, p) for m in self.ring.members for p in m.phrases
                   if phrase_pattern(p) is not None]
        self.assertEqual(widened, [("Le Limier", "Who is X?")])

    def test_the_placeholder_is_a_bare_capital_not_any_x(self):
        # 'X' inside a word is a letter, not a slot - otherwise a phrase like
        # "the axle" would start taking arbitrary text.
        self.assertIsNone(PLACEHOLDER.search("the axle"))
        self.assertIsNone(PLACEHOLDER.search("Xenon"))
        self.assertTrue(PLACEHOLDER.search("Who is X?"))

    def test_the_sign_is_a_gate_not_the_countersign(self):
        # What convenes him is the train's half. The countersign itself is
        # prose in his core, and stays there - the train never speaks.
        core = load_core(self.limier)
        self.assertIn("Who is John Galt?", core)
        self.assertIn("echo the countersign once, then work", core)


class RoutesFireOnlyWhenInvoked(unittest.TestCase):
    """Route names are common words. Ordinary prose must not convene a route.

    take_route() matched a route name as a bare substring, so "I need to build
    a shelf" ran Build and convened Le Cartographe and Le Forgeron. Seven of
    the council's own 81 gate bullets tripped a route when read as text.

    The harm was not extra noise. A phantom route admits two or three members
    and those count against the cap, so a false activation SUPPRESSED a real
    one - which inverts what the cap is for.
    """

    def setUp(self):
        self.ring = load_ring()

    def test_ordinary_prose_containing_a_route_word_does_not_route(self):
        for text in ("I need to build a shelf this weekend",
                     "let me identify the serial number",
                     "harden the epoxy overnight",
                     "recover the deleted photos",
                     "publish nothing yet",
                     "the intake manifold is cracked",
                     "triage can wait until Monday",
                     "exhibit A is the receipt"):
            self.assertIsNone(route(self.ring, text).route,
                              f"prose routed: {text!r}")

    def test_no_gate_bullet_in_doctrine_trips_a_route(self):
        # The council's own prose is the sharpest available corpus of sentences
        # that talk about this work without meaning to invoke anything.
        for m in self.ring.members:
            for bullet in m.bullets:
                self.assertIsNone(route(self.ring, bullet).route,
                                  f"{m.name} bullet routed: {bullet[:60]!r}")

    def test_every_route_still_answers_to_a_deliberate_invocation(self):
        for name in load_routes():
            for verb in ("run", "take", "route"):
                t = route(self.ring, f"{verb} {name}")
                self.assertEqual(t.route, name, f"{verb} {name} did not route")

    def test_a_phantom_route_can_no_longer_push_a_real_member_over_the_cap(self):
        # The regression that made this worth fixing rather than tidying.
        t = route(self.ring,
                  "build me a plan, preserve this, security check, "
                  "argue against this")
        self.assertIsNone(t.route)
        self.assertEqual([c.member.name for c in t.candidates
                          if "over cap" in c.note], [])

    def test_route_this_is_not_an_invocation_form(self):
        # It would collide with member phrases: "build this" is Le Forgeron's
        # own invocation and "map this" is Le Cartographe's.
        self.assertIsNone(route(self.ring, "build this").route)
        forgeron = [c for c in route(self.ring, "build this").candidates
                    if c.member.name == "Le Forgeron"]
        self.assertEqual(len(forgeron), 1, "the member phrase must still fire")


class TheInvocationGrammarIsDoctrine(unittest.TestCase):
    """No gate vocabulary lives in Python, including this.

    The fix for route over-firing put `run|take|route` in rouage.py, which is
    the one thing this build has consistently refused to do - the roster, the
    precedence ladder, the cap, the anatomy and every member phrase are parsed
    from markdown so doctrine and code cannot drift. The verbs are read from
    le-conseil.md now, the same way the cap is read from a sentence rather than
    written as a number.
    """

    def test_the_verbs_come_from_doctrine(self):
        self.assertEqual(load_invocations(), ("run", "take", "route"))

    def test_editing_doctrine_changes_what_the_train_answers_to(self):
        # The property that makes this doctrine rather than decoration.
        conseil = pathlib.Path(load_ring().members[0].path).parent.parent / \
            "overlays" / "le-conseil.md"
        original = conseil.read_text(encoding="utf-8")
        try:
            conseil.write_text(original.replace(
                "`run`, `take`, or `route`,",
                "`run`, `take`, `route`, or `engage`,", 1), encoding="utf-8")
            self.assertIn("engage", load_invocations())
            self.assertEqual(
                route(load_ring(), "engage Publish").route, "Publish")
        finally:
            conseil.write_text(original, encoding="utf-8")
        self.assertIsNone(route(load_ring(), "engage Publish").route)

    def test_a_missing_grammar_is_refused_rather_than_assumed(self):
        # Same discipline as the cap and the anatomy table: if doctrine does
        # not say it, the train does not invent a default.
        import tempfile
        stub = pathlib.Path(tempfile.mkdtemp()) / "le-conseil.md"
        stub.write_text("# nothing here", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_invocations(stub)


class Precedence(unittest.TestCase):
    """'Precedence follows irreversibility.'"""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_preservation_outranks_everything(self):
        trace = route(self.ring, "map this, then archive first")
        counted = [c.member.name for c in trace.candidates
                   if not c.member.standing]
        self.assertEqual(counted[0], "Le Sauvegarder")

    def test_the_ladder_decides_who_survives_the_cap(self):
        trace = route(
            self.ring,
            "preserve this, map this, security check, argue against this, "
            "classify this",
        )
        admitted = [c.member.name for c in trace.admitted()]
        self.assertIn("Le Sauvegarder", admitted)
        self.assertIn("Le Vigile", admitted)
        self.assertNotIn("Le Cartographe", admitted)

    def test_ordering_is_stable_for_unranked_members(self):
        # 'All others - by relevance' resolves to dial position, which is
        # arbitrary but declared. Arbitrary-and-declared beats inclination.
        trace = route(self.ring, "classify this, map this")
        others = [c.member.position for c in trace.candidates
                  if not c.member.standing]
        self.assertEqual(others, sorted(others))


class CoresOnly(unittest.TestCase):
    """'No loading doctrine at runtime. Cores only.'"""

    @classmethod
    def setUpClass(cls):
        cls.ring = load_ring()

    def test_load_core_excludes_doctrine(self):
        for m in self.ring.members:
            core = load_core(m)
            self.assertNotIn(DOCTRINE_HEADING, core)
            self.assertNotIn(CORE_HEADING, core)

    def test_load_core_keeps_the_gate(self):
        for m in self.ring.members:
            self.assertIn("Activation", load_core(m))

    def test_doctrine_exists_but_is_not_returned(self):
        # Guards against the test passing because the file has no doctrine.
        sceptique = self.ring.by_name("Le Sceptique")
        raw = sceptique.path.read_text(encoding="utf-8")
        self.assertIn(DOCTRINE_HEADING, raw)
        self.assertIn("Motto", raw)
        self.assertNotIn("Motto", load_core(sceptique))


class RoutineWork(unittest.TestCase):
    """'Routine work convenes no one.'"""

    def test_ordinary_request_lights_only_the_standing_register(self):
        ring = load_ring()
        trace = route(ring, "rename this file to lowercase")
        admitted = [c.member.name for c in trace.admitted()]
        self.assertEqual(admitted, ["Le Sceptique"])
        self.assertEqual(trace.failures, [])


if __name__ == "__main__":
    unittest.main()
