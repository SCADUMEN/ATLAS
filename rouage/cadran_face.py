"""LE CADRAN, as a face. A fifth display surface.

cadran_ascii.py reads a routing trace out as a table. This draws the same trace
as the object itself: a round dial in character cells, the twelve seats on the
chapter ring, the hands pointing where the train says they point. It is the
terminal's answer to dial.py's SVG, at the measure of the boot masthead.

It is bound by the same rule as every other Cadran surface, from
hardware/le-boitier.md - The Honesty Constraint:

    The display never shows a state the router did not produce.

So the plate prints every numeral, because naming a seat is the plate's job,
and the glyph beside each numeral comes only from the trace, because lighting
it is the train's. Anything the train does not drive is named UNDRIVEN below
the dial rather than drawn as though it were running.

The geometry borrows from premiere_lueur.py rather than restating it: the same
cell ASPECT, so a circle comes out round, and the same dwidth(), so the frame
stays square against what a terminal actually shows. The glyphs and colours are
cadran_ascii.py's, so a state reads the same on both character surfaces.

    python3 rouage/cadran_ascii.py "run Publish" --face
"""

from __future__ import annotations

import math
import textwrap

from cadran_ascii import COLOR, FAULT_COLOR, MARKER, RESET
from dial import load_anatomy, owner_of
from premiere_lueur import ASPECT, WIDTH, dwidth
from rouage import Ring, Trace, load_ring

INNER = WIDTH - 4

# Column radius of the bezel. 24 leaves room inside a 60-column frame for the
# crown to sit outside the case at three o'clock, and gives 25 rows - a dial
# that fits on one screen with its bands beneath it.
RADIUS = 24

# Where things sit, as a fraction of the bezel radius. Seats on the chapter
# ring, hands short of it so a tip never lands on a numeral.
SEAT_RING = 0.76
HOUR_REACH = 0.46
MINUTE_REACH = 0.60

# Hand colours, from dial.py's SVG: hour cyan, minute white. The split hand is
# where the route was aimed, drawn dashed and dim, as the SVG draws it.
HOUR_COLOR = "\033[38;5;51m"
MINUTE_COLOR = "\033[38;5;255m"
SPLIT_COLOR = "\033[38;5;101m"
BEZEL_COLOR = "\033[38;5;136m"

# The point of every hand. Must never be a state glyph from cadran_ascii.MARKER:
# a hand's tip lands beside a seat, and a tip that looked like a marker would
# read as that seat's state.
HAND_TIP = "•"


def seat_angle(position: str) -> float:
    """Clockwise degrees from twelve o'clock. Seat 12 is at the top, 03 at the
    right - the same layout dial.py engraves its batons at."""
    return (int(position) % 12) * 30.0


def hand_glyph(angle: float, tip: bool = False) -> str:
    """The character for one cell of a hand pointing at `angle` degrees
    clockwise from twelve o'clock - one of 0, 30, 60 ... 330.

    A hand is drawn as a run of these from the pivot outward. Every cell but
    the last is called with tip=False and draws the shaft; the outermost cell
    is called with tip=True and draws the point. This one choice decides
    whether a hand reads as a hand.

    The angle on screen is the true angle: cell_at() already corrects for a
    cell being twice as tall as it is wide.
    """
    # The Operator's choice, from four rendered candidates: plain ASCII
    # diagonals, so every slanted hand reads as slanted and the face looks the
    # same in every font, with a lume dot at the point.
    if tip:
        return HAND_TIP
    folded = angle % 180  # a hand to 01 and a hand to 07 are the same line
    if folded == 0:
        return "|"
    if folded == 90:
        return "-"
    return "/" if folded < 90 else "\\"


