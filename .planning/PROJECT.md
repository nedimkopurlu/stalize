# Stalize — Gerçek Veri BIST100 Analiz Terminali

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

## Current Milestone: v3.0 — (Tanımlanmadı)

**Sonraki adım:** `/gsd:new-milestone` ile v3.0 hedeflerini belirle

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

### Active

(v3.0 için yeni gereksinimler — `/gsd:new-milestone` ile tanımlanacak)

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

**v2.0 teslim durumu (2026-04-27):**
- 16 faz, 42 plan, 24/24 gereksinim tamamlandı
- Backend: ~730K satır Python | Frontend: ~4.6K satır TypeScript
- 57 aktif route, 17/17 teknik test geçiyor, TypeScript sıfır hata

**Altyapı:**
- FastAPI + SQLAlchemy async + PostgreSQL
- Next.js frontend (App Router)
- APScheduler arka plan işleri
- KAP parser, portföy snapshot omurgası, EMA teknik analiz motoru

**Aktif veri kaynakları:**
- 1. KAP (şirket bildirimleri — birincil)
- 2. Resmi kurumlar: Borsa İstanbul, TCMB, TÜİK, HMB, MKK, Takasbank, TEFAS (9 aktif)
- 3. Global + yerel haber: Reuters, Bloomberg, FT, CNBC, Investing, BloombergHT, Ekonomim, Dunya

**Teknik borç (v3.0 için):**
- Pydantic V2 ConfigDict geçişi
- 5 fazda formal VERIFICATION.md eksik
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

---
*Last updated: 2026-04-27 — v2.0 milestone tamamlandı (16 faz, 24/24 gereksinim)*
