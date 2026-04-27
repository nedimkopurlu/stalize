# 16-01 SUMMARY: EMA 50/200 Trend Score Component

**Completed:** 2026-04-26
**Status:** ✅ GREEN — tüm testler geçti

## Uygulanan Mantık

### `_compute_ema_trend_score(df)` — 0-50 arası float

```python
score = 0.0
if close > ema_200:
    score += 20.0                                      # taban
    if ema_50 > ema_200:
        score += 15.0                                  # golden cross zonu
    momentum_ratio = (close - ema_200) / ema_200
    momentum_ratio = max(0.0, min(0.10, momentum_ratio))
    score += momentum_ratio * 150.0                    # 0-15 puan
```

Sınır değerler:
| Durum | Puan |
|---|---|
| NaN (< 200 bar) | 0.0 |
| close < ema_200 | 0.0 |
| close > ema_200, ema_50 ≤ ema_200, 0 momentum | ~20.0 |
| close > ema_200, ema_50 > ema_200, 0 momentum | 35.0 |
| close ≥ ema_200 × 1.10, ema_50 > ema_200 | 50.0 |

### `calculate_score()` Blend Formülü

```python
signal_score = 50 + (net_bullish_bearish_ratio * 50)   # 0-100
ema_normalized = _compute_ema_trend_score(df) * 2.0     # 0-100
blended = signal_score * 0.6 + ema_normalized * 0.4
score = clamp(blended, 0.0, 100.0)
```

### `analyze_stock()` Dönüş Değişikliği

`indicators["ema_trend_score"]` anahtarı eklendi (float 0-50).

## Test Sonuçları

**17 passed, 0 failed** (SGNL-01/02/03 regression yok)

Yeni EMA testleri:
- `test_ema_trend_score_below_ema200` ✅
- `test_ema_trend_score_above_ema200_no_golden_cross` ✅
- `test_ema_trend_score_golden_cross_no_momentum` ✅
- `test_ema_trend_score_max_momentum` ✅
- `test_ema_trend_score_nan_when_insufficient_data` ✅
- `test_calculate_score_stays_in_range` ✅

## Minimum Bar Sayısı

`calculate_indicators()` zaten `ema_200` hesaplıyordu (`df < 50` guard var).
EMA-200 için en az 200 bar gerekir ancak `ta.trend.ema_indicator` NaN döndürdüğünde
`_compute_ema_trend_score` güvenli şekilde `0.0` döner — minimum bar guard değiştirilmedi.
