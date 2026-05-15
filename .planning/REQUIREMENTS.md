# Requirements: v7.0 — Analiz Kalitesi & Sistem Bütünlüğü

**Milestone:** v7.0  
**Started:** 2026-05-15  
**Goal:** BIST audit bulgularındaki tüm eksiklikleri kapatmak — veri kalitesi, sektör bazlı scoring, market regime, Türkçe NLP, portföy derinliği, backtest kalitesi  

---

## v1 Requirements

### VKL — Veri Kalitesi

- [x] **VKL-01**: Kullanıcı, yfinance'den gelen BIST fundamental değerleri için USD→TRY sanity check sonucu "düşük güven" uyarısı görür; şüpheli değerlere dayanılarak karar alınmaz
- [x] **VKL-02**: Kullanıcı, her hisse için 0-100 data quality score'u hisse listesinde ve detay sayfasında görür
- [x] **VKL-03**: Kullanıcı, tavan/taban (devre kesici) durumundaki hisseleri fiyat kutusunda renkli badge ile anında fark eder
- [x] **VKL-04**: Kullanıcı, ince piyasalı hisselerde (düşük likidite) otomatik uyarı görür; Amihud illiquidity ratio tabanlı 3 kademeli likidite skoru (yüksek/orta/düşük)

### KAP — Duyuru Sınıflandırması

- [x] **KAP-01**: KAP duyuruları tip koduna göre otomatik kategorize edilir (Finansal Sonuçlar / Temettü / Sermaye Artırımı / İçeriden Öğrenme / Düzenleyici)
- [x] **KAP-02**: Kullanıcı, hisse detay sayfasında KAP duyurularını kategori badge'iyle görür; yüksek etkili kategoriler vurgulanır

### REJ — Market Regime Engine

- [ ] **REJ-01**: Sistem, BIST100 için günlük piyasa rejimini otomatik tespit eder (Boğa / Ayı / Yatay / Volatil) — ADX+EMA200+ATR kural tabanlı, USD-adjusted XU100.IS
- [ ] **REJ-02**: Mevcut piyasa rejimi dashboard'da ve hisse detay sayfasında regime badge olarak gösterilir
- [ ] **REJ-03**: Backtest sonuçları rejim bazında filtrelenebilir (Boğa/Ayı/Yatay/Volatil sinyal performans karşılaştırması)

### SEK — Sektör Bazlı Analiz

- [ ] **SEK-01**: Bankacılık hisseleri sektöre özel skorlanır: F/DD (P/TBV) + ROE ağırlıklı; yanıltıcı standart PE/PB banka sektöründe uygulanmaz
- [ ] **SEK-02**: GYO hisseleri P/B "NAV proxy" skoru alır; UI'da gerçek NAD verisinin mevcut olmadığı açıklama notu gösterilir
- [ ] **SEK-03**: Holding hisseleri halka açık bağlı ortaklık piyasa değerleri toplanarak yaklaşık NAV iskontosu hesaplanır ve skorlamaya yansıtılır

### PORT — Portföy Analizi

- [ ] **PORT-01**: Kullanıcı, portföyünün BIST100'e göre betasını portföy sayfasında görür (252 günlük pencere, 0-3 aralığına kırpılmış)
- [ ] **PORT-02**: Kullanıcı, portföydeki pozisyonlar arası korelasyon matrisini portföy sayfasında görür
- [ ] **PORT-03**: Kullanıcı, her potansiyel pozisyon için volatilite bazlı pozisyon büyüklüğü önerisi görür (portföyün %1-2 risk kuralı, ATR×2 stop mesafesi)

### NLP — Türkçe Sentiment

- [ ] **NLP-01**: VADER kaldırılır; KAP duyuruları mevcut OpenAI GPT-4o-mini entegrasyonu üzerinden Türkçe sentiment analizine tabi tutulur (batch, APScheduler ile)
- [ ] **NLP-02**: RSS haber akışları keyword tabanlı Türkçe kural seti ile sınıflandırılır (pozitif/negatif/nötr); VADER bağımlılığı tamamen kaldırılır

### BACK — Backtest Kalitesi

