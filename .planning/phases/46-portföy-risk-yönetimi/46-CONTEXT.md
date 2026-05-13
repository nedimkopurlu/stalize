# Phase 46: Portföy Risk Yönetimi - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Portföy sayfasına sektör dağılımı görselleştirmesi ve yoğunlaşma uyarıları eklenir. Mevcut `getPortfolioRiskGuard` endpoint'i (`/risk/portfolio`) kullanılır — `sector_exposure` ve `positions[].exposure_pct` alanları zaten mevcut. Yeni API veya backend değişikliği gerekmez.

</domain>

<decisions>
## Implementation Decisions

### Sektör Görselleştirme Biçimi
- Yatay bar chart — CSS Modules ile custom progress bar, harici kütüphane gerekmez — RISK-01
- Her satır: sektör adı + yüzde (%) + yatay dolgu bar
- Sıralama: ağırlık büyükten küçüğe
- En büyük 3 sektörü vurgula (bold veya border)

### Yoğunlaşma Uyarıları
- Sektör ağırlığı >%35 ise turuncu/sarı ⚠ + "Bankacılık sektöründe yoğunlaşma: %42 ⚠" mesajı — RISK-02
- Tek hisse ağırlığı >%20 ise aynı format: "AKBNK tek hisse ağırlığı: %24 ⚠" — RISK-03
- Uyarılar pozisyon tablosunun üstünde ayrı `riskAlerts` bölümünde listelenir (K/Z tablosuna müdahale etmez)
- Tek hisse ağırlığı: `PortfolioRiskResponse.positions[].exposure_pct` kullan (backend zaten hesaplamış)

### Veri Kaynağı & Hesaplama
- Mevcut `api.getPortfolioRiskGuard(totalValue)` çağrısı kullan — portfolio page'de `totalValue` hesaplandıktan sonra çağrılır
- `PortfolioRiskResponse.sector_exposure` → sektör dağılımı ve yoğunlaşma kontrolü
- `PortfolioRiskResponse.positions[]` → tek hisse exposure_pct (RISK-03)
- Mevcut `history?.risk_summary` yerine bu API'ye geçilir veya ek fetch olarak eklenir

### Özet Kart Güncellemesi (RISK-04)
- Mevcut sağ-risk kartına (`riskRows`) "Açık pozisyon: X hisse" ve "En büyük 3 sektör: Bankacılık %42, Enerji %18, Sanayi %15" satırları eklenir
- `activePositions` sayısı zaten `positions.filter(p => p.is_active).length` ile hesaplanabilir
- "En büyük 3 sektör" → sector_exposure'u büyükten küçüğe sırala, ilk 3'ü al

### Claude's Discretion
- CSS sınıf isimleri (riskAlerts, sectorBar, sectorRow vb.)
- Bar rengi (var(--accent) veya sektöre özgü renk — tek renk önerilir)
- Uyarı rengi: var(--accent-yellow) veya turuncu (#f59e0b) — mevcut tasarım tokenlarına uygun

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/lib/api.ts:217` → `PortfolioRiskResponse` interface — `sector_exposure[]` (sector, exposure_pct, limit_pct, status) + `positions[]` (symbol, exposure_pct, at_risk)
- `frontend/src/lib/api.ts:1143` → `api.getPortfolioRiskGuard(portfolioValue)` — endpoint zaten var, çağrılmıyor
- `frontend/src/app/portfolio/page.tsx:415` → risk summary kısmi kullanımı (positions_at_risk, risk.active_positions) — risk kartı mevcut (`riskRows` section)
- `frontend/src/app/portfolio/page.tsx:519` → sağ kolon risk bölümü — yeni sektör özeti buraya eklenir

### Established Patterns
- CSS Modules: `page.module.css` co-located
- Data fetching: `useState` + `useEffect` + `loadData()` pattern; birden fazla API çağrısı `Promise.all` ile paralel
- Error/loading: `const [loading, setLoading] = useState(true)` pattern
- Design tokens: `var(--accent-green)`, `var(--accent-red)`, `var(--text-muted)`, `var(--bg-card)`

### Integration Points
- `frontend/src/app/portfolio/page.tsx` — `loadData()` içine `api.getPortfolioRiskGuard(totalValue)` ekle; `riskAlerts` section ve `sectorDist` section render et
- `frontend/src/app/portfolio/page.module.css` — yeni sektör bar ve uyarı CSS sınıfları ekle
- `PortfolioPosition.sector` mevcut değil — sektör verisi `PortfolioRiskResponse.positions[].sector` üzerinden alınır

</code_context>

<specifics>
## Specific Ideas

- Sektör bar formatı: "Bankacılık ████████░░ 42%"
- Uyarı satırı: "⚠ Bankacılık sektöründe yoğunlaşma: %42 (eşik: %35)"
- Özet kart ek satır: "En büyük 3 sektör: Bankacılık %42, Enerji %18, Sanayi %15"
- `getPortfolioRiskGuard` total portfolio value ile çağrılır: `positions.reduce((sum, p) => sum + (p.current_price ?? p.entry_price) * p.quantity, 0)`

</specifics>

<deferred>
## Deferred Ideas

- Sektör bazlı benchmarking (BIST100 sektör ağırlıklarıyla karşılaştırma) — v2
- Pie/donut chart grafik — CSS bar yeterli; grafik kütüphanesi gerekmez

</deferred>

---

*Phase: 46-portföy-risk-yönetimi*
*Context gathered: 2026-05-14*
