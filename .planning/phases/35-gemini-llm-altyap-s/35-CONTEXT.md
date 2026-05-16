# Phase 35: Gemini LLM Altyapısı - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend'de `google-generativeai` SDK ile Gemini 2.0 Flash servis katmanı kurulur. Tüm LLM çağrıları bu katmandan geçer. Quota aşımında (429) sistem hata yerine yapılandırılmış Türkçe fallback mesajı döner. Üst fazlar (36, 37, 39) bu katmanı import ederek kullanır.

Bu faz yalnızca backend'i kapsar — frontend değişikliği yoktur.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Saf altyapı fazı — tüm implementasyon kararları Claude'un takdirine bırakılmıştır.

Bilinen kısıtlar:
- SDK: `google-generativeai` (pip paketi)
- Model: `gemini-2.0-flash` (free tier: 15 req/min, 1500 req/gün)
- API key: `GEMINI_API_KEY` env var — `backend/app/core/config.py`'e eklenir
- Fallback: quota (429) ve network hata durumunda Türkçe placeholder döner, exception fırlatmaz
- Modül: `backend/app/services/gemini_service.py` — singleton pattern (diğer servislerle tutarlı)
- Async: `generate_content_async` kullanılır (FastAPI async uyumlu)
- Test: pytest ile unit test, Gemini SDK mock'lanır

</decisions>

<code_context>
## Existing Code Insights

### Established Patterns
- Servis singletons: `scoring_engine = ScoringEngine()` modül sonunda — aynı pattern kullanılır
- Settings: `backend/app/core/config.py` → `Settings(BaseSettings)` — `GEMINI_API_KEY: Optional[str] = None` eklenecek
- Async: tüm servisler `async def` kullanıyor; `AsyncSessionLocal()` context manager pattern
- Error handling: background task'lar `try/except Exception as e: logging.error(...)` — sessizce log, re-raise yok
- Logger: `logger = logging.getLogger(__name__)` her servis dosyasının başında

### Reusable Assets
- `backend/app/core/config.py` — settings singleton, env var pattern
- `backend/app/services/scoring.py` — singleton pattern referansı
- `backend/app/api/endpoints.py` — yeni endpoint buraya eklenir (`/api/llm/analyze/{symbol}`)

### Integration Points
- Phase 36: `gemini_service.analyze_stock(symbol, data)` → hisse detay endpoint'i
- Phase 37: `gemini_service.daily_summary(market_data)` → APScheduler job
- Phase 39: `gemini_service.model_portfolio_rationale(decisions)` → haftalık portföy kararı

</code_context>

<specifics>
## Specific Ideas

- Fallback mesajı Türkçe olmalı: "Analiz şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin."
- Önbellek: Phase 36'da eklenecek (bu fazda değil) — servis sadece generate eder
- Rate limit: servis `asyncio.sleep` ile retry yapmaz — 429 durumunda direkt fallback döner

</specifics>

<deferred>
## Deferred Ideas

- Response streaming (frontend için) — v2'ye bırakıldı
- Multi-model fallback (Gemini → başka model) — overkill, free tier yeterli
- Token sayacı / maliyet takibi — free tier'da gereksiz

</deferred>
