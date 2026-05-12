# Phase 43: Karar Dili Güvenliği & Skor Açıklanabilirliği - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

"GÜÇLÜ AL/AL/TUT/SAT/GÜÇLÜ SAT" direktif etiketleri direktif olmayan güvenli dile çevrilir; hisse listesi, hisse detay hero ve model portföy tablosunda yeni etiketler kullanılır. Hisse detay sayfasında skor bileşen dökümü (temel/teknik/sentiment katkısı) progress bar formatında gösterilir; eksik bileşen için uyarı eklenir. Mevcut `/stocks/{symbol}/score-breakdown` backend endpoint'i kullanılır.

</domain>

<decisions>
## Implementation Decisions

### Etiket Sistemi Tasarımı
- Yeni güvenli etiketler: "Yüksek Öncelikli İzleme / Pozitif Görünüm / Nötr İzleme / Zayıflayan Görünüm / Riskli Görünüm" (KARAR-01 birebir)
- Etiket hem hisse listesi (`/stocks`), hem hisse detay hero, hem model portföy tablosunda gösterilir
- Backend'de DB değişikliği yok — display layer'da mapping fonksiyonu ile translate et
- Her etiketin yanında kısa tek cümle tooltip: "Teknik ve temel skor yüksek; yakından izlenebilir" gibi

### Skor Dökümü UI
- Hisse detay sayfasında mevcut metrik kartlarının altında ayrı "Skor Dökümü" bölümü
- 3 bileşen için yatay progress bar'lar + rakam: "Temel: 72 — %45 katkı", "Teknik: 65 — %40 katkı", "Haber: 55 — %15 katkı"
- Eksik bileşen: sarı ⚠ ikon + "Eksik veri — ağırlık yeniden dağıtıldı" yazısı (SKOR-02)
- Mevcut `/stocks/{symbol}/score-breakdown` endpoint'i kullanılır — frontend'de fetch et (SKOR-03)

### Veri Bütünlüğü Göstergesi
- Hisse listesinde skor hücresinin yanında küçük ikon; hisse detay'da skor dökümü bölümünde (KARAR-02)
- Yüksek volatilite uyarısı: hisse kartı/listesinde sarı ⚠, hover'da "Yüksek volatilite — sinyaller daha az güvenilir" (KARAR-03)
- Format: "3/3 bileşen mevcut" veya "2/3 bileşen" — sade metin
- Uyarı tetikleme: fundamental_score NULL ise VEYA 20 günlük fiyat değişimi >%15

### Claude's Discretion
- CSS sınıf isimleri, animasyon süresi, progress bar renkleri — Claude belirler (mevcut design token sistemi takip edilir)
- Tooltip implementasyon yöntemi (CSS :hover veya title attribute) — Claude belirler

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/scoring.py`: `get_contextual_score_breakdown()` → `/stocks/{symbol}/score-breakdown` endpoint zaten var (backend/app/api/stocks.py:394)
- `backend/app/services/scoring.py`: `_recommendation_for_score()` → "GÜÇLÜ AL/AL/TUT/SAT/GÜÇLÜ SAT" label üreten fonksiyon
- `frontend/src/app/stocks/[symbol]/page.tsx:142` → `recColor()` ve `decisionPrimaryLabel()` helper fonksiyonları — bunlara etiket mapping eklenecek
- `frontend/src/app/page.tsx:211` → `stock.recommendation ?? '-'` — dashboard'da da recommendation gösteriliyor
- `frontend/src/app/stocks/page.tsx` → hisse listesinde recommendation kolonu (tam satır bulunamadı ama var)
- `frontend/src/components/StockHelpers.tsx` → `formatPrice()`, `formatPercentage()` helper'lar

### Established Patterns
- CSS Modules pattern: her sayfa için `page.module.css`, component için `Component.module.css`
- Design tokens: `var(--accent-green)`, `var(--accent-red)`, `var(--text-muted)`, `var(--bg-card)` vb.
- Data fetching: `useEffect` + `useState` + `loadData()` pattern
- Error/loading states: `const [loading, setLoading] = useState(true)` pattern

### Integration Points
- Etiket mapping: `frontend/src/app/stocks/[symbol]/page.tsx` içinde `recColor()` ve `decisionPrimaryLabel()` → yeni `safeLabel()` helper
- Skor dökümü: hisse detay sayfasına yeni `ScoreBreakdown` bölümü, `/stocks/${symbol}/score-breakdown` API çağrısı
- Hisse listesi: `frontend/src/app/stocks/page.tsx` recommendation display satırı
- Model portföy: `frontend/src/app/model-portfolio/page.tsx:53`

</code_context>

<specifics>
## Specific Ideas

- Etiket mapping tablosu (backend recommendation → frontend safe label):
  - "GÜÇLÜ AL" → "Yüksek Öncelikli İzleme"
  - "AL" → "Pozitif Görünüm"
  - "TUT" → "Nötr İzleme"
  - "SAT" → "Zayıflayan Görünüm"
  - "GÜÇLÜ SAT" → "Riskli Görünüm"
- Tooltip metinleri:
  - Yüksek Öncelikli İzleme: "Teknik ve temel göstergeler güçlü; yakından takip edilebilir."
  - Pozitif Görünüm: "Göstergeler genel olarak olumlu; dikkatli değerlendirilebilir."
  - Nötr İzleme: "Karma sinyaller; net yön için bekleme önerilir."
  - Zayıflayan Görünüm: "Göstergeler baskı altında; dikkatli olunmalı."
  - Riskli Görünüm: "Yüksek risk sinyalleri mevcut; değerlendirme önerilmez."

</specifics>

<deferred>
## Deferred Ideas

- Etiket sisteminin backend'de DB'ye kaydedilmesi (şimdilik display-layer mapping yeterli)
- Volatilite için ayrı endpoint — şimdilik frontend'de hesaplanacak (son fiyat verisiyle proxy)

</deferred>
