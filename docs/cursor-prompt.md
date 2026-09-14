# Subtext — Agent Context

> Paste this into Cursor, Windsurf, Copilot, Gemini, or any coding assistant as
> project context before asking it to change anything.
>
> **Last verified against the code: September 2026.**

---

## What this is

Subtext is a **disclosure intelligence engine for Indian equities**. It reads
filings that listed companies are legally required to publish, tracks how their
language changes quarter over quarter, and reports what changed — with the
source sentence attached.

**It is not an "AI stock report generator".** That framing was abandoned as
undifferentiated. Read `docs/product-definition.md` before proposing features —
`prd.md` and `vision.md` still describe the old product and are stale.

Tagline: *"We don't tell you what to buy. We tell you what changed."*

---

## Current state: v0, Engine A only

Working end to end:

```
BSE announcement API
   -> transcript PDF (following cover-letter links where needed)
   -> speaker-attributed turns (management / analyst / journalist)
   -> structured claims per topic          [needs an LLM key]
   -> deterministic quarter-over-quarter diff
   -> terminal or Telegram output
```

```bash
python -m subtext transcripts INFY   # list earnings-call transcripts on BSE
python -m subtext parse INFY         # speaker attribution        [no key needed]
python -m subtext extract INFY       # structured claims          [needs key]
python -m subtext diff INFY          # the actual product         [needs key]
python -m subtext batch --universe 100   # coverage report        [no key needed]
python -m subtext providers          # which LLM backend is configured
python -m subtext telegram           # check bot token, find chat id
python -m pytest tests/ -v           # 16 tests, no network
```

---

## Module map

| File | Responsibility |
|---|---|
| `subtext/bse.py` | BSE API: ticker resolution, filing search, PDF download, disk cache |
| `subtext/transcript.py` | PDF -> speaker-attributed turns. The hardest code in the repo |
| `subtext/claims.py` | Transcript -> structured claims (Pydantic models + prompt) |
| `subtext/providers.py` | Pluggable LLM backends (Gemini/Groq/OpenRouter/GitHub/Anthropic) |
| `subtext/diffengine.py` | Compares two quarters. **Pure Python, no LLM** |
| `subtext/render.py` | Terminal output |
| `subtext/telegram.py` | Bot API delivery, message chunking |
| `subtext/batch.py` | Whole-index coverage runs |
| `subtext/universe.py` | Nifty constituents from NSE's published CSVs |
| `subtext/cli.py` | Argparse entry point |

---

## Design decisions — do not undo these

**1. Claims diff, not text diff.**
Transcripts are reworded every quarter, so a textual diff is pure noise. Each
quarter is normalised into a structured record (topic, stance, verbatim quote)
and the *records* are compared. If you are tempted to `difflib` two transcripts,
you have misunderstood the product.

**2. Only management turns reach the model.**
Analyst and journalist wording would contaminate the stance reading. This is why
speaker attribution is the hard core of the parser rather than a nicety. Never
pass a whole transcript to the LLM.

**3. The diff engine contains no LLM.**
The model normalises each quarter; arithmetic decides what changed. Same inputs
always produce the same output, and the result is auditable. Keep
`diffengine.py` free of API calls.

**4. Quotes are verified in code.**
`claims.verify_quotes()` checks every cited sentence appears verbatim in the
source. Unverified claims are **dropped from the diff**, not merely flagged. A
promise of evidence is worth nothing if nothing checks it.

**5. Refuse rather than emit something unsound.**
If a filing has no speaker attribution, the CLI declines and says why. If a
ticker is ambiguous, `resolve_ticker` raises instead of guessing. Silently
analysing the wrong company is worse than failing.

**6. No Buy/Hold/Avoid verdict, no conviction score.**
Publishing a public research recommendation engages SEBI's Research Analyst
regulations. Output evidence, changes and flags; let the user form the view.
See `product-definition.md` §5.

