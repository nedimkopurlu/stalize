"""Market events router — KAP/makro olay akışı ve korelasyon analizi."""
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/intelligence/overview")
async def get_intelligence_overview(limit: int = 10):
    """Birleşik KAP/makro olay akışı özeti."""
    try:
        from app.services.market_intelligence import market_intelligence_service
        return await market_intelligence_service.get_overview(limit=limit)
    except Exception as e:
        logger.error(f"Piyasa akışı özeti hatası: {e}", exc_info=True)
        # Return degraded response so dashboard still loads
        return {
            "feed": [],
            "scenarios": [],
            "source_summary": {},
            "horizon_summary": {},
            "priority_mode": "kap_first",
            "primary_source": "KAP",
            "error": "Piyasa akışı alınamadı",
        }



@router.get("/correlation/matrix")
async def get_correlation_matrix(window_days: int = 30):
    """
    Dinamik korelasyon matrisini getir.

    window_days: 30, 60, veya 90 gün
    """
    from app.services.dynamic_correlation import correlation_engine

    try:
        if window_days not in [30, 60, 90]:
            window_days = 30

        result = await correlation_engine.compute_correlation_matrix(window_days=window_days)

        if not result:
            raise HTTPException(status_code=503, detail="Yeterli veri yok")

        return result

    except Exception as e:
        logger.error(f"Korelasyon matrisi hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Korelasyon matrisi hesaplanamadı")


@router.get("/correlation/crisis")
async def get_crisis_mode_status():
    """Kriz modu durumunu kontrol et."""
    from app.services.dynamic_correlation import correlation_engine

    try:
        # Son korelasyon matrisini hesapla
        result = await correlation_engine.compute_correlation_matrix(window_days=30)

        if not result:
            return {
                "crisis_mode": False,
                "reason": "Veri yok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        stats = result.get("statistics", {})
        crisis = result.get("crisis_mode", False)

        return {
            "crisis_mode": crisis,
            "statistics": stats,
            "alert_level": "🔴 KRİTİK" if crisis else "🟢 NORMAL",
            "mean_correlation": stats.get("mean_correlation"),
            "mean_volatility_pct": stats.get("mean_volatility_pct"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Kriz modu hatası: {e}", exc_info=True)
        return {"error": "Kriz modu hesaplanamadı"}


@router.get("/correlation/diversification-advice")
async def get_diversification_advice():
    """Portföy çeşitlendirme tavsiyesi al."""
    from app.services.dynamic_correlation import correlation_engine

    try:
        recommendations = await correlation_engine.get_diversification_recommendations()

        if not recommendations:
            raise HTTPException(status_code=503, detail="Tavsiye üretilemiyor")

        return recommendations

    except Exception as e:
        logger.error(f"Diversifikasyon tavsiyesi hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Diversifikasyon tavsiyesi alınamadı")


@router.get("/correlation/low-correlation-pairs")
async def get_low_correlation_pairs(threshold: float = 0.3, limit: int = 20):
    """Düşük korelasyonlu hisse çiftlerini getir (çeşitlendirme için)."""
    from app.services.dynamic_correlation import correlation_engine

    try:
        pairs = await correlation_engine.find_low_correlation_pairs(
            correlation_threshold=threshold
        )

        return {
            "pairs": [
                {
                    "symbol1": s1,
                    "symbol2": s2,
                    "correlation": corr,
                    "quality": "excellent" if corr < 0.1 else "good" if corr < 0.3 else "fair"
                }
                for s1, s2, corr in pairs[:limit]
            ],
            "total_found": len(pairs),
            "threshold": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Düşük korelasyon çiftleri hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Korelasyon çiftleri hesaplanamadı")
