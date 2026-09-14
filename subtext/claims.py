"""Transcript -> structured management claims, one record per quarter.

This is deliberately NOT a text diff. Text diffs on transcripts produce noise:
every sentence is reworded every quarter. What we want is a *claims* diff — the
same topics, quarter over quarter, with a stance attached. So we normalise each
quarter into a comparable record first, then compare records (see diffengine).

Only management turns are sent to the model. Analyst and journalist wording
would otherwise contaminate the stance reading.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from . import config
from .transcript import Transcript


class Topic(str, Enum):
    guidance = "guidance"
    margins = "margins"
    demand = "demand"
    capital_allocation = "capital_allocation"
    capex = "capex"
    hiring = "hiring"
    competition = "competition"
    risk = "risk"


class Stance(str, Enum):
    confident = "confident"
    positive = "positive"
    neutral = "neutral"
    cautious = "cautious"
    negative = "negative"


STANCE_SCORE = {
    Stance.confident: 5, Stance.positive: 4, Stance.neutral: 3,
    Stance.cautious: 2, Stance.negative: 1,
}


class Claim(BaseModel):
    topic: Topic
    statement: str = Field(description="The claim in one neutral sentence.")
    stance: Stance = Field(description="How committed management sounds.")
    quote: str = Field(description="Verbatim sentence from the transcript. Never paraphrase.")
    figures: list[str] = Field(default_factory=list,
                               description="Numbers management cited, verbatim. Empty if none.")


class QuarterExtract(BaseModel):
    period_label: str = Field(description='Quarter as management refers to it, e.g. "Q1 FY27".')
    claims: list[Claim]
    tone_score: int = Field(ge=1, le=10, description="1 defensive, 10 highly confident.")
    tone_rationale: str


SYSTEM = """You are analysing an Indian listed company's earnings call transcript.

Extract what MANAGEMENT claimed, topic by topic. Rules — breaking any of these
is a failure:

1. Use only the text provided. Never add outside knowledge about the company.
2. `quote` must be copied VERBATIM from the transcript, word for word. If you
   cannot find a supporting sentence, do not emit the claim at all.
3. If a topic is not discussed, omit it. Do not invent a neutral placeholder.
4. `figures` holds only numbers management actually said. Empty list otherwise.
5. Stance reflects how committed the language is, not whether the news is good.
   "We are confident of 8-10% growth" is confident. "We remain watchful of the
   demand environment" is cautious, even though nothing bad was announced.
6. At most one claim per topic — the most consequential one."""


def _fingerprint(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:20]


def extract(transcript: Transcript, *, ticker: str, period_hint: str = "",
            refresh: bool = False) -> QuarterExtract:
    """Extract one quarter's claims. Cached on disk by content hash."""
    body = transcript.management_text()
    if not body.strip():
        raise ValueError("No management turns found — cannot extract claims.")

    cache = config.CACHE_DIR / "claims" / f"{ticker}_{_fingerprint(body + config.MODEL)}.json"
    if cache.exists() and not refresh:
        return QuarterExtract.model_validate_json(cache.read_text("utf-8"))

    import anthropic

    # An unset ANTHROPIC_API_KEY does not mean there are no credentials: the SDK
    # also resolves an OAuth profile written by `ant auth login`. Construct with
    # no arguments in that case and let the SDK do its own lookup.
    try:
        client = (anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                  if config.ANTHROPIC_API_KEY else anthropic.Anthropic())
    except Exception as e:
        raise RuntimeError(
            f"No Anthropic credentials found ({e}). Either add ANTHROPIC_API_KEY "
            f"to .env, or run `ant auth login`."
        ) from e
    prompt = (
        f"Company: {ticker}\n"
        f"Period (from the filing, may be approximate): {period_hint or 'unknown'}\n\n"
        f"Management remarks from the earnings call:\n\n{body}"
    )
    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=QuarterExtract,
    )
    result: QuarterExtract = response.parsed_output

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(result.model_dump_json(indent=2), "utf-8")
    return result


def _normalise(s: str) -> str:
    return " ".join(s.lower().split())


def verify_quotes(extract_: QuarterExtract, transcript: Transcript) -> list[Claim]:
    """Return claims whose `quote` is NOT found verbatim in the transcript.

    The product promise is that every claim carries its source sentence. That
    promise is only worth something if it is checked, so we check it in code
    rather than trusting the model's word.
    """
    haystack = _normalise(transcript.management_text())
    return [c for c in extract_.claims if _normalise(c.quote) not in haystack]


def save(extract_: QuarterExtract, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(extract_.model_dump_json(indent=2), "utf-8")


def load(path: Path) -> QuarterExtract:
    return QuarterExtract.model_validate(json.loads(path.read_text("utf-8")))
