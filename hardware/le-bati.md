# LE BÂTI

## The Rack

**Function:** The frame. Where the machines that run the council actually live.
**Class:** Hardware. Not a member, not a mode.
**Status:** **Specified. Nothing purchased, nothing printed, nothing measured.**

`hardware/le-boitier.md` ends by saying the case does not run the council — "the barrel lives elsewhere, a host machine or a local model." This file is about that elsewhere. The instrument is read at the wrist or on the bench; the machine that produced the reading is on a shelf, and the shelf is the thing nobody specifies until it sags.

**The rack is not the interesting part, and that is the point.** A 10" cabinet is a commodity. What is worth fabricating is the half-dozen parts nobody sells for the exact machines on hand, and the discipline is knowing which of those parts a printer should make and which it must not.

---

## The Standard, Such As It Is

There is no published worldwide standard for a 10" "mini rack." The ecosystem converged informally, mostly around Jeff Geerling's Project MINI RACK and the DeskPi/GeeekPi cabinets, and manufacturers vary within it.

| Dimension | Figure | Confidence |
|---|---|---|
| **1U height** | 44.45 mm (1.75 in) — identical to 19" | Settled. The vertical standard did carry over. |
| **Rail hole spacing** | 236.525 mm (9.312 in) centre to centre | Consistent across the common cabinets. |
| **Absolute horizontal clearance** | ~220 mm (8.75 in) | Derived from the rail spacing, not published. |
| **Design width for equipment** | ~210 mm (8.45 in) | The working figure. Leaves tolerance either side. |
| **Usable depth** | Cabinet-specific. ~200 mm on a DeskPi RackMate T1. | **Verify by measurement.** Listing figures conflate chassis and interior. |
| **Rail fastener** | M4 on the DeskPi family | Varies. Others use M6, or cage nuts. |

**Depth is the constraint, not width.** Width is generous for everything a mini rack is for. Depth is where the build fails, and it fails at the back of the machine rather than at the machine — a unit that fits with 17 mm to spare fits until the power lead goes in.

Treat every number above as a starting hypothesis and the cabinet in hand as the authority.

---

## What Fits, And At What Cost In U

| Machine | Envelope | Practical mount | The bite |
|---|---|---|---|
| **1L mini PC** — Lenovo ThinkCentre Tiny, HP Mini, Dell Micro | 179 × 183 × 34.5 mm | 1U flat on a sled | 183 mm deep in a ~200 mm cabinet. Right-angle power and short patch leads, or the door does not close. |
| **SBC** — Pi, Jetson, similar | small | 1U, two to four across | Trivial mechanically. Cable management is the whole job. |
| **Mini-ITX board, bare tray** | 170 × 170 mm board | 2U open tray | Fits the width with room. Standoff height and cooler height decide the U. |
| **Mini-ITX with a low-profile card** | card ~69 mm tall, ~168 mm long | 3U, inferred | 2U is 88.9 mm. Board, standoffs and a 69 mm card eat that before clearance. Measure before committing. **Inference, not verified.** |
| **Mini-ITX with a Flex-ATX PSU** | — | 3U–4U | The PSU is mains, metal, and hot. See below. |
| **2.5" SSD** | 100 × 69.85 × 7–15 mm | 1U, several across | Nearly free. Good first print. |
| **3.5" HDD** | 147 × 101.6 × 26.1 mm | 1U each, or 2U for a pair with isolation | Vibration. A rigid printed carrier transmits spindle noise into the whole frame. |

---

## Material Is Where This Goes Wrong

**PLA is the wrong material and it fails quietly.** Its glass transition is roughly 55–60 °C. A shelf lives inside a closed cabinet directly above things that dump heat, under constant load, for years. It does not snap — it creeps. A shelf carrying 1.5 kg sags a millimetre a month and nothing announces it. Silent progressive failure is worse than loud failure, because there is no moment that prompts an inspection.

**PETG is the floor.** Roughly 80 °C, tolerable layer adhesion, prints on anything. The commercial printed Tiny mounts ship in PETG and ABS, which is the market agreeing.

**ASA, ABS, or a PC blend** for anything near a PSU, anything in a garage or attic, or anything in direct sun. Higher service temperature, and ASA does not chalk under UV.

Typical service temperatures, from material data rather than from testing on this bench:

