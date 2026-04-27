# Phase 17: Evren Genişlemesi - Research

**Researched:** 2026-04-27
**Domain:** Borsa Istanbul universe expansion, yfinance rate limiting, SQLAlchemy/Alembic migration, React infinite scroll
**Confidence:** HIGH (code reading) / MEDIUM (yfinance rate limits — undocumented by Yahoo)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Yeni `bist_full_universe.py` dosyası oluştur — statik, elle hazırlanmış, kontrol edilebilir
- config.py'de BIST100_UNIVERSE referansını BIST_FULL_UNIVERSE ile değiştir
- Her hisse için 7 alan: symbol, name, sector, market (yıldız/ana/gelişen), is_bist30, is_bist100, is_bist250
- Manuel bakım — yılda 1-2 kez güncelleme yeterli
- Batch büyüklüğü: her 10 hissede bir 1s sleep (mevcut: her 5'te 2s)
- Hata izolasyonu: başarısız sembol log'a düşüp devam etsin, batch durmasın
- full_initial_load: arka planda çalışsın — Railway'de timeout yok
- daily_update period: 5d (değişiklik yok)
- Sayfalama tipi: infinite scroll — aşağı kaydırıldıkça yeni hisseler yüklensin
- Yükleme birimi: sayfa başı 50 hisse
- Filtreler: sektör dropdown + BIST30/100/250 toggle + metin arama (sembol veya ad)
- Varsayılan sıralama: piyasa değeri büyükten küçüğe

### Claude's Discretion
- Borsa İstanbul piyasa sınıflandırması (yıldız/ana/gelişen) için tüm sembolleri araştır ve ata
- Hisse sayısı kesin ~500 olmayabilir; mevcut aktif sembollerin gerçek sayısı araştırmayla belirlenir

### Deferred Ideas (OUT OF SCOPE)
- Otomatik sembol discovery (KAP/Borsa İstanbul scraping) — Phase 17 kapsam dışı, manuel liste yeterli
- Sembol ekleme/çıkarma admin paneli — Phase 17 kapsam dışı
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| F-01-A | bist_full_universe.py — ~500+ sembol statik liste (symbol, name, sector, market, is_bist30, is_bist100, is_bist250) | Yapı mevcut bist100_universe.py'den genişletilir; 7 alanlı dict pattern netleştirildi |
| F-01-B | DataCollector rate limiting — batch 10, sleep 1s, error isolation | Mevcut `(i+1) % 5 == 0: sleep(2)` pattern doğrudan değiştirilir |
| F-01-C | Stock model — market_tier, is_bist250 alanları + migration | stocks tablosuna `op.add_column()` ile nullable STRING ve nullable BOOLEAN eklenir |
| F-01-D | Frontend infinite scroll — 50/sayfa, sektör+BIST filter, arama, market_cap sort | Intersection Observer API + useCallback ref + offset pagination; backend limit parametresi 100→50 |
| NF-02 | ~500 hisse için günlük veri güncellemesi rate limit toleranslı tamamlanmalı | Batch 10 + 1s sleep = ~50s/500 hisse — doğrulanabilir sınır |
| NF-03 | Hisse listesi sayfası <2s yüklenmeli | Offset pagination 500 satır için yeterli; DB index market_cap DESC zaten var |
</phase_requirements>

---

## Summary

Phase 17, mevcut 100 hisselik BIST100 evrenini ~500+ aktif Borsa İstanbul hissesine genişletir. Araştırma dört kritik alanı kapsar: (1) Borsa İstanbul'un gerçek hisse sayısı ve piyasa segmentleri, (2) yfinance rate limiting güvenli sınırlar, (3) SQLAlchemy/Alembic ile mevcut tabloya sütun ekleme, (4) React'ta Intersection Observer tabanlı infinite scroll.

Borsa İstanbul'da Nisan 2026 itibarıyla **607 aktif hisse** mevcuttur (stockanalysis.com, günlük güncelleme). Bu, CONTEXT.md'deki "~500" tahmininden daha fazladır. Ancak tüm 607 sembolün yfinance `.IS` formatını destekleyip desteklemediği garanti edilemez — bazı küçük şirketler Yahoo Finance'ta kapsanmayabilir. Güvenli yaklaşım: bilinen BIST endeksleri (BIST30, BIST100, BIST250, BIST Stars, BIST Main, BIST Sub) üzerinden listeyi oluşturmak ve yfinance'tan başarısız dönenleri sessizce atlamak.

yfinance rate limiting, Yahoo Finance'ın belgesiz bir API korumasıdır. 2025 boyunca açık GitHub issue'larında raporlanan patern: ~100 request → 30 saniye bekleme. Mevcut proje diskcache ile 300s TTL uyguluyor — bu doğru önlem. CONTEXT.md kararı (batch 10, 1s sleep) makul fakat agresif; `initialize_stocks()` için tek seferlik ilk yüklemede daha uzun sleep önerilir.

**Primary recommendation:** Statik liste için BIST30+BIST100 kesin listesine (100 hisse doğrulanmış) BIST250+BIST Stars+BIST Main kaynaklı semboller eklenerek ~400-600 hisselik bir liste oluştur. yfinance hataları zaten izole ediliyor; bilinmeyen semboller otomatik atlanır.

---

## Standard Stack

### Core (Mevcut — değiştirilmiyor)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 0.2.54 | Hisse fiyat ve metadata çekimi | Mevcut, çalışıyor |
| SQLAlchemy[asyncio] | 2.0.40 | Async ORM | Mevcut |
| alembic | 1.15.2 | Database migrations | Mevcut, 2 migration'ı var |
| diskcache | 5.6.3 | yfinance result caching | Mevcut |
| React | 19.2.4 | Frontend | Mevcut |
| Next.js | 16.2.3 | Frontend framework | Mevcut |

### Yeni Ekleme Gerekenler
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-intersection-observer | 10.0.3 | Infinite scroll sentinel detection | `useInView` hook ile sentinel ref — native Intersection Observer'ın React wrapper'ı |

**Not:** Native `IntersectionObserver` da kullanılabilir (bağımlılık eklenmez), ancak `react-intersection-observer` 10.0.3, `useInView` hook ile React 19 uyumlu ve `useCallback` ref karmaşıklığını ortadan kaldırır. İki yaklaşım da çalışır.

**Installation (opsiyonel, sadece react-intersection-observer tercih edilirse):**
```bash
cd frontend && npm install react-intersection-observer
```

---

## Architecture Patterns

### 17-01: bist_full_universe.py Yapısı

Mevcut `bist100_universe.py` referans alınır, yeni dosya aynı yapıyı genişletir:

```python
# backend/app/data/bist_full_universe.py
BIST_FULL_UNIVERSE: List[Dict[str, object]] = [
    {
        "symbol": "AKBNK",
        "name": "Akbank",
        "sector": "Banka",
        "market": "yıldız",   # yıldız | ana | gelişen
        "is_bist30": True,
        "is_bist100": True,
        "is_bist250": True,
    },
    # ... diğer hisseler
]

def get_full_symbols() -> List[str]:
    return [item["symbol"] for item in BIST_FULL_UNIVERSE]

def get_bist30_symbols() -> List[str]:
    return [item["symbol"] for item in BIST_FULL_UNIVERSE if item["is_bist30"]]

def get_bist100_symbols() -> List[str]:
    return [item["symbol"] for item in BIST_FULL_UNIVERSE if item["is_bist100"]]

def get_bist250_symbols() -> List[str]:
    return [item["symbol"] for item in BIST_FULL_UNIVERSE if item["is_bist250"]]
```

### config.py Değişim Noktaları

Tek bir import ve referans değişimi yeterli:

```python
# config.py — ÖNCE:
from app.data.bist100_universe import (
    BIST100_UNIVERSE, get_bist100_company_map, ...
)
BIST100_UNIVERSE: List[...] = BIST100_UNIVERSE

# config.py — SONRA:
from app.data.bist_full_universe import (
    BIST_FULL_UNIVERSE, get_full_symbols, get_bist100_symbols, ...
)
BIST100_UNIVERSE: List[...] = BIST_FULL_UNIVERSE  # geriye dönük uyum için aynı isim
```

DataCollector `self.universe = list(settings.BIST100_UNIVERSE)` kullanıyor — settings üzerinden gider, doğrudan etkilenmez.

### 17-02: DataCollector Rate Limiting Değişikliği

```python
# data_collector.py — collect_price_data() içinde:
# ÖNCE: if (i + 1) % 5 == 0: await asyncio.sleep(2)
# SONRA:
async def collect_price_data(self, period: str = "5y"):
    async with AsyncSessionLocal() as db:
        for i, symbol in enumerate(self.symbols):
            try:
                await self._collect_stock_prices(db, symbol, period)
            except Exception as e:
                logger.error(f"  ❌ {symbol} izole hata: {e}")
                # batch durmuyor, devam ediyor
            if (i + 1) % 10 == 0:
                await db.commit()
                await asyncio.sleep(1)
        await db.commit()
```

**Kritik:** `_collect_stock_prices()` zaten try/except içeriyor (`except Exception as e: logger.error(...)`). Ancak bu exception'ı yutup devam ettiğine dikkat — dıştaki loop için de aynı pattern uygulanır.

### 17-03: Alembic Migration

```python
# backend/alembic/versions/003_stock_market_tier_bist250.py
revision = '003'
down_revision = '002'

def upgrade() -> None:
    op.add_column('stocks', sa.Column('market_tier', sa.String(20), nullable=True))
    op.add_column('stocks', sa.Column('is_bist250', sa.Boolean(), nullable=True,
                  server_default=sa.text('false')))

def downgrade() -> None:
    op.drop_column('stocks', 'is_bist250')
    op.drop_column('stocks', 'market_tier')
```

**Neden nullable:** Mevcut ~100 kayıt için `market_tier` değeri bilinmiyor; NULL başlangıç değeri sorunsuz. `initialize_stocks()` yeniden çalıştığında doldurur.

**alembic/env.py'ye import ekle:** `import app.models.stock` satırı env.py'de yoksa ekle (models kaydı için).

### 17-04: Frontend Infinite Scroll

Mevcut sayfa `'use client'` direktifi ile zaten Client Component. Mevcut `loadStocks()` offset destekliyor (`api.getStocks({ offset })`). Değişiklik minimal:

```typescript
// stocks/page.tsx — infinite scroll eklentisi
const [page, setPage] = useState(0);
const [hasMore, setHasMore] = useState(true);
const sentinelRef = useRef<HTMLDivElement>(null);

const loadMore = useCallback(async () => {
  if (loading || !hasMore) return;
  setLoading(true);
  const res = await api.getStocks({
    sort_by: 'market_cap',
    limit: 50,
    offset: page * 50,
    sector: filterSector || undefined,
    bist30: filterBist30 || undefined,
    search: search || undefined,
    // yeni: bist100, bist250 filter parametreleri eklenecek
  });
  setStocks(prev => page === 0 ? res.stocks : [...prev, ...res.stocks]);
  setTotal(res.total);
  setHasMore(res.stocks.length === 50);
  setPage(prev => prev + 1);
  setLoading(false);
}, [page, loading, hasMore, filterSector, filterBist30, search]);

// Sentinel observer
useEffect(() => {
  const el = sentinelRef.current;
  if (!el) return;
  const observer = new IntersectionObserver(
    (entries) => { if (entries[0].isIntersecting) void loadMore(); },
    { threshold: 0.1 }
  );
  observer.observe(el);
  return () => observer.disconnect();
}, [loadMore]);

// Filter değişiminde page sıfırlama
useEffect(() => {
  setPage(0);
  setStocks([]);
  setHasMore(true);
}, [filterSector, filterBist30, search, filterBist100, filterBist250]);
```

**Sentinel div (table'ın altına):**
```tsx
<div ref={sentinelRef} style={{ height: 1 }} />
{loading && <div className="skeleton" />}
```

### Backend API Değişikliği

`GET /stocks` endpoint'ine `bist100` ve `bist250` filter parametresi eklenmeli:

```python
# api/stocks.py
bist100: Optional[bool] = None,
bist250: Optional[bool] = None,
# ...
if bist100:
    query = query.where(Stock.is_bist100)
if bist250:
    query = query.where(Stock.is_bist250)
```

### Recommended Project Structure (değişen dosyalar)

```
backend/
├── app/
│   ├── data/
│   │   ├── bist100_universe.py       # korunur (geriye uyum)
│   │   └── bist_full_universe.py     # YENİ — ~500+ sembol
│   ├── models/
│   │   └── stock.py                  # +market_tier, +is_bist250
│   ├── services/
│   │   └── data_collector.py         # batch 10, sleep 1s, error isolation
│   ├── api/
│   │   └── stocks.py                 # +bist100/bist250 filter params
│   └── core/
│       └── config.py                 # BIST_FULL_UNIVERSE import
├── alembic/versions/
│   └── 003_stock_market_tier_bist250.py  # YENİ migration
frontend/
├── src/app/stocks/
│   └── page.tsx                      # infinite scroll + BIST250 filter
├── src/lib/
│   └── api.ts                        # +bist100, +bist250 params
```

### Anti-Patterns to Avoid

- **`alembic autogenerate` ile `nullable=False` sütun eklemek:** Mevcut satırlar için NULL hatası verir. Her zaman önce nullable, sonra backfill, sonra NOT NULL.
- **Filtre değişiminde `page` sıfırlamamak:** Sektör değişince eski hisseler yeni yüklemelere karışır. Filter state değişiminde `stocks = []` ve `page = 0` zorunlu.
- **`initialize_stocks()` içinde rate limit bekleme yapmamak:** `initialize_stocks()` her sembol için `ticker.info` çağırıyor — bu ayrı bir rate limiting riski. Batch sleep burada da gerekebilir (mevcut kodda yok).
- **`bist100_universe.py`yi silmek:** Mevcut testler `test_bist100_universe.py` bu dosyayı import ediyor. Geriye dönük uyum için dosyayı koru veya testleri güncelle.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Intersection Observer scroll detection | Scroll event listener + debounce | Native `IntersectionObserver` API veya `react-intersection-observer` | Scroll events CPU yoğun; IO asynchronous, performant |
| yfinance caching | Custom HTTP cache | Mevcut `diskcache` (300s TTL) | Zaten kurulu, çalışıyor |
| Database migration | Manuel ALTER TABLE SQL | Alembic `op.add_column()` | Version tracking, rollback |
| Pagination | Frontend-side slice | Backend offset/limit | 500 satır JSON'ı tek seferde göndermek yasak |

**Key insight:** Mevcut kod altyapısı (diskcache + retry logic + async) doğru şekilde kurulmuş. Phase 17 ağırlıklı olarak konfigürasyon ve veri genişletmesidir, sıfırdan mimari değil.

---

## Common Pitfalls

### Pitfall 1: yfinance Rate Limiting — initialize_stocks()

**What goes wrong:** `initialize_stocks()` her yeni sembol için `ticker.info` çağırıyor (JSON metadata). 500 sembol için 500 ayrı istek = 429 Too Many Requests.

**Why it happens:** Mevcut kodda `initialize_stocks()` içinde batch sleep yok. `collect_price_data()` içinde var ama `initialize_stocks()` değiştirilmedi.

**How to avoid:** `initialize_stocks()` döngüsüne de batch sleep ekle (her 10 sembolde 1s). İlk yüklemede yavaş olmak sorun değil — Railway'de arka planda çalışıyor.

**Warning signs:** Log'da birden fazla `⚠️ {symbol} bilgisi alınamadı: YFRateLimitError` satırı.

### Pitfall 2: Filter Değişiminde Stale Infinite Scroll State

**What goes wrong:** Kullanıcı sektör filtresi değiştirdiğinde, eski hisseler listede kalır ve yeni sayfa üstlerine eklenir.

**Why it happens:** `page` state sıfırlanmaz, `stocks` state temizlenmez.

**How to avoid:** Her filter state değişiminde `useEffect` ile `setPage(0)`, `setStocks([])`, `setHasMore(true)` çalıştır.

**Warning signs:** Sektör değiştirince hem eski hem yeni sektör hisseleri listede görünüyor.

### Pitfall 3: Alembic Migration Import Eksik

**What goes wrong:** `alembic upgrade head` çalışır ama yeni `Stock` model alanları tabloya yansımaz veya autogenerate boş diff üretir.

**Why it happens:** `alembic/env.py`'de `import app.models.stock` satırı yoksa SQLAlchemy metadata'ya kaydedilmez.

**How to avoid:** `env.py`'de mevcut import'ları kontrol et — `portfolio_v2` import edilmiş. Aynı şekilde `import app.models.stock` ekle.

**Warning signs:** `alembic check` "no new upgrade operations" diyorsa import eksiktir.

### Pitfall 4: Mevcut Test Kırılması

**What goes wrong:** `test_bist100_universe.py` şunu test ediyor: `len(BIST100_UNIVERSE) == 100`. `bist_full_universe.py` oluştururken `bist100_universe.py`yi değiştirirsek bu test kırılır.

**Why it happens:** Config değişikliği eski dosyayı etkiliyor.

**How to avoid:** `bist100_universe.py` olduğu gibi korunur; `bist_full_universe.py` ayrı dosya olarak oluşturulur. Sadece `config.py` import'u değişir. Test ya kalsın ya güncellensin — ancak `BIST100_UNIVERSE` listesi değişmiyorsa test etkilenmez.

**Warning signs:** `pytest tests/test_bist100_universe.py` fail olursa.

### Pitfall 5: Borsa İstanbul Sembol Formatı Tutarsızlıkları

**What goes wrong:** Bazı Borsa İstanbul sembolleri yfinance'ta farklı format gerektirir. Örneğin rüçhan hakları veya tercihli hisse sınıfları (THYAO için THYAO.IS çalışır ama bazı küçük semboller çalışmayabilir).

**Why it happens:** yfinance kapsamı, Borsa İstanbul'daki tüm 607 sembolü desteklemiyor olabilir.

**How to avoid:** `initialize_stocks()` ve `collect_price_data()` zaten try/except + loglama içeriyor. Başarısız semboller loga düşer, veri tabanında `is_active=True` olarak kalır ama fiyat verisi olmaz. Tolere edilebilir.

---

## Code Examples

### Mevcut DataCollector batch pattern (collect_price_data):
```python
# Mevcut — backend/app/services/data_collector.py:179-184
for i, symbol in enumerate(self.symbols):
    await self._collect_stock_prices(db, symbol, period)
    # Rate limit koruması: her 5 hissede bir 2 saniye bekle
    if (i + 1) % 5 == 0:
        await db.commit()
        await asyncio.sleep(2)
```

### Hedef pattern (Phase 17 sonrası):
```python
# Batch 10, sleep 1s, error isolation
for i, symbol in enumerate(self.symbols):
    try:
        await self._collect_stock_prices(db, symbol, period)
    except Exception as e:
        logger.error(f"  ❌ {symbol} izole hata — devam: {e}")
    if (i + 1) % 10 == 0:
        await db.commit()
        await asyncio.sleep(1)
await db.commit()
```

### Alembic migration — add column pattern (alembic 1.15.2, PostgreSQL):
```python
# Source: alembic.sqlalchemy.org/en/latest/ops.html
def upgrade() -> None:
    op.add_column('stocks', sa.Column('market_tier', sa.String(20), nullable=True))
    op.add_column('stocks', sa.Column('is_bist250', sa.Boolean(),
                  nullable=True, server_default=sa.text('false')))

def downgrade() -> None:
    op.drop_column('stocks', 'is_bist250')
    op.drop_column('stocks', 'market_tier')
```

### Stock model yeni alanlar:
```python
# backend/app/models/stock.py — eklenecek alanlar
market_tier = Column(String(20), nullable=True)  # yıldız | ana | gelişen
is_bist250 = Column(Boolean, default=False)
```

### Intersection Observer infinite scroll — sentinel callback ref pattern:
```typescript
// Source: freecodecamp.org/news/infinite-scrolling-in-react/
const observer = useRef<IntersectionObserver | null>(null);

const sentinelRef = useCallback((node: HTMLDivElement | null) => {
  if (loading) return;
  if (observer.current) observer.current.disconnect();
  observer.current = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && hasMore) {
      void loadNextPage();
    }
  });
  if (node) observer.current.observe(node);
}, [loading, hasMore]);
```

### api.ts — yeni filter parametreleri:
```typescript
getStocks: (params?: {
  sort_by?: string;
  limit?: number;
  offset?: number;
  sector?: string;
  bist30?: boolean;
  bist100?: boolean;   // YENİ
  bist250?: boolean;   // YENİ
  search?: string;
  recommendation?: string;
})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scroll event + debounce | IntersectionObserver API | ~2019, stable | CPU düşük, smooth scroll |
| OFFSET pagination tek yol | OFFSET (küçük tablo) / Cursor (büyük tablo) | PostgreSQL 10+ | 500 satır için OFFSET yeterli |
| yfinance threads=True bulk | Sequential + sleep + retry | 2025 rate limit artışı | Threading = daha hızlı 429 |

**Deprecated/outdated:**
- `yf.download(tickers, threads=True)` ile büyük batch: 2025 itibarıyla 429 tetikleme riski daha yüksek. Sequential küçük batch + sleep daha güvenilir.

---

## Key Research Findings

### Borsa İstanbul Hisse Sayısı
- **607 aktif hisse** (stockanalysis.com, Nisan 2026, günlük güncelleme)
- Bunların tamamı yfinance `.IS` formatını desteklemeyebilir — bazıları küçük şirketler
- Güvenli başlangıç hedefi: **400-500 sembol** (BIST250 + BIST Stars + BIST Main kapsamı)
- Market segmentleri: **BIST Stars** (yıldız), **BIST Main** (ana), **BIST Sub Market** (gelişen)
- Bu segmentler Borsa İstanbul tarafından yılda en az 2 kez güncelleniyor

### yfinance Rate Limiting (Confidence: MEDIUM — belgesiz)
- Yahoo Finance rate limit değerleri resmi olarak belgelenmiyor
- Community gözlemi: ~100 request → 30 saniye bekleme gerekebilir
- Mevcut diskcache (300s TTL) doğru önlem — aynı sembol 5 dakika içinde tekrar istek atmıyor
- `collect_price_data()` için batch 10 + 1s sleep = ~50 saniye/500 hisse minimal duration
- `initialize_stocks()` için benzer batch sleep EKLENMELİ (şu an yok)

### Alembic Migration
- PostgreSQL'de `op.add_column()` ile nullable sütun ekleme idempotent değil (tablo yoksa hata)
- Pattern: nullable=True ile ekle, downgrade'de drop
- `env.py`'de import zorunlu: `import app.models.stock`
- Mevcut `001` ve `002` migration'ları `if_not_exists=True` kullanıyor — model aynısını

### Offset Pagination (500 satır için)
- 500 satırda OFFSET performans sorunu minimal — cursor pagination gerekmez
- Mevcut backend zaten `offset` parametresini destekliyor
- Maksimum `limit=200` kısıtı var — 50 olarak değiştirilmeli (veya default değiştirilmeli)

### Infinite Scroll vs Load More
- Intersection Observer API tüm modern tarayıcılarda destekleniyor (IE hariç)
- React 19 + Next.js 16 'use client' component içinde doğrudan kullanılabilir
- `react-intersection-observer 10.0.3` isteğe bağlı — native API yeterli

---

## Open Questions

1. **yfinance `.IS` kapsamı: 607 sembollerin kaçı çalışır?**
   - What we know: Mevcut 100 sembolün tamamı çalışıyor
   - What's unclear: 500+ sembol için coverage oranı bilinmiyor
   - Recommendation: `initialize_stocks()` log'larından başarısız sembolleri sayarak belirle; %80+ çalışırsa kabul edilebilir

2. **`is_bist250` mevcut 100 hisse için backfill gerekiyor mu?**
   - What we know: BIST250, BIST100'ü içerir + 150 hisse daha
   - What's unclear: Mevcut 100 hissenin is_bist250 değerleri tanımlı değil
   - Recommendation: `bist_full_universe.py`'de is_bist250=True olan kayıtlar `initialize_stocks()` çalışırken günceller; ayrı backfill gerekmez

3. **Next.js 16.2.3 `'use client'` + `IntersectionObserver`: SSR sorun çıkarır mı?**
   - What we know: Next.js 16 AGENTS.md'de breaking changes uyarısı var
   - What's unclear: `window` / `IntersectionObserver` SSR guard gerekiyor mu?
   - Recommendation: `useEffect` içinde oluşturulduğu için SSR güvenli — `useEffect` sadece client'ta çalışır

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (asyncio_mode = auto) |
| Config file | backend/pytest.ini |
| Quick run command | `cd backend && pytest tests/test_bist100_universe.py -x` |
| Full suite command | `cd backend && pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| F-01-A | BIST_FULL_UNIVERSE yapısı — symbol/name/sector/market/is_bist30/is_bist100/is_bist250 alanları var | unit | `pytest tests/test_bist_full_universe.py -x` | ❌ Wave 0 |
| F-01-A | Semboller unique, her sembol 7 alan içeriyor, is_bist30 kümesi is_bist100 kümesinin alt kümesi | unit | `pytest tests/test_bist_full_universe.py -x` | ❌ Wave 0 |
| F-01-A | BIST100_UNIVERSE backward compat — eski 100 sembol hala config'de | unit | `pytest tests/test_bist100_universe.py -x` | ✅ (pass olmalı) |
| F-01-B | collect_price_data batch 10 + 1s sleep | unit | `pytest tests/test_data_collector_batch.py -x` | ❌ Wave 0 |
| F-01-B | Hata izolasyonu — tek sembol fail ettiğinde batch devam ediyor | unit | `pytest tests/test_data_collector_batch.py -x` | ❌ Wave 0 |
| F-01-C | Stock model — market_tier ve is_bist250 alanları mevcut | unit | `pytest tests/test_models.py -x` | ✅ (güncelle) |
| F-01-D | getStocks() bist100/bist250 parametreleri API'ye gönderiliyor | smoke | Manuel browser test | manual-only |

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/test_bist_full_universe.py tests/test_models.py -x`
- **Per wave merge:** `cd backend && pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_bist_full_universe.py` — yeni universe yapısını test eder (F-01-A)
- [ ] `tests/test_data_collector_batch.py` — batch/sleep/isolation test eder (F-01-B)
- [ ] `tests/test_models.py` güncelleme — `market_tier` ve `is_bist250` alanlarını test eder (F-01-C)

---

## Sources

### Primary (HIGH confidence)
- Proje kaynak kodu — `backend/app/data/bist100_universe.py`, `data_collector.py`, `models/stock.py`, `config.py`, `api.ts`, `stocks/page.tsx`
- Alembic docs (alembic.sqlalchemy.org) — `op.add_column()`, nullable column migration pattern
- MDN Web API — `IntersectionObserver` API

### Secondary (MEDIUM confidence)
- [stockanalysis.com/list/borsa-istanbul](https://stockanalysis.com/list/borsa-istanbul/) — 607 aktif hisse sayısı (günlük güncelleme)
- [borsaistanbul.com/en/markets/equity-market/markets](https://www.borsaistanbul.com/en/markets/equity-market/markets) — BIST Stars/Main/Sub segment kriterleri
- [freecodecamp.org — Infinite Scrolling in React](https://www.freecodecamp.org/news/infinite-scrolling-in-react/) — `lastElementRef` + `IntersectionObserver` pattern
- [github.com/ranaroussi/yfinance discussions/2431](https://github.com/ranaroussi/yfinance/discussions/2431) — ~100 request → 30s pause community finding

### Tertiary (LOW confidence — flag for validation)
- yfinance `.IS` sembol kapsamı (607'nin kaçı çalışır) — test edilmedi, LOW
- Exact rate limit thresholds — Yahoo resmi belge yok, LOW

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — kaynak kod okundu, mevcut kütüphaneler doğrulandı
- Architecture patterns: HIGH — mevcut pattern'lar kaynak koddan çıkarıldı
- Borsa Istanbul symbol count: MEDIUM — stockanalysis.com (günlük güncelleme, Nisan 2026)
- yfinance rate limiting: MEDIUM — community reports, resmi kaynak yok
- Pitfalls: HIGH — kod okunarak somut risk noktaları belirlendi
- Alembic migration: HIGH — resmi docs + mevcut migration örnekleri

**Research date:** 2026-04-27
**Valid until:** 2026-05-27 (yfinance rate limit davranışı için 30 gün; Borsa İstanbul sembol listesi için 6 ay)
