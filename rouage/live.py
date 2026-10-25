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
from cadran_face import face_kit
from dial import (CSS, INK, SETTLE_PROPOSAL, SETTLE_UTTERANCE, STATE_INK,
                  dial_svg, esc, load_anatomy)
from rouage import load_ring, route

OUT = Path(__file__).resolve().parent / "cadran-live.html"

APP_CSS = """

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
.console select { font-family: var(--data); font-size: 13px; padding: 9px 10px;
  background: var(--field); border: 1px solid var(--rule); color: var(--ink); }
.console select:focus-visible { outline: 2px solid var(--brass);
  outline-offset: 2px; }
.facefig { margin-top: 10px; }
.facefig .plate { display: flex; justify-content: center; overflow-x: auto; }
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
    chips += ('<button class="chip" data-eg="run Publish" '
              'data-tier="Le Curateur">run Publish &#183; tier Le Curateur</button>')
    # The sheet's Plate 3 turn, so the two pages demonstrate one settle.
    chips += (f'<button class="chip" data-eg="{esc(SETTLE_UTTERANCE)}" '
              f'data-member="{esc(SETTLE_PROPOSAL[0])}" '
              f'data-reason="{esc(SETTLE_PROPOSAL[1])}">a seller shrugged '
              f'&#183; propose {esc(SETTLE_PROPOSAL[0])}</button>')

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
    <input type="text" id="tier" autocomplete="off" spellcheck="false"
           placeholder="tiered: (none)" aria-label="Tiered members">
    <label><input type="checkbox" id="arm"> Arm Le Fripon</label>
  </div>
  <div class="console">
    <select id="member" aria-label="Proposed member">
      <option value="">propose: (no one)</option></select>
    <input type="text" id="reason" autocomplete="off" spellcheck="false"
           placeholder="reason, in your own words" aria-label="Reason">
  </div>
  <p class="hint">The train matches <b>named invocation only</b>. A route needs
  its verb &#8212; <b>run Publish</b>, not &#8220;publish&#8221;. Describing a
  situation fires nothing on its own: that half of every gate is the
  barrel's. In a session the barrel proposes by invoking a member's skill with
  a reason; <b>propose</b> stands in for it here. The reason is admitted in
  its own words, noted beside the bullet it sits nearest, and refused only as
  an inverted gate &#8212; closer to a prohibition than to any activation. Le
  Fripon alone still needs his gate quoted and the crown armed. <b>Tiered</b>
  names who Le Sceptique tiered this turn, comma-separated &#8212; anyone else
  admitted holds at Le Sas. Empty leaves Le Sas transparent.</p>
  <div class="console">{chips}</div>

  <div class="live">
    <figure><div class="plate">{base}</div>
      <figcaption><b>Plate 1</b> &#8212; live. Dark positions are genuinely
      dark: the gate did not fire.</figcaption></figure>
    <div id="readout"></div>
  </div>

  <figure class="facefig"><div class="plate term"><pre id="face"></pre></div>
    <figcaption><b>Plate 2</b> &#8212; the same turn as the terminal face
    <code>bin/atlas-settle</code> draws after it, named and proposed together.
    In a session it is drawn only when the train did more than the standing
    watch. Assembled from <code>face_kit()</code>; <code>test_face_js.py</code>
    holds it to <code>cadran_face.py</code> byte for byte.</figcaption></figure>

  <footer>
    <span>Forgotten Industries &#183; ATLAS &#183; Le Conseil</span>
    <span>A thing documented is a thing not yet lost.</span>
  </footer>
</div>
<script type="module">
const D = {emit.as_json()};
const INK = {json.dumps(INK)};
const STATE_INK = {json.dumps(STATE_INK)};
const K = {json.dumps(face_kit(ring=ring, anatomy=anatomy), ensure_ascii=False, separators=(",", ":"))};
{Path(__file__).resolve().parent.joinpath("train.js").read_text(encoding="utf-8").replace("export ", "")}
{Path(__file__).resolve().parent.joinpath("face.js").read_text(encoding="utf-8").replace("export ", "")}
{Path(__file__).resolve().parent.joinpath("paint.js").read_text(encoding="utf-8")}
</script>
"""


def main() -> None:
    OUT.write_text(page(), encoding="utf-8")
    print(f"wrote {OUT}  ({len(page()) // 1024} KB)")


if __name__ == "__main__":
    main()
