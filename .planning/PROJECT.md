# Stalize — Borsa İstanbul Analiz Terminali

## What This Is

Stalize, BIST100 odaklı ama BIST'i etkileyen yerel ve küresel akışları birlikte okuyabilen, tamamen gerçek veriye dayalı bir finansal analiz terminalidir. Sistem teknik, temel, KAP, makro ve haber/olay verilerini tek karar yüzeyinde toplar. Veri yoksa boş döner; mock, simülasyon veya sentetik haber üretmez.

## Core Value

Gerçek ve denetlenebilir veriyle çalışan, orta ve uzun vadeli yatırım kararlarını güçlendiren bir BIST100 analiz ve portföy işletim sistemi kur.
Ana kullanım odağı: dashboard-first, hisse seçimi ve portföy yönetimi.

## Design Philosophy

Stalize'da tasarım ayrı bir katman değil, ürün mantığının parçasıdır.

- Arayüzün tek amacı yatırım kararını hızlandırmak olacak.
- Aynı veri aynı görsel dilde sunulacak; sayfalar kendi başına farklı ürün gibi davranmayacak.
- Büyük vitrin alanları, gereksiz hero blokları ve bilgi tekrarı kabul edilmeyecek.
- Her fazda dokunulan ekranlarda bulunan tasarım tutarsızlıkları aynı iş paketinde düzeltilecek.
- Dashboard-first, sade, kurumsal ve modern bir terminal hissi korunacak.

## Investment Philosophy

Sistem beş katmanla bakar:

1. **TEMEL** — F/K, PD/DD, ROE, marjlar, borçluluk, büyüme
2. **TEKNİK** — trend, momentum, ATR, hacim, RSI, MACD, yapı
3. **ŞİRKET OLAYLARI** — KAP bildirimi, finansal sonuç, temettü, geri alım, yatırım, ihale
4. **MAKRO** — TCMB, TÜİK, HMB, emtia, faiz, döviz, piyasa rejimi
5. **HABER ETKİSİ** — resmi kaynak + yerel/global medya, etki büyüklüğüne göre sıralı

**Odak:** günlük trade sinyali değil; özellikle 3-12 ay ufkunda, gerektiğinde daha kısa veya daha uzun elde tutulabilecek daha sağlam pozisyon kararları.

## User Fit

Bu ürün şu kullanıcı profiline göre şekilleniyor:

- ana ekran olarak dashboard kullanmak isteyen
- borsa dışı bilgi kalabalığı istemeyen
- hisse seçimi, piyasa takibi ve portföy yönetimini birlikte görmek isteyen
- trade yerine orta vadeli ve uzun vadeli karar desteği arayan
- sistemin kendi haftalık model portföyünü kurmasını ama kişisel portföyünü ayrı yönetmek isteyen

## Shipped: v2.0 — Gerçek Veri Çekirdeği ✅

**Tamamlandı:** 2026-04-27 — 16 faz, 42 plan, 24/24 gereksinim

**Teslim edilenler:**
- Tüm mock/simülasyon fallback'ler temizlendi; sistem gerçek veri yoksa boş döner
- KAP + TCMB + TÜİK + HMB + Borsa İstanbul + MKK + Takasbank + TEFAS omurgası
- Explainable skor motoru (Temel %45 + Teknik %40 + Haber %15) + EMA trend bileşeni
- Haftalık model portföy sistemi (review, öz değerlendirme, değişim günlüğü, karar bandı)
- Kişisel portföy — ayrı yüzey, benchmark karşılaştırma, günlük snapshot
- Glassmorphism terminal arayüzü — dashboard, hisse detay, portföy, glassmorphism design system

## Shipped: v3.0 — Tüm Borsa + Kullanılabilir Platform ✅

**Tamamlandı:** 2026-04-28 — 5 faz, 9 plan

**Teslim edilenler:**
- BIST100 kısıtı kaldırıldı; 399 aktif Borsa İstanbul hissesi, rate limiting, hata izolasyonu
- Hisse sayfası: TradingView gömülü grafik, EV/EBITDA, rakip karşılaştırma, 10 KAP haberi
- Sistem teması auto-detect (prefers-color-scheme), manuel toggle, Tarama + Watchlist nav
- Tarama motoru: /screener endpoint + frontend, 4 hazır şablon, özelleştirilebilir builder, localStorage
- İzleme listesi: /watchlist sayfası (localStorage), hisse sayfasından toggle

## Requirements

### Validated

- ✓ FastAPI + PostgreSQL + Next.js monorepo omurgası çalışıyor — v1.0
- ✓ BIST100 veri çekimi ve temel teknik akışlar mevcut — v1.0
- ✓ KAP feed tabanlı şirket olayı altyapısı mevcut — v1.0
- ✓ Teknik sinyal katmanında ATR, hacim oranı, RSI divergence mevcut — v1.1
- ✓ AI/LLM çekirdeği kaldırıldı; pure veri analizi yeterli — v2.0
- ✓ Tüm mock/simülasyon fallback'ler kaldırıldı; gerçek veri zorunlu — v2.0
- ✓ KAP + 8 resmi kaynak ingest omurgası (TCMB, TÜİK, HMB, MKK, Takasbank, TEFAS, Borsa İstanbul) — v2.0
- ✓ Explainable skor motoru F/45 T/40 N/15 + EMA trend bileşeni — v2.0
- ✓ Haftalık model portföy + öz değerlendirme + günlük snapshot — v2.0
- ✓ Kişisel portföy ayrı yüzey + BIST100 benchmark karşılaştırma — v2.0
- ✓ Glassmorphism terminal arayüzü — dashboard, hisse detay, portföy — v2.0
- ✓ 399 aktif Borsa İstanbul hissesi; rate limiting + hata izolasyonu ile güvenli çekim — v3.0
- ✓ TradingView gömülü grafik + EV/EBITDA + rakip karşılaştırma + 10 KAP haberi — v3.0
- ✓ Sistem teması auto-detect (prefers-color-scheme), manuel toggle — v3.0
- ✓ Tarama motoru: /screener endpoint, 4 şablon, özelleştirilebilir builder, localStorage — v3.0
- ✓ İzleme listesi: localStorage tabanlı, hisse sayfasından toggle — v3.0

