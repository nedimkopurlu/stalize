from app.models.model_portfolio import ModelPortfolioHolding
from app.services.model_portfolio import (
    _build_next_week_adjustments,
    _build_review_summary,
    _classify_holding_failure,
)


def test_classify_holding_failure_detects_multiple_weaknesses():
    holding = ModelPortfolioHolding(
        symbol="TEST",
        technical_score=42,
        fundamental_score=49,
        sentiment_score=41,
        overall_score=54,
    )

    reasons = _classify_holding_failure(holding, -8.4)

    assert "technical_breakdown" in reasons
    assert "fundamental_weakness" in reasons
    assert "negative_news_flow" in reasons
    assert "low_conviction" in reasons
    assert "deep_drawdown" in reasons


def test_build_next_week_adjustments_switches_to_defensive_mode():
    adjustments = _build_next_week_adjustments(
        poor_performers=[
            {"symbol": "AAA", "return_pct": -7.2, "failure_tags": ["deep_drawdown"]},
            {"symbol": "BBB", "return_pct": -5.6, "failure_tags": ["technical_breakdown"]},
            {"symbol": "CCC", "return_pct": -2.1, "failure_tags": ["market_relative_weakness"]},
        ],
        sector_drag={"Bankacılık": -1.3, "Enerji": -1.4},
        factor_drag={"technical_breakdown": 1.8, "negative_news_flow": 1.2},
    )

    assert adjustments["review_mode"] == "defensive"
    assert adjustments["penalized_symbols"] == ["AAA", "BBB"]
    assert adjustments["sector_caps"] == {"Bankacılık": 1, "Enerji": 1}
    assert adjustments["factor_penalties"] == {
        "technical_breakdown": 6,
        "negative_news_flow": 6,
    }


def test_build_review_summary_mentions_penalized_symbols():
    summary = _build_review_summary(
        portfolio_return=-3.4,
        top_drags=[("Bankacılık", -1.7), ("Enerji", -0.8)],
        factor_drag={"technical_breakdown": 2.2, "negative_news_flow": 1.4},
        adjustments={
            "penalized_symbols": ["AKBNK", "TUPRS"],
            "sector_caps": {"Bankacılık": 1},
            "factor_penalties": {"technical_breakdown": 6},
            "review_mode": "defensive",
        },
    )

    assert "Bankacılık" in summary
    assert "AKBNK" in summary
    assert "teknik kırılım" in summary
