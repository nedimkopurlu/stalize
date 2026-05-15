"""Unit tests for calculate_round_trip_cost — BACK-01 slippage/commission model."""
import pytest

from app.services.signal_tracking import calculate_round_trip_cost


class TestCalculateRoundTripCost:
    """Tests for the module-level calculate_round_trip_cost function."""

    def test_bist30_true_no_liquidity_score(self):
        """BIST30=True → 10bps slippage → 2 × (0.001 + 0.001) = 0.004"""
        result = calculate_round_trip_cost(is_bist30=True, liquidity_score=None)
        assert result == pytest.approx(0.004, rel=1e-6), f"Expected 0.004, got {result}"

    def test_bist30_false_orta(self):
        """liquidity_score='orta' → 20bps slippage → 2 × (0.002 + 0.001) = 0.006"""
        result = calculate_round_trip_cost(is_bist30=False, liquidity_score="orta")
        assert result == pytest.approx(0.006, rel=1e-6), f"Expected 0.006, got {result}"

    def test_bist30_false_dusuk(self):
        """liquidity_score='düşük' → 40bps slippage → 2 × (0.004 + 0.001) = 0.010"""
        result = calculate_round_trip_cost(is_bist30=False, liquidity_score="düşük")
        assert result == pytest.approx(0.010, rel=1e-6), f"Expected 0.010, got {result}"

    def test_bist30_false_yuksek(self):
        """liquidity_score='yüksek' → same as BIST30, 10bps → 0.004"""
        result = calculate_round_trip_cost(is_bist30=False, liquidity_score="yüksek")
        assert result == pytest.approx(0.004, rel=1e-6), f"Expected 0.004, got {result}"

    def test_bist30_false_none_defaults_to_orta(self):
        """None liquidity_score → defaults to 'orta' → 0.006"""
        result = calculate_round_trip_cost(is_bist30=False, liquidity_score=None)
        assert result == pytest.approx(0.006, rel=1e-6), f"Expected 0.006, got {result}"

    def test_bist30_true_overrides_dusuk(self):
        """is_bist30=True takes priority even when liquidity_score='düşük' → 0.004"""
        result = calculate_round_trip_cost(is_bist30=True, liquidity_score="düşük")
        assert result == pytest.approx(0.004, rel=1e-6), f"Expected 0.004, got {result}"
