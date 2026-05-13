# Phase 46: Portföy Risk Yönetimi - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 46-portföy-risk-yönetimi
**Areas discussed:** Sektör görselleştirme, Uyarı konumu & tasarımı, Veri kaynağı, Özet kart

---

## Sektör Görselleştirme Biçimi

| Option | Description | Selected |
|--------|-------------|----------|
| Yatay bar chart (CSS) | Custom progress bar, harici kütüphane yok | ✓ |
| Liste (sadece metin + %) | En basit yaklaşım | |
| Pasta/donut grafik | Görsel ama yeni kütüphane gerektirir | |

**User's choice:** Yatay bar chart (CSS Modules ile)
**Notes:** [auto] Recommended — no external library, consistent with existing CSS patterns.

---

## Uyarı Konumu & Tasarımı

| Option | Description | Selected |
|--------|-------------|----------|
| Pozisyon tablosu üstünde ayrı section | Tabloya müdahale etmez, göze çarpar | ✓ |
| Özet kart içinde | Kompakt ama kalabalık olabilir | |
| Modal/tooltip | Kullanıcı görmeyebilir | |

**User's choice:** Ayrı riskAlerts bölümü
**Notes:** [auto] Recommended — success criteria "positions üstünde veya ayrı bölümde" diyor.

---

## Veri Kaynağı & Hesaplama

| Option | Description | Selected |
|--------|-------------|----------|
| Mevcut getPortfolioRiskGuard | API zaten var, sector_exposure hazır | ✓ |
| Frontend'de hesapla | Positions'tan manuel sektör grupla | |
| Yeni backend endpoint | Gereksiz efor | |

**User's choice:** getPortfolioRiskGuard endpoint'i kullan
**Notes:** [auto] Recommended — PortfolioRiskResponse.sector_exposure ve positions[].exposure_pct zaten var.

---

## Özet Kart Güncellemesi

| Option | Description | Selected |
|--------|-------------|----------|
| Mevcut risk kartına ekle | Yeni kart yok, compakt | ✓ |
| Ayrı yeni kart oluştur | Daha fazla alan ama layout değişir | |

**User's choice:** Mevcut riskRows section'a ek satırlar
**Notes:** [auto] Recommended — mevcut risk kartı RISK-04 için ideal konum.

---

## Claude's Discretion

- CSS sınıf isimleri
- Bar rengi (tek renk, accent token)
- Uyarı ikon ve renk tonu

## Deferred Ideas

- Sektör bazlı BIST100 benchmark karşılaştırması — v2
- Pie/donut chart — CSS bar yeterli
