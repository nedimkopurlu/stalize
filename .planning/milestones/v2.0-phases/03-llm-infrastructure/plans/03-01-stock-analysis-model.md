---
phase: 03-llm-infrastructure
plan_id: "03-01"
title: "LLMI-01: StockAnalysis Pydantic model + instructor integration"
requirement: LLMI-01
wave: 1
estimated_minutes: 45
autonomous: true
depends_on: ["03-00"]
files_modified:
  - backend/requirements.txt
  - backend/app/services/llm_sentiment.py
  - backend/app/services/sentiment.py
  - backend/app/services/kap_parser.py
  - backend/app/services/tuik_adapter.py
  - backend/app/services/tcmb_adapter.py
  - backend/tests/test_llm_cache.py
must_haves:
  truths:
    - "analyze() returns a StockAnalysis instance, not a dict"
    - "karar field is one of AL, SAT, TUT — ValidationError raised otherwise"
    - "_to_legacy_dict() maps StockAnalysis to the legacy dict shape callers expect"
    - "All four caller files (sentiment.py, kap_parser.py, tuik_adapter.py, tcmb_adapter.py) call _to_legacy_dict() and no longer do dict-key access on analyze() result"
    - "test_llm_cache.py still passes after migration"
  artifacts:
    - path: "backend/app/services/llm_sentiment.py"
      provides: "StockAnalysis model, instructor-patched client, _to_legacy_dict helper"
      contains: "class StockAnalysis(BaseModel)"
    - path: "backend/requirements.txt"
      provides: "instructor==1.15.1 dependency"
      contains: "instructor==1.15.1"
  key_links:
    - from: "DeepSeekSentimentService.__init__"
      to: "instructor.from_openai"
      via: "self._patched_client = instructor.from_openai(self.client, mode=instructor.Mode.JSON)"
      pattern: "instructor.from_openai"
    - from: "analyze()"
      to: "self._patched_client.chat.completions.create"
      via: "response_model=StockAnalysis"
      pattern: "response_model=StockAnalysis"
    - from: "sentiment.py / kap_parser.py / tuik_adapter.py / tcmb_adapter.py"
      to: "_to_legacy_dict"
      via: "analysis = _to_legacy_dict(await llm_sentiment_service.analyze(...))"
      pattern: "_to_legacy_dict"
---

<objective>
Integrate the `instructor` library into `DeepSeekSentimentService` so `analyze()` returns a validated `StockAnalysis` Pydantic object instead of a raw dict parsed from JSON. Add `_to_legacy_dict()` so the four existing callers keep working without any business-logic changes.

Purpose: Eliminate brittle `json.loads` + regex fence stripping (current lines 95–103 of llm_sentiment.py). instructor handles JSON extraction, retries on ValidationError, and type coercion automatically.
Output: `llm_sentiment.py` rewritten with StockAnalysis model + instructor client; four caller files updated; requirements.txt gains instructor.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/REQUIREMENTS.md
@.planning/phases/03-llm-infrastructure/03-CONTEXT.md
@.planning/phases/03-llm-infrastructure/RESEARCH.md
@backend/app/services/llm_sentiment.py
@backend/tests/test_llm_cache.py

<interfaces>
<!-- Current llm_sentiment.py exports — executor must preserve these signatures -->

Module-level:
  _llm_cache: diskcache.Cache          ← Phase 2, must not change
  llm_sentiment_service: DeepSeekSentimentService  ← module singleton, must remain

DeepSeekSentimentService.analyze() current signature:
  async def analyze(
      self,
      title: str,
      summary: str = "",
      source: str = "Unknown",
      symbol: str = None,
      event_type: str = None,
  ) -> Dict

Caller access patterns after migration (from RESEARCH.md Caller Impact Map):
  sentiment.py:     analysis["sentiment_score"], analysis["importance_score"]
  kap_parser.py:    analysis["sentiment_score"], analysis["sentiment_label"],
                    analysis["sentiment_confidence"], analysis["importance_score"]
  tuik_adapter.py:  analysis.get("sentiment_score"), analysis.get("sentiment_label"),
                    analysis.get("sentiment_confidence")
  tcmb_adapter.py:  analysis.get("sentiment_score"), analysis.get("sentiment_label"),
                    analysis.get("sentiment_confidence")
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add instructor to requirements.txt and rewrite llm_sentiment.py</name>
  <files>backend/requirements.txt, backend/app/services/llm_sentiment.py</files>
  <behavior>
    - StockAnalysis(karar="AL", ...) is valid; StockAnalysis(karar="BUY", ...) raises ValidationError
    - analyze() returns StockAnalysis instance (isinstance check passes)
    - analyze() with no client returns StockAnalysis(karar="TUT", gerekçe="LLM devre dışı")
    - _to_legacy_dict(StockAnalysis(karar="AL", ...))["sentiment_score"] == 0.7
    - _to_legacy_dict(StockAnalysis(karar="SAT", ...))["sentiment_score"] == -0.7
    - _to_legacy_dict(StockAnalysis(karar="TUT", ...))["sentiment_score"] == 0.0
    - _to_legacy_dict result has keys: sentiment_score, sentiment_label, sentiment_confidence, importance_score, summary, reasoning, staleness_warning
  </behavior>
  <action>
