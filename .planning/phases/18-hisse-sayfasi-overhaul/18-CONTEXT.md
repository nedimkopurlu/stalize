# Phase 18: Hisse Sayfası Overhaul — Context

**Status:** Ready for execution

## Existing State
Stock detail page (`/stocks/[symbol]/page.tsx`) already has:
- CandlestickEMAPanel with EMA 50/200 overlay
- FundamentalMetricCard (F/K, PD/DD, ROE, Net Marj, Borç/Özsermaye)
- KAPNewsCard (shows 5 items)
- ScoreLayerPanel + full score breakdown
- Risk levels (stop-loss, target, support, resistance)
- Technical signals list

## What Needs to Be Added

### 18-01: TradingView Widget
- Add TradingView Advanced Chart iframe alongside existing CandlestickEMAPanel
- Symbol format: `BIST:SYMBOL` (e.g. BIST:AKBNK)
- Embed URL: TradingView's public widget embed

### 18-02: EV/EBITDA in Fundamentals
- Backend already has `ev_ebitda` in Fundamental model and API response
- FundamentalMetricCard just needs to show it
- StockFundamentals type needs `ev_ebitda` field

### 18-03: Competitor Comparison Table
- New backend endpoint: `GET /stocks/{symbol}/peers`
- Returns 3-5 same-sector stocks with: symbol, name, current_price, daily_change_pct, pe_ratio, pb_ratio, overall_score, recommendation
- Frontend: CompetitorTable component on stock detail page

### 18-04: KAP Feed Expansion
- Change `api.getStockNews(symbol, 5)` to `api.getStockNews(symbol, 10)` in stock detail page

### 18-05: Score Card Minor Improvements
- Add last_data_update timestamp to ScoreLayerPanel if not already shown
- (existing implementation is solid, minor polish only)
