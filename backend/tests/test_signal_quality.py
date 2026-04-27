"""SGNL-01 / SGNL-02 / SGNL-03 / EMA Trend Score — RED-then-GREEN TDD tests."""
import pytest
import pandas as pd
import numpy as np
from httpx import AsyncClient, ASGITransport
from app.services.technical import technical_engine
from app.main import app


def _synthetic_df(close_series, high_series=None, low_series=None, volume_series=None, rsi_series=None):
    """Build a minimal DataFrame shaped like TechnicalAnalysisEngine expects."""
    n = len(close_series)
    return pd.DataFrame({
        "close": close_series,
        "high": high_series if high_series is not None else [c + 1 for c in close_series],
        "low": low_series if low_series is not None else [c - 1 for c in close_series],
        "volume": volume_series if volume_series is not None else [1_000_000] * n,
        "rsi_14": rsi_series if rsi_series is not None else [50.0] * n,
        "atr_14": [5.0] * n,
    })


# ── SGNL-01 ──────────────────────────────────────────────────────────────────

def test_atr_stop_loss_formula():
    """SGNL-01: stop_loss = last_close - (2 * atr_14). Given last_close=100, atr_14=5 → 90.0."""
    df = _synthetic_df([98, 99, 100])
    assert technical_engine._compute_stop_loss(df) == pytest.approx(90.0)


def test_target_price_uses_swing_high():
    """SGNL-01: target_price uses nearest swing high above last_close within last 20 bars."""
    closes = [100] * 19 + [100]
    highs  = [101] * 18 + [108.5, 101]
    df = _synthetic_df(closes, high_series=highs)
    assert technical_engine._compute_target_price(df) == pytest.approx(108.5)


def test_target_price_fallback_when_no_resistance():
    """SGNL-01: when no bar in last 20 has high > last_close, fallback to last_close * 1.05."""
    closes = [100] * 20
    highs  = [99] * 20  # no high above last_close
    df = _synthetic_df(closes, high_series=highs)
    assert technical_engine._compute_target_price(df) == pytest.approx(105.0)


@pytest.mark.asyncio
async def test_technical_endpoint_includes_stop_loss_and_target():
    """SGNL-01: analyze_stock() result must include stop_loss and target_price keys."""
    # Expect real-seeded fixture stock; conftest provides one
    result = await technical_engine.analyze_stock("ASELS")
    assert result is not None
    assert "stop_loss" in result and isinstance(result["stop_loss"], (int, float))
    assert "target_price" in result and isinstance(result["target_price"], (int, float))
    assert result["stop_loss"] < result["indicators"].get("last_close", result["stop_loss"] + 1) < result["target_price"]


# ── SGNL-02 ──────────────────────────────────────────────────────────────────

def test_volume_ratio_one_when_equal_to_avg():
    """SGNL-02: volume_ratio = 1.0 when current equals avg_20d."""
    from app.services.technical import compute_volume_ratio
    assert compute_volume_ratio(current=1_000_000, avg_20d=1_000_000) == pytest.approx(1.0)


def test_volume_ratio_multiplier():
    """SGNL-02: volume_ratio correctly computes multiplier (e.g. 2_400_000 / 1_000_000 = 2.4)."""
    from app.services.technical import compute_volume_ratio
    assert compute_volume_ratio(current=2_400_000, avg_20d=1_000_000) == pytest.approx(2.4)


def test_volume_ratio_none_when_avg_missing():
    """SGNL-02: volume_ratio returns None when avg_20d is None or 0."""
    from app.services.technical import compute_volume_ratio
    assert compute_volume_ratio(current=1_000_000, avg_20d=None) is None
    assert compute_volume_ratio(current=1_000_000, avg_20d=0) is None


