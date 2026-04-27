---
plan: 12-01
phase: 12-portfolyo-sayfa-skeleton
status: complete
implemented_by: codex
---

# Plan 12-01 Summary: Portföy Sayfa Skeleton

## Status: ✅ Complete (Codex tarafından uygulandı)

## Uygulanan Değişiklikler

**frontend/src/app/portfolio/page.tsx**
- /portfolio rotasında AppShell ile tam sayfa render edilir
- api.getPortfolioPositions() ile pozisyonlar yüklenir
- Pozisyon yokken 'Henüz pozisyon yok' boş durum gösterilir
- Her pozisyon için symbol, entry_price, current_price, pnl_pct gösterilir
- Pozisyon ekleme formu (POST /api/portfolio/positions)
- Pozisyon kapatma (DELETE)

**frontend/src/lib/api.ts**
- `PortfolioPosition` v1.2 arayüzü (entry_price, quantity, entry_date, pnl_pct, current_price)
- `PortfolioSnapshot` arayüzü
- `api.getPortfolioPositions()` fonksiyonu

## Must-Have Doğrulaması

- ✅ /portfolio sayfası Sidebar ile render edilir
- ✅ Pozisyon kartları symbol + entry price + current price + P&L% gösterir
- ✅ Boş durum 'Henüz pozisyon yok'
- ✅ PortfolioPosition ve PortfolioSnapshot api.ts'ten export edilir
- ✅ Sidebar 'Portföyüm' linki /portfolio'ya işaret eder
