# Phase 17: Evren Genişlemesi - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 17 BIST100 kısıtını kaldırır: ~500 aktif Borsa İstanbul hissesini veri tabanına alır, DataCollector'ı 500 hisse için çalışabilir hale getirir, ve frontend hisse listesini infinite scroll + filtreler ile 500 hisseyi yönetilebilir biçimde sunar.

Bu faz veri ve altyapı odaklıdır — yeni hisse sayfası tasarımı (Phase 18), UI overhaul (Phase 19) kapsam dışıdır.

</domain>

<decisions>
## Implementation Decisions

### Sembol Listesi Kaynağı
- Yeni `bist_full_universe.py` dosyası oluştur — statik, elle hazırlanmış, kontrol edilebilir
- config.py'de BIST100_UNIVERSE referansını BIST_FULL_UNIVERSE ile değiştir
- Her hisse için 7 alan: symbol, name, sector, market (yıldız/ana/gelişen), is_bist30, is_bist100, is_bist250
- Manuel bakım — yılda 1-2 kez güncelleme yeterli

### DataCollector Rate Limiting
- Batch büyüklüğü: her 10 hissede bir 1s sleep (mevcut: her 5'te 2s)
- Hata izolasyonu: başarısız sembol log'a düşüp devam etsin, batch durmasın
- full_initial_load: arka planda çalışsın — Railway'de timeout yok
- daily_update period: 5d (değişiklik yok)

### Frontend Sayfalama ve Filtreleme
- Sayfalama tipi: infinite scroll — aşağı kaydırıldıkça yeni hisseler yüklensin
- Yükleme birimi: sayfa başı 50 hisse
- Filtreler: sektör dropdown + BIST30/100/250 toggle + metin arama (sembol veya ad)
- Varsayılan sıralama: piyasa değeri büyükten küçüğe

### Claude's Discretion
- Borsa İstanbul piyasa sınıflandırması (yıldız/ana/gelişen) için tüm sembolleri araştır ve ata
- Hisse sayısı kesin ~500 olmayabilir; mevcut aktif sembollerin gerçek sayısı araştırmayla belirlenir

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/data/bist100_universe.py` — genişletilecek, yeni dosya bu yapıyı referans alır
- `backend/app/services/data_collector.py` — DataCollector.collect_price_data() batch sleep burada
- `backend/app/core/config.py` — BIST100_UNIVERSE, BIST100_COMPANIES, BIST100_SYMBOLS değişkenleri
- `backend/app/models/stock.py` — Stock modeli (is_bist30, is_bist100 flag'leri mevcut)
- `frontend/src/app/stocks/page.tsx` — hisse listesi sayfası, mevcut filtreleme buraya eklenecek

### Established Patterns
- Universe veri yapısı: `{"symbol": "AKBNK", "name": "Akbank", "sector": "Banka", "is_bist30": True}`
- DataCollector batch: `if (i + 1) % 5 == 0: await asyncio.sleep(2)` — parametre değişecek
- Config: `BIST100_UNIVERSE: List[Dict[str, object]] = BIST100_UNIVERSE` — tek değişim noktası

### Integration Points
- `config.py` Settings class: BIST100_UNIVERSE → BIST_FULL_UNIVERSE swap
- `data_collector.py` `initialize_stocks()` ve `collect_price_data()`: self.universe kaynaklı
- `stock.py` modeli: `is_bist250` alanı yoksa migration gerekecek
- Frontend `api.ts` getStocks() — sayfa bazlı pagination parametresi eklenecek

</code_context>

<specifics>
## Specific Ideas

- Infinite scroll için frontend'de Intersection Observer API kullanılabilir (React hook)
- yfinance `.IS` sembol formatı: "AKBNK.IS" — mevcut format, değişiklik yok
- Stock modelinde `market_tier` (yıldız/ana/gelişen) alanı backend migration ile eklenecek

</specifics>

<deferred>
## Deferred Ideas

- Otomatik sembol discovery (KAP/Borsa İstanbul scraping) — Phase 17 kapsam dışı, manuel liste yeterli
- Sembol ekleme/çıkarma admin paneli — Phase 17 kapsam dışı

</deferred>
