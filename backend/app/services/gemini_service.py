"""
Gemini LLM Servis Katmanı — Phase 35.
Tüm LLM çağrıları bu modülden geçer.
Quota aşılırsa (429) veya herhangi bir hata oluşursa Türkçe fallback döner.
"""
import logging
from typing import Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from app.core.config import settings

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = "Analiz şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin."


class GeminiService:
    """Google Gemini 2.0 Flash servis katmanı."""

    def __init__(self) -> None:
        self._configured = False
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._configured = True

    async def generate(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
    ) -> str:
        """
        Verilen prompt ile Gemini'ye istek gönderir.
        Başarılıysa yanıt metnini döner.
        Quota (429) veya herhangi hata durumunda FALLBACK_MESSAGE döner, exception fırlatmaz.
        """
        if not self._configured:
            logger.warning("GEMINI_API_KEY yapılandırılmamış; fallback döndürülüyor.")
            return FALLBACK_MESSAGE

        try:
            llm = genai.GenerativeModel(model)
            response = await llm.generate_content_async(prompt)
            return response.text
        except ResourceExhausted as e:
            logger.warning("Gemini quota aşıldı (429): %s", e)
            return FALLBACK_MESSAGE
        except Exception as e:
            logger.error("Gemini generate hatası: %s", e)
            return FALLBACK_MESSAGE


gemini_service = GeminiService()