- [ ] **BACK-01**: Backtest simülasyonu likidite kademesine göre gerçekçi slipaj modeli içerir (BIST30: 10bps, sıra 30-70: 20bps, sıra 70-100: 40bps) + %0.1 komisyon
- [ ] **BACK-02**: Backtest sonuçları rejim bazında ayrılmış olarak sunulur (Boğa/Ayı/Yatay/Volatil dönem performans karşılaştırması)

### UI — Arayüz İyileştirmeleri

- [ ] **UI-01**: Hisse detay sayfası hiyerarşik bölüm yapısına kavuşur (Hero → Skor Özeti → Teknik → Temel → Haberler → Regime → İlgili Hisseler)
- [ ] **UI-02**: Pozisyon açmadan önce kullanıcıya otomatik doldurulmuş 7 maddelik ön-işlem checklist gösterilir (rejim, likidite, skor, korelasyon, tavan/taban, pozisyon büyüklüğü, çıkış planı)

### TECH — Tech Debt

- [x] **TECH-01**: `safeLabel()` helper `StockHelpers.tsx`'e taşınır; inline duplikasyon (3 sayfa: stocks, [symbol], model-portfolio) tek kaynaktan beslenir

---

## Future Requirements

*(Veri erişilebilirliği nedeniyle v7.0'a alınmayan — v8.0 için)*

- Banka NIM/NPL oranları — yfinance'de mevcut değil; KAP finansal tablo scraping gerektirir
- GYO gerçek NAD — SPK'ya bildirilen çeyreklik değerleme raporlarından çekilmesi gerekir
- Multi-timeframe teknik analiz (haftalık + aylık) — on-demand hesaplama performans riski; Phase 4 sonrası benchmarking gerekli
- İşlem sonrası öğrenme döngüsü — geçmiş kararların analizi; yeterli kapalı pozisyon birikimi gerekiyor

---

## Out of Scope

- Kripto para — odak dışı, veri karmaşıklığı ekler
- Bildirimler/alarmlar — kullanıcı istemedi
- Kullanıcı hesabı / authentication — kişisel araç, tek kullanıcı
- Otomatik alım-satım — karar her zaman kullanıcıda
- BIST100 dışı hisseler — v8'e bırakılır
- BERTurk / HuggingFace NLP modeli — Railway 512MB RAM sınırı aşılıyor; OpenAI entegrasyonu yeterli
- KAP finansal tablo scraping (NIM/NPL için) — karmaşıklık; v8.0'a bırakıldı
- Gerçek bid-ask spread verisi — ücretli Borsa İstanbul market data feed gerektirir

---

## Traceability

| Req | Phase | Status |
|-----|-------|--------|
| VKL-01 | Phase 48 | ⬜ Pending |
| VKL-02 | Phase 48 | ⬜ Pending |
| VKL-03 | Phase 49 | ⬜ Pending |
| VKL-04 | Phase 49 | ⬜ Pending |
| KAP-01 | Phase 49 | ⬜ Pending |
| KAP-02 | Phase 49 | ⬜ Pending |
| REJ-01 | Phase 50 | ⬜ Pending |
| REJ-02 | Phase 50 | ⬜ Pending |
| REJ-03 | Phase 54 | ⬜ Pending |
| SEK-01 | Phase 51 | ⬜ Pending |
| SEK-02 | Phase 51 | ⬜ Pending |
| SEK-03 | Phase 51 | ⬜ Pending |
| PORT-01 | Phase 52 | ⬜ Pending |
| PORT-02 | Phase 52 | ⬜ Pending |
| PORT-03 | Phase 52 | ⬜ Pending |
| NLP-01 | Phase 53 | ⬜ Pending |
| NLP-02 | Phase 53 | ⬜ Pending |
| BACK-01 | Phase 54 | ⬜ Pending |
| BACK-02 | Phase 54 | ⬜ Pending |
| UI-01 | Phase 55 | ⬜ Pending |
| UI-02 | Phase 55 | ⬜ Pending |
| TECH-01 | Phase 48 | ⬜ Pending |

---

*Last updated: 2026-05-15 — v7.0 requirements defined (21 requirements, 9 categories)*