class _Canvas:
    """A grid of cells, each a character and an optional colour. Colour is
    kept beside the character, never inside it, so padding is computed on the
    plain text and escapes can never shift the frame."""

    def __init__(self, rows: int, cols: int):
        self.rows, self.cols = rows, cols
        self.cells = [[(" ", "") for _ in range(cols)] for _ in range(rows)]
        self.locked = [[False] * cols for _ in range(rows)]

    def put(self, r: int, c: int, ch: str, code: str = "", *,
            lock: bool = False, force: bool = False) -> None:
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.locked[r][c] and not force:
            return
        self.cells[r][c] = (ch, code)
        if lock:
            self.locked[r][c] = True

    def text(self, r: int, c: int, s: str, code: str = "") -> None:
        """Locked text: hands are drawn after and pass behind it."""
        for i, ch in enumerate(s):
            self.put(r, c + i, ch, code, lock=True, force=True)

    def centred(self, r: int, s: str, code: str = "") -> None:
        self.text(r, (self.cols - len(s)) // 2, s, code)

    def row(self, r: int, color: bool) -> tuple[str, str]:
        plain = "".join(ch for ch, _ in self.cells[r]).rstrip()
        if not color:
            return plain, plain
        # One escape per run of a colour, not per cell. A bezel row is mostly
        # one brass run; painting cell by cell made it hundreds of bytes of
        # escapes for a few dozen characters.
        out, run, run_code = [], [], ""

        def flush() -> None:
            if run:
                text = "".join(run)
                out.append(f"{run_code}{text}{RESET}" if run_code else text)
                run.clear()

        for ch, code in self.cells[r][:len(plain)]:
            code = code if ch != " " else ""
            if code != run_code:
                flush()
                run_code = code
            run.append(ch)
        flush()
        return plain, "".join(out)


def _framed(plain: str, painted: str) -> str:
    pad = INNER - dwidth(plain)
    if pad < 0:
        raise ValueError(f"row is {dwidth(plain)} columns, over {INNER}: {plain!r}")
    return f"│ {painted}{' ' * pad} │"


def face(trace: Trace, anatomy: dict | None = None, ring: Ring | None = None,
         *, color: bool = False) -> str:
    """The dial under one routing trace. Every lit cell traces to the Trace."""
    if anatomy is None:
        anatomy = load_anatomy()
    if ring is None:
        ring = load_ring()

    d = trace.to_dict()
    seat = {p["position"]: p for p in d["positions"]}

    def state_of(pos: str) -> str:
        return seat[pos]["state"] if pos in seat else "dark"

    def paint(state: str) -> str:
        return COLOR[state] if color else ""

    half = int(round(RADIUS * ASPECT))
    rows = 2 * half + 1
    cv = _Canvas(rows, INNER)
    cr, cc = half, INNER // 2

    def cell_at(angle: float, reach: float) -> tuple[int, int]:
        a = math.radians(angle)
        return (int(round(cr - reach * half * math.cos(a))),
                int(round(cc + reach * RADIUS * math.sin(a))))

    # --- the case: one cell of outline, wherever inside meets outside -------
    # Normalised on half + 0.5, as premiere_lueur.sphere() is, so the poles
    # are a short flat run of cells rather than one cell with a notch under it.
    def inside(r: int, c: int) -> bool:
        x = (c - cc) / (RADIUS + 0.5)
        y = (r - cr) / (half + 0.5)
        return x * x + y * y <= 1.0

    bezel = BEZEL_COLOR if color else ""
    for r in range(rows):
        for c in range(INNER):
            if inside(r, c) and not all(inside(r + dr, c + dc)
                                        for dr, dc in ((1, 0), (-1, 0),
                                                       (0, 1), (0, -1))):
                cv.put(r, c, "░", bezel)
    # Major markers at the twelve seats, and the bezel's pip at twelve. The pip
    # is engraved, not lit: the bezel is Le Sauvegarder's, and it turns one way.
    for h in range(12):
        r, c = cell_at(h * 30.0, 1.0)
        # Snap onto the outline rather than trusting rounding to land on it.
        while 0 <= r < rows and not inside(r, c):
            r += 1 if r < cr else -1
        cv.put(r, c, "▲" if h == 0 else "▓", bezel, lock=True, force=True)

    # --- the crown, outside the case at three o'clock -----------------------
    cstate = state_of("crown")
    cv.text(cr, cc + RADIUS + 1, "═")
    cv.text(cr, cc + RADIUS + 2, MARKER[cstate], paint(cstate))

    # --- the twelve seats ---------------------------------------------------
    for m in ring.hours:
        st = state_of(m.position)
        r, c = cell_at(seat_angle(m.position), SEAT_RING)
        label = m.position
        start = c - 1
        cv.text(r, start, label)
        cv.text(r, start + len(label), MARKER[st], paint(st))

    # --- plate engravings and the two bands ---------------------------------
    # Rows chosen to clear the seats: 04 and 08 sit at cr+5 but wide of
    # centre, 05 and 07 at cr+8, so the bands live between them.
    cv.centred(cr + 3, owner_of(anatomy, "dial plate"))
    held = len(trace.halted)
    if held:
        cv.centred(cr + 5, f"{owner_of(anatomy, 'brake')} · {held} HELD",
                   paint("dissent"))
    released = any(s.startswith("RELEASE") for s in d["stages"])
    band = "FAULT" if d["failures"] else "RELEASED" if released else "NO RELEASE"
    cv.centred(cr + 6, f"{owner_of(anatomy, 'escapement')} · {band}",
               FAULT_COLOR if color and d["failures"] else "")

    # --- the hands, read exactly as cadran_ascii.py reads them ---------------
    hour = d["admitted"][0] if d["admitted"] else None
    minute = d["route_end"]
    split = d["route_aimed"] if d["route_aimed"] != d["route_end"] else None

    def draw_hand(pos: str | None, reach: float, code: str,
                  dashed: bool = False) -> None:
        if not pos or not pos.isdigit():
            return
        angle = seat_angle(pos)
        # Walk the ray first, draw second: the tip is the outermost cell the
        # hand reaches, and that is only known once the walk has finished.
        path: list[tuple[int, int]] = []
        steps = 40
        for i in range(2, steps + 1):
            cell = cell_at(angle, reach * i / steps)
            if cell not in path and cell != (cr, cc):
                path.append(cell)
        for n, (r, c) in enumerate(path):
            tip = n == len(path) - 1
            # A dashed hand skips alternate shaft cells but always keeps its
            # tip - a split hand without a point would not say where it aimed.
            if dashed and not tip and n % 2 == 1:
                continue
            cv.put(r, c, hand_glyph(angle, tip=tip), code if color else "")

    # Drawn longest first so the hour hand, the shorter, sits on top where
    # the two share a seat - which is how a real movement stacks them.
    draw_hand(split, MINUTE_REACH, SPLIT_COLOR, dashed=True)
    draw_hand(minute, MINUTE_REACH, MINUTE_COLOR)
    draw_hand(hour, HOUR_REACH, HOUR_COLOR)
    cv.text(cr, cc, "◉")

    # --- assemble -----------------------------------------------------------
    title = "LE CADRAN · face"
    o = [f"┌─ {title} " + "─" * max(WIDTH - len(title) - 5, 1) + "┐"]
    o += [_framed(*cv.row(r, color)) for r in range(rows)]
    o.append(_framed("", ""))

    def hand_name(pos: str | None) -> str:
        if not pos:
            return "—"
        return f"{pos} {seat.get(pos, {}).get('name', '')}".strip()

    lit = [f"{MARKER[state_of(m.position)]} {m.position} {m.name}"
           for m in sorted(ring.hours, key=lambda m: m.position)
           if state_of(m.position) != "dark"]
    if cstate != "dark":
        lit.append(f"{MARKER[cstate]} crown")
    # Each entry is held together with no-break spaces while wrapping, so a
    # line never ends on "Le" and leaves the name to the next one.
    nbsp = "\u00a0"
    seats = "  ".join(e.replace(" ", nbsp) for e in lit) or "none lit"
    footer = [
        *(ln.replace(nbsp, " ") for ln in
          textwrap.wrap("SEATS  " + seats, INNER, subsequent_indent=" " * 7)),
        f"HANDS  hour → {hand_name(hour)}   minute → {hand_name(minute)}",
    ]
    if split:
        footer.append(f"       split → {hand_name(split)} (aimed)")
    footer.append("UNDRIVEN  registers · up-and-down · calendar")
    o += [_framed(ln, ln) for ln in footer]
    o.append("└" + "─" * (WIDTH - 2) + "┘")
    o.append(f' INPUT  "{d["utterance"]}"   armed {d["armed"] or "—"}')
    return "\n".join(o)