**Step 1 — Add instructor to requirements.txt:**

In `backend/requirements.txt`, add under `# NLP & Sentiment`:
```
instructor==1.15.1
```

**Step 2 — Rewrite backend/app/services/llm_sentiment.py:**

Replace the entire file with the following (preserve all comments and structure):

```python
import asyncio
import logging
import os
import instructor
import diskcache
from datetime import date, datetime, timezone, timedelta
from typing import Dict, List, Literal, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Module-level singletons ───────────────────────────────────────────────────

LLM_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../cache/llm")
)
os.makedirs(LLM_CACHE_DIR, exist_ok=True)
_llm_cache = diskcache.Cache(LLM_CACHE_DIR)           # Phase 2: MLCA-03
_llm_semaphore = asyncio.Semaphore(5)                  # Phase 3: LLMI-02

_STALENESS_THRESHOLD = timedelta(minutes=15)           # Phase 3: LLMI-03


# ── Pydantic model (LLMI-01) ──────────────────────────────────────────────────

class StockAnalysis(BaseModel):
    """Structured LLM output for a single stock/news analysis."""
    karar: Literal["AL", "SAT", "TUT"]
    risk: str
    ödül: str
    çelişkiler: List[str]
    gerekçe: str
    staleness_warning: Optional[str] = None  # set programmatically, NEVER by LLM


# ── Legacy compatibility helper ───────────────────────────────────────────────

def _to_legacy_dict(analysis: "StockAnalysis") -> dict:
    """Map StockAnalysis → legacy dict consumed by kap_parser, sentiment, tuik, tcmb."""
    score_map = {"AL": 0.7, "TUT": 0.0, "SAT": -0.7}
    label_map = {"AL": "pozitif", "TUT": "nötr", "SAT": "negatif"}
    score = score_map.get(analysis.karar, 0.0)
    return {
        "sentiment_score": score,
        "sentiment_label": label_map.get(analysis.karar, "nötr"),
        "sentiment_confidence": 0.9,
        "importance_score": abs(score) * 10,
        "summary": analysis.gerekçe[:100] if analysis.gerekçe else "",
        "reasoning": analysis.gerekçe,
        "staleness_warning": analysis.staleness_warning,
    }


# ── Service ───────────────────────────────────────────────────────────────────

class DeepSeekSentimentService:
    """
    KAP ve makro haberler için DeepSeek API tabanlı akıllı nedensellik ve etki analiz motoru.
    instructor kütüphanesi ile yapılandırılmış çıktı (StockAnalysis) döndürür.
    """

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.LLM_MODEL
        self.client = None
        self._patched_client = None

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            # instructor wraps AsyncOpenAI; Mode.JSON required for DeepSeek
            # (DeepSeek does NOT support Mode.JSON_SCHEMA — would cause 400 error)
            self._patched_client = instructor.from_openai(
                self.client,
                mode=instructor.Mode.JSON
            )
            settings.LLM_ENABLED = True
            logger.info(f"DeepSeek + instructor aktif (Model: {self.model})")
        else:
            logger.warning("DEEPSEEK_API_KEY eksik. LLM analizleri çalışmayacaktır.")

    def _build_system_prompt(self) -> str:
        return """Sen kıdemli bir Borsa İstanbul (BIST) veri analisti, quant stratejisti ve fon yöneticisisin.
Sana bir şirket KAP bildirimi veya makroekonomik kriz haberi verilecek.

LÜTFEN aşağıdaki kurallara harfiyen uyan, DOĞRUDAN ve TEMİZ bir JSON döndür. Başka hiçbir markdown kullanma:

{
    "karar": "<AL | SAT | TUT>",       // Yatırım kararı: AL (alım fırsatı), SAT (sat/azalt), TUT (bekle/izle)
    "risk": "<string>",                // Bu haberin taşıdığı başlıca risk faktörü (1-2 cümle)
    "ödül": "<string>",                // Bu haberin sunduğu potansiyel fırsat/kazanç (1-2 cümle)
    "çelişkiler": ["<string>"],        // Karşıt sinyaller veya belirsizlik kaynakları (liste, boş olabilir)
    "gerekçe": "<string>"             // Karar için detaylı ekonomik/finansal gerekçe (2-4 cümle)
}

staleness_warning alanını sen üretme — bu alan sistem tarafından doldurulur.
"""

    async def analyze(
        self,
        title: str,
        summary: str = "",
        source: str = "Unknown",
        symbol: str = None,
        event_type: str = None,
        as_of: Optional[datetime] = None,   # LLMI-03: veri tarih damgası
    ) -> "StockAnalysis":
        """
        Gelen haberi DeepSeek/instructor'a gönderip StockAnalysis döndürür.
        Callers must wrap result with _to_legacy_dict() for legacy field access.
        """
        if not self.client:
            logger.error("DeepSeek Client başlatılamamış. Fallback StockAnalysis dönülüyor.")
            return StockAnalysis(
                karar="TUT",
                risk="",
                ödül="",
                çelişkiler=[],
                gerekçe="LLM devre dışı",
            )

        # ── Cache check (before semaphore — cache hits don't occupy a slot) ──────
        date_str = date.today().isoformat()
        cache_key = f"analysis:{symbol}:{date_str}:{hash(title)}"
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"LLM cache hit: {cache_key}")
            return cached  # returns StockAnalysis (picklable via diskcache)

        # ── Staleness detection (LLMI-03) ─────────────────────────────────────────
        now = datetime.now(timezone.utc)
        staleness_warning = None
        if as_of is not None:
            if as_of.tzinfo is None:
                as_of = as_of.replace(tzinfo=timezone.utc)
            age = now - as_of
            if age > _STALENESS_THRESHOLD:
                staleness_warning = (
                    f"Veri {int(age.total_seconds() // 60)} dakikadan eski"
                )

        as_of_str = (as_of or now).strftime("%Y-%m-%d %H:%M UTC")
        prompt = (
            f"VERİ TARİHİ: {as_of_str}\n"
            f"KAYNAK: {source}\n"
            f"HABER BAŞLIĞI: {title}\n"
            f"İÇERİK: {summary}\n\n"
            "Bu haberin detaylı etkisini analiz et ve JSON ver:"
        )

        try:
            logger.info(f"DeepSeek'e gönderiliyor: '{title[:50]}...'")
            # ── Concurrency limit (LLMI-02) ────────────────────────────────────────
            async with _llm_semaphore:
                result: StockAnalysis = await self._patched_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    response_model=StockAnalysis,
                    temperature=0.2,
                    max_tokens=500,
                )

            result.staleness_warning = staleness_warning   # LLMI-03 post-injection
            _llm_cache.set(cache_key, result, expire=1800)
            return result

        except Exception as e:
            logger.error(f"DeepSeek/instructor hatası: {e}")
            return StockAnalysis(
                karar="TUT", risk="", ödül="", çelişkiler=[], gerekçe="Hata"
            )


llm_sentiment_service = DeepSeekSentimentService()
```

