# Requirements: Yatırım Asistanı

**Defined:** 2026-05-04
**Updated:** 2026-05-08 — v6.0: KARAR-01..04, BACKTEST-01..04, VERI-01..04, RISK-01..04, GUNLUK-01..04, SKOR-01..03 eklendi
**Core Value:** Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## v1 Requirements

### Dashboard

- [x] **DASH-01**: Kullanıcı BIST100 endeks özeti görür (bugünkü değer, değişim, hacim)
- [x] **DASH-02**: Kullanıcı USD/TRY, EUR/TRY ve diğer önemli çiftlerin anlık değerini görür
- [x] **DASH-03**: Kullanıcı altın fiyatlarını (gram, ons, çeyrek, yarım, tam) görür
- [x] **DASH-04**: Kullanıcı portföyünün günlük değişimini dashboard'dan görür

### Keşif & Skorlama

- [x] **DISC-01**: Kullanıcı teknik ve temel skora göre sıralanmış BIST100 hisselerini görür
- [x] **DISC-02**: Kullanıcı "bugünkü ilginç hisseler" listesini genel skora göre görür
- [x] **DISC-03**: Kullanıcı sektör, öneri ve BIST30/100 gibi filtreleri uygulayabilir

### Hisse Detay

- [x] **STCK-01**: Kullanıcı hisse fiyat grafiğini farklı periyotlarda görür (1G/1H/3A/6A/1Y/5Y)
- [x] **STCK-02**: Kullanıcı temel metrikleri (F/K, PD/DD, ROE, marjlar, borçluluk) görür
- [x] **STCK-03**: Kullanıcı teknik göstergeleri (RSI, MACD, destek/direnç, stop, hedef) görür
- [x] **STCK-04**: Kullanıcı "Analiz Et" butonuna basınca AI hisseyi Türkçe analiz eder (on-demand)
- [x] **STCK-05**: Kullanıcı hisseye ait KAP açıklamalarını ve haberleri görür
- [x] **STCK-06**: Kullanıcı aynı sektördeki benzer hisseleri karşılaştırmalı olarak görür

### Haberler & Zeka

- [x] **NEWS-01**: Kullanıcı tüm BIST haberlerini ve KAP akışını kronolojik sırayla görür
- [x] **NEWS-02**: Kullanıcı günlük AI piyasa özetini dashboard veya intelligence sayfasında görür

### Portföy

- [x] **PORT-01**: Kullanıcı gerçek pozisyonlarını girebilir (hisse, lot, fiyat, tarih, stop, hedef, gerekçe)
- [x] **PORT-02**: Kullanıcı pozisyonu kapatabilir ve gerçek K/Z hesaplanır
- [x] **PORT-03**: Kullanıcı portföy performansını BIST100 ile karşılaştırmalı olarak görür
- [x] **PORT-04**: Kullanıcı izleme listesini (watchlist) yönetir (ekle/çıkar)
- [x] **PORT-05**: Kullanıcı portföy getiri tarihçesini grafik olarak görür

### Model Portföy

- [x] **MODEL-01**: Sistem BIST100 evreninde haftalık model portföy oluşturur
- [x] **MODEL-02**: Kullanıcı model portföyün bu haftaki seçimlerini ve gerekçesini görür
- [x] **MODEL-03**: Kullanıcı model portföyün geçmiş haftalarını görür
- [x] **MODEL-04**: Kullanıcı kendi portföyünü model portföyle karşılaştırır

### LLM Entegrasyonu

