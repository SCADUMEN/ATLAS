"""Guards for the boot masthead.

premiere_lueur.py has no trace to be honest about, so the failures that stalk
the Cadran do not apply here. Two different ones do.

The first is the frame coming apart. A panel padded on the wrong measure looks
correct until a glyph of a different width lands in it, and then every row below
is ragged. cadran_ascii.py pads with str.ljust() and its rows measure 68 to 78
where the frame intends 64; that is the bug this surface is built not to have,
so the width guard here is the one test that must never be relaxed.

The second is the drawing quietly degrading. The globe and the figure each took
several passes to become legible, and both failure modes were subtle: a
graticule that punched holes through the sphere, and a body that read as an
abstract mass. Neither would raise an error. So the anatomy and the sphere's
solidity are asserted, to make a regression loud.
"""

from __future__ import annotations

import os
import re
import unittest

from premiere_lueur import (
    INNER,
    MOTTO,
    RAMP,
    TITLE,
    WIDTH,
    dwidth,
    premiere_lueur,
    sphere,
)


class TheFrameIsSquare(unittest.TestCase):
    """The guard cadran_ascii.py does not hold. Everything else here is
    cosmetic by comparison: a reader forgives a plain globe, not a torn box."""

    def setUp(self):
        self.rows = premiere_lueur().splitlines()

    def test_every_row_is_exactly_the_frame_width_in_display_columns(self):
        # Display columns, not len(). The two agree only while every glyph is
        # narrow, and agreeing by luck is not the property under test.
        ragged = [(i, dwidth(r)) for i, r in enumerate(self.rows)
                  if dwidth(r) != WIDTH]
        self.assertEqual(ragged, [], f"rows off the frame width: {ragged}")

    def test_the_border_closes_on_all_four_corners(self):
        self.assertTrue(self.rows[0].startswith("┌─"))
        self.assertTrue(self.rows[0].endswith("┐"))
        self.assertTrue(self.rows[-1].startswith("└"))
        self.assertTrue(self.rows[-1].endswith("┘"))
        for row in self.rows[1:-1]:
            self.assertTrue(row.startswith("│") and row.endswith("│"),
                            f"content row lost a border: {row!r}")

    def test_the_title_is_engraved_in_the_top_rule(self):
        self.assertIn(TITLE, self.rows[0])


class TheGlobeIsSolid(unittest.TestCase):
    """A globe with holes in it is the graticule's one failure mode, and it is
    silent: stepping the engraved line below the ramp's first character writes
    a space, which reads as a puncture rather than as a meridian."""

    def test_no_interior_cell_is_blank(self):
        for row in sphere():
            body = row.strip()
            self.assertNotIn(" ", body,
                             f"the graticule punched through the globe: {row!r}")

    def test_the_lower_limb_still_carries_ink(self):
        # The ambient floor exists so the unlit underside reads as resting on
        # the figure. If shading ever drops it, the globe dissolves.
        rows = sphere()
        self.assertTrue(rows[-1].strip(), "the globe's last row is empty")
        self.assertTrue(set(rows[-1].strip()) <= set(RAMP[1:]))

    def test_the_globe_is_round_not_elliptical(self):
        # Cells are about twice as tall as wide, so a correct sphere is about
        # twice as wide in columns as it is tall in rows. Without the aspect
        # correction this ratio collapses toward 1 and the globe goes oblate.
        rows = sphere()
        span = max(dwidth(r) for r in rows)
        ratio = span / len(rows)
        self.assertGreater(ratio, 1.6, f"globe is squat: ratio {ratio:.2f}")
        self.assertLess(ratio, 2.4, f"globe is stretched: ratio {ratio:.2f}")


class TheFigureReadsAsABody(unittest.TestCase):
    """Line art beat block shading here only because each mark is legible as
    anatomy. These assert the marks that carry that reading, so a well-meant
    tidy cannot quietly turn the bearer back into a blob."""

    def setUp(self):
        self.panel = premiere_lueur()

    def test_the_head_is_an_explicit_token(self):
        # A head the viewer has to infer is a head the viewer does not find.
        head = [r for r in self.panel.splitlines() if " o " in r]
        self.assertEqual(len(head), 1, "the figure's head is missing or doubled")

    def test_the_torso_is_present(self):
        self.assertIn("/|\\", self.panel)

    def test_the_stance_is_asymmetric(self):
        # Symmetry is what made every earlier attempt read as a shape rather
        # than a person: a kneel has one leg down and one extended.
        legs = next(r for r in self.panel.splitlines() if "|  |  \\" in r)
        self.assertIn("|  |  \\", legs)

    def test_the_arms_rise_toward_the_globe(self):
        self.assertIn("\\             /", self.panel)


class TheMottoIsSeatedInTheFrame(unittest.TestCase):

    def test_the_motto_appears_once_inside_the_border(self):
        rows = [r for r in premiere_lueur().splitlines() if MOTTO in r]
        self.assertEqual(len(rows), 1, "the motto is missing or repeated")
        self.assertTrue(rows[0].startswith("│") and rows[0].endswith("│"))

    def test_the_motto_fits_the_inner_width(self):
        # 58 columns against 60. Tight enough that a single added word would
        # break the frame, so the margin is asserted rather than assumed.
        self.assertLessEqual(dwidth(MOTTO), INNER)


class TheMastheadIsFixed(unittest.TestCase):
    """An engraving, not a readout. It carries no state, so it has no reason
    to differ between two boots."""

    def test_two_renders_are_identical(self):
        self.assertEqual(premiere_lueur(), premiere_lueur())


class TheRiteCarriesTheSamePanel(unittest.TestCase):
    """The panel lives twice: drawn here, and written into the rite text that
    the model reproduces. Two copies of anything drift, and this pair would
    drift silently - a stale rite still renders, just wrong. So the copy is
    checked against the renderer rather than trusted.

    The launcher cannot print the masthead: Claude Code takes the alternate
    screen buffer on startup and wipes anything already on it. Reproducing the
    panel in the rite is what puts it in the transcript, where it survives.
    """

    def setUp(self):
        here = os.path.dirname(os.path.abspath(__file__))
        coda = os.path.join(here, os.pardir, "runtime", "compact-coda.md")
        with open(coda, encoding="utf-8") as handle:
            self.coda = handle.read()

    def test_the_rite_text_holds_the_canonical_panel(self):
        fence = re.search(r"```text\n(.*?)\n```", self.coda, re.S)
        self.assertIsNotNone(fence, "the rite's text fence is gone")
        canonical = premiere_lueur().splitlines()
        embedded = fence.group(1).splitlines()[:len(canonical)]
        self.assertEqual(embedded, canonical,
                         "the rite's panel has drifted from the renderer; "
                         "repaste `python3 rouage/premiere_lueur.py`")

    def test_the_rite_does_not_also_carry_the_old_text_masthead(self):
        # The panel is titled and carries the motto, so the plain heading and
        # the bare motto line it replaced must not creep back alongside it.
        self.assertNotIn("—— FIRST LIGHT ——", self.coda)
        self.assertEqual(self.coda.count(MOTTO), 1,
                         "the motto appears outside the panel")


if __name__ == "__main__":
    unittest.main()
