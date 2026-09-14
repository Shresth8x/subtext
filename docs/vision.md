# Subtext — Big Product Vision & Growth Roadmap

> This document outlines the full long-term vision for Subtext beyond the MVP.
> It answers: "What does this become if we go all in?"

---

## The Insight

India has 120M+ demat accounts. The number will hit 250M by 2030.
Every single one of these investors needs research. None of them can afford Bloomberg.

But here's the real opportunity:

**The existing research platforms (Screener.in, Tijori, Trendlyne) are DATA companies.**
They collect and display numbers. They don't interpret, synthesize, learn, or connect people.

**Subtext can be the first INTELLIGENCE + COMMUNITY platform for Indian equities.**

That's a fundamentally different and far more defensible business.

---

## V1 → V2 → V3: The Platform Arc

```
V1 (Now): Tool
  └─ AI report generator + screener + Telegram alerts
  └─ Value: saves 6 hours of manual research per stock
  └─ Moat: low (any competitor can replicate)

V2 (6 months): Network
  └─ Social research layer + thesis tracking + community
  └─ Value: collective intelligence, not just AI intelligence
  └─ Moat: medium (data network effects starting to form)

V3 (12+ months): Platform
  └─ API for fintechs + RA marketplace + WhatsApp bot + portfolio intelligence
  └─ Value: becomes infrastructure for the Indian investing ecosystem
  └─ Moat: high (data + network + integrations + brand trust)
```

---

## V2 Features: Zero-Friction, Automatic Value

> **Design rule for every feature**: User gets value BEFORE doing any extra work.
> "Task before reward" = nobody uses it. "Reward immediately" = sticky product.

### 🔥 1. NSDL/CDSL Portfolio Statement Upload

**The concept**: Every Indian investor has a portfolio statement PDF from NSDL or CDSL (they download it for taxes anyway). User uploads ONE file → Subtext reads all their holdings automatically → delivers a full portfolio health report in 2 minutes.

**Zero manual entry. No broker API (which requires SEBI registration). No ongoing effort.**

**Why this wins**:
- Solves portfolio analysis WITHOUT needing broker API approvals
- One-time upload → immediate comprehensive value (red flags, concentration risk, sector breakdown)
- No competitor does this — everyone is stuck chasing broker API integrations
- Repeat use: users re-upload every quarter when they get new statements

**What it produces**:
```
📊 PORTFOLIO HEALTH REPORT — uploaded 14 Sep 2026
12 holdings analyzed | ₹4.2L portfolio

⚠️ RED FLAGS
  ADANIPORTS — Debt growing faster than earnings (flagged)
  ZOMATO     — Loss-making, no clear path to profitability at current burn

✅ GREEN FLAGS
  INFY       — Strong cash flow, management credibility 8.2/10
  TATAPOWER  — Renewable tailwind, promoter recently bought

📊 CONCENTRATION
  IT sector: 42% (overweight vs. index 15%) — high sector risk
  Top 3 stocks: 71% of portfolio — highly concentrated

🎯 SECTOR vs. VALUATION
  Your FMCG holdings: avg PE 48x vs. sector 5yr avg 42x — slightly expensive
```

---

### 🔥 2. Morning Dispatch (Fully Automatic — Opt In Once, Value Every Day)

**The concept**: User subscribes once. Every morning at 7:00 AM IST, Subtext sends a Telegram/WhatsApp message with:
- AI-filtered BSE corporate announcements from last 18 hours (only material ones)
- Their personal watchlist updates
- One macro data point with historical context

**User effort after subscribing: zero.** Subtext scrapes BSE XML feeds, filters noise with AI, personalizes for their watchlist.

```
☀️ SUBTEXT MORNING DISPATCH — Mon 14 Sep 2026

📋 MATERIAL ANNOUNCEMENTS (BSE — last 18 hours)
  🔴 ZOMATO     — ₹8,500Cr QIP approved. Dilution ~4.2%.
  🟢 TATAPOWER  — Promoters bought 0.4% stake at ₹420.
  🟡 WIPRO      — Q2 growth guidance cut (third consecutive downgrade).

📊 YOUR WATCHLIST
  RELIANCE — No material news
  INFY     — Concall transcript published. Mgmt: "Deal pipeline strongest in 6 quarters"

⚡ ONE CONTEXT
  FII sold ₹4,200Cr Friday. In 7 of 9 similar 3-day sell streaks since 2020,
  index corrected 2–3% within 10 trading days.

Research Only — Not Investment Advice
```

