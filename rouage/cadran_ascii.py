"""LE CADRAN, in characters. A third display surface.

Renders a routing trace as a framed terminal panel. Nothing else.

This is dial.py's sibling: dial.py draws the diver's chronograph as SVG, this
draws it as a fixed-width text panel. Both consume one Trace and both are bound
by the same rule, from hardware/le-boitier.md - The Honesty Constraint:

    The display never shows a state the router did not produce.

So the panel is driven only by the Trace. The registers, the up-and-down arc
and the perpetual calendar are drawn UNDRIVEN and say so, because the train
does not drive them. Dark positions are genuinely dark - the gate did not fire.
There is no demo loop; an instrument displaying invented state is a prop.

Ownership is not restated here. Every engraving - ATLAS on the bezel, L'ARCHIVE
on the plate, LE SAS on the escapement, LE FREIN on the brake - is read out of
overlays/le-conseil.md at render time through dial.owner_of(), the same anatomy
table the SVG dial engraves from. There is no second copy to drift.

    python3 rouage/cadran_ascii.py "run Publish"
    python3 rouage/cadran_ascii.py "run Publish" --tier "Le Curateur"
    python3 rouage/cadran_ascii.py "argue against this" --verdict "Le Renégat:Archive"
    python3 rouage/cadran_ascii.py "run Publish" --color

Colour is optional and off unless stdout is a terminal. It reinforces the state
glyph; it never carries the state alone. le-boitier.md ranks legibility first,
and a panel piped to a file or read on a monochrome display must lose nothing.
"""

from __future__ import annotations

import os
import sys
import textwrap

from dial import load_anatomy, owner_of
from rouage import STATES, Ring, Trace, load_ring, route

# Six discrete states, six distinct glyphs - the character-surface equivalent of
# le-boitier.md's six LED colours. The glyph is the carrier: active is solid,
# consulted is half-filled (weighed, part surfaced), sealed is a locked facet,
# held is an empty seat (stopped at the door), dissent is a refusal, dark is a
# dot (off). No two are alike, so no state can be read as another at a glance.
MARKER = {
    "active": "●",
    "consulted": "◐",
    "sealed": "◆",
    "held": "○",
    "dissent": "✕",
    "dark": "·",
}

# Every state rouage.STATES can emit needs a glyph here. A missing one would
# fall through to `dark` and render as its own opposite - the display lying,
# which le-boitier.md calls the difference between a gauge and a prop. This is
# dial.py's `_UNMAPPED` assert, restated for glyphs. `dark` is absence and is
# not in STATES, so it is added by hand.
_UNMAPPED = set(STATES) - set(MARKER)
assert not _UNMAPPED, f"panel cannot render states the train emits: {_UNMAPPED}"
assert "dark" in MARKER, "panel has no glyph for the absent gate"
assert len(set(MARKER.values())) == len(MARKER), "two states share a glyph"

# ANSI, mapping the six colours le-boitier.md's state table already names:
# matrix green, highlighter yellow, amber, amber-grey, magenta, off. Applied
# only when colour is enabled; the glyph above stands without it. Red is not
# here - it is fault-only, and a fault is a text band, never a marker.
RESET = "\033[0m"
COLOR = {
    "active": "\033[38;5;42m",     # matrix green
    "consulted": "\033[38;5;226m",  # highlighter yellow
    "sealed": "\033[38;5;214m",    # amber
    "held": "\033[38;5;101m",      # amber-grey
    "dissent": "\033[38;5;201m",   # magenta
    "dark": "\033[38;5;238m",      # off - the dimmest grey the frame allows
}
FAULT_COLOR = "\033[38;5;203m"     # red, and only ever the fault band


def _paint(text: str, code: str, on: bool) -> str:
    return f"{code}{text}{RESET}" if on else text


def _line(content: str, inner: int, *, token: str = "",
          code: str = "", on: bool = False) -> str:
    """One framed row. Padded on the plain text so the right border stays put,
    then the state token is coloured in place - colour is zero display-width,
    so it never shifts the frame."""
    padded = content[:inner].ljust(inner)
    if on and token and token in padded:
        padded = padded.replace(token, _paint(token, code, True), 1)
    return f"│ {padded} │"


