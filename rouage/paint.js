// Paint a trace onto the dial that dial.py already drew.
//
// This writes values, never geometry. Every element it touches carries a
// data- hook emitted by dial_svg(), so the case, bezel, subdials and chapter
// ring are Python's and stay Python's - there is no second renderer to drift.

const svg = document.querySelector(".plate svg");
const byPos = (sel) => Object.fromEntries(
  [...svg.querySelectorAll(sel)].map((el) => [el.dataset[Object.keys(el.dataset)[0]], el]));

const batons = byPos("[data-baton]");
const names = byPos("[data-name]");
const states = byPos("[data-state]");
const routeLabels = Object.fromEntries(
  [...svg.querySelectorAll("[data-route]")].map((el) => [el.dataset.route, el]));
const legends = Object.fromEntries(
  [...svg.querySelectorAll("[data-legend]")].map((el) => [el.dataset.legend, el]));
const bands = Object.fromEntries(
  [...svg.querySelectorAll("[data-band]")].map((el) => [el.dataset.band, el]));
const hands = Object.fromEntries(
  [...svg.querySelectorAll("[data-hand]")].map((el) => [el.dataset.hand, el]));

const cx = +hands.minute.getAttribute("x1");
const cy = +hands.minute.getAttribute("y1");
const SIZE = 820;

function polar(r, pos) {
  const a = (-90 + (parseFloat(pos) % 12) * 30) * Math.PI / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}

// A legend has to travel with the hand it names, or it sits where the base
// render happened to leave it and labels nothing.
function setHand(name, pos, r, legend, legendR) {
  const el = hands[name];
  const lg = legend ? legends[legend] : null;
  if (!el) return;
  if (!pos) {
    el.setAttribute("opacity", "0");
    if (lg) lg.setAttribute("opacity", "0");
    return;
  }
  const [x, y] = polar(r, pos);
  el.setAttribute("x2", x.toFixed(1));
  el.setAttribute("y2", y.toFixed(1));
  el.setAttribute("opacity", name === "hour" ? "0.92" : "0.9");
  if (lg) {
    const [lx, ly] = polar(legendR, pos);
    lg.setAttribute("x", lx.toFixed(1));
    lg.setAttribute("y", ly.toFixed(1));
    lg.setAttribute("opacity", "0.85");
  }
}

export function paint(t) {
  const seat = Object.fromEntries(t.positions.map((p) => [p.position, p]));

  for (const pos of Object.keys(batons)) {
    const p = seat[pos];
    const lit = p && p.state !== "dark";
    const ink = p ? (STATE_INK[p.state] || INK.dark) : INK.dark;

    const b = batons[pos];
    b.setAttribute("stroke", ink);
    b.setAttribute("stroke-width", lit ? 11 : 8);
    b.setAttribute("opacity", lit ? 1 : 0.8);
    if (lit) b.setAttribute("filter", "url(#glow)"); else b.removeAttribute("filter");

    const n = names[pos];
    n.textContent = p ? p.name : "·";
    n.setAttribute("fill", ink);
    n.setAttribute("opacity", lit ? 1 : 0.55);
    if (lit) n.setAttribute("filter", "url(#glowsoft)"); else n.removeAttribute("filter");

    states[pos].textContent = lit ? `${pos}  ${p.state.toUpperCase()}` : pos;
  }

  for (const [name, el] of Object.entries(routeLabels)) {
    const on = t.route === name;
    el.setAttribute("fill", on ? INK.cyan : INK.dim);
    el.setAttribute("opacity", on ? 1 : 0.62);
    el.setAttribute("font-size", on ? 9 : 8);
  }

  // Same rule the static dial follows: a hand that would rest under another
  // is not drawn, because a hand indicating nothing is a hand that lies.
  // From the precedence-ordered list, never from t.positions - that is sorted
  // by seat for display, so its first entry is the lowest hour number rather
  // than the least reversible member.
  const prec = t.admitted.length ? t.admitted[0] : null;
  // The hour hand must differ from where the MINUTE hand points, not from
  // routeEnd - with no route the minute hand falls back to precedence, and
  // comparing against routeEnd drew a second hand under the first.
  const minuteAt = t.routeEnd || prec || null;
  setHand("minute", minuteAt, SIZE * 0.196 - 10);
  setHand("hour", prec && prec !== minuteAt ? prec : null,
          SIZE * 0.196 - 74, "precedence", SIZE * 0.196 - 52);
  setHand("split",
    t.routeAimed && t.routeAimed !== t.routeEnd ? t.routeAimed : null,
    SIZE * 0.196 - 26, "aimed", 70);

  // The bands are trace-driven text and exist in the base render whether or
  // not that trace justified them, so the browser writes or blanks them. An
  // element cannot be created here; it can only be filled or emptied.
  const released = t.stages.some((x) => x.startsWith("RELEASE"));
  const state = t.failures.length ? "FAULT" : released ? "RELEASED" : "NO RELEASE";
  if (bands.escapement) {
    bands.escapement.textContent = `LE SAS \u00b7 ${state}`;
    bands.escapement.setAttribute("fill", t.failures.length ? INK.fault : INK.dim);
  }
  if (bands.fault) bands.fault.textContent = t.failures.length ? t.failures[0].toUpperCase() : "";
  if (bands.brake) bands.brake.textContent = "";

  document.getElementById("readout").innerHTML = readout(t);
}

