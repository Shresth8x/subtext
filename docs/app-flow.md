# Subtext — App Flow Document

> **Version**: 1.0 | **Date**: September 2026

---

## 1. User Roles

| Role | Access | Limits |
|---|---|---|
| **Guest** | Landing page, public report pages (if shared) | Cannot generate reports |
| **Free User** | Full app, all features | 5 AI reports/month, screener for 10 stocks |
| **Pro User** | Full app + PDF export + priority queue | Unlimited reports, Nifty 500 screener |
| **Admin** | Backend config, system stats | Internal only, not a UI role in v1 |

---

## 2. Screen Inventory

| Screen ID | Route | Name | Auth Required |
|---|---|---|---|
| S01 | `/` | Landing Page | No |
| S02 | `/login` | Login | No |
| S03 | `/signup` | Sign Up | No |
| S04 | `/dashboard` | Dashboard Home | Yes |
| S05 | `/research` | Research Generator | Yes |
| S06 | `/research/[reportId]` | Report Viewer | Yes (own) / No (shared) |
| S07 | `/screener` | Screener Config & Results | Yes |
| S08 | `/watchlist` | Watchlist | Yes |
| S09 | `/alerts` | Telegram Alerts Setup | Yes |
| S10 | `/settings` | Account & Preferences | Yes |
| S11 | `/upgrade` | Pricing / Upgrade | Yes |
| S12 | `/auth/callback` | OAuth Callback (redirect) | No |
| TG01 | Telegram | `/start` command | — |
| TG02 | Telegram | `/connect [code]` command | — |
| TG03 | Telegram | `/research [TICKER]` command | — |
| TG04 | Telegram | Screener alert (bot-initiated) | — |

---

## 3. Session Flow

### 3.1 New User Onboarding

```
[S01: Landing]
    │
    ├─► "Get Started Free" CTA
    │       │
    │       ▼
    │   [S03: Sign Up]
    │   (Email + password OR Google OAuth)
    │       │
    │       ▼
    │   Email verification (if email signup)
    │       │
    │       ▼
    │   [Onboarding Modal — 3 steps, skippable]
    │   Step 1: "Search for your first stock"
    │   Step 2: "Connect Telegram for daily alerts"
    │   Step 3: "Set your screener thresholds"
    │       │
    │       ▼
    │   [S04: Dashboard] ← first time empty state
    │
    └─► "Sign In" link
            │
            ▼
        [S02: Login]
            │
            ▼
        [S04: Dashboard]
```

### 3.2 Returning User Flow

```
[S02: Login] → JWT issued → [S04: Dashboard]
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
            [S05: Research] [S07: Screener] [S08: Watchlist]
```

### 3.3 Core Flow — Generate a Research Report

```
[S05: Research Generator]

1. User types company name or ticker in search bar
   → Autocomplete shows: "Reliance Industries — NSE: RELIANCE"
   → User selects

2. Live key metrics load instantly (from Redis cache or yfinance)
   → Right panel shows: PE 22.4 | ROE 18.2% | CMP ₹2,847 | ...

3. (Optional) User uploads PDFs via drag-and-drop
   → Each file uploads to R2 in background
   → File chips appear with green checkmark when ready

4. User clicks "Generate Research Report →"
   → Tier check: Free user has 3/5 reports used? Proceed.
     If 5/5 → show upgrade modal (S11)

5. Two-panel collapses, report streaming area appears below

6. Progress indicator shows:
   [✓] Fetching live market data...
   [✓] Loading your documents...
   [/] Analyzing fundamentals...    ← currently running (spinner)
   [ ] Building report...

7. Report sections stream in one by one:
   • FUNDAMENTALS card fades in, text streams
   • MANAGEMENT DNA card fades in, text streams
   • ... (all 6 sections)
   • ⚠️ BEAR COUNTER-POINT — mandatory last card

8. On completion:
   → Report saved to DB → URL updates to /research/[reportId]
   → Action bar appears: [Share] [Download PDF] [Add to Watchlist]
   → Usage counter updates: "4 / 5 reports used"

9. User can share report URL → shared report visible to anyone
   (no auth required to view public shared reports)
```

### 3.4 Telegram Bot Flow — Connect

```
[S09: Alerts screen]

1. User sees: "Connect your Telegram to receive daily screener alerts"
2. User clicks "Connect Telegram"
3. System generates a unique 8-character code: "AL-A3F9"
4. Instructions shown:
   a. Open Telegram
   b. Search @SubtextBot
   c. Send: /connect AL-A3F9

5. SubtextBot in Telegram:
   → Receives /connect AL-A3F9
   → Validates code → links Telegram chat_id to user account
   → Sends confirmation: "✅ Connected! You'll receive daily screener alerts."

6. S09 updates: "🟢 Telegram Connected | @username"
7. User can toggle alert types:
   - Daily screener results
   - Earnings reminders (Phase 2)
   - Watchlist alerts (Phase 2)
```