Key decisions in this implementation (per LLMI-01, CONTEXT.md, RESEARCH.md):
- `mode=instructor.Mode.JSON` NOT `Mode.JSON_SCHEMA` — DeepSeek incompatible with json_schema
- `staleness_warning` defaults to `None` — instructor will NOT ask LLM to generate it
- `_patched_client` on `self` (not module-level) — matches where `self.client` lives
- Manual json.loads + regex fence stripping (old lines 95-103) deleted — instructor handles this
- System prompt updated to describe karar/risk/ödül/çelişkiler/gerekçe schema explicitly
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py::test_stock_analysis_model_valid tests/test_llm_infrastructure.py::test_stock_analysis_model_invalid_karar tests/test_llm_infrastructure.py::test_legacy_dict_adapter -v 2>&1 | tail -15</automated>
  </verify>
  <done>test_stock_analysis_model_valid, test_stock_analysis_model_invalid_karar, and test_legacy_dict_adapter all PASS (not xfail). instructor import succeeds.</done>
</task>

<task type="auto">
  <name>Task 2: Migrate four caller files + fix test_llm_cache.py</name>
  <files>
    backend/app/services/sentiment.py,
    backend/app/services/kap_parser.py,
    backend/app/services/tuik_adapter.py,
    backend/app/services/tcmb_adapter.py,
    backend/tests/test_llm_cache.py
  </files>
  <action>
