---
phase: 04-ai-daily-briefing
plan_id: "04-00"
title: "Wave 0 — xfail test stubs"
requirement: BREF-01, BREF-02, BREF-03, BREF-04, BREF-05
wave: 0
estimated_minutes: 20
type: execute
depends_on: []
files_modified:
  - backend/tests/test_daily_briefing.py
autonomous: true
must_haves:
  truths:
    - "All BREF-01..BREF-05 test stubs exist and are marked xfail"
    - "pytest collects all tests without import errors"
    - "pytest reports xfail (not ERROR) for every stub"
  artifacts:
    - path: "backend/tests/test_daily_briefing.py"
      provides: "xfail stubs for all 8 BREF behaviors"
      min_lines: 80
  key_links:
    - from: "backend/tests/test_daily_briefing.py"
      to: "backend/app/models/model_daily_briefing.py"
      via: "import DailyBriefing (guarded by xfail)"
---

<objective>
Create the xfail test skeleton that defines the acceptance criteria for every BREF requirement before any production code is written. These stubs turn RED (xfail) now and GREEN (xpass) as waves 1-3 are implemented.

Purpose: Red-first contracts that prevent regressions and prove each requirement is met.
Output: `backend/tests/test_daily_briefing.py` with 8 xfail stubs.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/phases/04-ai-daily-briefing/04-CONTEXT.md
@.planning/phases/04-ai-daily-briefing/RESEARCH.md
@backend/pytest.ini
@backend/tests/conftest.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write xfail test stubs for all BREF behaviors</name>
  <files>backend/tests/test_daily_briefing.py</files>
  <action>
Create `backend/tests/test_daily_briefing.py` with exactly these 8 xfail stubs. Each stub is decorated with `@pytest.mark.xfail(reason="...", strict=False)` so it shows as `xfail` (not error) before implementation and `xpass` after.

Do NOT import production modules at module level — wrap imports inside each test function body so collection succeeds even when the modules do not exist yet.