**7. Everything is cached on disk** (`data/cache/`, gitignored). Be polite to
BSE: keep the delay between requests, never parallelise the scraper hard.

---

## Transcript formats seen in the wild

Three so far. The parser branches on them. If coverage work is your task, this
is where it happens.

| Format | Example | Speaker marker | Status |
|---|---|---|---|
| Participants block | INFY, DMART | Name on its own line; roles from a `CORPORATE PARTICIPANTS:` header | works |
| Colon-delimited | TCS, HDFCBANK | `Name:` line; roles inferred from moderator's "from the line of X" hand-offs | works |
| Unattributed prose | RELIANCE | none — names appear only inside sentences | refused by design |

Companies also sometimes file a **cover letter linking to the transcript on
their own website** (the Adani group does this). `bse.fetch_transcript_pdf()`
detects that and follows the link via the PDF's link annotations.

Banks and NBFCs file the quarterly earnings call under the BSE category
**"Analyst / Investor Meet - Outcome"**, not "Earnings Call Transcript" — SBI,
Axis and Bajaj Finance all do. The filters in `bse.py` account for this.

---

## Bugs already found and fixed — do not reintroduce

Each of these was silent and produced plausible but wrong output:

1. **A page-furniture filter that deleted the CEO.** Dropping lines that repeat
   on >50% of pages seems sensible until you realise the busiest speaker's name
   is a standalone line on most pages. Only the top/bottom two lines per page
   are eligible now.
2. **`re.I` on the analyst-intro regex defeated `[A-Z]`**, so the capture ran
   past the name into "... from `<firm>`". No analyst ever matched and every
   analyst was labelled management. The flag is scoped `(?i:...)` now.
3. **Exclusion rules matched free text.** `HEADLINE` and `MORE` are long blurbs,
   not subject lines. Reliance mentions its analyst meet in passing and all four
   of its transcripts were discarded. Exclusions test `NEWSSUB` only.
4. **Only half of Infosys parsed.** One filing often holds two transcripts
   (press conference, then earnings call), each with its own participants block.
   Scanning only the first 400 lines missed the entire earnings call.
5. **Ligatures broke quote verification.** PDF text carries `speciﬁc` as one
   glyph. `_LIGATURES` normalises them.
6. **BSE serves older attachments from `AttachHis`, not `AttachLive`.**
7. **Fuzzy ticker search returned the wrong company.** `MARUTI` resolved to
   MARUTI GLOBAL INDUSTRIES, not Maruti Suzuki. Exact ticker match is required.

---

## Conventions

- Python 3.11+, standard library plus `requests`, `pymupdf`, `pydantic`
- No secrets in code. Everything via `.env` / `config.py`
- New LLM backends go in `providers.py`, never inline in `claims.py`
- Windows is a first-class target: force UTF-8 on stdout, use `pathlib`
- Tests must run without network or an API key

---

## What to build next, in order

1. **Prove the model path.** `extract` and `diff` have never made a real API
   call. Get a free key at aistudio.google.com/apikey, set `GEMINI_API_KEY` in
   `.env`, then run `python -m subtext diff INFY`. This is the top priority.
2. **Close the coverage gaps.** Run `python -m subtext batch --universe 100` and
   read `data/coverage_*.json`. The `roles_not_separated` bucket is the biggest
   remaining cluster — those parse fine but management and analysts land
   together, so stance readings cannot be trusted.
3. **Telegram scheduling** — a daily job that diffs watchlist tickers when a new
   transcript appears.
4. **Engine B**: the announcement firehose -> morning dispatch + governance
   tripwires (pledge changes, auditor resignations, rating actions). See
   `product-definition.md` §7.

---

## When in doubt

1. `docs/product-definition.md` — what we're building and why
2. `docs/prototype-status.md` — measured coverage and known gaps
3. `docs/trd.md` — stack and architecture (still broadly current)
4. Do not add dependencies without a reason. This runs on a student laptop.
