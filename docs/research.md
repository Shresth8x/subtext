# Subtext — Research Document

> **Version**: 1.0 | **Date**: September 2026

---

## 1. Problem Landscape Research

### 1.1 Indian Retail Investor Market Size

- **120 million+** demat accounts in India as of 2024 (up from 40M in 2020)
- **₹40+ lakh crore** managed by retail investors in direct equities
- NSE has 2,300+ listed companies — brokerages' research desks cover only top 150-200
- **95%** of retail traders lose money — primary cause cited in SEBI reports: lack of information and analysis skills

**Sources**:
- SEBI Annual Report 2023-24
- NSE Monthly Bulletin, August 2024
- AMFI investor education reports

### 1.2 The Research Gap

Most retail investors rely on:
1. YouTube finance channels (biased, often promotional)
2. Telegram "tips" groups (often pump-and-dump schemes)
3. Social media hot takes
4. Self-research using raw Screener.in data (requires financial literacy)

What they lack:
- Ability to interpret financial statements
- Understanding of concall transcripts
- Valuation context (is PE 30 cheap or expensive for this sector?)
- Systematic screening (not just following trends)

---

## 2. Competitor Analysis

### 2.1 Screener.in

**What it does**: Data aggregation for NSE/BSE stocks. Custom screens. Financial statements.

**Strengths**: Comprehensive data, powerful custom formulas, huge community
**Weaknesses**:
- Zero AI interpretation — dumps raw numbers, user must interpret
- No document analysis (no concall, no annual report digest)
- No alerts or notifications
- No Telegram integration
- UI is very utilitarian (not beautiful)

**How we differ**: We take Screener.in data as input and add the interpretation layer.

---

### 2.2 Tijori Finance

**What it does**: Premium data platform — concall transcripts, analyst reports, insider trades

**Strengths**: Very rich data, great for professionals
**Weaknesses**:
- ₹4,999–₹9,999/month pricing (inaccessible to most retail investors)
- Still data-only, no AI synthesis
- No screener + alert pipeline

**How we differ**: We democratize access to the analysis layer at near-zero cost.

---

### 2.3 Trendlyne

**What it does**: Technical screener, fundamentals, some AI features

**Strengths**: Good screener, some AI signals
**Weaknesses**:
- AI features are shallow (single-sentence summaries, not deep analysis)
- No PDF document upload
- No custom configuration of screener thresholds
- Alert system is basic

**How we differ**: Deeper AI analysis (6-section report), PDF RAG, full customization.

---

### 2.4 ChatGPT / Claude (direct use)

**What it does**: Users manually paste financial data and ask for analysis

**Strengths**: Very powerful reasoning
**Weaknesses**:
- No live Indian market data
- User must manually gather and paste all data
- No persistent history
- No automated screener
- No Telegram integration
- Not specialized for Indian markets (misses SEBI nuances, promoter structures)

**How we differ**: Subtext automates the data gathering, specializes the prompt, integrates live NSE data, and wraps everything in a purpose-built UI.

---

### 2.5 Bloomberg Terminal / Refinitiv Eikon

**What they do**: Institutional-grade data + analytics platform

**Strengths**: The gold standard — real-time data, research, news, everything
**Weaknesses**:
- $25,000–$30,000/year subscription
- Completely inaccessible to retail investors
- Designed for professional traders, overwhelming for others

**How we differ**: Subtext is the "Bloomberg for retail investors" — we take the concept and make it accessible for free.

---

### 2.6 Perplexity Finance / Gemini Deep Research

**What they do**: General AI research assistants with web search

**Strengths**: Smart, broad knowledge, web access
**Weaknesses**:
- Not specialized for Indian equity research
- No structured 6-section report format
- No screener, no alerts, no watchlist
- No PDF document upload for company-specific docs
- No Telegram bot

**How we differ**: Specialization. Subtext does one thing (Indian equity research) and does it perfectly.

---

## 3. Technology Inspiration

### 3.1 How yfinance Works

`yfinance` is a Python library that reverse-engineers Yahoo Finance's internal API. For Indian stocks:
- Ticker format: `RELIANCE.NS` (NSE) or `RELIANCE.BO` (BSE)
- Provides: info (PE, ROE, etc.), history (OHLCV), earnings, quarterly financials
- Rate limit: ~2,000 requests/hour (we batch with delays to stay safe)
- Limitation: Some Indian-specific data (promoter holding, pledged shares) not available → we supplement with NSE CSV downloads

### 3.2 How RAG (Retrieval-Augmented Generation) Works

Problem: LLMs have a context window limit. Annual reports are 200+ pages.

Solution:
1. **Chunk**: Split PDF into ~1,000 token chunks
2. **Embed**: Convert each chunk to a vector (1,536 dimensions for OpenAI embedding)
3. **Store**: Save vectors in pgvector (PostgreSQL extension)
4. **Retrieve**: When generating a report, take the research query → embed it → find the 8 most semantically similar chunks
5. **Augment**: Inject those 8 chunks into the LLM prompt as context
6. **Generate**: LLM uses the retrieved chunks + live data to write the report

