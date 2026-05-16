# Phase 39: Model Portföy AI Kararları - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Requirements: MODEL-01..04, LLM-04

**Durum değerlendirmesi:**
- MODEL-01 ✅ — `generate_weekly_model_portfolio()` servisi ve APScheduler job mevcut
- MODEL-02 ❌ — Gerekçe şu an `_holding_rationale()` (deterministik string) ile üretiliyor; Gemini kullanılmıyor. Haftalık karar özeti de `_build_review_summary()` ile yazılıyor (Gemini değil)
- MODEL-03 ❌ — Backend'de `get_model_portfolio_history()` mevcut; ancak frontend sayfasında geçmiş görüntüleme yok — sadece güncel hafta gösteriliyor
- MODEL-04 ❌ — Kullanıcının kendi portföy getirisi ile model portföy getirisi karşılaştırması yok
- LLM-04 ❌ — Gemini, model portföy haftalık karar döngüsüne entegre değil

Bu fazda yapılacaklar:
1. LLM-04: `generate_weekly_model_portfolio()` içinde Gemini ile haftalık Türkçe özet/gerekçe üretme
2. MODEL-03: Frontend'de model portföy geçmişi bölümü
3. MODEL-04: Frontend'de basit karşılaştırma kartı (kullanıcı portföyü vs model portföy vs BIST100)

</domain>

<decisions>
## Implementation Decisions

### LLM-04 / MODEL-02: Gemini entegrasyonu — `backend/app/services/model_portfolio.py`

**Nerede**: `generate_weekly_model_portfolio()` fonksiyonunun sonunda, `week.review_summary` atanmadan önce, Gemini çağrısı yapılır.

**Prompt**: Haftalık karar özeti (eklenen/çıkarılan hisseler + portföy durumu) bilgisiyle Türkçe gerekçe istenir:

```python
async def _generate_gemini_rationale(changes: dict, holdings_count: int) -> str:
    """Gemini ile haftalık model portföy değişikliklerini açıkla."""
    added = changes.get("added", [])
    removed = changes.get("removed", [])
    
    prompt_parts = [f"Model portföy bu hafta {holdings_count} hisse içeriyor."]
    if added:
        prompt_parts.append(f"Eklenen hisseler: {', '.join(added[:5])}")
    if removed:
        prompt_parts.append(f"Çıkarılan hisseler: {', '.join(removed[:5])}")
    if not added and not removed:
        prompt_parts.append("Bu hafta portföy kompozisyonunda büyük değişiklik yapılmadı.")
    
    prompt = " ".join(prompt_parts) + (
        " Bu portföy kararlarını yatırımcılara 2-3 cümleyle açıkla. "
        "Türkçe, anlaşılır ve profesyonel bir dil kullan."
    )
    return await gemini_service.generate(prompt)
```

**Nereye yazılır**: Üretilen metin `week.review_summary` field'ına eklenir (mevcut `_build_review_summary()` çıktısının yerine VEYA yanına eklenecek — karar: Gemini çıktısı önce yazılır, deterministic text fallback olarak korunur. Eğer Gemini FALLBACK_MESSAGE dönerse, mevcut `_build_review_summary()` kullanılır).

**Ne zaman çağrılır**: `generate_weekly_model_portfolio()` içinde, hafta kayıt işlemi tamamlandıktan sonra, `db.commit()` öncesinde. Bu async fonksiyon olduğundan doğrudan `await` edilir.

**Fallback**: Gemini FALLBACK_MESSAGE dönerse veya exception oluşursa, mevcut deterministik özet kullanılır. Gemini hatası üretimi bozmaz.

### MODEL-03: Frontend geçmiş bölümü — `frontend/src/app/model-portfolio/page.tsx`

**Yeni komponent**: `ModelPortfolioHistory` — `api.getModelPortfolioHistory(8)` çağırır (son 8 hafta), basit liste olarak gösterir.

**Gösterilecek bilgiler**: Hafta | Portföy Getirisi | BIST100 | Değişim özeti (review_summary + change_summary)

**Yerleşim**: `AiPortfolioSection` ve `strategiesSection` arasına yerleştirilir.

