// LE CADRAN, as a face, assembled in the browser.
//
// Not a port of cadran_face.py. The geometry - case, majors, numerals,
// engraving, and every path a hand can take - arrives as K, the kit
// face_kit() exports, so nothing here can draw a circle differently. What is
// left is what a trace changes: the marker beside each numeral, the two bands,
// which hands go down and in what order, and the footer. That assembly is the
// one thing written twice, and test_face_js.py holds it to face()'s bytes.

// textwrap.wrap(text, width, subsequent_indent=indent), for the one shape the
// footer gives it: words separated by runs of spaces, none longer than a line.
// Whitespace is dropped at the start of every line after the first and at the
// end of every line, as Python's drop_whitespace does. A no-break space is not
// whitespace there either, which is what keeps "Le" beside its name.
function wrap(text, width, indent) {
  const chunks = text.split(/( +)/).filter((c) => c !== "").reverse();
  const lines = [];
  while (chunks.length) {
    const lead = lines.length ? indent : "";
    const room = width - lead.length;
    if (lines.length && chunks[chunks.length - 1].trim() === "") chunks.pop();
    const cur = [];
    let len = 0;
    while (chunks.length && len + chunks[chunks.length - 1].length <= room) {
      const c = chunks.pop();
      cur.push(c);
      len += c.length;
    }
    if (!cur.length && chunks.length) cur.push(chunks.pop()); // over-long word
    if (cur.length && cur[cur.length - 1].trim() === "") cur.pop();
    if (cur.length) lines.push(lead + cur.join(""));
  }
  return lines;
}

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// cadran_face.rim(): a label set in a register's rim, any odd cell to the right.
const rim = (label, inner) => {
  const n = [...label].length, left = Math.floor((inner - n) / 2);
  return "─".repeat(left) + label + "─".repeat(inner - n - left);
};

// cadran_face.readings(): the three registers, counted off the turn's seats.
// Le Sceptique is standing and left out, as he is left out of the cap.
export function readings(K, t) {
  const seats = t.positions.filter((p) => p.position !== "01" && p.state !== "dark");
  const noise = seats.filter((p) => p.state === "held").length;
  return { signal: seats.length - noise, noise, gain: seats.length,
           cap: Math.max(K.cap, t.capAuthorized || 0) };
}

