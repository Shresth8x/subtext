# Subtext — UX Design Document

> **Version**: 1.0 | **Date**: September 2026

---

## 1. Design Philosophy

### Core Principle: "Serious But Approachable"

Subtext serves retail investors who are smart but not professional traders. The design must feel:
- **Trustworthy** — like a Bloomberg or Refinitiv, not a crypto gambling site
- **Clear** — financial data is complex; the UI must reduce cognitive load, not add to it
- **Fast** — no loading spinners on the main action. Stream everything.
- **Honest** — disclaimers are visible, not hidden in footer fine print

### Anti-patterns to Avoid
- ❌ Red/green flashing numbers (casino feel)
- ❌ Dark patterns hiding the "Research Only" disclaimer
- ❌ Information overload — don't show 50 metrics at once
- ❌ Overwhelming dashboards that feel like a data warehouse
- ❌ Generic SaaS blue-and-white (boring, forgettable)

---

## 2. Visual Identity

### 2.1 Color Palette

**Primary brand**: Deep navy with gold accents — communicates wealth, trust, intelligence

```css
/* Brand Colors */
--color-navy-950: #0a0f1e;    /* Page background */
--color-navy-900: #0d1529;    /* Card background */
--color-navy-800: #1a2540;    /* Elevated surface */
--color-navy-700: #1e2d4a;    /* Borders, dividers */
--color-navy-400: #4a6080;    /* Muted text */

--color-gold-400: #d4a853;    /* Primary accent — brand gold */
--color-gold-300: #e8c070;    /* Hover state gold */
--color-gold-100: #fdf3dc;    /* Light gold tint */

/* Semantic Colors */
--color-buy: #22c55e;         /* Green — Buy verdict */
--color-hold: #f59e0b;        /* Amber — Hold verdict */
--color-avoid: #ef4444;       /* Red — Avoid verdict */

/* Neutrals */
--color-text-primary: #f0f4ff;   /* Near-white body text */
--color-text-secondary: #9ab0cc; /* Muted labels */
--color-text-muted: #4a6080;     /* Timestamps, metadata */
```

**Accent glow effects**: Subtle `box-shadow: 0 0 20px rgba(212, 168, 83, 0.15)` on active cards.

### 2.2 Typography

```css
/* Import in globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

--font-sans: 'Inter', system-ui, sans-serif;    /* Body, UI */
--font-mono: 'JetBrains Mono', monospace;        /* Tickers, numbers, data */

/* Scale */
--text-xs:   0.75rem;   /* 12px — metadata, timestamps */
--text-sm:   0.875rem;  /* 14px — secondary labels */
--text-base: 1rem;      /* 16px — body text */
--text-lg:   1.125rem;  /* 18px — section headers */
--text-xl:   1.25rem;   /* 20px — card titles */
--text-2xl:  1.5rem;    /* 24px — page titles */
--text-3xl:  1.875rem;  /* 30px — hero text */
```

**Rule**: All stock tickers displayed in `font-mono`. All prices and percentages in `font-mono`. All prose analysis in `font-sans`.

### 2.3 Spacing & Grid

- Base unit: 4px (0.25rem)
- Card padding: 24px (1.5rem)
- Section gap: 32px (2rem)
- Page max-width: 1280px with 24px horizontal padding
- Content area (with sidebar): 960px max

### 2.4 Component Style

**Cards**: `border-radius: 12px`, `border: 1px solid var(--color-navy-700)`, subtle gold-glow on hover

**Buttons**:
- Primary: Gold fill, navy text, 8px radius
- Secondary: Ghost with gold border
- Danger: Red with low opacity background

**Input fields**: Dark fill, gold focus ring (`outline: 2px solid var(--color-gold-400)`)

---

## 3. Layout System

### 3.1 Global Layout

```
┌─────────────────────────────────────────────────────────┐
│  TOPBAR (64px)                                          │
│  [Subtext logo]    [Search]    [Tier badge] [Avatar]  │
├──────────────┬──────────────────────────────────────────┤
│  SIDEBAR     │  MAIN CONTENT AREA                       │
│  (240px)     │                                          │
│              │  [Page content — max 960px centered]     │
│  - Dashboard │                                          │
│  - Research  │                                          │
│  - Screener  │                                          │
│  - Watchlist │                                          │
│  - Alerts    │                                          │
│  - Settings  │                                          │
│              │                                          │
│  [Pro badge] │                                          │
└──────────────┴──────────────────────────────────────────┘
```

**Mobile (< 768px)**: Sidebar collapses to bottom tab bar with 5 icons.

### 3.2 Sidebar Navigation Items

| Icon | Label | Route |
|---|---|---|
| BarChart2 | Dashboard | /dashboard |
| Search | Research | /research |
| Filter | Screener | /screener |
| Star | Watchlist | /watchlist |
| Bell | Alerts | /alerts |
| Settings | Settings | /settings |

---

## 4. Screen-by-Screen UI Rules

### 4.1 Dashboard

**Purpose**: At-a-glance overview of watchlist, recent reports, screener status

**Layout**: 3-column grid (on desktop)
- Column 1 (60%): Recent reports list + watchlist quick view
- Column 2 (40%): Screener status card + next run countdown + Telegram connection status

**Key components**:
- **Screener Status Card**: Shows last run time, # shortlisted stocks, next run at HH:MM. Gold pulsing dot if screener is running.
- **Recent Reports**: List of last 5 reports with verdict badge (Buy/Hold/Avoid) and conviction score. Clickable.
- **Usage Meter** (free tier): "3 / 5 reports used this month" with progress bar. Gold-colored bar.

