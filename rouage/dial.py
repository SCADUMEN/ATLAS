"""LE CADRAN - the dial. Diver's chronograph.

Renders a routing trace. Nothing else.

hardware/le-boitier.md: the display is driven by the routing trace 'never by a
demo loop, an idle animation, or a startup sequence that lights markers for
effect.' This module takes a Trace and returns SVG. It has no other input, so
there is nothing it could invent.

Anything the train does not yet drive is drawn UNDRIVEN and says so on its face:

  - The three registers are Le Sceptique's, from stage 7 (TIER), a person.
  - The up-and-down arc is the context window. The train does not measure it.
  - Consulted is a real state the train cannot yet emit. It has its own
    ink anyway, so the dial cannot mistranslate it the day it arrives.

Drawing any of those lit would make this a prop.

    python3 rouage/dial.py                       # specimen sheet
    python3 rouage/dial.py "what happened here"
    python3 rouage/dial.py "red team this" --arm "Le Fripon"

Legibility constraints are from le-boitier.md and are not styling: uniform
stroke weights, no hairlines, ground lifted off pure black. Halation is now
deliberate but bounded - see le-boitier.md for why that reversed.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

from rouage import CONSEIL, STATES, Trace, load_ring, load_routes, route

OUT = Path(__file__).resolve().parent / "cadran.html"

# The anatomy table in le-conseil.md, scoped by its header row. Unscoped, the
# 'Not an hour' table below it also matches and silently reassigns the crown.
ANATOMY_HEADER = re.compile(r"^\|\s*Part\s*\|\s*Council\s*\|.*$", re.M)
ANATOMY_ROW = re.compile(r"^\|\s*\*\*([^*|]+)\*\*\s*\|\s*([^|]+?)\s*\|", re.M)

# Chassis mechanism -> the part it stands for in the anatomy table.
#
# Deliberately empty. le-conseil.md is written for a diver's chronograph and
# this chassis IS one, so every mechanism answers to the name doctrine already
# gave it and nothing needs translating. The marine-chronometer draft needed
# two entries here - bezel->gimbal ring, crown->winding arbor - because a
# chronometer has neither a rotating bezel nor a crown. Those entries being
# gone is the argument for this form: the arguable step is the one that
# disappeared. The hook stays so a future chassis has somewhere to declare its
# substitutions rather than making them silently.
CHASSIS: dict[str, str] = {}

INK = {
    # Tokyo Night ground, CRT neon on top. Cyan, magenta, matrix green and
    # amber are the four lit hues; amber is FI's own and carries the states
    # that are held rather than running.
    "bg": "#0b0c12",
    "brass_hi": "#c9a86a",
    "brass_lo": "#6e5a30",
    "plate": "#14161f",
    "edge": "#2a2f42",
    "ink": "#e8ecff",
    "dim": "#ab9668",
    "cyan": "#35e6ff",
    "amber": "#d9a04a",     # bezel furniture, not a state

    "active": "#3dff9e",     # matrix green
    "sealed": "#ffb43d",     # amber
    "held": "#7d6f52",
    "dark": "#463a24",
    "consulted": "#e8f04a",  # highlighter yellow - weighed, not surfaced
    "dissent": "#ff4fd8",    # magenta
    # Red stays fault-only and never becomes a marker state. Fault is the one
    # signal that means the routing itself failed, and a colour that means
    # exactly one thing is worth more than a sixth marker hue. It also keeps
    # red off the chapter ring, where it would have to be told apart from
    # magenta at a glance - as a text band it never competes with dissent.
    "fault": "#ff5470",
}

# Every state rouage.STATES can emit needs an entry here. A missing one falls
# through to `dark`, which on this dial means "the gate did not fire" - so an
# unmapped state does not render as unknown, it renders as its own opposite.
# That is the display lying, which le-boitier.md calls the difference between
# a gauge and a prop.
STATE_INK = {
    "consulted": INK["consulted"],
    "active": INK["active"],
    "sealed": INK["sealed"],
    "held": INK["held"],
    "dissent": INK["dissent"],
    "dark": INK["dark"],
}

_UNMAPPED = set(STATES) - set(STATE_INK)
assert not _UNMAPPED, f"dial cannot render states the train emits: {_UNMAPPED}"


def polar(cx: float, cy: float, r: float, pos: str) -> tuple[float, float]:
    """Dial position -> point. 12 at top, clockwise, 30 degrees per hour.

    Fractional positions are allowed so that parts which are not hours can sit
    between them - '11.5' is the gap between 11 and 12.
    """
    hour = float(pos) % 12
    a = math.radians(-90 + hour * 30)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_anatomy(conseil: Path = CONSEIL) -> dict[str, str]:
    """Parse the anatomy table: part -> the council entity that owns it.

    Ownership is doctrine, so it is read from doctrine. Hardcoding this table
    would let the dial keep engraving an owner that le-conseil.md had already
    reassigned, which is the same drift the train avoids for the roster.
    """
    text = conseil.read_text(encoding="utf-8")
    header = ANATOMY_HEADER.search(text)
    if header is None:
        raise ValueError("le-conseil.md: anatomy table not found")

    block: list[str] = []
    for line in text[header.end():].splitlines():
        line = line.strip()
        if not line:                 # the newline the header match left behind
            continue
        if not line.startswith("|"):  # first prose line ends the table
            break
        block.append(line)

    return {part.strip().casefold(): owner.strip()
            for part, owner in ANATOMY_ROW.findall("\n".join(block))}


def owner_of(anatomy: dict[str, str], mechanism: str) -> str:
    """Engraving for one mechanism. Never invents; says so when doctrine is
    silent, because an unlabelled part and an unassigned part are not the
    same fact and the instrument must not conflate them."""
    part = CHASSIS.get(mechanism, mechanism)
    owner = anatomy.get(part)
    if owner is None:
        return "UNASSIGNED IN DOCTRINE"
    if owner.strip("—- ") == "":       # the hands: deliberately no one
        return "DELIBERATELY NO ONE"
    return owner.upper()


def dial_svg(trace: Trace, size: int = 820, detailed: bool = True,
             anatomy: dict[str, str] | None = None) -> str:
    """One chronograph. Every lit element traces to a field in `trace`.

    Mechanism ownership comes from `anatomy` (le-conseil.md). An engraving is
    not a drive signal: naming who owns a subdial says nothing about whether
    a needle may move in it, and the undriven ones stay undriven.
    """
    states = {p["position"]: p for p in trace.to_dict()["positions"]}
    unsealed = trace.armed is not None
    if anatomy is None and detailed:
        anatomy = load_anatomy()

    W = size
    H = int(size * 0.93)
    cx, cy = W / 2, size * 0.439

    r_case = size * 0.395        # outer edge of the rotating bezel
    r_bezel_in = size * 0.340    # where the bezel stops and the dial begins
    r_dial = size * 0.336
    r_chapter = size * 0.306
    r_baton = size * 0.032
    r_reserve = size * 0.258
    # Two label radii. The horizontal flanks are the tight axis - at 3 and 9
    # a name has to clear a register and still stop short of the dial edge -
    # so they sit closer in than 12 and 6, where the column is empty. The
    # bezel eats the outer band a chronometer left free, so both come in.
    # One radius, not two. The flanks used to sit 6px closer in than 12 and 6
    # to buy clearance, which meant the twelve names never actually formed a
    # ring - they formed two arcs that nearly matched, which reads as a
    # mistake rather than as a decision. A dial's text belongs on concentric
    # baselines; the clearance is bought with type size instead.
    r_label = size * 0.196
    r_label_v = r_label
    r_reg = size * 0.134
    rr = size * 0.042

    o: list[str] = []
    add = o.append
    add(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif">')

    add(f'''<defs>
      <linearGradient id="brass" x1="0" y1="0" x2="0.35" y2="1">
        <stop offset="0" stop-color="{INK['brass_hi']}"/>
        <stop offset="0.4" stop-color="{INK['brass_lo']}"/>
        <stop offset="0.7" stop-color="{INK['brass_hi']}"/>
        <stop offset="1" stop-color="{INK['brass_lo']}"/>
      </linearGradient>
      <radialGradient id="plate" cx="0.5" cy="0.36" r="0.78">
        <stop offset="0" stop-color="#1e2233"/>
        <stop offset="1" stop-color="{INK['plate']}"/>
      </radialGradient>
      <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
        <feGaussianBlur stdDeviation="2.1" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="glowsoft" x="-80%" y="-80%" width="260%" height="260%">
        <feGaussianBlur stdDeviation="1.0" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>''')

    # --- lugs -------------------------------------------------------------
    # A diver's watch is worn, so it has lugs. Drawn first, behind the case.
    for ang in (-135, -45, 45, 135):
        add(f'<g transform="rotate({ang} {cx:.1f} {cy:.1f})">'
            f'<rect x="{cx + r_case - 18:.1f}" y="{cy - 19:.1f}" '
            f'width="56" height="36" rx="12" fill="#2e271f" '
            f'stroke="#171310" stroke-width="3"/></g>')

    # --- the crown and the two pushers, on the right flank ----------------
    # le-boitier.md's control table: crown at 3, guarded pusher above it,
    # reset below. All three are chronograph parts, which is why that table
    # never quite fitted a chronometer - a chronometer has no pushers at all.
    #
    # The upper pusher is the only control that lights, and it lights from
    # trace.armed. That is the honest wiring: arming is Le Fripon's state,
    # not the crown's. The chronometer draft lit the winding arbor for it.
    def flank(ang: float, body: str) -> None:
        add(f'<g transform="rotate({ang} {cx:.1f} {cy:.1f})">{body}</g>')

    fripon_ink = INK["active"] if unsealed else INK["brass_lo"]
    flank(-30, (  # 02 - Le Fripon, guarded
        f'<rect x="{cx + r_case - 6:.1f}" y="{cy - 21:.1f}" width="30" '
        f'height="42" rx="5" fill="#2a2416" stroke="#3d3320" stroke-width="2"/>'
        f'<rect x="{cx + r_case + 2:.1f}" y="{cy - 11:.1f}" width="24" '
        f'height="22" rx="4" fill="{fripon_ink}"/>'))
    flank(30, (   # 04 - reset
        f'<rect x="{cx + r_case - 2:.1f}" y="{cy - 11:.1f}" width="26" '
        f'height="22" rx="4" fill="url(#brass)" stroke="#3d3320" '
        f'stroke-width="2"/>'))
    crown = [f'<rect x="{cx + r_case - 4:.1f}" y="{cy - 26:.1f}" width="36" '
             f'height="52" rx="6" fill="url(#brass)" stroke="#3d3320" '
             f'stroke-width="2.5"/>']
    for i in range(4):     # fluting, so it reads as a thing you grip
        fx = cx + r_case + 3 + i * 7.5
        crown.append(f'<line x1="{fx:.1f}" y1="{cy-20:.1f}" x2="{fx:.1f}" '
                     f'y2="{cy+20:.1f}" stroke="#3d3320" stroke-width="2"/>')
    flank(0, "".join(crown))

    # --- the case ---------------------------------------------------------
    add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_case:.1f}" fill="#241f1a" '
        f'stroke="url(#brass)" stroke-width="5"/>')

    # --- the rotating bezel: ATLAS ---------------------------------------
    # Unidirectional by construction. The teeth are the grip; the ratchet is
    # the doctrine. le-conseil.md: it can report only that less time remains
    # than you thought, never more. The train does not set it - L'Operateur
    # does, before going under - so it is drawn at its reference position.
    for i in range(72):    # coin edge
        a = math.radians(i * 5)
        add(f'<line x1="{cx + (r_case-1)*math.cos(a):.1f}" '
            f'y1="{cy + (r_case-1)*math.sin(a):.1f}" '
            f'x2="{cx + (r_case-9)*math.cos(a):.1f}" '
            f'y2="{cy + (r_case-9)*math.sin(a):.1f}" '
            f'stroke="#3d3320" stroke-width="3"/>')

    add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_bezel_in:.1f}" '
        f'fill="#0f1220" stroke="#3d3320" stroke-width="2"/>')

    # Bounded at each end. A scale that fades off into the plate at its inner
    # edge reads as unfinished; two rules turn it into a chapter ring, which
    # is what it is. Not hairlines - le-boitier.md rules those out.
    scale_out = r_case - 12
    scale_in = scale_out - 14
    for rr_ in (scale_out, scale_in):
        add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr_:.1f}" fill="none" '
            f'stroke="{INK["amber"]}" stroke-width="1.6" opacity="0.5"/>')

    for m in range(60):    # the 60-minute scale
        a = math.radians(-90 + m * 6)
        inner = scale_out - (14 if m % 5 == 0 else 8)
        add(f'<line x1="{cx + scale_out*math.cos(a):.1f}" '
            f'y1="{cy + scale_out*math.sin(a):.1f}" '
            f'x2="{cx + inner*math.cos(a):.1f}" '
            f'y2="{cy + inner*math.sin(a):.1f}" '
            f'stroke="{INK["amber"]}" stroke-width="{3.5 if m % 5 == 0 else 2}" '
            f'opacity="{0.95 if m % 5 == 0 else 0.6}"/>')

    if detailed:
        for m in (10, 20, 30, 40, 50):
            a = math.radians(-90 + m * 6)
            # Between the dial edge and the inner end of the tick marks. Any
            # further out and the dial circle, drawn after this, paints over
            # them - which is exactly what the first pass did.
            nr = r_case - 36
            add(f'<text x="{cx + nr*math.cos(a):.1f}" '
                f'y="{cy + nr*math.sin(a) + 5:.1f}" text-anchor="middle" '
                f'fill="{INK["amber"]}" font-size="15" font-weight="500" '
                f'opacity="0.95">{m}</text>')

    # The lume pip at zero. On a real bezel this is the only part that glows.
    add(f'<path d="M {cx:.1f} {cy - r_case + 8:.1f} '
        f'L {cx - 11:.1f} {cy - r_case + 26:.1f} '
        f'L {cx + 11:.1f} {cy - r_case + 26:.1f} Z" '
        f'fill="{INK["active"]}" opacity="0.95" filter="url(#glow)"/>')
    if detailed:
        # Must sit outside r_dial: the dial circle is drawn after this and
        # paints over anything inside it. The first pass put this at
        # r_case-52, which is inside the dial, and it vanished.
        add(f'<text x="{cx:.1f}" y="{cy - r_bezel_in - 7:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="10" '
            f'font-family="ui-monospace,monospace" letter-spacing="2">'
            f'&#9664; {esc(owner_of(anatomy, "bezel"))}</text>')

    add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_dial:.1f}" fill="url(#plate)" '
        f'stroke="{INK["edge"]}" stroke-width="3"/>')

    # --- up-and-down arc: the power reserve, 9 through 12 to 3 -----------
    # le-boitier.md specifies an arc, not a subdial. The train does not
    # measure the context window, so the arc is drawn as an empty track.
    add(f'<path d="M {cx-r_reserve:.1f} {cy:.1f} '
        f'A {r_reserve:.1f} {r_reserve:.1f} 0 0 1 {cx+r_reserve:.1f} {cy:.1f}" '
        f'fill="none" stroke="#232840" stroke-width="9" stroke-linecap="round"/>')
    if detailed:
        add(f'<text x="{cx:.1f}" y="{cy - r_reserve + 18:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="10" font-family="ui-monospace,monospace" '
            f'letter-spacing="2">UP &#183; DOWN</text>')
        add(f'<text x="{cx:.1f}" y="{cy - r_reserve + 31:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="9" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5">{esc(owner_of(anatomy, "barrel"))} '
            f'&#183; UNDRIVEN</text>')


    # --- chapter ring -----------------------------------------------------
    for hour in range(1, 13):
        pos = f"{hour:02d}"
        entry = states.get(pos)
        state = entry["state"] if entry else "dark"
        ink = STATE_INK.get(state, INK["dark"])
        lit = state != "dark"

        bxp, byp = polar(cx, cy, r_chapter, pos)
        axp, ayp = polar(cx, cy, r_chapter - r_baton, pos)
        width = 11 if lit else 8
        opacity = "1" if lit else "0.8"
        halo = ' filter="url(#glow)"' if lit else ''
        soft = ' filter="url(#glowsoft)"' if lit else ''
        add(f'<line x1="{bxp:.1f}" y1="{byp:.1f}" x2="{axp:.1f}" y2="{ayp:.1f}" '
            f'stroke="{ink}" stroke-width="{width}" stroke-linecap="round" '
            f'opacity="{opacity}"{halo}/>')

        if not detailed:
            continue

        # Labels on their own annulus, inside the batons and clear of the
        # registers. Each name is set AWAY from the centre: hours 1-5 are on
        # the right flank and run rightward, 7-11 on the left and run left.
        # Anchoring them the other way walks every name back across the
        # registers and the hand, which is what put Le Sceptique on the 12.
        lx, ly = polar(cx, cy, r_label if hour % 6 else r_label_v, pos)
        anchor = "middle"
        if 1 <= hour <= 5:
            anchor, lx = "start", lx + 8
        elif 7 <= hour <= 11:
            anchor, lx = "end", lx - 8
        # Already an entity, so it must not go through esc() - that turns the
        # ampersand into &amp; and prints "&#183;" on every dark position.
        name = esc(entry["name"]) if entry else "&#183;"
        tail = "  " + state.upper() if lit else ""
        add(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" fill="{ink}" '
            f'font-size="14.5" font-weight="500" '
            f'opacity="{1 if lit else 0.55}"{soft}>'
            f'{name}</text>')
        add(f'<text x="{lx:.1f}" y="{ly+15:.1f}" text-anchor="{anchor}" '
            f'fill="{INK["dim"]}" font-size="10.5" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5">{pos}{tail}</text>')

    # --- plate signature --------------------------------------------------
    if detailed:
        # Moved below centre. The 12 column is the date aperture's now, and the
        # registers leaving 6 freed the whole lower half - which is where a
        # signature and its certification sit on a real dial anyway.
        add(f'<text x="{cx:.1f}" y="{cy + size*0.144:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="12" font-family="ui-monospace,monospace" '
            f'letter-spacing="6">{esc(owner_of(anatomy, "dial plate"))}</text>')
        # The certification line, where a rated dial carries it. A chronometer
        # marking is not decoration: it attests the movement was tested against
        # a standard and its rate recorded. This one has a standard - the four
        # admission conditions in le-sas.md - but the trace carries no evidence
        # the movement was measured against it, so the dial declines the claim.
        # Same move as UNDRIVEN: state the thing you cannot show.
        #
        # 'DIAL PLATE' used to sit between these and has gone. The mechanism
        # list already says the plate is L'Archive, and with the calendar pair
        # flanking this column a fourth line made the dial's most crowded axis
        # unreadable. Signature then certification is how a rated dial reads.
        # Two short lines rather than one for the same reason: a single line
        # runs straight into the apertures' owner engravings.
        add(f'<text x="{cx:.1f}" y="{cy + size*0.144 + 15:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="8" font-family="ui-monospace,monospace" '
            f'letter-spacing="2" opacity="0.8">CHRONOMETER</text>')
        add(f'<text x="{cx:.1f}" y="{cy + size*0.144 + 26:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="8" font-family="ui-monospace,monospace" '
            f'letter-spacing="2">UNCERTIFIED</text>')
        # 'Rate recorded, never reset' left with the chronometer. It was that
        # chassis's honesty procedure; a diver's equivalent is the bezel's
        # one-way ratchet, which is structure rather than a printed sentence.
        # A dive dial earns its legibility by carrying less, not more.

    # --- registers: housings only, undriven ------------------------------
    # Names come from the anatomy row, not from this file. The driver is the
    # occupant of 01 - the register belongs to the position, and whoever
    # holds the position inherits it.
    # They cluster at the top right, beside 01, because 01 is what drives them.
    # Cardinal 3/6/9 was tri-compax convention and nothing more - it scattered
    # one member's readout across three corners of a dial whose other parts sit
    # with their owners. Smaller, and set along the tangent so the group reads
    # as one instrument rather than three unrelated subdials.
    if detailed:
        names = [n.strip().upper()
                 for n in owner_of(anatomy, "registers").split("·")]
        if len(names) != 3:                 # doctrine changed shape; say so
            names = ["UNREADABLE"] * 3
        driver = (states.get("01") or {}).get("name", "")
        drives = driver.upper() if driver else "FROM 01"

        # A triangle, not a row. Strung along the tangent they read as a
        # diagonal smear from 12 down to 3 rather than as one group in the
        # corner, which defeats the point of moving them beside 01.
        #
        # The driver is engraved once beneath the group, not inside all three.
        # At this size the owner's name is wider than a 54px housing, so three
        # copies overflowed their circles and ran into each other. One
        # engraving under a group that plainly belongs together says the same
        # thing and is legible, which le-boitier.md ranks first.
        gx, gy = polar(cx, cy, size * 0.141, "1.5")
        gr = size * 0.033
        trio = ((0.0, -size * 0.0366),
                (-size * 0.0366, size * 0.0195),
                (size * 0.0366, size * 0.0195))
        for label, (ox, oy) in zip(names, trio):
            rx, ry = gx + ox, gy + oy
            add(f'<circle cx="{rx:.1f}" cy="{ry:.1f}" r="{gr:.1f}" fill="#0e1120" '
                f'stroke="{INK["edge"]}" stroke-width="2.5"/>')
            add(f'<text x="{rx:.1f}" y="{ry-2:.1f}" text-anchor="middle" '
                f'fill="{INK["dim"]}" font-size="8.5" '
                f'font-family="ui-monospace,monospace" letter-spacing="1">'
                f'{esc(label)}</text>')
            add(f'<text x="{rx:.1f}" y="{ry+10:.1f}" text-anchor="middle" '
                f'fill="{INK["held"]}" font-size="7" '
                f'font-family="ui-monospace,monospace" letter-spacing="0.5">'
                f'UNDRIVEN</text>')
        add(f'<text x="{gx:.1f}" y="{gy + size*0.0195 + gr + 13:.1f}" '
            f'text-anchor="middle" fill="{INK["dim"]}" font-size="7.5" '
            f'font-family="ui-monospace,monospace" letter-spacing="1">'
            f'{esc(drives)}</text>')

    # --- perpetual calendar: subdial at 10:30, date aperture under 12 -----
    # The complication spans both its owners. The cycle dial sits at the top
    # left beside 11, which owns it; the date reads through an aperture on the
    # 12 column, and 12 is Le Redempteur - the hour that owns return after
    # collapse, which is exactly what a perpetual calendar needs once it has
    # stopped and lost its place. Nothing else on the dial has a failure mode
    # that lands on a different member from its owner.
    #
    # LEAP rather than MONTH on the dial: the four-year position is the whole
    # difference between a perpetual calendar and an annual one. Drop it and
    # the mechanism forgets, which is the one thing this instrument is named
    # against.
    #
    # Both undriven. The train emits no date, and a window showing nothing is
    # self-evidently undriven in a way a blank subdial is not.
    if detailed:
        owner = esc(owner_of(anatomy, "perpetual calendar"))

        kx, ky = polar(cx, cy, size * 0.138, "10.5")
        kr = size * 0.040
        add(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{kr:.1f}" fill="#0f1220" '
            f'stroke="{INK["edge"]}" stroke-width="2.5"/>')
        add(f'<text x="{kx:.1f}" y="{ky-11:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="9" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5">LEAP</text>')
        add(f'<text x="{kx:.1f}" y="{ky+1:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="7" font-family="ui-monospace,monospace" '
            f'letter-spacing="0.5" opacity="0.85">{owner}</text>')
        add(f'<text x="{kx:.1f}" y="{ky+13:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="7" font-family="ui-monospace,monospace" '
            f'letter-spacing="1">UNDRIVEN</text>')

        wx, wy = cx, cy - size * 0.048
        add(f'<text x="{wx:.1f}" y="{wy - 17:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="8" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5" opacity="0.85">DATE</text>')
        add(f'<rect x="{wx - 21:.1f}" y="{wy - 11:.1f}" width="42" height="22" '
            f'rx="3" fill="#0a0d18" stroke="{INK["edge"]}" stroke-width="2"/>')
        add(f'<text x="{wx:.1f}" y="{wy + 3.5:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="8" font-family="ui-monospace,monospace" '
            f'letter-spacing="1">UNDRIVEN</text>')

    # --- skeleton cutaway: la roue a colonnes ----------------------------
    # A cutaway is legal here for a reason that is not decorative. The honesty
    # rule governs LIT elements that claim to show state; a machined part that
    # indicates nothing is not making a claim, which is why le-boitier.md can
    # already list this wheel as "not lit, visible through the caseback".
    #
    # So the plate is opened over the one mechanism worth seeing work, and the
    # only thing that moves is driven: the wheel is drawn one column advanced
    # when a verdict was carried this turn, and at rest when none was. Drawing
    # a generic train of wheels turning would be gear-porn - a part that looks
    # busy without being connected to anything, which is the exact failure the
    # rest of this dial is built to avoid.
    if detailed:
        wx2, wy2 = polar(cx, cy, size * 0.132, "7.5")
        wr = size * 0.044
        advanced = bool(trace.verdicts)

        add(f'<circle cx="{wx2:.1f}" cy="{wy2:.1f}" r="{wr:.1f}" fill="#0a0d18" '
            f'stroke="{INK["edge"]}" stroke-width="2.5"/>')
        spin = 30 if advanced else 0
        add(f'<g transform="rotate({spin} {wx2:.1f} {wy2:.1f})" opacity="0.95">')
        for i in range(12):                       # the wheel's teeth
            a = math.radians(i * 30)
            add(f'<line x1="{wx2 + (wr-5)*math.cos(a):.1f}" '
                f'y1="{wy2 + (wr-5)*math.sin(a):.1f}" '
                f'x2="{wx2 + (wr-12)*math.cos(a):.1f}" '
                f'y2="{wy2 + (wr-12)*math.sin(a):.1f}" '
                f'stroke="{INK["brass_lo"]}" stroke-width="2.5"/>')
        for i in range(6):                        # the columns themselves
            a = math.radians(i * 60 + 30)
            add(f'<circle cx="{wx2 + (wr*0.42)*math.cos(a):.1f}" '
                f'cy="{wy2 + (wr*0.42)*math.sin(a):.1f}" r="3.4" '
                f'fill="url(#brass)"/>')
        add(f'<circle cx="{wx2:.1f}" cy="{wy2:.1f}" r="4" '
            f'fill="{INK["brass_hi"]}"/>')
        add('</g>')
        add(f'<text x="{wx2:.1f}" y="{wy2 - wr - 18:.1f}" text-anchor="middle" '
            f'fill="{INK["dim"]}" font-size="7.5" '
            f'font-family="ui-monospace,monospace" letter-spacing="1">'
            f'{esc(owner_of(anatomy, "column wheel"))}</text>')
        add(f'<text x="{wx2:.1f}" y="{wy2 - wr - 8:.1f}" text-anchor="middle" '
            f'fill="{INK["dissent"] if advanced else INK["held"]}" font-size="7" '
            f'font-family="ui-monospace,monospace" letter-spacing="1">'
            f'{"ADVANCED" if advanced else "AT REST"}</text>')

    # --- the hand ---------------------------------------------------------
    # le-conseil.md: the hand sweeps to what ended the route. It can, now that
    # routes exist - so route_end wins when there is one. The old reading
    # (highest-precedence admitted hour) stays as the fallback for turns that
    # named no route, which is most of them, and it is no longer an admitted
    # stand-in for a mechanism that did not exist.
    ranked = [c.member.position for c in trace.admitted()
              if c.member.position != "crown"]
    # The hour hand: highest precedence still standing. A chronograph's running
    # hands and its chrono hand measure different things, and so do these. The
    # route is a SEQUENCE - who goes first. Precedence is IRREVERSIBILITY -
    # what matters most if only one thing can be acted on. They diverge, and
    # the divergence is the reading: the route can end at Le Messager while the
    # thing you cannot undo is still sitting at Le Vigile.
    #
    # Short and blunt, so it is never mistaken for the minute hand. Drawn only
    # when it differs from where the route stopped; superimposed it would be a
    # second hand indicating nothing, which is the same test the rattrapante
    # has to pass.
    precedence_first = ranked[0] if ranked else None
    if trace.route_end:
        ranked = [trace.route_end] + [p for p in ranked if p != trace.route_end]
    if precedence_first and precedence_first != trace.route_end:
        px, py = polar(cx, cy, r_label - 74, precedence_first)
        add(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
            f'stroke="{INK["cyan"]}" stroke-width="5.5" stroke-linecap="round" '
            f'opacity="0.92"/>')
        # Past the tip on the same ray, not above it - above put the legend
        # across the hand it was labelling.
        plx, ply = polar(cx, cy, r_label - 52, precedence_first)
        add(f'<text x="{plx:.1f}" y="{ply:.1f}" text-anchor="middle" '
            f'fill="{INK["cyan"]}" font-size="7" '
            f'font-family="ui-monospace,monospace" letter-spacing="1" '
            f'opacity="0.85">PRECEDENCE</text>')

    # --- la rattrapante: the split-seconds hand ---------------------------
    # A route has two termini now - where it was aimed and where it actually
    # stopped - and until this the gap between them survived only as a line of
    # text. A rattrapante is exactly two hands riding superimposed until
    # something splits them, which is the mechanism this situation already is.
    #
    # Drawn only when they differ. A route that completed as intended has one
    # hand, because a split hand resting under the main one would be a
    # complication indicating nothing, and doctrine keeps the hands unassigned
    # precisely so they never say more than the trace does.
    split = trace.route_aimed if (
        trace.route_aimed and trace.route_aimed != trace.route_end) else None
    if split:
        sx, sy = polar(cx, cy, r_label - 26, split)
        add(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" '
            f'stroke="{INK["held"]}" stroke-width="2.6" stroke-linecap="round" '
            f'stroke-dasharray="7 5" opacity="0.9"/>')
        # The legend rides inboard on the same ray. At the tip it collides with
        # whatever complication sits at that hour - LEAP at 10:30 was the case.
        lx2, ly2 = polar(cx, cy, 70, split)
        add(f'<text x="{lx2:.1f}" y="{ly2:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="7" '
            f'font-family="ui-monospace,monospace" letter-spacing="1">'
            f'AIMED</text>')
    # Stops short of the label annulus. The hand always points at an admitted
    # member, so a hand long enough to touch the chapter ring is a hand that
    # always crosses that member's own name - it would strike out the one
    # label the reading depends on. le-boitier.md ranks legibility first.
    if trace.route and trace.route_end is None and detailed:
        add(f'<text x="{cx:.1f}" y="{cy + size*0.075:.1f}" text-anchor="middle" '
            f'fill="{INK["held"]}" font-size="7.5" '
            f'font-family="ui-monospace,monospace" letter-spacing="1.5">'
            f'ROUTE ARRESTED &#183; NOTHING TO INDICATE</text>')
    if ranked:
        hx, hy = polar(cx, cy, r_label - 10, ranked[0])
        add(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{hx:.1f}" y2="{hy:.1f}" '
            f'stroke="{INK["ink"]}" stroke-width="4.5" stroke-linecap="round"/>')
    add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="{INK["brass_hi"]}"/>')
    add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.5" fill="{INK["plate"]}"/>')

    # --- control legend, below the case ----------------------------------
    # The three flank controls named. They are drawn on the case itself, so
    # this is a key to them rather than a second set of indications.
    if detailed:
        ly_c = cy + r_case + 44
        # The Scuba Dude is a figure on a Vostok's dial. This instrument
        # cannot do that: le-conseil.md puts L'Operateur outside the case
        # entirely, "not a part". But the crown is the one thing he touches,
        # and he is the only one who may turn it - so his mark goes there and
        # nowhere else. A maker's mark on the dial would put the wearer inside
        # the movement, which is the one place doctrine says he is not.
        add(f'<text x="{cx + r_case + 46:.1f}" y="{cy + 4:.1f}" '
            f'fill="{INK["brass_hi"]}" font-size="10" '
            f'font-family="ui-monospace,monospace" letter-spacing="2" '
            f'opacity="0.9">MTM</text>')
        add(f'<text x="{cx - 360:.1f}" y="{ly_c:.1f}" fill="{fripon_ink}" '
            f'font-size="10.5" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5">02 PUSHER &#183; LE FRIPON &#183; '
            f'{"ARMED" if unsealed else "SEALED"}</text>')
        add(f'<text x="{cx:.1f}" y="{ly_c:.1f}" text-anchor="middle" '
            f'fill="{INK["brass_hi"]}" font-size="10.5" '
            f'font-family="ui-monospace,monospace" letter-spacing="1.5">'
            f'03 CROWN &#183; {esc(owner_of(anatomy, "crown"))}</text>')
        add(f'<text x="{cx + 360:.1f}" y="{ly_c:.1f}" text-anchor="end" '
            f'fill="{INK["dim"]}" font-size="10.5" '
            f'font-family="ui-monospace,monospace" letter-spacing="1.5">'
            f'04 PUSHER &#183; RESET</text>')

    # --- route ring on the rehaut ----------------------------------------
    # The Eco-Drive prints its twelve months around the rehaut and indicates
    # one. The nine named routes are this instrument's equivalent vocabulary,
    # and unlike the months they are trace-driven: trace.route says which is
    # running. Printed dim, lit when taken - so the ring shows what the
    # instrument CAN do as well as what it is doing, which is the same reason
    # a dark hour still carries a numeral.
    #
    # The lower sector is skipped: Le Sas and Le Frein already hold the rehaut
    # at 6, and a ring that ran under them would be a ring nobody could read.
    if detailed:
        names = list(load_routes())
        span, start = 232.0, -116.0        # degrees, centred on 12
        for i, rname in enumerate(names):
            a = math.radians(start + span * (i / (len(names) - 1)) - 90)
            rx, ry = cx + (r_chapter + 12) * math.cos(a), cy + (r_chapter + 12) * math.sin(a)
            taken = trace.route == rname
            rot = math.degrees(a) + 90
            # Past the vertical the tangent runs backwards and the legend sets
            # upside down. Flipping 180 is what a curved dial legend does on
            # the far side of the ring; without it half the vocabulary reads
            # bottom-to-top, which is worse than not printing it.
            if rot > 90 or rot < -90:
                rot += 180
            add(f'<text x="{rx:.1f}" y="{ry + 3:.1f}" text-anchor="middle" '
                f'fill="{INK["cyan"] if taken else INK["dim"]}" '
                f'font-size="{9 if taken else 8}" '
                f'font-family="ui-monospace,monospace" letter-spacing="1" '
                f'opacity="{1 if taken else 0.62}" '
                f'transform="rotate({rot:.1f} {rx:.1f} {ry:.1f})">'
                f'{esc(rname.upper())}</text>')

    # --- le frein: the brake ---------------------------------------------
    # A halt is a whole-ring state, not a per-position one, so it cannot be
    # carried by marker colour alone - the dissenter goes magenta, but the
    # members it stopped are only 'held', which is what an over-cap member
    # looks like too. The band is what distinguishes being held because the
    # room was full from being held because someone pulled the brake.
    if detailed and trace.halted:
        add(f'<text x="{cx:.1f}" y="{cy + size*0.262:.1f}" text-anchor="middle" '
            f'fill="{INK["dissent"]}" font-size="9" '
            f'font-family="ui-monospace,monospace" letter-spacing="1.5">'
            f'{esc(owner_of(anatomy, "brake"))} &#183; '
            f'{len(trace.halted)} HELD &#183; AWAITING L\'OP&#201;RATEUR</text>')

    # --- escapement band --------------------------------------------------
    # The escapement is internal and unseen, so it gets a band and not a
    # subdial. It reports one of two things it actually did: released, or
    # faulted. Silence here would be the escapement's own failure mode.
    if detailed:
        released = any(s.startswith("RELEASE") for s in trace.stages)
        if trace.failures:
            band, band_ink = "FAULT", INK["fault"]
        elif released:
            band, band_ink = "RELEASED", INK["dim"]
        else:
            band, band_ink = "NO RELEASE", INK["held"]

        # On the rehaut - the flange between the chapter ring and the dial
        # edge. Fixed position now: this chassis has a wider chord there than
        # the chronometer did, so the state fits without the band moving.
        add(f'<text x="{cx:.1f}" y="{cy + size*0.315:.1f}" text-anchor="middle" '
            f'fill="{band_ink}" font-size="10" font-family="ui-monospace,monospace" '
            f'letter-spacing="1.5">'
            f'{esc(owner_of(anatomy, "escapement"))} &#183; {band}</text>')

        # The fault itself reads inward, where the chord is wide enough for a
        # sentence. A lamp says THAT the escapement faulted; the instrument
        # still has to say WHICH, or the trace is the only place it exists.
        if trace.failures:
            add(f'<text x="{cx:.1f}" y="{cy + size*0.258:.1f}" text-anchor="middle" '
                f'fill="{INK["fault"]}" font-size="8" opacity="0.9" '
                f'font-family="ui-monospace,monospace" letter-spacing="0.5">'
                f'{esc(trace.failures[0].upper())}</text>')

    add("</svg>")
    return "\n".join(o)


# The page is an object record, not a dashboard. overlays/forgotten-industries.md
# asks for museum object record / repair manual / technical field documentation
# and rules out cyberpunk excess and RGB. So: an engineer's computation sheet,
# with the instrument recessed into it as a dark plate. Archive cream was the
# obvious move and therefore the wrong one - FI's material world is anodised
# aluminium, brass fittings and pale green engineering pads, not parchment.
CSS = """
:root {
  --sheet:  #d2d8ca;
  --field:  #e2e6db;
  --rule:   #a9b49c;
  --soft:   #c0c8b6;
  --ink:    #1e231b;
  --dim:    #5b6252;
  --brass:  #7a6532;
  --oxide:  #8f3722;
  --plate:  #0f1317;
  --display: Rockwell, "Rockwell Nova", "Roboto Slab", Georgia, serif;
  --body: "Gill Sans", "Gill Sans MT", GillSans, Optima, "Segoe UI", system-ui, sans-serif;
  --data: Menlo, ui-monospace, "SF Mono", Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0; color: var(--ink); font-family: var(--body);
  font-size: 16px; line-height: 1.6;
  padding: 40px 28px 96px;
  background-color: var(--sheet);
  background-image:
    repeating-linear-gradient(0deg, transparent 0 23px, rgba(30,35,27,.05) 23px 24px),
    repeating-linear-gradient(90deg, transparent 0 23px, rgba(30,35,27,.05) 23px 24px);
}
.sheet { max-width: 1180px; margin: 0 auto; }

