# Subtext — Product Requirements Document (PRD)

> **Version**: 1.0 | **Date**: September 2026 | **Status**: Approved for Development

---

## 1. Executive Summary

**Subtext** is an AI-powered equity research platform that gives Indian retail investors institutional-grade stock analysis in under 60 seconds. Users upload company documents (annual reports, concall transcripts) and receive a structured research report covering fundamentals, management quality, valuation, technicals, and risk — plus a daily automated screener that pushes shortlisted alerts to Telegram.

**Tagline**: *"Institutional-grade research. For everyone."*

**One-liner**: Subtext is the Bloomberg Terminal for the 100 million Indian retail investors who can't afford one.

---

## 2. Problem Statement

### The Gap
Indian retail investors manage ₹40+ lakh crore in direct equities. Yet:
- **95% lack access** to quality research (brokerages only cover top 200 stocks)
- **Existing tools** (Screener.in, Tijori, Trendlyne) surface raw data — but zero actionable interpretation
- **ChatGPT/Claude** can analyze but has no live Indian market data and can't read PDFs fluently at scale
- **SEBI research analysts** cost ₹5,000–₹50,000/month for advisory subscriptions

### The Consequence
Retail investors make decisions on tips, Reddit posts, and YouTube videos. Institutions use multi-analyst research desks. The information asymmetry is enormous.

### Subtext's Answer
Combine real-time NSE/BSE data + document intelligence (RAG over PDFs) + LLM reasoning → deliver a structured, honest research report with a mandatory bear case, in 60 seconds, for free or near-free.

---

## 3. Target Users

### Primary: DIY Retail Investor (India)
- Age: 22–40
- Portfolio: ₹1L – ₹50L
- Behavior: Uses Zerodha/Groww, reads Screener.in, follows finance YouTubers
- Pain: Has data, lacks interpretation. Spends 3–6 hours researching one stock manually
- Goal: Make better-informed buy/hold/sell decisions without hiring an advisor

### Secondary: Finance Students & CFA Aspirants
- Uses Subtext to practice fundamental analysis, compare AI output vs. own analysis
- High word-of-mouth potential in colleges

### Tertiary: SEBI-Registered Research Analysts (Small RAs)
- Use Subtext as a productivity tool to generate first-draft research notes
- Potential B2B upsell path

---

## 4. Core Value Propositions

| Value | What it means |
|---|---|
| ⚡ Speed | Full research report in < 60 seconds vs. 6 hours manually |
| 🧠 Depth | 6-dimension analysis: Fundamentals, Mgmt DNA, Valuation, Technicals, Risks, Verdict |
| 🔒 Honesty | Mandatory bear case in every report. No fabricated data — "no data" if missing |
| 🔔 Proactivity | Daily screener runs at 6 AM. Shortlisted stocks → Telegram alert before market open |
| 🆓 Accessible | Free tier (5 reports/month). No Bloomberg subscription needed |
| 📱 Mobile-first | Works on mobile browser. Telegram bot for alerts |

---

## 5. Feature Requirements

### 5.1 MVP Features (Phase 1 — Ship in 4 weeks)

#### F1: Stock Research Report Generator
- User searches for any NSE-listed stock by ticker or company name
- System fetches live data (PE, ROE, Debt/Equity, Revenue growth, Promoter holding, 50/200 EMA, RSI, Volume)
- User can optionally upload PDFs (Annual Report, MDA, Concall transcripts — up to 3 files, 50MB total)
- System generates a structured report with 6 sections (see §6)
- Report is saved to user's history and downloadable as PDF
- Report generation streams in real-time (user sees text appearing, not a loading spinner)

#### F2: Daily Stock Screener
- Admin/user configures screener thresholds in a YAML-style config UI
- Default universe: Nifty 500 (configurable to Nifty 50 or custom watchlist)
- Screener runs daily at 6:00 AM IST (cron job)
- Shortlisted stocks (those passing all filters) trigger a Telegram alert

#### F3: Telegram Alert Bot
- User connects their Telegram via `/connect` command in the bot
- Every shortlisted stock alert includes:
  - Key metrics (PE, ROE, Price vs. 200 EMA)
  - 2-line AI summary
  - Bear counter-point
  - "Research Only — Not Investment Advice" disclaimer
