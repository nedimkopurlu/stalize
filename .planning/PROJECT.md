# Yatırım Asistanı

## What This Is

Kişisel bir yatırım asistanı. BIST100 hisseleri, döviz ve altın için fırsat keşfi, portföy takibi ve AI destekli analiz sunar. Sadece bir araç değil — yatırımcıya hem karar desteği verir hem de her adımda neden öyle düşündüğünü açıklayarak borsa öğretir.

## Core Value

Kullanıcının "bu hisseyi neden almalıyım?" sorusuna hem veriyle hem açıklamayla cevap vermek — karar kullanıcıda, anlayış asistanda.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Keşif & Analiz**
- [ ] Temel analiz (F/K, PD/DD, net kar, bilanço büyümesi) ile BIST100 hisselerini skorla
- [ ] Teknik analiz (RSI, MACD, hareketli ortalamalar) ile BIST100 hisselerini skorla
- [ ] İki skoru birleştirerek "bugün ilginç hisseler" listesi sun
- [ ] Kullanıcı "Analiz Et" dediğinde AI o hisseyi Türkçe açıklasın (on-demand, verimli API kullanımı)
- [ ] Her metriğin yanında ne anlama geldiğini açıkla (öğretici mod)

**Haberler**
- [ ] Genel haber sayfası (tüm BIST haberlerini göster)
- [ ] Hisse detay sayfasında o hisseye ait KAP açıklamaları ve basın haberleri

**Portföy**
- [ ] Kullanıcı gerçek alım-satımlarını girer (hisse, lot, fiyat, tarih)
- [ ] Portföy performansını göster (kazanç/kayıp, BIST100 ile karşılaştırma)
- [ ] İzleme listesi (watchlist) — henüz almadığı ama takip ettiği hisseler

**Model Portföy**
- [ ] Asistan kendi model portföyünü özerk olarak yönetir (BIST100, haftalık güncelleme)
- [ ] Neden o hisseyi aldığını/sattığını kaydet
- [ ] Tüm değişiklik geçmişi tarihli olarak sakla
- [ ] Kullanıcı kendi portföyünü model portföyle karşılaştırabilsin

**Dashboard**
- [ ] BIST100 özeti (endeks, bugünkü hareketler)
- [ ] Döviz takibi (USD/TRY, EUR/TRY, GBP/TRY ve diğer çiftler — toplamda 5-10)
- [ ] Altın takibi (gram, ons, çeyrek, yarım, tam)
- [ ] Portföy özeti

**UX**
- [ ] Giriş yok — direkt açılır
- [ ] Hem mobil hem masaüstü (responsive)
- [ ] Türkçe arayüz

### Out of Scope

- Kripto para — odak dışı, veri karmaşıklığı ekler
- Bildirimler/alarmlar — kullanıcı istemedi
- Kullanıcı hesabı / authentication — kişisel araç, tek kullanıcı
- Otomatik alım-satım — karar her zaman kullanıcıda
- BIST100 dışı hisseler — v1 için likit evren yeterli

## Current Milestone: v5.0 — LLM Entegrasyonlu Yatırım Asistanı

**Goal:** Gemini 2.0 Flash ile LLM entegrasyonu ekle; prototype tasarımına tam uyum sağla; tüm eksik sayfaları (Keşif, Haberler, Portföy, Model Portföy) tamamla.

**Target features:**
- Gemini 2.0 Flash entegrasyonu (ücretsiz, on-demand hisse analizi + günlük piyasa özeti + model portföy gerekçeleri)
- Frontend tasarım tutarsızlıkları giderilmesi (prototype'a tam uyum)
- Keşif & Hisse Detay sayfası (skorlu liste + AI analizi)
- Haberler sayfası (KAP + basın + günlük Gemini özeti)
- Portföy sayfası (alım-satım, P&L, watchlist)
- Model Portföy sayfası (özerk AI kararları + Türkçe gerekçe)

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
| On-demand AI analizi | API maliyeti kontrolü, gereksiz çağrı yok | — Pending |
| BIST100 evreni | Likit, veri kaliteli, odaklı başlangıç | — Pending |
| Kripto yok | Kullanıcı odağını dağıtır, v1 için gereksiz | — Pending |
| Model portföy özerk | AI kendi kararlarını verir, kullanıcı karşılaştırır | — Pending |
| Giriş yok | Kişisel araç, tek kullanıcı, sürtünmeyi azaltır | — Pending |
| Gemini 2.0 Flash | Ücretsiz tier yeterli, Türkçe mükemmel, DeepSeek'in yerini alıyor | — Pending |
| LLM güvenli fallback | Gemini quota dolsa endpoint hata değil placeholder döner | — Pending |

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
*Last updated: 2026-05-08 after v5.0 milestone start — LLM entegrasyonu + frontend iyileştirme*