```python
"""
Phase 4: AI Daily Briefing — xfail test stubs.

Each test defines acceptance criteria for one BREF requirement.
Status before implementation: xfail (expected).
Status after wave implementation: xpass (passes).

Run: cd backend && python -m pytest tests/test_daily_briefing.py -x -q
"""
import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ─────────────────────────────────────────────────────────
# BREF-02: ORM model fields
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 1: model_daily_briefing.py not yet created", strict=False)
def test_daily_briefing_model_fields():
    """DailyBriefing ORM has all required columns."""
    from app.models.model_daily_briefing import DailyBriefing
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(DailyBriefing)
    column_names = {c.key for c in mapper.mapper.column_attrs}
    required = {
        "id", "date", "kap_summary", "price_summary", "macro_summary",
        "notable_stocks", "ai_commentary", "created_at", "generation_duration_ms",
    }
    assert required.issubset(column_names), f"Missing columns: {required - column_names}"


# ─────────────────────────────────────────────────────────
# BREF-02: GET /api/briefing/today — 404 when no record
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 1: briefing.py router not yet created", strict=False)
@pytest.mark.asyncio
async def test_briefing_today_endpoint_404():
    """GET /api/briefing/today returns 404 when no briefing record exists for today."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from unittest.mock import patch, AsyncMock

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    with patch("app.api.briefing.get_db") as mock_get_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_get_db.return_value = mock_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/briefing/today")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Brifing henüz üretilmedi"


# ─────────────────────────────────────────────────────────
# BREF-02: GET /api/briefing/today — 200 with data + X-Cache header
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 1: briefing.py router not yet created", strict=False)
@pytest.mark.asyncio
async def test_briefing_today_endpoint_200():
    """GET /api/briefing/today returns 200 with briefing data and X-Cache: HIT header."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    fake_briefing = MagicMock()
    fake_briefing.date = datetime.date.today()
    fake_briefing.kap_summary = "Test KAP özeti"
    fake_briefing.price_summary = "Test fiyat özeti"
    fake_briefing.macro_summary = "Test makro özeti"
    fake_briefing.notable_stocks = []
    fake_briefing.ai_commentary = {"risk_summary": "Düşük risk", "opportunities": [], "watch_list": []}
    fake_briefing.created_at = datetime.datetime.now(datetime.timezone.utc)
    fake_briefing.generation_duration_ms = 4200

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_briefing

    with patch("app.api.briefing.get_db") as mock_get_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_get_db.return_value = mock_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/briefing/today")

    assert response.status_code == 200
    assert response.headers.get("x-cache") == "HIT"
    body = response.json()
    assert "kap_summary" in body
    assert "ai_commentary" in body


# ─────────────────────────────────────────────────────────
# BREF-04: Notable stocks algorithm
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 2: briefing_generator.py not yet created", strict=False)
def test_notable_stocks_algorithm():
    """
    Stocks with volume > 2x 20-day avg OR abs(daily_change_pct) > 3.0
    are flagged as notable. Stocks below both thresholds are excluded.
    """
    from app.services.briefing_generator import _is_notable_stock

    # Volume anomaly only
    assert _is_notable_stock(volume=1_000_000, avg_volume_20d=400_000, daily_change_pct=0.5) is True
    # Price move only
    assert _is_notable_stock(volume=100_000, avg_volume_20d=200_000, daily_change_pct=-3.5) is True
    # Both thresholds met
    assert _is_notable_stock(volume=900_000, avg_volume_20d=400_000, daily_change_pct=4.0) is True
    # Neither threshold — excluded
    assert _is_notable_stock(volume=100_000, avg_volume_20d=200_000, daily_change_pct=1.0) is False
    # Exactly at boundary (not over) — excluded
    assert _is_notable_stock(volume=800_000, avg_volume_20d=400_000, daily_change_pct=3.0) is False


# ─────────────────────────────────────────────────────────
# BREF-05: DailyCommentary Pydantic model
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 2: briefing_generator.py (DailyCommentary) not yet created", strict=False)
def test_daily_commentary_model():
    """DailyCommentary Pydantic model validates required fields correctly."""
    from app.services.briefing_generator import DailyCommentary

    valid = DailyCommentary(
        risk_summary="Yüksek döviz volatilitesi risk oluşturuyor.",
        opportunities=["THYAO", "GARAN"],
        watch_list=["EREGL — demir fiyatı baskısı", "AKBNK — kur riski"],
    )
    assert valid.risk_summary.startswith("Yüksek")
    assert "THYAO" in valid.opportunities
    assert len(valid.watch_list) == 2

    # Missing required field raises ValidationError
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        DailyCommentary(
            risk_summary="Only this field",
            # opportunities and watch_list missing
        )


# ─────────────────────────────────────────────────────────
# BREF-01: APScheduler cron registered with correct timezone
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 3: APScheduler cron not yet registered in main.py", strict=False)
def test_briefing_cron_registered():
    """APScheduler has a job named 'generate_daily_briefing' with timezone Europe/Istanbul."""
    from app.main import scheduler

    job_funcs = [job.func.__name__ for job in scheduler.get_jobs()]
    assert "generate_daily_briefing" in job_funcs, (
        f"No job named 'generate_daily_briefing' in scheduler. Found: {job_funcs}"
    )

    # Find the job and check its trigger timezone
    briefing_job = next(j for j in scheduler.get_jobs() if j.func.__name__ == "generate_daily_briefing")
    trigger = briefing_job.trigger
    # APScheduler CronTrigger stores timezone as pytz/zoneinfo object
    tz_str = str(trigger.timezone)
    assert "Istanbul" in tz_str, f"Expected Europe/Istanbul timezone, got: {tz_str}"


# ─────────────────────────────────────────────────────────
# BREF-02: Upsert idempotency (second insert with same date = no duplicate)
# ─────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="Wave 3: _upsert_briefing not yet implemented", strict=False)
@pytest.mark.asyncio
async def test_briefing_upsert():
    """
    Calling _upsert_briefing twice with the same date does not create a duplicate row.
    Uses a real AsyncSessionLocal against the test database (or mocks the execute call).
    """
    from unittest.mock import patch, AsyncMock, MagicMock

    # Mock the DB session so no real DB is needed
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    with patch("app.services.briefing_generator.AsyncSessionLocal", return_value=mock_session):
        from app.services.briefing_generator import _upsert_briefing

        payload = dict(
            date=datetime.date.today(),
            kap_summary="KAP test",
            price_summary="Fiyat test",
            macro_summary="Makro test",
            notable_stocks=[],
            ai_commentary=None,
            generation_duration_ms=999,
        )
        # First upsert
        await _upsert_briefing(**payload)
        # Second upsert — same date, should not raise, should call ON CONFLICT DO UPDATE
        await _upsert_briefing(**payload)

    # execute was called twice (once per upsert)
    assert mock_session.execute.call_count == 2
    # commit was called twice
    assert mock_session.commit.call_count == 2
```

Verify: `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py --collect-only -q 2>&1 | head -30` should show 8 tests collected with no collection errors (tests will show as xfail when run).
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py -q 2>&1 | tail -10</automated>
  </verify>
  <done>
    - pytest collects 8 tests without ImportError or SyntaxError
    - All 8 tests report xfail (not ERROR, not FAILED)
    - No production modules need to exist for collection to succeed
  </done>
</task>

</tasks>

<verification>
Run: `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend && /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m pytest tests/test_daily_briefing.py -v`

Expected output: 8 tests, all `XFAIL`. Zero `ERROR`. Zero `FAILED`.
</verification>

<success_criteria>
- `backend/tests/test_daily_briefing.py` exists with 8 xfail stubs
- `pytest --collect-only` lists all 8 without collection errors
- `pytest` run reports `8 xfailed` with no errors
- Stubs cover BREF-01, BREF-02 (model + 404 + 200), BREF-03/04 (notable_stocks), BREF-05 (DailyCommentary), BREF-01 (scheduler), BREF-02 (upsert)
</success_criteria>

<rollback>
Delete `backend/tests/test_daily_briefing.py`. No production code is touched in this wave.
</rollback>

<output>
After completion, create `.planning/phases/04-ai-daily-briefing/plans/04-00-SUMMARY.md` with:
- Files created: `backend/tests/test_daily_briefing.py`
- Test count: 8 xfail stubs
- Stubs cover: BREF-01 through BREF-05
</output>
