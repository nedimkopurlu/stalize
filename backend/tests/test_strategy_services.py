"""Strategy lab service tests."""

from app.services.backtest import STRATEGIES, backtest_service
from app.services.risk_guard import risk_guard_service


def test_backtest_metrics_use_conservative_position_sizing():
    trades = [
        {"symbol": "AAA", "exit_date": "2026-01-02", "return_pct": 10.0},
        {"symbol": "BBB", "exit_date": "2026-01-03", "return_pct": -5.0},
        {"symbol": "CCC", "exit_date": "2026-01-04", "return_pct": 8.0},
    ]

    metrics = backtest_service._metrics(trades, {"return_pct": 3.0})

    assert metrics["trades"] == 3
    assert metrics["total_return_pct"] < 13.0
    assert metrics["win_rate_pct"] == 66.7
    assert metrics["excess_return_pct"] is not None


def test_backtest_strategy_catalog_covers_core_modes():
    assert {"trend_quality", "breakout", "mean_reversion", "composite_signal"}.issubset(STRATEGIES)


def test_cash_policy_raises_cash_in_risk_off_market():
    action = risk_guard_service._cash_action(current_cash_pct=5.0, recommended_cash_pct=35.0)

    assert action["status"] == "raise_cash"
    assert "nakit" in action["detail"].lower()


def test_risk_score_increases_for_sector_and_stop_pressure():
    score = risk_guard_service._risk_score(
        positions=[{"at_risk": True}, {"at_risk": False}],
        sectors=[{"status": "over_limit"}],
        invested_pct=95.0,
        market={"label": "risk_off"},
    )

    assert score >= 70
    assert risk_guard_service._risk_level(score) == "high"