- [x] **LLM-01**: Hisse analizi AI tarafından Türkçe yapılır (on-demand)
- [x] **LLM-02**: Günlük piyasa özeti AI tarafından Türkçe üretilir (günde bir, cache'li)
- [x] **LLM-03**: Model portföy haftalık kararları AI tarafından gerekçelendirilerek yazılır
- [x] **LLM-04**: AI analiz başarısız olursa kullanıcı dostu Türkçe fallback mesajı gösterilir

### Görsel Tasarım

- [x] **DESIGN-01**: Uygulama koyu tema finans paneli görünümüyle çalışır
- [x] **DESIGN-02**: Tüm sayfalarda tutarlı renk, tipografi ve boşluk sistemi kullanılır
- [x] **DESIGN-03**: Hisse listesi okunabilir, filtre edilebilir tablo formatında sunulur
- [x] **DESIGN-04**: Mobil (375px) ve tablet (768px) breakpoint'lerde kullanılabilir
- [x] **DESIGN-05**: Loading skeleton'lar ve empty state'ler tüm sayfalarda standart şekilde uygulanır
- [x] **DESIGN-06**: Hardcoded hex renkler yerine CSS değişkenleri kullanılır

## v5.1 Requirements (Tamamlandı)

### UI/UX İyileştirme

- [x] **UI-01**: Dashboard ve hisse listesindeki hardcoded renkler CSS değişkenleriyle değiştirilir
- [x] **UI-02**: Stok, portföy ve watchlist tabloları mobilde yatay kaydırma veya sütun gizleme ile kullanılabilir hale gelir
- [x] **UI-03**: Boş durumlar (empty state) tüm sayfalarda ikon + başlık + açıklama + aksiyon formatında standardize edilir
- [x] **UI-04**: Yükleme mesajları ve hata durumları tüm sayfalarda tutarlı CSS sınıfları ile gösterilir
- [x] **UI-05**: Hisse detay hero bölümü ve fundGrid mobil breakpoint'lerde düzgün görünür

### Veri Doğruluğu

- [x] **DATA-01**: formatTRY ve formatPct fonksiyonları NaN/Infinity değerlerini '—' olarak gösterir
- [x] **DATA-02**: Portföy K/Z hesabındaki null/undefined değerleri güvenli şekilde işlenir
- [x] **DATA-03**: Hisse detay sayfasında temel veri yokken yükleme iskeleti ve 'Yok' etiketi gösterilir

### Eksik Fonksiyonlar

- [x] **FEAT-01**: Hisse detay sayfasında izleme listesine ekle/çıkar butonu çalışır (localStorage)
- [x] **FEAT-02**: Portföy pozisyon formu geçersiz girişlerde kullanıcıyı uyarır
- [x] **FEAT-03**: Portföy sayfasında BIST100 ile karşılaştırma grafiği gösterilir

### AI Kalite

- [x] **AI-01**: Hisse analizi promtu derinleştirilir: valuasyon yorumu, sektör bağlamı, risk/fırsat dengesi açık şekilde ele alınır
- [x] **AI-02**: Günlük piyasa özeti makro bağlam (döviz, faiz, küresel piyasalar) içerir; cache mantığı doğrulanır
- [x] **AI-03**: Model portföy haftalık karar döngüsünde Groq gerekçe kalitesi artırılır; karar logları veritabanına doğru kaydedilir
- [x] **AI-04**: Tüm AI endpoint'lerde hata yönetimi standartlaştırılır; fallback mesajları kullanıcı dostu Türkçe gösterilir

## v6.0 Requirements

### Karar Dili Güvenliği (KARAR)

- [x] **KARAR-01**: Sistem "GÜÇLÜ AL/AL/TUT/SAT/GÜÇLÜ SAT" etiketleri yerine direktif olmayan güvenli etiketler kullanır — "Yüksek Öncelikli İzleme / Pozitif Görünüm / Nötr İzleme / Zayıflayan Görünüm / Riskli Görünüm"
- [ ] **KARAR-02**: Skor gösteriminin yanında veri bütünlüğü göstergesi yer alır — kaç bileşen mevcut, kaçı eksik bilgisi gösterilir
- [ ] **KARAR-03**: Yüksek volatilite veya eksik fundamental verisi olan hisseler için görsel uyarı işareti gösterilir
- [x] **KARAR-04**: Her karar etiketinin yanında etiketin ne anlama geldiğini açıklayan tooltip veya bilgi notu yer alır

### Backtest & Sinyal Performansı (BACKTEST)

- [ ] **BACKTEST-01**: Sinyal performans tablosu: sinyal tarihi, hisse, etiket, 1 haftalık getiri, 1 aylık getiri, BIST100'e göre relatif performans, başarılı mı
- [ ] **BACKTEST-02**: Filtre seçenekleri: dönem (son 1A/3A/6A), karar etiketi, başarı durumu
- [ ] **BACKTEST-03**: Hit ratio özeti görünür: kaç sinyalin tuttuğu (%), ortalama 1 haftalık / 1 aylık getiri
- [ ] **BACKTEST-04**: Sinyal performans verisi yoksa açıklayıcı boş durum gösterilir

### Veri Tazeliği & Sistem Sağlığı (VERI)

- [ ] **VERI-01**: Hisse listesi ve hisse kartlarında son fiyat güncelleme zamanı gösterilir
- [ ] **VERI-02**: Hisse detay sayfasında fundamental veri dönemi etiketi gösterilir (ör. "2024-Q3")
- [ ] **VERI-03**: 8 saatten eski fiyat verisi için görsel uyarı gösterilir
- [ ] **VERI-04**: AI analizinin altına hangi veri tarihine dayandığı notu eklenir

### Portföy Risk Yönetimi (RISK)

- [ ] **RISK-01**: Portföy sayfasında sektör dağılımı görselleştirmesi gösterilir
- [ ] **RISK-02**: Tek sektör ağırlığı >%35 olduğunda yoğunlaşma uyarısı görünür
- [ ] **RISK-03**: Tek hisse ağırlığı >%20 olduğunda yoğunlaşma uyarısı görünür
- [ ] **RISK-04**: Portföy özet kartına toplam pozisyon sayısı ve en büyük 3 sektör bilgisi eklenir

### İşlem Disiplini & Günlüğü (GUNLUK)

- [ ] **GUNLUK-01**: Pozisyon formuna "kararı bozan koşul" metin alanı eklenir
- [ ] **GUNLUK-02**: Pozisyon kapatılırken çıkış nedeni seçimi eklenir: Stop Tetiklendi / Hedefe Ulaştı / Senaryo Bozuldu / Diğer
- [ ] **GUNLUK-03**: Kapalı pozisyonlar listesinde giriş gerekçesi ve çıkış nedeni görünür
- [ ] **GUNLUK-04**: Portfolio sayfasında kapalı pozisyon istatistiği: toplam kapatılan, ortalama K/Z, planlı çıkış oranı

### Skor Açıklanabilirliği (SKOR)

- [ ] **SKOR-01**: Hisse detay sayfasında skor bileşen dökümü görünür: temel/teknik/sentiment'in puana katkısı yüzde ve rakam olarak
- [ ] **SKOR-02**: Bileşen eksikse "Eksik veri — ağırlık yeniden dağıtıldı" uyarısı gösterilir
- [ ] **SKOR-03**: Skor dökümü backend `score-breakdown` API'den dinamik olarak render edilir

## v2 Requirements (Ertelendi)

### Analiz Derinliği

- **ANALIZ-01**: Sektör bazlı değerleme karşılaştırması — hissenin F/K'sı sektör ortalamasıyla gösterilir
- **ANALIZ-02**: Piyasa rejimi motoru — BIST düşüş trendindeyken hisse sinyalleri zayıflatılır
- **ANALIZ-03**: Pozisyon büyüklüğü kalkulatörü — portföy riski bağlamlı önerilen lot miktarı
- **ANALIZ-04**: Kişisel risk profili — agresif/muhafazakar seçimi skor ağırlıklarını etkiler
- **ANALIZ-05**: Teknik analiz bütüncül doğal dil yorumu (30+ indikatörü özetleyen tek cümle)

### Portföy

- **PORT-06**: Temettü takibi — alınan temettüler pozisyon getirisine dahil edilir
- **PORT-07**: Portföy beta / BIST100 korelasyon skoru görsel olarak gösterilir
- **PORT-08**: Yeni pozisyon eklemeden önce portföy etkisi analizi

## Out of Scope

| Feature | Reason |
|---------|--------|
| Kripto para | Odak dışı, veri karmaşıklığı |
| Bildirimler/alarmlar | Kullanıcı istemedi, kişisel araç |
| Kullanıcı hesabı / auth | Tek kullanıcı kişisel araç |
| Otomatik alım-satım | Karar her zaman kullanıcıda |
| BIST100 dışı hisseler | v1 için likit evren yeterli |
| Gerçek zamanlı WebSocket | Polling yeterli, kişisel kullanım |
| Native mobil uygulama | Web-first |
| Sektör bazlı değerleme (v6.0) | Kapsam yönetimi — v2'ye eklendi |
| Piyasa rejimi motoru (v6.0) | Kapsam yönetimi — v2'ye eklendi |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| KARAR-01 | Phase 43 | Complete |
| KARAR-02 | Phase 43 | Pending |
| KARAR-03 | Phase 43 | Pending |
| KARAR-04 | Phase 43 | Complete |
| SKOR-01 | Phase 43 | Pending |
| SKOR-02 | Phase 43 | Pending |
| SKOR-03 | Phase 43 | Pending |
| BACKTEST-01 | Phase 44 | Pending |
| BACKTEST-02 | Phase 44 | Pending |
| BACKTEST-03 | Phase 44 | Pending |
| BACKTEST-04 | Phase 44 | Pending |
| VERI-01 | Phase 45 | Pending |
| VERI-02 | Phase 45 | Pending |
| VERI-03 | Phase 45 | Pending |
| VERI-04 | Phase 45 | Pending |
| RISK-01 | Phase 46 | Pending |
| RISK-02 | Phase 46 | Pending |
| RISK-03 | Phase 46 | Pending |
| RISK-04 | Phase 46 | Pending |
| GUNLUK-01 | Phase 47 | Pending |
| GUNLUK-02 | Phase 47 | Pending |
| GUNLUK-03 | Phase 47 | Pending |
| GUNLUK-04 | Phase 47 | Pending |

**Coverage:**
- v6.0 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-04*
*Last updated: 2026-05-08 — v6.0 Karar Güvenliği & Sistem Olgunlaşması eklendi (23 yeni requirement)*
