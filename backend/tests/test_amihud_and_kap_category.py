"""
Tests for Amihud illiquidity scoring and KAP category classification.

Tests 1-6: Amihud threshold logic (pure function, no DB)
Tests 7-13: KAP _event_type_to_kap_category mapping (pure function, no DB)
"""
import types
import pytest


# ─── Amihud threshold helper (mirrors the logic in scoring.py) ───

def _amihud_score(ratio: float) -> str:
    """Pure threshold classifier — mirrors scoring.py calculate_amihud_liquidity logic."""
    if ratio < 0.001:
        return "yüksek"
    elif ratio <= 0.01:
        return "orta"
    return "düşük"


def _compute_amihud_ratio(price_rows):
    """
    Compute the mean Amihud ratio from a list of SimpleNamespace rows
    with attributes: close, volume.
    Rows must be in chronological order (oldest first).
    Returns (amihud_ratio, liquidity_score) or (None, None) if insufficient data.
    """
    if len(price_rows) < 5:
        return (None, None)

    amihud_values = []
    for i in range(1, len(price_rows)):
        prev_close = price_rows[i - 1].close
        curr_close = price_rows[i].close
        vol = price_rows[i].volume
        if not prev_close or not vol or vol == 0:
            continue
        ret = abs((curr_close - prev_close) / prev_close)
        amihud_values.append(ret / vol)

    if not amihud_values:
        return (None, None)

    ratio = sum(amihud_values) / len(amihud_values)
    ratio = min(ratio, 1.0)
    score = _amihud_score(ratio)
    return (ratio, score)


def _make_rows(price_vol_pairs):
    """Build list of SimpleNamespace rows from (close, volume) tuples."""
    return [
        types.SimpleNamespace(close=close, volume=vol)
        for close, vol in price_vol_pairs
    ]


# ─── Test 1: Normal input returns (float, str) tuple with valid score ───

def test_amihud_returns_tuple_with_valid_score():
    rows = _make_rows([
        (100, 1000),
        (102, 900),
        (101, 1100),
        (103, 950),
        (100, 1050),
    ])
    result = _compute_amihud_ratio(rows)
    assert isinstance(result, tuple), "Should return a tuple"
    ratio, score = result
    assert isinstance(ratio, float), "ratio should be float"
    assert score in {"yüksek", "orta", "düşük"}, f"Unexpected score: {score}"


# ─── Test 2: All volume=0 → (None, None) ───

def test_amihud_all_zero_volume_returns_none():
    rows = _make_rows([
        (100, 0),
        (102, 0),
        (101, 0),
        (103, 0),
        (100, 0),
    ])
    result = _compute_amihud_ratio(rows)
    assert result == (None, None), "All zero-volume rows should return (None, None)"


# ─── Test 3: Fewer than 5 rows → (None, None) ───

def test_amihud_fewer_than_5_rows_returns_none():
    rows = _make_rows([
        (100, 1000),
        (102, 900),
        (101, 1100),
        (103, 950),
    ])
    result = _compute_amihud_ratio(rows)
    assert result == (None, None), "Fewer than 5 rows should return (None, None)"


# ─── Test 4: ratio = 0.0005 → "yüksek" ───

def test_amihud_score_yuksek():
    assert _amihud_score(0.0005) == "yüksek"


# ─── Test 5: ratio = 0.005 → "orta" ───

def test_amihud_score_orta():
    assert _amihud_score(0.005) == "orta"


# ─── Test 6: ratio = 0.02 → "düşük" ───

def test_amihud_score_dusuk():
    assert _amihud_score(0.02) == "düşük"


# ─── KAP category tests ───

@pytest.fixture(scope="module")
def kap_parser():
    from app.services.kap_parser import KAPParser
    return KAPParser()


# ─── Test 7: dividend → "Temettü" ───

def test_kap_category_dividend(kap_parser):
    assert kap_parser._event_type_to_kap_category("dividend") == "Temettü"


# ─── Test 8: earnings → "Finansal Sonuçlar" ───

def test_kap_category_earnings(kap_parser):
    assert kap_parser._event_type_to_kap_category("earnings") == "Finansal Sonuçlar"


# ─── Test 9: rights_issue → "Sermaye Artırımı" ───

def test_kap_category_rights_issue(kap_parser):
    assert kap_parser._event_type_to_kap_category("rights_issue") == "Sermaye Artırımı"


# ─── Test 10: bonus_issue → "Sermaye Artırımı" ───

def test_kap_category_bonus_issue(kap_parser):
    assert kap_parser._event_type_to_kap_category("bonus_issue") == "Sermaye Artırımı"


# ─── Test 11: share_sale → "İçeriden Öğrenme" ───

def test_kap_category_share_sale(kap_parser):
    assert kap_parser._event_type_to_kap_category("share_sale") == "İçeriden Öğrenme"


# ─── Test 12: other → "Diğer" ───

def test_kap_category_other(kap_parser):
    assert kap_parser._event_type_to_kap_category("other") == "Diğer"


# ─── Test 13: unknown event type → "Diğer" (fallback) ───

def test_kap_category_unknown_fallback(kap_parser):
    assert kap_parser._event_type_to_kap_category("unknown_xyz") == "Diğer"
