"""Tests for the live train: bin/atlas-route and rouage/hook.py.

    python3 -m unittest discover rouage -v

Every case pins one promise the hook makes to a live session: the train decides
who convenes, the router draws the dial, held members stay out of the barrel's
prose, and no failure of any kind stops the Operator's prompt.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hook
from rouage import REPO, load_ring

ROUTE = REPO / "bin" / "atlas-route"
WHEN = "2026-10-09T00:00:00Z"
NO_LOG = {"ATLAS_NO_WINDING": "1"}

# Six named members against a cap of four. Precedence decides who passes; the
# test reads names out of the trace rather than restating the ladder here.
CROWDED = ("preserve this, map this, security check, argue against this, "
           "classify this, reconstruct this")


def context(payload: dict) -> str:
    return payload["hookSpecificOutput"]["additionalContext"]


class Gates(unittest.TestCase):
    """The prompts the Operator actually types, through the doctrine as written."""

    def assert_limier(self, prompt: str):
        payload = hook.respond(prompt, NO_LOG, WHEN)
        self.assertIsNotNone(payload, prompt)
        self.assertIn("08●", payload["systemMessage"])
        self.assertIn("● 08 Le Limier", payload["systemMessage"])
        self.assertIn("- Le Limier (08)", context(payload))
        self.assertIn("skill `atlas:le-limier`", context(payload))

    def test_release_the_hound_convenes_le_limier(self):
        # Added to Le Limier's gate in subroutines/le-limier.md. Containment
        # matching means the plural fires the same gate.
        self.assert_limier("release the hound")
        self.assert_limier("ok, release the hounds on this drive")

    def test_who_is_jj_ammo_can_convenes_le_limier_however_it_is_typed(self):
        for prompt in ("Who is JJ Ammo Can?", "who is jj ammo can?",
                       "who is jj ammo can"):
            self.assert_limier(prompt)


class Silence(unittest.TestCase):

    def test_the_standing_turn_draws_nothing(self):
        # Le Sceptique stands on every turn. Drawing him alone would put the
        # dial on every prompt, and a readout on every turn is noise.
        self.assertIsNone(hook.respond("lets get some xp", NO_LOG, WHEN))

    def test_skills_that_draw_their_own_dial_are_left_alone(self):
        for prompt in ("/atlas:le-cadran release the hound",
                       "/atlas:le-conseil map this"):
            self.assertIsNone(hook.respond(prompt, NO_LOG, WHEN), prompt)

    def test_opt_out(self):
        env = {"ATLAS_NO_ROUTE": "1", **NO_LOG}
        self.assertIsNone(hook.respond("release the hound", env, WHEN))


class TheCrown(unittest.TestCase):

    def test_winding_the_crown_always_draws_the_dial(self):
        # /atlas with nothing convened still shows the train it set going.
        payload = hook.respond("/atlas lets get some xp", NO_LOG, WHEN)
        self.assertIn("LE CADRAN", payload["systemMessage"])
        self.assertIn('INPUT  "lets get some xp"', payload["systemMessage"])
        self.assertIn("winds the crown", context(payload))

    def test_the_rite_routes_its_arguments_not_its_command(self):
        payload = hook.respond("/atlas release the hound", NO_LOG, WHEN)
        self.assertIn("- Le Limier (08)", context(payload))
        self.assertNotIn("/atlas", payload["systemMessage"].split("INPUT")[1])

    def test_bare_rite_draws_too(self):
        self.assertIn("LE CADRAN",
                      hook.respond("/atlas", NO_LOG, WHEN)["systemMessage"])


class TwoSurfaces(unittest.TestCase):
    """The dial shows the trace; the barrel's context keeps held members out."""

    def test_held_members_are_on_the_dial_and_counted_not_named_in_context(self):
        trace = hook.route(load_ring(), CROWDED)
        held = [c.member.name for c in trace.candidates if c.state == "held"]
        self.assertTrue(held, "the crowded prompt must exceed the cap")

        payload = hook.respond(CROWDED, NO_LOG, WHEN)
        ctx = context(payload)
        self.assertIn(f"Held by Le Sas: {len(held)}.", ctx)
        for name in held:
            self.assertNotIn(name, ctx)
        self.assertIn("Recorded failure: over-cap", ctx)

    def test_a_sealed_member_is_named_as_sealed_and_not_convened(self):
        fripon = next(m for m in load_ring().members if m.sealed)
        payload = hook.respond(f"bring in {fripon.phrases[0]}", NO_LOG, WHEN)
        ctx = context(payload)
        sealed_block = ctx.split("Sealed")[1]
        self.assertIn(fripon.name, sealed_block)
        self.assertNotIn("Convened", ctx)

    def test_the_model_is_told_not_to_redraw_the_dial(self):
        ctx = context(hook.respond("release the hound", NO_LOG, WHEN))
        self.assertIn("Do not redraw it", ctx)

    def test_the_dial_carries_no_escape_codes(self):
        msg = hook.respond("release the hound", NO_LOG, WHEN)["systemMessage"]
        self.assertNotIn("\x1b[", msg)