/* masthead ------------------------------------------------------------- */
.masthead { display: flex; justify-content: space-between; align-items: baseline;
  gap: 20px; flex-wrap: wrap;
  border-bottom: 2px solid var(--ink); padding-bottom: 10px; }
.mark { font-family: var(--display); font-size: 19px; letter-spacing: .07em;
  text-transform: uppercase; }
.ref { font-family: var(--data); font-size: 11px; letter-spacing: .16em;
  text-transform: uppercase; color: var(--dim); }
.motto { font-family: var(--data); font-size: 10.5px; letter-spacing: .2em;
  text-transform: uppercase; color: var(--brass);
  border-bottom: 1px solid var(--rule); padding: 7px 0 9px; margin-bottom: 42px; }

/* record head ---------------------------------------------------------- */
.record { display: grid; grid-template-columns: 232px 1fr; gap: 46px;
  align-items: start; margin-bottom: 46px; }
.spine dl { margin: 0; }
.spine dt { font-family: var(--data); font-size: 10px; letter-spacing: .15em;
  text-transform: uppercase; color: var(--dim); margin-top: 15px; }
.spine dt:first-child { margin-top: 0; }
.spine dd { margin: 3px 0 0; font-size: 14.5px;
  font-variant-numeric: tabular-nums; }
