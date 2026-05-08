"""
LLM Servis Katmanı — Phase 35.
Groq (llama-3.3-70b) birincil sağlayıcı, Gemini yedek.
Tüm LLM çağrıları bu modülden geçer.
Hata durumunda Türkçe fallback döner.
"""
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = "Analiz şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin."

SYSTEM_PROMPT = """Sen deneyimli bir Türk borsa analistsin. BIST hisseleri üzerine derinlemesine,
gerçekçi ve yatırımcıya değer katan analizler yazıyorsun. Analizlerin:
- Verilen sayısal verileri yorumluyor, sadece tekrar etmiyor
- Sektörel bağlamı ve piyasa koşullarını dikkate alıyor
- Hem fırsatları hem riskleri dengeli ele alıyor
- Net bir sonuç ve yönlendirme içeriyor
- Profesyonel ama anlaşılır bir dille yazılıyor
- Türkçe, akıcı ve doğal bir üslup kullanıyor

Asla "bu bir yatırım tavsiyesi değildir" gibi yasal uyarılar ekleme.
Kısa ama özlü ol — 5-8 cümle ideal."""


class GeminiService:
    """LLM servis katmanı — Groq birincil, Gemini yedek."""

    def __init__(self) -> None:
        self._groq_client = None
        self._gemini_configured = False

        # Groq istemcisini başlat
        if settings.GROQ_API_KEY:
            try:
                from groq import AsyncGroq
                self._groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq istemcisi başlatıldı (llama-3.3-70b).")
            except Exception as e:
                logger.error("Groq başlatma hatası: %s", e)

        # Gemini yedek olarak
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini_configured = True
            except Exception as e:
                logger.warning("Gemini yapılandırma hatası: %s", e)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
    ) -> str:
        """
        Verilen prompt ile LLM'e istek gönderir.
        Groq başarısız olursa Gemini'yi dener.
        Her iki sağlayıcı da başarısız olursa FALLBACK_MESSAGE döner.
        """
        sys = system_prompt or SYSTEM_PROMPT

        # 1. Groq ile dene
        if self._groq_client:
            try:
                response = await self._groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": sys},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1024,
                    temperature=0.65,
                )
                text = response.choices[0].message.content
                if text:
                    return text.strip()
            except Exception as e:
                logger.warning("Groq generate hatası, Gemini'ye geçiliyor: %s", e)

        # 2. Gemini yedek
        if self._gemini_configured:
            try:
                import google.generativeai as genai
                llm = genai.GenerativeModel(
                    "gemini-2.0-flash",
                    system_instruction=sys,
                )
                response = await llm.generate_content_async(prompt)
                return response.text.strip()
            except Exception as e:
                logger.error("Gemini generate hatası: %s", e)

        logger.error("Tüm LLM sağlayıcıları başarısız.")
        return FALLBACK_MESSAGE


gemini_service = GeminiService()