---

### 🔥 3. Promoter Activity Radar (Fully Automatic — BSE SAST Feed)

**The concept**: Promoter buying/selling is legally mandated to be filed on BSE (SAST disclosures) within 2 days. BSE provides a public data feed. Subtext polls it every 2 hours and sends instant alerts for any stock on a user's watchlist.

**User does nothing after adding stocks to watchlist.**

```
🔔 PROMOTER MOVE — HDFC Bank

Promoter HDFC Ltd bought 0.8% stake at ₹1,720
Total promoter holding: 26.1% ↑ from 25.3%

Context: 3rd promoter purchase in 12 months.
Prior buys: ₹1,450 (May 2026), ₹1,580 (Jul 2026)
Pattern: Promoter is accumulating on dips.

Research Only — Not Investment Advice
```

---

### 🔥 4. Management Credibility Score (Auto-Built, Shown on Every Report)

**The concept**: For any stock, Subtext automatically tracks the last 8 quarters of management revenue/profit guidance vs. actual results (from NSE earnings releases). Shows a credibility score on every report page — no user input ever needed.

```
INFY — Management Credibility: 8.2/10 ★★★★☆

Guidance vs. Actual (last 8 quarters):
  Q1 FY24: Guided 4-7%   → Actual 9.4%  ✅ Beat by 2.4pp
  Q2 FY24: Guided 4-7%   → Actual 8.1%  ✅ Beat by 1.1pp
  Q3 FY24: Guided 1-3.5% → Actual 3.6%  ✅ Beat by 0.1pp
  Q4 FY24: Guided 1-3.5% → Actual 1.2%  ❌ Missed by 0.3pp
  ...

Current guidance: 8% revenue growth FY27
At similar guidance levels historically: Beat 75% of time
```

This is competitive moat territory — proprietary synthesized data built entirely from public filings.

---

### 🔥 5. Red Flag Scanner (30 Seconds, Pure Data Math)

**The concept**: A fast, lightweight scan separate from the full research report. Enter any ticker → 30 seconds → specific accounting and governance flags. No PDF uploads, no AI prompt needed — just financial ratio math.

```
🔍 RED FLAG SCAN — ADANIPORTS

⚠️ Gross debt +34% YoY vs. EBITDA +12% — leverage increasing faster than earnings
⚠️ Trade receivables grew 2.4x revenue growth — possible recognition issue
✅ Operating cash flow > reported PAT in 6/8 quarters — profits are real
✅ No promoter pledge changes in last 4 quarters

Summary: 2 flags, 2 greens | Warrants deeper review

Research Only — Not Investment Advice
```

---

### 🔥 6. Auto Peer Comparison (On Every Report, No Extra Work)

**The concept**: Every research report automatically includes a sector peer comparison table. User never asks for it — it's just there.

```
HDFC BANK vs. Peers (auto-populated)

           HDFC   ICICI  KOTAK  AXIS
PE          19x    18x    22x    14x
ROE        16.8%  18.1%  14.2%  17.3%
NIM         4.1%   4.3%   4.8%   3.9%
NPA (Gross) 1.2%   2.1%   1.7%   1.7%

↑ HDFC has best asset quality but not cheapest on PE.
  ICICI leads on ROE. Axis cheapest but higher NPAs.
```

**The concept**: When a user generates a research report and decides to invest based on it, they log their "thesis" — the specific reasons they're buying and the price they think it's worth.

Subtext then tracks whether the thesis played out over 3, 6, 12 months.

**Why this is huge**:
- Investors learn from their own mistakes (not just AI analysis)
- Creates a credibility score per user
- Users with high accuracy scores become "trusted voices" on the platform
- Completely unique — no other Indian platform does this
- Proprietary accuracy dataset = massive competitive moat

**What it looks like**:
```
My Thesis — RELIANCE (Added: Sep 2026)
"Jio will drive 20% revenue growth in FY27.
 Retail margins will recover by Q4. Buying at ₹2,847."

Status: 📊 Tracking (47 days)
Current P&L: +12.4% vs. Nifty +4.2% (outperforming ✅)
Thesis check: Revenue growth confirmed in Q2 results ✅
              Retail margins: Still under pressure ❌

Subtext verdict: "Thesis partially validated. Watch retail margins."
```

