# LE BOÎTIER

## The Case

**Function:** The physical instrument. Enclosure, controls, and display for Le Conseil.
**Class:** Hardware. Not a member, not a mode.
**Status:** **Specified. Not built.**

Le Conseil was designed as semantics and turned out to be an object. Every control the physical build needs was already specified in `overlays/le-conseil.md`, and specified as the correct *kind* of control — a bezel that rotates, a crown that unscrews, a pusher that authorizes. This file records the enclosure so the build has doctrine like everything else does.

**The reference is a marine chronometer.** Not a costume, and not the first answer — the council was drafted against a diver's chronograph, which got the sealed case and the legibility right and the rest wrong. A watch divides a continuous quantity nobody can stop. This instrument does not: its positions are modes rather than hours, its hand does not sweep, and nothing about it is periodic.

A chronometer fits because it is not a watch that happens to be large. It is a mounted reference instrument, and every one of its defining properties was already in the doctrine before the form was named:

| Already committed | Chronometer, as actually built |
|---|---|
| "Reserve is the context window" | The **up-and-down dial** — a power-reserve complication showing hours until rewinding |
| Preservation cannot be accidental | Wound by a **separate key**, kept with the box, at a fixed time, **and the winding is logged** |
| "The display never shows a state the router did not produce" | **Never adjusted at sea.** You record its rate; you do not correct it |
| Le Sas regulates release and has no stake | **Detent escapement** — releases once per beat, frictionless, too delicate to move while running |
| Le Vigile owns custody | Gimballed box, lock and key, opened by an officer |
| The instrument is read; L'Opérateur decides | A chronometer indicates. It has one job and no opinion |

Sealed, legible in bad conditions, and operated deliberately. The gimbals are the requirement the diver's case was standing in for: the instrument stays level regardless of what the ship does.

---

## Controls

Every control maps to a mode, and the mapping constrains the mechanism.

| Control | Mode | Mechanism | Why that mechanism |
|---|---|---|---|
| **Winding key** | Le Sauvegarder | Detached key, square socket, arbor on the box below the dial | **A separate object you must go and fetch.** There is no path to the movement that does not begin with retrieving it. Preservation cannot be accidental, and now it cannot be reached for absently either. |
| **Gimbal ring** | — | Two pivots, 3 and 9 | Not a control. The instrument stays level regardless of what the ship does. |
| **Upper pusher** | Le Fripon | Guarded momentary | The only control that authorizes a mode. Guarded because accidental engagement is the exact failure the charter exists to prevent. |
| **Lower pusher** | Reset | Momentary | Clears the reading. Never touches L'Archive. |

### The Detached Key Is Doctrine, Not Styling

To give input, L'Opérateur must retrieve the key, open the box, and wind. To seal the instrument, he puts the key back.

A crown is attached, and an attached control can be turned absently. A key cannot: it is a discrete object with its own location, and forgetting where it is stops the instrument entirely. That makes preservation a deliberate errand rather than a gesture, and it makes the sealed state the resting state. A chronometer sitting in its closed box is an archive that is protected. That is the correct default and the case should make it obvious at a glance.

**The winding is logged.** Ships' chronometers were wound at a fixed hour by a named person who signed for it. That is Le Sauvegarder's whole function rendered as a procedure, and it is the reason the crown was never quite the right control: a crown records nothing.

### The Bezel Is An Open Question

`overlays/le-conseil.md` assigns ATLAS to the bezel, and a chronometer has no rotating bezel. Two ways out, and this is L'Opérateur's call:

1. **ATLAS becomes the reference itself.** A chronometer is the standard other instruments are checked against, and is never corrected — you record its rate. That is the bezel's fail-safe asymmetry restated as an operating procedure, and it is arguably stronger.
2. **Keep a rotating bezel** on the dial ring, breaking from the chronometer reference for one part.

Option 1 costs a rewrite of the anatomy table in `overlays/le-conseil.md`, `ATLAS.md`, and `README.md`. Nothing has been changed there yet.

### The Guarded Pusher

