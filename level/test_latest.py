"""Invariants for the update check. Run: python3 -m unittest discover level -v"""

import unittest

import latest as l


def refs(*versions):
    """Fake ls-remote output for the given atlas--v tags."""
    return "".join(
        f"0000000000000000000000000000000000000000\trefs/tags/atlas--v{v}\n"
        for v in versions
    )


class UpdateLine(unittest.TestCase):
    def test_newer_available(self):
        line = l.update_line("1.2.0", refs("1.3.0"))
        self.assertEqual(line, "UPDATE: v1.3.0 available — run /plugin to update")

    def test_up_to_date_is_silent(self):
        # Latest == installed: nothing to say.
        self.assertIsNone(l.update_line("1.2.0", refs("1.2.0")))

    def test_installed_ahead_is_silent(self):
        # A dev checkout can sit ahead of the newest published tag.
        self.assertIsNone(l.update_line("1.3.0", refs("1.2.0")))

    def test_picks_max_numerically_not_lexically(self):
        # 1.10.0 is newer than 1.2.0; a string compare would pick 1.2.0.
        line = l.update_line("1.2.0", refs("1.2.0", "1.10.0", "1.9.0"))
        self.assertEqual(line, "UPDATE: v1.10.0 available — run /plugin to update")

    def test_malformed_lines_ignored(self):
        noise = "not a ref\nrefs/heads/main\nrefs/tags/atlas--vX.Y.Z\n"
        self.assertIsNone(l.update_line("1.2.0", noise + refs("1.2.0")))

    def test_malformed_lines_do_not_hide_a_real_newer_tag(self):
        noise = "garbage\nrefs/tags/wrong-format\n"
        line = l.update_line("1.2.0", noise + refs("1.4.0"))
        self.assertEqual(line, "UPDATE: v1.4.0 available — run /plugin to update")

    def test_empty_input_is_silent(self):
        self.assertIsNone(l.update_line("1.2.0", ""))

    def test_unknown_current_version_is_silent(self):
        # Without a known installed version there is nothing to compare against.
        self.assertIsNone(l.update_line("", refs("9.9.9")))


class Parsing(unittest.TestCase):
    def test_parse_version_forms(self):
        for text in ("1.2.0", "v1.2.0", "atlas--v1.2.0", "refs/tags/atlas--v1.2.0"):
            self.assertEqual(l.parse_version(text), (1, 2, 0), text)

    def test_parse_version_rejects_garbage(self):
        for text in ("", "abc", "1.2", "v1"):
            self.assertIsNone(l.parse_version(text), text)

    def test_latest_from_tags_none_when_empty(self):
        self.assertIsNone(l.latest_from_tags([]))


if __name__ == "__main__":
    unittest.main()