---

### 🔥 2. Community Research Feed (Social Layer + SEO Goldmine)

**The concept**: Every AI-generated report has a public URL. Users can choose to publish their thesis + the AI report. Other users can:
- Read it
- Leave comments
- Mark it "helpful" or "I disagree — here's why"
- Follow the researcher

**Why this is huge**:
- Network effects: more users → more published research → more users (flywheel)
- SEO: 50,000 indexed research pages = massive organic traffic
- "Reddit meets Screener.in" — a community that produces and validates research
- Community data helps Subtext train better models (with consent)

**Monetization path**: Top researchers get a "Verified Analyst" badge. Premium users pay to get direct access to top analysts' research before it's public.

---

### 🔥 3. WhatsApp Bot (10x Telegram's Reach)

India has 500M+ WhatsApp users. Most retail investors never use Telegram.

**The concept**: `wa.me/+91XXXXXXXXXX` → message "RELIANCE" → get a mini research report.

WhatsApp Business API (via Gupshup or Wati) lets you build this.

**Why this is huge**:
- WhatsApp is where Indian investors actually live
- Your Telegram bot is impressive for developers. WhatsApp is for everyone.
- Viral sharing: investor shares a mini-report screenshot in a family group chat
- India's biggest "super-app" opportunity in investing

**Technical path**: WhatsApp Business API (Meta) → webhook → same backend logic as Telegram bot.

---

### 🔥 4. Portfolio Intelligence (Read-Only Broker Connect)

**The concept**: Users connect their Zerodha / Groww / Upstox account via read-only API (NOT for trading — just to import holdings). Subtext:
- Generates a report on their actual portfolio
- Flags stocks in their portfolio with deteriorating fundamentals
- Shows concentration risk ("60% of your portfolio is in FMCG — sector looks expensive")
- Sends weekly "portfolio health check" to Telegram/WhatsApp

**Why this is huge**:
- Makes Subtext personal — not generic research, but analysis of YOUR money
- Deep stickiness — users won't leave if their portfolio is connected
- Only Smallcase currently does something adjacent, and poorly

**Hard constraint**: Read-only. Never write/trade. Make this extremely clear in UI.

---

### 🔥 5. Earnings Intelligence Engine

**The concept**: Before every quarterly result:
1. Subtext analyzes the last 4 quarters of management guidance vs. actuals
2. Calculates a "Management Credibility Score" per company
3. Sends a pre-earnings alert: "INFY reports in 3 days. Management has beaten revenue guidance 3 of last 4 quarters. Consensus expects 8% growth."

After results drop:
1. Scrapes BSE/NSE announcement (PDF)
2. Runs AI analysis on results vs. Subtext's prior report
3. Sends "Verdict Update" — "Q2 results came in. Here's how our previous thesis held up."

**Why this is huge**:
- Timing is everything in investing — pre-earnings research is extremely valuable
- No one does automatic "thesis validation" against results in India
- Creates a "living" research product vs. a static report

---

## V3 Features: Build the Platform

### 💰 6. Subtext API (B2B Revenue)

**The concept**: Other fintech apps (Groww, PaytmMoney, INDmoney, mutual fund platforms) can integrate Subtext research via API.

When a user is about to buy a stock on Groww, Groww shows:
> "Subtext says: Hold | Conviction 7/10 | ⚠️ Bear case: Margin pressure"

**Revenue model**: Per-call API pricing (₹0.50–₹2 per research call). Even 0.1% of Groww's DAU is 10,000 API calls/day = ₹5,000–₹20,000/day.

**Path to ₹1Cr+/month** at scale. This is the real B2B play.

---

### 💰 7. SEBI RA Marketplace

**The concept**: SEBI-registered Research Analysts (small independent RAs) are allowed to provide personalized investment advice. There are 1,400+ registered RAs in India. Most have no good tech platform.

Subtext offers:
- Subtext Pro workspace for RAs (AI-assisted report drafting)
- Subscriber management (their clients pay RA, RA uses Subtext)
- Report publishing + distribution
- Performance tracking (their calls tracked automatically)

**Revenue**: ₹2,000–₹5,000/month per RA. 1,000 RAs = ₹2–5Cr/month.

---

### 💰 8. Subtext Pro Subscription (Consumer)

