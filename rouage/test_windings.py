"""atlas-windings: counts that separate named from unnamed, and no text out."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import windings

NAMES = {"01": "Le Sceptique", "crown": "Le Sauvegarder", "04": "Le Vigile",
         "07": "Le Limier"}
SECRET = "wipe the drive with the tax scans on it"


def prompt(when, utterance, admitted=("01",)):
    return {"when": when, "utterance": utterance, "admitted": list(admitted),
            "failures": []}


def settle(when, utterance, admitted, proposals, failures=()):
    return {"when": when, "utterance": utterance, "admitted": list(admitted),
            "failures": list(failures), "kind": "settle",
            "proposals": [list(p) for p in proposals]}


class Summary(unittest.TestCase):

    def setUp(self):
        self.log = [
            prompt("2026-10-25T01:00:00Z", SECRET),
            settle("2026-10-25T01:00:30Z", SECRET, ["crown", "04", "01"],
                   [("Le Sauvegarder", "source at risk"), ("Le Vigile", "")]),
            prompt("2026-10-25T01:01:00Z", "ok"),
            prompt("2026-10-26T09:00:00Z", "release the hound", ["07", "01"]),
            prompt("2026-10-26T09:05:00Z", "do it"),
            settle("2026-10-26T09:05:20Z", "do it", ["01"],
                   [("Le Messager", "bench log")],
                   ["rejected proposal: Le Messager cited a prohibition, not an "
                    "activation - ..."]),
        ]
        self.s = windings.summarize(self.log, NAMES)

    def test_named_and_unnamed_are_counted_apart(self):
        self.assertEqual(self.s["named"], {"Le Limier": 1})
        self.assertEqual(self.s["automatic"], {"Le Sauvegarder": 1, "Le Vigile": 1})
        self.assertEqual(self.s["proposed"],
                         {"Le Sauvegarder": 1, "Le Vigile": 1, "Le Messager": 1})

    def test_a_turn_is_its_prompt_entry_plus_its_settle_entry(self):
        self.assertEqual((self.s["prompts"], self.s["settles"], self.s["lit"]), (4, 2, 2))

    def test_continuations_and_their_dark_rate(self):
        self.assertEqual((self.s["continuations"], self.s["continuationsDark"]), (2, 2))

    def test_an_inverted_gate_is_counted_as_such(self):
        self.assertEqual(self.s["failures"], {"inverted": 1})

    def test_per_day_carries_only_unnamed_admissions(self):
        self.assertEqual(self.s["perDay"],
                         {"2026-10-25": {"Le Sauvegarder": 1, "Le Vigile": 1}})

    def test_no_prompt_or_reason_text_leaves_the_report(self):
        out = json.dumps(self.s) + windings.render(self.s)
        for text in (SECRET, "source at risk", "bench log", "release the hound"):
            self.assertNotIn(text, out)


class Reading(unittest.TestCase):

    def test_since_filters_and_junk_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "windings.jsonl"
            log.write_text("\n".join([
                json.dumps(prompt("2026-10-20T00:00:00Z", "old")),
                "not json",
                json.dumps(prompt("2026-10-25T00:00:00Z", "new")),
            ]) + "\n", encoding="utf-8")
            self.assertEqual(len(windings.entries(log, since="2026-10-24")), 1)


if __name__ == "__main__":
    unittest.main()
