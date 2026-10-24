"""Tests for the turn read back: bin/atlas-settle and rouage/settle.py.

    python3 -m unittest discover rouage -v

The Stop hook draws the one dial a turn gets, from what actually convened:
the named half the prompt carried and the council skills the barrel invoked.
Each case is a transcript shaped like the ones Claude Code writes.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import settle
from rouage import REPO

SETTLE = REPO / "bin" / "atlas-settle"
WHEN = "2026-10-24T00:00:00Z"
NO_LOG = {"ATLAS_NO_WINDING": "1"}


def prompt(text: str, human: bool = True) -> dict:
    return {"type": "user", "origin": {"kind": "human" if human else "task"},
            "message": {"role": "user", "content": text}}


def command(name: str, args: str = "") -> dict:
    return prompt(f"<command-message>{name.lstrip('/')}</command-message>\n"
                  f"<command-name>{name}</command-name>\n"
                  f"<command-args>{args}</command-args>")


def skill(name: str, args: str = "") -> list[dict]:
    """A Skill call, its result, and the skill body it loads."""
    call = {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "t1", "name": "Skill",
         "input": {"skill": name, "args": args}}]}}
    result = {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "Launching"}]}}
    body = {"type": "user", "isMeta": True,
            "message": {"content": "## OPERATIONAL CORE ..."}}
    return [call, result, body]


def reply(text: str = "done") -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


class Transcript:
    """A transcript file on disk, for one test."""

    def __init__(self, *entries):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "session.jsonl"
        rows = []
        for e in entries:
            rows.extend(e if isinstance(e, list) else [e])
        self.path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def respond(self, env=None, **event):
        return settle.respond({"transcript_path": str(self.path), **event},
                              NO_LOG if env is None else env, WHEN)

    def close(self):
        self.dir.cleanup()


class TheTurnIsReadBack(unittest.TestCase):

    def run_turn(self, *entries, env=None, **event):
        t = Transcript(*entries)
        self.addCleanup(t.close)
        return t.respond(env, **event)

    def test_a_named_turn_draws_the_dial_it_used_to_get_at_prompt_time(self):
        payload = self.run_turn(prompt("release the hound"), reply())
        self.assertIn("08●", payload["systemMessage"])
        self.assertIn("● 08 Le Limier", payload["systemMessage"])

    def test_a_member_the_barrel_convened_is_on_the_dial(self):
        payload = self.run_turn(
            prompt("the board died after the bios flash and i dont know why"),
            skill("atlas:le-limier", "a system failed and nobody has the "
                                     "sequence of what happened"),
            reply())
        self.assertIn("● 08 Le Limier", payload["systemMessage"])

    def test_a_quiet_turn_draws_nothing(self):
        self.assertIsNone(self.run_turn(prompt("what time is it"), reply()))

    def test_the_rite_and_the_displays_are_left_alone(self):
        for entries in (
            [command("/atlas", "release the hound"),
             skill("atlas:le-limier", "reconstruct")],
            [command("/atlas:le-cadran", "release the hound")],
            [command("/atlas:le-conseil", "release the hound")],
        ):
            self.assertIsNone(self.run_turn(*entries, reply()), entries[0])

    def test_a_typed_member_command_still_routes_its_words(self):
        payload = self.run_turn(command("/atlas:le-limier", "release the hound"),
                                reply())
        self.assertIn("Le Limier", payload["systemMessage"])

    def test_only_this_turns_calls_count(self):
        # Le Limier convened last turn. This turn convened nobody.
        payload = self.run_turn(
            prompt("the board died and i dont know why"),
            skill("atlas:le-limier", "failure sequence unknown"), reply(),
            prompt("ok thanks"), reply())
        self.assertIsNone(payload)

    def test_a_task_notification_is_not_the_turns_prompt(self):
        payload = self.run_turn(
            prompt("the board died and i dont know why"),
            skill("atlas:le-limier", "failure sequence unknown"),
            prompt("<task-notification>done</task-notification>", human=False),
            reply())
        self.assertIn("Le Limier", payload["systemMessage"])

    def test_displays_helpers_and_other_plugins_are_not_proposals(self):
        payload = self.run_turn(
            prompt("tidy up"),
            skill("atlas:le-cadran", "x"), skill("atlas:git-cleanup"),
            skill("claude-in-chrome", "open a tab"), reply())
        self.assertIsNone(payload)

    def test_le_fripon_is_not_admitted_on_a_paraphrase(self):
        payload = self.run_turn(
            prompt("is my nas login actually safe"),
            skill("atlas:le-fripon", "test whether the nas login holds"),
            reply())
        self.assertNotIn("● 05 Le Fripon", payload["systemMessage"])

    def test_opt_outs_and_a_missing_transcript_are_silent(self):
        entries = (prompt("release the hound"), reply())
        self.assertIsNone(self.run_turn(*entries, env={"ATLAS_NO_ROUTE": "1"}))
        self.assertIsNone(self.run_turn(*entries, stop_hook_active=True))
        self.assertIsNone(settle.respond(
            {"transcript_path": "/nonexistent/x.jsonl"}, NO_LOG, WHEN))
        self.assertIsNone(settle.respond({}, NO_LOG, WHEN))


class TheProposals(unittest.TestCase):

    def test_args_are_collapsed_and_cut_to_a_reason(self):
        ring = settle.load_ring()
        long = "a  system\nfailed " + "and more " * 60
        (name, reason), = settle.proposals_for(ring, [("le-limier", long)])
        self.assertEqual(name, "Le Limier")
        self.assertTrue(reason.startswith("a system failed and more"))
        self.assertLessEqual(len(reason), settle.REASON_LIMIT)

    def test_an_atlas_skill_not_on_the_ring_is_dropped(self):
        ring = settle.load_ring()
        self.assertEqual(settle.proposals_for(ring, [("le-fantome", "x")]), [])


class TheSettleEntry(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "windings.jsonl"
        self.env = {"ATLAS_WINDING_LOG": str(self.log)}

    def respond(self, *entries):
        t = Transcript(*entries)
        self.addCleanup(t.close)
        return t.respond(self.env)

    def test_a_proposed_turn_is_recorded_as_a_settle(self):
        self.respond(prompt("the board died and i dont know why"),
                     skill("atlas:le-limier", "failure sequence unknown"),
                     reply())
        entry = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(entry["kind"], "settle")
        self.assertEqual(entry["proposals"],
                         [["Le Limier", "failure sequence unknown"]])
        self.assertIn("08", entry["admitted"])

    def test_a_named_only_turn_is_not_recorded_twice(self):
        # atlas-route already wrote this prompt's winding.
        self.respond(prompt("release the hound"), reply())
        self.assertFalse(self.log.exists())


class TheWrapper(unittest.TestCase):

    def run_hook(self, stdin: str, cwd: Path) -> subprocess.CompletedProcess:
        env = {**os.environ, **NO_LOG}
        env.pop("ATLAS_NO_ROUTE", None)
        return subprocess.run([str(SETTLE)], input=stdin, cwd=cwd, env=env,
                              text=True, capture_output=True, timeout=20)

    def test_draws_from_a_foreign_cwd(self):
        t = Transcript(prompt("release the hound"), reply())
        self.addCleanup(t.close)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "rouage.py").write_text("raise SystemExit(9)\n")
            done = self.run_hook(
                json.dumps({"transcript_path": str(t.path)}), Path(tmp))
        self.assertEqual(done.returncode, 0)
        self.assertIn("Le Limier", json.loads(done.stdout)["systemMessage"])

    def test_garbage_on_stdin_is_a_silent_clean_exit(self):
        for stdin in ("", "not json", "[1, 2]", '{"transcript_path": 7}'):
            done = self.run_hook(stdin, REPO)
            self.assertEqual(done.returncode, 0, stdin)
            self.assertEqual(done.stdout.strip(), "", stdin)

    def test_the_plugin_wires_it_when_the_turn_stops(self):
        hooks = json.loads((REPO / "hooks" / "hooks.json").read_text())
        commands = [h["command"] for group in hooks["hooks"]["Stop"]
                    for h in group["hooks"]]
        self.assertEqual(commands, ['"${CLAUDE_PLUGIN_ROOT}/bin/atlas-settle"'])


if __name__ == "__main__":
    unittest.main()