.spine dd code { font-size: 12.5px; }
h1 { font-family: var(--display); font-size: clamp(42px, 6vw, 62px);
  line-height: 1.02; margin: -8px 0 10px; letter-spacing: -.005em; }
.deck { font-size: 19px; line-height: 1.45; margin: 0 0 18px; max-width: 30ch; }
.lede p { margin: 0 0 14px; max-width: 62ch; color: var(--dim); font-size: 15.5px; }

/* plates --------------------------------------------------------------- */
figure { margin: 0 0 44px; }
.plate { position: relative; background: var(--plate);
  border: 1px solid var(--rule); padding: 22px; }
.reg { position: absolute; width: 15px; height: 15px; border: 0 solid var(--brass); }
.reg.tl { top: -1px; left: -1px; border-top-width: 2px; border-left-width: 2px; }
.reg.tr { top: -1px; right: -1px; border-top-width: 2px; border-right-width: 2px; }
.reg.bl { bottom: -1px; left: -1px; border-bottom-width: 2px; border-left-width: 2px; }
.reg.br { bottom: -1px; right: -1px; border-bottom-width: 2px; border-right-width: 2px; }
.plate svg { display: block; width: 100%; height: auto; }
/* The scroller sits inside the plate, not on it, so the registration marks
   stay pinned to the plate's corners instead of scrolling away with the
   object. Plate 1's dial is capped at a readable size rather than blown up
   to the sheet width; the strip's svgs sit in figures and still fill. */
