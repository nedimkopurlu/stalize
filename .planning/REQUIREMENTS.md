# Requirements: Yatırım Asistanı

**Defined:** 2026-05-04
**Updated:** 2026-05-08 — v5.0: LLM (Gemini 2.0 Flash) ve Frontend Tasarım gereksinimleri eklendi
**Core Value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## v1 Requirements

### Dashboard

- [x] **DASH-01**: Kullanıcı BIST100 endeks özetini görür (günlük değişim, hacim)
- [x] **DASH-02**: Kullanıcı 5-10 döviz çiftini takip eder (USD/TRY, EUR/TRY, GBP/TRY vb.)
- [x] **DASH-03**: Kullanıcı altın fiyatlarını takip eder (gram, ons, çeyrek, yarım, tam)
- [x] **DASH-04**: Kullanıcı portföy özetini görür (toplam değer, günlük değişim)

### Keşif & Tarama

- [x] **DISC-01**: Kullanıcı BIST100 hisselerini temel + teknik skora göre filtreler ve sıralar
- [x] **DISC-02**: Kullanıcı "bugün ilginç hisseler" listesini görür (yüksek skor = öne çıkar)
- [ ] **DISC-03**: Kullanıcı bir hisseye tıklayıp detay sayfasına gider

### Hisse Detay

- [ ] **STCK-01**: Kullanıcı hissenin fiyat grafiğini görür (7g, 1ay, 3ay, 1y)
- [ ] **STCK-02**: Kullanıcı temel metrikleri görür (F/K, PD/DD, net kar, bilanço büyümesi) — her metriğin yanında ne anlama geldiğini açıklayan tooltip/açıklama
- [ ] **STCK-03**: Kullanıcı teknik göstergeleri görür (RSI, MACD, hareketli ortalamalar) — yanında açıklama
- [ ] **STCK-04**: Kullanıcı "Analiz Et" butonuna basınca Gemini o hisseye özel Türkçe analiz üretir (on-demand, tekrar basılmadan yeni istek gitmez)
- [ ] **STCK-05**: Kullanıcı hissenin KAP açıklamalarını görür
- [ ] **STCK-06**: Kullanıcı hissenin basın haberlerini görür

### Haberler

- [ ] **NEWS-01**: Kullanıcı tüm BIST haberlerini tek sayfada görür (KAP + basın, tarih sıralı)

### Portföy

- [ ] **PORT-01**: Kullanıcı alım işlemi girer (hisse, lot, fiyat, tarih)
- [ ] **PORT-02**: Kullanıcı satım işlemi girer; kapalı pozisyon gerçekleşen kâr/zararla görünür
- [ ] **PORT-03**: Kullanıcı açık pozisyonlarını ve kâr/zararını görür (TL ve % olarak)
- [ ] **PORT-04**: Kullanıcı portföy performansını BIST100 endeksiyle karşılaştırır
- [ ] **PORT-05**: Kullanıcı izleme listesine (watchlist) hisse ekler/çıkarır; watchlist canlı fiyatlarla görünür

### Model Portföy

- [ ] **MODEL-01**: Asistan haftalık model portföy oluşturur (BIST100 evreni, tamamen özerk)
- [ ] **MODEL-02**: Her alım/satım kararı Gemini tarafından yazılan Türkçe gerekçesiyle birlikte tarihli olarak kaydedilir
- [ ] **MODEL-03**: Kullanıcı model portföyün tüm geçmişini görür (hangi tarihte ne alındı/satıldı, neden)
- [ ] **MODEL-04**: Kullanıcı kendi portföyünün performansını model portföyle karşılaştırır

### LLM Entegrasyonu (Gemini 2.0 Flash)

- [ ] **LLM-01**: Backend'de Gemini 2.0 Flash servis katmanı çalışır (google-generativeai SDK, quota aşılırsa graceful fallback)
- [ ] **LLM-02**: Kullanıcı hisse detay sayfasında "Analiz Et" butonu ile on-demand Türkçe Gemini analizi alır; önbellek ile tekrar istek gitmez
- [ ] **LLM-03**: Sistem her sabah otomatik olarak Gemini'den kısa günlük piyasa özeti üretir; dashboard'da ve haberler sayfasında görünür
- [ ] **LLM-04**: Model portföy haftalık karar döngüsünde Gemini portföy değişikliklerini Türkçe gerekçeyle açıklar

