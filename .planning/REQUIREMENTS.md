# Requirements: Yatırım Asistanı

**Defined:** 2026-05-04
**Updated:** 2026-05-08 — v5.1: UI-01..05, DATA-01..03, FEAT-01..03, AI-01..04 eklendi; traceability güncellendi
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
- [x] **PORT-02**: Kullanıcı satım işlemi girer; kapalı pozisyon gerçekleşen kâr/zararla görünür
- [ ] **PORT-03**: Kullanıcı açık pozisyonlarını ve kâr/zararını görür (TL ve % olarak)
- [ ] **PORT-04**: Kullanıcı portföy performansını BIST100 endeksiyle karşılaştırır
- [ ] **PORT-05**: Kullanıcı izleme listesine (watchlist) hisse ekler/çıkarır; watchlist canlı fiyatlarla görünür

### Model Portföy

- [ ] **MODEL-01**: Asistan haftalık model portföy oluşturur (BIST100 evreni, tamamen özerk)
- [ ] **MODEL-02**: Her alım/satım kararı Gemini tarafından yazılan Türkçe gerekçesiyle birlikte tarihli olarak kaydedilir
- [ ] **MODEL-03**: Kullanıcı model portföyün tüm geçmişini görür (hangi tarihte ne alındı/satıldı, neden)
- [ ] **MODEL-04**: Kullanıcı kendi portföyünün performansını model portföyle karşılaştırır

### LLM Entegrasyonu (Gemini 2.0 Flash)

- [x] **LLM-01**: Backend'de Gemini 2.0 Flash servis katmanı çalışır (google-generativeai SDK, quota aşılırsa graceful fallback)
- [ ] **LLM-02**: Kullanıcı hisse detay sayfasında "Analiz Et" butonu ile on-demand Türkçe Gemini analizi alır; önbellek ile tekrar istek gitmez
- [x] **LLM-03**: Sistem her sabah otomatik olarak Gemini'den kısa günlük piyasa özeti üretir; dashboard'da ve haberler sayfasında görünür
- [ ] **LLM-04**: Model portföy haftalık karar döngüsünde Gemini portföy değişikliklerini Türkçe gerekçeyle açıklar

### Frontend Tasarım

- [x] **DESIGN-01**: Dashboard BIST100 grafiği tüm 6 periyot tabını gösterir (1G, 1H, 1A, 3A, 1Y, Tüm) — 1G/1H için intraday veri yoksa mock veri gösterilir
- [x] **DESIGN-02**: Dashboard kazananlar/kaybedenler satırlarında prototype'a uygun 40×28px mini sparkline gösterilir
- [x] **DESIGN-03**: Model portföy sayfası 6 strateji kartını gösterir (Temettü Avcısı, Büyüme Lokomotifleri, Defansif Kalkan vb.) ✅
- [x] **DESIGN-04**: Light mode hover durumları theme-aware CSS değişkeni kullanır (hardcoded rgba(255,255,255,.03) kaldırılır) ✅
- [x] **DESIGN-05**: Ölü kod temizlenir: SparklineWidget.tsx silindi, api.ts'ten kullanılmayan metodlar kaldırıldı ✅
- [x] **DESIGN-06**: Dashboard portföy kartı pozisyon yoksa "/portföy" sayfasına yönlendiren boş durum mesajı gösterir ✅

### UI/UX İyileştirme (v5.1)

- [ ] **UI-01**: Tüm 7 sayfada (dashboard, stocks, stock-detail, intelligence, portfolio, watchlist, model-portfolio) piksel düzeyinde görsel geçiş yapılır; layout/spacing/renk tutarsızlıkları giderilir
- [ ] **UI-02**: Mobile responsive düzeltmeler: tüm sayfalarda 375px ve 768px kırılım noktaları çalışır
- [ ] **UI-03**: Boş durumlar (empty states) standardize edilir — her sayfada tutarlı mesaj ve yönlendirme butonu
- [ ] **UI-04**: Yükleme skeleton ve hata durumları tüm sayfalarda tutarlı gösterilir
- [ ] **UI-05**: Hisse detay sayfası hero ve fundGrid görsel sorunları tamamen çözülür

### Veri & Hesaplama Doğruluğu (v5.1)

- [ ] **DATA-01**: Portföy K/Z hesabı doğrulanır; kapalı pozisyonlar dashboard'da ve portföy sayfasında yanlış görünmez
- [ ] **DATA-02**: Null/undefined veri durumunda tüm sayfalarda güvenli fallback — NaN veya çöken render yerine anlamlı placeholder
- [ ] **DATA-03**: Hisse detay teknik/temel metriklerinde eksik veri görsel placeholder ile gösterilir (boş kutu yerine)

