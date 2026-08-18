# LE BOÎTIER

## The Case

**Function:** The physical instrument. Enclosure, controls, and display for Le Conseil.
**Class:** Hardware. Not a member, not a mode.
**Status:** **Specified. Not built.**

Le Conseil was designed as semantics and turned out to be an object. Every control the physical build needs was already specified in `overlays/le-conseil.md`, and specified as the correct *kind* of control — a bezel that rotates, a crown that unscrews, a pusher that authorizes. This file records the enclosure so the build has doctrine like everything else does.

**The reference is a diver's chronograph.** Not a costume. A marine chronometer was drafted against this file for a while and was returned: it is a fine instrument and the wrong one, because it has neither a rotating bezel nor a crown, and `overlays/le-conseil.md` had already assigned both. Every mechanism the doctrine names is a chronograph part, and the anatomy table maps onto the form with nothing left over and nothing renamed.

That is the whole argument. The chassis that needs no translation layer is the chassis the doctrine was written for:

| Already committed | Chronograph, as actually built |
|---|---|
| ATLAS is the bezel, and unidirectional by construction | A **dive bezel** ratchets one way only. It can report that less time remains than you thought, never more |
| Le Sauvegarder is the crown, and the only way in | A **screw-down crown**, unscrewed deliberately, sealing when it is closed. Nothing enters the movement past it |
| Le Fripon never self-activates | The **upper pusher** — guarded, momentary, per engagement |
| Signal · Noise · Gain | **Registers.** The horological term for a chronograph's subdials is the word the doctrine already used |
| "Reserve is the context window" | The **up-and-down complication**, showing what is left before rewinding |
| Le Sas regulates release and has no stake | The **escapement**, internal and unseen, releasing once per beat |
| Le Continuant holds the long arc | The **perpetual calendar** — the complication that does not forget the shape of time, and loses its place if it stops |
| The instrument is read; L'Opérateur decides | A watch indicates. It has one job and no opinion |

Sealed, legible in bad conditions, and operated deliberately.

**The objection this file used to make against a watch still stands, and is survivable.** A watch divides a continuous quantity nobody can stop; this instrument's positions are modes rather than hours and nothing about it is periodic. True — and the answer is that the dial is not periodic even though the movement behind it is. The hand does not sweep; it indicates. Periodicity was already admitted at the escapement, which releases once per beat, and a chronograph is precisely the watch built for measuring an interval that starts when you decide it starts.

---

## Controls

Every control maps to a mode, and the mapping constrains the mechanism.

| Control | Mode | Mechanism | Why that mechanism |
|---|---|---|---|
| **Crown** | Le Sauvegarder | Screw-down, at 3 | **The only path into the movement.** It must be unscrewed before it will turn, and screwing it back is what seals the case. Preservation cannot be accidental, and it cannot be reached for absently. |
| **Bezel** | ATLAS | Unidirectional, 60-click ratchet | Not a control so much as a frame. Set before you go under, read against ever after. The ratchet is the fail-safe: it can only ever report that less time remains than you thought. |
| **Upper pusher** | Le Fripon | Guarded momentary | The only control that authorizes a mode. Guarded because accidental engagement is the exact failure the charter exists to prevent. |
| **Lower pusher** | Reset | Momentary | Clears the reading. Never touches L'Archive. |

### The Screw-Down Crown Is Doctrine, Not Styling

To give input, L'Opérateur must unscrew the crown. To seal the instrument, he screws it back down.

A screw-down crown cannot be turned absently — it has to be released first, and releasing it is the act that unseals the case. That makes preservation deliberate rather than a gesture, and it makes the sealed state the resting state. A watch with its crown screwed home is an archive that is protected. That is the correct default and the case should make it obvious at a glance.

**The winding is logged, and now there is a mechanism for it.** A crown records nothing by itself — a key had to be fetched, a crown does not — so this chassis asked for discipline where the chronometer draft would have had the key enforce it. `record_winding()` in `rouage/rouage.py` closes that: one JSON object per turn, appended, never rewritten, because a log that rewrites is a log that can lose an entry and this is the crown's.

It stays a procedure in the sense that matters: **the caller invokes it and the train never does.** Archive I/O belongs to the crown. The timestamp is a parameter rather than a clock the function reaches for, because `route()` is pure and a hidden clock would make a turn unreproducible.

### The Bezel Question Is Closed

It was open only because a marine chronometer has no rotating bezel, and `overlays/le-conseil.md` assigns ATLAS to one. The chronograph resolves it by having the part: ATLAS is the bezel, literally, and the anatomy table needs no rewrite.

