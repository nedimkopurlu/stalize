---
phase: 03-llm-infrastructure
plan_id: "03-00"
title: "Wave 0: xfail test stubs + validation scaffold"
requirement: LLMI-01, LLMI-02, LLMI-03
wave: 0
estimated_minutes: 20
autonomous: true
depends_on: []
files_modified:
  - backend/tests/test_llm_infrastructure.py
  - backend/tests/test_llm_cache.py
  - .planning/phases/03-llm-infrastructure/03-VALIDATION.md
must_haves:
  truths:
    - "pytest collects test_llm_infrastructure.py without import errors"
    - "All 7 stubs are marked xfail so the full suite stays green"
    - "test_llm_cache.py still passes after stub file is added"
  artifacts:
    - path: "backend/tests/test_llm_infrastructure.py"
      provides: "xfail stubs for all LLMI requirements"
      exports: ["test_stock_analysis_model_valid", "test_stock_analysis_model_invalid_karar",
                "test_semaphore_limits_concurrency", "test_staleness_warning_set_when_old",
                "test_no_staleness_warning_fresh", "test_instructor_integration",
                "test_legacy_dict_adapter"]
    - path: ".planning/phases/03-llm-infrastructure/03-VALIDATION.md"
      provides: "Validation strategy for phase gate"
  key_links:
    - from: "backend/tests/test_llm_infrastructure.py"
      to: "backend/app/services/llm_sentiment.py"
      via: "import app.services.llm_sentiment as ls"
      pattern: "import app.services.llm_sentiment"
---

<objective>
Create failing test stubs (xfail) for all Phase 3 requirements before any implementation begins. This ensures every requirement has a test that will turn green as the implementation is completed in Waves 1–3.

Purpose: Establish the test scaffold so Waves 1–3 executors can run `pytest tests/test_llm_infrastructure.py -x -q` after each task and see tests flip from xfail to pass.
Output: `backend/tests/test_llm_infrastructure.py` (7 xfail stubs), updated `backend/tests/test_llm_cache.py` notes, `03-VALIDATION.md`.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/REQUIREMENTS.md
@.planning/phases/03-llm-infrastructure/03-CONTEXT.md
@.planning/phases/03-llm-infrastructure/RESEARCH.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Write xfail test stubs for LLMI-01, LLMI-02, LLMI-03</name>
  <files>backend/tests/test_llm_infrastructure.py</files>
  <behavior>
    - test_stock_analysis_model_valid: StockAnalysis(karar="AL", risk="...", ödül="...", çelişkiler=[], gerekçe="...") does not raise
    - test_stock_analysis_model_invalid_karar: StockAnalysis(karar="BUY", ...) raises ValidationError
    - test_semaphore_limits_concurrency: asyncio.Semaphore(5) is module-level attribute of llm_sentiment; value is 5
    - test_staleness_warning_set_when_old: analyze() with as_of 20 minutes ago returns StockAnalysis with staleness_warning != None
    - test_no_staleness_warning_fresh: analyze() with as_of 5 minutes ago returns StockAnalysis with staleness_warning is None
    - test_instructor_integration: mock _patched_client.chat.completions.create to return StockAnalysis; verify analyze() returns StockAnalysis
    - test_legacy_dict_adapter: _to_legacy_dict(StockAnalysis(karar="AL", ...)) returns dict with keys sentiment_score, sentiment_label, sentiment_confidence, importance_score
  </behavior>
  <action>
Create `backend/tests/test_llm_infrastructure.py` with the following structure:

```python
"""
Tests for Phase 3: LLM Infrastructure (LLMI-01, LLMI-02, LLMI-03).
All tests are initially marked xfail — they pass as implementation lands in Waves 1-3.
"""
import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError


# ── LLMI-01: StockAnalysis Pydantic model ─────────────────────────────────────

@pytest.mark.xfail(reason="LLMI-01 not yet implemented", strict=True)
def test_stock_analysis_model_valid():
    """StockAnalysis accepts valid AL/SAT/TUT karar values without error."""
    from app.services.llm_sentiment import StockAnalysis
    for karar in ("AL", "SAT", "TUT"):
        m = StockAnalysis(
            karar=karar,
            risk="orta risk",
            ödül="yüksek getiri",
            çelişkiler=["makro baskı"],
            gerekçe="test gerekçe",
        )
        assert m.karar == karar
    assert m.staleness_warning is None  # default


@pytest.mark.xfail(reason="LLMI-01 not yet implemented", strict=True)
def test_stock_analysis_model_invalid_karar():
    """StockAnalysis rejects karar values outside AL/SAT/TUT."""
    from app.services.llm_sentiment import StockAnalysis
    with pytest.raises(ValidationError):
        StockAnalysis(
            karar="BUY",
            risk="",
            ödül="",
            çelişkiler=[],
            gerekçe="",
        )


# ── LLMI-02: asyncio.Semaphore(5) ────────────────────────────────────────────

@pytest.mark.xfail(reason="LLMI-02 not yet implemented", strict=True)
def test_semaphore_limits_concurrency():
    """Module exposes _llm_semaphore = asyncio.Semaphore(5)."""
    import app.services.llm_sentiment as ls
    assert hasattr(ls, "_llm_semaphore"), "_llm_semaphore missing from module"
    sem = ls._llm_semaphore
    assert isinstance(sem, asyncio.Semaphore)
    # Semaphore internal value is 5 at module import (no slots acquired)
    assert sem._value == 5


# ── LLMI-03: staleness_warning ───────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.xfail(reason="LLMI-03 not yet implemented", strict=True)
async def test_staleness_warning_set_when_old(tmp_path):
    """analyze() with as_of > 15 minutes ago returns staleness_warning set."""
    import app.services.llm_sentiment as ls
    import diskcache

    stale_as_of = datetime.now(timezone.utc) - timedelta(minutes=20)
    mock_analysis = ls.StockAnalysis(
        karar="TUT", risk="düşük", ödül="orta", çelişkiler=[], gerekçe="test"
    )

    test_cache = diskcache.Cache(str(tmp_path / "stale_test"))
    with patch.object(ls, "_llm_cache", test_cache):
        service = ls.DeepSeekSentimentService.__new__(ls.DeepSeekSentimentService)
        service.api_key = "test_key"
        service.model = "deepseek-chat"
        service.client = MagicMock()
        service._patched_client = MagicMock()
        service._patched_client.chat = MagicMock()
        service._patched_client.chat.completions = MagicMock()
        service._patched_client.chat.completions.create = AsyncMock(return_value=mock_analysis)

        result = await service.analyze(title="Stale News", symbol="AKBNK", as_of=stale_as_of)

    assert result.staleness_warning is not None
    assert "dakika" in result.staleness_warning


@pytest.mark.asyncio
@pytest.mark.xfail(reason="LLMI-03 not yet implemented", strict=True)
async def test_no_staleness_warning_fresh(tmp_path):
    """analyze() with as_of < 15 minutes ago returns staleness_warning = None."""
    import app.services.llm_sentiment as ls
    import diskcache

    fresh_as_of = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_analysis = ls.StockAnalysis(
        karar="AL", risk="orta", ödül="yüksek", çelişkiler=[], gerekçe="test"
    )

    test_cache = diskcache.Cache(str(tmp_path / "fresh_test"))
    with patch.object(ls, "_llm_cache", test_cache):
        service = ls.DeepSeekSentimentService.__new__(ls.DeepSeekSentimentService)
        service.api_key = "test_key"
        service.model = "deepseek-chat"
        service.client = MagicMock()
        service._patched_client = MagicMock()
        service._patched_client.chat = MagicMock()
        service._patched_client.chat.completions = MagicMock()
        service._patched_client.chat.completions.create = AsyncMock(return_value=mock_analysis)

        result = await service.analyze(title="Fresh News", symbol="AKBNK", as_of=fresh_as_of)

    assert result.staleness_warning is None


# ── LLMI-01: instructor integration ──────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.xfail(reason="LLMI-01 not yet implemented", strict=True)
async def test_instructor_integration(tmp_path):
    """analyze() returns StockAnalysis instance (not dict) when instructor is active."""
    import app.services.llm_sentiment as ls
    import diskcache

    expected = ls.StockAnalysis(
        karar="AL", risk="düşük", ödül="yüksek", çelişkiler=[], gerekçe="kâr artışı"
    )

    test_cache = diskcache.Cache(str(tmp_path / "instr_test"))
    with patch.object(ls, "_llm_cache", test_cache):
        service = ls.DeepSeekSentimentService.__new__(ls.DeepSeekSentimentService)
        service.api_key = "test_key"
        service.model = "deepseek-chat"
        service.client = MagicMock()
        service._patched_client = MagicMock()
        service._patched_client.chat = MagicMock()
        service._patched_client.chat.completions = MagicMock()
        service._patched_client.chat.completions.create = AsyncMock(return_value=expected)

        result = await service.analyze(title="Test Haber", symbol="GARAN")

    assert isinstance(result, ls.StockAnalysis)
    assert result.karar == "AL"


# ── LLMI-01: legacy dict adapter ─────────────────────────────────────────────

@pytest.mark.xfail(reason="LLMI-01 not yet implemented", strict=True)
def test_legacy_dict_adapter():
    """_to_legacy_dict converts StockAnalysis → legacy dict with expected keys."""
    from app.services.llm_sentiment import StockAnalysis, _to_legacy_dict
    analysis = StockAnalysis(
        karar="AL", risk="orta", ödül="yüksek", çelişkiler=[], gerekçe="test"
    )
    result = _to_legacy_dict(analysis)
    assert result["sentiment_score"] == pytest.approx(0.7)
    assert result["sentiment_label"] == "pozitif"
    assert result["sentiment_confidence"] == 0.9
    assert result["importance_score"] == pytest.approx(7.0)
    assert "summary" in result
    assert "reasoning" in result
```

