---
phase: 26
plan: 1
title: Frontend Quality — FE-01 through FE-05
status: complete
completed: "2026-04-28"
---

# Phase 26 — Frontend Quality: Summary

## What Was Done

### FE-01: Empty Catch Blocks Fixed

- `frontend/src/app/screener/page.tsx` line 61: `catch(() => {})` → `catch((e: unknown) => console.error('Sector load failed:', e))`
- `frontend/src/app/stocks/page.tsx` line 33: same fix

### FE-02: MacroPanel Unsafe Type Assertion Removed

`frontend/src/lib/api.ts` `MacroIndicators` interface — added all `*_as_of` fields from the backend response:
```typescript
usdtry_as_of: string | null;
gold_try_as_of: string | null;
bist100_as_of: string | null;
interest_rate_as_of: string | null;
inflation_rate_as_of: string | null;
```

`frontend/src/components/MacroPanel.tsx` — removed double `as string` cast:
```typescript
const rawAsOf = indicators[asOfKey];
const asOfValue = typeof rawAsOf === 'string' ? rawAsOf : null;
```

TypeScript now knows `indicators[asOfKey]` is `string | null` — no unsafe assertion needed.

### FE-03: Screener Uses api.ts

`frontend/src/lib/api.ts` — added `screenStocks()` function:
```typescript
screenStocks: (params: Record<string, string>) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<{ stocks?: StockSummary[]; count?: number }>(`/screener?${qs}`);
},
```

`frontend/src/app/screener/page.tsx` — replaced raw `fetch()` with `api.screenStocks(params)`. All error handling now flows through the centralized `apiFetch` wrapper.

### FE-04: Portfolio Form Client-Side Validation

`frontend/src/app/portfolio/page.tsx` `submitPosition()` — added validation before API call:
```typescript
const entryPrice = Number(form.entry_price);
const quantity = Number(form.quantity);
if (entryPrice <= 0) { setError('Alış fiyatı 0\'dan büyük olmalı'); return; }
if (quantity <= 0) { setError('Adet 0\'dan büyük olmalı'); return; }
```

### FE-05: Confirmation Dialogs for Destructive Actions

- `frontend/src/app/portfolio/page.tsx` `closePosition()`:
  ```typescript
  if (!window.confirm('Bu pozisyonu kapatmak istediğinizden emin misiniz?')) return;
  ```
- `frontend/src/app/watchlist/page.tsx` `removeSymbol()`:
  ```typescript
  if (!window.confirm(`${sym} izleme listesinden çıkarılsın mı?`)) return;
  ```

## Files Changed

- `frontend/src/lib/api.ts`
- `frontend/src/components/MacroPanel.tsx`
- `frontend/src/app/screener/page.tsx`
- `frontend/src/app/stocks/page.tsx`
- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/watchlist/page.tsx`

## Acceptance Criteria Status

- [x] FE-01: `catch(() => {})` blokları kaldırıldı; sektör yükleme hatası console.error ile loglanıyor
- [x] FE-02: `asOfKey` unsafe type assertion kaldırıldı; MacroIndicators tipi tüm `*_as_of` alanlarını içeriyor
- [x] FE-03: Screener tüm fetch işlemlerini `api.screenStocks()` üzerinden yapıyor
- [x] FE-04: Portföy formu `entry_price <= 0` veya `quantity <= 0` gönderildiğinde client-side hata gösteriyor
- [x] FE-05: Pozisyon kapatma ve watchlist çıkarma aksiyonları onay dialogu gösterdikten sonra gerçekleşiyor