export function face(K, t) {
  const cells = K.cells.map((row) => row.map((c) => [c[0], c[1], ""]));
  const locked = K.locked.map((row) => row.slice());
  const put = (r, c, ch, hex, lock = false, force = false, bg = "") => {
    if (r < 0 || r >= K.rows || c < 0 || c >= K.inner) return;
    if (locked[r][c] && !force) return;
    cells[r][c] = [ch, hex, bg];
    if (lock) locked[r][c] = 1;
  };
  const text = (r, c, s, hex = "", bg = "") =>
    [...s].forEach((ch, i) => put(r, c + i, ch, hex, true, true, bg));
  const centred = (r, s, hex = "") =>
    text(r, Math.floor((K.inner - [...s].length) / 2), s, hex);

  const seat = Object.fromEntries(t.positions.map((p) => [p.position, p]));
  const stateOf = (pos) => (seat[pos] ? seat[pos].state : "dark");

  for (const [pos, [r, c]] of Object.entries(K.markers))
    text(r, c, K.marker[stateOf(pos)], K.color[stateOf(pos)]);

  for (const pos of K.hours) {
    const [r, c] = K.markers[pos];
    const s = stateOf(pos);
    if (s === "dark") text(r, c - 2, pos, K.color.dark);
    else text(r, c - 3, ` ${pos}${K.marker[s]} `, K.plateInk, K.color[s]);
  }

  const reading = readings(K, t);
  for (const [key, [r, c]] of Object.entries(K.registers)) {
    const n = reading[key];
    const over = n > reading.cap;
    const hex = over ? K.fault : K.registerColor[key];
    for (let i = 0; i < K.cap; i++)
      put(r + 1, c + 1 + 2 * i, K.pip[i < n ? 0 : 1], i < n ? hex : K.color.dark);
    [...rim(over ? ` ${n}/${reading.cap} ` : ` ${n} `, K.registerInner)].forEach((ch, i) =>
      put(r + 2, c + 1 + i, ch, "─ ".includes(ch) ? K.registerRim : hex));
  }

  // The browser train has no column wheel, so nothing is ever halted here;
  // the band is still drawn from the trace when a trace carries it.
  const held = (t.halted || []).length;
  if (held) centred(K.bandRows.brake, `${K.owners.brake} · ${held} HELD`, K.color.dissent);
  const released = t.stages.some((s) => s.startsWith("RELEASE"));
  const band = t.failures.length ? "FAULT" : released ? "RELEASED" : "NO RELEASE";
  centred(K.bandRows.escapement, `${K.owners.escapement} · ${band}`,
          t.failures.length ? K.fault : "");

  const hour = t.admitted.length ? t.admitted[0] : null;
  const minute = t.routeEnd;
  const split = t.routeAimed !== t.routeEnd ? t.routeAimed : null;
  const at = { split, minute, hour };
  for (const [kind, hex] of K.handOrder) {
    const pos = at[kind];
    if (!pos || !/^\d+$/.test(pos)) continue;
    for (const [r, c, ch] of K.hands[kind][pos]) put(r, c, ch, hex);
  }
  text(K.cr, K.cc, K.pivot);

  // Every glyph the face can hold is one column wide, so code points are the
  // measure; cadran_face.py's dwidth() guard is what proves that stays true.
  const framed = (plain, painted) =>
    `│ ${painted}${" ".repeat(K.inner - [...plain].length)} │`;
  const row = (r) => {
    let n = cells[r].length;
    while (n && cells[r][n - 1][0] === " ") n -= 1;
    const plain = cells[r].slice(0, n).map((c) => c[0]).join("");
    // A run is one style. A seat's plate is bold black on its state's
    // colour, written as dial.span_style() writes it for the sheet.
    let html = "", run = "", style = "";
    const flush = () => {
      if (run) html += style ? `<span style="${style}">${esc(run)}</span>` : esc(run);
      run = "";
    };
    for (const [ch, h, bg] of cells[r].slice(0, n)) {
      const code = bg ? `color:${h};background:${bg};font-weight:bold`
        : ch === " " || !h ? "" : `color:${h}`;
      if (code !== style) { flush(); style = code; }
      run += ch;
    }
    flush();
    return [plain, html];
  };

  const plainLines = [], htmlLines = [];
  const add = (plain, html = esc(plain)) => { plainLines.push(plain); htmlLines.push(html); };
  const top = `┌─ ${K.title} ` + "─".repeat(Math.max(K.width - [...K.title].length - 5, 1)) + "┐";
  add(top);
  for (let r = 0; r < K.rows; r++) {
    const [p, h] = row(r);
    add(framed(p, p), framed(p, h));
  }
  add(framed("", ""));

  const handName = (pos) =>
    pos ? `${pos} ${seat[pos] ? seat[pos].name : ""}`.trim() : "—";
  const lit = K.hours.filter((pos) => stateOf(pos) !== "dark")
    .map((pos) => `${K.marker[stateOf(pos)]} ${pos} ${K.names[pos]}`);
  if (stateOf("crown") !== "dark") lit.push(`${K.marker[stateOf("crown")]} crown`);
  const nbsp = " ";
  const seats = lit.map((e) => e.replaceAll(" ", nbsp)).join("  ") || "none lit";
  const footer = [
    ...wrap("SEATS  " + seats, K.inner, " ".repeat(7)).map((l) => l.replaceAll(nbsp, " ")),
    `HANDS  hour → ${handName(hour)}   minute → ${handName(minute)}`,
  ];
  if (split) footer.push(`       split → ${handName(split)} (aimed)`);
  footer.push(K.undriven);
  for (const l of footer) add(framed(l, l));
  add("└" + "─".repeat(K.width - 2) + "┘");
  add(` INPUT  "${t.utterance}"   armed ${t.armed || "—"}`);
  return { text: plainLines.join("\n"), html: htmlLines.join("\n") };
}
