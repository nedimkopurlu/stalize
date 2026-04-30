---
phase: 24
plan: 1
title: Data Reliability — DATA-01 through DATA-05
status: complete
completed: "2026-04-28"
---

# Phase 24 — Data Reliability: Summary

## What Was Done

### DATA-01: KAP Symbol Extraction — BIST_FULL_SYMBOLS

`app/services/kap_parser.py` `_extract_symbols()` — changed `settings.BIST100_SYMBOLS` to `settings.BIST_FULL_SYMBOLS` so all 399 listed stocks get symbol extraction, not just the BIST100 subset.

### DATA-02: Naive datetime → UTC-aware

Added `timezone` to imports and fixed all `datetime.now()` calls:
- `app/services/data_collector.py`: import updated; `stock.last_data_update = datetime.now(timezone.utc)`
- `app/services/sentiment.py`: same pattern for `stock.last_data_update`
- `app/services/fundamental.py`: `datetime.now(timezone.utc).year` for period string
- `app/services/kap_parser.py`: fallback published date uses `datetime.now(timezone.utc).isoformat()`

### DATA-03: yfinance Empty vs Network Error Differentiation

`app/services/data_collector.py` `_fetch()` inside `get_ticker_history()`:
- Explicit `if result is None or result.empty: logger.debug("no data available")` before returning empty DataFrame
- Network errors (non-rate-limit) log `logger.warning(f"yfinance network error: {type(e).__name__}")` before re-raising
- Rate-limit exhaustion gets its own `logger.warning("rate limit exhausted after 3 attempts")`
- Call site message improved from emoji `⚠️` to plain searchable text

### DATA-04: Diskcache 1 GB Size Limit

`app/services/data_collector.py` line 36:
```python
_yf_cache = diskcache.Cache(YFINANCE_CACHE_DIR, size_limit=1_000_000_000)  # 1 GB cap
```
Prevents unbounded disk growth on Railway.

### DATA-05: NewsItem Unique Constraint + Duplicate Check Fix

`app/models/news.py`:
- Added `UniqueConstraint("source", "url", name="uq_news_source_url")` via `__table_args__`
- Added `UniqueConstraint` to import from `sqlalchemy`

`app/services/kap_parser.py` `store_announcements()`:
- Duplicate check changed from broad `(url OR title)` to precise `(source == "KAP") AND (url == link)` 
- Eliminates false-positive duplicate rejection on same-titled but different-URL announcements

## Files Changed

- `backend/app/services/kap_parser.py`
- `backend/app/services/data_collector.py`
- `backend/app/services/sentiment.py`
- `backend/app/services/fundamental.py`
- `backend/app/models/news.py`

## Acceptance Criteria Status

- [x] DATA-01: BIST250+ haberleri sisteme giriyor; symbol extraction BIST_FULL_SYMBOLS kullanıyor
- [x] DATA-02: Tüm `datetime.now()` çağrıları UTC-aware
- [x] DATA-03: yfinance boş dönüş ile ağ hatası log'da ayrı mesajlarla ayırt ediliyor
- [x] DATA-04: Diskcache 1 GB sınırlı; sınırsız büyüme yok
- [x] DATA-05: `uq_news_source_url` unique constraint eklendi; duplicate check (source, url) AND mantığıyla çalışıyor
