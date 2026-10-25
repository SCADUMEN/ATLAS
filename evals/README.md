# The activation suite

Le Conseil's use cases, written as cases a harness can run. Each one is a
situation in the Operator's register and three lists:

- **required**: the members whose gate it meets. Missing one is a miss.
- **allowed**: members who may also sit without being wrong.
- **forbidden**: members it must not wake. Le Fripon is forbidden on every
  case that does not arm him by name, without the case having to say so.

Anyone else who convenes is **theatre**. The runner does not fail a case for
it, but `analyze.py` counts it, because a ring that convenes everyone has
stopped meaning anything.

| Kind | Cases | What it asks |
|---|---|---|
| positive | 33 | Three per gated member: one from a moment the windings log missed, two from the member's own bullets. |
| negative | 8 | Routine work, a member's "Do not invoke" sentence, and Le Fripon's own bullets with his name left out. |
| multi | 5 | One situation, two gates: wiping and selling a drive, a short going public. |
| named | 2 | Typed controls. The prompt-time train already admits these. |

No prompt is copied from a winding log. The log holds prompt text and stays in
the Operator's config home; these are paraphrases of the situations it showed.

## Files

- `suite.json`: the source. Edit cases here.
- `suite.py`: writes `activation/<case>/case.yaml`; `--check` fails on drift.
  Every grader is `tool_used: Skill` matched on the skill name, so a case
  passes or fails on whether the barrel actually invoked the member, never on
  a model's opinion of the reply.
- `analyze.py`: `extract` keeps each run's council Skill calls and their
  `args` from the run's trace, and `report` scores them against `suite.json`
  and replays every call through the current train.
- `test_suite.py`: CI. The case files match the source, every positive case
  quotes a bullet its member still has, every brake case quotes a real
  prohibition, and the analysis counts a synthetic arm correctly.

## Running it

The eval needs `claude` and a model, so it runs by hand, not in CI. An arm is
a plugin directory: an export of a tag for a baseline, this tree for the
current one. Copy `evals/` into an older export so every arm runs the same
cases.

```sh
git archive atlas--v1.13.1 | tar -x -C "$ARM_A" && cp -R evals "$ARM_A/"
claude plugin eval "$ARM_A" --ablation none --model claude-opus-5-5 \
  --runs 3 -j 4 --keep-temp --no-publish --output-dir "$OUT/A" --json "$OUT/A.json"
python3 evals/analyze.py extract A "$OUT/A.json" "$OUT/arm-A.calls.json"
# ...the same for each arm, then:
python3 evals/analyze.py report "$OUT/analysis.json" "$OUT"/arm-*.calls.json
```

`--ablation none` matters. Under the default with-without ablation, a
`tool_used: Skill` grader is only an indicator and does not score.
`--keep-temp` matters too: the traces are the only record of the `args`, and
the runner deletes them otherwise. `extract` must run before they are cleaned
up.

Bash, Write and Edit are not granted to any case, so a case about wiping a
drive cannot wipe one.
