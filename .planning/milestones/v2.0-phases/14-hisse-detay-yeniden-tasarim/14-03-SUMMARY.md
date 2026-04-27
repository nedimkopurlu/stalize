---
phase: 14-hisse-detay-yeniden-tasarim
plan: "03"
subsystem: frontend-components, backend-api
tags: [fundamentals, kap-news, glassmorphism, stock-detail]
dependency_graph:
  requires: [14-01]
  provides: [FundamentalMetricCard, KAPNewsCard, GET /stocks/{symbol}/fundamentals]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx, backend/app/api/stocks.py]
tech_stack:
  added: []
  patterns: [glassmorphism-card, parallel-fetch, type-alias]
key_files:
  created:
    - frontend/src/components/FundamentalMetricCard.tsx
    - frontend/src/components/KAPNewsCard.tsx
  modified:
    - backend/app/api/stocks.py
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/[symbol]/page.tsx
decisions:
  - "Used KapNewsItem = StockNewsItem type alias — existing news endpoint already returns correct shape with items field"
  - "GET /stocks/{symbol}/news already existed (line 323); only added /fundamentals endpoint"
  - "Fundamentals and kapNews fetched non-blocking in parallel after main loadStock to avoid blocking page render"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-26"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 5
---

# Phase 14 Plan 03: Temel Metrik Kartı ve KAP Haber Bileşeni — Summary

One-liner: Glassmorphism FundamentalMetricCard (F/K, PD/DD, ROE, net marj, borç/özsermaye) ve KAPNewsCard (başlık+tarih+kategori+dış link) bileşenleri oluşturuldu; GET /stocks/{symbol}/fundamentals endpoint eklendi; hisse detay sayfasına entegre edildi.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Backend — GET /stocks/{symbol}/fundamentals endpoint | 3f117fa9 | backend/app/api/stocks.py |
| 2 | Frontend — FundamentalMetricCard + KAPNewsCard + api.ts + page.tsx | 018f7a51 | api.ts, FundamentalMetricCard.tsx, KAPNewsCard.tsx, page.tsx |

## What Was Built

### Task 1 — Backend
- Added `Fundamental` model import to `stocks.py`
- Added `GET /stocks/{symbol}/fundamentals` endpoint returning `pe_ratio`, `pb_ratio`, `roe`, `net_margin`, `debt_to_equity`, `fundamental_score`, `period`
- Returns null fields (not errors) when no fundamentals record exists for the stock
- `GET /stocks/{symbol}/news` was already present at line 323 — not duplicated

### Task 2 — Frontend
**api.ts:**
- Added `KapNewsItem` as type alias for existing `StockNewsItem` (same shape, backend already returns correct fields)
- Added `StockFundamentals` interface matching backend response
- Added `getStockFundamentals(symbol)` function to api object

**FundamentalMetricCard.tsx:**
- 5 MetricRow components: F/K (P/E), PD/DD (P/B), ROE (×100 → %), Net Marj (×100 → %), Borç/Özsermaye
- Shows `—` (dash) for null values, never 'N/A'
- Period label shown when available
- Loading and empty states handled

**KAPNewsCard.tsx:**
- Shows title as clickable `<a target="_blank">` when `url` is present, plain text otherwise
- Date formatted in Turkish locale (tr-TR)
- Category badge with Turkish labels (Jeopolitik, Makro, Sektör, Şirket)
- Source label shown as secondary text
- Empty state: "Henüz bildirim yok"

**page.tsx:**
- Imports: `FundamentalMetricCard`, `KAPNewsCard`, `KapNewsItem`, `StockFundamentals` added
- State: `fundamentals`, `kapNews`, `fundLoading`, `newsLoading` added
- In `loadStock`: parallel non-blocking fetch of fundamentals and kapNews after main data loads
- metricsRow[0] placeholder replaced with `<FundamentalMetricCard fundamentals={fundamentals} loading={fundLoading} />`
- bottomGrid[1] inline KAP news implementation replaced with `<KAPNewsCard news={kapNews} loading={newsLoading} />`

## Deviations from Plan

### Auto-noted: Different approach for KapNewsItem

**Found during:** Task 2
**Issue:** Plan specified a new `KapNewsItem` interface with `news[]` array, but existing `getStockNews()` already returns `StockNewsResponse` with `items[]`. Creating a separate interface would be redundant.
**Fix:** Used `export type KapNewsItem = StockNewsItem` alias instead — same type, no duplication. KAPNewsCard receives `items` passed as `news` prop from page.tsx.
**Impact:** Zero — type-safe, TypeScript clean.

## Known Stubs

None — all data fields are wired to real DB queries. Null values display `—` as specified.

## Success Criteria Verification

- GET /stocks/{symbol}/news: already existed, returns 200 with `items[]` array
- GET /stocks/{symbol}/fundamentals: added, returns 200 with pe_ratio/pb_ratio/roe/net_margin/debt_to_equity
- FundamentalMetricCard: 5 MetricRow components (F/K, PD/DD, ROE, net marj, borç/özsermaye)
- KAPNewsCard: url present = KAP dış link; url absent = plain text; empty = "Henüz bildirim yok"
- TypeScript: zero errors in modified files (only pre-existing .next/dev/types error for deleted causal page)
- page.tsx metricsRow[0] and bottomGrid[1] placeholders replaced with real components

## Self-Check: PASSED

Files exist:
- frontend/src/components/FundamentalMetricCard.tsx: FOUND
- frontend/src/components/KAPNewsCard.tsx: FOUND

Commits exist:
- 3f117fa9: FOUND (backend fundamentals endpoint)
- 018f7a51: FOUND (frontend components)
