"""
Tests for 10-03: Scoring weights rebalanced — Fundamental 45%, Technical 40%, News 15%.
Requirements: MIDT-02, CLEN-04
"""
from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Test 1: Weighted calculation with all three scores present
# ---------------------------------------------------------------------------
def test_calculate_overall_score_all_scores():
    """
    calculate_overall_score(fundamental=80, technical=60, sentiment=40) must return 66.0.
    80*0.45 + 60*0.40 + 40*0.15 = 36 + 24 + 6 = 66.0
    """
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = 80.0
    stock.technical_score = 60.0
    stock.sentiment_score = 40.0

    overall, rec = engine.calculate_overall_score(stock)

    expected = 80 * 0.45 + 60 * 0.40 + 40 * 0.15  # = 66.0
    assert abs(overall - expected) < 0.01, f"Expected {expected}, got {overall}"
    assert rec == "AL", f"Score 66.0 should be 'AL', got {rec}"


# ---------------------------------------------------------------------------
# Test 2: Only fundamental_score present — normalize to 100% weight
# ---------------------------------------------------------------------------
def test_calculate_overall_score_only_fundamental():
    """
    If only fundamental_score=70 is available, overall should equal 70.0
    (weight fully re-normalized to fundamental alone).
    """
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = 70.0
    stock.technical_score = None
    stock.sentiment_score = None

    overall, rec = engine.calculate_overall_score(stock)

    assert abs(overall - 70.0) < 0.01, f"Expected 70.0, got {overall}"


# ---------------------------------------------------------------------------
# Test 3: All scores None -> DEFAULT_SCORE=50.0 + "TUT"
# ---------------------------------------------------------------------------
def test_calculate_overall_score_all_none():
    """When all three input scores are None, return (50.0, 'TUT')."""
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = None
    stock.technical_score = None
    stock.sentiment_score = None

    overall, rec = engine.calculate_overall_score(stock)

    assert overall == 50.0, f"Expected DEFAULT_SCORE 50.0, got {overall}"
    assert rec == "TUT", f"Expected 'TUT', got {rec}"


# ---------------------------------------------------------------------------
# Test 4: Recommendation thresholds
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("score,expected_rec", [
    (85.0, "GÜÇLÜ AL"),
    (80.0, "GÜÇLÜ AL"),
    (79.9, "AL"),
    (65.0, "AL"),
    (64.9, "TUT"),
    (45.0, "TUT"),
    (44.9, "SAT"),
    (25.0, "SAT"),
    (24.9, "GÜÇLÜ SAT"),
    (10.0, "GÜÇLÜ SAT"),
])
def test_recommendation_thresholds(score, expected_rec):
    """Recommendation thresholds: >=80 GÜÇLÜ AL, >=65 AL, >=45 TUT, >=25 SAT, <25 GÜÇLÜ SAT."""
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    # Set fundamental only so overall == score directly
    stock.fundamental_score = score
    stock.technical_score = None
    stock.sentiment_score = None

    overall, rec = engine.calculate_overall_score(stock)

    assert abs(overall - score) < 0.01, f"Expected overall={score}, got {overall}"
    assert rec == expected_rec, f"Score {score} -> expected {expected_rec}, got {rec}"


# ---------------------------------------------------------------------------
# Test 5: unrelated legacy scores are ignored
# ---------------------------------------------------------------------------
def test_legacy_scores_ignored():
    """
    Adding unrelated legacy attributes should not change the result.
    Scoring engine must only read fundamental/technical/sentiment scores.
    """
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()

    stock_without_legacy = MagicMock()
    stock_without_legacy.fundamental_score = 70.0
    stock_without_legacy.technical_score = 50.0
    stock_without_legacy.sentiment_score = 30.0

    stock_with_legacy = MagicMock()
    stock_with_legacy.fundamental_score = 70.0
    stock_with_legacy.technical_score = 50.0
    stock_with_legacy.sentiment_score = 30.0
    stock_with_legacy.unused_score = 99.0

    overall_without, _ = engine.calculate_overall_score(stock_without_legacy)
    overall_with, _ = engine.calculate_overall_score(stock_with_legacy)

    assert abs(overall_without - overall_with) < 0.01, (
        f"legacy attributes should not affect result: {overall_without} vs {overall_with}"
    )


