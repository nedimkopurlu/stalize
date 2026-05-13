# Phase 47: İşlem Disiplini & Günlüğü - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Pozisyon açma formuna "kararı bozan koşul" alanı eklenir; pozisyon kapatma diyaloğuna çıkış nedeni seçimi zorunlu hale getirilir; kapalı pozisyonlar listesinde gerekçe ve çıkış nedeni gösterilir; kapalı pozisyon istatistik özeti eklenir. Backend'e `exit_reason` ve `invalidation_condition` alanları eklenir (migration ile).

</domain>

<decisions>
## Implementation Decisions

### Backend Veritabanı Değişiklikleri
- `backend/app/models/portfolio_v2.py` → `exit_reason = Column(String(50), nullable=True)` ve `invalidation_condition = Column(Text, nullable=True)` ekle — GUNLUK-01, GUNLUK-02
- Alembic migration: `ALTER TABLE portfolioposition ADD COLUMN exit_reason VARCHAR(50)` + `ADD COLUMN invalidation_condition TEXT` — nullable, default NULL, mevcut kayıtları bozmaz
- `close_position` endpoint (portfolio_v2.py satır 303+): `exit_reason` parametresini `ClosePositionBody` Pydantic modeline ekle, kaydederken `pos.exit_reason = body.exit_reason` yaz — GUNLUK-02
- `add_position` endpoint: `invalidation_condition` parametresini kabul et, kaydet — GUNLUK-01
- GET /portfolio/positions response'a `exit_reason: string | null` ve `invalidation_condition: string | null` ekle

### Çıkış Nedeni Seçimi (GUNLUK-02)
- Dört seçenek: "Stop Tetiklendi" / "Hedefe Ulaştı" / "Senaryo Bozuldu" / "Diğer"
- `<select>` element, kapatma formunda `exit_reason` state ile kontrol edilir
- "Diğer" seçildiğinde conditional `<textarea>` açılır — `exit_reason_other` state, kısa açıklama için
- "Diğer" seçilmiş ve `exit_reason_other` boşsa handleClosePosition() engellenir — GUNLUK-05 success criterion
- Backend'e gönderilecek değer: "Diğer" ise `"Diğer: [açıklama]"` formatında birleştirilir
- `exit_reason` zorunlu — boş bırakılamaz (handleClosePosition validation)

### Kararı Bozan Koşul Alanı (GUNLUK-01)
- Pozisyon ekleme formuna (`isAddOpen` modal) yeni `invalidation_condition` textarea — zorunlu değil
- Placeholder: "Ör. MACD negatif geçerse veya 90 TL altına sararsa"
- `PositionForm` type'a `invalidation_condition: string` eklenir
- `EMPTY_FORM`'a `invalidation_condition: ''` eklenir
- `handleAddPosition()` içinde trim edilip API body'ye eklenir

### Kapalı Pozisyon Listesi Görünümü (GUNLUK-03)
- Mevcut kapalı pozisyonlar listesi `frontend/src/app/portfolio/page.tsx:closedPositions.map(...)` içinde
- Her pozisyon satırı altında (veya expandable row olarak): italik `rationale` (varsa) + exit_reason badge/label
- Badge format: "Çıkış: Hedefe Ulaştı" — küçük gri veya renkli chip
- Boş rationale için gösterilmez (sadece `exit_reason` gösterilir)
- `PortfolioPosition` interface'e `exit_reason: string | null` ve `invalidation_condition: string | null` eklenir

### Kapalı Pozisyon İstatistik Özeti (GUNLUK-04)
- Kapalı pozisyonlar tablosunun üstünde inline stats bar — ayrı kart değil
- 3 metrik: "Kapatılan: N" | "Ort. K/Z: +X%" | "Planlı Çıkış: %Y"
- Planlı çıkış oranı = (stop + hedef çıkışları) / toplam kapatılan * 100
- Hesaplama: `closedPositions.filter(p => p.exit_reason === 'Stop Tetiklendi' || p.exit_reason === 'Hedefe Ulaştı').length / closedPositions.length * 100`
- "Diğer: [açıklama]" ile başlayanlar planlı değil; "Senaryo Bozuldu" da planlı değil
- Kapalı pozisyon yoksa stats bar gösterilmez

