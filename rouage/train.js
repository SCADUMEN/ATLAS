// LE ROUAGE, in the browser. The stage logic only - no gate vocabulary.
//
// Every phrase, the roster, the precedence ladder, the cap, the routes and the
// invocation verbs arrive as `D`, generated from the markdown by rouage/emit.py.
// Nothing here may hardcode any of them: this file is the algorithm and the
// doctrine is still the single source.
//
// This IS a second implementation of the stages, which is a real cost. It is
// held honest by rouage/test_conformance.py, which runs the same input matrix
// through this and through rouage.py and asserts identical traces.

export function fold(text) {
  return text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

function matches(member, folded) {
  for (const p of member.phrases) if (folded.includes(fold(p))) return p;
  return null;
}

// Stage 2 - EVALUATE. Literal phrases only. The prose bullets are the semantic
// half and belong to the barrel; reading them here would be interpreting.
function evaluate(D, utterance, armed) {
  const folded = fold(utterance);
  const out = [];
  for (const m of D.members) {
    const hit = matches(m, folded);
    if (m.standing) { out.push({ m, reason: "standing", state: "active", note: "" }); continue; }
    if (!hit) continue;
    const sealed = m.sealed && fold(armed || "") !== fold(m.name);
    out.push({
      m, reason: `named:${hit}`,
      state: sealed ? "sealed" : "active",
      note: sealed ? "named without authorization" : "",
    });
  }
  return out;
}

// Stage 2b - ROUTE. Deliberate invocation only: every route name is a common
// English word, so a bare match convenes members out of ordinary prose.
function takeRoute(D, utterance, trace) {
  const folded = fold(utterance);
  const verbs = D.invoke.join("|");
  const hit = Object.keys(D.routes).find((n) =>
    new RegExp(`\\b(?:${verbs})\\s+${fold(n).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(folded));
  if (!hit) return [];

  trace.route = hit;
  const steps = D.routes[hit];
  if (!steps.length) {
    trace.notices.push(`route ${hit}: delegated to protocol, no sequence for the train`);
    return [];
  }
  const resolve = (s) => D.members.find(
    (m) => fold(m.name) === fold(s) || fold(m.name).endsWith(" " + fold(s)));

  const out = [], seen = new Set();
  for (const step of steps) {
    const m = resolve(step);
    if (!m || seen.has(fold(m.name))) continue;
    seen.add(fold(m.name));
    const sealed = m.sealed && fold(trace.armed || "") !== fold(m.name);
    out.push({
      m, reason: `route:${hit}`,
      state: sealed ? "sealed" : "active",
      note: sealed ? "route step without authorization" : "",
    });
  }
  const resolved = steps.map(resolve).filter(Boolean);
  trace.routePositions = resolved.map((m) => m.position);
  trace.routeEnd = resolved.length ? resolved[resolved.length - 1].position : null;
  trace.routeAimed = trace.routeEnd;
  trace.notices.push(`route ${hit}: ${steps.join(" -> ")}`);
  return out;
}

// Stage 3 - ORDER. Precedence follows irreversibility, and the ladder is
// doctrine's, not this file's.
function order(D, cands) {
  // (ladder index, dial position) - a TUPLE, matching rouage.py. Ranking on
  // the index alone and leaning on sort stability tie-breaks by roster order
  // instead of by position, which picks a different member off the ladder and
  // therefore points the hour hand somewhere else.
  const rank = (c) => {
    const i = D.precedence.findIndex((n) => fold(n) === fold(c.m.name));
    return [i === -1 ? D.precedence.length : i, c.m.position];
  };
  return [...cands].sort((a, b) => {
    const [ra, pa] = rank(a), [rb, pb] = rank(b);
    return ra - rb || (pa < pb ? -1 : pa > pb ? 1 : 0);
  });
}

// Stage 4 - METER. The cap is a ceiling, never a floor; full ring is measured
// on what matched, not on what survived.
function meter(D, cands, trace) {
  const lit = new Set(cands.filter((c) => c.m.position !== "crown").map((c) => c.m.position));
  if (lit.size === D.members.filter((m) => m.position !== "crown").length) {
    trace.failures.push(`full ring: ${lit.size} hours matched - discrimination failure in the gates`);
  }
  const effective = trace.capAuthorized && trace.capAuthorized > D.cap ? trace.capAuthorized : D.cap;
  if (effective > D.cap) trace.notices.push(`cap widened by authorization: ${D.cap} -> ${effective}`);

  const counted = cands.filter((c) => !c.m.standing && c.state === "active");
  counted.forEach((c, i) => {
    if (i >= effective) { c.state = "held"; c.note = `over cap (${counted.length} convened, cap ${effective})`; }
  });
  const over = counted.filter((c) => c.state === "held").length;
  if (over) trace.failures.push(`over-cap: ${counted.length} convened, cap ${effective}, ${over} held`);
  return cands;
}

// Stage 9a. Where the route actually ended, not where it was aimed.
function settleRouteEnd(trace, cands) {
  if (!trace.route || !trace.routePositions.length) return;
  const live = new Set(cands.filter((c) => c.state === "active").map((c) => c.m.position));
  for (let i = trace.routePositions.length - 1; i >= 0; i--) {
    const pos = trace.routePositions[i];
    if (live.has(pos)) {
      if (pos !== trace.routeEnd) {
        trace.notices.push(`route ${trace.route}: cut short at ${pos} - ${trace.routeEnd} did not pass`);
      }
      trace.routeEnd = pos;
      return;
    }
  }
  trace.notices.push(`route ${trace.route}: no step survived; the hand indicates nothing`);
  trace.routeEnd = null;
}

// Python's repr(), for the failure strings. The two engines are compared field
// by field, so a rejection reported here must read exactly as rouage.py writes
// it - including the quoting, which Python chooses by content.
function pyRepr(s) {
  const q = (s.includes("'") && !s.includes('"')) ? '"' : "'";
  let out = "";
  for (const ch of s) {
    if (ch === "\\") out += "\\\\";
    else if (ch === q) out += "\\" + ch;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else {
      const c = ch.codePointAt(0);
      out += (c < 0x20 || c === 0x7f)
        ? "\\x" + c.toString(16).padStart(2, "0")
        : ch;
    }
  }
  return q + out + q;
}

// Stage 6 - COLLECT. The barrel's half, admitted into the train.
//
// This is the one stage whose input the train cannot derive: something read an
// artifact for meaning and decided a prose bullet fired. That reading happened
// upstream, in the barrel. What happens here is still a literal string match -
// the citation against the member's own Activation bullets - which is why the
// browser may do it at all. Reading the bullets FOR meaning would be
// interpreting, and this file is forbidden that.
//
// Mirrors admit_proposals() in rouage.py, policy (b) Cited. Every rejection
// string is duplicated from there deliberately: the conformance test compares
// them verbatim, so a divergence is a test failure rather than a dial that
// quietly disagrees with the council.
function admitProposals(D, trace, proposals, cands, resolvable, requireEvidence) {
  const admitted = [];
  const seen = new Set(cands.map((c) => fold(c.m.name)));

  for (const proposal of proposals) {
    const [name, citation, rawEvidence] = proposal;
    const evidence = rawEvidence ? rawEvidence.trim() : "";

    const m = D.members.find((x) => fold(x.name) === fold(name));
    if (!m) {
      trace.failures.push(`rejected proposal: unknown member ${pyRepr(name)}`);
      continue;
    }

    const folded = fold(m.name);
    if (seen.has(folded)) continue;

    const cited = citation.trim();
    if ((m.prohibitions || []).includes(cited)) {
      // An inverted gate: the barrel found the sentence saying DO NOT fire on
      // this and offered it as grounds to fire. Louder than a typo, and the
      // trace must not collapse the two.
      trace.failures.push(
        `rejected proposal: ${m.name} cited a prohibition, not ` +
        `an activation - its gate names this as a reason to stay ` +
        `dark: ${pyRepr(citation)}`);
      continue;
    }

    if (!(m.bullets || []).includes(cited)) {
      trace.failures.push(
        `rejected proposal: ${m.name} cited text not found ` +
        `verbatim in its Activation section: ${pyRepr(citation)}`);
      continue;
    }

    // A citation proves the gate is real; it cannot prove the premise was.
    // Evidence is an object id the train resolves without reading it.
    // `resolvable === null` is no verifier at all, which is recorded as
    // explicitly unchecked - not as a verification that never happened.
    let note = "";
    if (evidence) {
      if (resolvable === null || resolvable === undefined) {
        note = `evidence ${evidence} (unverified)`;
      } else if (resolvable.includes(evidence)) {
        note = `evidence ${evidence}`;
      } else {
        trace.failures.push(
          `rejected proposal: ${m.name} cited evidence that ` +
          `does not resolve: ${pyRepr(evidence)}`);
        continue;
      }
    } else if (requireEvidence) {
      trace.failures.push(`rejected proposal: ${m.name} supplied no evidence`);
      continue;
    }

    seen.add(folded);
    if (m.sealed && fold(trace.armed || "") !== folded) {
      const unauth = "proposed without authorization";
      admitted.push({
        m, reason: `proposed:${cited}`, state: "sealed",
        note: note ? `${unauth}; ${note}` : unauth,
      });
    } else {
      admitted.push({ m, reason: `proposed:${cited}`, state: "active", note });
    }
  }
  return admitted;
}

export function route(D, utterance, armed = null, capAuthorized = null, opts = {}) {
  const trace = {
    utterance, armed, capAuthorized,
    stages: [], failures: [], notices: [],
    route: null, routeEnd: null, routeAimed: null, routePositions: [],
  };
  trace.stages.push("WIND", "EVALUATE");
  let cands = evaluate(D, utterance, armed);
  const routed = takeRoute(D, utterance, trace);
  if (routed.length) {
    const seen = new Set(routed.map((c) => fold(c.m.name)));
    cands = routed.concat(cands.filter((c) => !seen.has(fold(c.m.name))));
    trace.stages.push("ROUTE->named");
  }
  const proposals = opts.proposals || null;
  if (proposals && proposals.length) {
    cands = cands.concat(admitProposals(
      D, trace, proposals, cands,
      opts.resolvable === undefined ? null : opts.resolvable,
      Boolean(opts.requireEvidence)));
  }

  trace.stages.push("ORDER");
  cands = order(D, cands);
  trace.stages.push("METER");
  cands = meter(D, cands, trace);
  trace.stages.push("LOAD", "COLLECT->barrel", "TIER->01");
  settleRouteEnd(trace, cands);
  trace.stages.push("RELEASE->sas", "DISTRIBUTE", "RECORD->crown");

  trace.admitted = cands
    .filter((c) => c.state === "active" && c.m.position !== "crown")
    .map((c) => c.m.position);
  trace.positions = [...cands]
    .sort((a, b) => (a.m.position < b.m.position ? -1 : 1))
    .map((c) => ({ position: c.m.position, name: c.m.name, state: c.state, reason: c.reason, note: c.note }));
  return trace;
}
