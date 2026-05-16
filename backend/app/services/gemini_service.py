"""
LLM Servis Katmanı — Phase 35.
OpenAI ChatGPT API sağlayıcısı.
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


class OpenAIService:
    """LLM servis katmanı — OpenAI Chat Completions API."""

    def __init__(self) -> None:
        self._client = None
        self._configured = False

        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self._configured = True
                logger.info("OpenAI istemcisi başlatıldı (%s).", settings.OPENAI_MODEL)
            except Exception as e:
                logger.error("OpenAI başlatma hatası: %s", e)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Verilen prompt ile LLM'e istek gönderir.
        OpenAI başarısız olursa FALLBACK_MESSAGE döner.
        """
        sys = system_prompt or SYSTEM_PROMPT
        if not self._configured or self._client is None:
            logger.error("OpenAI API anahtarı yapılandırılmamış.")
            return FALLBACK_MESSAGE

        try:
            response = await self._client.chat.completions.create(
                model=model or settings.OPENAI_MODEL,
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
            logger.error("OpenAI generate hatası: %s", e)

        return FALLBACK_MESSAGE


GeminiService = OpenAIService
gemini_service = OpenAIService()