# ---------------------------------------------------------------------------
# Test 6: Weight sum = 1.0
# ---------------------------------------------------------------------------
def test_config_weights_sum_to_one():
    """WEIGHT_FUNDAMENTAL + WEIGHT_TECHNICAL + WEIGHT_NEWS must equal 1.0."""
    from app.core.config import settings

    total = settings.WEIGHT_FUNDAMENTAL + settings.WEIGHT_TECHNICAL + settings.WEIGHT_NEWS
    assert abs(total - 1.0) < 0.001, (
        f"Weight sum must be 1.0, got {total} "
        f"(F={settings.WEIGHT_FUNDAMENTAL} T={settings.WEIGHT_TECHNICAL} N={settings.WEIGHT_NEWS})"
    )
    assert settings.WEIGHT_FUNDAMENTAL == pytest.approx(0.45)
    assert settings.WEIGHT_TECHNICAL == pytest.approx(0.40)
    assert settings.WEIGHT_NEWS == pytest.approx(0.15)


# ---------------------------------------------------------------------------
# Test 7: No legacy model/causal weights in config
# ---------------------------------------------------------------------------
def test_no_legacy_model_causal_weights_in_config():
    """config.py must not expose WEIGHT_ML, WEIGHT_CAUSAL, or WEIGHT_MACRO."""
    from app.core.config import settings

    assert not hasattr(settings, "WEIGHT_ML"), "WEIGHT_ML must be removed from config"
    assert not hasattr(settings, "WEIGHT_CAUSAL"), "WEIGHT_CAUSAL must be removed from config"
    assert not hasattr(settings, "WEIGHT_MACRO"), "WEIGHT_MACRO must be removed from config"


# ---------------------------------------------------------------------------
# Test 8: overall_score stays within [0, 100]
# ---------------------------------------------------------------------------
def test_overall_score_clamped():
    """overall_score must be clamped between 0.0 and 100.0."""
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = 150.0  # out of range input
    stock.technical_score = None
    stock.sentiment_score = None

    overall, _ = engine.calculate_overall_score(stock)

    assert 0.0 <= overall <= 100.0, f"overall_score out of range: {overall}"


def test_score_breakdown_all_components():
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = 80.0
    stock.technical_score = 60.0
    stock.sentiment_score = 40.0

    breakdown = engine.get_score_breakdown(stock)

    assert breakdown["overall_score"] == pytest.approx(66.0)
    assert breakdown["recommendation"] == "AL"
    assert breakdown["summary"]["available_component_count"] == 3
    assert breakdown["summary"]["normalization_applied"] is False
    assert len(breakdown["components"]) == 3
    assert breakdown["components"][0]["normalized_weight"] == pytest.approx(0.45)


def test_score_breakdown_with_missing_component_normalizes():
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.fundamental_score = 80.0
    stock.technical_score = 60.0
    stock.sentiment_score = None

    breakdown = engine.get_score_breakdown(stock)

    assert breakdown["overall_score"] == pytest.approx(70.59, abs=0.01)
    assert breakdown["summary"]["normalization_applied"] is True
    assert breakdown["summary"]["missing_component_count"] == 1
    assert breakdown["summary"]["weight_coverage"] == pytest.approx(0.85)
    assert breakdown["missing_components"][0]["key"] == "sentiment_score"


@pytest.mark.asyncio
async def test_contextual_score_breakdown_adds_company_macro_and_risk_layers():
    from app.services.scoring import ScoringEngine

    engine = ScoringEngine()
    stock = MagicMock()
    stock.id = 1
    stock.fundamental_score = 70.0
    stock.technical_score = 65.0
    stock.sentiment_score = 55.0
    stock.daily_change_pct = 1.8
    stock.is_bist30 = True

    class FakeResult:
        def __init__(self, items):
            self._items = items

        def scalars(self):
            return self

        def all(self):
            return self._items

    class FakeNews:
        def __init__(self, source, category, sentiment_score, importance_score, title):
            self.source = source
            self.category = category
            self.sentiment_score = sentiment_score
            self.importance_score = importance_score
            self.title = title
            self.published_at = datetime.now(timezone.utc)
            self.stock_id = 1 if source == "KAP" else None

    company_items = [
        FakeNews("KAP", "investment", 0.4, 0.9, "Yeni yatırım teşviki"),
    ]
    macro_items = [
        FakeNews("TCMB", "macro", -0.1, 0.8, "Faiz kararı"),
    ]

    class FakeDB:
        def __init__(self):
            self.calls = 0

        async def execute(self, _stmt):
            self.calls += 1
            return FakeResult(company_items if self.calls == 1 else macro_items)

    breakdown = await engine.get_contextual_score_breakdown(stock, db=FakeDB(), crisis_mode=False)

    assert breakdown["recommendation"] in {"TUT", "AL", "GÜÇLÜ AL"}
    assert len(breakdown["components"]) == 6
    assert {item["key"] for item in breakdown["components"]} == {
        "fundamental_score",
        "technical_score",
        "sentiment_score",
        "company_event_score",
        "macro_regime_score",
        "risk_overlay_score",
    }
    assert breakdown["summary"]["crisis_mode"] is False