### Active (v4.0)

*(Henüz tanımlanmadı — `/gsd:new-milestone` ile başlat)*

### Out of Scope

### Out of Scope

| Feature | Reason |
|---------|--------|
| Otomatik emir iletimi | Sistem karar desteği verir, emir vermez |
| Multi-user erişim | Kişisel kullanım |
| OAuth / kayıt sistemi | Gerek yok |
| Mobil uygulama | Web-first |
| AI/LLM briefing | Kaldırıldı — pure veri analizi yeterli (v2.0) |
| Causal knowledge graph | Kaldırıldı — kullanılmıyor, karmaşıklık ekliyor (v2.0) |
| XGBoost fiyat tahmini | Kaldırıldı — veri yetersizliği, güvenilmez (v2.0) |
| Simülasyon/backtesting çıktısı | Gerçek veri dışında kabul yok |
| Operasyonel debug panellerinin ana dashboard'da görünmesi | Son kullanıcı odağına hizmet etmiyor |

## Context

**v3.0 teslim durumu (2026-04-28):**
- 21 faz toplam, 51 plan, v3.0: 5 faz / 9 plan
- Backend: FastAPI + SQLAlchemy async + PostgreSQL; /screener + /peers endpoint eklendi
- Frontend: Next.js App Router; screener + watchlist sayfaları, TradingView iframe, infinite scroll
- Stock model: is_bist250 + market_tier kolonları; alembic migration 003
- TypeScript sıfır hata

**Altyapı:**
- FastAPI + SQLAlchemy async + PostgreSQL
- Next.js frontend (App Router)
- APScheduler arka plan işleri
- KAP parser, portföy snapshot omurgası, EMA teknik analiz motoru

**Aktif veri kaynakları:**
- 1. KAP (şirket bildirimleri — birincil)
- 2. Resmi kurumlar: Borsa İstanbul, TCMB, TÜİK, HMB, MKK, Takasbank, TEFAS (9 aktif)
- 3. Global + yerel haber: Reuters, Bloomberg, FT, CNBC, Investing, BloombergHT, Ekonomim, Dunya

**Teknik borç (v4.0 için):**
- Pydantic V2 ConfigDict geçişi
- Glassmorphism CSS kaldırma (deferred — kullanıcı mevcut tasarımı beğeniyor)
- Watchlist backend persistence yok (localStorage only)
- Screener performance optimization (500 hisse sub-query join)
- Makro parser kalibrasyon (TCMB/TÜİK kırılgan uçlar)

## Constraints

- **Gerçek veri zorunlu**: mock, simülasyon, sentetik olay yok
- **Kaynak önceliği**: ülkeye göre değil, BIST etkisine göre; şirket olayında KAP birinci
- **LLM yok**: sistem kural tabanlı ve veri tabanlı çalışır
- **Python**: 3.9
- **Çalışma ortamı**: lokal geliştirme, localhost servisleri

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI/LLM kaldır | güvenilir veri çekirdeğine odak | ✓ v2.0 tamamlandı |
| KAP birincil kaynak | şirket etkisini en doğru yerden almak | ✓ aktif ilke |
| Impact-first kaynak stratejisi | BIST'i etkileyen haber ülke fark etmeksizin önemli | ✓ aktif ilke |
| Simülasyon yasak | veri gelmiyorsa boş dönmek daha güvenli | ✓ aktif ilke |
| Önce veri güvenilirliği, sonra UI | yanlış verinin güzel görünmesi değer üretmez | ✓ aktif ilke |
| Dashboard-first sade UX | kullanıcı önce hisse seçimi ve piyasa odağını görmeli | ✓ aktif ilke |
| Haftalık model portföy | sistem sadece analiz değil, haftalık karar masası da sunmalı | ✓ v2.0 tamamlandı |
| Model portföy öz değerlendirme | sistem geçen haftanın zayıflığını okuyup sonraki haftada adapte olmalı | ✓ v2.0 tamamlandı |
| Ayrı kişisel portföy | kullanıcının gerçek portföyü sistem portföyünden ayrı yönetilmeli | ✓ v2.0 tamamlandı |
| Faz içi tasarım temizliği | teknik ilerleme sırasında görülen UI tutarsızlığı ertelenmez | ✓ aktif ilke |
| EMA 50/200 blend (60/40) | orta vadeli trend sinyalini teknik skora yansıt | ✓ v2.0 tamamlandı |
| Glassmorphism terminal | koyu tema, sade, kurumsal operatör terminali hissi | ✓ v2.0 tamamlandı |
| bist_full_universe.py statik liste | yılda 1-2 güncelleme yeterli, otomatik discovery karmaşıklık ekliyor | ✓ v3.0 tamamlandı |
| Watchlist localStorage tabanlı | backend gerektirmiyor, kişisel kullanım için yeterli | ✓ v3.0 tamamlandı |
| TradingView iframe embed | free widget, BIST:SYMBOL format çalışıyor, sıfır bakım | ✓ v3.0 tamamlandı |
| Screener iki aşamalı (SQL + Python) | SQL hız + Python esnekliği; Fundamental join karmaşıklığını azaltır | ✓ v3.0 tamamlandı |

---
*Last updated: 2026-04-28 — v3.0 milestone tamamlandı (5 faz, 9 plan)*
