# Requirements: Yatırım Asistanı

**Defined:** 2026-05-04
**Core Value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## v1 Requirements

### Dashboard

- [ ] **DASH-01**: Kullanıcı BIST100 endeks özetini görür (günlük değişim, hacim)
- [ ] **DASH-02**: Kullanıcı 5-10 döviz çiftini takip eder (USD/TRY, EUR/TRY, GBP/TRY vb.)
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
| DASH-01 | TBD | Pending |
| DASH-02 | TBD | Pending |
| DASH-03 | TBD | Pending |
| DASH-04 | TBD | Pending |
| DISC-01 | TBD | Pending |
| DISC-02 | TBD | Pending |
| DISC-03 | TBD | Pending |
| STCK-01 | TBD | Pending |
| STCK-02 | TBD | Pending |
| STCK-03 | TBD | Pending |
| STCK-04 | TBD | Pending |
| STCK-05 | TBD | Pending |
| STCK-06 | TBD | Pending |
| NEWS-01 | TBD | Pending |
| PORT-01 | TBD | Pending |
| PORT-02 | TBD | Pending |
| PORT-03 | TBD | Pending |
| PORT-04 | TBD | Pending |
| PORT-05 | TBD | Pending |
| MODEL-01 | TBD | Pending |
| MODEL-02 | TBD | Pending |
| MODEL-03 | TBD | Pending |
| MODEL-04 | TBD | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: TBD (roadmapper will assign)
- Unmapped: 23 pending roadmap

---
*Requirements defined: 2026-05-04*
*Last updated: 2026-05-04 after initial definition*
