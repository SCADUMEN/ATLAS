"""Invariants for the level computation. Run: python3 -m unittest discover level -v"""

import math
import unittest

import level as g


class Curve(unittest.TestCase):
    def test_inverse_holds_at_every_threshold(self):
        # The XP required for level L must read back as exactly level L.
        for lv in range(1, 101):
            xp = math.ceil(g.xp_for(lv, 13000))
            self.assertEqual(g.level_for(xp, 13000), lv, f"level {lv}")

    def test_monotonic_in_xp(self):
        last = -1
        for xp in range(0, 20000, 137):
            cur = g.level_for(xp, 13000)
            self.assertGreaterEqual(cur, last)
            last = cur

    def test_capped_at_100(self):
        self.assertEqual(g.level_for(10 ** 9, 13000), 100)

    def test_zero(self):
        self.assertEqual(g.level_for(0, 13000), 0)


class Ledger(unittest.TestCase):
    def setUp(self):
        self.r = g.compute()

    def test_level_consistent_with_xp(self):
        self.assertEqual(self.r["level"],
                         g.level_for(self.r["xp"], self.r["xp100"]))
        self.assertTrue(0 <= self.r["level"] <= 100)

    def test_no_module_claims_a_missing_file(self):
        # Evidence rule: every built module's file must exist, or it is a bug.
        self.assertEqual(self.r["missing"], [], "built modules with no file")

    def test_reincarnation_is_the_lone_s_tier(self):
        s = [m for m in self.r["counted"] if m["tier"] == "S"]
        self.assertEqual([m["id"] for m in s], ["reincarnation"])
        self.assertEqual(s[0]["xp"], 1000)

    def test_tiers_parsed(self):
        with open(g.DOCTRINE, encoding="utf-8") as fh:
            self.assertEqual(g.parse_tiers(fh.read())["S"], 1000)


if __name__ == "__main__":
    unittest.main()