- User can type `/research RELIANCE` in Telegram to trigger a quick mini-report

#### F4: Watchlist & Report History
- Users can add stocks to a personal watchlist
- All generated reports stored with timestamp, accessible from dashboard
- Side-by-side report comparison for 2 stocks

#### F5: Auth & User Management
- Email + Google OAuth login
- Free tier: 5 AI reports/month, daily screener alerts for up to 10 stocks
- Pro tier: Unlimited reports, full Nifty 500 screener, PDF export, priority queue

---

### 5.2 Growth Features (Phase 2 — Post-MVP)

#### F6: Portfolio Analyzer
- User inputs their portfolio (ticker + quantity)
- Subtext auto-generates a portfolio health score
- Flags concentration risk, sector imbalance, stocks with deteriorating fundamentals

#### F7: Multi-stock Comparison Table
- Compare up to 5 stocks side-by-side across all metrics
- AI gives a ranked recommendation

#### F8: Research Feed (Social Layer)
- Public feed of AI-generated research summaries (anonymized)
- Users can upvote/save research from others
- Builds network effects and SEO (publicly indexed research pages)

#### F9: Earnings Calendar Integration
- Alerts user 1 day before a watched company reports quarterly results
- Auto-runs analysis after results are published

---

## 6. Research Report Structure (The Core Output)

Every Subtext report follows this exact structure:

```
📊 SUBTEXT RESEARCH REPORT
Company: [Name] | Ticker: [NSE:XXXX] | Date: [DD-MMM-YYYY]
Generated by AI | Research Only — Not Investment Advice
─────────────────────────────────────────────

1. FUNDAMENTALS
   Revenue quality, margin trajectory, cash flow vs. reported profits,
   debt structure, ROE sustainability, accounting red flags

2. MANAGEMENT DNA
   Concall tone analysis, overpromising detection, promoter pledge/stake
   reduction flags, language change vs. prior quarter

3. VALUATION REALITY
   PE/EV-EBITDA vs. historical average and sector peers,
   growth premium assessment

4. TECHNICAL STRUCTURE
   Trend phase (accumulation/markup/distribution/markdown),
   key support/resistance, volume confirmation

5. RISK FACTORS
   3 things that could destroy this thesis (sector, company, macro)

6. FINAL VERDICT
   Buy / Hold / Avoid | Conviction: X/10
   Price at which this becomes interesting
   One-line summary

⚠️ BEAR COUNTER-POINT (mandatory in every report)
   The strongest argument AGAINST this stock right now
```

---

## 7. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Report generation time | < 60 seconds (streaming, user sees progress) |
| Screener run time | < 5 minutes for Nifty 500 |
| Uptime | 99.5% (excluding scheduled maintenance) |
| Data freshness | Live price data, fundamentals updated daily |
| No fabricated data | If any data field is missing → output "no data", never invent |
| Mobile responsiveness | Full functionality on 375px width |
| PDF upload limit | 3 files, 50MB total per report |

---

## 8. Constraints & Hard Rules

These are non-negotiable and must be enforced in code and in UI copy:

1. ❌ **No order placement** — Subtext never connects to a broker API
2. ❌ **No capital deployment** of any kind
3. ❌ **Never fabricate data** — model is instructed with strict system prompt; missing data → "no data"
4. ✅ **Mandatory disclaimer** on every report, alert, and page: "Research Only — Not Investment Advice"
5. ✅ **Mandatory bear counter-point** in every research report and Telegram alert
6. ✅ **All thresholds configurable** — nothing hardcoded in screener logic
7. ✅ **SEBI compliance**: No personalized investment advice, no target prices framed as guarantees

---

## 9. Success Metrics (KPIs)

| Metric | 30-day target | 6-month target |
|---|---|---|
| Registered users | 100 | 5,000 |
| Reports generated | 500 | 50,000 |
| Daily active users | 20 | 500 |
| Telegram bot subscribers | 50 | 2,000 |
| Free → Pro conversion | N/A | 3% |
| Report generation p95 latency | < 60s | < 45s |

---

## 10. Out of Scope (v1)

- US/global stock markets
- Options/derivatives analysis
- Real-time intraday data (end-of-day is sufficient for v1)
- Mobile native app (iOS/Android)
- SEBI RA registration (platform is a tool, not advisory service)
- Direct broker integration
