#!/usr/bin/env node
// LE CADRAN, live in the terminal.
//
// Not a fourth face. The geometry arrives as K from face_kit(), the routing as
// train.js, the assembly as face.js - all three already held to cadran_face.py
// by test_face_js.py and test_conformance.py. This file only watches the
// crown's log and puts what face() returns on the screen.
//
// Bound by hardware/le-boitier.md - The Honesty Constraint: the display never
// shows a state the router did not produce. So there is no idle motion. The
// dial moves when, and only when, a winding lands in windings.jsonl, and every
// frame of that motion is face() of a prefix of the real trace - never a hand
// drawn somewhere the train did not point it.
//
//     node rouage/tui/cadran.mjs            follow the live log
//     node rouage/tui/cadran.mjs --log F    follow another log

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Box, Text, render, useApp, useInput, useStdin } from "ink";

import { route } from "../train.js";
import { face } from "../face.js";

const h = React.createElement;
const ROUAGE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argLog = process.argv.indexOf("--log");
const LOG = argLog > 0 ? process.argv[argLog + 1]
  : path.join(os.homedir(), ".claude", "atlas", "windings.jsonl");

// How long each frame of a winding stays up. Long enough to read the order the
// train worked in, short enough that a turn settles before the next one lands.
const FRAME_MS = 90;

// D and K are generated from the markdown at launch, every launch, so a
// doctrine edit reaches this dial the next time it starts. Nothing is cached
// on disk to fall behind.
function loadDoctrine() {
  const py = [
    "import emit, json",
    "from cadran_face import face_kit",
    "print('{\"D\":' + emit.as_json() + ',\"K\":' + json.dumps(face_kit(), ensure_ascii=False) + '}')",
  ].join("\n");
  const out = spawnSync("python3", ["-c", py], { cwd: ROUAGE, encoding: "utf8" });
  if (out.status !== 0) throw new Error(out.stderr || "python3 failed to emit the doctrine");
  return JSON.parse(out.stdout);
}

function readWindings() {
  try {
    return fs.readFileSync(LOG, "utf8").split("\n").filter(Boolean)
      .map((l) => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);
  } catch {
    return [];
  }
}

// Route a recorded winding again. A settle entry carries the barrel's
// proposals; a prompt entry has none. The record is the authority: if today's
// doctrine admits someone different, the face says so rather than pass the
// replay off as what happened.
function replay(D, w) {
  const t = route(D, w.utterance || "", w.armed || null, null,
                  { proposals: w.proposals || null });
  const recorded = (w.admitted || []).join(",");
  const replayed = t.admitted.join(",");
  return { t, drift: recorded === replayed ? null : { recorded, replayed } };
}

// The order the dial comes up in, as a list of traces, each a prefix of t.
// The last one must be t itself: the dial always comes to rest on the real
// trace. Every one is drawn by face(), so a frame can only show seats, hands
// and bands the train actually produced for this turn.
//
// t.positions  seats in precedence order, each {position, name, state}
// t.stages     WIND, EVALUATE, ... RELEASE - the escapement band reads these
// t.admitted   the hour hand points at admitted[0]
// t.routeEnd / t.routeAimed   the minute and split hands
//
// The reveal is the train first, then who it seated, then where it pointed:
// the stages wind through on a dark dial, the seats light in precedence
// order, and the hands and any fault arrive with the trace itself.
export function frames(t) {
  const dark = { ...t, positions: [], admitted: [], failures: [], halted: [],
                 routeEnd: null, routeAimed: null };
  const seq = t.stages.map((_, i) => ({ ...dark, stages: t.stages.slice(0, i + 1) }));
  const wound = seq.length ? seq[seq.length - 1] : dark;
  t.positions.forEach((_, i) => seq.push({ ...wound, positions: t.positions.slice(0, i + 1) }));
  seq.push(t);
  return seq;
}

// face() hands back HTML spans for the browser; the terminal wants runs.
const ENT = { "&lt;": "<", "&gt;": ">", "&amp;": "&" };
const unesc = (s) => s.replace(/&(lt|gt|amp);/g, (m) => ENT[m]);
// A span carries a colour, and a seat's plate adds a background and bold.
function runs(htmlLine) {
  const out = [];
  const re = /<span style="([^"]*)">(.*?)<\/span>|([^<]+)/g;
  let m;
  while ((m = re.exec(htmlLine))) {
    if (!m[1]) { out.push([unesc(m[3]), {}]); continue; }
    const st = Object.fromEntries(m[1].split(";").map((d) => d.split(":")));
    out.push([unesc(m[2]), { color: st.color, backgroundColor: st.background,
                             bold: st["font-weight"] === "bold" }]);
  }
  return out;
}

