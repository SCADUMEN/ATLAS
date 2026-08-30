"""Invariants for the ledger guard. Run: python3 -m unittest discover level -v

The detectors are tested against synthetic ledgers, not the repo's own, so these
stay true while `overlays/le-niveau.md` changes. The assertion about the real
ledger is at the bottom and is deliberately not enabled yet — turning it on is
the same decision as writing `verdict()`.
"""

import os
import tempfile
import unittest

import ledger_guard as lg
from level import parse_ledger, parse_tiers

TIERS = """
## Tiers

| Tier | XP | Meaning |
|---|---|---|
| S | 1000 | . |
| A | 500 | . |
| B | 250 | . |
| C | 100 | . |
| D | 50 | . |
"""

def ledger(*rows):
    """Build a doctrine fragment: rows are (id, tier, status, path) tuples."""
    body = "\n".join(f"| {i} | {i} | test | {t} | {s} | {p} |" for i, t, s, p in rows)
    return TIERS + "\n## The Module Ledger\n\n| ID | Module | Category | Tier | Status | Path |\n|---|---|---|---|---|---|\n" + body + "\n"


def ids(dups):
    """duplicates() yields rows; these tests only care which ids collided."""
    return [(path, [m["id"] for m in rows]) for path, rows in dups]


class Duplicates(unittest.TestCase):
    def test_none_when_every_path_is_distinct(self):
        m = parse_ledger(ledger(("a", "B", "built", "x.md"),
                                ("b", "B", "built", "y.md")))
        self.assertEqual(lg.duplicates(m), [])

    def test_flags_two_rows_on_one_path(self):
        m = parse_ledger(ledger(("a", "B", "built", "x.md"),
                                ("b", "S", "planned", "x.md")))
        self.assertEqual(ids(lg.duplicates(m)), [("x.md", ["a", "b"])])

    def test_reports_all_ids_on_a_path_and_keeps_ledger_order(self):
        m = parse_ledger(ledger(("a", "B", "built", "x.md"),
                                ("b", "B", "built", "y.md"),
                                ("c", "B", "built", "x.md"),
                                ("d", "B", "built", "y.md")))
        self.assertEqual(ids(lg.duplicates(m)), [("x.md", ["a", "c"]),
                                                 ("y.md", ["b", "d"])])


class Premature(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        open(os.path.join(self.repo, "here.md"), "w").close()

    def test_planned_row_with_no_file_is_clean(self):
        m = parse_ledger(ledger(("a", "S", "planned", "absent.md")))
        self.assertEqual(lg.premature(m, self.repo), [])

    def test_planned_row_whose_file_exists_is_flagged(self):
        m = parse_ledger(ledger(("a", "S", "planned", "here.md")))
        self.assertEqual([x["id"] for x in lg.premature(m, self.repo)], ["a"])

    def test_built_row_whose_file_exists_is_not_flagged(self):
        # A built row on a real path is the normal, correct case.
        m = parse_ledger(ledger(("a", "S", "built", "here.md")))
        self.assertEqual(lg.premature(m, self.repo), [])

    def test_a_directory_counts_as_existing(self):
        # rouage/ is a directory; os.path.exists must be the test, not isfile.
        os.mkdir(os.path.join(self.repo, "dir"))
        m = parse_ledger(ledger(("a", "S", "planned", "dir/")))
        self.assertEqual([x["id"] for x in lg.premature(m, self.repo)], ["a"])

    def test_unearned_xp_sums_only_the_premature_rows(self):
        md = ledger(("a", "S", "planned", "here.md"),
                    ("b", "A", "planned", "here.md"),
                    ("c", "S", "planned", "absent.md"),
                    ("d", "S", "built", "here.md"))
        m, t = parse_ledger(md), parse_tiers(md)
        self.assertEqual(lg.unearned_xp(lg.premature(m, self.repo), t), 1500)



class Policy(unittest.TestCase):
    """The two rules of verdict(), and the asymmetry between them."""

    def _v(self, md, repo):
        m, t = parse_ledger(md), parse_tiers(md)
        return lg.verdict(lg.duplicates(m), lg.premature(m, repo), t, m)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        open(os.path.join(self.repo, "here.md"), "w").close()

    def test_clean_ledger_passes(self):
        md = ledger(("a", "B", "built", "here.md"),
                    ("b", "S", "planned", "absent.md"))
        self.assertEqual(self._v(md, self.repo), [])

    def test_premature_row_blocks(self):
        md = ledger(("a", "S", "planned", "here.md"))
        self.assertEqual(len(self._v(md, self.repo)), 1)

    def test_spec_plus_planned_completion_is_tolerated(self):
        # The roadmap shape: one row counts, one waits. It cannot score twice.
        md = ledger(("a", "B", "built", "absent.md"),
                    ("b", "S", "planned", "absent.md"))
        self.assertEqual(self._v(md, self.repo), [])

    def test_two_counting_rows_on_one_path_block(self):
        md = ledger(("a", "B", "built", "absent.md"),
                    ("b", "S", "built", "absent.md"))
        self.assertEqual(len(self._v(md, self.repo)), 1)

    def test_partial_counts_as_a_counting_row(self):
        md = ledger(("a", "B", "partial", "absent.md"),
                    ("b", "S", "built", "absent.md"))
        self.assertEqual(len(self._v(md, self.repo)), 1)

    def test_three_rows_on_a_path_are_not_a_pair(self):
        md = ledger(("a", "B", "built", "absent.md"),
                    ("b", "S", "planned", "absent.md"),
                    ("c", "C", "planned", "absent.md"))
        self.assertEqual(len(self._v(md, self.repo)), 1)

    def test_a_tolerated_pair_still_blocks_once_its_file_appears(self):
        # The composition: tolerating the pair is only safe because premature
        # is strict. Same ledger, file now on disk -> the premature rule fires.
        md = ledger(("a", "B", "built", "here.md"),
                    ("b", "S", "planned", "here.md"))
        self.assertEqual(len(self._v(md, self.repo)), 1)

    def test_the_message_carries_the_magnitude(self):
        md = ledger(("a", "S", "planned", "here.md"))
        self.assertIn("1000 XP", self._v(md, self.repo)[0])


class RealLedger(unittest.TestCase):
    def test_findings_are_reportable_without_a_policy(self):
        # --list must work before verdict() exists, or the guard cannot be used
        # to inform the decision it is waiting on.
        self.assertEqual(lg.main(["--list"]), 0)

    def test_the_repo_ledger_passes_its_own_guard(self):
        self.assertEqual(lg.main([]), 0)


if __name__ == "__main__":
    unittest.main()