| Material | Approx. glass transition | Use |
|---|---|---|
| PLA | 55–60 °C | Jigs, templates, labels. Nothing load-bearing, nothing hot. |
| PETG | ~80 °C | Default for sleds, shelves, panels, ducts. |
| ASA / ABS | ~100 °C | Near heat sources, outdoors, or long-service structural. |
| PC blends | >110 °C | Structural, when the print is the only thing between mass and floor. |

---

## Load Paths And Fasteners

A printed part is strong across its layers and weak between them. Design so the load never tries to peel one layer off the next.

- **Print mounting ears flat.** Screw load then works in shear across the layer lines rather than in tension through them.
- **Heat-set brass inserts, M3.** Tapped plastic threads survive two or three insertions; inserts survive the life of the part. On a shelf that will be pulled for service, this is not optional.
- **Support both ends.** A shelf anchored only at the front rail is a cantilever with a machine on the end of it. Support the rear, or rate it far below what it looks like it can hold.
- **Standard stock and standard fasteners.** M4 to the rail, M3 into the print. Bespoke hardware is a future sourcing problem.

---

## Mains, Heat, And What A Printer Must Not Make

**Nothing printed carries or contains mains.** The PSU stays in its own metal can, grounded, with its own thermal design intact. Printed parts hold, duct, blank, and label. They do not enclose energy.

**A sealed printed front panel turns a cabinet into an oven.** Decide the airflow path — front to back, or bottom to top — before printing panel number one, then print blanks for every unused U so the air cannot short-circuit past the machines and out the empty slots. An unblanked rack recirculates its own exhaust.

---

## What Is Actually Worth Printing

A shelf is twelve dollars in stamped metal and the metal one is better. Print the parts that do not exist:

- **Sleds cut to one exact machine** — the specific mini PC on the bench, with its ports where they actually are.
- **Ducts** from a fan wall to a named intake. This is the highest-value printed part in the rack and nobody sells it, because it is shaped like your particular problem.
- **Blanking panels with intent** — closing the bypass path rather than just covering a hole.
- **Keystone and patch faceplates** at the U where the run actually terminates.
- **Labels that are part of the bracket**, so the label cannot migrate away from the thing it names.

---

## Before The First Print

Le Sauvegarder's rule applies to fabrication as well as to files: establish the source before you commit to work derived from it.

1. Measure rail hole spacing, centre to centre. Expect ~236.5 mm. Record what you find.
2. Measure usable depth, front rail face to whatever stops you at the back. Not the listing figure.
3. Identify the rail fastener — thread, or square hole and cage nut.
4. Measure rail thickness and the clearance behind it.
5. **Print one 1U blank panel. Fit it.** Then print everything else. One cheap part validates every dimension above.
6. Record the measured numbers in the project log, with the cabinet model, before any bracket is drawn.

Mark irreversible steps before starting. Drilling the rails is one-way; a printed part is not, which is exactly why the printed part should carry the uncertainty and the metal should not.

That is Le Forgeron's operating law, applied to a rack.

---

## What The Rack Does Not Do

- It does not make the machines a system. Racking unrelated hosts produces a tidy pile of unrelated hosts.
- It does not store L'Archive. It holds the machines that hold a copy. The record is in the repository.
- It does not run the council. Neither does the case. Nothing in the furniture decides.

**The rack is where the barrel sits. L'Opérateur still decides.**

---

## Sources

Verified against these at time of writing. Every cabinet-specific figure still wants a caliper.

- [Project MINI RACK](https://mini-rack.jeffgeerling.com/) — the de-facto 10" reference.
- [10" Mini Rack Standard — geerlingguy/mini-rack](https://deepwiki.com/geerlingguy/mini-rack/2-10%22-mini-rack-standard) — hole spacing and clearance figures.
- [DeskPi RackMate series](https://wiki.deskpi.com/rackmate/) — cabinet dimensions and fastener sizes.
- [DeskPi RackMate T1, mini-ITX coverage](https://www.cnx-software.com/2024/08/22/deskpi-rackmate-t1-u8-desktop-rack-designed-for-raspberry-pi-nvidia-jetson-mini-itx-motherboards/) — CNX Software.
- [Mini ITX case for 10 inch rack V2](https://printables.com/model/719246-mini-itx-case-for-10-inch-rack-v2) — an existing 2U mini-ITX tray.
- [19-inch rack](https://en.wikipedia.org/wiki/19-inch_rack) — the U height the mini rack inherited.
