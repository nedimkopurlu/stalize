from app.services.model_portfolio import _build_decision_band


def test_build_decision_band_combines_review_and_changes():
    band = _build_decision_band(
        review_notes={
            "factor_drag": [
                {"factor": "technical_breakdown", "label": "teknik kırılım", "weighted_drag": 1.4},
                {"factor": "negative_news_flow", "label": "negatif haber/KAP akışı", "weighted_drag": 1.1},
            ],
            "next_week_adjustments": {
                "penalized_symbols": ["AKBNK", "SAHOL"],
            },
        },
        review_summary="Geçen hafta bankacılık zayıflığı portföyü baskıladı.",
        changes={
            "added": ["ASELS"],
            "removed": ["AKBNK"],
            "summary": "eklenen: ASELS; çıkarılan: AKBNK",
        },
    )

    assert band is not None
    assert band["headline"] == "Bu haftaki model portföy kararı"
    assert "bankacılık zayıflığı" in band["focus"]
    assert any("ASELS" in item for item in band["actions"])
    assert any("AKBNK" in item for item in band["actions"])
    assert any("teknik kırılım" in item for item in band["actions"])
