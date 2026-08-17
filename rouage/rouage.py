"""LE ROUAGE - the going train.

Specification: overlays/le-rouage.md
Manifest:      overlays/le-conseil.md

Carries force from the barrel to the escapement and distributes the regulated
result. Its defining property, from the specification:

    The train decides nothing.

Everything here is either a literal string match, an ordering declared in
le-conseil.md, or a count. Nothing in this module reads for meaning. If a
change to this file requires understanding what the operator *meant*, that
change belongs in the barrel, not the train.

The roster, the precedence ladder, the panel cap, and the activation phrases
are all parsed from the markdown at runtime. None of them are written down
twice. A doctrine change is a markdown edit, and the train picks it up.

Stdlib only. This runs on the single-board computer in the case.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

# (member, citation) or (member, citation, evidence). Evidence is an object
# id the barrel claims is the artifact its citation is about - see
# admit_proposals() for why it is a separate field and not the citation.
# Union, not `|`: annotations are lazy under __future__, but this alias is a
# module-level expression and PEP 604 unions need 3.10. The repo runs on 3.9.
Proposal = Union[tuple[str, str], tuple[str, str, str]]

REPO = Path(__file__).resolve().parent.parent
CONSEIL = REPO / "overlays" / "le-conseil.md"

CORE_HEADING = "## OPERATIONAL CORE"
DOCTRINE_HEADING = "## DOCTRINE"


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def fold(text: str) -> str:
    """Casefold and strip accents, so 'Renegat' matches 'Renégat'.

    The subroutines already anticipate this: le-redempteur.md lists both
    "Le Rédempteur" and "Le Redempteur" as invocation phrases. Folding here
    means the doctrine does not have to keep listing both.
    """
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


# --------------------------------------------------------------------------
# The parsed ring
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Member:
    position: str            # "01" .. "12", or "crown"
    name: str                # "Le Sceptique"
    path: Path
    phrases: tuple[str, ...] = ()
    standing: bool = False   # runs every turn, uncapped
    sealed: bool = False     # never self-activates; requires arming
    bullets: tuple[str, ...] = ()  # the semantic half of the gate, verbatim

    def matches(self, utterance: str) -> str | None:
        """Return the phrase that fired, or None. Literal containment only."""
        folded = fold(utterance)
        for phrase in self.phrases:
            if fold(phrase) in folded:
                return phrase
        return None


@dataclass(frozen=True)
class Ring:
    members: tuple[Member, ...]
    precedence: tuple[str, ...]   # member names, most irreversible first
    cap: int

    def by_name(self, name: str) -> Member | None:
        for m in self.members:
            if fold(m.name) == fold(name):
                return m
        return None

    @property
    def hours(self) -> tuple[Member, ...]:
        return tuple(m for m in self.members if m.position != "crown")


# --------------------------------------------------------------------------
# Parsing the manifest
# --------------------------------------------------------------------------

ROSTER_ROW = re.compile(
    r"^\|\s*(\d{2})\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*`([^`]+)`\s*\|", re.M
)
CROWN_ROW = re.compile(
    r"^\|\s*\*\*(Le Sauvegarder)\*\*\s*\|[^|]*\|\s*`([^`]+)`\s*\|", re.M
)
PRECEDENCE_SECTION = re.compile(r"^##\s+Precedence\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
PRECEDENCE_ITEM = re.compile(r"^\d+\.\s+\*\*([^*]+)\*\*", re.M)
CAP_PHRASE = re.compile(r"\*\*(\w+) to (\w+) members convene at once\.\*\*")

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}


def parse_activation(
    path: Path,
) -> tuple[tuple[str, ...], bool, bool, tuple[str, ...]]:
    """Extract (phrases, standing, sealed, bullets) from a gate block.

    Reads only the '### Activation' (or '### Standing Activation') section
    inside OPERATIONAL CORE. The quoted strings in that section are the
    machine-matchable half of the gate, and evaluate() matches them.

    The prose bullets beneath them are the semantic half - "an artifact
    shows modification whose cause is unknown" - and are not matched here;
    doing that would require interpretation, which le-rouage.md prohibits
    the train from doing. They are still extracted, verbatim, because
    admit_proposals() needs something to check a barrel's citation against
    without re-reading the file for meaning itself.
    """
    text = path.read_text(encoding="utf-8")

    core = text.split(CORE_HEADING, 1)
    if len(core) != 2:
        raise ValueError(f"{path.name}: no {CORE_HEADING}")
    body = core[1].split(DOCTRINE_HEADING, 1)[0]

    block = re.search(r"^###\s+.*Activation\s*$(.*?)(?=^###\s|\Z)", body,
                      re.M | re.S)
    if block is None:
        raise ValueError(f"{path.name}: no Activation section")
    section = block.group(1)

    phrases = tuple(dict.fromkeys(re.findall(r'"([^"]+)"', section)))
    standing = "**Always on.**" in section
    sealed = "does not self-activate" in section
    bullets = tuple(m.group(1).strip()
                     for m in re.finditer(r"^-\s+(.+)$", section, re.M))
    return phrases, standing, sealed, bullets


def load_ring(conseil: Path = CONSEIL) -> Ring:
    """Parse the manifest and every gate block. This is the archive state."""
    text = conseil.read_text(encoding="utf-8")

    members: list[Member] = []
    rows = [(pos, name, rel) for pos, name, rel in ROSTER_ROW.findall(text)]
    rows += [("crown", name, rel) for name, rel in CROWN_ROW.findall(text)]

    for position, name, rel in rows:
        path = REPO / rel
        phrases, standing, sealed, bullets = parse_activation(path)
        members.append(Member(position, name.strip(), path,
                              phrases, standing, sealed, bullets))

    # Scoped to the '## Precedence' section. The numbered list under
    # 'Adding Or Removing A Member' is membership criteria, not a ladder,
    # and an unscoped match silently ranks the ring behind four adjectives.
    ladder = PRECEDENCE_SECTION.search(text)
    if ladder is None:
        raise ValueError("le-conseil.md: precedence section not found")
    precedence = tuple(PRECEDENCE_ITEM.findall(ladder.group(1)))

    cap_match = CAP_PHRASE.search(text)
    if cap_match is None:
        raise ValueError("le-conseil.md: panel cap not found")
    cap = NUMBER_WORDS[cap_match.group(2).casefold()]

    return Ring(tuple(members), precedence, cap)


def load_core(member: Member) -> str:
    """Return the OPERATIONAL CORE text alone.

    le-rouage.md: 'No loading doctrine at runtime. Cores only.' The assertion
    is not paranoia - it is the only place this rule can actually be enforced.
    """
    text = member.path.read_text(encoding="utf-8")
    core = text.split(CORE_HEADING, 1)[1].split(DOCTRINE_HEADING, 1)[0]
    assert DOCTRINE_HEADING not in core, f"{member.path.name}: doctrine leaked"
    return core.strip()


# --------------------------------------------------------------------------
# The cycle
# --------------------------------------------------------------------------

@dataclass
class Candidate:
    member: Member
    reason: str              # "named:<phrase>" | "standing" | "proposed:<cite>"
    state: str = "active"    # active | consulted | sealed | held
    note: str = ""


@dataclass
class Trace:
    """What the train emits. The dial renders this and nothing else.

    Two surfaces, and they are not the same surface:

      - This trace records held members, for inspection. That is what makes
        'absence is signal' verifiable rather than asserted.
      - The prose ATLAS returns must NOT name them. le-sas.md: held members
        are 'not named, not listed, and not marked absent in output.'

    Rendering this trace directly into prose would violate suppression.
    """
    utterance: str
    stages: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    armed: str | None = None

    def admitted(self) -> list[Candidate]:
        return [c for c in self.candidates if c.state == "active"]

    def to_dict(self) -> dict:
        return {
            "utterance": self.utterance,
            "armed": self.armed,
            "stages": self.stages,
            "failures": self.failures,
            "positions": [
                {
                    "position": c.member.position,
                    "name": c.member.name,
                    "state": c.state,
                    "reason": c.reason,
                    "note": c.note,
                }
                for c in sorted(self.candidates, key=lambda c: c.member.position)
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def evaluate(ring: Ring, utterance: str, armed: str | None = None) -> list[Candidate]:
    """Stage 2 - EVALUATE. Literal matching. No interpretation.

    `armed` is the name of the mode L'Opérateur authorized for this turn only.
    le-boitier.md: 'Arming must expire.' It expires because it is an argument
    and this function keeps no state - there is nowhere for it to persist.
    """
    found: list[Candidate] = []
    for member in ring.members:
        if member.standing:
            found.append(Candidate(member, "standing"))
            continue

        phrase = member.matches(utterance)
        if phrase is None:
            continue

        if member.sealed and fold(armed or "") != fold(member.name):
            found.append(Candidate(member, f"named:{phrase}", "sealed",
                                   "named without authorization"))
            continue

        found.append(Candidate(member, f"named:{phrase}"))
    return found


def order(ring: Ring, candidates: list[Candidate]) -> list[Candidate]:
    """Stage 3 - ORDER. Precedence follows irreversibility, as declared.

    Anything not on the ladder sorts after everything on it, by dial position.
    le-rouage.md: 'No reordering by preference.'
    """
    def rank(c: Candidate) -> tuple[int, str]:
        for i, name in enumerate(ring.precedence):
            if fold(name) == fold(c.member.name):
                return (i, c.member.position)
        return (len(ring.precedence), c.member.position)

    return sorted(candidates, key=rank)


def meter(ring: Ring, candidates: list[Candidate], trace: Trace) -> list[Candidate]:
    """Stage 4 - METER. Le Sas enforces the cap. It does not trim quietly.

    Le Sceptique is standing and is not counted against the cap.
    """
    # Full ring is a fault in the gates, so it is measured on what matched -
    # not on what survived. le-rouage.md: 'Full ring. Every hour matched.'
    # A sealed Fripon still matched; a held member still matched. Counting
    # survivors instead would hide the discrimination failure behind the
    # very cap that the failure caused to fire.
    lit_hours = {c.member.position for c in candidates
                 if c.member.position != "crown"}
    if len(lit_hours) == len(ring.hours):
        trace.failures.append(
            f"full ring: {len(lit_hours)} hours matched - "
            "discrimination failure in the gates"
        )

    counted = [c for c in candidates if not c.member.standing and c.state == "active"]

    for i, c in enumerate(counted):
        if i >= ring.cap:
            c.state = "held"
            c.note = f"over cap ({len(counted)} convened, cap {ring.cap})"

    over = sum(1 for c in counted if c.state == "held")
    if over:
        trace.failures.append(
            f"over-cap: {len(counted)} convened, cap {ring.cap}, {over} held"
        )
    return candidates


def route(
    ring: Ring,
    utterance: str,
    armed: str | None = None,
    proposals: list[Proposal] | None = None,
    verify: Callable[[str], bool] | None = None,
    require_evidence: bool = False,
) -> Trace:
    """One turn of the train. Pure: same ring + same input, same trace.

    `proposals` is the barrel's semantic-half output for this turn - see
    admit_proposals() for what it is and how it is admitted. Optional and
    defaults to none, so a caller with no barrel (or a barrel that found
    nothing) still gets exactly the old, literal-only behaviour.

    Stages 6 (COLLECT) and 7 (TIER) are the barrel's and Le Sceptique's.
    They are recorded as stages the train reached and handed off, never as
    stages the train performed.
    """
    trace = Trace(utterance=utterance, armed=armed)

    trace.stages.append("WIND")
    trace.stages.append("EVALUATE")
    candidates = evaluate(ring, utterance, armed)
    trace.candidates = candidates
    if proposals:
        candidates = candidates + admit_proposals(
            ring, trace, proposals, verify, require_evidence)

    trace.stages.append("ORDER")
    candidates = order(ring, candidates)

    trace.stages.append("METER")
    trace.candidates = meter(ring, candidates, trace)

    trace.stages.append("LOAD")
    for c in trace.admitted():
        load_core(c.member)   # asserts cores-only; text goes to the barrel

    trace.stages.append("COLLECT->barrel")
    trace.stages.append("TIER->01")
    trace.stages.append("RELEASE->sas")
    trace.stages.append("DISTRIBUTE")
    trace.stages.append("RECORD->crown")
    return trace


# --------------------------------------------------------------------------
# The barrel boundary
# --------------------------------------------------------------------------

def admit_proposals(
    ring: Ring,
    trace: Trace,
    proposals: list[Proposal],
    verify: Callable[[str], bool] | None = None,
    require_evidence: bool = False,
) -> list[Candidate]:
    """Admit the barrel's semantic gate matches into the deterministic train.

    Every activation block has two halves. The quoted phrases are matchable
    and `evaluate()` handles them. The prose bullets - "an artifact shows
    modification whose cause is unknown" - are not matchable without reading
    for meaning, which the train is forbidden to do.

    So the barrel proposes and the train disposes: proposals still pass
    through order(), meter(), and the Fripon seal downstream, which is what
    keeps "the train decides nothing" true even though something upstream did.

    `proposals` is a list of (member_name, citation) where citation is the
    activation bullet the barrel claims fired.

    Decided (L'Opérateur, 2026-08-16): **Cited**. Of the three options this
    docstring used to carry -

      (a) Permissive  - admit any proposal; the cap and seal are the only
                        defence. Risks theatre.
      (b) Cited       - reject any proposal whose citation is not a verbatim
                        line in that member's Activation section. Auditable
                        and still a string match, so the train stays
                        deterministic.
      (c) Strict      - admit nothing automatically. Maximum honesty, but
                        eleven of thirteen gates go permanently dark.

    - (b) is what is built. A proposal is admitted only if `citation`,
    stripped, equals one of `member.bullets` exactly: the same prose lines
    parse_activation() already pulled out of the doctrine at load time, so
    there is no second copy of the gate text to drift from the file. This
    is still a literal match, just against a different field than
    evaluate() checks, so "the train decides nothing" survives - whatever
    read the artifact for meaning and decided the bullet applied was the
    barrel, upstream of here.

    A citation that does not match verbatim is a rejected proposal, not a
    held candidate: it never reaches order() or meter(), because the cap
    and the seal are for things that actually convened. The rejection is
    recorded to trace.failures instead - a barrel that keeps citing text
    that is not there is itself a discrimination failure in the gates, the
    same category evaluate() already reports as full-ring and over-cap.

    A member already present in trace.candidates (named, or standing) is
    skipped rather than duplicated - one convened member should occupy one
    cap slot, not one per route that found it.

    A correctly cited sealed member (Le Fripon) is still not admitted
    unless `trace.armed` names him. A true bullet says Matthew might want
    to invoke him, never that he has - the same distinction evaluate()
    already draws for a named sealed match.

    Return the candidates to merge into trace.candidates before order().
    """
    admitted: list[Candidate] = []
    seen = {fold(c.member.name) for c in trace.candidates}

    for proposal in proposals:
        name, citation, *rest = proposal
        evidence = (rest[0].strip() if rest and rest[0] else "")

        member = ring.by_name(name)
        if member is None:
            trace.failures.append(f"rejected proposal: unknown member {name!r}")
            continue

        folded_name = fold(member.name)
        if folded_name in seen:
            continue

        cited = citation.strip()
        if cited not in member.bullets:
            trace.failures.append(
                f"rejected proposal: {member.name} cited text not found "
                f"verbatim in its Activation section: {citation!r}"
            )
            continue

        # A citation proves the gate is real. It cannot prove the premise was.
        # The barrel can quote Le Limier's bullet perfectly with nothing having
        # been modified at all - the gate exists, the fact was invented, and
        # nothing above this line can tell the difference. Evidence is the
        # second field that narrows that gap: an object id the train resolves
        # without reading it. Resolving is not interpreting, so the train stays
        # as dumb as le-rouage.md requires.
        #
        # It narrows the gap; it does not close it. A real object that has
        # nothing to do with the claim still passes. This catches fabrication,
        # not misattribution, and saying otherwise would overstate the check.
        note = ""
        if evidence:
            if verify is None:
                # Recorded, explicitly NOT checked. A trace that showed bare
                # evidence here would be claiming a verification that never
                # happened, which is the failure the whole instrument is
                # built against.
                note = f"evidence {evidence} (unverified)"
            elif verify(evidence):
                note = f"evidence {evidence}"
            else:
                trace.failures.append(
                    f"rejected proposal: {member.name} cited evidence that "
                    f"does not resolve: {evidence!r}"
                )
                continue
        elif require_evidence:
            trace.failures.append(
                f"rejected proposal: {member.name} supplied no evidence"
            )
            continue

        seen.add(folded_name)
        if member.sealed and fold(trace.armed or "") != folded_name:
            unauth = "proposed without authorization"
            admitted.append(Candidate(
                member, f"proposed:{cited}", "sealed",
                f"{unauth}; {note}" if note else unauth))
        else:
            admitted.append(Candidate(member, f"proposed:{cited}", note=note))

    return admitted


def git_evidence(repo: Path = REPO) -> Callable[[str], bool]:
    """An evidence verifier backed by a real repository.

    Deliberately a separate function the caller opts into, rather than
    something admit_proposals() reaches for itself. The train has no business
    knowing what git is: keep it as an injected callable and rouage.py still
    runs anywhere, the boundary stays testable with a two-line fake, and a
    future evidence store that is not git needs no change to the train.

    `git cat-file -e` resolves an object or exits non-zero. That covers a
    commit, a tree, or a blob - which matters, because the barrel should not
    have to commit in order to cite. `git add` followed by `git write-tree`
    gives a tree id for exactly the staged state; `git hash-object -w` gives
    a blob id for one file. Either lets evidence point at what is being
    looked at without a junk commit for every proposal.

    The `-w` is not optional and the trap is quiet: `git hash-object` without
    it computes the same content address but writes nothing, so the id looks
    correct and does not resolve. An unwritten object is not evidence - there
    is nothing for anyone to go and read later - so rejecting it is right,
    but the error says 'does not resolve' rather than 'you forgot -w'.
    """
    def verify(ref: str) -> bool:
        try:
            done = subprocess.run(
                ["git", "-C", str(repo), "cat-file", "-e", f"{ref}^{{object}}"],
                capture_output=True, timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return False       # no git, no repo, no claim of verification
        return done.returncode == 0

    return verify
