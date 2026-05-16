"""Signal tracking persistence and outcome tests."""
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import DateTime, inspect as sa_inspect

from app.main import app
from app.models.signal import SignalDecisionSnapshot
from app.services.signal_tracking import SignalTrackingService


def test_signal_snapshot_model_timezone_columns():
    mapper = sa_inspect(SignalDecisionSnapshot)

    assert isinstance(mapper.columns["generated_at"].type, DateTime)
    assert mapper.columns["generated_at"].type.timezone is True
    assert isinstance(mapper.columns["evaluated_at"].type, DateTime)
    assert mapper.columns["evaluated_at"].type.timezone is True


@pytest.mark.parametrize(
    "action,actual_return,excess_return,expected",
    [
        ("buy", 5.0, 2.0, "success"),
        ("strong_buy", -3.5, -4.0, "failure"),
        ("buy", -0.5, -0.25, "partial"),
        ("exit", -4.0, -1.0, "success"),
        ("reduce", 4.0, 3.0, "failure"),
        ("watch", 1.0, 0.5, "success"),
    ],
)
def test_classify_signal_outcome(action, actual_return, excess_return, expected):
    service = SignalTrackingService()

    assert service.classify_outcome(action, actual_return, excess_return) == expected


def test_pct_change_rounds_to_two_decimals():
    service = SignalTrackingService()

    assert service._pct_change(100, 112.345) == 12.35


@pytest.mark.asyncio
async def test_signal_outcomes_endpoint_shape():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/signals/outcomes?limit=5&horizon=1w")

    assert resp.status_code == 200
    payload = resp.json()
    assert "items" in payload
    assert "summary" in payload
    assert payload["count"] == len(payload["items"])


def test_signal_snapshot_unique_constraint_exists():
    constraints = {constraint.name for constraint in SignalDecisionSnapshot.__table__.constraints}

    assert "uq_signal_stock_decision_date" in constraints


def test_calibration_bucket_metrics():
    service = SignalTrackingService()
    rows = [
        SignalDecisionSnapshot(action="buy", outcome_1w="success", actual_return_1w_pct=4.0, excess_return_1w_pct=2.0),
        SignalDecisionSnapshot(action="buy", outcome_1w="partial", actual_return_1w_pct=1.0, excess_return_1w_pct=-0.5),
        SignalDecisionSnapshot(action="buy", outcome_1w="failure", actual_return_1w_pct=-3.0, excess_return_1w_pct=-4.0),
    ]

    bucket = service._calibration_bucket("buy", rows, "1w")

    assert bucket["count"] == 3
    assert bucket["success_rate"] == pytest.approx(33.3)
    assert bucket["non_failure_rate"] == pytest.approx(66.7)
    assert bucket["avg_return_pct"] == pytest.approx(0.67)
    assert bucket["avg_excess_return_pct"] == pytest.approx(-0.83)


def test_calibration_recommendations_waits_for_sample_size():
    service = SignalTrackingService()

    assert service._calibration_recommendations([], "1w") == [
        "Örneklem henüz düşük; eşik değiştirmek için en az 20 ölçülmüş sinyal beklenmeli."
    ]


def test_suggest_policy_stays_observation_with_low_sample():
    service = SignalTrackingService()

    policy = service.suggest_policy([], "1w")

    assert policy["mode"] == "observation"
    assert policy["reasons"] == ["sample_size_below_20"]


def test_suggest_policy_enforces_when_buy_signals_fail():
    service = SignalTrackingService()
    rows = [
        SignalDecisionSnapshot(
            action="buy",
            risk_level="high" if index < 8 else "medium",
            outcome_1w="failure" if index < 16 else "success",
            actual_return_1w_pct=-3.0 if index < 16 else 4.0,
            excess_return_1w_pct=-4.0 if index < 16 else 2.0,
        )
        for index in range(20)
    ]

    policy = service.suggest_policy(rows, "1w")

    assert policy["mode"] == "enforced"
    assert policy["min_buy_confidence"] == 80
    assert policy["min_buy_risk_reward"] == pytest.approx(1.8)
    assert policy["block_high_risk_buys"] is True