.scroll { overflow-x: auto; }
.scroll > svg { max-width: 620px; margin: 0 auto; }
figcaption { font-family: var(--data); font-size: 11px; line-height: 1.6;
  color: var(--dim); margin-top: 9px; letter-spacing: .04em; }
figcaption b { color: var(--ink); font-weight: 400; letter-spacing: .14em;
  text-transform: uppercase; }
.strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px; }
.strip figcaption { margin-top: 7px; text-align: center; }

/* reading -------------------------------------------------------------- */
h2 { font-family: var(--display); font-size: 15px; letter-spacing: .1em;
  text-transform: uppercase; margin: 0 0 12px; font-weight: 400;
  border-bottom: 1px solid var(--rule); padding-bottom: 7px; }
.reading { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px 42px; margin-bottom: 48px; align-items: start; }
.group { background: var(--field); border: 1px solid var(--soft); padding: 16px 18px 14px; }
/* align-items: baseline, not the flex default. Three type sizes in two
   families sit in this row - a mono label, a body-face owner, a mono note -
   and stretch puts each at the top of its own box, so no two share a
   baseline. This is the line that makes the column read as typeset rather
   than assembled. */
.row { display: flex; justify-content: space-between; gap: 14px;
  align-items: baseline;
  padding: 6px 0; border-bottom: 1px dotted var(--soft); font-size: 14px; }
