---
phase: 2
slug: ml-persistence-caching
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (existing) |
| **Config file** | `backend/pytest.ini` (exists — Wave 0 installs test files only) |
| **Quick run command** | `cd backend && pytest tests/test_ml_persistence.py tests/test_yf_cache.py tests/test_llm_cache.py -x -q` |
| **Full suite command** | `cd backend && pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Req | Test Type | Automated Command | File Exists | Status |
|---------|-----|-----------|-------------------|-------------|--------|
| save-creates-files | MLCA-01 | unit | `pytest tests/test_ml_persistence.py::test_save_creates_files -x` | ❌ W0 | ⬜ |
| load-restores-model | MLCA-01 | unit | `pytest tests/test_ml_persistence.py::test_load_restores_model -x` | ❌ W0 | ⬜ |
| first-run-saves | MLCA-01 | unit | `pytest tests/test_ml_persistence.py::test_first_run_saves_model -x` | ❌ W0 | ⬜ |
| weekly-retrain-job | MLCA-01 | unit | `pytest tests/test_ml_persistence.py::test_weekly_retrain_job -x` | ❌ W0 | ⬜ |
| price-cache-hit | MLCA-02 | unit | `pytest tests/test_yf_cache.py::test_price_cache_hit -x` | ❌ W0 | ⬜ |
| price-cache-ttl | MLCA-02 | unit | `pytest tests/test_yf_cache.py::test_price_cache_ttl -x` | ❌ W0 | ⬜ |
| info-cache-ttl | MLCA-02 | unit | `pytest tests/test_yf_cache.py::test_info_cache_ttl -x` | ❌ W0 | ⬜ |
| empty-not-cached | MLCA-02 | unit | `pytest tests/test_yf_cache.py::test_empty_not_cached -x` | ❌ W0 | ⬜ |
| llm-cache-hit | MLCA-03 | unit | `pytest tests/test_llm_cache.py::test_cache_hit_skips_api -x` | ❌ W0 | ⬜ |
| llm-cache-key | MLCA-03 | unit | `pytest tests/test_llm_cache.py::test_cache_key_format -x` | ❌ W0 | ⬜ |
| llm-cache-expiry | MLCA-03 | unit | `pytest tests/test_llm_cache.py::test_cache_expiry -x` | ❌ W0 | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_ml_persistence.py` — 4 stubs for MLCA-01
- [ ] `backend/tests/test_yf_cache.py` — 4 stubs for MLCA-02
- [ ] `backend/tests/test_llm_cache.py` — 3 stubs for MLCA-03

---

## Mock/Patch Strategy

All tests must mock external calls (no real HTTP or DB calls):

```python
# MLCA-01: mock db session to return synthetic PriceHistory rows
from unittest.mock import AsyncMock, patch, MagicMock

# MLCA-02: mock yf.Ticker to avoid real Yahoo HTTP calls
with patch("app.services.data_collector.yf.Ticker") as mock_ticker:
    mock_ticker.return_value.history.return_value = pd.DataFrame(...)

# MLCA-03: mock the AsyncOpenAI client
with patch.object(service, "client") as mock_client:
    mock_client.chat.completions.create = AsyncMock(return_value=...)
```

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Instructions |
|----------|-------------|------------|--------------|
| Restart backend, verify no retraining at startup | MLCA-01 | Requires live DB with price data | `uvicorn app.main:app`, watch logs for "loaded from disk" not "training" |
| Weekly retrain fires without manual trigger | MLCA-01 | Requires waiting for APScheduler | Check logs Sunday 02:00 or manually trigger via admin endpoint |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
