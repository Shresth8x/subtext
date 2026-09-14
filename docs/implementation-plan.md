# Subtext — Implementation Plan

> **Version**: 1.0 | **Date**: September 2026

---

## Overview

4 phases. Each phase ships something demonstrable. Phase 1 is the hackathon MVP.

| Phase | Duration | Ships |
|---|---|---|
| Phase 1 | Week 1–2 | Working screener + Telegram alerts (the spec from images) |
| Phase 2 | Week 3–4 | Full web app + AI report generator + streaming |
| Phase 3 | Week 5–6 | PDF upload + RAG + report history + watchlist |
| Phase 4 | Week 7–8 | Polish, sharing, public pages, deployment, monitoring |

---

## Phase 1 — Screener + Telegram (Hackathon Baseline)

**Goal**: A working Python script that screens Nifty 500, generates a mini AI report, and sends it to Telegram. One command to run it: `python main.py --phase 1`. This is what you demo first to prove it works.

### 1.1 Setup & Scaffolding

- [ ] Create project directory: `subtext/`
- [ ] `python -m venv venv` + activate
- [ ] Create `requirements.txt` with initial deps:
  ```
  fastapi uvicorn
  yfinance pandas pandas-ta
  openai langchain langchain-openai
  python-telegram-bot
  celery redis
  supabase
  python-dotenv pydantic-settings
  httpx aiohttp
  ```
- [ ] Create `config.yaml` with default screener thresholds
- [ ] Create `.env` from template (no hardcoded secrets)
- [ ] Create `main.py` CLI entry point with `--phase` flag

**Test**: `python main.py --help` shows all available options.

### 1.2 Data Fetcher

- [ ] `services/data_fetcher.py`
  - `fetch_fundamentals(ticker: str) -> dict | None`
    - Uses `yfinance.Ticker(f"{ticker}.NS")`
    - Returns: pe, roe, debt_to_equity, revenue_growth, promoter_holding, price, market_cap
    - Returns `None` if any critical field is missing (never fabricate)
  - `fetch_technicals(ticker: str) -> dict | None`
    - Uses `yfinance` history + `pandas_ta`
    - Returns: ema50, ema200, rsi, volume, above_200_ema (bool)
  - `get_nifty500_tickers() -> list[str]`
    - Reads from `data/nifty500.csv` (download once from NSE website)

**Test** (automated):
```bash
python -m pytest tests/test_data_fetcher.py -v
# Tests: fetch RELIANCE fundamentals, check no None values, check types
# Tests: fetch_technicals for INFY, check EMA calculated correctly
# Tests: missing ticker returns None (not exception)
```

### 1.3 Screener Engine

- [ ] `services/screener_engine.py`
  - `load_config(path: str) -> ScreenerConfig`
  - `passes_filters(data: dict, config: ScreenerConfig) -> bool`
  - `run_screener(config: ScreenerConfig) -> list[StockResult]`
    - Iterates tickers, calls fetch_fundamentals + fetch_technicals
    - Skips tickers where data is None (logs them)
    - Returns list of passing stocks

**Test** (automated):
```bash
python -m pytest tests/test_screener.py -v
# Tests: known good stock (with mocked data) passes correct filters
# Tests: known bad stock fails on PE filter
# Tests: stock with None data is skipped, not crashed
# Tests: config disabling a filter makes it pass through
```

### 1.4 Telegram Bot

- [ ] Get bot token from @BotFather
- [ ] `services/telegram_bot.py`
  - `send_screener_alert(chat_id: str, results: list[StockResult])`
    - Formats message per spec (bear counter-point + disclaimer mandatory)
  - `send_mini_report(chat_id: str, ticker: str, data: dict)`
- [ ] Add `/start` and `/research TICKER` commands via polling (no webhook in phase 1)

**Test** (manual):
- Run `python main.py --phase 1`
- Confirm Telegram message received
- Confirm message contains bear counter-point
- Confirm "Research Only" disclaimer present

### 1.5 Cost Logger

- [ ] `services/cost_logger.py`
  - Log token usage per run to `runs.log`
  - Print estimated cost to console: `[COST] Run cost: ~$0.023 | Total this month: ~$0.12`

---

## Phase 2 — Web App + AI Report Generator

**Goal**: A beautiful Next.js app where users can search stocks, get streaming AI reports, and manage their watchlist.

### 2.1 Next.js App Setup

- [ ] `npx create-next-app@latest subtext-web --typescript --tailwind --app`
- [ ] Install shadcn/ui: `npx shadcn@latest init`
- [ ] Add required components: `npx shadcn@latest add button card input badge table`
- [ ] Set up Supabase client: `npm install @supabase/supabase-js`
- [ ] Set up Zustand: `npm install zustand`
- [ ] Set up fonts: Inter + JetBrains Mono via `next/font/google`
- [ ] Implement design tokens in `globals.css` (all CSS vars from ux-design.md)

