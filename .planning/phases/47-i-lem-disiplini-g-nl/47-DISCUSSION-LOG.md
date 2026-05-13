# Phase 47: İşlem Disiplini & Günlüğü - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 47-işlem-disiplini-günlüğü
**Areas discussed:** Backend migration, Çıkış nedeni davranışı, Kapalı pozisyon listesi, İstatistik özeti konumu

---

## Backend Migration

| Option | Description | Selected |
|--------|-------------|----------|
| Alembic migration (nullable) | ALTER TABLE ile 2 nullable column, mevcut veri korunur | ✓ |
| Default değer ile | Tüm mevcut kayıtlara boş string yazar | |

**User's choice:** Alembic migration, nullable=True
**Notes:** [auto] Recommended — mevcut kayıtlar bozulmaz, NULL kabul edilir.

---

## "Diğer" Textarea Davranışı

| Option | Description | Selected |
|--------|-------------|----------|
| Conditional inline textarea | "Diğer" seçilince açılır, zorunlu | ✓ |
| Modal içinde ayrı adım | Daha karmaşık UX | |
| Her zaman görünür | Gereksiz alan kaplar | |

**User's choice:** Conditional inline textarea
**Notes:** [auto] Recommended — basit ve mevcut form pattern ile uyumlu.

---

## Kapalı Pozisyon Listesi Görünümü

| Option | Description | Selected |
|--------|-------------|----------|
| Inline row altında | Her pozisyon satırının altında rationale + badge | ✓ |
| Expandable/collapsible | Tıklandığında açılır | |
| Ayrı kolon | Tablo çok geniş olur | |

**User's choice:** Inline row altında — italik rationale + exit_reason badge
**Notes:** [auto] Recommended — mobil uyumlu, tablo değişikliği gerekmez.

---

## İstatistik Özeti Konumu

| Option | Description | Selected |
|--------|-------------|----------|
| Tablo üstünde stats bar | Inline 3 metrik, ayrı kart yok | ✓ |
| Ayrı kart/bölüm | Risk kartı gibi ayrı section | |
| Dashboard'da | Portfolio page dışında | |

**User's choice:** Kapalı pozisyonlar tablosunun üstünde inline stats bar
**Notes:** [auto] Recommended — az alan, direkt ilgili bölümde.

---

## Claude's Discretion

- CSS sınıf isimleri
- Exit reason badge rengi
- Migration dosya adlandırması

## Deferred Ideas

- Backtest entegrasyonu — v2
- Zengin metin editörü — v2
