# Subtext — Technical Requirements Document (TRD)

> **Version**: 1.0 | **Date**: September 2026

---

## 1. Stack Decision Summary

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript | Industry standard, SSR, SEO, streaming support |
| Styling | Tailwind CSS + shadcn/ui | Fast, professional, accessible components |
| Charts | TradingView Lightweight Charts | Best-in-class financial charting, free |
| State | Zustand | Lightweight, no boilerplate |
| Backend | FastAPI (Python 3.11) | Native async, perfect for AI/ML, auto OpenAPI docs |
| AI Orchestration | LangChain + LangGraph | RAG pipelines, agent loops, streaming |
| LLM | OpenAI GPT-4o (primary) + Claude 3.5 Sonnet (fallback) | Best reasoning + cost balance |
| PDF Processing | LlamaIndex + PyMuPDF | Best RAG framework for documents |
| Vector Store | pgvector (via Supabase) | No extra service, co-located with main DB |
| Task Queue | Celery + Redis | Background screener jobs, report queuing |
| Primary Database | PostgreSQL (via Supabase) | Relational, free tier, built-in auth |
| Cache | Redis (via Upstash) | Rate limiting, session cache, Celery broker |
| File Storage | Cloudflare R2 | S3-compatible, free egress, generous free tier |
| CDN | Cloudflare | Free tier, global edge, R2 native integration |
| Auth | Supabase Auth | Google OAuth + email, JWT, built-in row-level security |
| Telegram Bot | python-telegram-bot | Well-maintained, async, production-ready |
| Financial Data | yfinance + NSE India (unofficial) | Free, covers all NSE tickers |
| Technical Analysis | pandas-ta | 130+ indicators, vectorized, fast |
| Deployment - Frontend | Vercel | Free tier, native Next.js, automatic previews |
| Deployment - Backend | Railway | Free tier, Docker support, cron support |
| Monitoring | Sentry (free tier) | Error tracking, performance monitoring |
| CI/CD | GitHub Actions | Free, native GitHub integration |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENTS                            │
│   Next.js Browser App    │    Telegram Bot              │
└──────────────┬───────────┴──────────┬───────────────────┘
               │                      │
               ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│                    CLOUDFLARE CDN                       │