**Test**: `npm run dev` → app loads at localhost:3000 with correct fonts and colors.

### 2.2 Auth (Supabase)

- [ ] Create Supabase project
- [ ] Enable Email + Google OAuth providers
- [ ] Implement `(auth)/login/page.tsx` and `(auth)/signup/page.tsx`
- [ ] Create `middleware.ts` — redirect unauthenticated users to /login
- [ ] `lib/supabase.ts` — browser + server Supabase clients

**Test** (automated):
```bash
# Playwright e2e test
npx playwright test tests/auth.spec.ts
# Tests: signup flow completes, redirects to dashboard
# Tests: login with wrong password shows error
# Tests: unauthenticated /dashboard redirects to /login
```

### 2.3 FastAPI Backend Setup

- [ ] Create `subtext-backend/` directory
- [ ] `main.py` with CORS, health route, Supabase JWT middleware
- [ ] Deploy to Railway (free tier): connect GitHub repo
- [ ] Set all env vars in Railway dashboard

**Test**:
```bash
curl https://api.subtext.co/health
# → {"status": "ok", "version": "1.0.0"}
```

### 2.4 Research Generator UI

- [ ] `app/(dashboard)/research/page.tsx`
  - Stock search autocomplete (calls `/api/tickers/search?q=`)
  - "Generate Report" button
  - SSE streaming display (EventSource API)
- [ ] `components/research/ReportStream.tsx` — streaming markdown renderer
- [ ] `components/research/ReportSection.tsx` — individual section card with fade-in

**Test** (manual + automated):
```bash
npx playwright test tests/research.spec.ts
# Tests: search "reliance" → autocomplete shows RELIANCE
# Tests: clicking Generate fires POST /research/generate
# Tests: SSE stream event arrives → text appears in DOM
# Tests: Bear counter-point card always present in output
```

### 2.5 FastAPI Report Generator

- [ ] `routers/research.py`
  - `POST /research/generate` → creates report record, queues Celery task, returns job_id
  - `GET /research/stream/{job_id}` → SSE endpoint
- [ ] `services/ai_analyst.py`
  - Builds context from yfinance data
  - Constructs research prompt from template
  - Streams GPT-4o response
  - Extracts structured fields (verdict, conviction, bear counterpoint)

**Test** (automated):
```bash
python -m pytest tests/test_ai_analyst.py -v
# Tests: analyst returns all 6 sections
# Tests: verdict is one of BUY/HOLD/AVOID
# Tests: bear_counterpoint is non-empty
# Tests: if yfinance returns None PE, output contains "no data" not a fabricated number
```

---

## Phase 3 — PDF Upload + RAG + History + Watchlist

### 3.1 PDF Upload to R2

- [ ] Frontend: `components/research/PDFDropzone.tsx` (drag-and-drop)
- [ ] API: `POST /upload/pdf` → presigned R2 URL → client uploads directly
- [ ] Backend: `services/storage.py` — R2 operations via boto3

**Test**:
```bash
python -m pytest tests/test_storage.py -v
# Tests: upload PDF → get back file_id
# Tests: file retrievable via signed URL
# Tests: non-PDF file rejected (400)
# Tests: file > 50MB rejected (413)
```

### 3.2 RAG Pipeline

- [ ] `services/pdf_processor.py`
  - Download PDF from R2 → PyMuPDF → extract text
  - Chunk with RecursiveCharacterTextSplitter
  - Embed with OpenAI text-embedding-3-small
  - Store in pgvector (document_embeddings table)
- [ ] Update `ai_analyst.py` to retrieve relevant chunks when file_ids provided

**Test** (automated):
```bash
python -m pytest tests/test_pdf_processor.py -v
# Tests: sample annual report PDF → chunks created
# Tests: embedding shape is (1536,)
# Tests: similarity search returns relevant chunks
# Tests: report generated WITH PDF context vs. without — different outputs
```

### 3.3 Report History

- [ ] `app/(dashboard)/research/[reportId]/page.tsx` — full report viewer
- [ ] Dashboard: recent reports list (last 5, with verdict badge)
- [ ] `GET /reports` — paginated list
- [ ] `GET /reports/{id}` — single report

**Test**:
```bash
npx playwright test tests/history.spec.ts
# Tests: generate report → appears in history
# Tests: clicking history item → loads report viewer
# Tests: shared report URL works without auth
```

### 3.4 Watchlist

