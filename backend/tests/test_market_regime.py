"""
Tests for MarketRegimeEngine._classify_regime — pure logic, no I/O.

All 4 regime types and priority rules are covered (6 tests).
"""
import pytest

from app.services.market_regime import MarketRegimeEngine

engine = MarketRegimeEngine()


def test_classify_boga():
    """close > EMA200, ADX > 25, atr_ratio < 0.02 → Boğa"""
    result = engine._classify_regime(adx=30, ema200=1.20, usd_close=1.25, atr=0.015)
    assert result == "Boğa", f"Expected 'Boğa', got '{result}'"


def test_classify_ayi():
    """close < EMA200, ADX > 25, atr_ratio < 0.02 → Ayı"""
    result = engine._classify_regime(adx=28, ema200=1.30, usd_close=1.25, atr=0.015)
    assert result == "Ayı", f"Expected 'Ayı', got '{result}'"


def test_classify_yatay():
    """ADX < 25 and atr_ratio < 0.02 → Yatay"""
    result = engine._classify_regime(adx=20, ema200=1.20, usd_close=1.25, atr=0.015)
    assert result == "Yatay", f"Expected 'Yatay', got '{result}'"


def test_classify_volatil_overrides_boga():
    """atr_ratio >= 0.02 takes priority over Bull conditions → Volatil"""
    # atr_ratio = 0.030 / 1.25 = 0.024 >= 0.02
    result = engine._classify_regime(adx=30, ema200=1.20, usd_close=1.25, atr=0.030)
    assert result == "Volatil", f"Expected 'Volatil', got '{result}'"


def test_classify_volatil_overrides_ayi():
    """atr_ratio >= 0.02 takes priority over Bear conditions → Volatil"""
    # atr_ratio = 0.026 / 1.25 = 0.0208 >= 0.02
    result = engine._classify_regime(adx=28, ema200=1.30, usd_close=1.25, atr=0.026)
    assert result == "Volatil", f"Expected 'Volatil', got '{result}'"


def test_classify_volatil_with_weak_adx():
    """atr_ratio >= 0.02 takes priority even with weak ADX → Volatil"""
    # atr_ratio = 0.030 / 1.25 = 0.024 >= 0.02
    result = engine._classify_regime(adx=15, ema200=1.20, usd_close=1.25, atr=0.030)
    assert result == "Volatil", f"Expected 'Volatil', got '{result}'"
