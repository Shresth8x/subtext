# Subtext — Backend Schema Document

> **Version**: 1.0 | **Date**: September 2026

---

## 1. Database: PostgreSQL (via Supabase) + pgvector

### Extensions Required
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for fuzzy ticker search
```

---

## 2. Schema — All Tables

### 2.1 `users`
*(Managed primarily by Supabase Auth — this is an extension table)*

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT,
    avatar_url      TEXT,
    tier            TEXT NOT NULL DEFAULT 'free'  -- 'free' | 'pro'
                    CHECK (tier IN ('free', 'pro')),
    reports_used_this_month  INT NOT NULL DEFAULT 0,
    reports_reset_at         TIMESTAMPTZ NOT NULL DEFAULT (DATE_TRUNC('month', NOW()) + INTERVAL '1 month'),
    telegram_chat_id         BIGINT UNIQUE,       -- NULL until connected
    telegram_username        TEXT,
    connect_code             TEXT UNIQUE,          -- 8-char code for Telegram pairing
    connect_code_expires_at  TIMESTAMPTZ,
    screener_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS: users can only read/write their own row
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_self ON users
    USING (auth.uid() = id);
```

---

### 2.2 `stock_tickers`
*(Reference table — pre-populated with NSE universe)*

```sql
CREATE TABLE stock_tickers (
    ticker          TEXT PRIMARY KEY,              -- 'RELIANCE', 'INFY'
    company_name    TEXT NOT NULL,
    sector          TEXT,
    industry        TEXT,
    index_member    TEXT[],                        -- ['nifty50', 'nifty500']
    isin            TEXT UNIQUE,
    logo_url        TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickers_search ON stock_tickers
    USING GIN (company_name gin_trgm_ops, ticker gin_trgm_ops);
```

---

### 2.3 `reports`

```sql
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker          TEXT NOT NULL REFERENCES stock_tickers(ticker),
    company_name    TEXT NOT NULL,
    
    -- Status
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'fetching_data', 'generating', 'complete', 'failed')),
    
    -- Report content (full markdown text)
    full_text       TEXT,                          -- NULL until complete
    
    -- Extracted structured fields
    verdict         TEXT CHECK (verdict IN ('BUY', 'HOLD', 'AVOID')),
    conviction_score INT CHECK (conviction_score BETWEEN 1 AND 10),
    bear_counterpoint TEXT,                        -- extracted from full_text
    one_liner       TEXT,
    
    -- Key metrics at time of report
    pe_ratio        NUMERIC(10, 2),
    roe_percent     NUMERIC(10, 2),
    debt_to_equity  NUMERIC(10, 4),
    promoter_holding_pct NUMERIC(10, 2),
    cmp             NUMERIC(12, 2),                -- current market price at generation time
    above_200_ema   BOOLEAN,
    
    -- Document context
    pdf_file_ids    TEXT[],                        -- R2 file IDs used in this report
    used_rag        BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Sharing
    is_public       BOOLEAN NOT NULL DEFAULT FALSE,
    share_token     TEXT UNIQUE DEFAULT encode(gen_random_bytes(8), 'hex'),
    
    -- Cost tracking
    input_tokens    INT,
    output_tokens   INT,
    estimated_cost_usd NUMERIC(10, 6),
    
    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    
    error_message   TEXT                           -- populated if status = 'failed'
);

-- Indexes
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_ticker ON reports(ticker);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);

-- RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY reports_own ON reports
    USING (auth.uid() = user_id);
CREATE POLICY reports_public ON reports
    FOR SELECT USING (is_public = TRUE);
```

---

### 2.4 `document_embeddings`
*(pgvector — RAG chunks)*

