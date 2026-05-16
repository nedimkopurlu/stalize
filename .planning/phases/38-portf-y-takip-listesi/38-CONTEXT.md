# Phase 38: Portföy + Takip Listesi - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Requirements: PORT-01..05

**Durum değerlendirmesi:**
- PORT-01 ✅ — `POST /portfolio/positions` + frontend "Yeni Pozisyon" formu mevcut
- PORT-03 ✅ — Portföy sayfası açık pozisyonları K/Z ile gösteriyor
- PORT-04 ✅ — `GET /portfolio/history` BIST100 karşılaştırma verisi + frontend chart mevcut
- PORT-05 ✅ — `/watchlist` sayfası localStorage + `api.getStocks({symbols})` ile canlı fiyat gösteriyor

**Eksik (bu fazda yapılacak tek şey):**
- PORT-02 ❌ — Satım/pozisyon kapatma işlemi yok. DB modelinde `exit_price`, `exit_date`, `realized_pnl` alanları yok. Backend'de PATCH endpoint yok. Frontend'de "Kapat" butonu yok.

Bu faz yalnızca PORT-02 implementasyonunu kapsar.

</domain>

<decisions>
## Implementation Decisions

### DB Migration: `004_portfolio_position_close_fields.py`

Mevcut `portfolio_positions` tablosuna 3 nullable kolon eklenir:
- `exit_price FLOAT` — çıkış fiyatı (satış fiyatı)
- `exit_date DATE` — satış tarihi
- `realized_pnl FLOAT` — gerçekleşen kâr/zarar TL olarak

ORM model güncellenir: `backend/app/models/portfolio_v2.py` → `PortfolioPosition` class'ına bu 3 kolon eklenir.

### Backend: `PATCH /portfolio/positions/{id}/close`

Pydantic request model:
```python
class PositionClose(BaseModel):
    exit_price: float
    exit_date: date
```

Logic:
1. DB'de pozisyonu bul (is_active=True şartı)
2. 404 if not found
3. Hesapla: `realized_pnl = (exit_price - entry_price) * quantity`
4. Güncelle: `is_active=False`, `exit_price`, `exit_date`, `realized_pnl`
5. `PortfolioChangeLog` kaydı: `action="REMOVE"`, `reason=f"Satış fiyatı: {exit_price}"`
6. Commit
7. Return: `{id, symbol, realized_pnl, status: "closed"}`

### Backend: `GET /portfolio/positions` güncelleme

Kapalı pozisyonları da döner (son 30 günde kapanmış olanlar) — `is_active=True OR (is_active=False AND exit_date >= today-30days)`. Frontend gösterimde açık ve kapalı ayrımı `is_active` field'ına göre yapılır.

Response'a yeni alanlar eklenir:
- `is_active: bool`
- `exit_price: float | None`
- `exit_date: str | None`
- `realized_pnl: float | None`

### Frontend: `api.ts` güncellemesi

`PortfolioPosition` interface'ine eklenir:
```typescript
is_active: boolean;
exit_price: number | null;
exit_date: string | null;
realized_pnl: number | null;
```

Yeni method:
```typescript
closePosition: (id: number, data: { exit_price: number; exit_date: string }) =>
  apiFetch<{ id: number; symbol: string; realized_pnl: number | null; status: string }>(
    `/portfolio/positions/${id}/close`,
    { method: 'PATCH', body: JSON.stringify(data) }
  ),
```

### Frontend: Portföy sayfası — "Kapat" butonu + kapalı pozisyonlar

**Tablo değişikliği:**
- Mevcut positions tablosunda her satıra "Kapat" butonu eklenir (son sütun)
- "Kapat" butonuna basılınca inline modal/form açılır: çıkış fiyatı (pre-filled current_price) + çıkış tarihi (pre-filled today) + "Onayla" / "İptal"
- Onaylanınca `api.closePosition(pos.id, {...})` çağrılır → positions yeniden yüklenir

