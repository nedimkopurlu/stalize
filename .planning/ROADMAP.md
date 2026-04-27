# Roadmap: Stalize Gerçek Veri Finansal Analiz Sistemi

## Milestones

- ✅ **v2.0 Gerçek Veri Çekirdeği** — Phases 01–16 (shipped 2026-04-27)
- 🚀 **v3.0 Tüm Borsa + Kullanılabilir Platform** — Phases 17–21 (başlıyor)

## Phases

<details>
<summary>✅ v2.0 Gerçek Veri Çekirdeği (Phases 01–16) — SHIPPED 2026-04-27</summary>

- [x] Phase 01: Foundation Repair (5 plans) — mock/fake temizlik, routing, UTC
- [x] Phase 02: ML Persistence & Caching (4 plans) — XGBoost disk, requests-cache, diskcache
- [x] Phase 03: LLM Infrastructure (4 plans) — instructor, DeepSeek (sonradan kaldırıldı)
- [x] Phase 04: AI Daily Briefing (3 plans) — APScheduler brifing (sonradan kaldırıldı)
- [x] Phase 05: UI Redesign (5 plans) — dashboard, candlestick, skor tablosu
- [x] Phase 06: Teknik Düzeltmeler (3 plans) — APScheduler, async, pandas, double-count
- [x] Phase 07: Sinyal Kalitesi (4 plans) — ATR stop-loss, hacim ratio, RSI divergence
- [x] Phase 10: Temizlik & Skor (3 plans) — AI/LLM/ML/causal kaldırma, F/45 T/40 N/15
- [x] Phase 11: Model Portföy Backend (3 plans) — ORM, snapshot job, API endpoints
- [x] Phase 12: Portföy Sayfa Skeleton (2 plans) — heatmap + karşılaştırma skeleton
- [x] Phase 13: Dashboard & Glassmorphism (3 plans) — design system, sparklines, sektör dropdown
- [x] Phase 14: Hisse Detay Yeniden Tasarım (3 plans) — CandlestickEMAPanel, FundamentalCard, KAPNewsCard
- [x] Phase 15: Portföy Tamamlama (2 plans) — BIST100 benchmark, BistComparisonChart, heatmap
- [x] Phase 16: EMA Trend Skoru (2 plans) — EMA trend bileşeni TDD, scoring integrity

Full details: `.planning/milestones/v2.0-ROADMAP.md`

</details>

## v3.0 Tüm Borsa + Kullanılabilir Platform

**Hedef:** BIST100'den tüm Borsa İstanbul'a genişle, UI'yi baştan yaz, araştırma → karar → takip döngüsünü kapat.

- [ ] **Phase 17: Evren Genişlemesi** — BIST100 → tüm Borsa İstanbul (~500 hisse), rate limiting, sembol discovery
- [ ] **Phase 18: Hisse Sayfası Overhaul** — TradingView grafik, temel metrikler, rakip karşılaştırma, KAP akışı, skor kartı
- [ ] **Phase 19: UI/UX Foundation** — Robinhood/Midas tasarım sistemi, sistem teması (dark/light), bileşen kütüphanesi, mobil uyumluluk
- [ ] **Phase 20: Tarama Motoru** — hazır filtre şablonları + özelleştirilebilir builder, kaydet/yükle, sıralanabilir sonuç tablosu
- [ ] **Phase 21: Watchlist + Portföy** — izleme listesi, işlem girişi, P&L hesabı, portföy özet

### Phase 17: Evren Genişlemesi
**Hedef:** BIST100 (~100 hisse) kısıtını kaldır; tüm aktif Borsa İstanbul hisselerini (~500) veri tabanına al ve düzenli güncellenebilir hale getir.
- [ ] 17-01: bist_universe.py genişletme — tüm `.IS` sembollerini kapsayan BIST_FULL_UNIVERSE listesi
- [ ] 17-02: DataCollector rate limiting iyileştirmesi — adaptive batch sleep, retry, sembol başına hata izolasyonu
- [ ] 17-03: Hisse metadata enrichment — piyasa (yıldız/ana/gelişen), BIST30/100/250 üyelik flag'leri
- [ ] 17-04: Admin endpoint ve frontend hisse listesi sayfalama — 500 hisseyi yönetilebilir göster

**Başarı Kriterleri:**
- ~500 aktif Borsa İstanbul hissesi veritabanında
- Günlük DataCollector koşusu 400+ hisse için başarıyla tamamlanıyor
- Hisse listesi sayfası 500 hisseyi sayfalama ile <2s yüklüyor
- BIST30/100/250 üyelik filtresi çalışıyor

### Phase 18: Hisse Sayfası Overhaul
**Hedef:** Her hisse için güvenilir ve eksiksiz bir analiz sayfası: TradingView grafik + temel metrikler + rakip karşılaştırma + KAP/haber akışı + skor kartı.
- [ ] 18-01: TradingView gömülü widget — BIST:SYMBOL formatında, interaktif grafik
- [ ] 18-02: Temel metrikler kartı — F/K, PD/DD, EV/EBITDA, ROE, marj, büyüme, borç/özkaynak; backend /fundamentals endpoint genişletme
- [ ] 18-03: Rakip karşılaştırma tablosu — aynı sektörden 3-5 hisse yan yana metrik kıyaslaması
- [ ] 18-04: KAP + haber akışı — bildirimler ve haberler zaman çizgisinde, başlık + özet + kaynak + tarih
- [ ] 18-05: Skor kartı yeniden tasarım — Al/Tut/Sat badge, Temel/Teknik/Haber breakdown, son güncelleme zamanı