.row:last-child { border-bottom: 0; }
.k { font-family: var(--data); font-size: 11.5px; color: var(--dim);
  letter-spacing: .06em; white-space: nowrap;
  font-variant-numeric: tabular-nums; }
.v { text-align: right; }
.v .note-s { font-family: var(--data); font-size: 10.5px; color: var(--dim);
  margin-left: 8px; letter-spacing: .06em; }
.tag { font-family: var(--data); font-size: 10.5px; letter-spacing: .13em;
  text-transform: uppercase; font-variant-numeric: tabular-nums; }
.utt { font-family: var(--data); font-size: 13px; line-height: 1.65;
  word-break: break-word; }
.cycle { list-style: none; margin: 0; padding: 0; }
.cycle li { display: flex; gap: 12px; padding: 4px 0; font-size: 13.5px;
  align-items: baseline; font-variant-numeric: tabular-nums; }
.cycle .n { font-family: var(--data); font-size: 10.5px; color: var(--brass);
  min-width: 20px; }
.cycle .to { font-family: var(--data); font-size: 10.5px; color: var(--dim);
  margin-left: auto; }
.none { color: var(--dim); font-style: italic; font-size: 14px; }
.fault { color: var(--oxide); font-family: var(--data); font-size: 12.5px;
  line-height: 1.65; }

