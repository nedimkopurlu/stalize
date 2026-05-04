# Requirements: Yatırım Asistanı

**Defined:** 2026-05-04
**Core Value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## v1 Requirements

### Dashboard

- [ ] **DASH-01**: Kullanıcı BIST100 endeks özetini görür (günlük değişim, hacim)
- [x] **DASH-02**: Kullanıcı 5-10 döviz çiftini takip eder (USD/TRY, EUR/TRY, GBP/TRY vb.)
- [ ] **DASH-03**: Kullanıcı altın fiyatlarını takip eder (gram, ons, çeyrek, yarım, tam)
- [ ] **DASH-04**: Kullanıcı portföy özetini görür (toplam değer, günlük değişim)

### Keşif & Tarama

- [ ] **DISC-01**: Kullanıcı BIST100 hisselerini temel + teknik skora göre filtreler ve sıralar
- [ ] **DISC-02**: Kullanıcı "bugün ilginç hisseler" listesini görür (yüksek skor = öne çıkar)
- [ ] **DISC-03**: Kullanıcı bir hisseye tıklayıp detay sayfasına gider

### Hisse Detay

- [ ] **STCK-01**: Kullanıcı hissenin fiyat grafiğini görür (7g, 1ay, 3ay, 1y)
- [ ] **STCK-02**: Kullanıcı temel metrikleri görür (F/K, PD/DD, net kar, bilanço büyümesi) — her metriğin yanında ne anlama geldiğini açıklayan tooltip/açıklama
- [ ] **STCK-03**: Kullanıcı teknik göstergeleri görür (RSI, MACD, hareketli ortalamalar) — yanında açıklama
- [ ] **STCK-04**: Kullanıcı "Analiz Et" butonuna basınca AI o hisseye özel Türkçe analiz üretir (on-demand)
- [ ] **STCK-05**: Kullanıcı hissenin KAP açıklamalarını görür
- [ ] **STCK-06**: Kullanıcı hissenin basın haberlerini görür

### Haberler

- [ ] **NEWS-01**: Kullanıcı tüm BIST haberlerini tek sayfada görür (KAP + basın, tarih sıralı)

### Portföy

- [ ] **PORT-01**: Kullanıcı alım işlemi girer (hisse, lot, fiyat, tarih)
- [ ] **PORT-02**: Kullanıcı satım işlemi girer
- [ ] **PORT-03**: Kullanıcı açık pozisyonlarını ve kâr/zararını görür (TL ve % olarak)
- [ ] **PORT-04**: Kullanıcı portföy performansını BIST100 endeksiyle karşılaştırır
- [ ] **PORT-05**: Kullanıcı izleme listesine (watchlist) hisse ekler/çıkarır

### Model Portföy

- [ ] **MODEL-01**: Asistan haftalık model portföy oluşturur (BIST100 evreni, tamamen özerk)
- [ ] **MODEL-02**: Her alım/satım kararı gerekçesiyle birlikte tarihli olarak kaydedilir
- [ ] **MODEL-03**: Kullanıcı model portföyün tüm geçmişini görür (hangi tarihte ne alındı/satıldı, neden)
- [ ] **MODEL-04**: Kullanıcı kendi portföyünün performansını model portföyle karşılaştırır

## v2 Requirements

### Genişleme

- BIST100 dışı hisseler (BIST250 vb.)
- Teknik alarm/bildirim (fiyat seviyeleri, gösterge sinyalleri)
- Portföy analitikleri (sektör dağılımı, risk analizi)
- Kripto para takibi
- Çoklu portföy (gerçek vs. deneme portföyü)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Kripto para | Odak dışı, veri karmaşıklığı ekler — v2+ |
| Bildirimler/alarmlar | Kullanıcı istemedi |
| Authentication / kullanıcı hesabı | Kişisel araç, tek kullanıcı |
| Otomatik alım-satım | Karar her zaman kullanıcıda |
| BIST100 dışı hisseler | v1 için likit evren yeterli |
| Native mobil uygulama | Web-first, responsive yeterli |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DASH-01 | Phase 28 | Pending |
| DASH-02 | Phase 28 | Complete |
| DASH-03 | Phase 28 | Pending |
| DASH-04 | Phase 29 | Pending |
| DISC-01 | Phase 30 | Pending |
| DISC-02 | Phase 30 | Pending |
| DISC-03 | Phase 30 | Pending |
| STCK-01 | Phase 30 | Pending |
| STCK-02 | Phase 30 | Pending |
| STCK-03 | Phase 30 | Pending |
| STCK-04 | Phase 30 | Pending |
| STCK-05 | Phase 30 | Pending |
| STCK-06 | Phase 30 | Pending |
| NEWS-01 | Phase 31 | Pending |
| PORT-01 | Phase 32 | Pending |
| PORT-02 | Phase 32 | Pending |
| PORT-03 | Phase 32 | Pending |
| PORT-04 | Phase 32 | Pending |
| PORT-05 | Phase 32 | Pending |
| MODEL-01 | Phase 33 | Pending |
| MODEL-02 | Phase 33 | Pending |
| MODEL-03 | Phase 33 | Pending |
| MODEL-04 | Phase 33 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23/23 ✓
- Unmapped: 0

**Phase mapping notes:**
- DASH-01, DASH-02, DASH-03 are mapped to Phase 28 (Veri Altyapısı) because they require the data pipeline to exist before Phase 29 (Dashboard) can render them. Phase 29 consumes the data; Phase 28 produces it.
- DASH-04 is mapped to Phase 29 (Dashboard) because it depends on Phase 32 portföy data; its UI home is the dashboard screen.

---
*Requirements defined: 2026-05-04*
*Last updated: 2026-05-04 — traceability assigned by roadmapper (v4.0, Phases 28–33)*