```sql
CREATE TABLE document_embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    file_id         TEXT NOT NULL,                 -- R2 file ID
    chunk_index     INT NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       VECTOR(1536),                  -- OpenAI text-embedding-3-small
    metadata        JSONB,                         -- page number, section title, etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embeddings_report_id ON document_embeddings(report_id);
CREATE INDEX idx_embeddings_vector ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

### 2.5 `pdf_uploads`

```sql
CREATE TABLE pdf_uploads (
    id              TEXT PRIMARY KEY,              -- R2 object key / file_id
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    size_bytes      BIGINT NOT NULL,
    r2_bucket       TEXT NOT NULL DEFAULT 'subtext-pdfs',
    r2_key          TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'uploaded'
                    CHECK (status IN ('uploading', 'uploaded', 'processing', 'processed', 'failed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days')
                                                    -- auto-delete after 7 days
);

ALTER TABLE pdf_uploads ENABLE ROW LEVEL SECURITY;
CREATE POLICY uploads_own ON pdf_uploads USING (auth.uid() = user_id);
```

---

### 2.6 `watchlists`

```sql
CREATE TABLE watchlists (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker          TEXT NOT NULL REFERENCES stock_tickers(ticker),
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT,
    
    UNIQUE (user_id, ticker)                       -- one entry per user per stock
);

ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
CREATE POLICY watchlists_own ON watchlists USING (auth.uid() = user_id);
```

---

### 2.7 `screener_configs`

```sql
CREATE TABLE screener_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Universe
    universe        TEXT NOT NULL DEFAULT 'nifty500'
                    CHECK (universe IN ('nifty50', 'nifty500', 'custom')),
    custom_tickers  TEXT[],                        -- used if universe = 'custom'
    
    -- Filter thresholds (NULL = disabled)
    max_pe_ratio    NUMERIC(10, 2),
    min_roe_pct     NUMERIC(10, 2),
    max_debt_to_equity NUMERIC(10, 4),
    min_revenue_growth_pct NUMERIC(10, 2),
    min_promoter_holding_pct NUMERIC(10, 2),
    require_above_200ema BOOLEAN DEFAULT TRUE,
    min_rsi         INT CHECK (min_rsi BETWEEN 0 AND 100),
    max_rsi         INT CHECK (max_rsi BETWEEN 0 AND 100),
    max_results     INT NOT NULL DEFAULT 20,
    
    -- Schedule
    schedule_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    schedule_cron   TEXT NOT NULL DEFAULT '0 6 * * 1-5', -- 6AM IST Mon-Fri
    
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE screener_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY screener_configs_own ON screener_configs USING (auth.uid() = user_id);
```

---

### 2.8 `screener_runs`

```sql
CREATE TABLE screener_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    triggered_by    TEXT NOT NULL CHECK (triggered_by IN ('cron', 'manual')),
    universe        TEXT NOT NULL,
    tickers_scanned INT,
    tickers_shortlisted INT,
    status          TEXT NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running', 'complete', 'failed')),
    telegram_sent   BOOLEAN NOT NULL DEFAULT FALSE,
    run_duration_ms INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_screener_runs_user_id ON screener_runs(user_id);
CREATE INDEX idx_screener_runs_created_at ON screener_runs(created_at DESC);
```

---

### 2.9 `screener_results`

```sql
CREATE TABLE screener_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES screener_runs(id) ON DELETE CASCADE,
    ticker          TEXT NOT NULL,
    company_name    TEXT NOT NULL,
    pe_ratio        NUMERIC(10, 2),
    roe_percent     NUMERIC(10, 2),
    debt_to_equity  NUMERIC(10, 4),
    promoter_holding_pct NUMERIC(10, 2),
    cmp             NUMERIC(12, 2),
    above_200_ema   BOOLEAN,
    rsi             NUMERIC(6, 2),
    revenue_growth_pct NUMERIC(10, 2)
);

CREATE INDEX idx_screener_results_run_id ON screener_results(run_id);
```

---

### 2.10 `run_cost_log`

```sql
CREATE TABLE run_cost_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    report_id       UUID REFERENCES reports(id),
    run_type        TEXT NOT NULL CHECK (run_type IN ('report', 'screener', 'telegram_mini')),
    model           TEXT NOT NULL,                 -- 'gpt-4o', 'claude-3-5-sonnet'
    input_tokens    INT NOT NULL DEFAULT 0,
    output_tokens   INT NOT NULL DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. Auth Model

### Provider
**Supabase Auth** — handles JWT issuance, OAuth, email verification.

### Token Flow
```
Client → POST /auth/signin (Supabase) → JWT access token (1 hour)
JWT → Every API request as: Authorization: Bearer <token>
FastAPI middleware → supabase.auth.get_user(token) → validates + gets user_id
user_id → all DB queries scoped to this user
```

