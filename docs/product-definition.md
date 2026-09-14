# Product Definition — The Real Thesis

> **Supersedes**: the positioning in `prd.md` §1–2 and the feature framing in `vision.md`.
> **Status**: Draft 2. Written after concluding that the v1 positioning
> ("AI research report generator") was undifferentiated.
> **Date**: September 2026

---

## 1. Why the old positioning was weak

The original pitch was "AI writes you a stock research report." That is commoditised.
Anyone with an OpenAI key can build it in a weekend. Screener.in, Trendlyne, Tijori,
Perplexity Finance, and ChatGPT itself all overlap with it. There is no moat, no data
advantage, and nothing a user cannot get elsewhere.

The report is a **surface**, not a product. It cannot be the thing we sell.

---

## 2. The actual insight

India runs one of the most aggressive mandatory corporate disclosure regimes in the world.
Every listed company is legally forced to publish:

- quarterly results and (since April 2024) written earnings-call transcripts
- annual reports with subsidiaries, related-party transactions, segment revenue,
  contingent liabilities, auditor opinions and CARO clauses
- shareholding patterns every quarter, including promoter pledge
- promoter and insider trades within 2 trading days
- credit rating changes, auditor resignations, director resignations, with reasons
- every bulk and block deal, same day, with counterparty names

This is millions of pages a year. It is **completely public, completely free, and
completely unread**. No human can track it. Existing platforms ignore almost all of it
because they are built to display *numbers from a database*, not to read *documents over time*.

> **Every Indian platform shows you what a company IS — a snapshot of ratios today.**
> **Nobody shows you what CHANGED, and who else it touches.**

That gap is the product.

---

## 3. What we are building, in one sentence

**A disclosure intelligence engine for Indian equities: it reads every filing a listed
company is legally required to publish, tracks how the language and the numbers change
quarter over quarter, maps how companies are connected, and pushes only the changes that
matter — with the source paragraph attached.**

Not a report generator. A **monitoring layer over the disclosure system**.

The AI report still exists. It is now an output of the engine, not the engine itself.

---

## 4. Is this one product or four?

One. This is the important part.

The four differentiator ideas are not four separate products. They are four *readings*
of the same corpus, built on the same pipeline:

```
                   ONE INGESTION + EXTRACTION PIPELINE
        (filings -> parsed text -> structured claims + events + entities)
                                  |
        +--------------+----------+----------+------------------+
        v              v                     v                  v
   DIFF ENGINE    EVENT LOG            ENTITY GRAPH      SMART MONEY
   (same doc,     (what happened,      (who is           (who is
    two periods)   when, to whom)       connected)         buying)
        |              |                     |                  |
    Concall Diff   Pattern Match       Chain Reaction     Convergence
    AR Diff        Governance alerts   Peer exposure      Accumulation
    Credibility    Morning Dispatch    Interlocks         Pledge risk
```

- Concall Diff, Annual Report Diff and Management Credibility are **the same extraction
  code** run over different documents and time windows.
- Chain Reaction and Smart Money both need **entity resolution** (ticker ↔ company ↔
  subsidiary ↔ ISIN ↔ counterparty name). Build it once, both work.
- Pattern Match is just **querying the event log** that all the others write into.

Every feature makes the next one cheaper. That is what a real moat looks like: not one
clever feature, but a corpus that compounds.

---

## 5. Feasibility — honest audit of every data claim

This section exists because three claims in the earlier brainstorm were **factually wrong**,
and building on them would have failed.

### CONFIRMED REAL