│         (static assets, edge caching, DDoS)             │
└──────────────────────────┬──────────────────────────────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
┌──────────────────────┐  ┌────────────────────────────┐
│   VERCEL (Frontend)  │  │  RAILWAY (FastAPI Backend) │
│   Next.js App        │  │  /api/* REST + WebSocket   │
│   - SSR pages        │  │  - Auth middleware          │
│   - Static assets    │  │  - Report generator        │
│   - API routes       │  │  - Screener engine         │
└──────────────────────┘  │  - Telegram bot            │
                          │  - File upload handler     │
                          └──────────┬─────────────────┘
                                     │
              ┌──────────────────────┼──────────────────┐
              ▼                      ▼                  ▼
┌─────────────────┐  ┌───────────────────┐  ┌─────────────────┐
│   SUPABASE      │  │   UPSTASH REDIS   │  │  CLOUDFLARE R2  │
│   PostgreSQL    │  │   Cache + Broker  │  │  PDF Storage    │
│   pgvector      │  │   Rate limiting   │  │  Report exports │
│   Auth          │  │   Session store   │  └─────────────────┘
└─────────────────┘  └───────────────────┘
```

---

## 3. Frontend — Next.js 14

### 3.1 Project Structure
```
subtext-web/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx           # Sidebar + nav
│   │   ├── page.tsx             # Dashboard home
│   │   ├── research/
│   │   │   ├── page.tsx         # Research generator
│   │   │   └── [reportId]/page.tsx  # Report viewer
│   │   ├── screener/page.tsx    # Screener config
│   │   ├── watchlist/page.tsx   # User watchlist
│   │   └── alerts/page.tsx      # Telegram alert setup
│   ├── api/
│   │   └── auth/[...nextauth]/route.ts
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/                      # shadcn/ui components
│   ├── research/
│   │   ├── ReportGenerator.tsx  # Main search + upload UI
│   │   ├── ReportStream.tsx     # Streaming report display
│   │   ├── ReportSection.tsx    # Individual section card
│   │   └── VerdictBadge.tsx     # Buy/Hold/Avoid badge
│   ├── screener/
│   │   ├── ThresholdSliders.tsx
│   │   └── ResultsTable.tsx
│   ├── charts/
│   │   └── StockChart.tsx       # TradingView wrapper
│   └── layout/
│       ├── Sidebar.tsx
│       ├── Navbar.tsx
│       └── TelegramConnect.tsx
├── lib/
│   ├── api.ts                   # Typed API client
│   ├── supabase.ts              # Supabase client
│   └── utils.ts
├── store/
│   └── useAppStore.ts           # Zustand store
├── types/
│   └── index.ts                 # Shared TypeScript types
└── public/
```

### 3.2 Key Technical Decisions

**Streaming AI output**: Use `ReadableStream` + React's `useEffect` to display AI report text as it streams from the backend. Users see the report building in real-time. Never show a spinner while waiting 60 seconds.

**Server Components**: Research report viewer, dashboard stats, and watchlist are React Server Components (no client JS, fast initial load).

**Client Components**: Report generator (file upload, search), screener config (sliders), chart (TradingView needs DOM access).

**Error boundaries**: Every major section wrapped in ErrorBoundary with graceful fallback.

---

## 4. Backend — FastAPI

### 4.1 Project Structure
```
subtext-backend/
├── main.py                      # FastAPI app entry point
├── config.py                    # Pydantic settings (env vars)
├── requirements.txt
├── Dockerfile
│
├── routers/
│   ├── auth.py                  # JWT validation middleware
│   ├── research.py              # /research/generate, /research/stream
│   ├── screener.py              # /screener/run, /screener/config
│   ├── watchlist.py             # /watchlist/* CRUD
│   ├── reports.py               # /reports/* CRUD
│   └── health.py                # /health (Railway health check)
│
├── services/
│   ├── data_fetcher.py          # yfinance + NSE data
│   ├── pdf_processor.py         # PyMuPDF + LlamaIndex RAG
│   ├── ai_analyst.py            # LangChain + LLM chains
│   ├── screener_engine.py       # Filter logic + Celery task
│   ├── telegram_bot.py          # python-telegram-bot
│   └── storage.py               # Cloudflare R2 operations
│
├── models/
│   ├── database.py              # SQLAlchemy models
│   └── schemas.py               # Pydantic schemas (request/response)
│
├── tasks/
│   ├── celery_app.py            # Celery + Redis config
│   └── screener_task.py         # Daily screener cron task
│
└── prompts/
    ├── system_prompt.txt        # Core LLM system prompt
    ├── research_prompt.txt      # 6-section research template
    └── screener_alert_prompt.txt # Telegram alert mini-report
```

### 4.2 API Endpoints

```
POST   /auth/verify              # Verify Supabase JWT
POST   /research/generate        # Start report generation (returns job_id)
GET    /research/stream/{job_id} # SSE stream for real-time report
GET    /research/report/{id}     # Get completed report
GET    /research/history         # User's report history

GET    /screener/config          # Get user's screener config
PUT    /screener/config          # Update thresholds
POST   /screener/run             # Manual trigger
GET    /screener/results         # Last screener run results

GET    /watchlist                # Get user watchlist
POST   /watchlist                # Add stock
DELETE /watchlist/{ticker}       # Remove stock

POST   /upload/pdf               # Upload PDF to R2, returns file_id
DELETE /upload/{file_id}         # Delete uploaded PDF

GET    /health                   # Railway health check
```

### 4.3 Data Flow: Report Generation

```
1. Client sends POST /research/generate
   { ticker: "RELIANCE", file_ids: ["abc123", "def456"] }

2. Backend:
   a. Fetch live data (yfinance): PE, ROE, D/E, Revenue, EMA50/200, RSI
   b. Fetch shareholding (NSE CSV): Promoter %, FII %, DII %
   c. Load PDFs from R2 → chunk → embed → store in pgvector
   d. Build LangChain RAG chain with all context
   e. Stream LLM response → SSE endpoint

3. Client receives job_id → opens GET /research/stream/{job_id}
   → displays streaming markdown in real-time

4. On completion → save report to PostgreSQL → return report_id
```

---

## 5. AI Pipeline — LangChain + RAG

### 5.1 RAG Architecture

```python
# Simplified flow (actual implementation in ai_analyst.py)

# 1. Document Loading
loader = PyMuPDFLoader(pdf_path)
docs = loader.load_and_split()

# 2. Chunking
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3. Embedding + Storage
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PGVector(
    connection_string=DATABASE_URL,
    embedding_function=embeddings,
    collection_name=f"report_{report_id}"
)
vectorstore.add_documents(chunks)

# 4. Retrieval Chain
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-4o", streaming=True),
    retriever=retriever,
    return_source_documents=False
)
```

### 5.2 System Prompt (Hard Constraints)

```
You are a senior equity research analyst with 20 years of experience.
You are analyzing [COMPANY_NAME] ([TICKER]) for a retail investor.

HARD RULES — violating these is a critical failure:
1. If any data point is missing or unavailable, write "no data" — NEVER invent a number
2. Every section must be based on the provided context and live data only
3. The BEAR COUNTER-POINT section is MANDATORY — never skip it
4. End every report with: "Research Only — Not Investment Advice"
5. Never give a specific price target framed as a guarantee
6. Never recommend leverage, options, or derivatives

LIVE DATA PROVIDED:
[structured data block from yfinance]

DOCUMENTS PROVIDED (via RAG):
[retrieved chunks from uploaded PDFs]

Generate the research report following exactly the 6-section structure...
```

---

## 6. Screener Engine

### 6.1 Default Thresholds (config.yaml)

```yaml
screener:
  universe: "nifty500"           # nifty50 | nifty500 | custom
  custom_tickers: []             # used if universe: custom
  schedule: "0 6 * * 1-5"       # 6 AM IST, Mon-Fri (cron)
  
  filters:
    pe_ratio:
      max: 35
      enabled: true
    roe:
      min: 15                    # percent
      enabled: true
    debt_to_equity:
      max: 1.0
      enabled: true
    revenue_growth_yoy:
      min: 10                    # percent
      enabled: true
    promoter_holding:
      min: 40                    # percent
      enabled: true
    price_above_200_ema:
      enabled: true
    rsi:
      min: 40
      max: 70
      enabled: false             # optional technical filter

  output:
    max_results: 20              # cap shortlist
    send_telegram: true
    save_to_db: true
```

### 6.2 Screener Celery Task

```python
# tasks/screener_task.py
@celery_app.task
def run_daily_screener(user_id: str):
    config = load_user_config(user_id)
    tickers = get_universe(config.universe)
    
    results = []
    for ticker in tickers:
        data = fetch_fundamentals(ticker)  # yfinance
        if data is None:
            log_missing(ticker)
            continue  # Never fabricate — skip if no data
        
        if passes_all_filters(data, config.filters):
            results.append(build_result_card(ticker, data))
    
    if results and config.output.send_telegram:
        send_telegram_alert(user_id, results)
    
    save_screener_run(user_id, results)
    log_token_cost(estimate_cost(results))
```

---

## 7. Database — PostgreSQL Schema Overview

*(Full schema in backend-schema.md)*

**Core tables**: `users`, `reports`, `report_sections`, `watchlists`, `screener_configs`, `screener_runs`, `screener_results`, `pdf_uploads`, `vector_embeddings` (pgvector), `telegram_connections`

---

## 8. Caching Strategy

| Cache Layer | What's cached | TTL |
|---|---|---|
| Redis (Upstash) | yfinance fundamentals per ticker | 1 hour |
| Redis | NSE shareholding data | 24 hours |
| Redis | 200 EMA / RSI per ticker | 30 minutes |
| Redis | Rate limit counters (per user) | 1 minute sliding window |
| Redis | Celery task results | 24 hours |
| Cloudflare CDN | Static Next.js assets | 1 year (cache busted by hash) |
| Cloudflare CDN | Public report pages (if public) | 1 hour |

**Cache key convention**: `subtext:{resource}:{ticker}:{date}` e.g. `subtext:fundamentals:RELIANCE:2026-09-14`

---

## 9. CDN Strategy (Cloudflare)

- **R2 bucket** `subtext-pdfs` (private) — uploaded PDFs, accessed via signed URLs
- **R2 bucket** `subtext-exports` (public) — exported report PDFs, cached at edge
- **Workers** (optional future): edge-based rate limiting, bot protection
- **Rules**: Cache all `/static/*` routes from Vercel with 1-year TTL

---

## 10. Environment Variables

```bash
# AI
OPENAI_API_KEY=
ANTHROPIC_API_KEY=              # Fallback

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=                   # postgres://... (with pgvector)

# Redis
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
CELERY_BROKER_URL=              # redis://...

# Cloudflare R2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_PDF_BUCKET=subtext-pdfs
R2_EXPORTS_BUCKET=subtext-exports

# Telegram
TELEGRAM_BOT_TOKEN=

# App
NEXT_PUBLIC_API_URL=            # FastAPI backend URL
JWT_SECRET=                     # For signing internal tokens
ENVIRONMENT=development|production
```

> [!IMPORTANT]
> **Zero hardcoded secrets.** All env vars loaded via Pydantic BaseSettings in backend. All NEXT_PUBLIC_* vars safe to expose. All others server-side only.

---

## 11. Performance Targets

| Metric | Target | How achieved |
|---|---|---|
| First Contentful Paint | < 1.2s | Next.js SSR, Vercel edge |
| Time to First Token (report) | < 3s | Fast data fetch + streaming |
| Full report generation | < 60s | Streaming — user sees progress |
| Screener (Nifty 500) | < 5 min | Async batch with rate limiting |
| API p95 latency (non-AI) | < 200ms | Redis cache, indexed queries |

---

## 12. Security

- **Auth**: Supabase JWT on every API request. Row-Level Security on all DB tables.
- **File uploads**: Validated MIME type (PDF only), virus scan via ClamAV (optional), max 50MB
- **Rate limiting**: Redis-based per-user rate limiting: 5 reports/hour (free), 30/hour (pro)
- **SQL injection**: All queries via SQLAlchemy ORM with parameterized queries
- **Prompt injection**: PDF content sanitized before insertion into prompts. System prompt never overridable by user input.
- **CORS**: Strict origin whitelist (only Vercel domain + localhost in dev)