### Supabase RLS
Every table has Row Level Security enabled. Users can only access their own rows. `reports` with `is_public = TRUE` are readable by anyone (for sharing).

### Rate Limiting (Redis)
```python
# In auth middleware (FastAPI)
key = f"ratelimit:{user_id}:reports"
count = redis.incr(key)
if count == 1:
    redis.expire(key, 3600)  # 1-hour window
if count > limit:  # 5 for free, 30 for pro
    raise HTTPException(429, "Rate limit exceeded")
```

---

## 4. Real-time: Server-Sent Events (SSE)

Report generation is streamed via SSE. WebSockets are overkill for a one-directional stream.

```python
# FastAPI SSE endpoint
@router.get("/research/stream/{job_id}")
async def stream_report(job_id: str, user_id: str = Depends(get_current_user)):
    async def event_generator():
        async for chunk in generate_report_stream(job_id):
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'report_id': job_id})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

Client-side:
```typescript
// React component
const source = new EventSource(`/api/research/stream/${jobId}`)
source.onmessage = (e) => {
  const data = JSON.parse(e.data)
  if (data.type === 'chunk') setReportText(prev => prev + data.text)
  if (data.type === 'done') source.close()
}
```

---

## 5. File Storage (Cloudflare R2)

### Bucket Structure
```
subtext-pdfs/           (private)
  └── {user_id}/
      └── {file_id}.pdf

subtext-exports/        (public, CDN-cached)
  └── {report_id}/
      └── report.pdf
```

### Access Pattern
- **Upload**: Presigned R2 URL generated by backend → client uploads directly to R2 (bypasses backend, fast)
- **Read in AI pipeline**: Backend fetches from R2 using service credentials
- **Export**: Generate PDF → save to `subtext-exports` → return CDN URL

---

## 6. Environment Variables — Complete Reference

```bash
# === APPLICATION ===
ENVIRONMENT=development           # development | production
APP_URL=https://subtext.co     # For absolute URLs in emails/bots

# === AI ===
OPENAI_API_KEY=sk-...             # Primary LLM
ANTHROPIC_API_KEY=sk-ant-...      # Fallback LLM
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o

# === DATABASE ===
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...          # Safe for client
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Server-side only — NEVER expose
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres

# === CACHE / QUEUE ===
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...

# === STORAGE ===
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_PDF_BUCKET=subtext-pdfs
R2_EXPORTS_BUCKET=subtext-exports
R2_PUBLIC_URL=https://exports.subtext.co  # CDN domain for exports

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...       # For webhook validation

# === RATE LIMITS ===
FREE_TIER_REPORTS_PER_HOUR=5
PRO_TIER_REPORTS_PER_HOUR=30
MAX_PDF_UPLOAD_MB=50
MAX_PDFS_PER_REPORT=3

# === SCREENER ===
SCREENER_DEFAULT_UNIVERSE=nifty500
SCREENER_BATCH_SIZE=50            # Tickers per async batch
SCREENER_CRON=0 6 * * 1-5        # 6 AM IST Mon-Fri

# === MONITORING ===
SENTRY_DSN=https://...
LOG_LEVEL=INFO

# === NEXT.JS PUBLIC ===
NEXT_PUBLIC_API_URL=https://api.subtext.co
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## 7. Data Retention Policy

| Data | Retention | Reason |
|---|---|---|
| User reports | Indefinite | Core product value |
| PDF uploads | 7 days | Storage cost, user re-uploads as needed |
| Vector embeddings | Deleted with report | Linked to PDFs |
| Screener run results | 90 days | Trend analysis |
| Cost logs | 1 year | Billing & cost analysis |
| Auth sessions | Supabase default (7 days) | Security |

---

## 8. Indexes & Query Optimization

```sql
-- Fast ticker search (autocomplete)
CREATE INDEX idx_tickers_gin ON stock_tickers
    USING GIN (company_name gin_trgm_ops, ticker gin_trgm_ops);

-- Fast report history for user
CREATE INDEX idx_reports_user_created ON reports(user_id, created_at DESC);

-- Fast ANN vector search (RAG retrieval)
CREATE INDEX idx_embeddings_ivfflat ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Screener results lookup
CREATE INDEX idx_screener_results_run ON screener_results(run_id);
```
