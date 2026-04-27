---
phase: 07-sinyal-kalitesi
verified: 2026-04-20T10:30:00Z
status: human_needed
score: 5/5 must-haves verified
re_verification: false
human_verification:
  - test: "Open /stocks table and inspect the Hacim column"
    expected: "Values render as 'N.Nx' (e.g. '1.2x', '2.4x'). Hovering any Hacim cell shows a native tooltip 'Ham hacim: [formatted volume]'. A stock whose volume ≈ 20-day average shows approximately '1.0x'. No raw numbers like '1,234,567' appear."
    why_human: "toFixed(1) rendering and native title= tooltip require a running browser; automated checks confirm the code path exists but cannot verify pixel-level rendering."
  - test: "Click any stock → Teknik Analiz tab"
    expected: "Two cards appear below Destek/Direnç: 'Stop-Loss (2×ATR)' with a red border and a ₺ price, 'Hedef Fiyat' with a green border and a ₺ price. Both show real numbers — never '—' or empty for a stock with sufficient price data. Stop-Loss value is numerically less than current price, which is less than Hedef Fiyat."
    why_human: "Card visibility and color-coded borders require a running frontend. Automated checks confirm the JSX block and formatPrice calls exist but cannot render CSS variables (--red-border, --green-border)."
  - test: "Scan Aktif Sinyaller on several stocks"
    expected: "Stocks with a clear recent RSI-price divergence show a 'RSI Bullish Divergence' or 'RSI Bearish Divergence' row in the signal list. Stocks without divergence do NOT show such a row (no false-positive noise)."
    why_human: "Divergence accuracy depends on live price/RSI data patterns. Automated tests confirm the algorithm works on synthetic data; real-market false-positive rate cannot be verified without rendering actual stock data."
---

# Phase 07: Sinyal Kalitesi — Verification Report

**Phase Goal:** Every actionable signal shown to the user is grounded in price-relative risk levels and normalized volume context — divergence between RSI and price is surfaced automatically rather than requiring manual inspection.

**Verified:** 2026-04-20T10:30:00Z
**Status:** human_needed (all automated checks pass; 3 visual/behavioral items require human)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | `GET /api/stocks/{symbol}/technical` response contains `stop_loss` and `target_price` as finite floats; `stop_loss < last_close < target_price` | VERIFIED | `analyze_stock()` lines 493-505 in `technical.py`; `test_technical_endpoint_includes_stop_loss_and_target` PASSED |
| 2 | `stop_loss == round(last_close - 2 * atr_14, 2)` and `target_price` uses nearest swing high above last_close (fallback: `last_close * 1.05`) | VERIFIED | `_compute_stop_loss` and `_compute_target_price` in `technical.py` lines 339-361; formula manually validated and confirmed by 3 passing unit tests |
| 3 | Every dict in `GET /api/stocks` `stocks[]` contains `volume_ratio`; equals 1.0 when current == avg_20d; None when avg missing or zero | VERIFIED | `compute_volume_ratio` helper at `technical.py` line 548; wired into `stocks.py` line 97; `test_volume_ratio_*` tests ALL PASSED; `compute_volume_ratio(1_000_000, 1_000_000) == 1.0` manually confirmed |
| 4 | When RSI-price divergence is present, a divergence signal appears in `signals[]`; absent when no divergence | VERIFIED | `_detect_rsi_divergence` at `technical.py` lines 365-422; wired into `detect_signals` at line 286-288; bullish/bearish/no-divergence tests ALL PASSED |
| 5 | Frontend renders stop_loss + target_price (Technical tab), volume_ratio with tooltip (stocks table), divergence signals via existing loop | VERIFIED (automated portion) | JSX block at `[symbol]/page.tsx` lines 229-248; Hacim cell at `stocks/page.tsx` lines 194-195; TypeScript: `npx tsc --noEmit` → 0 errors |

**Score:** 5/5 truths verified (automated); 3 truths require human visual confirmation

### Required Artifacts

