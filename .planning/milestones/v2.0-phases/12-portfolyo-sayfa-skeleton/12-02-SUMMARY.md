---
plan: 12-02
phase: 12-portfolyo-sayfa-skeleton
status: complete
implemented_by: codex
---

# Plan 12-02 Summary: PerformanceCalendar ve BistComparisonChart Skeleton

## Status: ✅ Complete (Codex tarafından uygulandı)

## Uygulanan Değişiklikler

**frontend/src/components/PerformanceCalendar.tsx**
- 12 aylık günlük hücre grid — gri (boş), yeşil (pozitif pnl_pct), kırmızı (negatif)
- Boş dizi ile çökme olmaz

**frontend/src/components/BistComparisonChart.tsx**
- lightweight-charts ile iki çizgi: portföy ve benchmark (BIST100)
- Gerçek API verisi: portfolioSeries ve benchmarkSeries prop'ları

**frontend/src/app/portfolio/page.tsx**
- Her iki bileşen entegre edilmiştir

## Must-Have Doğrulaması

- ✅ PerformanceCalendar 12 aylık grid render eder
- ✅ BistComparisonChart lightweight-charts LineChart render eder
- ✅ Her iki bileşen /portfolio sayfasında entegre
