# Testing Patterns

**Analysis Date:** 2026-04-16

## Test Framework

**Runner:**
- None configured. No `jest.config.*`, `vitest.config.*`, or `pytest.ini` found in the project root, `frontend/`, or `backend/` (excluding `.venv`).

**Assertion Library:**
- Not applicable — no test files exist in the project source.

**Run Commands:**
```bash
# No test commands configured.
# frontend/package.json scripts: dev, build, start, lint
# No "test" script present.
```

## Test File Organization

**Location:**
- No test files exist in `frontend/src/` or `backend/app/`.
- The only `.test.*` / `.spec.*` / `test_*.py` files found are inside `backend/.venv/` (third-party package tests — not project tests).

**Naming:**
- Not applicable.

**Structure:**
- Not applicable.

## Test Structure

**Suite Organization:**
- Not established. No `describe`/`it` blocks (Jest/Vitest) or `class Test*`/`def test_*` functions (pytest) exist.

## Mocking

**Framework:**
- Not applicable — no mocking infrastructure is present.

## Fixtures and Factories

**Test Data:**
- No fixtures or factory files exist.

**Location:**
- No `fixtures/`, `factories/`, or `conftest.py` files found.

## Coverage

**Requirements:**
- None enforced. No coverage thresholds configured.

**View Coverage:**
```bash
# Not configured.
```

## Test Types

**Unit Tests:**
- Not present.

**Integration Tests:**
- Not present. The closest approximation is `backend/scripts/backtester.py` which runs historical simulations against a live database, but it is not a test suite — it has no assertions and exits via logging output.

**E2E Tests:**
- Not present. No Playwright, Cypress, or Selenium configuration found.

## What Exists Instead of Tests

**Manual validation scripts** in `backend/scripts/`:
- `backend/scripts/backtester.py` — runs a `SimpleBacktester` against the live PostgreSQL database to simulate buy signals using historical price data. No assertions, driven by `asyncio.run()`.
- `backend/scripts/initial_load.py` — data seeding script, not a test.
- `backend/scripts/update_ai.py`, `update_fundamentals.py` — maintenance scripts.
- `backend/scripts/scratch_bist.py` — exploratory/scratch script.

**FastAPI auto-docs** at `/docs` (Swagger UI) used for manual API verification.

## Guidance for Adding Tests

**If adding backend tests (recommended: pytest + httpx):**
- Place test files at `backend/tests/` (create this directory)
- Use naming: `test_<module>.py` — e.g., `test_scoring.py`, `test_endpoints.py`
- Use `pytest-asyncio` for async service tests
- Use `httpx.AsyncClient` with FastAPI `app` for endpoint tests
- Mock external calls (yfinance, KAP RSS, TCMB) to avoid network dependency

**If adding frontend tests (recommended: Vitest + Testing Library):**
- Place test files co-located with components: `src/components/ScoreRing.test.tsx`
- Or in a dedicated `src/__tests__/` directory
- Add `vitest` and `@testing-library/react` to `devDependencies`
- Add a `"test"` script to `frontend/package.json`

**Highest-priority untested code:**
- `backend/app/services/scoring.py` — `ScoringEngine.calculate_overall_score()` contains weight logic with branching (crisis mode) that is critical and entirely untested
- `backend/app/services/technical.py` — indicator calculations in `TechnicalAnalysisEngine`
- `frontend/src/components/StockHelpers.tsx` — pure utility functions (`formatPrice`, `formatVolume`, `formatMarketCap`) are ideal unit test candidates with no dependencies

---

*Testing analysis: 2026-04-16*