### Frontend Tasarım

- [x] **DESIGN-01**: Dashboard BIST100 grafiği tüm 6 periyot tabını gösterir (1G, 1H, 1A, 3A, 1Y, Tüm) — 1G/1H için intraday veri yoksa mock veri gösterilir
- [x] **DESIGN-02**: Dashboard kazananlar/kaybedenler satırlarında prototype'a uygun 40×28px mini sparkline gösterilir
- [x] **DESIGN-03**: Model portföy sayfası 6 strateji kartını gösterir (Temettü Avcısı, Büyüme Lokomotifleri, Defansif Kalkan vb.)
- [x] **DESIGN-04**: Light mode hover durumları theme-aware CSS değişkeni kullanır (hardcoded rgba(255,255,255,.03) kaldırılır)
- [x] **DESIGN-05**: Ölü kod temizlenir: SparklineWidget.tsx silindi, api.ts'ten kullanılmayan metodlar kaldırıldı
- [x] **DESIGN-06**: Dashboard portföy kartı pozisyon yoksa "/portföy" sayfasına yönlendiren boş durum mesajı gösterir

## v2 Requirements

### Genişleme

- BIST100 dışı hisseler (BIST250 vb.)
- Teknik alarm/bildirim (fiyat seviyeleri, gösterge sinyalleri)
- Portföy analitikleri (sektör dağılımı, risk analizi)
- Kripto para takibi
- Çoklu portföy (gerçek vs. deneme portföyü)
- Gemini sidebar sohbet asistanı (her sayfadan erişilebilir)
- Otomatik KAP haberi özeti (her yeni bildirim için kısa Gemini özeti)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Kripto para | Odak dışı, veri karmaşıklığı ekler — v2+ |
| Bildirimler/alarmlar | Kullanıcı istemedi |
| Authentication / kullanıcı hesabı | Kişisel araç, tek kullanıcı |
| Otomatik alım-satım | Karar her zaman kullanıcıda |
| BIST100 dışı hisseler | v1 için likit evren yeterli |
| Native mobil uygulama | Web-first, responsive yeterli |
| Sidebar chat arayüzü | v2'ye bırakıldı — önce on-demand analiz |
| Ücretli LLM API | Gemini 2.0 Flash free tier yeterli |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DASH-01 | Phase 28 | Complete |
| DASH-02 | Phase 28 | Complete |
| DASH-03 | Phase 28 | Complete |
| DASH-04 | Phase 29 | Complete |
| DISC-01 | Phase 28 | Complete |
| DISC-02 | Phase 28 | Complete |
| DESIGN-01 | Phase 34 | Complete |
| DESIGN-02 | Phase 34 | Complete |
| DESIGN-03 | Phase 34 | Complete |
| DESIGN-04 | Phase 34 | Complete |
| DESIGN-05 | Phase 34 | Complete |
| DESIGN-06 | Phase 34 | Complete |
| LLM-01 | Phase 35 | Pending |
| DISC-03 | Phase 36 | Pending |
| STCK-01 | Phase 36 | Pending |
| STCK-02 | Phase 36 | Pending |
| STCK-03 | Phase 36 | Pending |
| STCK-04 | Phase 36 | Pending |
| LLM-02 | Phase 36 | Pending |
| STCK-05 | Phase 36 | Pending |
| STCK-06 | Phase 36 | Pending |
| NEWS-01 | Phase 37 | Pending |
| LLM-03 | Phase 37 | Pending |
| PORT-01 | Phase 38 | Pending |
| PORT-02 | Phase 38 | Pending |
| PORT-03 | Phase 38 | Pending |
| PORT-04 | Phase 38 | Pending |
| PORT-05 | Phase 38 | Pending |
| MODEL-01 | Phase 39 | Pending |
| MODEL-02 | Phase 39 | Pending |
| MODEL-03 | Phase 39 | Pending |
| MODEL-04 | Phase 39 | Pending |
| LLM-04 | Phase 39 | Pending |

**Coverage:**
- v1 requirements: 33 total (23 original + 4 LLM + 6 DESIGN)
- Mapped to phases: 33/33 ✓
- Unmapped: 0

---
*Requirements defined: 2026-05-04*
*Last updated: 2026-05-08 — v5.0: LLM-01..04, DESIGN-01..06 eklendi; faz numaraları 34-39 olarak güncellendi*