### 3.5 Telegram Bot Flow — Quick Research

```
User in Telegram types: /research RELIANCE

Bot responds:
  "⏳ Generating mini-report for RELIANCE..."

  (30 seconds later)

  "📊 RELIANCE — Quick Research
   PE: 22.4 | ROE: 18.2% | D/E: 0.43 | Promoter: 50.3%

   FUNDAMENTALS: Revenue has grown 12% YoY driven by Jio...
   VERDICT: Hold | Conviction: 7/10
   BEAR CASE: Retail segment margins remain under pressure...

   ⚠️ Research Only — Not Investment Advice
   🔗 Full report: subtext.co/research/[id]"
```

### 3.6 Screener Alert Flow (Bot-Initiated)

```
[Daily 6:00 AM IST — Celery cron job fires]

1. Celery task: run_daily_screener for all users with active screener config

2. For each user:
   a. Fetch Nifty 500 fundamentals (batched, cached)
   b. Apply user's thresholds
   c. Build shortlist

3. Telegram message sent per user:

   "📊 SUBTEXT DAILY SCREENER — 14 Sep 2026
   Nifty 500 | 6 stocks shortlisted today

   ✅ RELIANCE — PE 22 | ROE 18% | ▲ Above 200 EMA
   ✅ INFY — PE 24 | ROE 29% | ▲ Above 200 EMA
   ✅ TATAPOWER — PE 28 | ROE 14% | ▲ Above 200 EMA
   [+ 3 more]

   ⚠️ Bear reminder: Screener finds candidates, not certainties.
   Research before acting.
   🔗 View full screener results: subtext.co/screener

   Research Only — Not Investment Advice"
```

---

## 4. State Transitions

### Report States

```
[idle] → [fetching_data] → [uploading_docs] → [generating] → [streaming] → [complete]
                                                     ↓
                                                 [failed] → Error card with retry
```

### Screener States

```
[idle] → [running] → [complete] → [alert_sent]
            ↓
         [failed] → Logged, no alert sent, error in dashboard
```

---

## 5. Error States & Recovery

| Error | User-facing message | Recovery |
|---|---|---|
| Stock not found in yfinance | "No data available for [TICKER]. Try a different ticker." | Suggest similar |
| PDF upload failed | "Upload failed. Please check file size (max 50MB) and format (PDF only)." | Retry button |
| LLM timeout (> 90s) | "Report is taking longer than usual. Your report will be emailed when ready." | Email fallback |
| Rate limit hit | "You've used all 5 reports this month. Upgrade for unlimited access." | Upgrade CTA |
| Screener data unavailable | Log "no data" for that ticker, skip it | Silent skip + log |
| Telegram not connected | "Connect Telegram in Settings → Alerts to receive this alert." | Link to S09 |

---

## 6. Navigation Rules

- **Active route** highlighted in sidebar with gold left border
- **Breadcrumb** shown on report viewer: `Research / RELIANCE / Report — 14 Sep 2026`
- **Back navigation**: Browser back always works (no history manipulation)
- **Deep links**: Every report has a permanent URL shareable without auth
- **404**: Custom page with "Stock not found" messaging and search bar

---

## 7. Mobile-Specific Flows

### Bottom Tab Bar (mobile)
```
[🏠 Home] [🔍 Research] [📊 Screener] [⭐ Watchlist] [🔔 Alerts]
```

### Mobile Report Generation
1. Search bar at top (sticky)
2. Select stock → metrics card slides up from bottom (sheet)
3. Upload button → native file picker
4. Generate → full-screen report reader (not split panel)
5. Swipe between report sections (card carousel)

---

## 8. Upgrade Flow (Free → Pro)

```
[Trigger: user hits 5 report limit, or clicks "Upgrade" in sidebar]
     │
     ▼
[S11: Upgrade Modal/Page]
  Free tier summary | Pro features list | ₹499/month (or ₹4,999/year)
     │
     ▼
  [Pay with Razorpay] (Phase 2 — Phase 1 has no paywall, all free)
     │
     ▼
  Webhook → Backend updates user.tier = 'pro'
     │
     ▼
  "Welcome to Pro! Limits removed."
```

> [!NOTE]
> In Phase 1 (hackathon demo), all users get Pro-tier access. Billing infrastructure is Phase 2.