| Artifact | Provides | Status | Details |
|----------|---------|--------|---------|
| `backend/tests/test_signal_quality.py` | 11 TDD tests for SGNL-01/02/03 | VERIFIED | 114 lines; 11 tests collected; all 11 PASSED; 0 `pytest.fail` guards remain (all GREEN) |
| `backend/app/services/technical.py` | `_compute_stop_loss`, `_compute_target_price`, `_detect_rsi_divergence`, `compute_volume_ratio` | VERIFIED | All 4 helpers present; wired into `analyze_stock` (lines 493-505) and `detect_signals` (lines 286-288); `compute_volume_ratio` module-level after singleton |
| `backend/app/api/stocks.py` | `volume_ratio` field + batched 20-day avg volume query | VERIFIED | `compute_volume_ratio` imported (line 10), called (line 97); `row_number()` window subquery present (lines 60-80); no N+1 query |
| `frontend/src/lib/api.ts` | `StockSummary.volume_ratio`, `TechnicalResult.stop_loss`, `TechnicalResult.target_price` | VERIFIED | Lines 44, 130-131 confirmed; TypeScript 0 errors |
| `frontend/src/app/stocks/[symbol]/page.tsx` | Stop-Loss + Hedef Fiyat cards in Technical tab | VERIFIED (code) | Lines 229-248; guard `technical.stop_loss != null`; `formatPrice()` calls; existing signals loop renders divergence |
| `frontend/src/app/stocks/page.tsx` | Volume ratio cell with tooltip | VERIFIED (code) | Line 194-195; `toFixed(1)x` render; `title` tooltip with raw volume; `—` for null |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `technical.py::_detect_rsi_divergence` | `detect_signals signals[]` | `div = self._detect_rsi_divergence(df); signals.append(div)` | WIRED | `technical.py` lines 286-288; divergence signals flow through `analyze_stock` return via `signals["signals"]` (line 501) |
| `technical.py::analyze_stock` | `/api/stocks/{symbol}/technical` response | dict keys `stop_loss`, `target_price` | WIRED | `technical.py` lines 504-505; endpoint returns engine result verbatim (no route-level filtering confirmed in `stocks.py`) |
| `stocks.py::get_stocks` | `PriceHistory` 20-day avg → `compute_volume_ratio` | `row_number()` window subquery + `compute_volume_ratio(s.volume, avg_volumes.get(s.id))` | WIRED | `stocks.py` lines 52-97; batched query runs unconditionally when `stock_ids` is non-empty |
| `frontend/stocks/page.tsx Hacim cell` | `StockSummary.volume_ratio` | `stock.volume_ratio.toFixed(1)x` ternary + `title` tooltip | WIRED | `stocks/page.tsx` lines 194-195; null guard + render on same ternary line |
| `frontend/[symbol]/page.tsx Technical tab` | `TechnicalResult.stop_loss / target_price` | `formatPrice(technical.stop_loss)` inside `srCard` blocks | WIRED | `[symbol]/page.tsx` lines 232-247; null guard (`!= null`) + formatPrice call present |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| SGNL-01 | 07-02, 07-04 | Stock detail page shows ATR-based stop-loss (close − 2×ATR) and first-resistance target price; both in `GET /api/stocks/{symbol}/technical` and rendered in UI | SATISFIED | `_compute_stop_loss` + `_compute_target_price` implemented; wired into `analyze_stock`; Stop-Loss + Hedef Fiyat cards in Technical tab; 4 tests GREEN |
| SGNL-02 | 07-03, 07-04 | Volume column shows normalized ratio (e.g. "2.4x") vs 20-day average; hover reveals raw volume; stock with equal volume shows "1.0x" | SATISFIED | `compute_volume_ratio` helper; batched SQL avg query; `volume_ratio` in `/api/stocks` response; frontend `toFixed(1)x` + `title` tooltip; 4 tests GREEN |
| SGNL-03 | 07-02, 07-04 | RSI-price divergence signals appear in `top_signals`/`signals[]`; no divergence → no signal | SATISFIED | `_detect_rsi_divergence` implemented; wired additively into `detect_signals`; existing signals loop in frontend renders divergence signals automatically; 3 tests GREEN |

No orphaned requirements — all three SGNL-0x IDs are claimed by at least one plan and verified as implemented.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/app/stocks/[symbol]/page.tsx` | 259 | `{/* ── Causal Tab (placeholder) ───────────────── */}` with placeholder content | Info | Pre-existing from Phase 05; tracked by UICL-01 (Phase 08 requirement). Not introduced by Phase 07 commits. Does not affect SGNL-01/02/03 goal. |

No blocker or warning anti-patterns in Phase 07 deliverables. The causal tab placeholder predates this phase and is out-of-scope.

### Test Suite Results

```
backend/tests/test_signal_quality.py — 11 passed, 0 failed
Full backend suite — 46 passed, 13 xpassed, 0 failed
npx tsc --noEmit (frontend) — 0 errors
```

All 11 signal quality tests turn GREEN. No regressions in pre-existing tests.

### Human Verification Required

#### 1. Volume Ratio Table Rendering

**Test:** Start frontend dev server; open http://localhost:3000/stocks
**Expected:** Hacim column shows values like "1.2x", "0.8x", "2.4x" — NOT raw numbers. Hovering any cell shows a native tooltip "Ham hacim: [formatted volume]". A stock whose recent volume ≈ 20-day average shows close to "1.0x".
**Why human:** The `toFixed(1)x` ternary and `title=` attribute exist in the code, but pixel-level rendering and native browser tooltip behavior require a running browser to confirm.

#### 2. Stop-Loss and Hedef Fiyat Cards on Technical Tab

**Test:** Click any stock with sufficient price data → click "Teknik Analiz" tab
**Expected:** Two cards appear below Destek/Direnç: "Stop-Loss (2×ATR)" with red border and a ₺ price; "Hedef Fiyat" with green border and a ₺ price. Neither shows placeholder text or "—". Stop-Loss < current price < Hedef Fiyat holds numerically.
**Why human:** CSS variables (`--red-border`, `--green-border`) and conditional rendering require a running browser. Automated checks confirm the JSX block and `formatPrice()` calls exist, not visual output.

#### 3. Divergence Signals in Aktif Sinyaller

**Test:** Browse several stocks and inspect the Aktif Sinyaller list
**Expected:** Stocks with clear RSI-price divergence patterns show "RSI Bullish Divergence" or "RSI Bearish Divergence" entries. Stocks without divergence do NOT show these rows. False-positive noise is absent.
**Why human:** Real-market divergence quality (signal-to-noise ratio on BIST 100 data) cannot be verified from synthetic test data. The algorithm passes all contract tests but real-market edge cases require visual inspection.

### Gaps Summary

No gaps — all must-have truths verified, all artifacts are substantive and wired, all key links confirmed, all three requirements satisfied end-to-end. The three human verification items above are quality/UX confirmations, not correctness gaps.

---

_Verified: 2026-04-20T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
