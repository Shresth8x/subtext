# v0 Prototype — Status

> **Date**: September 2026 | Engine A (Diff), Concall Diff only.
> Everything below was verified against live BSE data, not mocked.

---

## What works today

```bash
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY for extract/diff

python -m subtext transcripts INFY    # list earnings-call transcripts on BSE
python -m subtext parse INFY          # parse one, show speaker attribution   [no API key]
python -m subtext extract INFY        # structured management claims          [needs key]
python -m subtext diff INFY           # quarter-over-quarter diff             [needs key]
python -m pytest tests/ -v            # 12 tests, no network needed
```

The pipeline: **BSE announcement API → transcript PDF → speaker-attributed turns
→ structured claims (LLM) → deterministic diff → rendered output.**

---

## Verified against live data

Ticker resolution, filing search, PDF download and parsing all run against BSE's
public endpoints. Sweep across eight companies:

| Ticker | Transcripts found | Turns | Speakers | Mgmt words | Analyst words | Result |
|---|---|---|---|---|---|---|
| INFY | 5 | 171 | 27 | 13,122 | 3,831 | ✅ |
| TCS | 5 | 81 | 15 | 5,104 | 1,564 | ✅ |
| HDFCBANK | 1 | 99 | 13 | 4,273 | 1,424 | ✅ |
| ASIANPAINT | 5 | 57 | 10 | 6,807 | 882 | ✅ |
| DMART | 2 | 241 | 25 | 12,248 | 6,326 | ✅ |
| SUNPHARMA | 7 | 59 | 5 | 8,274 | 0 | ⚠️ roles |
| RELIANCE | 4 | — | — | — | — | ❌ no attribution |
| TATAMOTORS | — | — | — | — | — | ❌ ticker lookup |

**6 of 8 fully working. Both failures are understood, not mysterious.**

---

## Design decisions worth keeping

**Claims diff, not text diff.** Every sentence is reworded every quarter, so a
textual diff is pure noise. Each quarter is normalised into a structured record
(topic, stance, verbatim quote) and the records are compared.

**Only management text reaches the model.** Analyst and journalist wording would
otherwise contaminate the stance reading. This is why speaker attribution is the
hard core of the parser rather than a nicety.

**The diff itself is deterministic.** No LLM in `diffengine.py`. The model
normalises; arithmetic decides what changed. Same inputs always give the same
output, and the result is auditable.

**Quotes are verified in code.** `verify_quotes()` checks every cited sentence
appears verbatim in the source. Unverified claims are dropped from the diff, not
merely flagged. A promise of evidence is worth nothing unchecked.

**Everything is cached on disk.** HTTP responses, PDFs and extractions. Cheap
iteration, and polite to BSE.

---

## Transcript formats found in the wild

Three so far, and the parser needed different logic for each:

| Format | Example | Speaker marker | Supported |
|---|---|---|---|
| Participants block | INFY, DMART | Name on its own line, roles from a `CORPORATE PARTICIPANTS:` block | ✅ |
| Colon-delimited | TCS, HDFCBANK | `Name:` line; roles inferred from the moderator's "from the line of X" hand-offs | ✅ |
| Unattributed prose | RELIANCE | none — names appear only inside sentences | ❌ by design |

---

## Bugs found and fixed during the build

Worth recording, because each was silent and would have produced plausible but
wrong output:

1. **The page-furniture filter deleted the CEO.** Dropping lines that repeat on
   >50% of pages seems reasonable until you realise the busiest speaker's name
   is a standalone line on most pages. Salil Parekh vanished from the Infosys
   transcript. Fixed by limiting the filter to the top/bottom two lines per page.
2. **`re.I` on the analyst-intro regex defeated `[A-Z]`.** The capture ran past
   the name into "… from `<firm>`", so no analyst was ever matched and every
   analyst was labelled management — exactly the contamination the design exists
   to prevent. Fixed with a scoped `(?i:…)` flag.
3. **Exclusion rules matched free text.** `HEADLINE` and `MORE` are long blurbs,
   not subject lines. Reliance's earnings-call filing mentions its analyst meet
   in passing, and all four of its transcripts were being discarded. Exclusions
   now apply to `NEWSSUB` only.
4. **Only half of Infosys was parsed.** A single filing often holds two
   transcripts (press conference, then earnings call), each with its own
   participants block. Scanning only the first 400 lines missed the entire
   earnings call and every analyst in it.
5. **Ligatures broke quote verification.** PDF text carries `speciﬁc` as one
   glyph, so verbatim matching failed on any sentence containing it.
6. **BSE serves old attachments from a different path.** `AttachLive` 404s for
   older filings; `AttachHis` holds them. HDFCBANK was failing on this.

---

## Known gaps

**RELIANCE — no speaker attribution.** RIL files continuous prose with no turn
markers. The parser detects this and refuses rather than mixing analyst
questions into management commentary. Fixing it needs a different approach
(speaker diarisation from the agenda timings RIL publishes alongside).

**SUNPHARMA — roles not separated.** All speakers classified as management; the
moderator phrasing doesn't match any known intro pattern. Management text is
still captured, but it may include analyst questions, so stance readings from it
are not yet trustworthy.

**TATAMOTORS — ticker lookup fails.** BSE's search returns nothing for that
symbol. Needs a fallback to a scrip master list rather than live search.

**Not yet built:** Telegram delivery, scheduling, watchlists, the Nifty 100
batch run, and any persistence beyond the on-disk cache.

---

## Next

1. Batch-run the Nifty 100 to get a real coverage number across formats
2. Telegram delivery of a completed diff
3. Fix the two role-inference gaps (SUNPHARMA class of failure)
4. Only then: Engine B (announcement firehose → Morning Dispatch)