def _wrap(label: str, body: str, inner: int) -> list[str]:
    """A labelled field, wrapped on spaces to the frame width with its
    continuations hanging under the body. Wrapping never splits a word, so a
    stage token or a member name survives intact for a reader and for a test."""
    indent = " " * len(label)
    width = inner - len(label)
    lines = textwrap.wrap(body, width) or [""]
    return [f"{label}{lines[0]}"] + [f"{indent}{ln}" for ln in lines[1:]]


def dial_ascii(trace: Trace, anatomy: dict | None = None,
               ring: Ring | None = None, *, color: bool = False,
               width: int = 64) -> str:
    """The instrument as a framed panel. Every line traces to a Trace field.

    The twelve seat names come from the ring, not the trace: the plate prints
    every numeral whether or not it is lit, and le-boitier.md draws the dark
    markers off rather than blank. The state beside each name comes only from
    the trace. Naming a seat is the plate's job; lighting it is the train's.
    """
    if anatomy is None:
        anatomy = load_anatomy()
    if ring is None:
        ring = load_ring()

    d = trace.to_dict()
    seat_state = {p["position"]: p for p in d["positions"]}
    inner = width - 4
    o: list[str] = []

    # --- top border carries the object's name -----------------------------
    title = "LE CADRAN · diver's chronograph"
    fill = width - len(title) - 5
    o.append(f"┌─ {title} " + "─" * max(fill, 1) + "┐")

    # --- bezel engraving and the wearer, who is not a part ----------------
    left = f"{owner_of(anatomy, 'bezel')} · unidirectional"
    right = "MTM · not a part"
    gap = inner - len(left) - len(right)
    o.append(_line(left + " " * max(gap, 1) + right, inner))
    o.append(_line("", inner))

    # --- the twelve seats -------------------------------------------------
    o.append(_line(f"{'POS':<4}{'MEMBER':<20}{'STATE':<11}WHY", inner))
    # Numeric seat order (01→12). The roster is written 11, 12, 01…10 - the two
    # pre-hours first - but a linear table reads most plainly ascending, and the
    # zero-padded positions sort the same lexically as numerically.
    for m in sorted(ring.hours, key=lambda m: m.position):
        entry = seat_state.get(m.position)
        state = entry["state"] if entry else "dark"
        reason = entry["reason"] if entry else ""
        token = f"{MARKER[state]} {state}"
        row = f"{m.position:<4}{m.name:<20}{token:<11}{reason}"
        o.append(_line(row, inner, token=token, code=COLOR[state], on=color))

    # The crown is a control, not an hour, so it sits apart. It carries a
    # state like any seat - Le Sauvegarder convenes when preservation is named.
    crown = seat_state.get("crown")
    cstate = crown["state"] if crown else "dark"
    ctoken = f"{MARKER[cstate]} {cstate}"
    o.append(_line(f"{'--':<4}{owner_of(anatomy, 'crown').title():<20}"
                   f"{ctoken:<11}crown · the only way in",
                   inner, token=ctoken, code=COLOR[cstate], on=color))
    o.append(_line("", inner))

    # --- the three hands --------------------------------------------------
    # Read exactly as dial.readout does. Hour is precedence #1 (admitted is in
    # precedence order); minute is where the route actually ended; split is
    # where it was aimed, shown only when that differs - the rattrapante rule.
    def hand(pos: str | None) -> str:
        if not pos:
            return "—"
        seat = seat_state.get(pos, {})
        return f"{pos} {seat.get('name', '')}".strip()

    hour = d["admitted"][0] if d["admitted"] else None
    minute = d["route_end"]
    split = d["route_aimed"] if d["route_aimed"] != d["route_end"] else None
    o.append(_line(f"HANDS   minute → {hand(minute):<18} hour → {hand(hour)}",
                   inner))
    o.append(_line(f"        split  → {hand(split)}", inner))
    o.append(_line(f"ROUTE   {d['route'] or '—'}   aimed {d['route_aimed'] or '—'}"
                   f"   ended {d['route_end'] or '—'}", inner))
    o.append(_line("", inner))

    # --- undriven complications, each saying so ---------------------------
    o.append(_line(f"REGISTERS  {owner_of(anatomy, 'registers')} — UNDRIVEN "
                   "(from 01)", inner))
    o.append(_line(f"UP·DOWN    {owner_of(anatomy, 'barrel')} — UNDRIVEN", inner))
    o.append(_line(f"CALENDAR   {owner_of(anatomy, 'perpetual calendar')} — "
                   "UNDRIVEN", inner))
    # The column wheel is the one non-register complication the train does
    # drive: it advances when a verdict was carried this turn.
    advanced = "ADVANCED" if trace.verdicts else "AT REST"
    o.append(_line(f"COLUMN     {owner_of(anatomy, 'column wheel')} · "
                   f"{advanced}", inner))
    o.append(_line("", inner))

    # --- the two bands ----------------------------------------------------
    # A halt is a sentence, not a colour: the brake names its held count,
    # because held-by-the-brake and held-because-the-room-was-full look
    # identical as markers and need different answers from L'Opérateur.
    held = len(trace.halted)
    brake = f"{owner_of(anatomy, 'brake')} · {held} held"
    if held:
        brake += " · awaiting L'Opérateur"
    o.append(_line(brake, inner))

    released = any(s.startswith("RELEASE") for s in d["stages"])
    band = "FAULT" if d["failures"] else "RELEASED" if released else "NO RELEASE"
    o.append(_line(f"{owner_of(anatomy, 'escapement')} · {band}", inner))
    o.append(_line("", inner))

    # --- the cycle, notices, faults ---------------------------------------
    for ln in _wrap("CYCLE   ", " → ".join(d["stages"]), inner):
        o.append(_line(ln, inner))
    notices = "; ".join(d["notices"]) if d["notices"] else "none recorded"
    for ln in _wrap("NOTICES ", notices, inner):
        o.append(_line(ln, inner))
    faults = "; ".join(d["failures"]) if d["failures"] else "none recorded"
    fault_lines = _wrap("FAULTS  ", faults, inner)
    for ln in fault_lines:
        token = faults if d["failures"] and faults in ln else ""
        o.append(_line(ln, inner, token=token, code=FAULT_COLOR, on=color))

    o.append("└" + "─" * (width - 2) + "┘")

    # --- input, outside the case - it is what was said, not what was shown -
    o.append(f' INPUT  "{d["utterance"]}"   armed {d["armed"] or "—"}')
    return "\n".join(o)