### API Güncellemesi
- `frontend/src/lib/api.ts` → `PortfolioPosition` interface'e `exit_reason: string | null` + `invalidation_condition: string | null` eklenir
- `api.closePosition(id, data)` — `data` type'ı genişletilir: `{ exit_price: number; exit_date: string; exit_reason: string }`
- `api.addPosition(data)` — `data` içine `invalidation_condition?: string` eklenir

### Claude's Discretion
- CSS sınıf isimleri (exitReasonBadge, closedStats, invalidationField)
- Exit reason badge rengi (neutral grey önerilir — red/green yoruma açık)
- Migration dosya adı (timestamp prefix ile Alembic otomatik oluşturur)

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/app/portfolio/page.tsx:22-43` → `PositionForm` type + `EMPTY_FORM` — `invalidation_condition` eklenecek
- `frontend/src/app/portfolio/page.tsx:245-247` → `closeForm` state (`exit_price`, `exit_date`) — `exit_reason` + `exit_reason_other` eklenecek
- `frontend/src/app/portfolio/page.tsx:410-422` → `handleClosePosition()` — exit_reason validation + API call güncellenecek
- `frontend/src/app/portfolio/page.tsx:393` → `handleAddPosition()` — invalidation_condition body'ye eklenecek
- `frontend/src/app/portfolio/page.tsx:406-407` → `activePositions` / `closedPositions` filter — stats bar için kullanılacak
- `backend/app/api/portfolio_v2.py:303` → `close_position()` endpoint — `ClosePositionBody` Pydantic modeli genişletilecek
- `backend/app/models/portfolio_v2.py:9-29` → `PortfolioPosition` model — 2 yeni column eklenecek
- `frontend/src/lib/api.ts:596-616` → `PortfolioPosition` interface — 2 yeni field eklenecek
- `frontend/src/lib/api.ts:1114` → `api.closePosition(id, data)` — data type genişletilecek

### Established Patterns
- Alembic migration: `backend/alembic/` — `alembic revision --autogenerate -m "..."` ile oluşturulur
- CSS Modules: co-located `page.module.css`
- State pattern: `useState<string>` için kontrollü form alanları
- Validation pattern: `handleClosePosition()` başında `if (!exit_reason) return` guard

### Integration Points
- `backend/app/models/portfolio_v2.py` → 2 yeni Column
- `backend/alembic/` → yeni migration dosyası
- `backend/app/api/portfolio_v2.py` → `ClosePositionBody` + `close_position()` + `add_position()` + GET response
- `frontend/src/lib/api.ts` → `PortfolioPosition` interface + `closePosition` + `addPosition`
- `frontend/src/app/portfolio/page.tsx` → form state, render, stats bar
- `frontend/src/app/portfolio/page.module.css` → yeni sınıflar

</code_context>

<specifics>
## Specific Ideas

- Çıkış nedeni select: `<select value={closeForm.exit_reason} onChange={...}>`  `<option value="">Seçiniz…</option>` + 4 seçenek
- "Diğer" koşullu textarea: `{closeForm.exit_reason === 'Diğer' && <textarea value={closeForm.exit_reason_other} ... />}`
- Stats bar format: `Kapatılan: 5 | Ort. K/Z: +3.2% | Planlı Çıkış: %60`
- Backend send format: `exit_reason === 'Diğer' ? 'Diğer: ' + exit_reason_other.trim() : exit_reason`

</specifics>

<deferred>
## Deferred Ideas

- Çıkış nedeni istatistiklerinin backtest dashboard ile entegrasyonu — v2
- Pozisyon gerekçesi için zengin metin editörü — v2

</deferred>

---

*Phase: 47-işlem-disiplini-günlüğü*
*Context gathered: 2026-05-14*
