# LE ROUAGE — build

Implementation of `overlays/le-rouage.md`. Python 3, stdlib only, no dependencies.

```sh
python3 -m unittest discover rouage -v
```

## Status

**Partially built.** The deterministic train runs. The barrel boundary is unresolved.

| Stage | State |
|---|---|
| 1 WIND | Recorded. Archive I/O belongs to the crown, not the train. |
| 2 EVALUATE | **Built** — literal phrase matching, half the gate. See below. |
| 3 ORDER | **Built** — precedence parsed from `le-conseil.md`. |
| 4 METER | **Built** — cap, seal, full-ring reporting. |
| 5 LOAD | **Built** — cores only, asserted. |
| 6 COLLECT | Delegated. The barrel generates; the train cannot. |
| 7 TIER | Delegated to Le Sceptique. A person, by design. |
| 8 RELEASE | **Built** — Le Sas conditions, minus the tier check, which needs 6–7. |
| 9 DISTRIBUTE | **Built** — emits the trace. |
| 10 RECORD | Recorded. Archive I/O. |

Nothing about the roster, the precedence ladder, the panel cap, or the activation
phrases is written down in the code. All four are parsed from the markdown at
runtime, so a doctrine edit changes behaviour and the two cannot drift.

## The Split In Every Gate

Building the evaluator surfaced something the specification implies but does not
state: **every activation block has two halves.**

From `subroutines/le-limier.md`:

> Invoke when Matthew names "Le Limier", "the bloodhound", "reconstruct this" —
> *matchable. This is what the train does.*

> Invoke automatically when: an artifact shows modification, damage, or repair
> whose cause is unknown — *not matchable without reading for meaning, which
> `le-rouage.md` prohibits the train from doing.*

So the train implements the named half only. The automatic half necessarily runs
in the barrel, which means the honest architecture is **the barrel proposes and
the train disposes**: proposals still pass through `order()`, `meter()`, and the
Fripon seal downstream. "The train decides nothing" survives, because everything
that constrains the outcome is enforced in code the barrel cannot reach around.

`admit_proposals()` is the boundary and it is **unimplemented on purpose** — the
admission policy is L'Opérateur's call, and it is the trust boundary of the whole
instrument. Three options are written out in the docstring.

## What The Build Found In The Doctrine

Two things a reader would not catch:

**The cap has no enforceable floor.** `le-conseil.md` says "Two to four members
convene at once," then "One is the common case." Only the ceiling is enforceable;
a floor of two would force a second member into turns that need one. `le-sas.md`
agrees — its admission condition names only the excess. The code enforces the
ceiling and ignores the floor. If the floor was meant literally, that is a
doctrine bug, not a code bug.

**Precedence and metering measure different things.** Full ring is a fault in the
*gates*, so it counts what matched. The cap acts on what *survived*. Measuring
full ring on survivors hides the discrimination failure behind the cap the
failure itself triggered. The first version of `meter()` had this backwards and
the test caught it.

## The Trace Is Not The Output

Two surfaces, and conflating them would break suppression:

- **The trace** records held and sealed members, for inspection. That is what
  makes *absence is signal* verifiable rather than asserted.
- **The prose ATLAS returns** must not name them. `le-sas.md`: held members are
  "not named, not listed, and not marked absent in output."

Rendering the trace directly into prose would violate the escapement. The dial
renders the trace; the answer does not.

## The Dial Reads The Anatomy Table

`dial.py` engraves every mechanism with the member that owns it, and the
ownership is parsed from the anatomy table in `le-conseil.md` at render time —
the same discipline the train applies to the roster, the ladder and the cap.
Reassign a part in the doctrine and the engraving follows. There is no second
copy of the mapping to drift.

Two consequences worth stating:

**An engraving is not a drive signal.** Naming the owner of a subdial says
nothing about whether a needle may move in it. The registers and the up-and-down
arc now read `LE SCEPTIQUE` and `LE BARILLET` *and* `UNDRIVEN`, which is what a
real instrument does — the maker's assignment is on the plate whether or not the
hand is running. Conflating the two would have been the `le-boitier.md` failure.

**The chassis renames nothing.** `CHASSIS` is empty. The anatomy table is
written for a diver's chronograph and the dial renders one, so every mechanism
answers to the name doctrine already gave it. The marine-chronometer draft
needed two entries there — bezel→gimbal ring, crown→winding arbor — because a
chronometer has neither a rotating bezel nor a crown; those entries being gone
is the argument for this form. The hook stays so a future chassis has somewhere
to declare its substitutions rather than making them silently. A part absent
from the table renders `UNASSIGNED IN DOCTRINE`; the hands render `DELIBERATELY
NO ONE`, which is a different fact and must not print the same.

## For The Case

`hardware/le-boitier.md`: the LEDs are driven by the routing trace, "never by a
demo loop, an idle animation, or a startup sequence that lights markers for
effect." `Trace.to_dict()` is that wire format. A position absent from
`positions` is genuinely dark.

The instrument form is still open — chronograph, pocket watch, longcase, or a
marine-chronometer chassis. The trace does not care, which is the point of
having built this first.
