# Phase 55 — UI: Hisse Detay Sayfa Yeniden Yapısı & Ön-işlem Checklist

## Özet

Hisse detay sayfasının (`/stocks/[symbol]`) iki ayrı UI geliştirmesi:

1. **UI-01:** Mevcut uzun scroll yapısını hiyerarşik section'lara böl — Hero, Skor Özeti, Teknik, Temel, Haberler, Piyasa Rejimi, İlgili Hisseler — ve sayfanın üstüne yapışkan bir section navigasyonu (anchor linkler) ekle.

2. **UI-02:** Hero section'a "Pozisyon Aç" butonu ekle. Butona tıklandığında 7 maddelik otomatik dolan bir ön-işlem checklist modalı aç: rejim, likidite, genel skor, korelasyon notu, tavan/taban durumu, pozisyon büyüklüğü kuralı, çıkış planı (düzenlenebilir metin alanı). Backend çağrısı yok — tüm veri `page.tsx`'in mevcut state'inden alınır. "Tümünü Onayladım" butonu modalı kapatır.

## Kapsam

- Sadece frontend: `frontend/src/app/stocks/[symbol]/page.tsx` ve `page.module.css`
- Yeni bileşen dosyası yok — modal ve section nav `page.tsx` içinde inline tanımlanır
- Backend değişikliği yok — `api.ts`, `StockHelpers.tsx` değiştirilmez
- Mevcut hiçbir içerik kaldırılmaz — yalnızca düzenleme ve kaplama

## Mevcut Sayfa Yapısı (Phase 55 öncesi)

```
topNav (sticky)
hero (grid: heroLeft + heroRight/scoreCard)
breakdownSection (skor dökümü)
positionSizeSection (PORT-03)
thesisSection (3 kart: tradePlan + reason×2)
chartSection
dossierSection (teknik + temel)
newsDossier
analysisSection (model gerekçeleri)
bottomSection (peers)
```

## Hedef Yapı (Phase 55 sonrası)

```
topNav (sticky, z-index:10)
sectionNav (sticky anchor linkler, z-index:9) ← YENİ
  [Hero] [Skor Özeti] [Teknik] [Temel] [Haberler] [Piyasa Rejimi] [İlgili Hisseler]

<section id="hero">
  hero (mevcut, sadece <section> wrapper eklenir)
  "Pozisyon Aç" butonu hero içine eklenir ← YENİ

<section id="skor-ozeti">
  breakdownSection + positionSizeSection + thesisSection

<section id="teknik">
  chartSection + dossierSection[teknik kard]

<section id="temel">
  dossierSection[temel kard]

<section id="haberler">
  newsDossier

<section id="piyasa-rejimi">
  YENİ section — MarketRegimeResponse'dan ADX/EMA200/ATR değerleri içeren kart

<section id="ilgili-hisseler">
  analysisSection + bottomSection (peers)
```

## Teknik Kararlar

### Section Nav
- `<nav>` elementi, `topNav` div'inin hemen altında, `position: sticky; top: <topNav height>px; z-index: 9`
- Anchor linkler: `href="#hero"` vb. — Next.js App Router ile uyumlu, hash navigasyonu
- Aktif section `IntersectionObserver` ile belirlenir (threshold: 0.2)
- Mobilde overflow-x: auto, scroll-snap

### Section Wrapper
- Mevcut `<section className={styles.hero}>` korunur, sadece `<section id="hero">` wrapper eklenmez — bunun yerine mevcut `<section>` elementlerine `id` attribute eklenir
- `<section id="skor-ozeti">` için birden fazla mevcut section birleştirilir, yani bir `<div id="skor-ozeti">` wrapper eklenir (section semantiği zaten var)

### Piyasa Rejimi Section (YENİ)
- `regime` state'i (`MarketRegimeResponse`) zaten yükleniyor
- `MarketRegimeResponse`: `{ regime, date, adx, ema200, atr }`
- Kart: rejim adı + renk, ADX değeri, EMA200 değeri, ATR değeri
- `regime` null ise section hiç gösterilmez

### Pre-trade Checklist Modal
- State: `const [checklistOpen, setChecklistOpen] = useState(false)`
- Modal: `position: fixed; inset: 0; z-index: 100` — backdrop blur
- 7 madde, her biri: ikon karakteri + etiket + otomatik dolu değer + `<input type="checkbox">`
- Madde 7 (Çıkış Planı): ayrıca `<textarea>` ile pre-fill, kullanıcı düzenleyebilir
- "Tümünü Onayladım" butonu: `onClick={() => setChecklistOpen(false)}`
- X butonu ve backdrop click de kapatır
- `disabled` olmayan her checkbox başlangıçta unchecked
- Korelasyon maddesi: sabit metin, checkbox kullanıcı kendisi işaretler

### "Pozisyon Aç" Butonu Konumu
- `heroLeft` div'inin altına, `<RegimeBadge>` sonrasına eklenir
- Stil: `analyzeBtn` gibi ama yeşil ton — ayrı CSS class `positionBtn`

## Bağımlılıklar

- Bu phase hiçbir yeni API endpoint veya backend değişikliği gerektirmez
- `regime`, `positionSize`, `technical`, `s` (StockDetail.stock), `decision` state'leri zaten `loadStock()` tarafından yükleniyor

## Gereksinimler

- UI-01: Section hiyerarşisi ve sticky nav
- UI-02: Ön-işlem checklist modal

## Plan Yapısı

- **55-01 (Wave 1):** Section hiyerarşisi — id ekleme, section nav bileşeni, yeni "Piyasa Rejimi" section'ı, CSS
- **55-02 (Wave 2, depends: 55-01):** Pre-trade checklist modal — state, bileşen, "Pozisyon Aç" butonu, CSS
