"""Tests for the deterministic core: diff arithmetic and quote verification.

Network and model calls are deliberately out of scope here — these cover the
logic that must never silently drift.

Run:  python -m pytest tests/ -v
"""
from pathlib import Path

import pytest

from subtext.claims import Claim, QuarterExtract, Stance, Topic, verify_quotes
from subtext.diffengine import compare
from subtext.transcript import MANAGEMENT, Transcript, Turn


def claim(topic, stance, quote="we said a thing", statement="stmt"):
    return Claim(topic=topic, statement=statement, stance=stance, quote=quote)


def extract(label, claims, tone=5):
    return QuarterExtract(period_label=label, claims=claims,
                          tone_score=tone, tone_rationale="because")


# ---------------------------------------------------------------- diff engine

def test_detects_softening():
    old = extract("Q4", [claim(Topic.guidance, Stance.confident)])
    new = extract("Q1", [claim(Topic.guidance, Stance.cautious)])
    d = compare(old, new, ticker="TEST")
    assert len(d.shifts) == 1
    assert d.shifts[0].delta == -3
    assert d.shifts[0].direction == "softened"


def test_detects_hardening():
    old = extract("Q4", [claim(Topic.margins, Stance.cautious)])
    new = extract("Q1", [claim(Topic.margins, Stance.positive)])
    d = compare(old, new, ticker="TEST")
    assert d.shifts[0].delta == 2
    assert d.shifts[0].direction == "hardened"


def test_new_topic_is_flagged():
    old = extract("Q4", [claim(Topic.demand, Stance.positive)])
    new = extract("Q1", [claim(Topic.demand, Stance.positive),
                         claim(Topic.competition, Stance.cautious)])
    d = compare(old, new, ticker="TEST")
    assert [c.topic for c in d.new_topics] == [Topic.competition]


def test_dropped_topic_is_flagged():
    """A topic management stops discussing is the signal people miss."""
    old = extract("Q4", [claim(Topic.margins, Stance.confident)])
    new = extract("Q1", [claim(Topic.demand, Stance.neutral)])
    d = compare(old, new, ticker="TEST")
    assert [c.topic for c in d.dropped_topics] == [Topic.margins]


def test_identical_stance_is_not_a_shift():
    same = [claim(Topic.guidance, Stance.positive)]
    d = compare(extract("Q4", same), extract("Q1", same), ticker="TEST")
    assert d.shifts == []
    assert len(d.steady) == 1
    assert d.is_empty


def test_shifts_sorted_worst_first():
    old = extract("Q4", [claim(Topic.guidance, Stance.confident),
                         claim(Topic.margins, Stance.neutral)])
    new = extract("Q1", [claim(Topic.guidance, Stance.negative),
                         claim(Topic.margins, Stance.positive)])
    d = compare(old, new, ticker="TEST")
    assert d.shifts[0].topic == Topic.guidance   # -4 before +1
    assert d.shifts[0].delta < d.shifts[1].delta


def test_tone_delta():
    d = compare(extract("Q4", [], tone=8), extract("Q1", [], tone=5), ticker="TEST")
    assert d.tone_delta == -3


def test_headline_mentions_what_changed():
    old = extract("Q4", [claim(Topic.guidance, Stance.confident)])
    new = extract("Q1", [claim(Topic.guidance, Stance.cautious)])
    assert "softened" in compare(old, new, ticker="TEST").headline()


# --------------------------------------------------------- quote verification

def _transcript(text):
    return Transcript(source=Path("x.pdf"),
                      turns=[Turn("CEO", MANAGEMENT, text)],
                      roles={"CEO": MANAGEMENT})


def test_verbatim_quote_passes():
    tr = _transcript("We are confident of achieving 8-10% revenue growth.")
    ex = extract("Q1", [claim(Topic.guidance, Stance.confident,
                              quote="We are confident of achieving 8-10% revenue growth.")])
    assert verify_quotes(ex, tr) == []


def test_fabricated_quote_is_caught():
    """The product's promise is a source line for every claim. Enforce it."""
    tr = _transcript("We are confident of achieving 8-10% revenue growth.")
    ex = extract("Q1", [claim(Topic.guidance, Stance.confident,
                              quote="We expect margins to collapse next year.")])
    assert len(verify_quotes(ex, tr)) == 1


def test_whitespace_differences_still_verify():
    tr = _transcript("We  remain   cautiously optimistic.")
    ex = extract("Q1", [claim(Topic.demand, Stance.cautious,
                              quote="We remain cautiously optimistic.")])
    assert verify_quotes(ex, tr) == []


def test_analyst_speech_is_not_valid_evidence():
    """Quotes must come from management, not from the analyst asking."""
    tr = Transcript(source=Path("x.pdf"),
                    turns=[Turn("Analyst", "analyst", "Are margins under pressure?")],
                    roles={"Analyst": "analyst"})
    ex = extract("Q1", [claim(Topic.margins, Stance.cautious,
                              quote="Are margins under pressure?")])
    assert len(verify_quotes(ex, tr)) == 1



# ------------------------------------------------------------------- telegram

def test_message_chunking_respects_limit():
    from subtext.telegram import _chunks
    text = "\n\n".join(f"block {i} " + "x" * 300 for i in range(40))
    parts = _chunks(text, limit=1000)
    assert len(parts) > 1
    assert all(len(p) <= 1000 for p in parts)


def test_chunking_never_splits_a_block():
    """A quote must never straddle two Telegram messages."""
    from subtext.telegram import _chunks
    blocks = [f"quote number {i}" for i in range(20)]
    parts = _chunks("\n\n".join(blocks), limit=120)
    rejoined = "\n\n".join(parts)
    for b in blocks:
        assert b in rejoined


def test_oversized_single_block_is_still_emitted():
    from subtext.telegram import _chunks
    parts = _chunks("y" * 500, limit=100)
    assert sum(len(p) for p in parts) == 500


def test_markdown_escaping():
    from subtext.telegram import _esc
    assert _esc("8-10% growth (CC).") == r"8\-10% growth \(CC\)\."


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
