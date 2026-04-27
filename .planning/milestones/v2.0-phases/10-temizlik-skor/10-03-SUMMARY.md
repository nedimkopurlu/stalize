---
plan: 10-03
phase: 10
subsystem: scoring
tags: [scoring, config, cleanup, weights, requirements]
dependency_graph:
  requires: [10-01, 10-02]
  provides: [clean-scoring-engine, rebalanced-weights, lean-requirements]
  affects: [backend/app/services/scoring.py, backend/app/core/config.py, backend/requirements.txt]
tech_stack:
  added: []
  patterns: [weighted-average-normalization, config-driven-weights]
key_files:
  created: []
  modified:
    - backend/app/core/config.py
    - backend/app/services/scoring.py
    - backend/requirements.txt
    - backend/tests/test_scoring.py
decisions:
  - "extra='ignore' added to Settings.Config so removed env vars in .env (DEEPSEEK_API_KEY, LLM_MODEL) do not cause pydantic ValidationError"
  - "diskcache==5.6.3 retained — still actively used in data_collector.py for yfinance result-level caching"
  - "GUCLU AL/AL/TUT/SAT/GUCLU SAT ASCII names used in scoring.py (no Turkish characters) for consistent DB storage"
  - "scoring.py _resolve_weights() now takes no stock argument — crisis mode removed (required causal_score which is gone)"
  - "ML/causal columns (ml_score, causal_score) retained in Stock model — not scored, not deleted (10-02 decision preserved)"
metrics:
  duration_minutes: 10
  completed_date: "2026-04-20"
  tasks_completed: 2
  files_modified: 4
requirements_satisfied: [MIDT-02, CLEN-04]
---

# Phase 10 Plan 03: Scoring Yeniden Yapilandirma ve requirements.txt Temizligi Summary

Scoring engine rewritten to use three real signal layers (Fundamental 45% / Technical 40% / News 15%); ML and LLM weight constants removed from config; xgboost, shap, instructor removed from requirements.txt — system is now pure data-analysis with no ML/LLM dependencies.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 RED | Failing scoring tests | 191059c5 | tests/test_scoring.py |
| 1 GREEN | config.py + scoring.py rewrite | 18b95e56 | app/core/config.py, app/services/scoring.py |
| 2 | requirements.txt cleanup | fcec8c7a | requirements.txt |

## Changes

### config.py — Ensemble Weights (MIDT-02)

**Removed:**
- `WEIGHT_ML = 0.20`, `WEIGHT_CAUSAL = 0.15`, `WEIGHT_MACRO = 0.10`, `WEIGHT_SENTIMENT = 0.10`
- LLM constants: `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `LLM_MODEL`, `LLM_ENABLED`
- ML constants: `ML_MODEL_DIR`, `LSTM_WINDOW_SIZE`, `LSTM_EPOCHS`, `XGBOOST_N_ESTIMATORS`
- `KNOWLEDGE_DIR`

**Added:**
```python
# Ensemble Weights — Orta vadeli yatirimci odagi (MIDT-02)
WEIGHT_FUNDAMENTAL: float = 0.45  # Temel analiz: F/K, PD/DD, ROE, marj
WEIGHT_TECHNICAL: float = 0.40    # Teknik analiz: EMA, ATR, RSI, hacim, divergence
WEIGHT_NEWS: float = 0.15         # Haber etkisi: KAP, TCMB, TUIK duygu
```

Sum: 0.45 + 0.40 + 0.15 = 1.0

### scoring.py — Engine Rewrite (MIDT-02)

**Removed:** `_resolve_weights(stock)` crisis mode (needed `causal_score`), 6-weight calculation, `ml_score`/`causal_score`/`macro_score` references.

**New `calculate_overall_score()` behavior:**
- Reads `stock.fundamental_score`, `stock.technical_score`, `stock.sentiment_score`
- Missing scores → weight normalized across available scores
- All None → returns `(50.0, "TUT")` default
- Clamped to `[0.0, 100.0]`
- Thresholds: `>= 80` GUCLU AL, `>= 65` AL, `>= 45` TUT, `>= 25` SAT, `< 25` GUCLU SAT

**Verification:** `calculate_overall_score(fundamental=80, technical=60, sentiment=40)` = **66.0 (AL)** ✓

### requirements.txt — ML/LLM Removal (CLEN-04)

**Removed:**
- `xgboost==2.1.4` — ML engine deleted in 10-02
- `shap==0.46.0` — XGBoost explainability, no longer needed
- `instructor==1.15.1` — LLM structured output, AI layer removed
- `# NLP & Sentiment` section header

**Retained:**
- `diskcache==5.6.3` — still used in `data_collector.py` for yfinance caching
- `scikit-learn==1.6.1` — used in technical/fundamental scoring helpers

## Verification Results

```
28 passed, 1 xfailed, 1 xpassed in 2.22s
Agirliklar OK: F=0.45 T=0.40 N=0.15
Skor OK: 66.0 (AL)
scoring.py temiz (no ml_score/causal_score references)
requirements.txt temiz (no xgboost/shap/instructor)
pip install --dry-run: OK
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pydantic ValidationError for removed env vars**
- **Found during:** Task 1 GREEN (first pytest run)
- **Issue:** DEEPSEEK_API_KEY in .env caused `extra_forbidden` ValidationError after removing the field from Settings
- **Fix:** Added `extra = "ignore"` to `Settings.Config` class — extra env vars are silently ignored
- **Files modified:** `backend/app/core/config.py`
- **Commit:** 18b95e56

## Phase 10 Completion Note

Phase 10 (Temizlik & Skor Yeniden Yapilandirma) is now fully complete:
- **10-01:** AI/LLM layer deleted (DailyBriefing, causal engine, DeepSeek scheduler)
- **10-02:** XGBoost ML engine deleted, mock portfolio routes removed
- **10-03:** Scoring weights rebalanced, config cleaned, requirements.txt lean

The codebase is now pure data analysis: Fundamental + Technical + News, no ML/LLM overhead.

## Known Stubs

None — scoring engine is fully wired with real weights and correct normalization logic.

## Self-Check: PASSED

Files verified:
- FOUND: backend/app/core/config.py (WEIGHT_FUNDAMENTAL=0.45, WEIGHT_TECHNICAL=0.40, WEIGHT_NEWS=0.15)
- FOUND: backend/app/services/scoring.py (no ml_score/causal_score references)
- FOUND: backend/requirements.txt (no xgboost/shap/instructor)
- FOUND: backend/tests/test_scoring.py (17 tests, all passing)

Commits verified:
- 191059c5: test(10-03) RED stubs
- 18b95e56: feat(10-03) config.py + scoring.py GREEN
- fcec8c7a: chore(10-03) requirements.txt cleanup
