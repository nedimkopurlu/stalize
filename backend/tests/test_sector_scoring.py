"""
Test sector classification and scoring pure functions.
No DB dependencies — all functions are pure.
"""
import pytest
from app.services.scoring import (
    classify_sector_category,
    calculate_bank_score,
    calculate_gyo_score,
    calculate_holding_nav_discount,
    BANK_TICKERS,
    HOLDING_TICKERS,
)


# ── classify_sector_category ──


def test_classify_bank_tickers_by_symbol():
    """Known bank tickers must return 'banka' regardless of sector string."""
    for ticker in ["AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB", "VAKBN", "TSKB", "QNBFB", "ALBRK"]:
        assert classify_sector_category(ticker, None) == "banka", f"Expected 'banka' for {ticker}"


def test_classify_holding_tickers_by_symbol():
    """Known holding tickers must return 'holding'."""
    for ticker in ["SAHOL", "KCHOL", "SISE", "TKFEN", "DOHOL"]:
        assert classify_sector_category(ticker, None) == "holding", f"Expected 'holding' for {ticker}"


def test_classify_gyo_by_real_estate_sector():
    """A non-bank, non-holding symbol with 'Real Estate' sector returns 'gyo'."""
    assert classify_sector_category("ISGYO", "Real Estate") == "gyo"
    assert classify_sector_category("EKGYO", "Real Estate Investment Trust") == "gyo"


def test_classify_real_estate_case_insensitive():
    """real estate sector string is matched case-insensitively."""
    assert classify_sector_category("MPARK", "real estate") == "gyo"
    assert classify_sector_category("VKGYO", "REAL ESTATE") == "gyo"


def test_classify_unknown_stock_returns_none():
    """Stocks not in any special set with a non-real-estate sector return None."""
    assert classify_sector_category("THYAO", "Industrials") is None
    assert classify_sector_category("EREGL", "Basic Materials") is None


def test_classify_none_sector_non_special_returns_none():
    """Non-special stock with no sector returns None."""
    assert classify_sector_category("BIMAS", None) is None


# ── calculate_bank_score ──


def test_bank_score_low_pb_high_roe():
    """pb < 0.8 → ptbv=100; roe > 0.20 → roe=100; result = 0.6*100 + 0.4*100 = 100.0"""
    assert calculate_bank_score(0.7, 0.22) == pytest.approx(100.0)


def test_bank_score_medium_pb_medium_roe():
    """pb in [0.8, 1.2) → ptbv=75; roe in (0.15, 0.20] → roe=75; result = 75.0"""
    assert calculate_bank_score(1.0, 0.16) == pytest.approx(75.0)


def test_bank_score_high_pb_low_roe():
    """pb in [1.2, 2.0) → ptbv=50; roe in (0.08, 0.15] → roe=50; result = 50.0"""
    assert calculate_bank_score(1.8, 0.10) == pytest.approx(50.0)


def test_bank_score_none_pb_none_roe():
    """Both None → each tier returns 50.0; result = 0.6*50 + 0.4*50 = 50.0"""
    assert calculate_bank_score(None, None) == pytest.approx(50.0)


def test_bank_score_very_high_pb():
    """pb >= 2.0 → ptbv=25; roe None → roe_score=50; result = 0.6*25 + 0.4*50 = 35.0"""
    assert calculate_bank_score(2.5, None) == pytest.approx(35.0)


def test_bank_score_low_roe():
    """roe <= 0.08 → roe_score=25; pb None → ptbv=50; result = 0.6*50 + 0.4*25 = 40.0"""
    assert calculate_bank_score(None, 0.05) == pytest.approx(40.0)


# ── calculate_gyo_score ──


def test_gyo_score_low_pb():
    """pb < 0.8 → 100.0"""
    assert calculate_gyo_score(0.7) == pytest.approx(100.0)


def test_gyo_score_medium_pb():
    """pb in [0.8, 1.2) → 75.0"""
    assert calculate_gyo_score(1.0) == pytest.approx(75.0)


def test_gyo_score_higher_pb():
    """pb in [1.2, 2.0) → 50.0"""
    assert calculate_gyo_score(1.5) == pytest.approx(50.0)


def test_gyo_score_very_high_pb():
    """pb >= 2.0 → 25.0"""
    assert calculate_gyo_score(3.0) == pytest.approx(25.0)


def test_gyo_score_none_returns_default():
    """pb is None → 50.0"""
    assert calculate_gyo_score(None) == pytest.approx(50.0)


# ── calculate_holding_nav_discount ──


def test_holding_nav_discount_positive():
    """holding_market_cap < sub_sum → positive discount (80 vs 100) = 0.20"""
    result = calculate_holding_nav_discount(80.0, 100.0)
    assert result == pytest.approx(0.20)


def test_holding_nav_discount_premium():
    """holding_market_cap > sub_sum → negative value (premium) (110 vs 100) = -0.10"""
    result = calculate_holding_nav_discount(110.0, 100.0)
    assert result == pytest.approx(-0.10)


def test_holding_nav_discount_none_market_cap():
    """If holding_market_cap is None → return None"""
    assert calculate_holding_nav_discount(None, 100.0) is None


def test_holding_nav_discount_zero_sub_sum():
    """If sub_sum is 0 → return None (avoid division by zero)"""
    assert calculate_holding_nav_discount(80.0, 0) is None


def test_holding_nav_discount_none_sub_sum():
    """If sub_sum is None → return None"""
    assert calculate_holding_nav_discount(80.0, None) is None


# ── BANK_TICKERS / HOLDING_TICKERS sets ──


def test_bank_tickers_set_contents():
    """BANK_TICKERS must include the nine expected bank symbols."""
    expected = {"AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB", "VAKBN", "TSKB", "QNBFB", "ALBRK"}
    assert expected.issubset(BANK_TICKERS)


def test_holding_tickers_set_contents():
    """HOLDING_TICKERS must include the five expected holding symbols."""
    expected = {"SAHOL", "KCHOL", "SISE", "TKFEN", "DOHOL"}
    assert expected.issubset(HOLDING_TICKERS)
