"""
Phase 6 — TECH-01: APScheduler Overlap Protection Tests.

Asserts that every scheduler job registered in app.main has:
  - max_instances = 1   (no concurrent execution of the same job)
  - misfire_grace_time = 300  (5-minute grace window for missed fires)

Run: cd backend && python -m pytest tests/test_scheduler_overlap.py -x -v
RED: before main.py is updated (no kwargs present yet)
GREEN: after main.py is updated with both kwargs on all 10 add_job() calls
"""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Helper: enumerate jobs after lifespan startup
# ─────────────────────────────────────────────────────────────────────────────

async def _get_all_jobs_via_lifespan():
    """
    Start the FastAPI lifespan, capture all scheduler jobs, then shut down.
    Returns list of APScheduler Job objects visible inside lifespan context.
    """
    from app.main import app, scheduler

    # Patch heavy async side-effects that are irrelevant to scheduler job registration
    with patch("app.core.database.async_engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_engine.dispose = AsyncMock()

        async with app.router.lifespan_context(app):
            jobs = scheduler.get_jobs()
            return list(jobs)


# ─────────────────────────────────────────────────────────────────────────────
# TECH-01 Test 1: max_instances == 1 on every job
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_jobs_have_max_instances_one():
    """
    Every APScheduler job registered in app.main must have max_instances == 1.
    This prevents two back-to-back fires of the same job from running concurrently.
    """
    jobs = await _get_all_jobs_via_lifespan()
    assert len(jobs) > 0, "No scheduler jobs found — is lifespan running correctly?"

    failing_jobs = [
        (job.func.__name__, getattr(job, "max_instances", None))
        for job in jobs
        if getattr(job, "max_instances", None) != 1
    ]
    assert not failing_jobs, (
        f"The following jobs do NOT have max_instances=1: {failing_jobs}\n"
        "Fix: add max_instances=1 to every scheduler.add_job() call in backend/app/main.py"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TECH-01 Test 2: misfire_grace_time == 300 on every job
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_jobs_have_misfire_grace():
    """
    Every APScheduler job registered in app.main must have misfire_grace_time == 300.
    This gives a 5-minute window before a missed fire is abandoned.
    """
    jobs = await _get_all_jobs_via_lifespan()
    assert len(jobs) > 0, "No scheduler jobs found — is lifespan running correctly?"

    failing_jobs = [
        (job.func.__name__, getattr(job, "misfire_grace_time", None))
        for job in jobs
        if getattr(job, "misfire_grace_time", None) != 300
    ]
    assert not failing_jobs, (
        f"The following jobs do NOT have misfire_grace_time=300: {failing_jobs}\n"
        "Fix: add misfire_grace_time=300 to every scheduler.add_job() call in backend/app/main.py"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TECH-01 Test 3: no removed briefing job is registered
# ─────────────────────────────────────────────────────────────────────────────

def test_removed_briefing_job_not_registered():
    """The removed briefing job must not be registered."""
    from app.main import scheduler

    job_funcs = [job.func.__name__ for job in scheduler.get_jobs()]
    assert "generate_daily_briefing" not in job_funcs


@pytest.mark.asyncio
async def test_planned_tefas_source_is_not_scheduled():
    """TEFAS is on-demand while its bulk endpoint is disabled, so it must not run in the scheduler."""
    jobs = await _get_all_jobs_via_lifespan()
    job_funcs = [job.func.__name__ for job in jobs]
    assert "background_tefas_scan" not in job_funcs


@pytest.mark.asyncio
async def test_model_portfolio_generation_not_intraday_forced():
    """Weekly model portfolio selection must not churn every few minutes."""
    jobs = await _get_all_jobs_via_lifespan()
    job = next(job for job in jobs if job.func.__name__ == "background_model_portfolio_generate")
    assert getattr(job.trigger, "interval", None) >= timedelta(hours=6)