- [ ] `app/(dashboard)/watchlist/page.tsx`
- [ ] `POST /watchlist`, `DELETE /watchlist/{ticker}`, `GET /watchlist`
- [ ] "Add to watchlist" button in report viewer action bar

**Test** (automated):
```bash
python -m pytest tests/test_watchlist.py -v
# Tests: add RELIANCE → appears in watchlist
# Tests: add same ticker twice → no duplicate (unique constraint)
# Tests: delete → gone from list
```

---

## Phase 4 — Polish, Sharing, Deployment, Monitoring

### 4.1 Report Sharing

- [ ] "Share" button generates public URL: `subtext.co/research/[share_token]`
- [ ] Public report page (no auth) — with "Sign up to generate your own" CTA
- [ ] Report pages indexed by Google (SEO — JSON-LD structured data)
- [ ] Open Graph meta tags for link previews (stock name + verdict)

### 4.2 Telegram Webhook (Production)

- [ ] Switch from polling to webhook in production (faster, no polling overhead)
- [ ] `POST /telegram/webhook` endpoint in FastAPI
- [ ] Register webhook: `https://api.telegram.org/bot{TOKEN}/setWebhook?url=...`

### 4.3 Screener in Production

- [ ] Celery Beat for scheduled screener runs (cron)
- [ ] Screener config UI: `app/(dashboard)/screener/page.tsx`
- [ ] Results table with sort/filter
- [ ] "Run now" manual trigger

**Test** (automated):
```bash
python -m pytest tests/test_screener_task.py -v
# Tests: Celery task triggers, runs for test universe (5 tickers)
# Tests: results saved to DB
# Tests: Telegram message sent (mocked)
```

### 4.4 Monitoring & Alerts

- [ ] Sentry integration (frontend + backend)
- [ ] Health check endpoint with DB + Redis ping
- [ ] Cost log dashboard in admin (simple table of run_cost_log)
- [ ] Alerting: if screener fails 2x in a row → notify admin via Telegram

### 4.5 Production Deployment Checklist

- [ ] Frontend: Deploy to Vercel (connect GitHub)
- [ ] Backend: Deploy to Railway (Docker, auto-deploy on push to main)
- [ ] Database: Supabase production project (separate from dev)
- [ ] Redis: Upstash (serverless Redis, generous free tier)
- [ ] R2: Cloudflare R2 buckets created and CORS configured
- [ ] Custom domain: subtext.co → Vercel, api.subtext.co → Railway
- [ ] SSL: Automatic via Vercel + Railway
- [ ] Environment variables: All set in Vercel + Railway dashboards

**Final Integration Test** (manual):
1. Sign up as new user
2. Search for "Reliance" → generate report
3. Upload an annual report PDF → generate report with PDF context
4. Add to watchlist → verify appears
5. Configure screener → trigger manual run → verify Telegram alert received
6. Share report → open in incognito → verify loads without auth
7. Check Sentry dashboard → zero errors

---

## Automated Testing Summary

| Test Suite | Command | Coverage |
|---|---|---|
| Backend unit tests | `pytest tests/ -v` | Data fetcher, screener, AI analyst, storage, cost logger |
| Backend integration | `pytest tests/integration/ -v` | Report generation end-to-end, screener task |
| Frontend e2e | `npx playwright test` | Auth, research flow, history, watchlist |
| Load test (Phase 4) | `k6 run load_test.js` | 100 concurrent report requests |

---

## Folder Structure (Final)

```
subtext/                          # Root repo
├── subtext-web/                  # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── store/
│   ├── types/
│   └── tests/                      # Playwright tests
│
├── subtext-backend/              # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── tasks/
│   ├── prompts/
│   ├── tests/                      # pytest tests
│   └── Dockerfile
│
├── data/
│   └── nifty500.csv                # NSE ticker universe
│
├── config.yaml                     # Screener thresholds
├── docs/                           # All 8 planning docs
│   ├── prd.md
│   ├── trd.md
│   ├── ux-design.md
│   ├── app-flow.md
│   ├── backend-schema.md
│   ├── implementation-plan.md
│   ├── research.md
│   └── cursor-prompt.md
│
├── .env.example                    # Template (never commit .env)
├── .gitignore
└── README.md
```

---

## Resume / Hackathon Talking Points

When presenting Subtext:

1. **"I built a RAG pipeline over financial documents"** — more impressive than "I used ChatGPT"
2. **"The system uses SSE for real-time streaming"** — shows you know systems
3. **"PostgreSQL with pgvector for semantic search"** — shows DB + ML knowledge
4. **"Celery cron job handles 500 stocks in < 5 minutes"** — shows async/distributed thinking
5. **"Row-level security in Supabase"** — shows you think about security
6. **"Cost tracking per run — ~$0.023 per report"** — shows product/business thinking
