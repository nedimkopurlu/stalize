---
phase: 47-i-lem-disiplini-g-nl
plan: "01"
subsystem: backend-portfolio
tags: [orm, migration, api, discipline, portfolio]
dependency_graph:
  requires: []
  provides: [exit_reason-field, invalidation_condition-field, 007-migration]
  affects: [portfolio_v2-api, portfolio_positions-table]
tech_stack:
  added: []
  patterns: [inspector-pattern-idempotent-migration]
key_files:
  created:
    - backend/alembic/versions/007_portfolio_position_discipline_fields.py
  modified:
    - backend/app/models/portfolio_v2.py
    - backend/app/api/portfolio_v2.py
decisions:
  - "exit_reason sütunu String(50) olarak tanımlandı — kısa enum-benzeri değerlere yönelik"
  - "invalidation_condition sütunu Text olarak tanımlandı — serbest metin senaryosu için"
  - "006 migration'ının inspector pattern'i aynen tekrar kullanıldı (idempotent)"
metrics:
  duration_minutes: 5
  completed_date: "2026-05-14"
  tasks_completed: 3
  files_changed: 3
---

# Phase 47 Plan 01: Backend İşlem Disiplini Alanları Özeti

**One-liner:** PortfolioPosition ORM modeline exit_reason (String 50) ve invalidation_condition (Text) sütunları eklendi; 007 Alembic migration ve API endpoint güncellemeleriyle GUNLUK-01/02 backend desteği tamamlandı.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ORM modeline iki yeni sütun ekle | af30a3e | backend/app/models/portfolio_v2.py |
| 2 | Alembic migration dosyası oluştur | ff0e8be | backend/alembic/versions/007_portfolio_position_discipline_fields.py |
| 3 | API endpoint'lerini güncelle | 1d830ac | backend/app/api/portfolio_v2.py |

## What Was Built

### ORM Model (portfolio_v2.py)
`PortfolioPosition` sınıfına iki yeni nullable sütun eklendi:
- `exit_reason = Column(String(50), nullable=True)` — çıkış nedeni etiketi (Stop Tetiklendi / Hedefe Ulaştı / Senaryo Bozuldu / Diğer)
- `invalidation_condition = Column(Text, nullable=True)` — kararı bozan koşul serbest metni

### Migration (007)
Inspector pattern ile idempotent upgrade: sütun yoksa ekle, varsa atla. 006→007 zinciri doğru. Mevcut kayıtlar bozulmaz.

### API Endpoints (portfolio_v2.py)
- `PositionCreate`: `invalidation_condition: Optional[str] = None` eklendi
- `PositionClose`: `exit_reason: Optional[str] = None` eklendi
- `add_position`: `invalidation_condition=body.invalidation_condition` ORM constructor'a aktarılıyor
- `close_position`: `pos.exit_reason = body.exit_reason` atanıyor
- `get_positions`: serialization dict'e `"exit_reason"` ve `"invalidation_condition"` eklendi

## Deviations from Plan

None — plan tam olarak yazıldığı gibi uygulandı.

## Known Stubs

None — tüm alanlar gerçek DB sütunlarına bağlı, frontend plan (47-02) bu değerleri okuyup yazacak.

## Self-Check: PASSED

- backend/app/models/portfolio_v2.py: FOUND, exit_reason ve invalidation_condition sütunları mevcut
- backend/alembic/versions/007_portfolio_position_discipline_fields.py: FOUND, syntax OK, down_revision="006"
- backend/app/api/portfolio_v2.py: FOUND, Pydantic modelleri yeni alanları kabul ediyor
- Commits: af30a3e, ff0e8be, 1d830ac — tamamı mevcut
