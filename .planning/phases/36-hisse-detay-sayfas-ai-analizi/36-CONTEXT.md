# Phase 36: Hisse Detay Sayfası + AI Analizi - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Requirements: DISC-03, STCK-01..04, LLM-02

Bu faz üç net teslimatı kapsar:
1. **Backend**: `POST /stocks/{symbol}/analyze` endpoint — `gemini_service.generate()` kullanarak hisse için Türkçe on-demand analiz üretir; response önbelleğe alınmaz (önbellek frontend'de session-scoped state ile sağlanır)
2. **Frontend - Analiz Et butonu**: `/stocks/[symbol]` sayfasına "Analiz Et" butonu + analiz paneli eklenir; aynı session'da ikinci kez basılmadan yeni istek gönderilmez (useState ile önbellek)
3. **Frontend - Tooltip**: Temel metrikler (F/K, PD/DD, ROE, Net Marj, Borç/Özkaynak, EV/FAVÖK) ve teknik göstergeler için Türkçe açıklama tooltip'leri eklenir

DISC-03 (hisse listesinden detay sayfasına navigasyon) zaten çalışıyor — `/stocks/[symbol]` route mevcut, linker `stocks/page.tsx`'te zaten var. Bu fazda ek iş gerekmez.

STCK-01 (fiyat grafiği) zaten implemente edilmiş — LineChart ve periyot seçici `page.tsx`'te mevcut. Bu fazda ek iş gerekmez.

</domain>

<decisions>
## Implementation Decisions

### Backend: `/stocks/{symbol}/analyze` endpoint

- **Method**: `POST` (idempotent değil, her çağrıda Gemini'ye gider; önbellek frontend sorumluluğunda)
- **Router**: `backend/app/api/stocks.py` — mevcut stocks router'ına eklenir
- **Import**: `from app.services.gemini_service import gemini_service`
- **Prompt**: Hisse verisini (sembol, ad, sektör, fiyat, günlük değişim, temel skor, teknik skor, öneri) derleyip Türkçe analiz isteği gönderir
- **Response shape**: `{"symbol": str, "analysis": str, "cached": false, "generated_at": ISO8601}`
- **Fallback**: `gemini_service.generate()` zaten fallback mesajı döner, 500 fırlatmaz — endpoint bunu olduğu gibi döner
- **No DB dependency** for the analyze endpoint — sadece `Stock` ve `Fundamental` tablosundan veri çeker (mevcut DB session pattern ile)

### Frontend: Analiz Et butonu + panel

- **State**: `const [analysis, setAnalysis] = useState<string | null>(null)` + `const [analyzeLoading, setAnalyzeLoading] = useState(false)`
- **Önbellek**: `analysis !== null` ise buton disable veya "Yenile" modu — aynı session'da ikinci istek gitmez (LLM-02 gereği)
- **API**: `api.analyzeStock(symbol)` → `POST /stocks/${symbol}/analyze` — `api.ts`'e eklenir
- **Yerleşim**: "Analiz Et" butonu Score Card'ın altına (hero section sağ kolon) — kullanıcı fiyat ve skor gördükten sonra analiz ister
- **Analiz paneli**: Butonun altında yeni `analysisPanel` section — `analysis` state dolu olduğunda render olur
- **Loading state**: Buton disabled + "Analiz ediliyor..." text

### Frontend: Tooltip'ler

- **Uygulama**: CSS-only tooltip (`:hover::after` + `data-tooltip` attribute) — no extra dependency
- **Kapsam**: 
  - Temel metrikler: F/K, PD/DD, ROE, Net Marj, Borç/Özkaynak, EV/FAVÖK
  - Teknik metrikler: RSI, MACD (teknik section'da gösteriliyorsa)
- **Türkçe tanımlar**:
  - F/K: "Fiyat/Kazanç — hisse fiyatının hisse başı kâra oranı. Düşük değer ucuz hisseye işaret edebilir."
  - PD/DD: "Piyasa Değeri/Defter Değeri — şirket değerinin özkaynaklara oranı. 1'in altı genellikle ucuz sayılır."
  - ROE: "Özkaynak Kârlılığı — şirketin özkaynaklarıyla ne kadar kâr ettiği. Yüksek değer iyidir."
  - Net Marj: "Net Kâr Marjı — gelirin yüzde kaçının kâra dönüştüğü. Yüksek değer iyidir."
  - Borç/Özkaynak: "Kaldıraç oranı. Düşük değer daha az finansal risk anlamına gelir."
  - EV/FAVÖK: "Şirket Değeri/FAVÖK — değerleme çarpanı. Düşük değer ucuzluğa işaret edebilir."
- **CSS**: `page.module.css`'e tooltip stilleri eklenir (mevcut `fundLabel` class'ına `title` attribute ile de yapılabilir — daha basit, SSR-uyumlu)
- **Karar**: HTML `title` attribute kullanılır — CSS module complexity eklemeden tarayıcı native tooltip sağlar; faz kapsamını minimal tutar

</decisions>

<code_context>
## Existing Code Insights

### Backend integration points
- `backend/app/api/stocks.py` — mevcut router, `from app.services.gemini_service import gemini_service` import edilecek
- Son endpoint `get_stock_peers` (satır ~370-419) — yeni `analyze_stock` endpoint onun altına eklenir
- DB session pattern: `db: AsyncSession = Depends(get_db)` — aynı pattern kullanılır
- `gemini_service.generate(prompt)` → `str` (ya Gemini yanıtı ya FALLBACK_MESSAGE) — async

### Frontend integration points
- `frontend/src/app/stocks/[symbol]/page.tsx` — 645 satır, hero section sağ kolon (satır 369-426) Score Card içeriyor — "Analiz Et" butonu `scoreCardDivider`'dan sonra eklenir (satır ~402)
- `frontend/src/lib/api.ts` — `analyzeStock(symbol: string)` metodu ve `StockAnalysisResponse` interface eklenir
- CSS: `frontend/src/app/stocks/[symbol]/page.module.css` — mevcut, `analyzeBtn`, `analyzePanel`, `analyzeText` class'ları eklenir
- `StockFundamentals` interface (satır ~239 api.ts) — değişiklik gerekmez

### Mevcut state pattern (page.tsx satır 141-150)
```typescript
const [detail, setDetail] = useState<StockDetail | null>(null);
const [technical, setTechnical] = useState<TechnicalResult | null>(null);
// ... aynı pattern ile:
const [analysis, setAnalysis] = useState<string | null>(null);
const [analyzeLoading, setAnalyzeLoading] = useState(false);
```

### Mevcut Score Card yapısı (page.tsx ~satır 370-426)
Score Card sonu:
```tsx
<div className={styles.scoreCardRows}>
  {/* target price, upside, stop loss satırları */}
</div>
// buraya "Analiz Et" butonu + analiz paneli eklenir
```

</code_context>

<specifics>
## Implementation Notes

- `analyzeStock` API call: `apiFetch<StockAnalysisResponse>('POST /stocks/${symbol}/analyze')` — `apiFetch` GET varsayılan, method override gerekebilir; mevcut `apiFetch` implementasyonunu kontrol et
- Gemini prompt'u: sembol, şirket adı, sektör, güncel fiyat, günlük değişim %, teknik skor, temel skor, öneri bilgisi içermeli — yeterli bağlam için
- Test: backend için `tests/test_stocks_analyze.py` (mock gemini_service) + frontend için manuel test (E2E)
- `title` attribute tooltip: `<span className={styles.fundLabel} title="F/K açıklaması">F/K</span>` — herhangi CSS değişikliği gerektirmez

</specifics>

<deferred>
## Deferred

- RSI/MACD tooltip'leri — teknik section'da gösterilen değerlerin yanında; bu fazda sadece temel metrikler yapılır (STCK-03 teknik göstergeler section'ı mevcut sayfada yok, zaten Phase 36 kapsamı dışında)
- Analiz önbelleği localStorage'a kalıcı kayıt — session-scoped yeterli (LLM-02 gereği)
- Analysis streaming (chunk-by-chunk) — v2'ye bırakıldı

</deferred>
