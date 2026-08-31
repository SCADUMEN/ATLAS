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

import functools
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

# What a member concluded, as opposed to whether it convened. The train had no
# representation of this at all, which is why three separate things could not
# work: Le Renegat's halt, the Dissent display state, and Consulted.
Verdict = tuple[str, str]        # (member_name, verdict)

# Le Renegat's verdicts, from le-conseil.md. Only two of the three halt.
HALTING = ("archive", "release")

# le-conseil.md Display States. 'dark' is absence and never stored.
STATES = ("consulted", "active", "sealed", "held", "dissent")

# The Named Routes table. Sequences are written with bare surnames and an
# arrow, so they are parsed the same way as everything else: from doctrine,
# never restated here.
ROUTES_HEADER = re.compile(r"^\|\s*Route\s*\|\s*Sequence\s*\|.*$", re.M)
# The invocation grammar is doctrine, not code. le-conseil.md states it in one
# sentence and this reads the verbs out of it - the same arrangement as the cap,
# which is parsed from "Two to four members convene at once" rather than being
# written here. Hardcoding `run|take|route` would have put the one piece of gate
# vocabulary that lives in Python back in Python.
#
# The rule exists because every route name is a common English word: matching
# them bare convened members out of ordinary prose. Member phrases survive loose
# matching because 54 of 55 are multi-word constructions nobody types by
# accident; route names are not, so they take a verb. The one that is not a
# construction is Le Limier's `Who is X?`, which is a form - see PLACEHOLDER.
INVOKE_PHRASE = re.compile(
    r"\*\*Routes are invoked by verb:\*\*\s*(.+?)(?:,\s*followed|\.)", re.S)
INVOKE_VERB = re.compile(r"`(\w+)`")


ROUTE_ROW = re.compile(r"^\|\s*\*\*([^*|]+)\*\*\s*\|\s*([^|]+?)\s*\|", re.M)

REPO = Path(__file__).resolve().parent.parent
CONSEIL = REPO / "overlays" / "le-conseil.md"

CORE_HEADING = "## OPERATIONAL CORE"
DOCTRINE_HEADING = "## DOCTRINE"

# The negative half of a gate: what must not CONVENE a member. Distinct from
# the '### Prohibitions' section every member carries, which is what a member
# must not DO once convened. Two different kinds, and only one had a home.
#
# Le Redempteur wrote his inline, as '**Do not fire on:**', in the first
# subroutine written - two months before the other nine - because he is the
# member most dangerous to fire wrongly. parse_activation() collected bullets
# across the whole Activation section, so all five of his guards landed in
# `bullets`, citations() offered them as quotable, and admit_proposals()
# accepted a guard as grounds to convene. Promoting the marker to a sibling
# heading is what separates them, and the section is matched here so the
# doctrine declares its own structure instead of the parser inferring it.
NEGATIVE_SECTION = re.compile(
    r"^###\s+Do Not Fire On\s*$(.*?)(?=^###\s|\Z)", re.M | re.S | re.I)


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def load_invocations(conseil: Path = CONSEIL) -> tuple[str, ...]:
    """The verbs a route answers to, parsed from le-conseil.md."""
    m = INVOKE_PHRASE.search(conseil.read_text(encoding="utf-8"))
    if m is None:
        raise ValueError("le-conseil.md: route invocation grammar not found")
    verbs = tuple(INVOKE_VERB.findall(m.group(1)))
    if not verbs:
        raise ValueError("le-conseil.md: no invocation verbs in the grammar")
    return verbs


def fold(text: str) -> str:
    """Casefold and strip accents, so 'Renegat' matches 'Renégat'.

    The subroutines already anticipate this: le-redempteur.md lists both
    "Le Rédempteur" and "Le Redempteur" as invocation phrases. Folding here
    means the doctrine does not have to keep listing both.
    """
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