/* field notes ---------------------------------------------------------- */
.notes { border-top: 2px solid var(--ink); padding-top: 26px; }
.notes .col { columns: 2; column-gap: 44px; max-width: 100%; }
.notes p { margin: 0 0 15px; font-size: 14.5px; line-height: 1.7;
  color: var(--dim); break-inside: avoid; }
.notes b { color: var(--ink); font-weight: 600; }
code { font-family: var(--data); font-size: .9em; color: var(--brass); }
footer { margin-top: 52px; border-top: 1px solid var(--rule); padding-top: 14px;
  display: flex; justify-content: space-between; gap: 18px; flex-wrap: wrap;
  font-family: var(--data); font-size: 10.5px; letter-spacing: .14em;
  text-transform: uppercase; color: var(--dim); }

@media (max-width: 860px) {
  .record { grid-template-columns: 1fr; gap: 28px; }
  .notes .col { columns: 1; }
  h1 { margin-top: 0; }
}
/* Landscape gate. The sheet is a technical drawing: the plate, the spine and
   the two-column notes all assume a long edge. Rather than reflow it into a
   column that no longer reads as a drawing, ask for the device to be turned.
   It is escapable on purpose - a hard orientation lock strands anyone whose
   rotation is locked, which is a real accessibility failure, not an edge case.

   The pointer test is load-bearing, not belt-and-braces. 'orientation:
   portrait' is true of ANY viewport taller than it is wide, so the first
   version of this gate fired when someone dragged a desktop preview panel
   narrower to make room for something beside it - the drawing vanished behind
   a card telling them to rotate a device they were not holding, which reads as
   the page having broken. A phone is identified by its input, not its aspect
   ratio: 'pointer: coarse' is the part of this query that actually means
   touch. The width bound only keeps tablets held upright out of it. */