class Faults(unittest.TestCase):
    """Loud on the dial's channel, never a blocked prompt, never a false dial."""

    def test_a_train_fault_is_reported_and_draws_nothing(self):
        with mock.patch.object(hook, "route", side_effect=ValueError("bad ring")):
            payload = hook.respond("release the hound", NO_LOG, WHEN)
        self.assertEqual(set(payload), {"systemMessage"})
        self.assertIn("faulted and drew nothing", payload["systemMessage"])
        self.assertIn("ValueError: bad ring", payload["systemMessage"])
        self.assertNotIn("LE CADRAN", payload["systemMessage"])

    def test_an_unwritable_log_is_reported_even_on_a_silent_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "not-a-dir"
            blocker.write_text("")
            env = {"ATLAS_WINDING_LOG": str(blocker / "windings.jsonl")}
            payload = hook.respond("lets get some xp", env, WHEN)
        self.assertIn("winding not recorded", payload["systemMessage"])
        self.assertNotIn("hookSpecificOutput", payload)


class TheLog(unittest.TestCase):

    def test_every_routed_turn_is_recorded_silent_or_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "atlas" / "windings.jsonl"
            env = {"ATLAS_WINDING_LOG": str(log)}
            hook.respond("lets get some xp", env, WHEN)
            hook.respond("release the hound", env, WHEN)
            hook.respond("/atlas:le-cadran map this", env, WHEN)
            entries = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual([e["utterance"] for e in entries],
                         ["lets get some xp", "release the hound"])
        self.assertEqual(entries[1]["when"], WHEN)
        self.assertIn("08", entries[1]["admitted"])

    def test_the_default_log_sits_under_the_claude_config_home(self):
        self.assertEqual(hook.winding_log({"CLAUDE_CONFIG_DIR": "/cfg"}),
                         Path("/cfg/atlas/windings.jsonl"))
        self.assertIsNone(hook.winding_log({"ATLAS_NO_WINDING": "1"}))


class Entrypoint(unittest.TestCase):
    """bin/atlas-route as Claude Code runs it: JSON on stdin, from any cwd."""

    def run_hook(self, stdin: str, cwd: Path) -> subprocess.CompletedProcess:
        env = {**os.environ, **NO_LOG}
        env.pop("ATLAS_NO_ROUTE", None)
        return subprocess.run([str(ROUTE)], input=stdin, cwd=cwd, env=env,
                              text=True, capture_output=True, timeout=20)

    def test_emits_a_user_prompt_submit_payload_from_a_foreign_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            # A planted module in the Operator's project must not shadow the
            # train: the wrapper runs python3 -I.
            (Path(tmp) / "rouage.py").write_text("raise SystemExit(9)\n")
            done = self.run_hook(json.dumps({"prompt": "release the hound"}),
                                 Path(tmp))
        self.assertEqual(done.returncode, 0)
        payload = json.loads(done.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"],
                         "UserPromptSubmit")
        self.assertIn("Le Limier", payload["systemMessage"])

    def test_garbage_on_stdin_is_a_silent_clean_exit(self):
        for stdin in ("", "not json", "[1, 2]", '{"prompt": 7}'):
            done = self.run_hook(stdin, REPO)
            self.assertEqual(done.returncode, 0, stdin)
            self.assertEqual(done.stdout.strip(), "", stdin)

    def test_the_plugin_wires_it_on_every_prompt(self):
        hooks = json.loads((REPO / "hooks" / "hooks.json").read_text())
        commands = [h["command"] for group in hooks["hooks"]["UserPromptSubmit"]
                    for h in group["hooks"]]
        self.assertEqual(commands, ['"${CLAUDE_PLUGIN_ROOT}/bin/atlas-route"'])


if __name__ == "__main__":
    unittest.main()
