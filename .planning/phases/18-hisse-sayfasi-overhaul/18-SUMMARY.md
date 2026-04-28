# Phase 18: Hisse Sayfası Overhaul — SUMMARY

**Completed:** 2026-04-28

## What Was Built

- **EV/EBITDA (FD/FAVÖK)**: Backend `/fundamentals` endpoint'e eklendi; FundamentalMetricCard'a yeni satır eklendi
- **TradingView widget**: `BIST:SYMBOL` formatında, dark theme, 500px yükseklikte iframe; mevcut CandlestickEMAPanel'in üzerinde
- **Rakip karşılaştırma**: Yeni `/stocks/{symbol}/peers` backend endpoint; aynı sektörden 5 hisse market_cap'e göre sıralı; CompetitorTable JSX bileşeni stock detail sayfasında
- **KAP haberleri**: 5 → 10 bildirim artırıldı
- **StockPeer tipi**: api.ts'e eklendi

## Files Modified
- `backend/app/api/stocks.py` (ev_ebitda + /peers endpoint)
- `frontend/src/lib/api.ts` (StockFundamentals.ev_ebitda, StockPeer, StockPeersResponse, getStockPeers)
- `frontend/src/components/FundamentalMetricCard.tsx` (EV/EBITDA satırı)
- `frontend/src/app/stocks/[symbol]/page.tsx` (TradingView, peers, 10 news)
