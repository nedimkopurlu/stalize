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

## Context

- Mevcut stack: Next.js (frontend, Vercel), FastAPI (backend, Railway), PostgreSQL
- Mevcut veri kaynağı: BloombergHT/Foreks API (BIST fiyatları)
- AI: DeepSeek API (on-demand analiz için, verimli kullanılacak)
- Kullanıcı tek kişi, Türkiye'de, BIST yatırımcısı
- Öğrenme hedefi önemli — uygulama sadece veri değil, anlayış da üretmeli

## Constraints

- **Verimlilik**: AI API çağrıları yalnızca kullanıcı "Analiz Et" dediğinde yapılır
- **Kapsam**: BIST100 (100 hisse) — genişleme v2'ye bırakılır
- **Platform**: Web-first, responsive — native app yok
- **Dil**: Tamamen Türkçe

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| On-demand AI analizi | API maliyeti kontrolü, gereksiz çağrı yok | — Pending |
| BIST100 evreni | Likit, veri kaliteli, odaklı başlangıç | — Pending |
| Kripto yok | Kullanıcı odağını dağıtır, v1 için gereksiz | — Pending |
| Model portföy özerk | AI kendi kararlarını verir, kullanıcı karşılaştırır | — Pending |
| Giriş yok | Kişisel araç, tek kullanıcı, sürtünmeyi azaltır | — Pending |

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
*Last updated: 2026-05-04 after initial questioning*
