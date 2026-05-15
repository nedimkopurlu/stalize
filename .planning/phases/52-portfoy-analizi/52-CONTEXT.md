# Phase 52 — Portföy Analizi — Context

## Goal

Kullanıcı, portföyünün piyasaya karşı betasını, pozisyonlar arası korelasyon matrisini ve volatilite bazlı pozisyon büyüklüğü önerisini portföy sayfasında görür.

## Requirements

- **PORT-01**: Portföy beta vs BIST100 — 252 günlük pencere, [0, 3] aralığına kırpılmış; beta > 1 ise "Piyasadan Daha Volatil" uyarısı.
- **PORT-02**: Pozisyonlar arası korelasyon matrisi — 90 günlük pencere; r > 0.7 çiftleri vurgulanır; < 20 veri noktası olan hisseler dışlanır.
- **PORT-03**: Volatilite bazlı pozisyon büyüklüğü önerisi — hisse detay sayfasında; %1-2 risk kuralı, ATR×2 stop mesafesi; `GET /stocks/{symbol}/position-size?portfolio_value=N`.

## Key Decisions (Autonomous)

### Beta Hesabı (PORT-01)
- Endpoint: `GET /portfolio/analytics` — `{beta, correlation_matrix, calculated_at}` döner
- 252 günlük günlük getiri: aktif pozisyonların ağırlıklı toplamı (pozisyon değerine göre ağırlık)
- Benchmark: `XU100.IS` — önce `CommodityPrice` tablosundan, yoksa yfinance fallback (zaten `_fetch_benchmark_history()` var)
- Formül: `beta = cov(portfolio_returns, index_returns) / var(index_returns)`; clamp `[0, 3]`
- Kütüphane: salt numpy (zaten requirements.txt'te)
- Veri kaynağı: `PriceHistory` tablosu (Stock ORM üzerinden join)

### Korelasyon Matrisi (PORT-02)
- Aynı endpoint `/portfolio/analytics` — `correlation_matrix: {symbols, matrix}` eklenir
- Format: `{symbols: ["THYAO", "GARAN", ...], matrix: [[1.0, 0.45], [0.45, 1.0]]}` (NxN)
- 90 günlük günlük getiri korelasyonu (numpy.corrcoef)
- Veri < 20 gün olan hisse matristen dışlanır, endpoint'te `excluded_symbols: list[str]` not eklenir

### Pozisyon Büyüklüğü (PORT-03)
- Yeni endpoint: `GET /stocks/{symbol}/position-size?portfolio_value=N`
- 14-günlük ATR — `PriceHistory.atr_14` sütunu kullanılır (zaten hesaplanmış, PriceHistory ORM'de var)
- Stop mesafesi: `ATR × 2`
- Risk miktarı: `portfolio_value × 0.01` (%1) ve `portfolio_value × 0.02` (%2)
- Max lot: `risk_amount / stop_distance` (tam sayıya yuvarlanır)
- Endpoint `backend/app/api/stocks.py` router'ına eklenir (GET /stocks/{symbol}/... pattern'iyle uyumlu)
- Frontend: hisse detay sayfasında "Pozisyon Büyüklüğü Rehberi" kartı; portfolio_value mevcut portföy değerinden otomatik hesaplanır

## Architecture Notes

### Backend
- `backend/app/api/portfolio_v2.py` — `/portfolio/analytics` endpoint'i buraya eklenir
- `backend/app/api/stocks.py` — `/stocks/{symbol}/position-size` endpoint'i buraya eklenir
- `_fetch_benchmark_history()` fonksiyonu portfolio_v2.py'da zaten mevcut — beta hesabında yeniden kullanılır
- `PriceHistory.atr_14` sütunu zaten mevcut — ATR için yeni hesap gerekmez
- `CommodityPrice` (XU100.IS) zaten portfolio_v2.py'da kullanılıyor

### Frontend
- `frontend/src/lib/api.ts` — 2 yeni interface + 2 yeni api metodu
- `frontend/src/app/portfolio/page.tsx` — beta + korelasyon matrisi bölümleri eklenir
- `frontend/src/app/stocks/[symbol]/page.tsx` — pozisyon büyüklüğü kartı eklenir
- CSS: `page.module.css` dosyaları (mevcut class pattern'ler takip edilir)

## Plan Structure

- **Plan 52-01 (Wave 1)**: Backend — `GET /portfolio/analytics` (beta + korelasyon) + `GET /stocks/{symbol}/position-size`
- **Plan 52-02 (Wave 2)**: Frontend — api.ts tipleri + portföy sayfası (beta + korelasyon matrisi) + hisse detay sayfası (pozisyon büyüklüğü)