.gate { display: none; }
.vh { position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; }
@media (orientation: portrait) and (max-width: 820px) and (pointer: coarse) {
  .gate { display: flex; position: fixed; inset: 0; z-index: 50;
    align-items: center; justify-content: center; padding: 32px;
    background-color: var(--sheet);
    background-image:
      repeating-linear-gradient(0deg, transparent 0 23px, rgba(30,35,27,.05) 23px 24px),
      repeating-linear-gradient(90deg, transparent 0 23px, rgba(30,35,27,.05) 23px 24px); }
  #portrait-ok:checked ~ .gate { display: none; }
  .gate-inner { max-width: 34ch; border: 1px solid var(--rule);
    background: var(--field); padding: 26px 24px; position: relative; }
  .gate .mark { font-size: 15px; margin-bottom: 20px; }
  .gate h2 { font-family: var(--display); font-size: 25px; letter-spacing: 0;
    text-transform: none; border: 0; padding: 0; margin: 0 0 10px; }
  .gate p { margin: 0 0 18px; font-size: 15px; color: var(--dim); }
  .gate label { font-family: var(--data); font-size: 10.5px; letter-spacing: .14em;
    text-transform: uppercase; color: var(--brass); border-bottom: 1px solid var(--brass);
    padding-bottom: 2px; cursor: pointer; }
  #portrait-ok:focus-visible ~ .gate label { outline: 2px solid var(--brass);
    outline-offset: 3px; }
}

/* Phones. The dial is vector and stays sharp at any size, but its engravings
   are set for a 620px plate - let it shrink to a 375px screen and they drop
   under 5px and stop being readable. So the object holds a legible minimum
   and pans instead, which is also how you read a real dial: you move it,
   you do not shrink it. Only the plate scrolls; the sheet never does. */
