"""Investment decision engine tests."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.investment_decision import DecisionInput, DecisionPolicy, investment_decision_engine


def _stock(**overrides):
    base = {
        "id": 1,
        "symbol": "ASELS",
        "name": "Aselsan",
        "current_price": 100.0,
        "daily_change_pct": 1.2,
        "volume": 3_000_000.0,
        "overall_score": 86.0,
        "technical_score": 76.0,
        "fundamental_score": 72.0,
        "sentiment_score": 60.0,
        "recommendation": "GÜÇLÜ AL",
        "is_bist30": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _prices(close_start=80.0, close_step=0.4, days=90):
    rows = []
    start = date.today() - timedelta(days=days)
    for index in range(days):
        close = close_start + (index * close_step)
        rows.append(
            SimpleNamespace(
                stock_id=1,
                date=start + timedelta(days=index),
                close=close,
                high=close + 2.0,
                low=close - 2.0,
                sma_50=close - 4.0,
                sma_200=close - 12.0,
                atr_14=3.0,
            )
        )
    return rows


def test_strong_buy_decision_includes_risk_plan():
    decision = investment_decision_engine.build_decision(
        DecisionInput(stock=_stock(), prices=_prices(), portfolio_value=100_000, risk_per_trade_pct=1.0)
    )

    assert decision["action"] == "strong_buy"
    assert decision["stop_loss"] == pytest.approx(94.0)
    assert decision["target_price"] > decision["current_price"]
    assert decision["risk_reward"] >= 1.8
    assert decision["position_size"]["shares"] > 0
    assert decision["position_size"]["estimated_exposure_pct"] <= decision["position_size"]["max_exposure_pct"]
    assert "invalidation" in decision


def test_weak_trend_reduces_action_even_with_average_score():
    prices = _prices(close_start=120.0, close_step=-0.45, days=90)
    latest = prices[-1]
    latest.sma_50 = latest.close + 5.0
    latest.sma_200 = latest.close + 12.0

    decision = investment_decision_engine.build_decision(
        DecisionInput(
            stock=_stock(
                current_price=latest.close,
                overall_score=42.0,
                technical_score=38.0,
                recommendation="SAT",
                is_bist30=False,
            ),
            prices=prices,
        )
    )

    assert decision["action"] in {"reduce", "exit"}
    assert decision["signals"]["trend"] in {"bearish", "weak"}


def test_position_size_respects_risk_budget_and_high_risk_cap():
    volatile_prices = _prices(close_start=70.0, close_step=0.0, days=90)
    for index, row in enumerate(volatile_prices):
        row.close = 70.0 + ((-1) ** index * 8.0)
        row.high = row.close + 5.0
        row.low = row.close - 5.0
    volatile_prices[-1].atr_14 = 10.0

    decision = investment_decision_engine.build_decision(
        DecisionInput(
            stock=_stock(current_price=80.0, daily_change_pct=6.5, is_bist30=False),
            prices=volatile_prices,
            portfolio_value=50_000,
            risk_per_trade_pct=1.0,
        )
    )

    assert decision["risk_level"] == "high"
    assert decision["position_size"]["max_exposure_pct"] == 5.0
    assert decision["position_size"]["estimated_exposure_pct"] <= 5.0


def test_enforced_policy_downgrades_buy_when_confidence_too_low():
    decision = investment_decision_engine.build_decision(
        DecisionInput(
            stock=_stock(),
            prices=_prices(),
            policy=DecisionPolicy(mode="enforced", min_buy_confidence=95, min_buy_risk_reward=1.5),
        )
    )

    assert decision["action"] == "watch"
    assert "confidence<95" in decision["policy"]["notes"]


def test_observation_policy_does_not_change_action():
    decision = investment_decision_engine.build_decision(
        DecisionInput(
            stock=_stock(),
            prices=_prices(),
            policy=DecisionPolicy(mode="observation", min_buy_confidence=100, min_buy_risk_reward=9.0),
        )
    )

    assert decision["action"] == "strong_buy"
    assert decision["policy"]["notes"] == []


@pytest.mark.asyncio
async def test_stock_decision_endpoint_shape():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/stocks/ASELS/decision?portfolio_value=100000&risk_per_trade_pct=1")

    assert resp.status_code in {200, 404, 503}
    if resp.status_code == 200:
        payload = resp.json()
        assert payload["symbol"] == "ASELS"
        assert payload["action"] in {"strong_buy", "buy", "watch", "hold", "reduce", "exit"}
        assert "position_size" in payload
        assert "risk_reward" in payload