| Data | Source | Frequency | Notes |
|---|---|---|---|
| Earnings call transcripts | Company site + exchange | Within 5 working days of the call (SEBI LODR Reg 46, from Apr 2024) | Only if a call happens. Near-total coverage in large/mid cap, patchy in small cap |
| Annual reports | BSE/NSE + company site | Yearly | Contains AOC-1 subsidiaries, Ind AS 24 related-party, Ind AS 108 segments, contingent liabilities, CARO clauses |
| Shareholding pattern | Exchange, Reg 31 | Quarterly, within 21 days | Promoter %, **pledge %**, FII, DII, public |
| Promoter / insider trades | SAST Reg 29, PIT Reg 7 | Within 2 trading days | This is the promoter radar feed |
| Bulk deals (>0.5% equity) | NSE/BSE | Same day, **with client name** | Near-real-time smart money |
| Block deals (≥ ₹10 Cr) | NSE/BSE | Same day, with name | |
| Mutual fund full portfolios | AMFI / AMC sites | Monthly, ~10 day lag | Allocation deltas per scheme |
| Delivery volume % | NSE | Daily, per security | Best free proxy for accumulation vs churn |
| Credit rating actions | CRISIL/ICRA/CARE + exchange filing | On event | Rating rationale PDFs are rich text, badly underused |
| Auditor resignation + reasons | Mandatory since SEBI's 2019 circular | On event | Highest-signal governance event in India |
| Corporate announcements | BSE/NSE feeds | Continuous | The firehose |

### THREE CORRECTIONS (the earlier brainstorm got these wrong)

**1. There is no daily per-stock FII data.**
The earlier example claimed *"FII net buyers in TRENT for 18 of last 22 sessions."*
That data does not exist publicly. NSE publishes FII/DII activity **aggregated across the
whole market**, not per stock. Per-stock foreign holding is visible only **quarterly**, in
the shareholding pattern.

→ **Fix**: Smart Money Convergence = bulk/block deals (daily, named) + insider and promoter
filings (2-day) + delivery-volume spikes (daily) + MF allocation deltas (monthly) +
FII/DII holding deltas (quarterly). Still a genuinely uncombined dataset. Just not daily FII.

**2. Indian annual reports do not name customers.**
The earlier example claimed *"Mphasis annual report lists TCS as a top-5 client."*
Indian companies disclose customer **concentration percentages anonymously**
("top 5 customers = 34% of revenue"). They almost never name them.

→ **Fix**: build the graph from what IS mandatory and named — subsidiaries and JVs (AOC-1),
**related-party transactions with names and amounts** (Ind AS 24), promoter group
cross-holdings, **common directorships** (board composition is disclosed), and auditors.
Chain-reaction alerts then run on **disclosed segment exposure**, not on named client links:
*"TCS BFSI revenue −15%. Mphasis derives 68% of revenue from BFSI per its segment reporting.
Mphasis reports in 12 days."* Same user value, real data underneath.

**3. Event pattern matching is not "easy".**
It needs years of backfilled, classified, deduplicated announcements before any usable
sample size exists. It is the heaviest data-engineering job of the four, not the lightest.

→ **Fix**: ship it *after* the event log has accumulated. And it must report **excess return
versus the sector index**, never raw returns — otherwise in a bull market every pattern looks
like it "works." Present as `11 of 14 prior instances outperformed the sector over 90 days`,
never as `79% win rate`.

### REAL BUT COST- OR EFFORT-GATED

- **MCA21 data** (director DINs, charges / secured borrowings filed): available, but priced
  per document with no bulk API. Defer. Director interlocks can be partially built from
  annual-report board disclosures without touching MCA.
- **Scraping at scale**: exchange sites rate-limit, and their terms restrict redistribution.
  Practical stance — transform rather than republish, cite and link every source, cache
  aggressively, respect limits. At real scale a licensed data vendor becomes a line item.
- **PDF reality**: a meaningful share of filings are scanned images needing OCR, and
  transcripts must have **speaker attribution parsed** so management statements are separated
  from analyst questions. Otherwise tone scoring is polluted by the analysts' own wording.

### REGULATORY — read this before writing the report prompt

The current spec outputs **"Buy / Hold / Avoid | Conviction X/10"**. That is a *research
recommendation* published to the public. SEBI's Research Analyst regulations govern exactly
that, and recent action against unregistered finfluencers makes this a live risk. The
"it isn't personalised" defence is weaker than the existing docs assume.

**This is a product opportunity, not just a constraint.** Drop the verdict and the conviction
score. Output **evidence, changes, flags and history with sources attached**, and let the user
form the view. That is:

- lower regulatory exposure
- more defensible — "we don't guess, we show you the paper trail"
- **more differentiated** — everyone else gives ratings; nobody gives the evidence chain

