"""Haberler ekranı için gerçek piyasa/KAP akışı."""
import datetime
import logging
from datetime import timezone
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Günlük AI piyasa özeti — in-memory cache ───
_summary_cache: dict = {}

DAILY_SUMMARY_PROMPT = (
    "BIST100 borsasındaki günlük piyasa koşulları hakkında yatırımcılara yönelik "
    "kısa Türkçe bir özet yaz. 3-4 cümle, anlaşılır dil, genel eğilim ve dikkat "
    "edilmesi gereken noktaları içersin."
)


@router.get("/intelligence/daily-summary")
async def get_daily_summary():
    """Günlük Gemini piyasa özeti — in-memory cache, her sabah 09:05'te sıfırlanır."""
    from app.services.gemini_service import gemini_service

    today = datetime.date.today().isoformat()
    if _summary_cache.get("date") == today and _summary_cache.get("summary"):
        return {
            "summary": _summary_cache["summary"],
            "generated_at": _summary_cache["generated_at"],
            "from_cache": True,
        }

    try:
        summary_text = await gemini_service.generate(DAILY_SUMMARY_PROMPT)
    except Exception as e:
        logger.error(f"Günlük özet üretim hatası: {e}")
        summary_text = "Piyasa özeti şu anda alınamıyor."

    generated_at = datetime.datetime.now(timezone.utc).isoformat()
    _summary_cache.clear()
    _summary_cache["date"] = today
    _summary_cache["summary"] = summary_text
    _summary_cache["generated_at"] = generated_at

    return {
        "summary": summary_text,
        "generated_at": generated_at,
        "from_cache": False,
    }


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


