# Subtext

> **"What they're really saying."**

Subtext is a disclosure intelligence engine for Indian equities. It reads every filing a
listed company is legally required to publish — earnings call transcripts, annual reports,
shareholding patterns, insider trades, rating actions, auditor resignations — tracks how the
language and the numbers **change** quarter over quarter, maps how companies are connected,
and pushes only what matters, with the source paragraph attached.

**We don't tell you what to buy. We tell you what changed.**

---

## Start here

> [!IMPORTANT]
> **[`docs/product-definition.md`](docs/product-definition.md) is the current product thesis.**
> It supersedes the positioning in `prd.md` and the feature framing in `vision.md`, which
> still describe the earlier "AI report generator" product. Read it first.

| Doc | What it covers | Status |
|---|---|---|
| [`product-definition.md`](docs/product-definition.md) | **The real thesis** — what we're building, feasibility audit of every data source, the four engines, build order | ✅ Current |
| [`trd.md`](docs/trd.md) | Tech stack, architecture, API endpoints | ✅ Mostly current |
| [`backend-schema.md`](docs/backend-schema.md) | Database schema, auth, env vars | ✅ Mostly current |
| [`ux-design.md`](docs/ux-design.md) | Color palette, typography, component rules | ✅ Current |
| [`app-flow.md`](docs/app-flow.md) | Screens, user flows, Telegram bot flows | ⚠️ Predates new thesis |
| [`implementation-plan.md`](docs/implementation-plan.md) | 4-phase build plan with test commands | ⚠️ Superseded by §8 of product-definition |
| [`cursor-prompt.md`](docs/cursor-prompt.md) | Paste into Cursor as project context | ⚠️ Needs rewrite for new thesis |
| [`prd.md`](docs/prd.md) | Product requirements, personas | ❌ Old positioning |
| [`research.md`](docs/research.md) | Competitor analysis, tech research | ⚠️ Competitor section still valid |
| [`vision.md`](docs/vision.md) | Long-term roadmap, monetisation, moat stack | ❌ Old feature framing |

---

## The four engines

All four run on **one ingestion + extraction pipeline**. They are not separate products.

| Engine | What it does | Ships |
|---|---|---|
| **A — Diff** | Concall Diff, Annual Report Diff, Management Credibility Ledger | v0 |
| **B — Event log** | Morning Dispatch, governance tripwires (pledge, auditor exit, rating action) | v1 |
| **C — Entity graph** | Chain-reaction alerts, real peer sets, director interlocks | v3 |
| **D — Smart money** | Bulk/block deals + insider filings + delivery spikes + MF deltas | v2 |

See [`product-definition.md` §7](docs/product-definition.md) for definitions.

---

## Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- **Backend**: FastAPI (Python) + LangChain + Celery
- **AI**: LLM extraction over filings + RAG (pgvector)
- **DB**: Supabase PostgreSQL + pgvector
- **Cache**: Upstash Redis
- **Storage**: Cloudflare R2
- **Deploy**: Vercel (frontend) + Railway (backend)

---

## Hard Rules

- ❌ No order placement, no broker API, no capital deployment
- ❌ Never fabricate data — "no data" if missing
- ❌ **No Buy/Hold/Avoid verdict, no conviction score** — publishing a public research
  recommendation engages SEBI's Research Analyst regulations. Output evidence, changes and
  flags with sources; let the user form the view. See `product-definition.md` §5.
- ✅ Every claim carries its source paragraph and a link to the filing
- ✅ Every output has "Research Only — Not Investment Advice"
- ✅ The only input a user ever gives is a watchlist — everything else is push
- ✅ All thresholds in `config.yaml` — nothing hardcoded

---

## Build order

Per [`product-definition.md` §8](docs/product-definition.md):

| Stage | Ships |
|---|---|
| **v0** (2–3 wks) | Concall Diff over Nifty 100 → Telegram + simple web page |
| **v1** (+4 wks) | Announcement firehose → Morning Dispatch + governance tripwires + watchlist |
| **v2** (+4 wks) | Smart money convergence + credibility ledger |
| **v3** (+6 wks) | Entity graph + chain reaction |
| **v4** | Event pattern matching (needs backfilled history first) |

> The generic ratio screener stays as plumbing. It is **not** the pitch and not the first build.

---

## Quick Start

> **v0 is running.** Engine A (Concall Diff) works end-to-end against live BSE
> data. See [`docs/prototype-status.md`](docs/prototype-status.md) for verified
> coverage, design decisions and known gaps.

```bash
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY for extract/diff

python -m subtext transcripts INFY   # list earnings-call transcripts on BSE
python -m subtext parse INFY         # speaker attribution          [no API key]
python -m subtext extract INFY       # structured claims            [needs key]
python -m subtext diff INFY          # quarter-over-quarter diff    [needs key]
python -m pytest tests/ -v           # 12 tests, no network
```

Verified on INFY, TCS, HDFCBANK, ASIANPAINT, DMART, SUNPHARMA. Two known gaps
(RELIANCE files unattributed prose; TATAMOTORS ticker lookup) are documented.

---

## Name

`subtext.co` is the working domain. `.com` / `.in` are taken; `subtext.money` and
`subtext.finance` are also free. No financial-services trademark conflict found — the main
holder of subtext.com is Renaissance Learning, in education (different class). Formal
clearance in IP India classes 9, 36 and 42 is still pending.