Update each caller to wrap the analyze() result with `_to_legacy_dict()`. Each file imports `_to_legacy_dict` and applies it immediately after the await.

**sentiment.py** (lines ~50-57):
```python
# Before:
analysis = await llm_sentiment_service.analyze(...)
normalized_score = (analysis["sentiment_score"] + 1.0) / 2.0 * 100.0
weight = max(0.1, float(analysis["importance_score"]))

# After:
from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict
...
_raw = await llm_sentiment_service.analyze(...)
analysis = _to_legacy_dict(_raw)
normalized_score = (analysis["sentiment_score"] + 1.0) / 2.0 * 100.0
weight = max(0.1, float(analysis["importance_score"]))
```

**kap_parser.py** (lines ~148-154):
```python
# Before:
analysis = await llm_sentiment_service.analyze(...)
score = analysis["sentiment_score"]
label = analysis["sentiment_label"]
confidence = analysis["sentiment_confidence"]
importance = analysis["importance_score"]

# After:
from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict
...
_raw = await llm_sentiment_service.analyze(...)
analysis = _to_legacy_dict(_raw)
score = analysis["sentiment_score"]
label = analysis["sentiment_label"]
confidence = analysis["sentiment_confidence"]
importance = analysis["importance_score"]
```

**tuik_adapter.py** (lines ~383-387):
```python
# Before:
analysis = await llm_sentiment_service.analyze(...)
score = analysis.get("sentiment_score", 0.0)
label = analysis.get("sentiment_label", "nötr")
confidence = analysis.get("sentiment_confidence", 0.5)

# After:
from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict
...
_raw = await llm_sentiment_service.analyze(...)
analysis = _to_legacy_dict(_raw)
score = analysis.get("sentiment_score", 0.0)
label = analysis.get("sentiment_label", "nötr")
confidence = analysis.get("sentiment_confidence", 0.5)
```

**tcmb_adapter.py** (lines ~335-339): same pattern as tuik_adapter.py.

**test_llm_cache.py** — update `make_mock_response` and the mock wiring:

The three existing cache tests mock `service.client.chat.completions.create`. After migration, `analyze()` calls `self._patched_client.chat.completions.create` (not `self.client`), and the return value is a `StockAnalysis` object (not a raw OpenAI response). Update all three tests:

1. Remove `make_mock_response` helper (returns raw OpenAI response object — no longer used)
2. Add `make_mock_stock_analysis` helper:
```python
from app.services.llm_sentiment import StockAnalysis

def make_mock_stock_analysis(karar: str = "AL") -> StockAnalysis:
    return StockAnalysis(
        karar=karar, risk="test risk", ödül="test ödül",
        çelişkiler=[], gerekçe="test gerekçe"
    )
```
3. In each test, set `service._patched_client = MagicMock()` and
   `service._patched_client.chat.completions.create = AsyncMock(return_value=make_mock_stock_analysis())`
   instead of mocking `service.client.chat.completions.create`.
4. Update `test_cache_hit_skips_api` assert to check `service._patched_client.chat.completions.create.call_count == 1`

Do NOT change the test names or the cache key / expiry logic being tested — only the mock wiring changes.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_cache.py tests/test_llm_infrastructure.py::test_instructor_integration -v 2>&1 | tail -15</automated>
  </verify>
  <done>test_llm_cache.py (3 tests) all PASS. test_instructor_integration PASSES (not xfail).</done>
</task>

</tasks>

<verification>
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py tests/test_llm_cache.py -v 2>&1 | tail -20
</verification>

<success_criteria>
- `from app.services.llm_sentiment import StockAnalysis, _to_legacy_dict` succeeds without ImportError
- test_stock_analysis_model_valid PASSES
- test_stock_analysis_model_invalid_karar PASSES
- test_legacy_dict_adapter PASSES
- test_instructor_integration PASSES
- All 3 test_llm_cache.py tests PASS
- No NameError or ImportError in any of the four caller files (grep for `_to_legacy_dict` confirms import added)
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-infrastructure/03-01-SUMMARY.md` with:
- Files modified and key changes per file
- StockAnalysis model field list
- _to_legacy_dict score mapping table (AL→0.7, TUT→0.0, SAT→-0.7)
- Note: test_llm_cache.py mock wiring updated to use _patched_client + StockAnalysis
</output>