function Face({ html }) {
  return h(Box, { flexDirection: "column" },
    html.split("\n").map((line, i) =>
      h(Text, { key: i }, runs(line).map(([s, style], j) =>
        h(Text, { key: j, ...style }, s)))));
}

function Cadran({ D, K }) {
  const { exit } = useApp();
  const { isRawModeSupported } = useStdin();
  const [log, setLog] = useState(() => readWindings());
  const [at, setAt] = useState(() => Math.max(readWindings().length - 1, 0));
  const [frame, setFrame] = useState(null);
  const follow = useRef(true);

  // Watch the crown's log. A new line moves the dial to it when following;
  // stepping back through history stops following until → reaches the end.
  useEffect(() => {
    const tick = () => {
      const next = readWindings();
      setLog((prev) => {
        if (next.length > prev.length && follow.current) setAt(next.length - 1);
        return next.length === prev.length ? prev : next;
      });
    };
    const id = setInterval(tick, 400);
    return () => clearInterval(id);
  }, []);

  const w = log[at];
  // Keyed on the entry, not the object: a reread of the log must not replay
  // the turn already on the dial.
  const played = useMemo(() => (w ? replay(D, w) : null), [at, w && w.when]);

  // Every winding animates: quiet turns too, since a gate that should have
  // fired is only visible if the misses are drawn.
  useEffect(() => {
    if (!played) return;
    const seq = frames(played.t);
    const show = (f) => setFrame({ html: face(K, f).html, stage: f.stages[f.stages.length - 1] });
    let i = 0;
    show(seq[0]);
    const id = setInterval(() => {
      i += 1;
      if (i >= seq.length) return clearInterval(id);
      show(seq[i]);
    }, FRAME_MS);
    return () => clearInterval(id);
  }, [played]);

  useInput((input, key) => {
    if (input === "q" || key.escape) exit();
    if (key.leftArrow) { follow.current = false; setAt((a) => Math.max(a - 1, 0)); }
    if (key.rightArrow) {
      setAt((a) => {
        const n = Math.min(a + 1, log.length - 1);
        if (n === log.length - 1) follow.current = true;
        return n;
      });
    }
  }, { isActive: isRawModeSupported });

  if (!w) {
    return h(Text, { dimColor: true }, `No windings yet in ${LOG}. The dial stays dark until the crown is wound.`);
  }
  // Face plus the two status lines. Shorter than that and the top of the dial
  // is cut off, so say how tall the pane needs to be rather than draw half.
  const need = frame ? frame.html.split("\n").length + 2 : 0;
  const short = process.stdout.rows && process.stdout.rows < need;
  return h(Box, { flexDirection: "column" },
    short ? h(Text, { color: "yellow", wrap: "truncate" },
      ` pane is ${process.stdout.rows} rows; the dial needs ${need}`) : null,
    frame ? h(Face, { html: frame.html }) : null,
    h(Text, { dimColor: true, wrap: "truncate" },
      ` ${w.when}  ${w.kind || "prompt"}  ${at + 1}/${log.length}` +
      `  stage ${frame && frame.stage ? frame.stage : "—"}` +
      `  ${follow.current ? "following" : "history"}  ← → step · q quit`),
    played.drift ? h(Text, { color: "red" },
      ` replay differs from the record: recorded [${played.drift.recorded}]` +
      ` · today's doctrine [${played.drift.replayed}]`) : null);
}

// Run as a program, not when a test imports frames().
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { D, K } = loadDoctrine();
  // The face is taller than most panes. On the main screen Ink can only
  // redraw that by clearing, and every cleared frame lands in scrollback, so
  // the dial runs on the alternate screen and the shell comes back untouched.
  const tty = process.stdout.isTTY;
  if (tty) process.stdout.write("\x1b[?1049h\x1b[H");
  process.on("exit", () => { if (tty) process.stdout.write("\x1b[?1049l"); });
  render(h(Cadran, { D, K }));
}
