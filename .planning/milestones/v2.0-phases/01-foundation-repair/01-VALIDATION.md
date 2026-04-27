---
phase: 1
slug: foundation-repair
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `backend/pytest.ini` — Wave 0 installs |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| KAP-mock-removal | 01 | 1 | FOND-01 | unit | `pytest tests/test_kap_parser.py -v` | ❌ W0 | ⬜ pending |
| feedparser-startup-check | 01 | 1 | FOND-01 | unit | `pytest tests/test_startup.py -v` | ❌ W0 | ⬜ pending |
| scoring-weight-alignment | 02 | 2 | FOND-02 | unit | `pytest tests/test_scoring.py -v` | ❌ W0 | ⬜ pending |
| router-split | 03 | 2 | FOND-04 | integration | `pytest tests/test_routers.py -v` | ❌ W0 | ⬜ pending |
| deps-removal | 04 | 1 | FOND-03 | manual | `pip show tensorflow` (must fail) | N/A | ⬜ pending |
| datetime-fix | 05 | 3 | FOND-05 | unit | `pytest tests/test_models.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/__init__.py` — test package marker
- [ ] `backend/tests/conftest.py` — shared fixtures (async DB session, test app client)
- [ ] `backend/tests/test_kap_parser.py` — stubs for FOND-01 (mock removal verification)
- [ ] `backend/tests/test_startup.py` — stubs for FOND-01 (feedparser startup check)
- [ ] `backend/tests/test_scoring.py` — stubs for FOND-02 (weight config alignment)
- [ ] `backend/tests/test_routers.py` — stubs for FOND-04 (router split, endpoint reachability)
- [ ] `backend/tests/test_models.py` — stubs for FOND-05 (UTC timezone enforcement)
- [ ] `backend/pytest.ini` — pytest configuration file
- [ ] `pip install pytest pytest-asyncio httpx` — test dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| pip install without tensorflow/torch/transformers | FOND-03 | Negative assertion on package absence | `pip show tensorflow` returns error; `pip show torch` returns error; `pip show transformers` returns error |
| ALTER TABLE for model_portfolio datetime fix | FOND-05 | create_all() won't alter existing column type | Connect to dev DB, run `\d model_portfolio_history`, verify `generation_date` has `timestamp with time zone` |
| Backend startup fails without feedparser | FOND-01 | Requires uninstalling feedparser temporarily | `pip uninstall feedparser -y && uvicorn app.main:app` must exit non-zero with clear error message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
