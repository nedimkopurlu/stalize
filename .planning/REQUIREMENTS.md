# Requirements: Stalize v3.0 — Tüm Borsa + Kullanılabilir Platform

*Last updated: 2026-04-27 — v3.0 tanımı tamamlandı*

---

## Milestone Goal

v2.0, veri omurgasını kurdu. v3.0, bunu gerçekten kullanılabilir bir yatırım araştırma ve takip platformuna dönüştürür:

- BIST100'den tüm Borsa İstanbul'a genişle (~500 hisse)
- UI'yi baştan yaz — Robinhood/Midas esinli: temiz, modern, sistem temalı
- Her hisse sayfasını güvenilir ve eksiksiz yap
- Tarama motoru ve portföy modülü ile araştırma → karar → takip döngüsünü kapat

---

## Functional Requirements

### F-01: Evren Genişlemesi — Tüm Borsa İstanbul
- [ ] BIST100 (~100) → Tüm Borsa İstanbul aktif hisseleri (~500) genişlemesi
- [ ] yfinance `.IS` sembol listesi otomatik discovery veya Borsa İstanbul katalog entegrasyonu
- [ ] DataCollector toplu çekim için akıllı rate limiting (batch sleep, retry, adaptive throttle)
- [ ] Hisse metadata: sembol, ad, sektör, piyasa (yıldız/ana/gelişen), BIST30/100/250 üyelik

### F-02: Güvenilir Hisse Sayfası
- [ ] TradingView gömülü grafik (BIST:SYMBOL formatında, interactive)
- [ ] Temel metrikler kartı: F/K, PD/DD, EV/EBITDA, ROE, marj, büyüme, borç/özkaynak
- [ ] Rakip karşılaştırması: aynı sektördeki 3-5 hisse yan yana metrik tablosu
- [ ] KAP + haber akışı: bildirimler ve haberler zaman çizgisinde, başlık + özet + tarih
- [ ] Skor kartı: Al/Tut/Sat sinyali + Temel/Teknik/Haber breakdown puanlarıyla
- [ ] Son fiyat, günlük değişim, 52-hafta aralığı, hacim — anlık güncel

### F-03: Tarama Motoru (Screener)
- [ ] Hazır filtre şablonları: "Düşük F/K", "Momentum", "KAP alımı yakın", "Yüksek temettü", "Güçlü bilanço"
- [ ] Özelleştirilebilir filtre builder: metrik seç, operatör (>, <, =), değer gir, birden fazla kriter AND ile birleştir
- [ ] Filtre setlerini kaydet ve yeniden uygula
- [ ] Sonuç tablosu: hisse, skor, fiyat, değişim, seçilen metrikler — sıralanabilir
- [ ] Sonuçtan tek tıkla hisse sayfasına geçiş

### F-04: Watchlist + Portföy Modülü
- [ ] Watchlist: hisseleri kaydet, skor + fiyat + günlük değişim ile izle
- [ ] Portföy: alım/satım işlemi gir (hisse, tarih, adet, fiyat)
- [ ] Maliyet bazı ve gerçekleşmemiş P&L her pozisyon için
- [ ] Portföy özet: toplam değer, toplam P&L, pozisyon başına ağırlık
- [ ] BIST100 benchmark karşılaştırması (mevcut, korunacak)

### F-05: Dashboard Yeniden Tasarım
- [ ] Piyasa özet kartı: BIST100 endeks, günlük kazananlar/kaybedenler (top 5)
- [ ] Makro bar: USD/TRY, EUR/TRY, altın, petrol — tek satırda
- [ ] Portföy özet kartı (watchlist + portföy)
- [ ] En yüksek skor alan hisseler listesi (tarama motoru bağlantılı)
- [ ] Son KAP bildirimleri akışı

---

## Non-Functional Requirements

### NF-01: UI/UX
- [ ] Robinhood/Midas esini — temiz kartlar, bol beyaz alan (dark'ta: bol koyu alan), net tipografi
- [ ] Sistem teması: cihaz dark/light ayarını takip et, manuel geçiş de mümkün
- [ ] Tutarlı tasarım dili: tüm sayfalarda aynı kart, başlık, tablo, badge bileşenleri
- [ ] Mobil uyumlu (responsive) — yatay scroll yok, 375px'te de okunabilir
- [ ] Sayfa geçişlerinde skeleton loader (boş beyaz flash yok)
- [ ] Her sayfada veri yoksa açıklayıcı boş durum mesajı (spinner loop yok)

### NF-02: Veri Güvenilirliği
- [ ] ~500 hisse için günlük veri güncellemesi başarıyla tamamlanmalı (rate limit toleranslı)
- [ ] Hata durumunda stale veri göster + "son güncelleme X saat önce" etiketi
- [ ] Veri yoksa boş dön — yanlış/mock veri üretme (v2.0'dan devam eden ilke)

### NF-03: Performans
- [ ] Hisse listesi sayfası 2 saniye altında yüklenmeli (pagination ile)
- [ ] Hisse detay sayfası 3 saniye altında yüklenmeli
- [ ] Tarama sonuçları 5 saniye altında dönmeli

---

## Out of Scope (v3.0)

| Feature | Reason |
|---------|--------|
| Fiyat/KAP alarmı ve push bildirimi | v4.0'a ertelendi |
| Otomatik emir iletimi | Kapsam dışı — karar desteği sistemi |
| AI/LLM entegrasyonu | Kullanıcı istemedi |
| Multi-user / auth | Kişisel kullanım |
| Mobil uygulama | Web-first |
| Backtesting / simülasyon | Gerçek veri dışında kabul yok |

---

## Requirements Traceability

| Req | Phase | Status |
|-----|-------|--------|
| F-01 Evren genişlemesi | Phase 17 | planned |
| F-02 Hisse sayfası | Phase 18 | planned |
| F-03 Tarama motoru | Phase 19 | planned |
| F-04 Watchlist + portföy | Phase 20 | planned |
| F-05 Dashboard | Phase 21 | planned |
| NF-01 UI/UX overhaul | Phases 18–21 | planned |
| NF-02 Veri güvenilirliği | Phase 17 | planned |
| NF-03 Performans | Phases 18–21 | planned |
