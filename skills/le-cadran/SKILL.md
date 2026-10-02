---
name: le-cadran
description: LE CADRAN — the dial, in the terminal. Routes one utterance through Le Rouage and prints the panel the train produced. Invoke only when the Operator types /atlas:le-cadran.
argument-hint: <utterance> [--face] [--tier "Le X"] [--verdict "Le X:Verdict"] [--arm "Le Fripon"]
disable-model-invocation: true
---

# /atlas:le-cadran

Hand-written, not generated. Le Cadran is a display, not a council member, so it
has no subroutine source and `bin/atlas-skills` does not manage this file.

## Run

Run exactly this, passing the Operator's arguments through as separate shell
words. Quote the utterance as one argument; pass any flags after it unchanged.

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/rouage/cadran_ascii.py" <utterance> [flags]
```

The arguments were: `$ARGUMENTS`

`--face` draws the dial itself (`rouage/cadran_face.py`) instead of the table.
Both read the same trace; the face is the object, the table is the record.

With no arguments, run it with no utterance. The script then routes its own
built-in demonstration turn, and the panel's INPUT line names it. Say that it
is the demonstration turn, not the Operator's.

## Reproduce

Print the script's stdout **verbatim** inside a `text` fence. Then stop.

- **Never draw the dial yourself.** Not from memory, not to fix an alignment,
  not to fill in a run that failed. `hardware/le-boitier.md`: the display never
  shows a state the router did not produce. A panel the model composed is a
  state the router did not produce.
- **Never relight what is dark or explain away what is undriven.** UNDRIVEN on
  the face is the instrument being honest about what the train cannot drive.
- If the script fails, show its stderr and say it failed. No panel.
- One sentence after the fence at most, and only to name a fault the panel
  itself reports. The panel is the answer.

## Le Fripon

`--arm "Le Fripon"` is the only way this skill unseals him, and only because the
Operator typed it. Never add it. This skill cannot be invoked by the model, so
the arm flag can only ever arrive from the Operator's own command line.