function rows(pairs) {
  return pairs.map(([k, v, n]) =>
    `<div class="row"><span class="k">${k}</span><span class="v">${v}` +
    (n ? `<span class="note-s">${n}</span>` : "") + `</span></div>`).join("");
}

function readout(t) {
  const lit = t.positions.filter((p) => p.state !== "dark");
  const prec = t.admitted.length ? t.admitted[0] : null;
  const seatName = (p) => p ? `${p} ${(t.positions.find((x) => x.position === p) || {}).name || ""}` : "&mdash;";

  return `
  <div class="group"><h2>Route</h2>${rows([
    ["taken", t.route || "&mdash;", ""],
    ["Hour &middot; cyan", seatName(prec),
      "precedence" + (prec === t.routeEnd ? " &middot; superimposed" : "")],
    ["Minute &middot; white", seatName(t.routeEnd), "route ended"],
    ["Split &middot; dashed",
      t.routeAimed && t.routeAimed !== t.routeEnd ? seatName(t.routeAimed) : "&mdash;",
      "route aimed"],
  ])}</div>
  <div class="group"><h2>Positions &middot; ${lit.length} of 13 lit</h2>${
    lit.map((p) => `<div class="row"><span>${p.name}</span>` +
      `<span class="tag" style="color:${STATE_INK[p.state]}">${p.state.toUpperCase()}</span></div>`).join("")
    || '<div class="none">Routine work convenes no one.</div>'}</div>
  <div class="group"><h2>Why each fired</h2>${
    lit.map((p) => `<div class="row"><span class="k">${p.position}</span>` +
      `<span class="k">${p.reason}${p.note ? " &middot; " + p.note : ""}</span></div>`).join("")
    || '<div class="none">&mdash;</div>'}</div>
  <div class="group"><h2>Notices</h2>${
    t.notices.map((n) => `<div class="row"><span>${n}</span></div>`).join("")
    || '<div class="none">None recorded.</div>'}</div>
  <div class="group"><h2>Faults</h2><div class="fault">${
    t.failures.map((f) => `<div>${f}</div>`).join("")
    || '<span class="none">None recorded.</span>'}</div></div>`;
}

const utt = document.getElementById("utt");
const arm = document.getElementById("arm");
const run = () => paint(route(D, utt.value, arm.checked ? "Le Fripon" : null));
utt.addEventListener("input", run);
arm.addEventListener("change", run);
document.querySelectorAll(".chip").forEach((c) =>
  c.addEventListener("click", () => { utt.value = c.dataset.eg; run(); utt.focus(); }));
run();