@pytest.mark.asyncio
async def test_stocks_list_includes_volume_ratio_key():
    """SGNL-02: every dict in GET /api/stocks response stocks[] must have volume_ratio key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/stocks?limit=5")
    assert resp.status_code == 200
    for s in resp.json()["stocks"]:
        assert "volume_ratio" in s


# ── SGNL-03 ──────────────────────────────────────────────────────────────────

def test_bullish_divergence_detected():
    """SGNL-03: price makes lower low but RSI makes higher low → bullish divergence detected."""
    closes = [100, 98, 96, 94, 92, 94, 93, 91, 90, 89]  # lower lows
    rsi    = [ 40, 35, 30, 28, 26, 32, 31, 33, 35, 38]  # higher lows
    df = _synthetic_df(closes, rsi_series=rsi)
    sig = technical_engine._detect_rsi_divergence(df)
    assert sig == {"type": "divergence", "name": "RSI Bullish Divergence", "direction": "bullish", "strength": 0.6}


def test_bearish_divergence_detected():
    """SGNL-03: price makes higher high but RSI makes lower high → bearish divergence detected."""
    closes = [90, 92, 94, 96, 98, 97, 99, 101, 103, 105]  # higher highs
    rsi    = [60, 65, 70, 75, 78, 72, 70, 68, 66, 64]     # lower highs
    df = _synthetic_df(closes, rsi_series=rsi)
    sig = technical_engine._detect_rsi_divergence(df)
    assert sig == {"type": "divergence", "name": "RSI Bearish Divergence", "direction": "bearish", "strength": 0.6}


def test_no_divergence_when_aligned():
    """SGNL-03: price and RSI both make higher highs → _detect_rsi_divergence returns None."""
    closes = [90, 92, 94, 96, 98, 100, 102, 104]
    rsi    = [55, 58, 61, 64, 67, 70, 73, 76]
    df = _synthetic_df(closes, rsi_series=rsi)
    assert technical_engine._detect_rsi_divergence(df) is None


# ── EMA TREND SCORE (16-01) ──────────────────────────────────────────────────

def _ema_df(close: float, ema_50: float, ema_200: float) -> pd.DataFrame:
    """Minimal DataFrame with ema_50 and ema_200 pre-populated."""
    n = 5
    df = pd.DataFrame({
        "close":   [close] * n,
        "high":    [close + 1] * n,
        "low":     [close - 1] * n,
        "volume":  [1_000_000] * n,
        "rsi_14":  [50.0] * n,
        "atr_14":  [5.0] * n,
        "ema_50":  [ema_50] * n,
        "ema_200": [ema_200] * n,
    })
    return df


def test_ema_trend_score_below_ema200():
    """16-01: price < ema_200 → EMA component = 0.0."""
    df = _ema_df(close=95.0, ema_50=90.0, ema_200=100.0)
    score = technical_engine._compute_ema_trend_score(df)
    assert score == pytest.approx(0.0)


def test_ema_trend_score_above_ema200_no_golden_cross():
    """16-01: price just above ema_200, ema_50 <= ema_200 → base = 20.0 + tiny momentum.
    With close=100.001 and ema_50<=ema_200, score = 20.0 + momentum (≈0) = ~20.0."""
    df = _ema_df(close=100.001, ema_50=98.0, ema_200=100.0)
    score = technical_engine._compute_ema_trend_score(df)
    assert score == pytest.approx(20.0, abs=0.2)  # tiny momentum bonus, no golden cross


def test_ema_trend_score_golden_cross_no_momentum():
    """16-01: price = ema_200 level exactly but ema_50 > ema_200 → base(20) + golden(15) = 35.0, momentum=0."""
    # close slightly above ema_200 so >ema_200 passes, but ratio=(close-ema_200)/ema_200=0 → 0 momentum bonus
    df = _ema_df(close=100.001, ema_50=102.0, ema_200=100.0)
    score = technical_engine._compute_ema_trend_score(df)
    assert score == pytest.approx(35.0, abs=0.2)  # allow tiny float noise


def test_ema_trend_score_max_momentum():
    """16-01: price >= 110% of ema_200 and ema_50 > ema_200 → max score = 50.0."""
    df = _ema_df(close=115.0, ema_50=105.0, ema_200=100.0)
    score = technical_engine._compute_ema_trend_score(df)
    assert score == pytest.approx(50.0)


def test_ema_trend_score_nan_when_insufficient_data():
    """16-01: ema_200 is NaN (< 200 bars) → EMA component = 0.0."""
    n = 5
    df = pd.DataFrame({
        "close":   [100.0] * n,
        "high":    [101.0] * n,
        "low":     [99.0] * n,
        "volume":  [1_000_000] * n,
        "rsi_14":  [50.0] * n,
        "atr_14":  [5.0] * n,
        "ema_50":  [float('nan')] * n,
        "ema_200": [float('nan')] * n,
    })
    score = technical_engine._compute_ema_trend_score(df)
    assert score == pytest.approx(0.0)


def test_calculate_score_stays_in_range():
    """16-01: blended calculate_score() result must be in [0.0, 100.0] for all EMA conditions."""
    for close, e50, e200 in [
        (50.0, 40.0, 100.0),   # below ema200
        (105.0, 98.0, 100.0),  # above ema200, no golden cross
        (115.0, 105.0, 100.0), # max momentum
    ]:
        df = _ema_df(close=close, ema_50=e50, ema_200=e200)
        # signals dict with a minimal bullish signal so calculate_score doesn't short-circuit
        signals = {"signals": [{"type": "test", "name": "test", "direction": "bullish", "strength": 1.0}]}
        score, rec = technical_engine.calculate_score(df, signals)
        assert 0.0 <= score <= 100.0, f"Score out of range: {score} (close={close}, e50={e50}, e200={e200})"