# A quoted activation phrase may carry a placeholder: a bare capital X standing
# in for the thing the Operator actually names. Le Limier's gate is written
# `asks "Who is X?" of any name, handle, or maker's mark, as in "Who is JJ Ammo
# Can?"` - a form and an illustration of it. parse_activation() collects every
# quoted string in the section, so both arrived here as literals, and literal
# containment made the sign fire for exactly two names: the placeholder itself,
# and the one example doctrine happened to print. Every other name asked the
# question correctly and convened nobody.
#
# So the placeholder is read as a placeholder. Doctrine is unchanged - it
# already wrote the form - and no member's trigger is named in Python, which is
# the whole arrangement: the phrases are parsed from the markdown, and teaching
# the parser a wider notion of "phrase" keeps them there. `Who is X?` is the
# only phrase in the ring carrying a bare X, so nothing else changes shape.
PLACEHOLDER = re.compile(r"(?<![A-Za-z])X(?![A-Za-z])")

# Decided (L'Operateur, 2026-08-31): **name-shaped, terminator optional.** The
# slot takes a run with no sentence-ender in it, and a phrase ending in `?`
# accepts either the mark or the end of the utterance - so `who is jj ammo can`
# typed without one still lands. This over-fires on prose of the same shape
# ("who is running the tests?"), which is deliberate and cheap: EVALUATE is
# half the gate, and the bullets, the Do Not Fire On section and the panel cap
# are the half that refuses. A sign that occasionally over-fires is recoverable
# downstream. A sign that never fires is the shrug the countersign exists to
# refuse.
PLACEHOLDER_RUN = r"[^?!.,;:]{1,60}"
QUESTION_MARK = re.escape("?")


@functools.lru_cache(maxsize=None)
def phrase_pattern(phrase: str) -> re.Pattern[str] | None:
    """Compile a placeholder phrase, or None if it is an ordinary literal.

    Built on the folded phrase so a pattern matches on the same terms
    `matches()` compares everything else on.
    """
    if not PLACEHOLDER.search(phrase):
        return None
    body = PLACEHOLDER_RUN.join(
        re.escape(fold(part)) for part in PLACEHOLDER.split(phrase))
    if body.endswith(QUESTION_MARK):
        body = body[:-len(QUESTION_MARK)] + r"(?:\?|$)"
    return re.compile(body)


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
    prohibitions: tuple[str, ...] = ()   # negative half: what must NOT fire it

    def matches(self, utterance: str) -> str | None:
        """Return the phrase that fired, or None.

        Literal containment, except where doctrine wrote a placeholder - then
        the phrase is the form and the slot takes what the Operator named.
        Either way the phrase returned is the verbatim doctrine string, so the
        trace and the dial report the gate as written rather than as compiled.
        """
        folded = fold(utterance)
        for phrase in self.phrases:
            pattern = phrase_pattern(phrase)
            if pattern is None:
                if fold(phrase) in folded:
                    return phrase
            elif pattern.search(folded):
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
# Trailing text inside the bold is tolerated so doctrine can qualify the
# sentence - "...convene at once - by default." - without the parser
# losing the numbers. The two number words stay the only thing read.
CAP_PHRASE = re.compile(r"\*\*(\w+) to (\w+) members convene at once[^*]*\*\*")

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}


def bullet_lines(section: str) -> tuple[str, ...]:
    """The '- ' lines of a section, verbatim and in order.

    Both halves of a gate are bullet lists and both must be read the same
    way, byte for byte, or a citation could be admissible against one and
    not the other.
    """
    return tuple(m.group(1).strip()
                 for m in re.finditer(r"^-\s+(.+)$", section, re.M))


