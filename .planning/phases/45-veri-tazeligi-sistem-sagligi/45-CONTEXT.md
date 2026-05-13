# Phase 45: Veri Tazeliği & Sistem Sağlığı - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Tüm sayfalarda verinin ne zaman güncellendiği gösterilir; stale data (>8 saat) görsel uyarısı eklenir; hisse detayda fundamental veri dönemi etiketi gösterilir; AI analizine veri tarihi notu eklenir.

</domain>

<decisions>
## Implementation Decisions

### Veri Tazeliği Gösterim
- Hisse listesi altbilgisinde tek genel güncelleme zamanı: "Veriler: 14:23 güncellendi" — `stock.updated_at` en son kaydın tarihinden hesaplanır — VERI-01
- Stale data uyarısı: `updated_at` 8 saatten eskiyse sarı ⚠ banner gösterilir — VERI-03
- Fundamental veri dönemi etiketi: "2024-Q3" formatında, hisse detay Temel Metrikler bölüm başlığına eklenir — VERI-02
- AI analiz tarihi notu: analiz sonucunun altında küçük gri metin "Bu analiz [tarih] verisine dayanmaktadır" — VERI-04

### Backend Entegrasyonu
- `StockSummary` interface'e `updated_at: string | null` alanı eklenir (backend Stock modelinde mevcut)
- Backend list endpoint'in `updated_at` döndürüp döndürmediği kontrol edilecek; döndürmüyorsa SQL select'e eklenir
- Fundamental `period` alanı zaten `/stocks/{symbol}/fundamentals` endpoint'inden geliyor olabilir — kontrol edilecek
- Stale hesaplama: frontend'de `Date.now() - new Date(updated_at).getTime() > 8 * 3600 * 1000`
- AI analiz tarihi: `/stocks/{symbol}/analyze` endpoint'i `analyzed_at` döndürüyorsa kullan, yoksa frontend'de `new Date().toLocaleDateString('tr-TR')` ile call anında timestamp kaydet

### Claude's Discretion
- CSS sınıf isimleri (stale banner, freshness label)
- Zaman formatı (HH:mm mi, "X saat önce" mi) — "HH:mm güncellendi" önerildi ama Claude belirleyebilir

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/stock.py:42` → `updated_at = Column(DateTime(timezone=True), ...)` mevcut
- `backend/app/models/fundamental.py:62` → `updated_at` mevcut — period alanı da olabilir
- `frontend/src/lib/api.ts:46` → `StockSummary` interface — `updated_at` yok, eklenecek
- `frontend/src/app/stocks/page.tsx` → hisse listesi, altbilgi alanı eklenecek
- `frontend/src/app/stocks/[symbol]/page.tsx` → AI analiz bölümü ve fundamental metrikler bölümü

### Established Patterns
- `StockSummary` interface'e yeni field ekleme paterni: api.ts'de interface'e ekle, backend'in döndürdüğünü kontrol et
- CSS Modules: co-located `.module.css` dosyaları
- Loading/error pattern: `useState<string | null>` + setError

### Integration Points
- `frontend/src/lib/api.ts` → StockSummary'e `updated_at: string | null` ekle
- `backend/app/api/stocks.py` → list endpoint SELECT'e `updated_at` dahil et (mevcut değilse)
- `frontend/src/app/stocks/page.tsx` → altbilgi + stale banner + fundamentals dönem
- `frontend/src/app/stocks/[symbol]/page.tsx` → fundamental başlık etiketi + AI analiz tarih notu

</code_context>

<specifics>
## Specific Ideas

- Altbilgi formatı: "Son güncelleme: 14:23" (en son `updated_at` değerinden)
- Stale banner: sarı arka plan, ⚠ ikon, "Veriler 8+ saat önce güncellendi — piyasa kapalı olabilir"
- Fundamental dönem: temel metrik grid başlığı yanında küçük badge: "(2024-Q3)"
- AI analiz notu: `<p className={styles.analysisDate}>Bu analiz 14.05.2026 verisine dayanmaktadır.</p>`

</specifics>

<deferred>
## Deferred Ideas

- Backend'e `is_stale` boolean alanı ekleme — frontend hesaplama yeterli
- Her hisse satırında ayrı timestamp — tek altbilgi daha temiz

</deferred>
