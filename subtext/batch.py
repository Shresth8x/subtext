"""Run the ingest+parse pipeline across a whole index and report coverage.

Deliberately stops before the model call. The open question for the product is
"does the pipeline survive the variety of real filings?", and that is answered
without spending a rupee on inference.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import bse, config
from .transcript import ANALYST, JOURNALIST, MANAGEMENT, parse as parse_pdf

# Why a ticker produced no usable diff input. Knowing the distribution of these
# matters more than the headline pass rate.
OK = "ok"
NO_TICKER = "ticker_not_found"
NO_TRANSCRIPT = "no_transcript_filed"
ONE_ONLY = "only_one_transcript"
NO_ATTRIBUTION = "no_speaker_attribution"
NO_ROLES = "roles_not_separated"
DOWNLOAD_FAILED = "download_failed"
PARSE_ERROR = "parse_error"


@dataclass
class Row:
    ticker: str
    status: str
    transcripts: int = 0
    turns: int = 0
    speakers: int = 0
    mgmt_words: int = 0
    other_words: int = 0
    name: str = ""
    detail: str = ""


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)
    seconds: float = 0.0

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            out[r.status] = out.get(r.status, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    @property
    def usable(self) -> list[Row]:
        return [r for r in self.rows if r.status == OK]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(
            {"seconds": round(self.seconds, 1), "counts": self.counts(),
             "rows": [asdict(r) for r in self.rows]}, indent=2), "utf-8")


def run_one(ticker: str, *, months: int) -> Row:
    try:
        scrip = bse.resolve_ticker(ticker)
    except Exception as e:
        return Row(ticker, NO_TICKER, detail=str(e)[:80])

    try:
        found = bse.find_transcripts(scrip.code, months_back=months)
    except Exception as e:
        return Row(ticker, PARSE_ERROR, name=scrip.name, detail=f"search: {str(e)[:70]}")

    if not found:
        return Row(ticker, NO_TRANSCRIPT, name=scrip.name)

    try:
        path = bse.fetch_transcript_pdf(found[0])
    except Exception as e:
        return Row(ticker, DOWNLOAD_FAILED, transcripts=len(found),
                   name=scrip.name, detail=str(e)[:80])

    try:
        tr = parse_pdf(path)
    except Exception as e:
        return Row(ticker, PARSE_ERROR, transcripts=len(found),
                   name=scrip.name, detail=f"{type(e).__name__}: {str(e)[:60]}")

    mgmt = sum(t.words for t in tr.by_role(MANAGEMENT))
    other = sum(t.words for t in tr.by_role(ANALYST)) + \
        sum(t.words for t in tr.by_role(JOURNALIST))
    row = Row(ticker, OK, transcripts=len(found), turns=len(tr.turns),
              speakers=len(tr.roles), mgmt_words=mgmt, other_words=other,
              name=scrip.name)

    if not tr.attributed:
        row.status = NO_ATTRIBUTION
    elif other == 0 and len(tr.roles) > 2:
        # Everyone landed in one bucket. Management text is probably polluted
        # with analyst questions, so stance readings can't be trusted.
        row.status = NO_ROLES
    elif len(found) < 2:
        row.status = ONE_ONLY          # parses fine, but nothing to diff against
    return row


def run(tickers: list[str], *, months: int = 14, verbose: bool = True) -> Report:
    rep = Report()
    t0 = time.time()
    for i, tk in enumerate(tickers, 1):
        row = run_one(tk, months=months)
        rep.rows.append(row)
        if verbose:
            print(f"  [{i:>3}/{len(tickers)}] {tk:<14}{row.status:<24}"
                  f"{row.mgmt_words:>7}w  {row.name[:30]}", flush=True)
    rep.seconds = time.time() - t0
    return rep


def format_report(rep: Report) -> str:
    total = len(rep.rows)
    counts = rep.counts()
    lines = ["", "=" * 66,
             f"  COVERAGE — {total} tickers in {rep.seconds/60:.1f} min", "=" * 66, ""]
    for status, n in counts.items():
        bar = "█" * int(40 * n / total)
        lines.append(f"  {status:<26}{n:>4}  {n/total:>5.0%}  {bar}")

    diffable = counts.get(OK, 0)
    lines += ["", f"  Diffable today: {diffable}/{total} ({diffable/total:.0%})", ""]

    stuck = [r for r in rep.rows if r.status not in (OK, ONE_ONLY)]
    if stuck:
        lines.append("  NOT USABLE:")
        for r in sorted(stuck, key=lambda r: r.status):
            lines.append(f"    {r.ticker:<14}{r.status:<24}{r.detail[:34]}")
    return "\n".join(lines)