**Başarı Kriterleri:**
- TradingView widget her hisse için doğru sembolle yükleniyor
- Temel metrikler veri varsa dolu, yoksa açıklayıcı boş durum gösteriyor
- Rakip tablosu sektör bilgisi olan hisseler için en az 2 rakip gösteriyor
- KAP feed en son 10 bildirimi gösteriyor
- Hisse detay sayfası <3s yükleniyor

### Phase 19: UI/UX Foundation
**Hedef:** Tüm UI'yi Robinhood/Midas esinli modern tasarım sistemine taşı — sistem teması (dark/light otomatik), temiz kartlar, tutarlı tipografi, mobil uyumluluk.
- [ ] 19-01: Tasarım sistemi — CSS değişkenleri yeniden yazımı (glassmorphism kaldır), sistem teması toggle, tipografi seti
- [ ] 19-02: Ortak bileşen kütüphanesi — Card, Badge, Button, Table, Skeleton, EmptyState standart bileşenleri
- [ ] 19-03: Dashboard yeniden tasarım — piyasa özet kartı, kazananlar/kaybedenler, makro bar (USD/TRY, altın, petrol)
- [ ] 19-04: Hisse listesi + navigasyon yeniden tasarım — sidebar, sayfa başlıkları, breadcrumb, mobil uyum

**Başarı Kriterleri:**
- Dark ve light tema cihaz ayarına göre otomatik uygulanıyor, manuel toggle da çalışıyor
- Glassmorphism CSS kaldırıldı, tutarsız stiller temizlendi
- Tüm sayfalarda aynı Card, Badge, Button bileşenleri kullanılıyor
- 375px genişlikte yatay scroll yok, tablo sütunları okunabilir

### Phase 20: Tarama Motoru
**Hedef:** Yatırımcının tüm Borsa İstanbul'u kriterlere göre tarayabildiği screener: hazır filtre şablonları + özelleştirilebilir builder, kaydet/yükle, sıralanabilir sonuç tablosu.
- [ ] 20-01: Backend screener endpoint — çoklu metrik filtresi (>, <, between), sektör/piyasa filtresi, skor filtresi
- [ ] 20-02: Hazır filtre şablonları — "Düşük F/K", "Momentum", "Güçlü Bilanço", "Yüksek Temettü", "KAP Alımı Yakın"
- [ ] 20-03: Özelleştirilebilir filtre builder UI — metrik seç, operatör seç, değer gir, filtreler AND ile birleşir
- [ ] 20-04: Sonuç tablosu + kaydet/yükle — sıralanabilir, filtre seti isimle kaydedilip geri yüklenebilir

**Başarı Kriterleri:**
- Hazır şablonlardan biri uygulandığında <5s sonuç dönüyor
- Özelleştirilebilir builder'da en az 3 farklı metrik kombinasyonu çalışıyor
- Filtre setleri browser'da (localStorage) kalıcı olarak kaydediliyor
- Sonuç tablosundan tek tıkla hisse detay sayfasına geçiş çalışıyor

### Phase 21: Watchlist + Portföy
**Hedef:** Araştırma → karar → takip döngüsünü kapat: izleme listesi (watchlist) + gerçek portföy takibi (işlem girişi, P&L, özet).
- [ ] 21-01: Watchlist backend — hisse kaydet/çıkar, watchlist items API endpoint
- [ ] 21-02: Watchlist UI — izlenen hisseler listesi, skor + fiyat + günlük değişim, hisse sayfasından "izlemeye ekle" butonu
- [ ] 21-03: Portföy işlem girişi — al/sat formu (hisse, tarih, adet, fiyat), işlem geçmişi tablosu
- [ ] 21-04: P&L hesabı ve portföy özet — maliyet bazı, gerçekleşmemiş kazanç/kayıp, pozisyon ağırlıkları, toplam değer

**Başarı Kriterleri:**
- Watchlist'e hisse ekle/çıkar çalışıyor, sayfa yenilemede kalıcı
- Al işlemi girildiğinde P&L doğru hesaplanıyor (güncel fiyat - maliyet bazı)
- Portföy özet kartı toplam değer, toplam P&L ve en büyük 5 pozisyonu gösteriyor
- Portföy sayfası BIST100 benchmark karşılaştırmasını koruyor

---

## Kuzey Yıldızı

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel tüm önemli akışları izleyebilen, tamamen gerçek veriye dayalı bir analiz terminalidir. Amaç günlük trade terminali değil; özellikle 3-12 ay ufkunda daha güçlü hisse seçimi ve portföy yönetimi yaptıran bir karar sistemi kurmak.

**Temel ilkeler:**
1. Mock yok, simülasyon yok, sentetik haber yok.
2. KAP şirket verisinde birinci kaynak.
3. Kaynak önceliği ülkeye göre değil, BIST etkisine göre.
4. Dokunulan her fazda UI tutarsızlığı aynı turda düzeltilir.
5. Veri gelmiyorsa sistem boş döner; yanlış tahmin üretmez.
