# Phase 54 — Backtest Kalitesi

## Goal

Backtest gerçekçiliğini artır: likidite katmanına göre slipaj modeli ve %0,1 komisyon ekle. Backtest sonuçlarına rejim bazlı performans kırılımı ekle (Boğa/Ayı/Yatay/Volatil dönem karşılaştırması).

## Scope

Bu faz mevcut sinyal takip altyapısını (`signal_tracking.py`, `signals.py`) genişletir — yeni bir backtesting sistemi inşa etmez. `backtester.py` bilinçli olarak devre dışı bırakılmış durumdadır ve bu fazda aktive edilmez.

## Requirements

- **BACK-01**: Slipaj modeli (BIST30: 10bps, rank 30-70: 20bps, rank 70-100: 40bps) + %0,1 komisyon her işlemde
- **BACK-02**: Sinyal kalibrasyonu sonuçlarına rejim bazlı kırılım (Boğa/Ayı/Yatay/Volatil)
- **REJ-03**: Backtest endpoint'ine opsiyonel `regime` sorgu parametresi ile filtreleme

## Key Decisions

### Slipaj Modeli (BACK-01)
- `stocks.is_bist30 = True` → 10 bps = 0.0010 slipaj
- `stocks.liquidity_score = "yüksek"` → 10 bps (BIST30 ile örtüşür)
- `stocks.liquidity_score = "orta"` → 20 bps = 0.0020
- `stocks.liquidity_score = "düşük"` → 40 bps = 0.0040
- `liquidity_score is None AND NOT is_bist30` → varsayılan 20 bps (orta kademe)
- Komisyon: %0,1 (0.001) her yönde (giriş + çıkış)
- Toplam maliyet: slipaj + komisyon (iki yönde hesaplandığında: 2 × (slipaj + 0.001))
- Maliyet, `actual_return` hesaplamalarına round-trip olarak uygulanır — snapshotlardaki mevcut fiyatlar değiştirilmez
- Net getiri: `gross_return - round_trip_cost` (round_trip_cost = 2 × (slipaj_oranı + 0.001))

### Rejim Kırılımı (BACK-02 + REJ-03)
- Her sinyal kararı tarihi, `market_regime` tablosuyla eşleştirilerek rejim etiketi eklenir
- Rejim eşleştirme: `MarketRegime.date == SignalDecisionSnapshot.decision_date`
- Eşleşme yoksa `"Bilinmiyor"` olarak etiketlenir
- `calibration_report()` yanıtına `by_regime` anahtarı eklenir
- `list_outcomes()` her kalemde `regime` alanı döner
- `GET /signals/calibration` ve `GET /signals/outcomes` endpoint'lerine `regime` sorgu parametresi eklenir

### Frontend (Plan 54-02)
- Mevcut `backtest/page.tsx` rejim kırılım tablosu ile genişletilir
- Rejim filtresi `filterBar`'a eklenir (select dropdown)
- Rejim kırılım tablosu KPI kartlarının altında, sinyal tablosunun üstünde gösterilir
- Yeni CSS sınıfları `backtest.module.css`'e eklenir

## Mevcut Altyapı

- `backend/app/services/signal_tracking.py` — `SignalTrackingService` sınıfı
- `backend/app/api/signals.py` — endpoint'ler
- `backend/app/models/signal.py` — `SignalDecisionSnapshot` ORM modeli
- `backend/app/models/market_regime.py` — `MarketRegime` ORM modeli (`date`, `regime` sütunları)
- `backend/app/models/stock.py` — `Stock.is_bist30` (Boolean) ve `Stock.liquidity_score` (String nullable)
- `frontend/src/app/backtest/page.tsx` — mevcut backtest sayfası
- `frontend/src/app/backtest/backtest.module.css` — mevcut stiller
