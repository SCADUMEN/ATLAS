# LE ROUAGE — build

Implementation of `overlays/le-rouage.md`. Python 3, stdlib only, no dependencies.

```sh
python3 -m unittest discover rouage -v
```

## Status

**Partially built.** The deterministic train runs. The admission policy at the barrel boundary is decided; the barrel that would use it does not exist yet.

| Stage | State |
|---|---|
| 1 WIND | **Built** — `record_winding()`. The caller invokes it; the train never does. |
| 2 EVALUATE | **Built** — literal phrase matching, half the gate. See below. |
| 2b ROUTE | **Built** — the nine named routes, matched by name. |
| 3 ORDER | **Built** — precedence parsed from `le-conseil.md`. |
| 4 METER | **Built** — cap, seal, full-ring reporting. |
| 5 LOAD | **Built** — cores only, asserted. |
| 6 COLLECT | Delegated, with a contract. `citations()` gives the barrel the exact quotable menu. |
| 7 TIER | Delegated to Le Sceptique. A person, by design. |
| 8a VERDICT | **Built** — la roue à colonnes: verdicts, dissent, le frein. |
| 8 RELEASE | **Built** — including the tier check. Le Sas checks tiers *exist*, which is structural; assigning them is Le Sceptique's. |
| 9 DISTRIBUTE | **Built** — emits the trace. |
| 10 RECORD | **Built** — same call. Append-only, time supplied by the caller. |

Nothing about the roster, the precedence ladder, the panel cap, the activation
phrases, the anatomy table or the route invocation grammar is written down in
the code. All of it is parsed from the markdown at runtime, so a doctrine edit
changes behaviour and the two cannot drift.

## Invariants, Not Just Cases

`InvariantsUnderComposition` runs a matrix — utterances by arming by verdicts
by tiers by cap authorizations — and asserts the properties that must hold for
every one of them:

- no candidate ends in a state the dial cannot render
- Le Fripon is never active without the crown
- nothing ever stops the crown, not le frein and not Le Sas
- the hand never indicates a member that is not standing
- `route_end` is always a step of the route
- a halt always has a dissenter visible on the dial
- every combination is reproducible

`route()` takes nine parameters. Hand-written cases test the paths someone
thought of, and the `route_end` bug lived precisely in the one nobody had:
every mechanism was correct alone and the fault was only in their combination.
This is that discovery method made systematic rather than lucky.

## Four Guards, One Failure Mode

A surface quietly falls behind the mechanism it reports on. It happened five
times, in four different places, and each time it was invisible
until something asserted it:

| Seam | Asserts | Caught |
|---|---|---|
| train → dial | every emittable state has an ink | `dissent` rendering as `dark`, its own opposite |
| dial → sheet | every ink is demonstrated | Plate 2 showing no route and no split hand |
| train → readout | every trace field is surfaced | three hands drawn with no key beside them |
| doctrine → panel | every named mechanism is listed |
| train → live readout | every trace field reaches the browser sheet too | the split-seconds hand, absent two commits after it was written into the anatomy |

None of these were noticed by reading. All four were found by asking the code
what it covered. That is the argument for keeping them as tests rather than as
attention.

## The Sheet Has To Keep Up With The Instrument

`SPECIMENS` in `dial.py` is Plate 2 — the showcase. It silently stopped covering
the instrument as the instrument grew: routes and the split hand were both
renderable and absent, and the old specimen form was a 3-or-4 tuple unpacked by
length, so it could not have expressed them anyway.

Each specimen is now a full `route()` call. A test asserts the sheet
demonstrates every state the dial has an ink for, with two structural
exemptions: `dark` is the *absence* of a candidate rather than a state one
carries, and `consulted` has no emitter because deciding a member was weighed
but not surfaced is semantic and belongs to the barrel.

Writing that guard is what caught the `dark` confusion — the first version
demanded a candidate hold a state no candidate can hold.

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

`admit_proposals()` is the boundary, and the admission policy — L'Opérateur's
call, the trust boundary of the whole instrument — is **decided: Cited**. A
proposal is admitted only if its citation is a verbatim line among the bullets
`parse_activation()` already extracted from that member's Activation section at
load time. Anything else is a rejected proposal: it never reaches `order()` or
`meter()`, and the rejection itself lands in `trace.failures` as a discrimination
failure, the same category as full-ring and over-cap. `route()` takes an
optional `proposals` argument that feeds straight into it — the two rejected
options (Permissive, Strict) are still in the docstring as a record of why not.

What is still missing is the barrel itself: nothing in this repo reads an
artifact for meaning and produces the `(member, citation)` pairs to hand in.
`admit_proposals()` is the mechanism a barrel would call; it is not the barrel.

## What The Build Found In The Doctrine

Two things a reader would not catch:

**The cap is a default, not an absolute** — decided after the fact, and the doctrine now says so. Widening takes the same explicit authorization Le Fripon's engagement takes, and is recorded. An unauthorized fifth member is still held: theatre cannot widen itself, which is the property the cap was protecting rather than the number four. Narrowing is refused outright, since that would be a way to suppress a member the gates admitted.

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
