# LE BOÎTIER

## The Case

**Function:** The physical instrument. Enclosure, controls, and display for Le Conseil.
**Class:** Hardware. Not a member, not a mode.
**Status:** **Specified. Not built.**

Le Conseil was designed as semantics and turned out to be an object. Every control the physical build needs was already specified in `overlays/le-conseil.md`, and specified as the correct *kind* of control — a bezel that rotates, a crown that unscrews, a pusher that authorizes. This file records the enclosure so the build has doctrine like everything else does.

**The reference is a diver's chronograph with a perpetual-calendar register layout.** Not a costume: a diver's case is sealed, legible in bad conditions, and operated by feel. All three are requirements here.

---

## Controls

Every control maps to a mode, and the mapping constrains the mechanism.

| Control | Mode | Mechanism | Why that mechanism |
|---|---|---|---|
| **Bezel** | ATLAS | Rotary encoder, 120 detents, unidirectional ratchet | The interface is set, not typed. Unidirectional because ATLAS can only report *less* remaining than you thought. |
| **Crown** | Le Sauvegarder | Screw-down, push-pull, rotary encoder | Input requires deliberately unsealing the case. Preservation cannot be accidental. |
| **Upper pusher** | Le Fripon | Guarded momentary | The only control that authorizes a mode. Guarded because accidental engagement is the exact failure the charter exists to prevent. |
| **Lower pusher** | Reset | Momentary | Clears the reading. Never touches L'Archive. |

### The Screw-Down Crown Is Doctrine, Not Styling

To give input, L'Opérateur must unscrew the crown. To seal the instrument, he screws it back down. Water resistance is archive integrity.

This makes preservation a two-step physical act with a tactile confirmation, and it makes the sealed state the resting state. An instrument sitting on the bench with its crown screwed down is an archive that is protected. That is the correct default and the case should make it obvious at a glance.

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

A 4 in round IPS panel rendering the existing interface at real size. The published artifact is the firmware UI. This validates dial layout, label legibility, and state colours before anything is cut, and it is the cheapest way to find out that a marker is unreadable at arm's length.

Build this first. Le Sauvegarder would insist.

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
