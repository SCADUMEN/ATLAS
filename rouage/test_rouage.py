"""Tests for Le Rouage.

le-rouage.md: 'Determinism is testable. The same input and the same archive
state must select the same modes. If it does not, the train is reasoning,
and it should not be.'

These are that test, plus one per prohibition. Stdlib unittest - no test
dependency to install on the board in the case.

    python3 -m unittest discover rouage -v
"""

import unittest

from rouage import (
    CORE_HEADING,
    DOCTRINE_HEADING,
    Ring,
    Trace,
    admit_proposals,
    evaluate,
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