@media (max-width: 700px) {
  body { padding: 22px 14px 64px; }
  .plate { padding: 12px; }
  .scroll > svg { min-width: 560px; max-width: none; }
  .strip { grid-template-columns: none; grid-auto-flow: column;
    grid-auto-columns: 190px; }
  .group { padding: 14px 15px 12px; }
  .reading { gap: 22px; }
  figure { margin-bottom: 34px; }
}
"""

# State colours for the sheet. The SVG palette is tuned for a dark plate and
# is unreadable on pale green, so the page keeps its own.
STATE_TEXT = {
    "consulted": "#8a7a12",
    "dissent": "#6b3f8c",
    "active": "#2f6d4e",
    "sealed": "#8a5a12",
    "held": "#6a7162",
    "dark": "#98a190",
}


MECHANISMS = (
    ("Bezel", "bezel", "unidirectional"),
    ("Dial plate", "dial plate", "ground"),
    ("Up-and-down arc", "barrel", "undriven"),
    ("Registers", "registers", "undriven"),
    ("Crown", "crown", "input"),
    ("Going train", "going train", "driving"),
    ("Escapement", "escapement", "release"),
    ("Column wheel", "column wheel", "verdicts"),
    ("Brake", "brake", "the halt"),
    ("Perpetual calendar", "perpetual calendar", "undriven"),
    ("Hands", "hands", "answer"),
)


def readout(trace: Trace, anatomy: dict[str, str]) -> str:
    d = trace.to_dict()
    lit = [p for p in d["positions"] if p["state"] != "dark"]

    rows = "".join(
        f'<div class="row"><span>{esc(p["name"])}</span>'
        f'<span class="tag" style="color:{STATE_TEXT.get(p["state"], "#98a190")}">'
        f'{p["state"].upper()}</span></div>' for p in lit)
    reasons = "".join(
        f'<div class="row"><span class="k">{p["position"]}</span>'
        f'<span class="k">{esc(p["reason"])}</span></div>' for p in lit)
    mechs = "".join(
        f'<div class="row"><span class="k">{esc(part)}</span>'
        f'<span class="v">{esc(owner_of(anatomy, key))}'
        f'<span class="note-s">{note}</span></span></div>'
        for part, key, note in MECHANISMS)

    # The cycle is the one thing here that is genuinely a sequence, so it is
    # the one thing numbered. Numbering the rest would be decoration.
    steps = []
    for i, stage in enumerate(d["stages"], 1):
        name, _, target = stage.partition("->")
        tail = f'<span class="to">&#8594; {esc(target)}</span>' if target else ""
        steps.append(f'<li><span class="n">{i:02d}</span>'
                     f'<span>{esc(name)}</span>{tail}</li>')
    cycle = f'<ol class="cycle">{"".join(steps)}</ol>'

    faults = ("".join(f"<div>{esc(f)}</div>" for f in d["failures"])
              if d["failures"] else '<div class="none">None recorded.</div>')
    notices = ("".join(f'<div class="row"><span>{esc(n)}</span></div>'
                       for n in d["notices"])
               if d["notices"] else '<div class="none">None recorded.</div>')

    return f"""
    <div class="group"><h2>Input</h2>
      <div class="utt">{esc(d['utterance'])}</div>
      <div class="row" style="margin-top:10px"><span class="k">armed</span>
        <span class="k">{esc(d['armed']) if d['armed'] else '&#8212;'}</span></div></div>
    <div class="group"><h2>Mechanisms</h2>{mechs}</div>
    <div class="group"><h2>Positions &#183; {len(lit)} of 13 lit</h2>{rows}</div>
    <div class="group"><h2>Why each fired</h2>{reasons}</div>
    <div class="group"><h2>Cycle</h2>{cycle}</div>
    <div class="group"><h2>Notices</h2>{notices}</div>
    <div class="group"><h2>Faults</h2><div class="fault">{faults}</div></div>
    """


SPECIMENS = [
    ("what happened here", None, "named &#183; one hour fires"),
    ("red team my backups", None, "named, unarmed &#183; SEALED"),
    ("red team my backups", "Le Fripon", "armed &#183; ACTIVE"),
    ("rename this file", None, "routine &#183; convenes no one"),
    ("preserve this, map this, security check, argue against this, classify this",
     None, "five named, cap of four &#183; held, reported"),
    ("preserve this, map this, security check, argue against this", None,
     "Le Reneg&#225;t returns Archive &#183; DISSENT, brake engaged",
     [("Le Renégat", "Archive")]),
]


REGS = ('<span class="reg tl"></span><span class="reg tr"></span>'
        '<span class="reg bl"></span><span class="reg br"></span>')


def render(trace: Trace, standalone: bool = True) -> str:
    """The object record.

    standalone=True gives a complete document. standalone=False gives the same
    page as a fragment - title, style and content, with no doctype, html, head
    or body - for hosts that supply their own document shell. One source either
    way, because two copies of this page would drift the way two copies of the
    anatomy table would.
    """
    ring = load_ring()
    anatomy = load_anatomy()
    spec = "".join(
        f'<figure>{dial_svg(route(ring, sp[0], sp[1], verdicts=sp[3] if len(sp) > 3 else None), 240, detailed=False)}'
        f'<figcaption>{sp[2]}</figcaption></figure>' for sp in SPECIMENS)
    head = ("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le Cadran</title>
<style>%s</style></head>
<body>""" % CSS) if standalone else f"<title>Le Cadran</title>\n<style>{CSS}</style>"
    return f"""{head}
<input type="checkbox" id="portrait-ok" class="vh">
<div class="gate"><div class="gate-inner">
  <div class="mark">Forgotten Industries</div>
  <h2>Turn the sheet</h2>
  <p>This is a technical drawing. The plate, the record spine and the notes are
  all set across the long edge &#8212; rotate to landscape to read it.</p>
  <label for="portrait-ok">Read in portrait anyway</label>
</div></div>
<div class="sheet">

  <header class="masthead">
    <div class="mark">Forgotten Industries</div>
    <div class="ref">Object record &#183; ATLAS / Le Conseil &#183; ref CDN-01</div>
  </header>
  <div class="motto">Human judgement // Machine collaboration // Contre l'oubli</div>

  <div class="record">
    <aside class="spine"><dl>
      <dt>Object</dt><dd>Le Cadran &#8212; the dial</dd>
      <dt>Class</dt><dd>Display. Prototype 0.</dd>
      <dt>Form</dt><dd>Diver's chronograph</dd>
      <dt>Status</dt><dd>Rendering. Not built.</dd>
      <dt>Drive</dt><dd>Routing trace only</dd>
      <dt>Source</dt><dd><code>rouage/rouage.py</code></dd>
      <dt>Doctrine</dt><dd><code>overlays/le-conseil.md</code></dd>
      <dt>Enclosure</dt><dd><code>hardware/le-boitier.md</code></dd>
    </dl></aside>
    <div class="lede">
      <h1>Le Cadran</h1>
      <p class="deck">Twelve positions that are operating modes, not hours.</p>
      <p>The council is one agent in many modes, laid out as a diver's
      chronograph because each part of that movement carries a real constraint.
      This sheet records the dial: what it shows, what drives it, and what it
      refuses to show.</p>
      <p>Every lit element traces to a field in a routing trace emitted by the
      going train. Anything the train cannot drive is drawn undriven and says
      so on its face. There is no demo loop and no idle animation &#8212; an
      instrument displaying invented state is a prop.</p>
    </div>
  </div>

  <figure>
    <div class="plate">{REGS}
      <div class="scroll">{dial_svg(trace, anatomy=anatomy)}</div></div>
    <figcaption><b>Plate 1</b> &#8212; the dial under one routing trace.
    Dark positions are genuinely dark: the gate did not fire.</figcaption>
  </figure>

  <div class="reading">{readout(trace, anatomy)}</div>

  <figure>
    <div class="plate">{REGS}<div class="scroll strip">{spec}</div></div>
    <figcaption><b>Plate 2</b> &#8212; specimens. One train, five inputs.</figcaption>
  </figure>

  <section class="notes">
    <h2>Field notes</h2>
    <div class="col">
    <p><b>Nothing on this chassis needs translating.</b>
    <code>overlays/le-conseil.md</code> is written for a diver's chronograph
    and this is one, so every mechanism answers to the name doctrine already
    gave it and <code>CHASSIS</code> is empty. The marine-chronometer draft
    needed two entries in it &#8212; bezel&#8594;gimbal ring, crown&#8594;winding
    arbor &#8212; because a chronometer has neither a rotating bezel nor a
    crown. Those entries being gone is the argument for this form: the arguable
    step is the one that disappeared.</p>
    <p><b>The bezel is unidirectional, and that is the honesty constraint as
    structure rather than a sentence.</b> A dive bezel ratchets one way only,
    so it can report that less time remains than you thought and never more.
    That fail-safe asymmetry is ATLAS's disposition exactly. The chronometer
    draft had to print &ldquo;rate recorded, never reset&rdquo; on the dial to
    say the same thing in words; here the teeth say it, and a dive dial earns
    its legibility by carrying less.</p>
    <p><b>The crown is the only way in, and the pushers are the only controls that
    authorize.</b> Le Sauvegarder is the crown at 3 &#8212; there is no path to
    the movement that does not pass through preservation. The guarded pusher at
    2 is Le Fripon and it is the one control that lights, driven from
    <code>trace.armed</code>. That is the honest wiring: arming is Le Fripon's
    state, not the crown's. The chronometer draft lit the winding arbor for it,
    which put the light on the wrong control.</p>
    <p><b>Every mechanism is engraved with the member that owns it, and the
    ownership is parsed, not written here.</b> The bezel, the plate, the arc,
    the registers, the crown and the escapement all read their owner out of the
    anatomy table in <code>overlays/le-conseil.md</code> at render time, the
    same way the train reads the roster and the cap. Reassign a part in the
    doctrine and the engraving follows; there is no second copy to drift.</p>
    <p><b>An engraving is not a drive signal.</b> Naming who owns a subdial says
    nothing about whether a needle may move in it &#8212; a watch carries the
    maker's assignment on a dead register without claiming it is running.
    So the registers and the arc now say whose they are <em>and</em> that they
    are undriven. Signal, Noise and Gain come from stage 7, which is Le
    Sceptique, which is a person. The arc is the context window, which the train
    does not measure. Drawing a needle in either would be the exact failure
    <code>hardware/le-boitier.md</code> names.</p>
    <p><b>Dissent appears now, and it is magenta rather than red.</b> A fault is
    the routing failing; dissent is a member doing its job, so it must not
    borrow the fault colour. The state arrives from <em>la roue &#224;
    colonnes</em>, the column wheel &#8212; the part that carries what a member
    concluded and routes the consequence without forming a verdict itself.
    <b>Consulted still never appears</b>: marking a member weighed-but-not-surfaced
    is a semantic call, so it belongs to the barrel, which does not exist.</p>
    <p><b>A halt needs a band, not a colour.</b> The dissenter goes magenta, but
    the members it stopped are only <em>held</em> &#8212; which is exactly what
    an over-cap member looks like. Marker colour cannot distinguish being held
    because the room was full from being held because someone pulled the brake,
    so <em>le frein</em> states it in words and names the count.</p>
    <p><b>The hand sweeps to what ended the route</b>, which is what doctrine
    always said and the dial could not do until routes existed. The nine named
    routes are parsed from <code>overlays/le-conseil.md</code> and matched by
    name &#8212; a route has the same two halves as a gate, and its own name is
    the matchable one. Turns that name no route fall back to the
    highest-precedence admitted hour.</p>
    <p><b>Harden ends where it began.</b> Its sequence is Vigile &#8594; Fripon
    &#8594; Vigile, so the hand reads 04 while the position is lit once &#8212;
    a candidate is a seat and a seat cannot be occupied twice. The route's shape
    is kept in the trace rather than by lighting a marker twice.</p>
    </div>
  </section>

  <footer>
    <span>Forgotten Industries &#183; ATLAS &#183; Le Conseil</span>
    <span>A thing documented is a thing not yet lost.</span>
  </footer>
</div>{"</body></html>" if standalone else ""}"""


def main() -> None:
    args = list(sys.argv[1:])
    armed = None
    if "--arm" in args:
        i = args.index("--arm")
        armed = args[i + 1]
        args = args[:i] + args[i + 2:]
    utterance = " ".join(args) or \
        "preserve this, map this, security check, argue against this"

    trace = route(load_ring(), utterance, armed)
    OUT.write_text(render(trace), encoding="utf-8")

    d = trace.to_dict()
    print(f"lit     {len([p for p in d['positions']])} of 13")
    print(f"faults  {json.dumps(d['failures'])}")
    print(f"wrote   {OUT}")
    if sys.platform == "darwin":
        subprocess.run(["open", str(OUT)], check=False)


if __name__ == "__main__":
    main()
