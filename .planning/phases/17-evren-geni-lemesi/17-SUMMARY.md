# Phase 17: Evren Genişlemesi — SUMMARY

**Completed:** 2026-04-28
**Status:** Done

## What Was Built

BIST100 (~100 hisse) kısıtı kaldırıldı; tüm aktif Borsa İstanbul hisseleri (~400) veri tabanına alınabilir hale getirildi.

### 17-01: bist_full_universe.py
- `backend/app/data/bist_full_universe.py` oluşturuldu
- 399 unique aktif Borsa İstanbul hissesi (yıldız + ana pazar)
- Her hisse: symbol, name, sector, market_tier, is_bist30, is_bist100, is_bist250
- 4 utility fonksiyon: get_bist_full_symbols(), get_bist_full_universe(), get_bist_full_company_map(), get_bist_full_sector_map()
- bist100_universe.py dokunulmadı (100 hisse, testler güvenli)

### 17-02: DataCollector Rate Limiting
- `collect_price_data()`: 5/2s → 10/1s batch sleep; her sembol try/except ile izole
- `initialize_stocks()`: her 10 hissede commit + 1s sleep + progress log eklendi
- Class docstring "BIST100" → "Borsa İstanbul" güncellendi

### 17-03: Model + Migration + Config
- `Stock` modeline `is_bist250` ve `market_tier` alanları eklendi
- Alembic migration 003: `is_bist250` (Boolean) + `market_tier` (String 20)
- `config.py`: BIST_FULL_UNIVERSE, BIST_FULL_SYMBOLS, BIST_FULL_COMPANIES, BIST_FULL_SECTORS eklendi (BIST100_* korundu)
- `DataCollector.__init__`: BIST100_UNIVERSE → BIST_FULL_UNIVERSE
- `initialize_stocks()`: is_bist100, is_bist250, market_tier universe'den okunuyor
- `/stocks` endpoint: `bist100` ve `bist250` query filtresi eklendi

### 17-04: Frontend Infinite Scroll
- `stocks/page.tsx`: limit 100 → 50, IntersectionObserver infinite scroll
- Yeni state: page, hasMore, loadingMore, sentinelRef
- Filter değişince sayfa sıfırlanıp yeniden yükleniyor
- BIST100 ve BIST250 toggle butonları eklendi (BIST30 yanına)
- "Tüm N hisse yüklendi" bitiş mesajı
- `api.ts`: StockSummary'e is_bist250, market_tier; getStocks'a bist100/bist250 param

## Files Modified
- `backend/app/data/bist_full_universe.py` (YENİ)
- `backend/app/models/stock.py`
- `backend/alembic/versions/003_add_market_tier_bist250.py` (YENİ)
- `backend/app/core/config.py`
- `backend/app/services/data_collector.py`
- `backend/app/api/stocks.py`  
- `frontend/src/app/stocks/page.tsx`
- `frontend/src/lib/api.ts`