### 4.2 Research Generator

**This is the hero screen — must be stunning.**

**Layout**: Two-panel

**Left Panel (55%)**: Input area
```
[Company search input — full width, prominent]
   Placeholder: "Search by company name or NSE ticker..."
   Autocomplete dropdown: shows top 5 matches with logo + ticker

[Upload Documents section]
   Drag-and-drop zone with dashed gold border
   "Upload Annual Report, MDA, Concall Transcripts (PDF, max 50MB)"
   File chips appear below when uploaded (with remove X)

[Generate Report button — full width, gold, large]
   "Generate Research Report →"
```

**Right Panel (45%)**: Context panel
- When empty: Shows "What Subtext analyzes" — 6 icons for each section
- When stock selected: Shows live key stats (PE, ROE, CMP, 52W H/L) — instantly fetched
- When report generating: Progress indicator with current step ("Fetching fundamentals... Analyzing documents... Generating report...")

**Streaming report display**: Below the two panels, once generation starts, the report appears section by section, with a blinking cursor. Each section has a header card that fades in as it streams.

### 4.3 Report Viewer

**URL**: `/research/[reportId]`

**Layout**: Full-width reading experience (max 800px centered)

**Header**:
```
[Company Name]  NSE: TICKER  •  Generated on: DD-MMM-YYYY
[Verdict Badge: BUY/HOLD/AVOID]  Conviction: 8/10
Research Only — Not Investment Advice
```

**6 Section Cards**: Each section is a card with:
- Section icon + title (colored header)
- AI-generated prose
- Cards are collapsible (click header to collapse)

**Bear Counter-Point**: Always at bottom, styled distinctly with a ⚠️ amber warning card. Cannot be collapsed.

**Action bar** (sticky bottom on mobile):
```
[Share] [Download PDF] [Add to Watchlist] [Regenerate]
```

**Key metric bar** (horizontal, below header):
```
PE: 22.4  |  ROE: 18.2%  |  D/E: 0.43  |  Promoter: 50.3%  |  200EMA: ▲ Above
```
All in monospace font. Color-coded: green if good, red if concerning, grey if neutral.

### 4.4 Screener Config

**Layout**: Split — config on left, preview on right

**Left**: Sliders and toggles for each threshold
```
[Universe selector]: Nifty 50 / Nifty 500 / Custom

[Filter: Max PE Ratio]     [Toggle ON/OFF]
Slider: 0 ←──────●──── 100    Value: 35

[Filter: Min ROE %]        [Toggle ON/OFF]
Slider: 0 ←──●────── 50       Value: 15

... (all configurable thresholds)

[Screener Schedule]: Daily at [06:00 AM IST ▼]

[Save & Activate button]
```

**Right**: Live preview — "Based on these settings, ~47 stocks from Nifty 500 would have passed yesterday's run."

**Results Table** (below): Last screener run results as sortable table.

### 4.5 Watchlist

**Layout**: Table + mini chart on row hover

**Columns**: Company | Ticker | CMP | PE | ROE | Last Report (verdict) | Actions

**Row actions**: Quick Research (opens generator) | Remove from Watchlist

### 4.6 Alerts (Telegram Setup)

**Step-by-step flow**:
```
Step 1: Search for @SubtextBot on Telegram
Step 2: Send /connect [shows user's unique code]
Step 3: Enter the code here → [____________________]
Step 4: Verify ✓
```

Once connected: Shows bot status (🟢 Connected), last alert sent, option to configure alert preferences.

---

## 5. Motion & Animation

| Element | Animation | Duration |
|---|---|---|
| Page transition | Fade + slide up (4px) | 200ms ease-out |
| Card hover | Gold glow intensify + 2px lift | 150ms ease |
| Report sections | Fade in staggered (each section 100ms apart) | 300ms |
| Streaming text | No animation — raw stream is already engaging | — |
| Verdict badge on load | Scale from 0.9 → 1.0 | 300ms spring |
| Sidebar item active | Slide gold bar from left | 150ms |
| Screener running | Pulsing gold dot | 1.5s infinite |
| Toast notifications | Slide in from bottom-right | 250ms |

**Rule**: No animation exceeds 300ms. No infinite animations except the screener pulse dot.

---

## 6. Empty States

Every empty state must be helpful, not just "No data":

| State | Message | CTA |
|---|---|---|
| No reports yet | "Your research journey starts here. Search for any NSE stock." | Search stock |
| Empty watchlist | "Add stocks to your watchlist to track them." | Browse stocks |
| Screener not configured | "Set your thresholds and let Subtext find opportunities for you." | Configure screener |
| Telegram not connected | "Connect Telegram to get daily alerts before market opens." | Connect now |

---

## 7. Accessibility Rules

- All interactive elements accessible via keyboard (Tab + Enter)
- Color is never the only indicator (always paired with icon or text)
- All icons have `aria-label`
- WCAG AA contrast ratio for all text (minimum 4.5:1)
- Focus ring always visible (gold outline)
- Screen reader support for verdict badges (role="status")

---

## 8. Responsive Breakpoints

```css
/* Mobile first */
sm:  640px   /* Large mobile */
md:  768px   /* Tablet */
lg:  1024px  /* Desktop sidebar layout unlocks */
xl:  1280px  /* Max content width */
```

**Mobile adaptations**:
- Sidebar → bottom tab bar
- Two-panel layouts → single column, stacked
- Report key metrics → horizontal scroll
- Tables → card list view
- Charts → reduced height (200px)