**Kapalı pozisyonlar bölümü:**
- Açık pozisyonlar tablosunun altına "Geçmiş Pozisyonlar" başlıklı tablo eklenir
- Sadece `is_active === false` pozisyonlar burada gösterilir
- Kolonlar: Sembol | Çıkış Tarihi | Alış | Satış | Adet | Gerçek K/Z (TL) | Gerçek K/Z%
- Veri yoksa "Son 30 günde kapatılmış pozisyon yok" mesajı

**State:**
- `const [closingId, setClosingId] = useState<number | null>(null)` — hangi pozisyon kapatılıyor
- `const [closeForm, setCloseForm] = useState<{exit_price: string; exit_date: string}>({exit_price: '', exit_date: todayISO()})`
- Mevcut state'e eklenir; büyük refactor yok

**Test**: Backend için `tests/test_portfolio_close.py` — PATCH endpoint tests with mock DB

</decisions>

<code_context>
## Existing Code Insights

### Backend
- `backend/app/models/portfolio_v2.py` — `PortfolioPosition` class (satır ~10-27): `is_active = Column(Boolean, default=True)`. 3 kolon eklenecek.
- `backend/app/api/portfolio_v2.py` — `@router.get("/portfolio/positions")` satır 87-122: `is_active==True` filtresi değişecek. `@router.post("/portfolio/positions")` satır 232-274: örnek alınacak. PATCH endpoint satır ~275'ten sonra eklenir.
- `backend/alembic/versions/` — son migration `003_add_market_tier_bist250.py`. Yeni: `004_portfolio_position_close_fields.py`
- `verify_api_key` dependency: `GET /portfolio/positions` ve `GET /portfolio/history` bunu kullanmıyor, `POST /portfolio/positions` kullanıyor. PATCH endpoint de `verify_api_key` kullanacak.

### Frontend
- `frontend/src/lib/api.ts` — `PortfolioPosition` interface satır 297-309. `addPosition` satır 747-761. `closePosition` metodu eklenecek.
- `frontend/src/app/portfolio/page.tsx` — 717 satır. Pozisyon tablosu satır 508-577. Tablo header satır 510-522 (9 kolon var). Yeni "İşlem" kolonu eklenecek (10. kolon). Close form ve kapalı pozisyonlar bölümü eklenir.
- `frontend/src/app/portfolio/page.module.css` — kapalı pozisyonlar tablosu için CSS class'ları eklenir.

### apiFetch method override pattern
`apiFetch<T>(path, options?)` — `FetchOptions` type'ı check edilmeli. Phase 36'da `POST /stocks/{symbol}/analyze` için `{ method: 'POST' }` çalıştı. Aynı pattern PATCH için kullanılacak: `{ method: 'PATCH', body: JSON.stringify(data) }`.

</code_context>

<specifics>
## Implementation Notes

- Alembic migration: `op.add_column('portfolio_positions', sa.Column('exit_price', sa.Float(), nullable=True))` x 3
- `realized_pnl` hesaplama: `(exit_price - entry_price) * quantity` (TL bazında, komisyon dahil değil)
- Realized P&L % hesaplama (frontend): `((exit_price - entry_price) / entry_price) * 100`
- Kapalı pozisyonlar sorgusu: `WHERE is_active=False AND exit_date >= today-30days ORDER BY exit_date DESC`
- `GET /portfolio/positions` response değişikliği: sadece `is_active=True` yerine hem açık hem 30 günlük kapalılar döner — mevcut frontend (positions tablosu) `is_active` filtresi ile ayırır

</specifics>

<deferred>
## Deferred

- Kapalı pozisyonların 30 günden eskilerini gösterme (sayfalama) — v2
- Satım işlemi formu için hisse fiyatı auto-fill (yfinance fetch) — kullanıcı manuel giriyor, yeterli
- Portföy export (CSV) — "İhraç et" butonu zaten disabled, v2'ye bırakıldı

</deferred>
