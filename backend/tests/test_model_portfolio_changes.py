from app.models.model_portfolio import ModelPortfolioHolding
from app.services.model_portfolio import _summarize_week_changes


def _holding(symbol: str, allocation_pct: float) -> ModelPortfolioHolding:
    return ModelPortfolioHolding(symbol=symbol, allocation_pct=allocation_pct)


def test_summarize_week_changes_detects_added_removed_and_reweights():
    previous = [
        _holding("AKBNK", 20),
        _holding("THYAO", 18),
        _holding("SISE", 12),
    ]
    current = [
        _holding("AKBNK", 24),
        _holding("SISE", 11),
        _holding("ASELS", 15),
    ]

    changes = _summarize_week_changes(current, previous)

    assert changes["added"] == ["ASELS"]
    assert changes["removed"] == ["THYAO"]
    assert changes["increased"][0]["symbol"] == "AKBNK"
    assert changes["decreased"][0]["symbol"] == "SISE"
    assert "eklenen: ASELS" in changes["summary"]
    assert "çıkarılan: THYAO" in changes["summary"]