**Free tier**: 5 reports/month, Telegram alerts, basic screener
**Pro (₹499/month)**: Unlimited reports, WhatsApp + Telegram, portfolio connect, PDF RAG, comparison table
**Analyst (₹1,499/month)**: All Pro + API access, thesis tracker, earnings intelligence, RA tools

At 10,000 Pro subscribers: **₹5Cr/month ARR**.

---

## The Moat Stack (Why This Can't Be Easily Copied)

```
Layer 1: AI Quality (Easy to replicate initially, but...)
    └─ We fine-tune on Indian management language patterns
    └─ We build proprietary accuracy dataset from thesis tracking
    └─ Over time: our model is better at Indian equities than generic GPT-4o

Layer 2: Network Effects (Hard to replicate)
    └─ Community research feed — more users = more content = better platform
    └─ Thesis accuracy data — only we have this dataset
    └─ RA network — switching cost is high once RAs are on platform

Layer 3: Distribution (Very hard to replicate)
    └─ WhatsApp bot at scale — brand recognition, viral sharing
    └─ B2B API integrations — once inside Groww's product, locked in
    └─ SEO from 100,000+ indexed research pages

Layer 4: Trust (Takes years to build)
    └─ Track record of accurate analysis (thesis tracker data)
    └─ SEBI-compliant framing baked into every output
    └─ No sensational tips, no fabricated data — reputation for honesty
```

---

## What To Build Next (Priority Order)

After Phase 1 (screener + Telegram) works:

| Priority | Feature | Why first |
|---|---|---|
| 1 | Thesis Tracker | Biggest differentiator, unique, creates data moat |
| 2 | Community Feed + SEO pages | Network effects + organic growth engine |
| 3 | WhatsApp Bot | 10x the addressable user base |
| 4 | Earnings Intelligence | Makes the product "alive" not static |
| 5 | Portfolio Connect (read-only) | Deep stickiness, personalization |
| 6 | Subtext API | B2B revenue, scaling the business |
| 7 | RA Marketplace | Enterprise tier, serious revenue |

---

## The Startup Path

**Month 1–2**: Ship Phase 1 (screener + Telegram). Get 100 users. Learn.

**Month 3–4**: Ship web app + AI reports (Phase 2). Apply to hackathons. Get press.

**Month 5–6**: Ship Thesis Tracker + Community Feed. This is the "product-market fit" moment.

**Month 7–9**: WhatsApp bot + Earnings Intelligence. Start talking to angels.

**Month 10–12**: Launch API beta. First B2B revenue. Apply to YC India / Antler / Surge.

**Year 2**: RA Marketplace. Series A story.

---

## Comparable Exits / Fundraises (Your "Why This Is Big" Slide)

| Company | What they did | Outcome |
|---|---|---|
| Smallcase | Portfolio baskets + broker integration | $50M+ raised |
| Tijori Finance | Premium financial data (India) | Acquired by HDFC Securities |
| Zerodha Varsity | Financial education | 5M+ learners, major brand |
| Finshots | Finance newsletter India | Acquired |
| Trade Brains | Stock education + data | Growing fast |

**Subtext is none of these exactly.** It's the combination of AI research + community + distribution that none of them have.

---

## The One-Slide Story (For Hackathons + Investors)

> "India has 120 million retail equity investors. Zero of them can afford institutional research.
> Screener.in gives them data. We give them answers.
> Subtext is an AI research co-pilot that reads annual reports, analyzes management credibility,
> spots accounting red flags, and delivers institutional-grade research in 60 seconds — for free.
> But the real play is the community layer: we're building the platform where India's retail investors
> collectively produce and validate research, creating a network effect that no AI alone can replicate."

---

## What Makes This "3rd Year CSE Student" Credible

The technical depth you can demonstrate:
- **RAG pipeline** over financial PDFs (pgvector + LlamaIndex)
- **Real-time streaming** via SSE (not a spinner, actual live output)
- **Async distributed jobs** (Celery + Redis) for screener at scale
- **WhatsApp + Telegram bot** integration
- **Full-stack SaaS** (Next.js + FastAPI + Supabase)
- **Cost optimization** — you know it costs $0.023/report and why
- **Security** — RLS, JWT, no hardcoded secrets

You don't need to explain all of this. Pick 3 that impress the specific audience.
For investors: focus on market size + network effect.
For technical judges: RAG pipeline + streaming + scale.
For product judges: thesis tracker + community feed.
