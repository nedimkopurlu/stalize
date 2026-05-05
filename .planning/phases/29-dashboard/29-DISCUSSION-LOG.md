# Phase 29: Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-05
**Phase:** 29-dashboard
**Areas discussed:** Eski dashboard, Layout, Widget içeriği, Portföy widget, Veri yenileme, BIST100 yapısı

---

## Mevcut dashboard (page.tsx)

| Option | Description | Selected |
|--------|-------------|----------|
| Sıfırdan yaz | Tamamen sil, yeni market API'lerine bağlı temiz dashboard yaz | ✓ |
| Koruyarak güncelle | Mevcut yapıyı koru, sadece API çağrılarını değiştir | |

**User's choice:** Sıfırdan yaz  
**Notes:** Eski kodun hiçbir parçası korunmaz.

---

## Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Satırlar halinde | BIST100, döviz, altın ayrı bloklar | |
| Esnek grid | BIST100 geniş banner + altında döviz/altın yan yana | ✓ |

**User's choice:** Esnek grid  

---

## Widget içeriği

| Option | Description | Selected |
|--------|-------------|----------|
| Fiyat + değişim | Sadece rakamlar | |
| Fiyat + değişim + ok rengi | ▲/▼ yön göstergesi | ✓ |

**User's choice:** Fiyat + değişim + ok rengi

---

## Portföy widget (DASH-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Boş durum placeholder | Alan var, "yakında" mesajı | ✓ |
| Tamamen atla | Phase 32'ye kadar görünmez | |

**User's choice:** Boş durum placeholder

---

## Veri yenileme

| Option | Description | Selected |
|--------|-------------|----------|
| Sadece yüklenince | Bir kez çeker | |
| Otomatik yenileme (30sn) | Her 30 saniyede güncellenir | ✓ |

**User's choice:** Otomatik yenileme (30sn)

---

## BIST100 widget

| Option | Description | Selected |
|--------|-------------|----------|
| Geniş banner (tam satır) | Sayfanın en üstünde full-width | ✓ |
| Diğer widget'larla eşit kart | Grid içinde bir kart | |

**User's choice:** Geniş banner

---

## Claude's Discretion

- Sayı formatı (ondalık, binlik ayraç)
- Loading skeleton tasarımı
- Error state yaklaşımı (per-card vs sayfa geneli)
- Hangi 6 döviz çiftinin sıralanacağı

## Deferred Ideas

- BIST100 sparkline grafiği
- Döviz alarm / trend notification
- Altın tarihsel grafik
