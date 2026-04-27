---
plan: 11-02
phase: 11-model-portfolyo-backend
status: complete
implemented_by: codex
---

# Plan 11-02 Summary: Günlük Snapshot APScheduler Job

## Status: ✅ Complete (Codex tarafından uygulandı)

## Uygulanan Değişiklikler

**backend/app/services/portfolio_snapshot.py**
- `take_daily_snapshot()`: Aktif pozisyonların gerçek yfinance kapanış fiyatlarını çeker
- `_fetch_close_price()`: `run_in_executor` ile async yfinance çağrısı (TECH-02 pattern)
- Upsert mantığı: aynı gün iki kez çalışırsa mükerrer kayıt oluşturmaz
- Aktif pozisyon yoksa sessizce çıkar
- `source_health` entegrasyonu: başarı/başarısızlık kaydı

**backend/app/main.py**
- APScheduler job: `take_daily_snapshot`, cron, mon-fri, 18:30 Europe/Istanbul

## Must-Have Doğrulaması

- ✅ APScheduler job hafta içi 18:30 İstanbul saatinde otomatik çalışır
- ✅ yfinance çağrısı `run_in_executor` ile — event loop bloke olmaz
- ✅ Günlük P&L yüzdesi hesaplanır ve portfolio_daily_snapshots'a kaydedilir
- ✅ Aynı gün iki kez çalışırsa upsert yapar (select + insert/update logic)
- ✅ Aktif pozisyon yoksa sessizce çıkar
