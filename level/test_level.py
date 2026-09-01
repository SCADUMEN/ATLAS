"""Invariants for the level computation. Run: python3 -m unittest discover level -v"""

import math
import pathlib
import re
import unittest

import level as g
import service as svc


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


class Service(unittest.TestCase):
    """The service axis: it records upkeep without ever moving the level."""

    def setUp(self):
        self.r = g.compute()
        with open(g.DOCTRINE, encoding="utf-8") as fh:
            self.md = fh.read()

    def test_documented_credits_match_the_derived_ones(self):
        # Doctrine and score cannot drift: the table in le-niveau.md is a
        # snapshot, and this is what keeps the snapshot true.
        documented = svc.parse_credits(self.md, g._rows)
        self.assertTrue(documented, "no service credit table found")
        for tier, credit in documented.items():
            self.assertEqual(credit, svc.credit(tier, self.r["tiers"]),
                             f"tier {tier} credit drifted from the derived value")

    def test_credit_is_a_tenth_of_the_tier(self):
        self.assertEqual(svc.credit("S", self.r["tiers"]), 100)
        self.assertEqual(svc.credit("C", self.r["tiers"]), 10)

    def test_service_never_enters_xp(self):
        # The whole point of the axis. XP is the sum of counted modules alone.
        self.assertEqual(self.r["xp"],
                         sum(m["xp"] for m in self.r["counted"]))
        self.assertGreater(self.r["service_pts"], 0, "no service recorded to test")

    def test_service_does_not_move_the_level(self):
        self.assertEqual(self.r["level"],
                         g.level_for(self.r["xp"], self.r["xp100"]))

    def test_every_service_row_names_a_ledgered_module(self):
        self.assertEqual(self.r["service_unledgered"], [],
                         "service rows naming no module in the ledger")

    def test_every_service_row_names_a_released_patch_version(self):
        changelog = pathlib.Path(g.REPO, "CHANGELOG.md").read_text(encoding="utf-8")
        for row in self.r["service"]:
            self.assertIn(f"## [{row['version']}]", changelog,
                          f"{row['version']} is not in the changelog")
            self.assertNotEqual(row["version"].split(".")[2], "0",
                                f"{row['version']} is not a patch release")

    def test_minor_and_major_rows_are_refused(self):
        md = ("### The Service Ledger\n"
              "| Version | Repaired | Note |\n"
              "|---|---|---|\n"
              "| 1.8.0 | git-cleanup | a minor |\n"
              "| 1.8.1 | git-cleanup | a patch |\n")
        rows = svc.parse_ledger(md, g._rows)
        self.assertEqual([r["version"] for r in rows], ["1.8.1"])

    def test_oneline_still_exposes_xp_to_the_ci_regex(self):
        # .github/workflows/test.yml scrapes the base XP out of this line with
        # grep -oE '\(([0-9]+)'. Appending the service suffix must not break it.
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            g.main(["--oneline"])
        line = buf.getvalue().strip()
        m = re.search(r"\((\d+)", line)
        self.assertIsNotNone(m, f"CI regex would find no XP in: {line}")
        self.assertEqual(int(m.group(1)), self.r["xp"])
        self.assertIn("Service", line)


class Prestige(unittest.TestCase):
    """Grand Complication is a count of modules past XP100, never a sum of XP."""

    def mods(self, *xps):
        return [dict(xp=x) for x in xps]

    def banner(self, counted, xp100=13000):
        """The --oneline banner for a synthetic ledger."""
        import contextlib, io as _io
        from unittest import mock
        xp = sum(m["xp"] for m in counted)
        r = dict(xp=xp, xp100=xp100, level=g.level_for(xp, xp100),
                 tiers={}, prestige=g.prestige_for(counted, xp100),
                 counted=counted, planned=[], missing=[],
                 service=[], service_pts=0, service_unledgered=[])
        buf = _io.StringIO()
        with mock.patch.object(g, "compute", return_value=r):
            with contextlib.redirect_stdout(buf):
                g.main(["--oneline"])
        return buf.getvalue().strip()

    def test_nothing_past_the_line_below_design_complete(self):
        self.assertEqual(g.prestige_for(self.mods(500, 500), 13000), 0)

    def test_the_crossing_module_earns_no_prestige(self):
        # 12900 before it, +500 = 13400. Over the line, but no module begins
        # past it: this is design-complete, not prestige.
        c = self.mods(*([1000] * 12), 900, 500)
        self.assertEqual(sum(m["xp"] for m in c), 13400)
        self.assertEqual(g.prestige_for(c, 13000), 0)

    def test_counts_modules_not_thousands_of_xp(self):
        # Two 250s wholly past the line is +2. The rule this replaced --
        # round((xp - xp100) / 1000) -- scored it 0. That drift is the bug.
        c = self.mods(*([1000] * 13), 250, 250)
        self.assertEqual(g.prestige_for(c, 13000), 2)
        self.assertEqual(round((sum(m["xp"] for m in c) - 13000) / 1000), 0)

    def test_design_complete_prints_level_100(self):
        # The readout the whole scale is anchored to must be reachable.
        line = self.banner(self.mods(*([1000] * 12), 900, 500))
        self.assertIn("Level 100", line)
        self.assertNotIn("Grand Complication", line)

    def test_plus_zero_is_never_printed(self):
        # Sweep the crossing region: every banner is either a Level or a +N
        # with N >= 1. `Grand Complication +0` must not be reachable at all.
        for extra in range(0, 2000, 50):
            c = self.mods(*([1000] * 12), 900, extra) if extra else self.mods(*([1000] * 12), 900)
            line = self.banner(c)
            self.assertNotIn("+0", line, f"printed +0 for {sum(m['xp'] for m in c)} XP")
            if "Grand Complication" in line:
                n = int(re.search(r"\+(\d+)", line).group(1))
                self.assertGreaterEqual(n, 1)

    def test_prestige_banner_still_exposes_xp_to_the_ci_regex(self):
        # test.yml scrapes the base XP with grep -oE '\(([0-9]+)'. It must keep
        # working on the prestige branch too, not just the level branch.
        c = self.mods(*([1000] * 13), 250, 250)
        line = self.banner(c)
        self.assertIn("Grand Complication +2", line)
        self.assertEqual(int(re.search(r"\((\d+)", line).group(1)), 13500)

    def test_live_ledger_agrees_with_the_readout(self):
        r = g.compute()
        self.assertEqual(r["prestige"], g.prestige_for(r["counted"], r["xp100"]))
        if r["prestige"]:
            self.assertEqual(r["level"], 100, "prestige without design-complete")


if __name__ == "__main__":
    unittest.main()