`overlays/le-conseil.md` states that Le Fripon never self-activates and requires authorization from L'Opérateur per engagement, with scope that does not carry over. In hardware that is a recessed or shrouded pusher requiring deliberate pressure — never a flush button that a sleeve can press.

**Arming must expire.** Scope not carrying over means the armed state times out and returns to sealed. A physical control that stays armed indefinitely violates the charter it implements.

---

## Display

| Element | Implementation | Notes |
|---|---|---|
| **Twelve hour markers** | Addressable RGB LEDs behind diffused acrylic batons | Seven states map to seven colours. Dark is genuinely off. |
| **Three registers** | Round LCD modules or LED rings | Signal · Noise · Gain, driven from 01 |
| **Hands** | Geared stepper on the centre post, full 360° | The answer. Sweeps to what ended the route. |
| **Escapement** | Single LED behind a window | Pulses once per release. Le Sas made visible. |
| **Power reserve** | Arc of LEDs, 9 through 12 to 3 | The context window. Colour shifts at low reserve. |
| **Plate** | Printed or etched, L'ARCHIVE signed under 12 | The ground the hours are printed on |

### Discrete States Are A Hardware Decision

Seven discrete states map to seven LED colours with no interpretation layer. A continuous display — brightness proportional to confidence — would need calibration and would be unreadable across twelve markers at a glance.

Legibility under bad conditions is a diver's requirement and it is also an astigmatism requirement: uniform stroke weights, no hairlines, ground lifted off pure black, colour pulled back from full saturation to prevent halation.

---

## The Honesty Constraint

`overlays/le-conseil.md`:

> The display never shows a state the router did not produce.

In software that is a discipline. **In hardware it is a wiring constraint.** The LEDs are driven by the routing trace emitted by `overlays/le-rouage.md` — never by a demo loop, an idle animation, or a startup sequence that lights markers for effect.

Which means the physical build **cannot be finished before Le Rouage exists.** Without the train there is no trace, and an instrument displaying invented state is a prop. This is a useful forcing function: the object cannot be faked into completion.

A boot self-test that walks the markers is permitted, provided it is visibly a self-test and terminates.

---

## Enclosure

### Prototype 1 — `.30 CAL`

An M19A1 ammunition can. Interior roughly 10.5 × 3 × 6.5 in.

Laid on its side, the 11 × 7.5 in face carries a dial of **6 to 6.5 in** diameter. Depth at 3 in is the tight axis but accommodates a geared stepper, an LED ring, and a single-board computer comfortably. The existing latch and hinge become the caseback — the instrument opens the way its doctrine says a case opens.

Controls mount through the short face: pusher, crown, pusher, vertically arranged, guarded by a fabricated crown block.

### Prototype 0 — Round Panel

A 4 in round IPS panel rendering the existing interface at real size. This validates dial layout, label legibility, and state colours before anything is cut, and it is the cheapest way to find out that a marker is unreadable at arm's length.

Build this first. Le Sauvegarder would insist.

**Started.** `rouage/dial.py` renders the dial as SVG from a routing trace and nothing else. It is not firmware, but it is the layout under test, and it is honest by construction: the registers and the up-and-down arc are drawn undriven because the train cannot drive them.

```sh
python3 rouage/dial.py "what happened here"
```

### Later

Wearability is not a first-prototype goal and should not constrain the first two. The semantics do not require a wrist.

---

## Fabrication Notes

L'Opérateur has drills, M3 taps, and case-modding experience. Custom fabrication is an available capability, not a blocker — trays, mounts, brackets, ducts, and pass-throughs are in scope.

- Standard fasteners and standard stock. Bespoke hardware is a future sourcing problem.
- Mark irreversible steps before starting. Drilling and cutting are one-way.
- Build the smallest version that can be tested, then expand.
- Fabricate to the tooling that exists.
- Document while building. The reasoning is gone by evening.

That is Le Forgeron's operating law, and it governs this build.

---

## What The Case Does Not Do

- It does not run the council. The barrel lives elsewhere — a host machine or a local model.
- It does not store L'Archive. It displays state; the record is in the repository.
- It does not decide. Nothing in the case decides, including the case.

**The instrument is read. L'Opérateur decides.**