### Eksik & Yarım Fonksiyonlar (v5.1)

- [ ] **FEAT-01**: İzleme listesi: hisse detay sayfasında "İzlemeye Ekle/Çıkar" butonu çalışır, watchlist sayfasıyla localStorage üzerinden senkron
- [ ] **FEAT-02**: Portföy pozisyon ekleme formu validasyon + başarılı işlem sonrası UI refresh doğru çalışır
- [ ] **FEAT-03**: Portföy karşılaştırma grafiği (BIST100 vs portföy) veri geldiğinde düzgün render edilir

### AI Kalite & Güvenilirlik (v5.1)

- [ ] **AI-01**: Hisse analizi promtu derinleştirilir: valuasyon yorumu, sektör bağlamı, risk/fırsat dengesi açık şekilde ele alınır
- [ ] **AI-02**: Günlük piyasa özeti makro bağlam (döviz, faiz, küresel piyasalar) içerir; cache mantığı doğrulanır
- [ ] **AI-03**: Model portföy haftalık karar döngüsünde Groq gerekçe kalitesi artırılır; karar logları veritabanına doğru kaydedilir
- [ ] **AI-04**: Tüm AI endpoint'lerde hata yönetimi standartlaştırılır; fallback mesajları kullanıcı dostu Türkçe gösterilir

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
| DESIGN-01 | Phase 34 | ✅ Complete (2026-05-08) |
| DESIGN-02 | Phase 34 | ✅ Complete (2026-05-08) |
| DESIGN-03 | Phase 34 | ✅ Complete (2026-05-08) |
| DESIGN-04 | Phase 34 | ✅ Complete (2026-05-08) |
| DESIGN-05 | Phase 34 | ✅ Complete (2026-05-08) |
| DESIGN-06 | Phase 34 | ✅ Complete (2026-05-08) |
| LLM-01 | Phase 35 | Complete |
| DISC-03 | Phase 36 | Pending |
| STCK-01 | Phase 36 | Pending |
| STCK-02 | Phase 36 | Pending |
| STCK-03 | Phase 36 | Pending |
| STCK-04 | Phase 36 | Pending |
| LLM-02 | Phase 36 | Pending |
| STCK-05 | Phase 37 | Pending (haberler sayfasında, detay sayfasında değil) |
| STCK-06 | Phase 37 | Pending (haberler sayfasında, detay sayfasında değil) |
| NEWS-01 | Phase 37 | Pending |
| LLM-03 | Phase 37 | Complete |
| PORT-01 | Phase 38 | Pending |
| PORT-02 | Phase 38 | Complete |
| PORT-03 | Phase 38 | Pending |
| PORT-04 | Phase 38 | Pending |
| PORT-05 | Phase 38 | Pending |
| MODEL-01 | Phase 39 | Pending |
| MODEL-02 | Phase 39 | Pending |
| MODEL-03 | Phase 39 | Pending |
| MODEL-04 | Phase 39 | Pending |
| LLM-04 | Phase 39 | Pending |
| UI-01 | Phase 40 | Pending |
| UI-02 | Phase 40 | Pending |
| UI-03 | Phase 40 | Pending |
| UI-04 | Phase 40 | Pending |
| UI-05 | Phase 40 | Pending |
| DATA-01 | Phase 41 | Pending |
| DATA-02 | Phase 41 | Pending |
| DATA-03 | Phase 41 | Pending |
| FEAT-01 | Phase 41 | Pending |
| FEAT-02 | Phase 41 | Pending |
| FEAT-03 | Phase 41 | Pending |
| AI-01 | Phase 42 | Pending |
| AI-02 | Phase 42 | Pending |
| AI-03 | Phase 42 | Pending |
| AI-04 | Phase 42 | Pending |

**Coverage:**
- v1 requirements: 33 total (23 original + 4 LLM + 6 DESIGN)
- v5.1 requirements: 12 total (5 UI + 3 DATA + 3 FEAT + 4 AI — wait: 5+3+3+4=15)
- v5.1 mapped: 15/15 ✓
- Total mapped: 48/48 ✓
- Unmapped: 0

---
*Requirements defined: 2026-05-04*
*Last updated: 2026-05-08 — v5.1: UI-01..05, DATA-01..03, FEAT-01..03, AI-01..04 eklendi; Phase 40-42 traceability güncellendi*