def main() -> None:
    """CLI. The same nine inputs dial.py's CLI drives, rendered to the terminal.

        python3 rouage/cadran_ascii.py "run Publish"
        python3 rouage/cadran_ascii.py "red team this" --arm "Le Fripon"
        python3 rouage/cadran_ascii.py "argue against this" --verdict "Le Renégat:Archive"
        python3 rouage/cadran_ascii.py "run Publish" --tier "Le Curateur"
        python3 rouage/cadran_ascii.py "run Publish" --color / --no-color
    """
    args = list(sys.argv[1:])

    def take(flag: str) -> list[str]:
        out = []
        while flag in args:
            i = args.index(flag)
            out.append(args[i + 1])
            del args[i:i + 2]
        return out

    def flag(name: str) -> bool:
        if name in args:
            args.remove(name)
            return True
        return False

    armed = (take("--arm") or [None])[0]
    tiers = take("--tier")
    verdicts = [tuple(v.split(":", 1)) for v in take("--verdict") if ":" in v]
    cap = (take("--cap") or [None])[0]

    force_color = flag("--color")
    no_color = flag("--no-color")
    # Off unless asked, or unless stdout is a terminal and the environment has
    # not opted out. A pipe or NO_COLOR yields identical text without escapes.
    color = force_color or (
        not no_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ)

    utterance = " ".join(args) or \
        "preserve this, map this, security check, argue against this"

    trace = route(load_ring(), utterance, armed,
                  verdicts=verdicts or None,
                  tiered=tiers or None,
                  authorize_cap=int(cap) if cap else None)
    print(dial_ascii(trace, color=color))


if __name__ == "__main__":
    main()
