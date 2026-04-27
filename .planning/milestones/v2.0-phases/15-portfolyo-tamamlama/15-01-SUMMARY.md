---
plan: 15-01
phase: 15-portfolyo-tamamlama
status: complete
implemented_by: codex
---

# Plan 15-01 Summary: Portfolio History BIST100 Benchmark

## Status: ✅ Complete (Codex tarafından uygulandı)

## Uygulanan Değişiklikler

**backend/app/api/portfolio_v2.py**
- GET /api/portfolio/history: `bist100_return` ve `portfolio_return` per day döner
- BIST100 kümülatif getirisi yfinance'den çekilir (XU100.IS) — hardcoded değil
- `active_return_spread` hesaplanır (portföy - benchmark)
- Snapshot yoksa boş liste döner (500 yok)

## Must-Have Doğrulaması

- ✅ GET /api/portfolio/history her gün için portfolio_return ve bist100_return döner
- ✅ BIST100 getirileri yfinance XU100.IS'ten çekilir
- ✅ Kümülatif getiriler ilk güne göre yüzde değerler
- ✅ Snapshot yoksa boş liste döner (hata yok)