Important: `strict=True` on all xfail markers means the test FAILS if it unexpectedly passes — this prevents the stubs from silently becoming no-ops.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py -v 2>&1 | tail -20</automated>
  </verify>
  <done>pytest collects 7 tests, all report xfail (not ERROR, not FAILED). Exit code 0.</done>
</task>

<task type="auto">
  <name>Task 2: Create 03-VALIDATION.md phase gate strategy</name>
  <files>.planning/phases/03-llm-infrastructure/03-VALIDATION.md</files>
  <action>
Create `.planning/phases/03-llm-infrastructure/03-VALIDATION.md` documenting the validation strategy for the phase gate. Include:

- Phase: 03-llm-infrastructure
- Status: Wave 0 complete
- Test file: `backend/tests/test_llm_infrastructure.py`
- Quick run: `cd backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py -x -q`
- Full suite: `cd backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/ -x -q`

Requirement → test mapping table:
| LLMI-01 | test_stock_analysis_model_valid, test_stock_analysis_model_invalid_karar, test_instructor_integration, test_legacy_dict_adapter |
| LLMI-02 | test_semaphore_limits_concurrency |
| LLMI-03 | test_staleness_warning_set_when_old, test_no_staleness_warning_fresh |

Phase gate condition: All 7 tests pass (not xfail) AND full `pytest tests/` suite is green.

Note on test_llm_cache.py: After Wave 1 migrates analyze() return type to StockAnalysis, test_llm_cache.py's `make_mock_response` helper must be updated — `service.client.chat.completions.create` now returns a `StockAnalysis` object (not an AsyncOpenAI response), because `_patched_client` (instructor-wrapped) is used for the API call. Wave 1 task must update test_llm_cache.py accordingly.
  </action>
  <verify>
    <automated>test -f /Users/nedimkopurlu/Downloads/PROJELER/stalize/.planning/phases/03-llm-infrastructure/03-VALIDATION.md && echo "exists"</automated>
  </verify>
  <done>03-VALIDATION.md exists and contains the requirement-to-test mapping table and phase gate condition.</done>
</task>

</tasks>

<verification>
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_llm_infrastructure.py -v 2>&1 | grep -E "XFAIL|ERROR|PASSED|FAILED|collected"
</verification>

<success_criteria>
- pytest collects exactly 7 tests from test_llm_infrastructure.py
- All 7 report xfail (exit code 0)
- No import errors or collection errors
- Existing test_llm_cache.py still passes
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-infrastructure/03-00-SUMMARY.md` with:
- What was created (test file, validation doc)
- Test names and their target requirements
- Note about test_llm_cache.py migration needed in Wave 1
</output>
