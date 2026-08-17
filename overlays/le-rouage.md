# LE ROUAGE

## The Going Train

**Function:** Carries force from the barrel to the escapement, and distributes the regulated result to the registers and the hands.
**Class:** Component. Not a member, not a mode, not a voice.
**Position:** Both sides of Le Sas. Before it, the train delivers. After it, the motion works distribute.
**Status:** **Partially built.** The deterministic train runs in `rouage/`. The barrel boundary is unresolved.

Le Rouage is the linkage. Every part of Le Conseil connects to every other part through it, and nothing reaches Le Sas except by way of the train.

Its defining property is the one that makes the whole instrument trustworthy:

**The train decides nothing.**

Fixed ratios. Deterministic transmission. A wheel that made choices would destroy the timekeeping, and a router that reasoned about content would be a second, ungoverned judge sitting outside the gate structure this repository exists to define.

---

## Current State

**Half of this component exists in code.** See `rouage/`.

Every activation block turns out to have two halves. The quoted invocation phrases — `"Le Limier"`, `"the bloodhound"` — are matchable, and the train matches them. The automatic conditions beneath them — *"an artifact shows modification whose cause is unknown"* — are not matchable without reading for meaning, which the prohibitions below forbid the train from doing.

So the built train handles named invocation, precedence, metering, the seal, and the trace. The automatic half necessarily runs in the barrel, and the honest arrangement is that **the barrel proposes and the train disposes**: a proposal still passes through ordering, the cap, and the Fripon seal, all enforced in code the barrel cannot reach around. That is what keeps *the train decides nothing* true even though something upstream of it did.

The admission policy for those proposals is undecided and is L'Opérateur's call. Until it is decided, the automatic half of every gate remains a model reading markdown and cooperating — which works, and is not yet a mechanism.

---

## The Cycle

One turn, in order. No stage is skipped and no stage is reordered.

```text
1  WIND      Le Sauvegarder admits the input. Nothing enters otherwise.
2  EVALUATE  Read every OPERATIONAL CORE activation block. Match or no-match.
3  ORDER     Apply the precedence ladder from overlays/le-conseil.md.
4  METER     Hand the candidate set to Le Sas for cap enforcement.
5  LOAD      Load the cores of admitted modes. Cores only, never doctrine.
6  COLLECT   Gather each mode's output against its declared output contract.
7  TIER      Hand to Le Sceptique (01). Nothing proceeds untiered.
8  RELEASE   Hand to Le Sas. It admits or holds.
9  DISTRIBUTE Drive the three registers and the hands from what was released.
10 RECORD    Return to Le Sauvegarder. Every passage is written down.
```

Steps 1–4 are the going train. Steps 9–10 are the motion works. Le Sas sits between them and is the only stage permitted to refuse.

---

## Ratios

The train's ratios are fixed, declared, and inspectable. They are not tuned per turn and not adjusted by the barrel.

| Ratio | Value | Source |
|---|---|---|
| Panel cap | 2–4 modes | `le-conseil.md` |
| Always-engaged | Le Sceptique (01) | not counted against cap |
| Never self-engaging | Le Fripon (05) | requires L'Opérateur per engagement |
| Precedence | Sauvegarder → Vigile → Sceptique → Renégat → relevance | `le-conseil.md` |
| Load granularity | `OPERATIONAL CORE` only | `le-conseil.md` |
| Halting verdicts | Renégat: Archive, Release | field operators stand down |

A change to any ratio is a change to this file and to `le-conseil.md`, committed. Never an in-flight adjustment.

---

## Prohibitions

- **No interpretation.** The train matches gate conditions. It does not assess whether a mode *ought* to fire beyond what its activation block states.
- **No content evaluation.** Tiering belongs to Le Sceptique, admission to Le Sas. The train touches neither.
- **No reordering by preference.** Precedence is declared. A train that resequenced by inclination would silently become the judge.
- **No memory between turns.** A train that accumulated state would develop preferences, and preferences are judgement.
- **No skipping stages.** Not for brevity, not for speed, not because a turn looks trivial. A trivial turn engages no modes, which is different from bypassing the cycle.
- **No silent truncation.** If the candidate set exceeds the cap, that is reported by Le Sas, not quietly trimmed.
- **No loading doctrine at runtime.** Cores only. The `DOCTRINE` sections are for authoring.

---

## Failure Reporting

The train reports on itself and on nothing else.

- **No match.** No gate fired. The common case. Answer directly, engage no one, report nothing.
- **Over-cap.** More candidates than the ratio permits. Hand to Le Sas; it reports the count.
- **Full ring.** Every hour matched. A discrimination failure in the gates, not a climax. Report as a defect.
- **Untiered.** Output reached step 8 without passing step 7. Return it; do not pass it.
- **Reserve low.** The barrel is running down. Stop cleanly, record state, hand off. Do not run the reserve to zero mid-cycle.

---

## Implementation Notes

For whoever builds this — including a future barrel.

- Gate evaluation should be cheap and separable from generation. Reading thirteen activation blocks is not a reasoning task; it is matching.
- The cycle is the same whether the barrel is a hosted frontier model or a local open-weight one. That portability is the point of specifying it here rather than in a prompt.
- Determinism is testable. The same input and the same archive state must select the same modes. If it does not, the train is reasoning, and it should not be.
- Every stage boundary is an observation point. A routing trace — which gates fired, what was held, at what tier — is what makes `absence is signal` verifiable rather than asserted, and it is what the dial displays.
- The dial is not the instrument. It shows the train's state. It must never show a state the train did not produce.

---

**The barrel supplies force. Le Rouage carries it. Le Sas releases it. The hands indicate.**

**Nothing in that sentence decides anything. That is why L'Opérateur can.**