def parse_activation(
    path: Path,
) -> tuple[tuple[str, ...], bool, bool, tuple[str, ...], tuple[str, ...]]:
    """Extract (phrases, standing, sealed, bullets, prohibitions) from a gate.

    Reads only the '### Activation' (or '### Standing Activation') section
    inside OPERATIONAL CORE. The quoted strings in that section are the
    machine-matchable half of the gate, and evaluate() matches them.

    The prose bullets beneath them are the semantic half - "an artifact
    shows modification whose cause is unknown" - and are not matched here;
    doing that would require interpretation, which le-rouage.md prohibits
    the train from doing. They are still extracted, verbatim, because
    admit_proposals() needs something to check a barrel's citation against
    without re-reading the file for meaning itself.

    '### Do Not Fire On' is the same kind of prose pointing the other way:
    conditions that must NOT convene the member. It is a sibling section
    rather than part of Activation, so the two cannot be collected into one
    list - which is exactly what happened while the block was written inline
    as bold text, and made every one of Le Redempteur's guards admissible as
    grounds to convene him. Absent section, empty tuple; most members have no
    negative gate yet.
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
    bullets = bullet_lines(section)

    negative = NEGATIVE_SECTION.search(body)
    prohibitions = bullet_lines(negative.group(1)) if negative else ()

    return phrases, standing, sealed, bullets, prohibitions


def load_ring(conseil: Path = CONSEIL) -> Ring:
    """Parse the manifest and every gate block. This is the archive state."""
    text = conseil.read_text(encoding="utf-8")

    members: list[Member] = []
    rows = [(pos, name, rel) for pos, name, rel in ROSTER_ROW.findall(text)]
    rows += [("crown", name, rel) for name, rel in CROWN_ROW.findall(text)]

    for position, name, rel in rows:
        path = REPO / rel
        phrases, standing, sealed, bullets, prohibitions = \
            parse_activation(path)
        members.append(Member(position, name.strip(), path,
                              phrases, standing, sealed, bullets,
                              prohibitions))

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


def load_routes(conseil: Path = CONSEIL) -> dict[str, tuple[str, ...]]:
    """Parse the Named Routes table: route name -> ordered member surnames.

    A route whose sequence cell is a file reference rather than a list of
    members maps to an empty tuple. Judgement is the case: it delegates to
    `overlays/le-protocol-de-trois.md`, so there is no sequence for the train
    to run and pretending otherwise would invent one.
    """
    text = conseil.read_text(encoding="utf-8")
    header = ROUTES_HEADER.search(text)
    if header is None:
        raise ValueError("le-conseil.md: named routes table not found")

    block: list[str] = []
    for line in text[header.end():].splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith("|"):
            break
        block.append(line)

    routes: dict[str, tuple[str, ...]] = {}
    for name, seq in ROUTE_ROW.findall("\n".join(block)):
        if "`" in seq:                      # a protocol reference, not a path
            routes[name.strip()] = ()
            continue
        steps = tuple(part.strip() for part in seq.split("\u2192") if part.strip())
        routes[name.strip()] = steps
    return routes


def resolve_step(ring: Ring, surname: str) -> Member | None:
    """'Taxonomiste' -> Le Taxonomiste. The routes table writes bare surnames
    while the roster writes full names, so this is the join between them."""
    target = fold(surname)
    for m in ring.members:
        if fold(m.name) == target or fold(m.name).endswith(" " + target):
            return m
    return None


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
    # Recorded, but not faults. A brake engagement and an authorized widening
    # are the movement working, not the routing failing. Putting them in
    # failures made the escapement report FAULT for a correct halt.
    notices: list[str] = field(default_factory=list)
    armed: str | None = None
    route: str | None = None
    route_end: str | None = None
    # The sequence as positions, kept so route_end can be re-resolved after the
    # gates have run. take_route() sets the intended terminus; only the gates
    # know the actual one.
    route_positions: tuple[str, ...] = ()
    # Where the route was aimed, kept after settle_route_end() moves route_end
    # to where it actually stopped. The gap between the two is the split.
    route_aimed: str | None = None
    verdicts: list[Verdict] = field(default_factory=list)
    halted: list[str] = field(default_factory=list)
    cap_authorized: int | None = None

    def admitted(self) -> list[Candidate]:
        return [c for c in self.candidates if c.state == "active"]

    def to_dict(self) -> dict:
        return {
            "utterance": self.utterance,
            "armed": self.armed,
            "stages": self.stages,
            "failures": self.failures,
            "notices": self.notices,
            "route": self.route,
            "route_end": self.route_end,
            "route_aimed": self.route_aimed,
            # Precedence order, not dial order. `positions` is sorted by seat
            # for display; anything asking "what matters most here" must read
            # this instead, or it gets the lowest hour number rather than the
            # least reversible member.
            "admitted": [c.member.position for c in self.admitted()
                         if c.member.position != "crown"],
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

    # The cap is a default, not an absolute. le-conseil.md's real target is
    # theatre - "every register lit at once is an error state, not a climax" -
    # and a complex turn that genuinely needs five members is not theatre.
    # So widening is allowed but never automatic: it takes the same explicit
    # authorization Le Fripon's engagement takes, and it is recorded. An
    # unauthorized fifth member is still held. Theatre cannot widen itself.
    effective = ring.cap
    if trace.cap_authorized is not None and trace.cap_authorized > ring.cap:
        effective = trace.cap_authorized
        trace.notices.append(
            f"cap widened by authorization: {ring.cap} -> {effective}"
        )

    counted = [c for c in candidates if not c.member.standing and c.state == "active"]

    for i, c in enumerate(counted):
        if i >= effective:
            c.state = "held"
            c.note = f"over cap ({len(counted)} convened, cap {effective})"

    over = sum(1 for c in counted if c.state == "held")
    if over:
        trace.failures.append(
            f"over-cap: {len(counted)} convened, cap {effective}, {over} held"
        )
    return candidates


def take_route(ring: Ring, trace: Trace, utterance: str) -> list[Candidate]:
    """Stage 2b. A route named in the utterance runs its sequence.

    Routes have the same two halves as gates. The triggers in the table - "a
    new artifact enters", "anything leaving the archive" - are semantic and
    belong to the barrel. **The route's own name is matchable**, exactly like
    an invocation phrase, so the named half is buildable with the mechanism
    that already exists and that is what this is.

    Order is the route's, not precedence's. That is the point of a route: it
    says who goes first, and re-sorting it would leave the name meaning
    nothing. In practice there is no conflict, because no route in doctrine
    names more than three distinct members and the cap is four.

    A member repeated in a sequence - Harden is Vigile, Fripon, Vigile - is
    admitted once. A candidate is a seat on the dial and a seat cannot be
    occupied twice; the route's shape is preserved in trace.route rather than
    by lighting a position twice.
    """
    routes = load_routes()
    folded = fold(utterance)
    verbs = "|".join(load_invocations())
    hit = next((name for name in routes
                if re.search(rf"\b(?:{verbs})\s+{re.escape(fold(name))}\b",
                             folded)), None)
    if hit is None:
        return []

    trace.route = hit
    steps = routes[hit]
    if not steps:
        # Judgement delegates to the three-witness protocol. Recorded, and no
        # members admitted, because inventing a sequence it does not have
        # would be the train deciding something.
        trace.notices.append(
            f"route {hit}: delegated to protocol, no sequence for the train"
        )
        return []

    admitted: list[Candidate] = []
    seen: set[str] = set()
    for surname in steps:
        member = resolve_step(ring, surname)
        if member is None:
            trace.failures.append(
                f"route {hit}: step {surname!r} matches no member"
            )
            continue
        if fold(member.name) in seen:
            continue
        seen.add(fold(member.name))
        if member.sealed and fold(trace.armed or "") != fold(member.name):
            admitted.append(Candidate(member, f"route:{hit}", "sealed",
                                      "route step without authorization"))
        else:
            admitted.append(Candidate(member, f"route:{hit}"))

    # The hand sweeps to what ended the route. The last STEP is the end even
    # when it repeats an earlier one - Harden ends at Vigile - so this reads
    # from the sequence, not from the deduplicated candidates.
    resolved = [resolve_step(ring, st) for st in steps]
    trace.route_positions = tuple(m.position for m in resolved if m)
    last = resolved[-1] if resolved else None
    trace.route_end = last.position if last else None
    trace.route_aimed = trace.route_end
    trace.notices.append(f"route {hit}: {' -> '.join(steps)}")
    return admitted


def roue_a_colonnes(
    ring: Ring,
    trace: Trace,
    verdicts: list[Verdict],
) -> None:
    """LA ROUE A COLONNES - the column wheel. Stage 8b, between METER and
    RELEASE. Records what members concluded and routes the consequence.

    A chronograph's column wheel is a state machine: each press rotates it and
    its columns route the levers. It holds which state the movement is in. It
    decides nothing, which is the whole reason this is the right part - the
    train had no representation of a member's *conclusion*, only of whether it
    convened, and three things were impossible as a result: Le Renegat's halt,
    the Dissent display state, and Consulted.

    **This is not a judge.** le-conseil.md: "No member issues a decision. The
    movement reads out; L'Operateur decides." A verdict is carried here, never
    formed here. And it is a component rather than any member's complication
    for the reason le-sas.md gives about the latch: a verdict channel owned by
    Le Renegat would be a channel with a stake in what passes through it.

    Two consequences, both mechanical:

      - Any member returning a verdict is marked `dissent` if that verdict
        halts, so the dial can show the state le-conseil.md already names.
      - **Le frein, the brake.** le-conseil.md Precedence: "Le Renegat's
        verdict of Archive or Release halts the field operators until
        L'Operateur accepts or overrides it." That is one of exactly two
        standing rules that override ordering; the other - Le Fripon never
        self-activating - has been enforced in code since the seal. This one
        was not enforced anywhere, so the manifest promised a halt that could
        not happen. It happens now.

    A verdict from a member that did not convene is rejected: concluding
    something requires having been in the room.
    """
    by_pos = {c.member.position: c for c in trace.candidates}
    halting_member: str | None = None

    for name, verdict in verdicts:
        member = ring.by_name(name)
        if member is None:
            trace.failures.append(f"rejected verdict: unknown member {name!r}")
            continue

        seat = by_pos.get(member.position)
        if seat is None or seat.state not in ("active", "consulted"):
            trace.failures.append(
                f"rejected verdict: {member.name} did not convene"
            )
            continue

        trace.verdicts.append((member.name, verdict))
        if verdict.strip().casefold() in HALTING:
            seat.state = "dissent"
            seat.note = f"verdict: {verdict}"
            halting_member = member.name

    if halting_member is None:
        return

    # The brake. Field operators are the hours that go and do things, so three
    # things are exempt and each for its own reason:
    #
    #   - the standing witness, who is not a field operator;
    #   - the dissenter itself, which must stay lit or the halt would erase
    #     its own cause from the dial;
    #   - **the crown.** Halting Le Sauvegarder would make a halt suspend
    #     preservation, which is exactly backwards. He is precedence #1
    #     because evidence loss cannot be undone, and le-conseil.md is explicit
    #     that there is no path around him. A brake that can stop the crown is
    #     a brake that can lose the archive.
    for c in trace.candidates:
        if (c.member.standing
                or c.member.position == "crown"
                or c.member.name == halting_member):
            continue
        if c.state == "active":
            c.state = "held"
            c.note = f"halted by {halting_member}"
            trace.halted.append(c.member.name)

    trace.notices.append(
        f"brake engaged: {halting_member} halted "
        f"{len(trace.halted)} field operator(s) - awaiting L'Operateur"
    )


def record_winding(trace: Trace, log: Path, when: str) -> None:
    """Stages 1 and 10 - WIND and RECORD. Le Sauvegarder's log.

    `hardware/le-boitier.md` demoted this from mechanism to procedure when the
    detached winding key became a screw-down crown: a key had to be fetched,
    a crown does not, so nothing enforces that a winding is recorded. That was
    logged as a fair trade. It is still the only mandatory role in the council
    with no mechanism at all, so here is the mechanism - and it stays a
    procedure in the sense that matters, because **the caller invokes it and
    the train never does.**

    Two things are deliberately parameters rather than things this reaches for:

      - `when`. route() is pure: same ring, same input, same trace. A clock
        inside it would make a turn unreproducible and quietly break the
        property every test depends on. The caller stamps the time, so the
        time is an input like any other.
      - `log`. Archive I/O belongs to the crown, not the train. Naming the
        path at the call site keeps that true and keeps this testable without
        writing into anyone's archive.

    One JSON object per line, appended. A log that rewrites is a log that can
    lose an entry, and this is the crown's: evidence loss cannot be undone.
    """
    entry = {
        "when": when,
        "utterance": trace.utterance,
        "route": trace.route,
        "armed": trace.armed,
        "admitted": [c.member.position for c in trace.admitted()],
        "verdicts": trace.verdicts,
        "halted": trace.halted,
        "notices": trace.notices,
        "failures": trace.failures,
    }
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def settle_route_end(trace: Trace) -> None:
    """Stage 9a. Where the route ACTUALLY ended, not where it was aimed.

    take_route() sets route_end from the sequence, which is the only thing it
    can know - the cap, the brake and Le Sas have not run yet. If the last step
    is then held, the hand would sweep to a member that never passed the door
    and the dial would report a route ending somewhere it was stopped short of.

    So the terminus is re-resolved once the gates are done: the last step that
    is still standing. A route cut short ended where it was cut, and saying so
    is the difference between indicating and asserting.

    Only isolation testing missed this. Every one of these mechanisms is
    correct alone; the fault was in their composition.
    """
    if not trace.route or not trace.route_positions:
        return

    live = {c.member.position for c in trace.candidates if c.state == "active"}
    for pos in reversed(trace.route_positions):
        if pos in live:
            if pos != trace.route_end:
                trace.notices.append(
                    f"route {trace.route}: cut short at {pos} - "
                    f"{trace.route_end} did not pass"
                )
            trace.route_end = pos
            return

    trace.notices.append(
        f"route {trace.route}: no step survived; the hand indicates nothing"
    )
    trace.route_end = None


def le_sas(ring: Ring, trace: Trace, tiered: list[str] | None) -> None:
    """Stage 8 - RELEASE. Le Sas's first admission condition, at last.

    le-sas.md lists four conditions. The cap has been enforced since METER.
    Load-bearing and non-theatrical are semantic and stay the barrel's. The
    first one - **Tiered** - was recorded as needing stages 6 and 7, and that
    was half right in a way worth correcting: the *assignment* of a tier is Le
    Sceptique's and is a person's job, but the file is explicit that "Le Sas
    checks that they exist, never what they say."

    Checking existence is not interpretation. So the check is the train's and
    always was; what was missing was a channel for tiers to arrive on, exactly
    as it was for proposals and for verdicts.

    `tiered` names the members whose output has been tiered. Anything admitted
    and absent from that list is held: "untiered material does not pass."

    Passing None skips the check entirely, and that is not the same as passing
    an empty list. None means no tiering was supplied and the train cannot
    know - so it holds nothing and claims nothing. An empty list means tiering
    was supplied and nothing was tiered, which holds everything. A gate that
    treated "I was not told" as "nothing qualifies" would be inventing a
    finding, and one that treated it as "everything qualifies" would be
    waving material through on an assumption.
    """
    if tiered is None:
        return

    ok = {fold(name) for name in tiered}
    for c in trace.candidates:
        if c.state != "active" or c.member.standing:
            continue
        # The crown is exempt, for the same reason le frein cannot stop it.
        # Holding Le Sauvegarder for want of a tier would make untiered
        # material block preservation - and preservation comes first precisely
        # because evidence loss cannot be undone. You preserve, then you tier.
        # A gate that can hold the crown is a gate that can lose the archive.
        if c.member.position == "crown":
            continue
        if fold(c.member.name) not in ok:
            c.state = "held"
            c.note = "untiered - did not pass Le Sas"

    untiered = [c.member.name for c in trace.candidates
                if c.note == "untiered - did not pass Le Sas"]
    if untiered:
        trace.failures.append(
            f"untiered: {len(untiered)} admitted member(s) carried no tier "
            "and were held"
        )


def route(
    ring: Ring,
    utterance: str,
    armed: str | None = None,
    proposals: list[Proposal] | None = None,
    verify: Callable[[str], bool] | None = None,
    require_evidence: bool = False,
    verdicts: list[Verdict] | None = None,
    authorize_cap: int | None = None,
    tiered: list[str] | None = None,
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
    trace = Trace(utterance=utterance, armed=armed,
                  cap_authorized=authorize_cap)

    trace.stages.append("WIND")
    trace.stages.append("EVALUATE")
    candidates = evaluate(ring, utterance, armed)
    routed = take_route(ring, trace, utterance)
    if routed:
        seen = {fold(c.member.name) for c in routed}
        candidates = routed + [c for c in candidates
                               if fold(c.member.name) not in seen]
        trace.stages.append("ROUTE->named")
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
    if verdicts:
        roue_a_colonnes(ring, trace, verdicts)
        trace.stages.append("VERDICT->colonnes")

    le_sas(ring, trace, tiered)
    settle_route_end(trace)
    trace.stages.append("RELEASE->sas")
    trace.stages.append("DISTRIBUTE")
    trace.stages.append("RECORD->crown")
    return trace


# --------------------------------------------------------------------------
# The barrel boundary
# --------------------------------------------------------------------------

def citations(ring: Ring) -> dict[str, tuple[str, ...]]:
    """The menu of quotable bullets, per member.

    admit_proposals() requires a citation verbatim, which is only a fair
    requirement if the barrel can see exactly what it is quoting. Without this
    a session has to reproduce a doctrine line from memory and any drift - a
    changed dash, a trimmed clause - is a rejection it cannot diagnose.

    The train still reads nothing for meaning. This hands over the same
    strings parse_activation() already extracted, and the barrel decides which
    one fired. Deciding that is the semantic half, which is the barrel's whole
    job and is exactly what the train must not do.

    Positives only. A member's prohibitions are deliberately NOT offered:
    this menu is the list of things it is valid to cite, and a guard is never
    valid grounds. Offering them made the menu itself the trap it exists to
    prevent - a barrel quoting faithfully from it could convene Le Redempteur
    on the sentence written to keep him dark. See admit_proposals() for what
    happens to one cited anyway.
    """
    return {m.name: m.bullets for m in ring.members if m.bullets}


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
        if cited in member.prohibitions:
            # Not the same error as a typo, and the trace must not say it is.
            # 'cited text not found' is a barrel quoting sloppily. This is a
            # barrel that found the sentence saying DO NOT fire on this and
            # offered it as grounds to fire - an inverted gate, which is what
            # a barrel rationalising toward a member it wants looks like from
            # here. Collapsing the two would make the louder failure the
            # quieter one.
            #
            # Decided (L'Operateur, 2026-08-28): rejected with its own failure
            # string, and the position stays dark. Not 'held' - held is for a
            # member that convened and was stopped at the door by the cap or
            # the brake, and this one never convened at all.
            trace.failures.append(
                f"rejected proposal: {member.name} cited a prohibition, not "
                f"an activation - its gate names this as a reason to stay "
                f"dark: {citation!r}"
            )
            continue

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
