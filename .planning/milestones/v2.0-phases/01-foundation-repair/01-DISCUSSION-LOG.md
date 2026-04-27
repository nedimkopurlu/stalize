# Phase 1: Foundation Repair - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 01-foundation-repair
**Areas discussed:** KAP Hata Modu, Scoring Ağırlıkları, Router Yapısı

---

## KAP Hata Modu

| Option | Description | Selected |
|--------|-------------|----------|
| Startup'ta hata | Backend hiç başlamasın — feedparser zorunlu dependency | ✓ |
| Çağrıda hata | Backend başlar ama KAP endpoint'i çağrılınca 500 döndürsün | |

**KAP geçici down:**

| Option | Description | Selected |
|--------|-------------|----------|
| Boş liste dönür | Scanner boş sonuç döndürsün, scheduler devam etsin | ✓ |
| Hata fırlat | KAP ulaşılamıyorsa her seferinde exception kaldır | |

**Loglama:**

| Option | Description | Selected |
|--------|-------------|----------|
| WARNING log + devam | Her başarısız tarama için WARNING, scheduler devam | ✓ |
| Sessiz boş liste | Log yazma, sadece boş döndür | |

**Mock kodu:**

| Option | Description | Selected |
|--------|-------------|----------|
| Tamamen silinsin | Mock method kaldırılsın, hiçbir yol ona ulaşamasın | ✓ |
| Kalsin ama çağırılmasın | Dead code olarak bırak | |

**User's choice:** Startup hard fail + geçici outage'da boş liste + WARNING log + mock tamamen sil

---

## Scoring Ağırlıkları

| Option | Description | Selected |
|--------|-------------|----------|
| Scoring.py değerleri kazanır | technical=30%, fundamental=20%, sentiment=15%, causal=20%, ml=15% | |
| Config.py değerleri kazanır | technical=20%, fundamental=25%, ml=20%, sentiment=10%, causal=15%, macro=10% | ✓ |
| Ben belirleyeyim | Kullanıcı özel değer verecekti | |

**WEIGHT_MACRO:**

| Option | Description | Selected |
|--------|-------------|----------|
| macro_score column'u kullan | Stock modelinde varsa dahil et, yoksa 0 say | ✓ |
| Kaldır config'den | WEIGHT_MACRO silinsin | |
| Macro sentimenta ekle | Sentiment_score'un bir parçası olarak değerlendir | |

**Config yeterliliği:**

| Option | Description | Selected |
|--------|-------------|----------|
| Evet, config.py yetsin | scoring.py hardcode değer içermesin | ✓ |
| Env var olarak da ayarlanabilsin | config.py default, .env ile override | |

**User's choice:** config.py kazanır, WEIGHT_MACRO → macro_score, scoring.py tamamen settings'ten okur

---

## Router Yapısı

| Option | Description | Selected |
|--------|-------------|----------|
| Domain gruplama | stocks.py, macro.py, portfolio.py, intelligence.py, causal.py, admin.py | ✓ |
| Mevcut prefix'lere göre | Her URL prefix'i ayrı dosya (10+ küçük router) | |
| Sana bırakıyorum | Claude görüşüne göre böl | |

**endpoints.py sonrası:**

| Option | Description | Selected |
|--------|-------------|----------|
| Silinsin | Tüm içerik taşındıktan sonra dosya kaldırılsın | ✓ |
| Redirection olarak kalsın | Eski dosya sadece import'ları re-export etsin | |

**main.py mount:**

| Option | Description | Selected |
|--------|-------------|----------|
| Her domain router ayrı include_router | 6 ayrı include_router satırı | ✓ |
| Tek aggregator __init__.py | api/__init__.py birleştirsin, main.py tek satır | |

**User's choice:** 6 domain dosya (stocks, macro, portfolio, intelligence, causal, admin), endpoints.py silinsin, her biri ayrı include_router

---

## Claude's Discretion

- Health check endpoint organizasyonu (admin.py mı, standalone mı)
- macro_news.py endpoint'lerinin macro.py mi intelligence.py mi gideceği
- KAP WARNING log mesajı tam metni

## Deferred Ideas

None
