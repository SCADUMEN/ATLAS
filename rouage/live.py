"""The interactive dial: one page, one train in the browser, no third copy.

dial_svg() is 800 lines of geometry and porting it would be a THIRD
implementation with no conformance guard - worse than the trade made for the
train. But the dial is almost entirely invariant: the case, bezel, subdials,
route ring and chapter geometry never change. Only baton colours, member
labels, three hand angles and two bands are trace-driven.

So the SVG is rendered once here, in Python, carrying `data-` hooks on exactly
those elements, and the browser writes only the values its train produced.
Geometry stays in dial.py the way gates stay in doctrine.
"""

from __future__ import annotations

import json
from pathlib import Path

import emit
from dial import CSS, INK, STATE_INK, dial_svg, load_anatomy
from rouage import load_ring, route

OUT = Path(__file__).resolve().parent / "cadran-live.html"

# No landscape gate here, and that is a decision rather than an omission.
#
# The object record gates because it is a technical DRAWING - the plate, the
# record spine and the two-column notes all assume a long edge, and reflowing
# them into a column stops it reading as a drawing at all. This page is a
# TOOL. Its job is an input, a dial and a readout, all of which stack down a
# phone perfectly well, and gating a tool behind a rotation is an obstacle
# rather than a courtesy. Different job, different answer.
#
# The gate's CSS still arrives with the shared stylesheet and matches nothing,
# so it is neutralised below rather than left as dead weight that looks like
# an oversight to the next reader.
APP_CSS = """
.gate { display: none !important; }

.live { display: grid; grid-template-columns: 1fr 330px; gap: 34px;
  align-items: start; }
@media (max-width: 900px) { .live { grid-template-columns: 1fr; } }
.console { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.console input[type=text] { flex: 1 1 320px; font-family: var(--data);
  font-size: 14px; padding: 10px 12px; background: var(--field);
  border: 1px solid var(--rule); color: var(--ink); }
.console input[type=text]:focus-visible { outline: 2px solid var(--brass);
  outline-offset: 2px; }
.console label { font-family: var(--data); font-size: 11px;
  letter-spacing: .12em; text-transform: uppercase; color: var(--dim);
  display: flex; align-items: center; gap: 7px; cursor: pointer; }
.hint { font-family: var(--data); font-size: 10.5px; color: var(--dim);
  letter-spacing: .04em; margin: -6px 0 18px; }
.hint b { color: var(--ink); font-weight: 400; }
.chip { font-family: var(--data); font-size: 10.5px; letter-spacing: .1em;
  text-transform: uppercase; background: var(--field);
  border: 1px solid var(--soft); color: var(--dim); padding: 5px 9px;
  cursor: pointer; }
.chip:hover, .chip:focus-visible { border-color: var(--brass);
  color: var(--ink); outline: none; }
"""


def page() -> str:
    ring = load_ring()
    anatomy = load_anatomy()
    # The base render must contain EVERY driven element, because paint() can
    # move and hide but cannot create. A trace with a route, a split and a
    # divergent precedence emits all three hands and both legends; the browser
    # then hides whichever the real trace does not justify.
    base = dial_svg(route(ring, "run Publish, security check",
                          tiered=["Le Curateur"]), anatomy=anatomy,
                   always_emit_bands=True)
    examples = ["run Publish", "what happened here", "red team my backups",
                "run Harden", "rename this file", "run Publish, security check"]
    chips = "".join(f'<button class="chip" data-eg="{e}">{e}</button>'
                    for e in examples)

    return f"""<title>Le Cadran &#183; Live</title>
<style>{CSS}{APP_CSS}</style>
<div class="sheet">
  <header class="masthead">
    <div class="mark">Forgotten Industries</div>
    <div class="ref">Le Cadran &#183; live &#183; ATLAS / Le Conseil</div>
  </header>
  <div class="motto">Human judgement // Machine collaboration // Contre l'oubli</div>

  <h1 style="font-size:clamp(34px,5vw,50px);margin:0 0 8px">Le Cadran</h1>
  <p class="deck">Type something. The council routes it.</p>

  <div class="console">
    <input type="text" id="utt" autocomplete="off" spellcheck="false"
           placeholder="run Publish" aria-label="Utterance">
    <label><input type="checkbox" id="arm"> Arm Le Fripon</label>
  </div>
  <p class="hint">The train matches <b>named invocation only</b>. A route needs
  its verb &#8212; <b>run Publish</b>, not &#8220;publish&#8221;. Describing a
  situation fires nothing: that half of every gate is the barrel's, and the
  barrel is a person or a model, never this page.</p>
  <div class="console">{chips}</div>

  <div class="live">
    <figure><div class="plate">{base}</div>
      <figcaption><b>Plate 1</b> &#8212; live. Dark positions are genuinely
      dark: the gate did not fire.</figcaption></figure>
    <div id="readout"></div>
  </div>

  <footer>
    <span>Forgotten Industries &#183; ATLAS &#183; Le Conseil</span>
    <span>A thing documented is a thing not yet lost.</span>
  </footer>
</div>
<script type="module">
const D = {emit.as_json()};
const INK = {json.dumps(INK)};
const STATE_INK = {json.dumps(STATE_INK)};
{Path(__file__).resolve().parent.joinpath("train.js").read_text(encoding="utf-8").replace("export ", "")}
{Path(__file__).resolve().parent.joinpath("paint.js").read_text(encoding="utf-8")}
</script>
"""


def main() -> None:
    OUT.write_text(page(), encoding="utf-8")
    print(f"wrote {OUT}  ({len(page()) // 1024} KB)")


if __name__ == "__main__":
    main()
