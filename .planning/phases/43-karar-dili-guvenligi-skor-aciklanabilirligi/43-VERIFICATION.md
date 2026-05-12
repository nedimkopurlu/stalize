---
phase: 43-karar-dili-guvenligi-skor-aciklanabilirligi
verified: 2026-05-12T18:30:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 43: Karar Dili Güvenliği & Skor Açıklanabilirliği Verification Report

**Phase Goal:** "GÜÇLÜ AL/SAT" gibi direktif etiketler direktif olmayan güvenli dile çevrilir; hisse detay sayfasında skor bileşen dökümü ve veri bütünlüğü göstergesi eklenir.
**Verified:** 2026-05-12T18:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Hisse listesinde (/stocks) "Görünüm" kolonu ve güvenli etiket gösteriliyor | VERIFIED | `stocks/page.tsx:258` — `<th>Görünüm</th>`; `safeLabel(stock.recommendation)` at line 323 |
| 2 | Hisse detay AI Karar Kartı signalLabel güvenli etiketle gösteriliyor | VERIFIED | `stocks/[symbol]/page.tsx:684-686` — `title={safeLabelTooltip(recommendation)}` + `{safeLabel(recommendation)}` |
| 3 | Model portföy HoldingRow recommendation güvenli etiket + tooltip ile gösteriliyor | VERIFIED | `model-portfolio/page.tsx:88-91` — `title={safeLabelTooltip(...)}` + `{safeLabel(...)}` |
| 4 | Dashboard ideaCard stock.recommendation güvenli etiketle gösteriliyor | VERIFIED | `page.tsx:238-239` — `title={safeLabelTooltip(stock.recommendation)}` + `{safeLabel(stock.recommendation)}` |
| 5 | Her güvenli etiketin yanında title tooltip metni mevcut | VERIFIED | All 4 display points have `title={safeLabelTooltip(...)}` confirmed |
| 6 | Hisse detay sayfasında "Skor Dökümü" bölümü progress bar formatında görünüyor | VERIFIED | `stocks/[symbol]/page.tsx:771-826` — `<section className={styles.breakdownSection}>` with `bd.components.map(...)` |
| 7 | Skor Dökümü her bileşen için progress bar + normalize edilmiş katkı yüzdesi gösteriyor | VERIFIED | `line 788` — `comp.normalized_weight * 100`; `styles.breakdownBarFill` with dynamic width |
| 8 | Eksik bileşen varsa "Eksik veri — ağırlık yeniden dağıtıldı" uyarısı çıkıyor | VERIFIED | `line 778-782` — `bd.summary.missing_component_count > 0` guard with `breakdownMissingAlert` div |
| 9 | Hisse listesinde ve detayda N/M bileşen sayacı görünüyor | VERIFIED | Detail: `line 703-710` `availableComponentCount/totalComponentCount bileşen mevcut`; List: `line 299` `componentCount(stock).available/total` badge |
| 10 | Yüksek volatilite durumunda sarı uyarı ikonu + tooltip çıkıyor | VERIFIED | Detail: `lines 466-477, 712-716` `volatilityAlert` calc + `volatilityWarning` span; List: `line 62 + 301-305` `isHighDailyVolatility()` + `volWarn` span |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/app/stocks/page.tsx` | `safeLabel` call in recommendation cell; `componentCount`, `isHighDailyVolatility` helpers | VERIFIED | `safeLabel` at lines 34,36,323; `componentCount` at 52; `isHighDailyVolatility` at 62; all wired into row render |
| `frontend/src/app/stocks/[symbol]/page.tsx` | `safeLabel` helper + tooltip, `breakdownSection` JSX, `volatilityAlert`, bileşen sayacı | VERIFIED | `safeLabel` at lines 166-173; breakdown at 771-826; `volatilityAlert` at 466; `componentIntegrity` at 703 |
| `frontend/src/app/model-portfolio/page.tsx` | `safeLabel` in HoldingRow with tooltip | VERIFIED | `safeLabel` at lines 59-66; applied at 88-91 with `title={safeLabelTooltip(...)}` |
| `frontend/src/app/page.tsx` | `safeLabel` in ideaCard recommendation span | VERIFIED | `safeLabel` at lines 102-109; applied at 238-239 |
| `frontend/src/app/stocks/[symbol]/page.module.css` | `breakdownSection`, `breakdownBar*`, `componentIntegrity`, `volatilityWarning` CSS classes | VERIFIED | All classes present at lines 1254-1356 |
| `frontend/src/app/stocks/page.module.css` | `integrityCell`, `componentBadge`, `volWarn` CSS classes | VERIFIED | All classes present at lines 316-342 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `recommendation string (backend)` | `safeLabel() helper` | `SAFE_LABEL_MAP Record lookup` | WIRED | Defined in all 4 pages; map covers all 5 recommendation levels |
| `safeLabel helper` | `title attribute tooltip` | `title={safeLabelTooltip(rec)}` / `SAFE_LABEL_TOOLTIP` | WIRED | All 4 display points have tooltip wired |
| `GET /stocks/{symbol}/score-breakdown` | `scoreBreakdown state` | `api.getStockScoreBreakdown(symbol)` at line 344 in Promise.all | WIRED | `api.ts:1047-1048` defines method; fetched in `loadStock` |
| `scoreBreakdown.breakdown.components` | `breakdownSection` render | `bd?.components map` at line 786 | WIRED | `const bd = scoreBreakdown?.breakdown ?? null` at line 429; `bd.components.map(...)` at 786 |
| `scoreBreakdown.breakdown.summary.available_component_count` | `N/M bileşen mevcut` text | `bd?.summary.available_component_count` at lines 476-477, 710 | WIRED | Both `totalComponentCount` and `availableComponentCount` computed correctly |
| `allPrices (20-day close)` | `volatilityAlert` boolean | `allPrices.slice(-20)` computation at lines 466-474 | WIRED | `volatile = abs((last-first)/first)*100 > 15`; conditional render at 712-716 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| KARAR-01 | 43-01 | Direktif etiketler yerine güvenli, direktif olmayan etiketler kullanılır | SATISFIED | `SAFE_LABEL_MAP` with all 5 levels in all 4 pages; display-layer only, DB unchanged |
| KARAR-02 | 43-02 | Skor gösteriminin yanında veri bütünlüğü göstergesi (kaç bileşen mevcut/eksik) | SATISFIED | `N/M bileşen mevcut` in detail page; `componentBadge` in list page |
| KARAR-03 | 43-02 | Yüksek volatilite veya eksik fundamental verisi için görsel uyarı | SATISFIED | `volatilityAlert` (20g >%15) in detail; `isHighDailyVolatility` (daily >%4) proxy in list; `volWarn` amber icon |
| KARAR-04 | 43-01 | Her karar etiketinin yanında anlamını açıklayan tooltip | SATISFIED | `SAFE_LABEL_TOOLTIP` + `title={safeLabelTooltip(...)}` on all 4 display points |
| SKOR-01 | 43-02 | Hisse detayda skor bileşen dökümü: temel/teknik/sentiment katkısı yüzde ve rakam olarak | SATISFIED | `breakdownSection` with `comp.raw_score` + `comp.normalized_weight * 100` katkı |
| SKOR-02 | 43-02 | Bileşen eksikse "Eksik veri — ağırlık yeniden dağıtıldı" uyarısı | SATISFIED | `breakdownMissingAlert` div shown when `bd.summary.missing_component_count > 0` |
| SKOR-03 | 43-02 | Skor dökümü backend `score-breakdown` API'den dinamik render | SATISFIED | `api.getStockScoreBreakdown(symbol)` fetched in `loadStock` Promise.all; `bd.components.map(...)` renders live data |

All 7 requirement IDs (KARAR-01..04, SKOR-01..03) satisfied. No orphaned requirements detected.

---

### Anti-Patterns Found

None detected. Checked all 4 modified frontend pages for:
- TODO/FIXME/placeholder comments — none found in phase additions
- Raw directive labels ("GÜÇLÜ AL", etc.) leaking into render output — none found outside SAFE_LABEL_MAP definitions and color-logic helpers (recColor, recSafeColor) which don't display strings directly
- Empty return implementations — not present; all new sections guarded with data checks (`bd && bd.components.length > 0`, `availableComponentCount !== null`)
- Hardcoded empty arrays used as display data — none; all data flows from API responses

---

### Human Verification Required

The following items require human verification in a browser (cannot be confirmed programmatically):

#### 1. Safe label visual rendering

**Test:** Visit `/stocks`, look at the "Görünüm" column for any stock with a non-null recommendation.
**Expected:** Shows "Yüksek Öncelikli İzleme" (not "GÜÇLÜ AL"), colored green for positive recommendations. Hover shows tooltip explaining the label.
**Why human:** CSS module class resolution and visual output cannot be verified statically.

#### 2. Score breakdown section visibility

**Test:** Visit `/stocks/THYAO` (or any stock), scroll below the metric cards.
**Expected:** "Skor Dökümü" section appears with labeled progress bars for each scoring component, showing score and percentage contribution.
**Why human:** Section only renders when `bd.components.length > 0`; requires live API data from `/stocks/{symbol}/score-breakdown`.

#### 3. Missing component warning

**Test:** Find a stock where `scoreBreakdown.breakdown.summary.missing_component_count > 0`.
**Expected:** Amber warning box "Eksik veri — ağırlık yeniden dağıtıldı" appears above the progress bars.
**Why human:** Requires live data with a stock that has incomplete scoring components.

#### 4. Volatility warning in stock list

**Test:** If any stock shows `daily_change_pct > 4%`, look at its row in `/stocks`.
**Expected:** Amber ⚠ icon appears next to the component badge in the fundamental score cell.
**Why human:** Depends on market conditions; no guaranteed stock with >4% daily move.

---

### Gaps Summary

No gaps. All automated checks passed:

- Plan 01 (KARAR-01, KARAR-04): `safeLabel()` helper, `SAFE_LABEL_MAP`, `SAFE_LABEL_TOOLTIP`, and `safeLabelTooltip()` are implemented in all 4 required pages. The "Görünüm" table header column is present in stocks list. All tooltip wiring uses `title={safeLabelTooltip(...)}` consistently.

- Plan 02 (KARAR-02, KARAR-03, SKOR-01, SKOR-02, SKOR-03): `breakdownSection` with progress bars is implemented and wired to live `scoreBreakdown` state fetched from `api.getStockScoreBreakdown()`. Component integrity badge (`N/M bileşen mevcut`) appears in both detail and list pages. Volatility alert implemented with 20-day calculation in detail and daily_change_pct proxy in list. All required CSS classes exist in both module files.

Commits `a6076bf`, `5e1bd68` (Plan 01) and `00e8a23`, `a08c526` (Plan 02) verified present in git log.

---

_Verified: 2026-05-12T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
