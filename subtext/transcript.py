"""Earnings-call transcript PDF -> speaker-attributed turns.

Why this matters: tone and hedging must be measured on what MANAGEMENT said.
If analyst questions leak into the sample, the signal is polluted by the
analysts' own wording. So attribution is not a nicety — it's the whole point.

Indian transcripts put the speaker name on its own line with no colon, e.g.

    Salil Parekh
    So what has happened today with client discussions is ...

The reliable way in is the participants block at the top of every transcript
("CORPORATE PARTICIPANTS:", "ANALYSTS:", ...). We harvest candidate names from
it, then keep only the candidates that actually appear as a standalone line in
the body. That second step is what filters out affiliations like "Moneycontrol"
or "The Times of India", which look exactly like names otherwise.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

MANAGEMENT, ANALYST, JOURNALIST, MODERATOR, UNKNOWN = (
    "management", "analyst", "journalist", "moderator", "unknown")

_ROLE_HEADERS = [
    (re.compile(r"^\s*(corporate participants|company participants|management"
                r"|management team|participants from)\b.*$", re.I), MANAGEMENT),
    (re.compile(r"^\s*(analysts?|research analysts?|investors?)\s*:?\s*$", re.I), ANALYST),
    (re.compile(r"^\s*(journalists?|media|press)\s*:?\s*$", re.I), JOURNALIST),
    (re.compile(r"^\s*(moderator|operator)\s*:?\s*$", re.I), MODERATOR),
]

# "Mr. Salil Parekh", "Salil Parekh", "Sanjana B." — 1-5 capitalised words.
_NAME_SHAPE = re.compile(
    r"^(?:mr\.?|ms\.?|mrs\.?|dr\.?)?\s*"
    r"((?:[A-Z][A-Za-z'’.\-]{0,20}\s+){0,4}[A-Z][A-Za-z'’.\-]{0,20}\.?)\s*$")

# Job titles and media outlets sit on their own lines in the participants block
# and are shaped exactly like names. Reject them explicitly.
_TITLE_OR_OUTLET = re.compile(
    r"\b(chief|officer|president|director|chairman|chairperson|founder|head|"
    r"manager|partner|analyst|secretary|treasurer|executive|ceo|cfo|coo|cto|"
    r"md|vp|evp|svp|avp|whole[- ]?time|independent|managing|deputy|joint|group|"
    r"news|times|today|tv\d*|channel|media|network|research|securities|capital|"
    r"broking|brokerage|institutional|equities|invest(?:ments?)?|financial|"
    r"business|economic|express|mint|reuters|bloomberg|moneycontrol|"
    r"standard|herald|chronicle|journal|magazine|wire|post|daily|weekly)\b",
    re.I)


@dataclass
class Turn:
    speaker: str
    role: str
    text: str

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class Transcript:
    source: Path
    turns: list[Turn]
    roles: dict[str, str]

    def by_role(self, role: str) -> list[Turn]:
        return [t for t in self.turns if t.role == role]

    def management_text(self) -> str:
        return "\n\n".join(f"{t.speaker}: {t.text}" for t in self.by_role(MANAGEMENT))

    def stats(self) -> dict[str, int]:
        c = Counter(t.role for t in self.turns)
        return {"turns": len(self.turns), "speakers": len(self.roles), **c}

    @property
    def attributed(self) -> bool:
        """Whether this filing carries usable speaker attribution.

        Some companies (Reliance, for one) file the transcript as continuous
        prose with no speaker markers anywhere — names appear only inside
        sentences. There is no turn structure to recover. We refuse to extract
        from those rather than silently mixing analyst questions into what we
        report as management commentary.
        """
        return sum(t.words for t in self.by_role(MANAGEMENT)) >= 500


_LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
              "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}


def _clean(raw: str) -> str:
    # Ligatures matter: PDF text carries "speciﬁc", and leaving it in place
    # breaks verbatim quote verification against anything the model writes back.
    for lig, plain in _LIGATURES.items():
        raw = raw.replace(lig, plain)
    raw = (raw.replace("�", "'").replace("’", "'").replace("‘", "'")
              .replace("“", '"').replace("”", '"')
              .replace("–", "-").replace("—", "-").replace("\xa0", " "))
    return re.sub(r"[ \t]+", " ", raw)


def _read_pages(pdf: Path) -> list[str]:
    with pymupdf.open(pdf) as doc:
        return [_clean(p.get_text()) for p in doc]


def _strip_page_furniture(pages: list[str]) -> list[str]:
    """Drop running headers/footers.

    Only the top and bottom two lines of each page are eligible. A naive
    frequency filter over the whole page is actively harmful here: in a long
    transcript the busiest speaker's name appears as a standalone line on most
    pages, so a global "repeats a lot" rule deletes the CEO.
    """
    EDGE = 2
    if len(pages) < 3:
        return [ln for p in pages for ln in p.splitlines()]

    counts = Counter()
    for p in pages:
        rows = [l.strip() for l in p.splitlines() if l.strip()]
        edges = rows[:EDGE] + rows[-EDGE:]
        for ln in {l for l in edges if len(l) <= 90}:
            counts[re.sub(r"\d+", "#", ln)] += 1
    noisy = {k for k, v in counts.items() if v >= max(3, int(len(pages) * 0.5))}

    out = []
    for p in pages:
        rows = p.splitlines()
        stripped = [l.strip() for l in rows if l.strip()]
        edge_set = set(stripped[:EDGE] + stripped[-EDGE:])
        for ln in rows:
            s = ln.strip()
            if s in edge_set and re.sub(r"\d+", "#", s) in noisy:
                continue
            out.append(ln)
    return out


def _candidate_names(lines: list[str]) -> tuple[dict[str, str], set[int]]:
    """Harvest name -> role from every participants block in the document.

    A single filing often carries two transcripts (press conference, then
    earnings call), each with its own block — so we scan the whole document,
    not just the head. Returns the candidates plus the line indices consumed by
    the blocks, so the caller can validate names against the body alone.
    """
    cands: dict[str, str] = {}
    block_idx: set[int] = set()
    role, run = None, 0

    for i, ln in enumerate(lines):
        s = ln.strip()
        matched = next((r for pat, r in _ROLE_HEADERS if pat.match(s)), None) if s else None
        if matched:
            role, run = matched, 0
            block_idx.add(i)
            continue
        if role is None:
            continue

        run += 1
        # A block is a short list. Prose, a long line, or a long run ends it.
        if run > 80 or len(s) > 90 or (len(s) > 40 and ". " in s):
            role = None
            continue
        block_idx.add(i)
        if not s:
            continue
        m = _NAME_SHAPE.match(s)
        if m and not _TITLE_OR_OUTLET.search(s) and not _JUNK_NAME.match(m.group(1).strip()):
            cands.setdefault(m.group(1).strip().rstrip("."), role)
    return cands, block_idx


def _validate(cands: dict[str, str], lines: list[str],
              block_idx: set[int]) -> dict[str, str]:
    """Keep only candidates that open a turn in the BODY.

    Validating against the whole document would readmit everything, since the
    participants block itself lists affiliations ("Reuters", "Moneycontrol") on
    their own lines and they look identical to names.
    """
    body = Counter(
        l.strip().rstrip(":").rstrip(".")
        for i, l in enumerate(lines) if l.strip() and i not in block_idx
    )
    return {n: r for n, r in cands.items() if body[n] >= 1}


_COLON_SPEAKER = re.compile(r"^\s*([A-Z][A-Za-z'.\- ]{2,40}):\s*(.*)$")
_MODERATOR_NAME = re.compile(r"^(moderator|operator|host)$", re.I)
# Indian calls are almost all run by the same conference vendors, and the
# moderator's hand-off line is near-universal: "...from the line of X from Y."
# The case-insensitive flag is scoped to the lead-in only. Applying re.I to the
# whole pattern would make [A-Z] match lowercase, and the capture would run past
# the name into "... from <firm>".
_INTRO = re.compile(
    r"(?i:from the line of|next question (?:is |comes )?from|question (?:is )?from"
    r"|we have (?:a |the next )?question from|now take a question from)"
    r"\s+(?i:mr\.?\s+|ms\.?\s+|mrs\.?\s+|dr\.?\s+)?"
    r"([A-Z][A-Za-z'.\-]+(?:\s+[A-Z][A-Za-z'.\-]+){0,3})")

# Lines that pass the name shape but are obviously not people.
_JUNK_NAME = re.compile(
    r"^(date|time|venue|subject|place|ref|sub|note|page|thank you|"
    r"agenda|annexure|regards|sincerely)$", re.I)


def _colon_speakers(lines: list[str]) -> dict[str, str]:
    """Speaker map for transcripts with no participants block (e.g. TCS).

    These use `Name:` as the turn marker. With no block to read roles from, we
    infer them: whoever the moderator introduces "from the line of ..." is an
    analyst; everyone else who speaks repeatedly is management.
    """
    hits = Counter()
    for ln in lines:
        m = _COLON_SPEAKER.match(ln)
        if m:
            hits[m.group(1).strip()] += 1

    # Scan the joined text, not line by line: PDF extraction wraps sentences, so
    # an introduction can straddle a line break ("...from the line of Sandeep\nShah
    # from Equirus") and a per-line scan silently misses that analyst.
    blob = " ".join(l.strip() for l in lines)
    introduced = {m.group(1).strip() for m in _INTRO.finditer(blob)}

    roles: dict[str, str] = {}
    for name, count in hits.items():
        if _JUNK_NAME.match(name):
            continue
        if _MODERATOR_NAME.match(name):
            roles[name] = MODERATOR
        elif count >= 2:
            roles[name] = ANALYST if name in introduced else MANAGEMENT
    return roles


def parse(pdf: Path) -> Transcript:
    lines = _strip_page_furniture(_read_pages(pdf))

    # Two layouts in the wild: a participants block up top (Infosys style), or
    # bare `Name:` turn markers with no block at all (TCS style). Try the block
    # first, fall back when it yields nothing usable.
    cands, block_idx = _candidate_names(lines)
    roles = _validate(cands, lines, block_idx)
    if not any(r == MANAGEMENT for r in roles.values()) or len(roles) < 2:
        colon = _colon_speakers(lines)
        if len(colon) > len(roles):
            roles = colon

    turns: list[Turn] = []
    speaker, buf = None, []

    def flush():
        if speaker and buf:
            body = " ".join(x.strip() for x in buf if x.strip()).strip()
            if body:
                turns.append(Turn(speaker, roles.get(speaker, UNKNOWN), body))

    for ln in lines:
        bare = ln.strip().rstrip(":").rstrip(".")
        if bare in roles:
            flush()
            speaker, buf = bare, []
            continue
        m = _COLON_SPEAKER.match(ln)
        if m and m.group(1).strip() in roles:
            flush()
            speaker, buf = m.group(1).strip(), [m.group(2)]
            continue
        if speaker:
            buf.append(ln)
    flush()

    return Transcript(source=pdf, turns=turns, roles=roles)
