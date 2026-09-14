"""Compare two quarters of extracted claims.

Deliberately deterministic — no LLM here. The model's job was to normalise each
quarter into a comparable record; deciding what changed is arithmetic over those
records. That keeps the diff auditable and reproducible, and means the same two
inputs always produce the same output.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .claims import Claim, QuarterExtract, STANCE_SCORE, Topic

# Below this, a stance move is noise rather than a signal worth alerting on.
MATERIAL_SHIFT = 1


@dataclass
class StanceShift:
    topic: Topic
    old: Claim
    new: Claim

    @property
    def delta(self) -> int:
        return STANCE_SCORE[self.new.stance] - STANCE_SCORE[self.old.stance]

    @property
    def direction(self) -> str:
        return "softened" if self.delta < 0 else "hardened"


@dataclass
class Diff:
    ticker: str
    old_label: str
    new_label: str
    shifts: list[StanceShift] = field(default_factory=list)
    new_topics: list[Claim] = field(default_factory=list)
    dropped_topics: list[Claim] = field(default_factory=list)
    steady: list[StanceShift] = field(default_factory=list)
    tone_old: int = 0
    tone_new: int = 0

    @property
    def tone_delta(self) -> int:
        return self.tone_new - self.tone_old

    @property
    def is_empty(self) -> bool:
        return not (self.shifts or self.new_topics or self.dropped_topics)

    def headline(self) -> str:
        if self.is_empty:
            return "No material change in management's framing."
        bits = []
        soft = [s for s in self.shifts if s.delta < 0]
        hard = [s for s in self.shifts if s.delta > 0]
        if soft:
            bits.append(f"softened on {', '.join(s.topic.value for s in soft)}")
        if hard:
            bits.append(f"firmed up on {', '.join(s.topic.value for s in hard)}")
        if self.new_topics:
            bits.append(f"raised {', '.join(c.topic.value for c in self.new_topics)} for the first time")
        if self.dropped_topics:
            bits.append(f"stopped discussing {', '.join(c.topic.value for c in self.dropped_topics)}")
        return "Management " + "; ".join(bits) + "."


def compare(old: QuarterExtract, new: QuarterExtract, *, ticker: str) -> Diff:
    by_topic_old = {c.topic: c for c in old.claims}
    by_topic_new = {c.topic: c for c in new.claims}

    diff = Diff(
        ticker=ticker,
        old_label=old.period_label,
        new_label=new.period_label,
        tone_old=old.tone_score,
        tone_new=new.tone_score,
    )

    for topic, new_claim in by_topic_new.items():
        old_claim = by_topic_old.get(topic)
        if old_claim is None:
            diff.new_topics.append(new_claim)
            continue
        shift = StanceShift(topic=topic, old=old_claim, new=new_claim)
        (diff.shifts if abs(shift.delta) >= MATERIAL_SHIFT else diff.steady).append(shift)

    for topic, old_claim in by_topic_old.items():
        if topic not in by_topic_new:
            diff.dropped_topics.append(old_claim)

    diff.shifts.sort(key=lambda s: s.delta)          # biggest softening first
    diff.new_topics.sort(key=lambda c: c.topic.value)
    diff.dropped_topics.sort(key=lambda c: c.topic.value)
    return diff
