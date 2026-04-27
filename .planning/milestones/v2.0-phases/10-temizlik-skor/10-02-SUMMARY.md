---
plan: 10-02
phase: 10
subsystem: backend
tags: [cleanup, ml-removal, portfolio-removal, xgboost, deletion]
dependency_graph:
  requires: [10-01]
  provides: [clean-main-no-ml-portfolio, AIRF-03, AIRF-04]
  affects:
    - backend/app/main.py
    - backend/app/models/__init__.py
    - backend/app/models/stock.py
tech_stack:
  added: []
  patterns: []
key_files:
  deleted:
    - backend/app/services/ml.py
    - backend/app/api/portfolio.py
    - backend/app/services/performance_monitor.py
    - backend/app/services/portfolio_optimizer.py
    - backend/app/models/portfolio.py
    - backend/tests/test_ml_persistence.py
    - backend/tests/test_ml_no_double_count.py
  modified:
    - backend/app/main.py
    - backend/app/models/__init__.py
    - backend/app/models/stock.py
decisions:
  - "[10-02]: models/portfolio.py deleted — PortfolioItem is Phase 11 scope; stock.py relationship and __init__.py export also removed for clean import"
  - "[10-02]: services/portfolio.py was never committed to git (untracked) — deleted from disk only"
  - "[10-02]: performance_monitor.py and portfolio_optimizer.py were untracked — deleted from disk only"
metrics:
  duration_min: 12
  completed_date: "2026-04-20"
  tasks_completed: 2
  files_changed: 8
---

# Phase 10 Plan 02: XGBoost ML ve Mock Portfolio Backend Kaldirma Summary

**One-liner:** XGBoost ML engine (ml.py + 2 test files) ve mock portfolio backend (4 service/api files) silindi; main.py ML preload + retrain + portfolio scheduler + router referanslarindan tamizlandi.

## What Was Done

### Task 1: XGBoost ML Dosyalari Silindi — Commit b509737e

**Silinen dosyalar:**
- `backend/app/services/ml.py` — XGBoost ml_engine singleton (preload, retrain, predict)
- `backend/tests/test_ml_persistence.py` — ML persistence testleri
- `backend/tests/test_ml_no_double_count.py` — ML double-count testi

**main.py degisiklikleri:**
- `background_xgb_retrain()` async fonksiyonu tamamen silindi
- Lifespan icindeki `ml_engine.preload_all_models()` blogu silindi
- `scheduler.add_job(background_xgb_retrain, ...)` satiri silindi

### Task 2: Mock Portfolio Backend Silindi — Commit 604583f4

**Silinen dosyalar:**
- `backend/app/api/portfolio.py` — mock portfolio router (GET /api/portfolio/*)
- `backend/app/services/performance_monitor.py` — AI audit ve ogrenme servisi
- `backend/app/services/portfolio_optimizer.py` — model portfolio optimizer
- `backend/app/models/portfolio.py` — PortfolioItem ORM modeli (Phase 11'de yeniden yazilacak)
- `backend/app/services/portfolio.py` — daha once silinmis, disk'te yoktu

**main.py degisiklikleri:**
- `from app.api import stocks, macro, portfolio, intelligence, admin` → `portfolio` cikarildi
- `background_audit_and_learn()` fonksiyonu tamamen silindi
- `background_model_portfolio_generation()` fonksiyonu tamamen silindi
- `scheduler.add_job(background_audit_and_learn, ...)` satiri silindi (18:05)
- `scheduler.add_job(background_model_portfolio_generation, ...)` satiri silindi (18:15)
- `app.include_router(portfolio.router, prefix="/api")` satiri silindi
- Logging mesaji guncellendi: Audit ve Portfolio referanslari cikarildi

**Auto-fix (Rule 1+2) degisiklikleri:**
- `backend/app/models/__init__.py` — `PortfolioItem` import ve export satirlari silindi
- `backend/app/models/stock.py` — `portfolio_items` relationship satiri silindi

## Remaining Scheduler Jobs (Sadece Tutulacaklar)

| Job | Trigger | Aciklama |
|-----|---------|----------|
| background_kap_scan | interval, KAP_SCAN_INTERVAL_MIN dk | KAP anlik bildirim taramasi |
| background_tcmb_scan | interval, 2h | TCMB makro veri taramasi |
| background_tuik_scan | cron, mon-fri 09:00 | TUIK ekonomik veri taramasi |
| background_dynamic_correlation | cron, mon 09:30 | Dinamik korelasyon matrisi |

ML ve portfolio ile ilgili hic job kalmadi.

## Verification Results

```
DELETED OK: app/services/ml.py
DELETED OK: app/api/portfolio.py
DELETED OK: app/services/portfolio.py
DELETED OK: app/services/performance_monitor.py
DELETED OK: app/services/portfolio_optimizer.py
DELETED OK: tests/test_ml_persistence.py
DELETED OK: tests/test_ml_no_double_count.py

app import OK

main.py clean (no portfolio/ML refs)

Tests: 11 passed, 1 xfailed, 4 xpassed — all OK
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] models/__init__.py PortfolioItem import kaldirildi**
- **Found during:** Task 2
- **Issue:** models/portfolio.py silindikten sonra `from app.models.portfolio import PortfolioItem` import satiri ImportError olusturuyordu
- **Fix:** `models/__init__.py`'den import ve `__all__` listesinden PortfolioItem cikarildi
- **Files modified:** `backend/app/models/__init__.py`
- **Commit:** 604583f4

**2. [Rule 1 - Bug] stock.py PortfolioItem relationship kaldirildi**
- **Found during:** Task 2
- **Issue:** `PortfolioItem` modeli silinince `stock.py`'deki `portfolio_items = relationship("PortfolioItem", ...)` satiri SQLAlchemy runtime hatasi veriyordu
- **Fix:** `stock.py`'den `portfolio_items` relationship satiri silindi
- **Files modified:** `backend/app/models/stock.py`
- **Commit:** 604583f4

## Known Stubs

None — bu plan sadece silme islemleri yapiyor, yeni kod yazmiyor.

## Self-Check: PASSED

- app/services/ml.py: DELETED
- app/api/portfolio.py: DELETED
- app/services/performance_monitor.py: DELETED from disk (was untracked)
- app/services/portfolio_optimizer.py: DELETED from disk (was untracked)
- app/models/portfolio.py: DELETED from disk (was untracked)
- tests/test_ml_persistence.py: DELETED
- tests/test_ml_no_double_count.py: DELETED
- main.py: CLEAN (no ML/portfolio refs, syntax OK, imports OK)
- Commit b509737e: EXISTS (Task 1 — ML deletion)
- Commit 604583f4: EXISTS (Task 2 — portfolio deletion)
