---
phase: 13-dashboard-hisse-listesi-glassmorphism
plan: "02"
subsystem: frontend/dashboard
tags: [dashboard, glassmorphism, sparkline, kap-feed, lightweight-charts]
dependency_graph:
  requires: [13-01]
  provides: [dashboard-redesign, sparkline-widget, kap-feed-column]
  affects: [frontend/src/app/page.tsx, frontend/src/lib/api.ts, backend/app/api/stocks.py]
tech_stack:
  added: [lightweight-charts@5.1.0 (AreaSeries v5 API)]
  patterns: [glassmorphism .glass-card, CSS grid 2-column layout, dynamic import for SSR safety]
key_files:
  created:
    - frontend/src/components/SparklineWidget.tsx
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/page.tsx
    - frontend/src/app/page.module.css
    - backend/app/api/stocks.py
decisions:
  - "KAP feed sourced from NewsItem where source='KAP' — no separate model needed"
  - "Sparkline data via yfinance in a new GET /stocks/sparkline endpoint (same pattern as macro.py)"
  - "kap-feed and sparkline routes placed BEFORE /{symbol} wildcard to avoid FastAPI routing conflict"
  - "lightweight-charts AreaSeries used over LineSeries for visual fill under the line"
  - "Existing portfolio cards and stats kept intact — plan only required adding missing pieces"
metrics:
  duration: "~25 minutes"
  completed_date: "2026-04-25"
  tasks: 3
  files_changed: 5
requirements_satisfied: [GLUI-02, CLEN-01, VIZZ-03]
---

# Phase 13 Plan 02: Dashboard Yeniden Tasarım (Sparkline + KAP Feed) Summary

Dashboard AI brifing bölümü kaldırılarak 3 bölgeli yeni layout tamamlandı: makro bant (üst), ana içerik alanı (sparkline widgetları + portföy + hisse tablosu, ~70%), sağ sütun (KAP bildirimleri, 320px sabit) — lightweight-charts v5 AreaSeries ile BIST100 ve USD/TRY 30 günlük sparkline, yfinance'den gerçek veri.

## What Was Built

### Task 1 — api.ts genişletmesi (commit: 5eec4d7c)
- `KapNotification`, `SparklinePoint`, `SparklineResponse` interface'leri eklendi
- `api.getKapFeed(limit)` → `GET /stocks/kap-feed?limit=10`
- `api.getSparklineData(symbol, days)` → `GET /stocks/sparkline?symbol=XU100&days=30`

### Task 2 — SparklineWidget.tsx (commit: f06f9d08)
- `'use client'` direktifli yeni bileşen
- lightweight-charts v5 `AreaSeries` (v5 breaking change: `chart.addSeries(AreaSeries)` pattern)
- `dynamic import('lightweight-charts')` SSR güvenliği için
- Trend rengi: son kapanış > ilk kapanış → `#10b981` (yeşil), aksi halde `#ef4444` (kırmızı)
- `useEffect` cleanup ile `chart.remove()`
- Boş state: "Veri yok" placeholder
- 30 günlük yüzde değişim etiketi

### Task 3 — Backend endpoints + dashboard page.tsx (commit: 0d9186c9)
Backend (stocks.py):
- `GET /stocks/kap-feed` — `NewsItem` tablosundan `source='KAP'` kayıtları, `/{symbol}` wildcard'ından ÖNCE tanımlandı
- `GET /stocks/sparkline` — yfinance `ticker.history()` ile günlük kapanış, son N noktayı döner

Frontend (page.tsx):
- `getIntelligenceOverview`, `IntelligenceOverview` import'u tamamen kaldırıldı
- 3 bölgeli grid layout: `mainLayout` (1fr 320px), `mainContent`, `rightColumn`
- `sparklineGrid` (2 kolon) ile BIST100 + USD/TRY SparklineWidget entegrasyonu
- KAP sütunu: `glass-card`, `maxHeight: 500px`, her bildirim tıklanabilir dış link
- Boş KAP: "Henüz bildirim yok" empty state
- Hisse tablosu `.glass-card` ile glassmorphism
- Her bölüm için ayrı loading skeleton

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Backend endpoints did not exist**
- **Found during:** Task 3
- **Issue:** Frontend calls `GET /stocks/kap-feed` and `GET /stocks/sparkline` but neither endpoint existed in backend
- **Fix:** Added both endpoints to `backend/app/api/stocks.py` before the `/{symbol}` wildcard route
- **Files modified:** `backend/app/api/stocks.py`
- **Commit:** 0d9186c9

**2. [Rule 3 - Blocking] page.module.css missing layout classes**
- **Found during:** Task 3
- **Issue:** New `mainLayout`, `mainContent`, `rightColumn`, `sparklineGrid` CSS classes referenced in page.tsx but absent from page.module.css
- **Fix:** Added all four class definitions with responsive breakpoints
- **Files modified:** `frontend/src/app/page.module.css`
- **Commit:** 0d9186c9

## Known Stubs

None. All data is wired to real API endpoints:
- Sparkline: yfinance 30-day close data via `/stocks/sparkline`
- KAP feed: real `NewsItem` records (source='KAP') via `/stocks/kap-feed`
- If no KAP data exists in DB, "Henüz bildirim yok" empty state is shown — correct behavior per spec

## Verification Results

```
# getBriefing/getIntelligenceOverview kaldırıldı?
grep "getBriefing|getIntelligenceOverview|BriefingData" frontend/src/app/page.tsx
# → boş çıktı ✓

# getKapFeed/getSparklineData var mı?
grep "getKapFeed|getSparklineData" frontend/src/app/page.tsx
# → 3 satır ✓

# TypeScript hatası?
npx tsc --noEmit → sadece causal page pre-existing error ✓

# Build?
npx next build → ✓ 10/10 pages, no errors
```

## Self-Check: PASSED

Files exist:
- frontend/src/components/SparklineWidget.tsx — FOUND
- frontend/src/lib/api.ts — FOUND (KapNotification, SparklineResponse exported)
- frontend/src/app/page.tsx — FOUND (no getBriefing, has getKapFeed/getSparklineData)
- backend/app/api/stocks.py — FOUND (/stocks/kap-feed and /stocks/sparkline endpoints)

Commits exist:
- 5eec4d7c — api.ts types + functions ✓
- f06f9d08 — SparklineWidget.tsx ✓
- 0d9186c9 — backend endpoints + page.tsx redesign ✓
