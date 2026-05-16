"""Haberler ekranı için gerçek piyasa/KAP akışı."""
import datetime
import logging
from datetime import timezone
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Günlük AI piyasa özeti — in-memory cache ───
_summary_cache: dict = {}

DAILY_SUMMARY_PROMPT = """Bugün BIST100 piyasasında yatırımcılar için günlük bir piyasa değerlendirmesi yaz.

Aşağıdaki konuları kısaca ele al:
1. Türk borsasının genel durumu ve son dönem eğilimi (yükselen mi, baskı altında mı?)
2. Küresel piyasaların (ABD, Avrupa, emtia) BIST'e olası etkisi
3. Türk yatırımcıların dikkat etmesi gereken makroekonomik faktörler (döviz kuru, faiz, enflasyon)
4. Bugün öne çıkabilecek sektörler veya temalar
5. Kısa vadeli bir yön önerisi

Yanıtı 4-6 cümlelik akıcı Türkçe paragraflar olarak yaz. Gereksiz yasal uyarı ekleme."""


@router.get("/intelligence/daily-summary")
async def get_daily_summary():
    """Günlük OpenAI piyasa özeti — in-memory cache, her sabah 09:05'te sıfırlanır."""
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
            "ai_digest": {
                "summary": "Haber akışı şu anda alınamadı; sistem kaynakları tekrar deneyecek.",
                "generated_by": "fallback",
                "confidence": 0,
                "generated_at": datetime.datetime.now(timezone.utc).isoformat(),
            },
            "priority_mode": "kap_first",
            "primary_source": "KAP",
            "error": "Piyasa akışı alınamadı",
        }
