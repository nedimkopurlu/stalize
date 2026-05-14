# Yatırım Asistanı

## What This Is

Kişisel bir yatırım asistanı. BIST100 hisseleri, döviz ve altın için fırsat keşfi, portföy takibi ve AI destekli analiz sunar. Sadece bir araç değil — yatırımcıya hem karar desteği verir hem de her adımda neden öyle düşündüğünü açıklayarak borsa öğretir.

## Core Value

Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## Requirements

### Validated

**v6.0 — Karar Güvenliği & Sistem Olgunlaşması (2026-05-14)**
- ✓ Direktif olmayan karar dili — "GÜÇLÜ AL/SAT" etiketleri 5 sayfada güvenli alternatiflerle değiştirildi — v6.0
- ✓ Skor bileşen şeffaflığı — dökümü, N/M bileşen sayacı, eksik veri uyarısı hisse detayda — v6.0
- ✓ Volatilite uyarı ikonu — yüksek volatilitede sarı ikon + tooltip — v6.0
- ✓ Sinyal backtest paneli — /backtest sayfası KPI, 7 sütun, 3 filtre — v6.0
- ✓ Veri tazeliği göstergeleri — stale banner (8h), son güncelleme saati, AI tarih notu, period badge — v6.0
- ✓ Portföy sektör risk yönetimi — CSS bar chart, yoğunlaşma uyarıları (>%35/>%20), risk özet kartı — v6.0
- ✓ İşlem disiplin alanları — kararı bozan koşul, zorunlu çıkış nedeni, kapalı poz. istatistikleri — v6.0

**Önceki milestone'lardan (v2.0–v5.1)**
- ✓ Temel analiz (F/K, PD/DD, net kar, bilanço büyümesi) ile BIST100 hisselerini skorla — v2.0
- ✓ Teknik analiz (RSI, MACD, hareketli ortalamalar) ile BIST100 hisselerini skorla — v2.0
- ✓ İki skoru birleştirerek "bugün ilginç hisseler" listesi sun — v2.0
- ✓ Kullanıcı "Analiz Et" dediğinde AI o hisseyi Türkçe açıklasın (Gemini) — v5.0
- ✓ Genel haber sayfası (Intelligence) + hisse KAP açıklamaları — v5.0
- ✓ Kullanıcı gerçek alım-satımlarını girer (portföy takip) — v5.0
- ✓ Portföy performansını göster (K/Z, BIST100 karşılaştırma) — v5.0
- ✓ İzleme listesi (watchlist) — v5.0
- ✓ Asistan model portföy yönetir (BIST100, AI kararları) — v5.0
- ✓ BIST100 özeti, döviz, altın takibi dashboard — v2.0/v4.0
- ✓ Giriş yok, responsive, tamamen Türkçe — v2.0

### Active (v7.0 — Analiz Kalitesi & Sistem Bütünlüğü)

**Veri Kalitesi:**
- [ ] yfinance BIST fundamental veri güvenilirlik katmanı — sanity check + data quality score
- [ ] Tavan/taban (devre kesici) tespiti ve UI göstergesi
- [ ] Likidite skoru — hacim tutarlılığı, spread proxy, thinly traded uyarısı
- [ ] `safeLabel()` ortak utility'e taşı (StockHelpers.tsx) — 5 dosyada duplikasyon giderilmeli

**Türkçe NLP & Sentiment:**
- [ ] VADER → Türkçe NLP (BERTurk/zemberek) migration
- [ ] KAP duyuru sınıflandırması — temettü, sermaye artırımı, mali sonuçlar, vs.

**Teknik Analiz Derinliği:**
- [ ] Multi-timeframe teknik analiz (günlük + haftalık + aylık)
- [ ] Market Regime Engine — boğa/ayı/yatay/volatil rejim tespiti

**Sektör Bazlı Analiz:**
- [ ] Banka sektörü skor adaptasyonu — NIM, NPL oranı, sermaye yeterlilik rasyosu
- [ ] GYO sektörü skor adaptasyonu — NAV iskonto, kira getirisi
- [ ] Holding sektörü skor adaptasyonu — NAV iskonto hesabı