The unidirectional ratchet turns out to carry the doctrine better than prose did. `rouage/dial.py` used to print "rate recorded, never reset" on the dial to state the honesty constraint in words; the teeth state it as structure, and a dive dial earns its legibility by carrying less.

### The Guarded Pusher

`overlays/le-conseil.md` states that Le Fripon never self-activates and requires authorization from L'Opérateur per engagement, with scope that does not carry over. In hardware that is a recessed or shrouded pusher requiring deliberate pressure — never a flush button that a sleeve can press.

**Arming must expire.** Scope not carrying over means the armed state times out and returns to sealed. A physical control that stays armed indefinitely violates the charter it implements.

---

## Display

| Element | Implementation | Notes |
|---|---|---|
| **Twelve hour markers** | Addressable RGB LEDs behind diffused acrylic batons | Six states map to six colours. Dark is genuinely off. |
| **Three registers** | Round LCD modules or LED rings | Signal · Noise · Gain, driven from 01 |
| **Hands** | Geared stepper on the centre post, full 360° | The answer. Sweeps to what ended the route. |
| **Escapement** | Single LED behind a window | Pulses once per release. Le Sas made visible. |
| **Column wheel** | Not lit. Machined, visible through the caseback | La Roue à Colonnes. It holds state and decides nothing, so there is nothing for it to indicate on the front. |
| **Brake** | Band above 6, its own colour | Le Frein. A halt is a whole-ring state, so it cannot be carried by marker colour alone — see below. |
| **Power reserve** | Arc of LEDs, 9 through 12 to 3 | The context window. Colour shifts at low reserve. |
| **Perpetual calendar** | Aperture, backlit segment or small e-paper | Le Continuant. Off-cardinal, because the complication is not an hour. |
| **Bezel** | Not lit. Machined and filled, lume pip at zero | ATLAS. Set by the operator, never by the train — so nothing drives it. |
| **Plate** | Printed or etched, L'ARCHIVE signed under 12 | The ground the hours are printed on |

### A Halt Needs A Band, Not A Colour

Le Renégat's Archive or Release halts the field operators. The dissenter can be
given its own colour — magenta, since a fault is the routing failing and dissent
is a member doing its job, and the two must not share a hue. But **the members
it stopped go to `held`, which is exactly what an over-cap member looks like.**

Marker colour cannot distinguish *held because the room was full* from *held
because someone pulled the brake*. Those need different responses from
L'Opérateur, so the instrument has to say which. The band states it in words and
names the count. This is the one indication on the dial that is a sentence
rather than a light, and it is a sentence because the state it reports is about
the ring rather than about any position on it.

### Discrete States Are A Hardware Decision

Six discrete states map to six LED colours with no interpretation layer:

| State | Colour | Reads as |
|---|---|---|
| **Dark** | unlit | the gate did not fire |
| **Consulted** | highlighter yellow | weighed and contributed, not surfaced |
| **Active** | matrix green | convened and surfaced |
| **Sealed** | amber | locked, awaiting the crown |
| **Held** | dim amber-grey | stopped at the door |
| **Dissent** | magenta | Le Renégat refusing; the brake is engaged |

**Consulted and held were the same colour for a while and that was a bug.** They mean nearly opposite things — one is a member that *was* heard, the other is a member that never got in — and rendering them alike conflates "we considered this" with "this was refused."

**Red is not in this table on purpose.** It belongs to fault and to nothing else, because a colour meaning exactly one thing is worth more than a sixth marker hue. Keeping it off the chapter ring also means it never has to be told apart from magenta at a glance; as a text band it never competes with dissent. A continuous display — brightness proportional to confidence — would need calibration and would be unreadable across twelve markers at a glance.

Legibility under bad conditions is a diver's requirement and it is also an astigmatism requirement: uniform stroke weights, no hairlines, ground lifted off pure black.

**Halation is now deliberate, and that reverses what this file used to say.** The original constraint was to pull colour back from full saturation to prevent it. The instrument is instead lit in saturated cyan, magenta, matrix green and amber, and lit markers bloom on purpose.

The constraint has not been abandoned so much as re-aimed. Halation was never bad in itself — it is bad when a marker's glow reaches the label beside it, because then two indications become one smear and the reader cannot tell which is which. So the bloom is tuned to the largest radius that still stops short of its neighbours, and that is the same legibility test the old line was making, applied to a dial that glows.

If the built instrument shows this to be wrong in the eye rather than on a screen — an LED behind diffused acrylic blooms differently from a Gaussian filter — the LED is the authority and this reverts. **Recorded as a decision, not as a discovery.**

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