Confirm with a securities lawyer before public launch. This document is not legal advice.

---

## 6. What the user actually experiences

Constraint held throughout: **the only input a user ever gives is a watchlist.** Everything
after that is push.

**Minute 1** — sign up, type 8 tickers, connect Telegram. Done. No forms, no uploads.

**Minute 2** — immediately receive a "state of your watchlist" brief, before doing anything else:

```
Your 8 stocks, what changed in the last 90 days:
  3 have open governance flags
  2 had a clear tone shift on their last earnings call
  1 had a promoter pledge increase you probably missed
```

Value before effort. This is the hook.

**Every morning, 7:00 AM** — the Dispatch. Filtered filings from the last 18 hours, only
material ones, only for their stocks, each with the source line quoted.

**Within 2 hours of any event** — promoter buy, pledge change, rating action, auditor exit,
bulk deal in their stocks → push alert with historical context.

**Within 24 hours of any earnings call** — the Concall Diff lands automatically. They never
asked for it. This is the moment they screenshot it and send it to a friend.

**Any time** — type a ticker, get the full dossier: diffs, credibility ledger, governance
timeline, peer exposure, connected companies, smart-money activity. All sourced.

---

## 7. The four engines, defined

### Engine A — Diff (highest priority, build first)

Same document type, two time periods, structured comparison.

- **Concall Diff**: extract per-topic claims (guidance, margins, demand, capex, hiring,
  competition) from each quarter's transcript into a structured record, then compare the
  records. *Not a text diff — a claims diff.* Detects hedging, new worries, disappeared
  topics, tone shift.
- **Annual Report Diff**: risk factors added or removed, accounting policy changes,
  contingent liability movement, CARO clause changes, auditor language changes. Companies
  change these quietly and nobody reads them.
- **Credibility Ledger**: guidance given vs. actual delivered, 8 quarters, per company.
  Falls out of the same extraction for free.

### Engine B — Event log

Every filing classified into a typed event with entity, date and valuation context. Powers
the Morning Dispatch, governance tripwires, and later the pattern matching.

Governance tripwires are the high-value subset: pledge increase, auditor resignation, CFO
churn, independent director exit with cause, rating downgrade, adverse CARO remark. These
preceded nearly every Indian blow-up — Yes Bank, DHFL, CG Power, Zee.

### Engine C — Entity graph

Ownership, related-party, director-interlock and disclosed segment-exposure edges. Powers
chain-reaction alerts and genuinely comparable peer sets.

### Engine D — Smart money

Bulk/block deals + insider filings + delivery spikes + MF deltas + quarterly holding deltas,
scored for convergence. Corrected per §5.

---

## 8. Build order (realistic for one developer)

| Stage | Weeks | Ships | Why this order |
|---|---|---|---|
| **v0** | 2–3 | Concall Diff over Nifty 100, delivered to Telegram plus a simple web page | One engine, one universe, fully demo-able. This alone is the "wow" |
| **v1** | +4 | Announcement firehose → Morning Dispatch + governance tripwires + watchlist + web app | The daily habit forms here |
| **v2** | +4 | Smart money convergence + credibility ledger | Reuses the entity layer |
| **v3** | +6 | Entity graph + chain reaction | Highest moat, needs the corpus first |
| **v4** | later | Event pattern matching | Needs backfilled history to be statistically honest |

**Cut from early versions**: user PDF upload + RAG, portfolio upload, community feed,
WhatsApp, public API, and the generic ratio screener as a hero feature. The screener stays
as plumbing, not as the pitch.

**The hardest part is not the AI.** It is pipeline reliability — inconsistent PDFs, OCR,
entity resolution, deduplication, backfill. Budget roughly 70% of effort there.

---

## 9. The pitch

> India forces every listed company to publish thousands of pages a year: transcripts,
> annual reports, pledge disclosures, insider trades, auditor resignations. It is all public
> and almost none of it is read. Existing platforms show you ratios in a table. We read the
> filings, track what changed between quarters, map who is connected to whom, and push you
> the five things that actually matter this morning — with the source paragraph attached.
>
> We don't tell you what to buy. We tell you what changed.