**API types**: `ModelPortfolioHistoryResponse` tipi api.ts'te mevcut (satır ~487). `weeks` array'i `ModelPortfolioWeekSummary` interface'ine göre şekillendirilmiş.

### MODEL-04: Karşılaştırma kartı — `frontend/src/app/model-portfolio/page.tsx`

**Minimal implementasyon**: `AiPortfolioSection` içinde, mevcut holdings ve stats bölümlerinin altına, basit 3-sütunlu karşılaştırma kartı eklenir.

**Veri kaynağı**:
- Model portföy getirisi: `data.week.portfolio_return_pct` (zaten yüklü, `ModelPortfolioCurrentResponse`'dan)
- BIST100: `data.week.benchmark_return_pct` (zaten yüklü)
- Kullanıcı portföyü: `api.getPortfolioHistory(30)` → `risk_summary.latest_portfolio_return_pct`

**Görünüm**: Küçük 3-sütunlu kart — "Kullanıcı Portföyü | Model Portföy | BIST100" — yüzde değerleri renkli

**State**: `const [userReturnPct, setUserReturnPct] = useState<number | null>(null)` — non-blocking fetch

</decisions>

<code_context>
## Existing Code Insights

### Backend
- `backend/app/services/model_portfolio.py` — `generate_weekly_model_portfolio()` satır ~362-508. Satır 320-335 arası `review_summary` hesabı yapılıyor. `changes = _summarize_week_changes(...)` satır ~481'de çağrılıyor (tam yerini read ile kontrol et). `from app.services.gemini_service import gemini_service` import eklenecek.
- `generate_weekly_model_portfolio()` async olduğundan `await _generate_gemini_rationale(...)` doğrudan kullanılabilir.
- `FALLBACK_MESSAGE` Gemini'de "Analiz şu an kullanılamıyor..." — eğer bu döndüyse mevcut deterministik özetle devam et.

### Frontend
- `frontend/src/app/model-portfolio/page.tsx` satır 28-145: `AiPortfolioSection` komponenti. `data` state'i `ModelPortfolioCurrentResponse` tipinde. Satır 102-140 arası stats section — buradan sonra karşılaştırma kartı eklenir.
- `frontend/src/lib/api.ts` satır ~477-492: `ModelPortfolioHistoryResponse` ve `ModelPortfolioWeekSummary` interface'leri. Satır 776: `getModelPortfolioHistory` metodu.
- Model portfolio sayfası 184 satır — küçük ve yönetilebilir.

### Mevcut `review_summary` alanı
`ModelPortfolioWeek.review_summary: Optional[str]` — DB'de var. `generate_weekly_model_portfolio()` bu field'ı `_build_review_summary()` ile doldurur. Gemini çıktısı bu field'a yazılacak (replace, not append).

</code_context>

<specifics>
## Implementation Notes

- `generate_weekly_model_portfolio()` içinde Gemini çağrısı: try/except ile wrapped; exception → deterministic fallback.
- `FALLBACK_MESSAGE` kontrolü: `if "kullanılamıyor" in gemini_text.lower(): gemini_text = deterministic_summary`.
- Frontend `ModelPortfolioHistory` komponenti: `loading=true` başlangıç, `getModelPortfolioHistory(8)` çağrısı, hafta listesi. Her satırda tarih aralığı, portföy getirisi (renkli), change_summary (italic). Veri yoksa "Henüz geçmiş portföy kaydı yok." mesajı.
- Backend test: `backend/tests/test_model_portfolio_gemini.py` — `generate_weekly_model_portfolio()` mock Gemini ile çağrılır, `week.review_summary`'nin Gemini çıktısını içerdiği doğrulanır. Alternatif: `_generate_gemini_rationale()` doğrudan test edilir.

</specifics>

<deferred>
## Deferred

- Per-holding Gemini rationale (`_holding_rationale()` → Gemini) — batch çağrı gerektirir (15 hisse × Gemini = rate limit sorunu); v2'ye bırakıldı
- Model portföy geçmişindeki her hafta için detaylı görünüm (holdings listesi) — v2'ye bırakıldı
- Portfolio vs model portfolio zaman serisi karşılaştırma grafiği — veri eşleştirmesi karmaşık, v2'ye bırakıldı

</deferred>
