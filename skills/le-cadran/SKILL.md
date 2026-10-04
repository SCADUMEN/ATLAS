---
name: le-cadran
description: LE CADRAN — the watch face, in the terminal. Routes one utterance through Le Rouage and draws the dial the train produced; the seated members then answer. Invoke only when the Operator types /atlas:le-cadran.
argument-hint: <utterance> [--tier "Le X"] [--verdict "Le X:Verdict"] [--arm "Le Fripon"]
disable-model-invocation: true
---

# /atlas:le-cadran

Hand-written, not generated. Le Cadran is a display, not a council member, so it
has no subroutine source and `bin/atlas-skills` does not manage this file.

## Run

Run exactly this, passing the Operator's arguments through as separate shell
words. Quote the utterance as one argument; pass any flags after it unchanged.

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/rouage/cadran_ascii.py" <utterance> --face [flags]
```

The arguments were: `$ARGUMENTS`

**`--color` is for a terminal, not this reply.** It prints ANSI escape codes,
and a `text` fence shows them as literal `[38;5;136m` noise. If the Operator
typed `--color`, leave it off the run here, so the panel comes out plain. After
the answer, give one line they can run themselves to see it in color:
`! python3 "${CLAUDE_PLUGIN_ROOT}/rouage/cadran_ascii.py" "<utterance>" --face [flags]`,
with their utterance and every flag they typed, `--color` included.

Pass `--face` exactly once: add it, or keep the Operator's if they typed it.
A second copy is not consumed as a flag and would be routed as utterance.
Le Cadran is the dial itself (`rouage/cadran_face.py`). The table of the same
trace belongs to `/atlas:le-conseil`: the face is the object, the table is the
record.

With no arguments, run it with no utterance. The script then routes its own
built-in demonstration turn, and the panel's INPUT line names it. Say that it
is the demonstration turn, not the Operator's.

## Reproduce

Print the script's stdout **verbatim** inside a `text` fence. Then answer.

- **Never draw the dial yourself.** Not from memory, not to fix an alignment,
  not to fill in a run that failed. `hardware/le-boitier.md`: the display never
  shows a state the router did not produce. A panel the model composed is a
  state the router did not produce.
- **Never relight what is dark or explain away what is undriven.** UNDRIVEN on
  the face is the instrument being honest about what the train cannot drive.
- If the script fails, show its stderr and say it failed. No panel, no answer.

## Answer

The face shows who was seated; the seated members answer the utterance. The
seats are the members named on the panel's `SEATS` line, and only those.

- **Load each seated member's `OPERATIONAL CORE` and nothing else** from
  `${CLAUDE_PLUGIN_ROOT}/subroutines/<member>.md` (`Le Limier` →
  `le-limier.md`, accents dropped). `overlays/le-conseil.md`: load granularity
  is the operational core.
- **Each seated field member answers under its own name**, as a `###` heading,
  doing its own work on the utterance: Le Limier reconstructs, Le Cartographe
  maps, and so on. Order them by the precedence ladder in
  `overlays/le-conseil.md`, seat number breaking ties.
- **Le Sceptique is the airlock, not a speaker.** He is seated on every turn,
  so he tiers every claim the others make and takes no heading of his own,
  unless the Operator named him or he is the only one seated. Alone, he answers
  the utterance plainly with every claim tiered, and borrows no dark member's
  method.
- **Dark members are silent.** No section, no borrowed voice, no "Le X would
  say". If a member the Operator wanted is dark, the face already says so.
- **Le Renégat's verdict halts the field.** If he is seated and returns Archive
  or Release, the members after him do not answer.
- **The demonstration turn gets no answer.** It is not the Operator's question.

## Le Fripon

`--arm "Le Fripon"` is the only way this skill unseals him, and only because the
Operator typed it. Never add it. This skill cannot be invoked by the model, so
the arm flag can only ever arrive from the Operator's own command line.
