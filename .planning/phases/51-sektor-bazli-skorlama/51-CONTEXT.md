# Phase 51: Sektör Bazlı Skorlama — Context

## Phase Goal

Bankacılık, GYO ve Holding hisseleri için sektöre özgü skorlama mantığı devreye girer; yanıltıcı standart metrikler bu sektörlerde uygulanmaz.

## Requirements

- **SEK-01**: Bankacılık hisseleri için F/DD (P/TBV) + ROE ağırlıklı sektör skoru; standart PE/PB bu hisseler için uygulanmaz.
- **SEK-02**: GYO hisseleri için P/B değeri NAV proxy skoru; UI'da "Gerçek NAD verisi mevcut değil" notu.
- **SEK-03**: Holding hisseleri için halka açık bağlı ortaklık piyasa değerleri toplamından yaklaşık NAV iskontosu; skora yansıtılır.

## Decisions

### Sector Identification

- `sector_category` VARCHAR(20) nullable column added via migration 011 to `stocks` table. Values: `"banka"` / `"gyo"` / `"holding"` / null.
- Bank tickers (hardcoded): AKBNK, GARAN, ISCTR, YKBNK, HALKB, VAKBN, TSKB, QNBFB, ALBRK
- GYO detection: `stock.sector` contains "Real Estate" (yfinance string)
- Holding tickers (hardcoded): SAHOL, KCHOL, SISE, TKFEN, DOHOL

### Banking Scoring (SEK-01)

`calculate_bank_score(pb_ratio, roe) -> float`:
- P/TBV tier: < 0.8 → 100, < 1.2 → 75, < 2.0 → 50, >= 2.0 → 25
- ROE tier: > 0.20 → 100, > 0.15 → 75, > 0.08 → 50, <= 0.08 → 25
- Weight: 60% P/TBV + 40% ROE
- Overrides `fundamental_score` in `update_all_scores()` for banks; standard PE/PB scoring is NOT applied.

### GYO Scoring (SEK-02)

- Same P/TBV tier formula applied to `pb_ratio` as NAV proxy.
- `sector_scoring_note` stored on Stock: "Gerçek NAD verisi mevcut değil; P/D değeri NAD yaklaşımı olarak kullanılmıştır"
- Overrides `fundamental_score` in `update_all_scores()` for GYO stocks.

### Holdings NAV (SEK-03)

Hardcoded subsidiary map:
```python
HOLDING_SUBSIDIARIES = {
    "SAHOL": ["AKBNK", "AKGRT", "AKENR"],
    "KCHOL": ["ARCLK", "TOASO", "TUPRS", "AYGAZ"],
    "SISE": ["TRKCM", "ANACM", "SODA"],
    "TKFEN": ["TKFEN"],   # self + external — use available only
    "DOHOL": ["DOAS", "DOHOL"],
}
```

NAV discount = `(sum_subsidiaries_market_cap - holding_market_cap) / sum_subsidiaries_market_cap`
- discount > 0.30 → sector_score boost (+15 to fundamental_score, capped 100)
- discount > 0.15 → small boost (+7)
- discount < 0 (premium) → penalty (-10)
- Stored as `nav_discount FLOAT nullable` on Stock.

### New DB Columns (migration 011)

Added to `stocks` table:
- `sector_category VARCHAR(20) nullable`
- `sector_score FLOAT nullable`
- `sector_scoring_method VARCHAR(50) nullable`
- `nav_discount FLOAT nullable`

### API Exposure

`/stocks/{symbol}/score-breakdown` response already includes `stock.sector_score`, `stock.sector_category`, `stock.sector_scoring_method`, `stock.nav_discount` via the guardrail_components extension pattern.

`/stocks/{symbol}` (detail) and `/stocks` (list) responses include `sector_category` and `nav_discount` passthrough.

### Frontend Display

Stock detail page — Skor Dökümü section (line ~807 in `page.tsx`):
- If `sector_scoring_method` is set: show a labeled badge below the breakdown bars: "Skorlama Yöntemi: {method}"
- If `sector_category === "gyo"`: show info note below badge: "Gerçek NAD verisi mevcut değil; P/D değeri NAD yaklaşımı olarak kullanılmıştır"
- If `sector_category === "holding"` and `nav_discount != null`: show NAV iskonto row: "NAV İskontosu: {%X}"

## Plan Structure

- **51-01** (Wave 1, autonomous): Backend — migration 011, sector_category classification util, bank/GYO/holding scoring methods, integration into `update_all_scores()`, API serialization.
- **51-02** (Wave 2, autonomous): Frontend — `api.ts` type extensions, Skor Dökümü sector display block in `page.tsx`.

## Depends On

Phase 48 (data_quality_score pattern — same migration + scoring pattern used here).