**Portföy Analizi:**
- [ ] Portföy beta hesabı (BIST100'e göre)
- [ ] Pozisyon büyüklüğü rehberi
- [ ] Holding korelasyon matrisi
- [ ] İşlem sonrası öğrenme döngüsü — geçmiş kararların analizi

**Backtest Kalitesi:**
- [ ] Slipaj + komisyon modellemesi
- [ ] Rejim bazlı sinyal performans analizi

**UI/UX:**
- [ ] Hisse detay sayfa hiyerarşisi yeniden yapılandırması
- [ ] Ön-işlem checklist

### Out of Scope

- Kripto para — odak dışı, veri karmaşıklığı ekler
- Bildirimler/alarmlar — kullanıcı istemedi
- Kullanıcı hesabı / authentication — kişisel araç, tek kullanıcı
- Otomatik alım-satım — karar her zaman kullanıcıda
- BIST100 dışı hisseler — v1 için likit evren yeterli

## Current State: v7.0 IN PROGRESS — Analiz Kalitesi & Sistem Bütünlüğü

**Started:** 2026-05-14  
**Goal:** BIST audit bulgularındaki tüm eksiklikleri kapatmak — Türkçe NLP, veri kalitesi, sektör bazlı scoring, market regime, portföy derinliği, backtest kalitesi

**Previous:** v6.0 Shipped 2026-05-14 | **Archive:** `.planning/milestones/v6.0-ROADMAP.md`

## Context

- Mevcut stack: Next.js (frontend, Vercel), FastAPI (backend, Railway), PostgreSQL
- LLM: Gemini 2.0 Flash (Google) — ücretsiz tier, 15 req/min, 1500 req/gün, Türkçe mükemmel
- Önceki LLM: DeepSeek (kaldırıldı v2.0'da) → Gemini ile yeniden ekleniyor
- Kullanıcı tek kişi, Türkiye'de, BIST yatırımcısı
- Öğrenme hedefi önemli — uygulama sadece veri değil, anlayış da üretmeli
- Prototype Stalize tasarımı uygulandı (v4.0 Phase 29) — tutarsızlıklar giderilecek

## Constraints

- **Verimlilik**: Gemini çağrıları yalnızca on-demand (kullanıcı "Analiz Et") veya günde bir otomatik özet için; gereksiz çağrı yok
- **Kapsam**: BIST100 (100 hisse) — genişleme v2'ye bırakılır
- **Platform**: Web-first, responsive — native app yok
- **Dil**: Tamamen Türkçe
- **LLM Ücretsiz**: Gemini 2.0 Flash free tier kullanılır; ücretli API'ye geçiş gerekmez

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| On-demand AI analizi | API maliyeti kontrolü, gereksiz çağrı yok | ✓ Good — v5.0'da doğrulandı |
| BIST100 evreni | Likit, veri kaliteli, odaklı başlangıç | ✓ Good — sonraki milestone'da genişletilebilir |
| Kripto yok | Kullanıcı odağını dağıtır, v1 için gereksiz | ✓ Good |
| Model portföy özerk | AI kendi kararlarını verir, kullanıcı karşılaştırır | ✓ Good — v5.0'da uygulandı |
| Giriş yok | Kişisel araç, tek kullanıcı, sürtünmeyi azaltır | ✓ Good |
| Gemini 2.0 Flash | Ücretsiz tier yeterli, Türkçe mükemmel, DeepSeek'in yerini alıyor | ✓ Good — v5.0'da doğrulandı |
| LLM güvenli fallback | Gemini quota dolsa endpoint hata değil placeholder döner | ✓ Good — v5.1'de iyileştirildi |
| Direktif olmayan karar dili | "GÜÇLÜ AL/SAT" yerine yorum içermeyen etiket sistemi | ✓ Good — v6.0'da uygulandı; safeLabel 5 sayfada |
| safeLabel inline (tech debt) | 5 dosyada kopya — shared utility'e taşınmadı | ⚠️ Revisit — v7.0'da StockHelpers.tsx'e taşı |

## Evolution

Bu döküman her fazda ve milestone sınırında güncellenir.

**Her faz geçişinde:**
1. Geçersizleşen gereksinimler → Out of Scope'a taşı
2. Doğrulanan gereksinimler → Validated'a taşı
3. Yeni gereksinimler → Active'e ekle
4. Alınan kararlar → Key Decisions'a ekle

**Her milestone sonunda:**
1. Tüm bölümleri gözden geçir
2. Core Value hâlâ doğru mu?
3. Out of Scope'daki gerekçeler hâlâ geçerli mi?

---
*Last updated: 2026-05-14 — v7.0 milestone started: Analiz Kalitesi & Sistem Bütünlüğü*
