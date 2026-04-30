---
phase: 25
plan: 1
title: Business Logic Correctness — LOGIC-01 through LOGIC-04
status: complete
completed: "2026-04-28"
---

# Phase 25 — Business Logic Correctness: Summary

## What Was Done

### LOGIC-01: Scoring Weight Consistency

`app/services/scoring.py` `_resolve_weights()` — changed from hard-coded `settings.WEIGHT_*` values to deriving weights from `CONTEXTUAL_WEIGHTS` (the same dict used by `get_contextual_score_breakdown()`):

```python
def _resolve_weights(self):
    core_keys = ("fundamental_score", "technical_score", "sentiment_score")
    core = {k: self.CONTEXTUAL_WEIGHTS[k] for k in core_keys}
    total = sum(core.values())
    return {k: v / total for k, v in core.items()}
```

Both `calculate_overall_score()` and the contextual breakdown now use the same relative ratios (0.30/0.25/0.15, normalized). The API's recommendation and breakdown fields no longer contradict each other.

### LOGIC-02: Screener HTTP 400 Validation

`app/api/stocks.py` `screen_stocks()` — added upfront validation for all min/max range pairs before the query executes:

```python
range_pairs = [("pe_ratio_min", pe_ratio_min, "pe_ratio_max", pe_ratio_max), ...]
for min_name, min_val, max_name, max_val in range_pairs:
    if min_val is not None and max_val is not None and min_val > max_val:
        raise HTTPException(status_code=400, detail=f"{min_name} > {max_name}")
```

Covers pe_ratio, pb_ratio, roe, score, market_cap, daily_change pairs.

### LOGIC-03: ATR Volatility in Technical Score

`app/services/technical.py` `calculate_score()` — added ATR-based penalty after the blended score:

```python
# ATR as % of price; >5% ATR penalizes toward neutral by up to -10 points
if atr_pct > 0.05:
    atr_adjustment = -min((atr_pct - 0.05) * 100, 10.0)
blended = signal_score * 0.6 + ema_normalized * 0.4 + atr_adjustment
```

High-volatility stocks (ATR > 5% of price) now receive a lower technical score than low-volatility stocks with identical signals.

### LOGIC-04: Portfolio P&L Partial Flag

`app/api/portfolio_v2.py` `get_positions()` — added `"partial": current_price is None` to every position in the response. Client can now detect incomplete P&L calculation without parsing null fields.

## Files Changed

- `backend/app/services/scoring.py`
- `backend/app/api/stocks.py`
- `backend/app/services/technical.py`
- `backend/app/api/portfolio_v2.py`

## Acceptance Criteria Status

- [x] LOGIC-01: calculate_overall_score ve get_contextual_score_breakdown aynı ağırlık oranlarını kullanıyor
- [x] LOGIC-02: pe_ratio_min > pe_ratio_max gönderildiğinde HTTP 400 dönüyor
- [x] LOGIC-03: ATR volatilite bileşeni teknik skorda aktif; yüksek volatiliteli hisse cezalandırılıyor
- [x] LOGIC-04: Fiyat alınamayan pozisyonlar `partial: true` ile işaretleniyor
