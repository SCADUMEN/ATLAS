"""Invariants for the release guard. Run: python3 -m unittest discover level -v"""

import unittest

import release_guard as g


class Guard(unittest.TestCase):
    def test_minor_bump_without_xp_move_blocks(self):
        msg = g.guard("1.4.3", "1.5.0", 11600, 11600)
        self.assertIsNotNone(msg)
        self.assertIn("did not move", msg)

    def test_minor_bump_with_xp_move_passes(self):
        self.assertIsNone(g.guard("1.4.3", "1.5.0", 10350, 11600))

    def test_major_bump_without_xp_move_blocks(self):
        # (2,0) > (1,9), so a major bump is held to the same rule.
        self.assertIsNotNone(g.guard("1.9.0", "2.0.0", 11600, 11600))

    def test_major_bump_with_xp_move_passes(self):
        self.assertIsNone(g.guard("1.9.0", "2.0.0", 11600, 12000))

    def test_patch_bump_is_exempt(self):
        # Bug fixes need not level up, even with no XP change.
        self.assertIsNone(g.guard("1.4.3", "1.4.4", 11600, 11600))

    def test_no_bump_is_a_noop(self):
        self.assertIsNone(g.guard("1.5.0", "1.5.0", 11600, 11600))

    def test_xp_going_down_on_patch_is_still_exempt(self):
        # The guard only speaks to major/minor bumps; a patch is never blocked.
        self.assertIsNone(g.guard("1.4.3", "1.4.4", 11600, 11000))

    def test_unparseable_version_never_blocks(self):
        # Absence of evidence must not fail a merge.
        self.assertIsNone(g.guard("", "1.5.0", 10350, 10350))
        self.assertIsNone(g.guard("nonsense", "also-nonsense", 10350, 10350))

    def test_v_prefixed_versions_parse(self):
        self.assertIsNotNone(g.guard("v1.4.3", "v1.5.0", 11600, 11600))


class Cli(unittest.TestCase):
    def test_exit_1_on_violation(self):
        self.assertEqual(g.main(["release_guard.py", "1.4.3", "1.5.0", "11600", "11600"]), 1)

    def test_exit_0_when_fine(self):
        self.assertEqual(g.main(["release_guard.py", "1.4.3", "1.5.0", "10350", "11600"]), 0)

    def test_exit_2_on_bad_args(self):
        self.assertEqual(g.main(["release_guard.py", "1.4.3", "1.5.0"]), 2)
        self.assertEqual(g.main(["release_guard.py", "1.4.3", "1.5.0", "x", "y"]), 2)


if __name__ == "__main__":
    unittest.main()
