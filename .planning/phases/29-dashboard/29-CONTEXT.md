# Phase 29: Dashboard - Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Kullanıcı uygulamayı açtığında piyasanın nabzını (BIST100, döviz, altın) ve portföy özetini tek sayfada görür. Mevcut `frontend/src/app/page.tsx` sıfırdan yeniden yazılır. Yeni Phase 28 market API'leri (`/market/bist100`, `/market/forex`, `/market/gold`) kullanılır. Hisse detay, tarama, portföy yönetimi ayrı fazlara aittir.

</domain>

<decisions>
## Implementation Decisions

### Mevcut kodu yeniden yazma
- **D-01:** `frontend/src/app/page.tsx` tamamen silinip sıfırdan yazılır. Eski kodun hiçbir parçası korunmaz (eski v3 API'lerine bağlı; model portfolio, KAP feed, sparkline grid — hepsi kaldırılır).
- **D-02:** `page.module.css` de sıfırdan yazılır; yalnızca yeni dashboard için gerekli stiller kalır.

### Layout yapısı
- **D-03:** Sayfanın en üstünde BIST100 tam genişlikte (full-width) banner. Tek bakışta endeks, günlük değişim ve hacim görünür.
- **D-04:** BIST100 banner'ın altında esnek grid: Döviz widgetı ve Altın widgetı yan yana (masaüstünde 2 kolon, mobilde 1 kolon).
- **D-05:** En altta portföy özet widgetı (tam genişlikte veya grid içinde tek satır).

### Widget içeriği
- **D-06:** Her döviz çifti için: sembol (USD/TRY), fiyat, günlük % değişim, yön ok işareti (▲ yeşil / ▼ kırmızı). Sparkline yok — sadece anlık değer + değişim.
- **D-07:** Altın widgetı: gram, ons, çeyrek, yarım, tam — her biri için TRY fiyatı + % değişim + ok rengi.
- **D-08:** BIST100 banner: Endeks değeri, günlük % değişim (yeşil/kırmızı), hacim. Değişim işareti büyük ve net okunur.

### Veri yenileme
- **D-09:** Sayfa açılışında veri çekilir (useEffect), ardından her 30 saniyede otomatik yenileme. `setInterval` ile `clearInterval` lifecycle temizleme.
- **D-10:** Her endpoint bağımsız olarak non-blocking şekilde yüklenir — BIST100, forex, gold ayrı state'ler. Biri başarısız olursa diğerleri çalışmaya devam eder.

### Portföy özeti (DASH-04)
- **D-11:** Portföy widgetı alanı tasarımda yer alır ama Phase 32 tamamlanana kadar "Portföy henüz eklenmedi — yakında" boş durum mesajı gösterir. Placeholder stiline uygun bir kart yerleştirilir.

### Tasarım sistemi
- **D-12:** Mevcut CSS custom properties kullanılır (`--bg-card`, `--accent-green`, `--accent-red`, `--text-primary`, `--text-secondary`). Yeni CSS sınıfı tanımlanmaz — mevcut `card`, `glass-card` sınıfları önceliklidir.
- **D-13:** `AppShell` ve `Sidebar` aynen korunur, yalnızca page içeriği değişir.
- **D-14:** Tamamen Türkçe etiketler ("Dolar", "Avro", "Sterlin", "Altın" vb.).

### Claude's Discretion
- Döviz çiftlerinin sırasının ve hangi 6 çiftin gösterileceğinin seçimi (Phase 28'de FOREX_PAIRS tanımlı: USD, EUR, GBP, CNY, JPY, CHF)
- Sayı formatı (binlik ayraç, ondalık basamak sayısı) — formatPrice() helper kullanılabilir
- Loading skeleton tasarımı
- Error state (kart başına mı, sayfa genelinde mi?)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 29 gereksinimleri
- `.planning/REQUIREMENTS.md` §DASH-01, DASH-02, DASH-03, DASH-04 — dashboard gereksinimleri

### Phase 28 market API'leri (tüketilecek)
- `backend/app/api/market.py` — `/market/bist100`, `/market/forex`, `/market/gold`, `/market/opportunities` endpoint tanımları ve dönüş şekilleri
- `backend/tests/test_market_endpoints.py` — endpoint response shape örnekleri (assertion'lardan çıkarılabilir)

### Frontend patterns ve tasarım sistemi
- `frontend/src/lib/api.ts` — Mevcut API client pattern'i; yeni market endpoint'ler için yeni metodlar eklenecek
- `frontend/src/app/globals.css` — Design token'lar (CSS custom properties)
- `frontend/src/components/AppShell.tsx` — Sayfa wrapper'ı (korunur)
- `frontend/src/components/Sidebar.tsx` — Nav (korunur)
- `frontend/src/components/StockHelpers.tsx` — `formatPrice()`, `formatVolume()`, `formatPercentage()` formatters
- `frontend/src/components/TerminalPrimitives.tsx` — `TerminalShell`, `TerminalPageHeader`, `TerminalSection` reusable primitives

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StockHelpers.tsx`: `formatPrice()`, `formatVolume()`, `formatPercentage()` — sayı formatlaması için kullanılabilir
- `TerminalPrimitives.tsx`: `TerminalShell`, `TerminalPageHeader`, `TerminalSection`, `TerminalMetric` — sayfa yapısı için
- `AppShell.tsx` + `Sidebar.tsx` — wrapper olarak korunur, dokunulmaz
- `globals.css` — `card`, `glass-card` CSS sınıfları widget kartları için hazır

### Established Patterns
- Tüm page'ler `'use client'` + `useEffect` ile client-side data fetching yapar — aynı pattern devam eder
- `apiFetch<T>()` generic helper `api.ts`'de tanımlı — yeni market metodları buraya eklenir
- Non-blocking parallel fetch: `Promise.allSettled([...])` + her endpoint için ayrı state — mevcut `page.tsx`'ten öğrenilecek pattern
- CSS Module kullanımı: `page.module.css` — responsive layout için

### Integration Points
- `api.ts`'e 3 yeni method eklenir: `getMarketBist100()`, `getMarketForex()`, `getMarketGold()`
- `page.tsx` sıfırdan yazılır; `AppShell` ile sarılır, Sidebar nav'da Dashboard aktif kalır
- Sidebar'da "Dashboard" linki `/` — değişmez

</code_context>

<specifics>
## Specific Ideas

- BIST100 değişimi büyük ve net görünmeli — tek bakışta piyasa yönü anlaşılmalı
- Yeşil/kırmızı oklar (▲/▼) sayı rengine eşlik eder — semantik renk çifti
- Portföy alanı placeholder olsa da gerçek bir "yakında" deneyimi olsun; boş gri kutu değil, açıklayıcı kart

</specifics>

<deferred>
## Deferred Ideas

- BIST100 sparkline grafiği — Phase 30 veya sonrasına bırakılır
- Döviz alarm / trend notification — v2 kapsamında
- Altın tarihsel grafik — Hisse Detay mantığı tamamlandıktan sonra

</deferred>

---

*Phase: 29-dashboard*
*Context gathered: 2026-05-05*
