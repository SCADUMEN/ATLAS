"""LA PREMIÈRE LUEUR, the boot masthead. A fourth display surface.

Renders the Arrival rite's masthead as a framed terminal panel: a shaded globe
borne by a kneeling figure, over the motto. Nothing else.

This is cadran_ascii.py's cousin rather than its sibling. The Cadran displays a
routing trace and is bound by The Honesty Constraint - the display never shows a
state the router did not produce. This surface displays no state at all. It is
an engraving, fixed at every boot, and it must not grow a field that claims to
report anything. If it ever needs to say what the movement is doing, that is the
Cadran's work, not this one's.

The rite carries the panel and the model reproduces it. The launcher cannot:
Claude Code takes the alternate screen buffer when it starts and wipes anything
already printed, so a masthead written before the interface flashes once and is
gone. Reproduced in the rite, it lands in the transcript and scrolls back.

That means the panel exists twice - drawn here, and written into the rite text
in runtime/compact-coda.md. This module is the canonical copy. When the drawing
changes, reprint it and repaste the fence; test_premiere_lueur.py fails if the
two ever disagree.

    python3 rouage/premiere_lueur.py

Two things about the drawing are load-bearing, and both were found the hard way.

The globe is sampled from a true circle and mapped onto cells with an aspect
correction, because a terminal cell is about twice as tall as it is wide and a
naively drawn circle comes out an ellipse. Its shading keeps an ambient floor so
the lower limb still carries ink; a globe that fades to nothing at the bottom
reads as dissolving rather than as resting on the figure beneath it.

The figure is line art, not blocks. Block-shaded bodies were tried in front,
three-quarter and profile views, heavy and light, and every one read as an
abstract mass at this scale. Line art reads as anatomy: `o` is unmistakably a
head, `/|\\` a torso, and legs that differ left from right are a kneel. The
world is a rendered mass; the bearer is a drawn figure. That split is the
design, not an inconsistency.
"""

from __future__ import annotations

import math
import unicodedata

# The Cadran's frame, restated at the same measure so the two panels read as one
# instrument. Four columns of the width go to the border and its padding.
WIDTH = 64
INNER = WIDTH - 4

# Dark to light. Five steps is enough to carry a sphere and few enough that each
# step is distinct on a terminal that renders the blocks at slightly different
# weights.
RAMP = " ░▒▓█"

# How much light reaches the unlit side. Well off zero on purpose - see the
# module docstring on the lower limb.
AMBIENT = 0.34

# Column radius of the globe. Ten fits the figure, the motto and the frame into
# a panel that does not scroll on an 80x24 terminal.
RADIUS = 10

# Light direction, from the upper left and slightly toward the viewer.
LIGHT = (-0.5, -0.6, 0.62)

# A terminal cell is about twice as tall as it is wide.
ASPECT = 0.5

MOTTO = "HUMAN JUDGEMENT // MACHINE COLLABORATION // CONTRE L'OUBLI"

TITLE = "FIRST LIGHT"

# Arms rise to the globe, head between the shoulders, one knee down. Kept as a
# constant rather than generated: every cell here was chosen, and a generator
# would only invite someone to tune it back into a blob.
FIGURE = (
    r"  \             /  ",
    r"   \    ___    /   ",
    r"    \  /   \  /    ",
    r"     \/  o  \/     ",
    r"         /|\       ",
    r"        / | \      ",
    r"       |  |  \     ",
    r"    ___|  |   \___ ",
)


def dwidth(text: str) -> int:
    """Display columns, not code points.

    cadran_ascii.py pads with str.ljust(), which counts code points. That holds
    for its own glyphs, all of which are narrow, but it is not the same measure
    and it does not survive a wide glyph. The frame here is guaranteed square
    against anything the drawing might later contain, so the padding is
    computed from what a terminal will actually show.
    """
    columns = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        columns += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return columns


def sphere(radius: int = RADIUS, ramp: str = RAMP, *,
           graticule: bool = True, ambient: float = AMBIENT) -> list[str]:
    """A lit sphere in character cells, radius given in columns.

    Rows are derived from the radius through ASPECT so the result is visually
    round, and the count is forced odd so there is a true centre row for the
    equator to sit on.
    """
    rows = int(round(radius * ASPECT * 2))
    if rows % 2 == 0:
        rows += 1
    half = rows // 2

    lx, ly, lz = LIGHT
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / norm, ly / norm, lz / norm

    last = len(ramp) - 1
    out = []
    for row in range(-half, half + 1):
        y = row / (half + 0.5)
        cells = []
        for col in range(-radius, radius + 1):
            x = col / (radius + 0.5)
            d2 = x * x + y * y
            if d2 > 1.0:
                cells.append(" ")
                continue

            z = math.sqrt(max(0.0, 1.0 - d2))
            lambert = max(0.0, x * lx + y * ly + z * lz)
            value = ambient + (1.0 - ambient) * lambert
            index = int(round(value * last))
            char = ramp[min(last, max(0, index))]

            if graticule and d2 < 0.90:
                # Latitude and longitude on the true sphere surface. The rim is
                # left alone: a meridian crossing the limb reads as a nick in
                # the silhouette rather than as a line on a globe.
                lat = math.asin(max(-1.0, min(1.0, y)))
                lon = math.atan2(x, z)
                on_lat = abs((lat / (math.pi / 6)) % 1.0 - 0.5) > 0.44
                on_lon = abs((lon / (math.pi / 6)) % 1.0 - 0.5) > 0.46
                if on_lat or on_lon:
                    # Engrave one step darker than the surroundings, floored at
                    # index 1. Stepping to ramp[0] - a space - would punch a
                    # hole clean through the globe.
                    char = ramp[max(1, min(last, index - 1))]

            cells.append(char)
        out.append("".join(cells).rstrip())
    return out


def _centre(rows, width: int = INNER) -> list[str]:
    """Centre a block as a whole, not row by row.

    Row-by-row centring would straighten the globe's own lighting asymmetry
    into a wobble, and would pull the figure's kneeling stance upright.
    """
    span = max(dwidth(row) for row in rows)
    pad = " " * ((width - span) // 2)
    return [pad + row for row in rows]


def _line(content: str, inner: int = INNER) -> str:
    """One framed row, padded on display width so the right border stays put."""
    pad = inner - dwidth(content)
    if pad < 0:
        raise ValueError(
            f"row is {dwidth(content)} columns, over {inner}: {content!r}")
    return f"│ {content}{' ' * pad} │"


def panel(title: str, art: list[str], footer: list[str] | None = None) -> str:
    """The Cadran's frame: a titled rule, the content, an optional footer."""
    fill = WIDTH - dwidth(title) - 5
    out = [f"┌─ {title} " + "─" * max(fill, 1) + "┐"]
    out += [_line(row.rstrip()) for row in art]
    if footer:
        out.append(_line(""))
        out += [_line(row) for row in footer]
    out.append("└" + "─" * (WIDTH - 2) + "┘")
    return "\n".join(out)


def premiere_lueur() -> str:
    """The finished masthead. Same string every call."""
    art = [""] + _centre(sphere()) + _centre(FIGURE)
    return panel(TITLE, art, footer=[MOTTO.center(INNER)])


def main() -> None:
    print(premiere_lueur())


if __name__ == "__main__":
    main()