This means the LLM effectively "reads" the most relevant parts of the annual report without needing to process all 200 pages.

**Inspiration**: [LlamaIndex documentation](https://docs.llamaindex.ai), [LangChain RAG tutorial](https://python.langchain.com/docs/tutorials/rag/)

### 3.3 How Server-Sent Events (SSE) Works

Unlike WebSockets (bidirectional), SSE is a one-directional stream from server → client. Perfect for AI text streaming.

```
Client                          Server
  │                               │
  │──── GET /stream/{id} ────────►│
  │                               │
  │◄── data: {"type":"chunk"} ────│ (token 1)
  │◄── data: {"type":"chunk"} ────│ (token 2)
  │      ...                      │
  │◄── data: {"type":"done"} ─────│
  │                               │
```

FastAPI has native `StreamingResponse` support. React's `EventSource` API handles this natively — no library needed.

### 3.4 How Celery Beat Works

Celery Beat is a scheduler that sends tasks to Celery workers on a schedule (like cron but Python-native):

```python
# tasks/celery_app.py
celery_app.conf.beat_schedule = {
    'daily-screener': {
        'task': 'tasks.screener_task.run_daily_screener',
        'schedule': crontab(hour=0, minute=30),  # 6 AM IST = 0:30 UTC
    },
}
```

The Beat process runs on Railway. Worker processes pick up tasks from Redis queue and execute them.

### 3.5 How Cloudflare R2 Works

R2 is Cloudflare's S3-compatible object storage:
- **Zero egress fees** (vs. AWS S3 which charges ~$0.09/GB egress)
- **boto3-compatible** (S3 SDK works with R2 with just endpoint URL change)
- **Presigned URLs**: Backend generates a time-limited upload URL → client uploads directly to R2 (bypasses backend, faster, cheaper)

---

## 4. How Subtext Differs (Differentiation Summary)

| Feature | Screener.in | Tijori | Trendlyne | ChatGPT | Subtext |
|---|---|---|---|---|---|
| Live NSE data | ✅ | ✅ | ✅ | ❌ | ✅ |
| AI interpretation | ❌ | ❌ | Shallow | ✅ | ✅ Deep |
| PDF document analysis | ❌ | ❌ | ❌ | Manual | ✅ Auto RAG |
| Automated screener | ✅ | ❌ | ✅ | ❌ | ✅ |
| Telegram alerts | ❌ | ❌ | Basic | ❌ | ✅ |
| Streaming reports | N/A | N/A | N/A | ✅ | ✅ |
| Bear counter-point | ❌ | ❌ | ❌ | Manual | ✅ Mandatory |
| Cost | Free/₹499 | ₹4,999 | ₹999 | $20/mo | Free/₹499 |
| Specialized India | ✅ | ✅ | ✅ | ❌ | ✅ |
| Beautiful UI | Okay | Okay | Okay | Okay | ✅ Premium |

---

## 5. Indian Market Specifics We Handle

Things ChatGPT/Claude miss that Subtext addresses:

1. **Promoter holding** — A uniquely Indian metric. >50% promoter holding = stability signal. Pledged shares = red flag.
2. **NSE vs. BSE ticker differences** — Subtext uses `.NS` suffix consistently (NSE primary listing)
3. **SEBI compliance framing** — All outputs include "Research Only — Not Investment Advice" (required to avoid SEBI RA regulations)
4. **Indian accounting standards (Ind AS)** — System prompt includes guidance on interpreting Indian GAAP vs Ind AS differences
5. **Concall culture** — Indian management often gives guidance in vague terms. System prompt trained to detect "management speak" and overpromising patterns common in Indian concalls
6. **FII/DII ownership** — Tracked alongside promoter holding (from NSE CSV feeds)

---

## 6. Sources Consulted

| Source | Used For |
|---|---|
| SEBI Annual Report 2023-24 | Market size stats, retail investor data |
| NSE India website | Nifty 500 ticker list, shareholding CSV format |
| yfinance GitHub + docs | Data availability, rate limits, ticker format |
| LangChain documentation | RAG pipeline design, LLM chain patterns |
| LlamaIndex documentation | PDF chunking strategies, embedding best practices |
| Supabase documentation | pgvector setup, RLS policies, auth flow |
| Cloudflare R2 documentation | Presigned URL flow, boto3 compatibility |
| OpenAI API documentation | text-embedding-3-small specs, GPT-4o pricing |
| Screener.in | UI inspiration, data field reference |
| Tijori Finance | Content depth inspiration |
| python-telegram-bot docs | Bot setup, webhook vs. polling trade-offs |
| Upstash documentation | Serverless Redis, Celery integration |
| Railway documentation | Deployment, cron jobs, Docker |
| Vercel documentation | Next.js deployment, environment variables |
