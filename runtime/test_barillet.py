"""Tests for the fitted-barrel record: bin/atlas-barillet.

The barrel is the one part of the instrument that is not version-controlled, so
its record in overlays/le-barillet.md is the only evidence it was ever fitted.
The serial is what makes that record falsifiable — the SHA-256 of the ordered
commit hashes of the work the barrel drove.

These tests care about two things above all: that the seal derived here matches
the one written by hand in the doctrine, and that the verifier can actually
*fail*. A checker that cannot be shown to reject a bad input is not evidence,
which is the failure mode the Service Record already records once.

    python3 -m unittest discover runtime -v
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "bin" / "atlas-barillet"
DOCTRINE = ROOT / "overlays" / "le-barillet.md"

# The first barrel, sealed by hand in overlays/le-barillet.md.
LE_CLAUDE_RANGE = "c612851..289aeb8"
LE_CLAUDE_SERIAL = "0d3a4b8622b0609c0e1e32fba8b97289d947a5256bc636055e5083eeab5bbda9"


def run(*args, env=None, check=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([str(a) for a in args], cwd=ROOT, env=e,
                          text=True, capture_output=True, check=check)


def have_range() -> bool:
    """A shallow checkout cannot resolve the historical range."""
    return subprocess.run(["git", "-C", str(ROOT), "rev-list", "--quiet",
                           LE_CLAUDE_RANGE], capture_output=True).returncode == 0


class TheSeal(unittest.TestCase):

    @unittest.skipUnless(have_range(), "historical range not in this checkout")
    def test_derives_the_serial_written_by_hand_in_the_doctrine(self):
        # The anchor. If this ever drifts, either the tool is wrong or the
        # history was rewritten -- and both must be loud.
        out = run(TOOL, "serial", LE_CLAUDE_RANGE).stdout.strip()
        self.assertEqual(out, LE_CLAUDE_SERIAL)

    @unittest.skipUnless(have_range(), "historical range not in this checkout")
    def test_matches_the_command_the_doctrine_tells_you_to_reproduce_it_with(self):
        # le-barillet.md publishes: git log --format=%H --reverse <range> | shasum -a 256
        log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H",
                              "--reverse", LE_CLAUDE_RANGE],
                             text=True, capture_output=True, check=True).stdout
        import hashlib
        self.assertEqual(hashlib.sha256(log.encode()).hexdigest(),
                         run(TOOL, "serial", LE_CLAUDE_RANGE).stdout.strip())

    def test_a_range_naming_no_commits_is_refused(self):
        r = run(TOOL, "serial", "HEAD..HEAD", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no commits", r.stderr)

    def test_an_unresolvable_range_is_refused(self):
        r = run(TOOL, "serial", "nope-not-a-ref..also-not", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not resolvable", r.stderr)


class TheVerifier(unittest.TestCase):

    @unittest.skipUnless(have_range(), "historical range not in this checkout")
    def test_the_committed_records_still_seal(self):
        r = run(TOOL, "verify")
        self.assertIn("seal holds", r.stdout)

    @unittest.skipUnless(have_range(), "historical range not in this checkout")
    def test_a_tampered_serial_is_rejected(self):
        # The test that makes the verifier evidence rather than decoration.
        text = DOCTRINE.read_text(encoding="utf-8").replace(LE_CLAUDE_SERIAL, "0" * 64)
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "le-barillet.md"
            bad.write_text(text, encoding="utf-8")
            r = run(TOOL, "verify", env={"ATLAS_BARILLET_DOCTRINE": str(bad)},
                    check=False)
        self.assertNotEqual(r.returncode, 0, "a forged seal was accepted")
        self.assertIn("BROKEN SEAL", r.stderr)

    def test_a_doctrine_with_no_records_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            empty = Path(d) / "le-barillet.md"
            empty.write_text("# LE BARILLET\n\nNo barrels yet.\n", encoding="utf-8")
            r = run(TOOL, "verify", env={"ATLAS_BARILLET_DOCTRINE": str(empty)},
                    check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no fitted-barrel records", r.stderr)


class TheRecord(unittest.TestCase):

    def test_the_model_is_never_guessed(self):
        # Nothing in the environment states which barrel is fitted. Inventing
        # one would defeat the reason the serial exists.
        env = {k: v for k, v in os.environ.items() if k != "ATLAS_BARREL"}
        r = subprocess.run([str(TOOL), "record", "HEAD~1..HEAD"], cwd=ROOT,
                           env=env, text=True, capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("never guessed", r.stderr)

    def test_the_emitted_block_carries_the_derived_serial(self):
        rng = "HEAD~1..HEAD"
        out = run(TOOL, "record", rng, "TEST BARREL",
                  env={"ATLAS_BARREL": "a test barrel"}).stdout
        serial = run(TOOL, "serial", rng).stdout.strip()
        self.assertIn(serial, out)
        self.assertIn("### `TEST BARREL`", out)
        self.assertIn("a test barrel", out)
        self.assertIn(f"git log --format=%H --reverse {rng} | shasum -a 256", out)

    def test_the_emitted_block_verifies(self):
        # Round trip: what `record` writes is what `verify` accepts. If the
        # emitted shape drifts from the shape the parser reads, this catches it.
        rng = "HEAD~2..HEAD"
        block = run(TOOL, "record", rng, "ROUND TRIP",
                    env={"ATLAS_BARREL": "a test barrel"}).stdout
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "le-barillet.md"
            f.write_text("# LE BARILLET\n\n## Fitted Barrels\n\n" + block,
                         encoding="utf-8")
            r = run(TOOL, "verify", env={"ATLAS_BARILLET_DOCTRINE": str(f)})
        self.assertIn("seal holds", r.stdout)
        self.assertIn("ROUND TRIP", r.stdout)

    def test_the_emitted_block_matches_the_doctrines_field_shape(self):
        out = run(TOOL, "record", "HEAD~1..HEAD", "SHAPE",
                  env={"ATLAS_BARREL": "a test barrel"}).stdout
        for field in ("**Fitted:**", "**Barrel:**", "**Drove:**", "**Serial:**"):
            self.assertIn(field, out, f"{field} missing from the record")
        self.assertRegex(out, r"```text\n[0-9a-f]{64}\n```")


class TheHost(unittest.TestCase):

    def test_the_host_is_named_not_invented(self):
        out = run(TOOL, "host").stdout.strip()
        self.assertTrue(out, "host printed nothing")

    def test_an_unmarked_environment_says_unknown(self):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("CLAUDE", "CODEX")) and k != "AI_AGENT"}
        r = subprocess.run([str(TOOL), "host"], cwd=ROOT, env=env,
                           text=True, capture_output=True, check=True)
        self.assertEqual(r.stdout.strip(), "unknown host")


if __name__ == "__main__":
    unittest.main()
