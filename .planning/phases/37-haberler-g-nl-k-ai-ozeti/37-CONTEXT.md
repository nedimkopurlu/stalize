# Phase 37: Haberler + Günlük AI Özeti - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Requirements: NEWS-01, LLM-03

**NEWS-01 durum değerlendirmesi**: `/intelligence` sayfası zaten KAP + piyasa haberlerini birleşik akış olarak tarih sıralamasıyla gösteriyor. Tüm filtreler (KAP, Piyasa, Makro, Resmi) çalışıyor. NEWS-01 backend+frontend açısından implementasyonu tamamlanmış sayılır. Bu fazda ek iş gerekmez.

**LLM-03 — Günlük AI Piyasa Özeti**: Her sabah Gemini 2.0 Flash tarafından kısa Türkçe piyasa özeti üretilir. Bu özet:
1. Dashboard (`/`) sayfasında "Piyasa Akışı" bölümünün üstünde gösterilir
2. Haberler (`/intelligence`) sayfasında feed listesinin üstünde gösterilir

Bu faz saf bir LLM entegrasyon fazıdır. Yeni sayfa, yeni DB tablo veya yeni model yok.

</domain>

<decisions>
## Implementation Decisions

### Backend: `GET /intelligence/daily-summary` endpoint

- **Router**: `backend/app/api/intelligence.py` — mevcut router'a eklenir
- **Önbellek**: In-memory dict `_summary_cache: dict` modül seviyesinde — `{"date": "2026-05-08", "summary": "...", "generated_at": ISO8601}`. Server restart'ta temizlenir; ilk istekte yeniden üretilir. DB tablo gerekmez.
- **Cache logic**: `if _summary_cache.get("date") == today → return cache; else → gemini_service.generate() → store → return`
- **Prompt**: BIST100'ün genel durumu, piyasa eğilimi hakkında kısa (3-4 cümle) Türkçe günlük özet isteği. Gerçek piyasa verisi prompt'a eklenmez (backend erişilebilir veri yoksa generik özet kabul edilir — Gemini'nin genel bilgisine dayanır)
- **APScheduler**: Her sabah 09:05'te `_summary_cache` temizlenir → bir sonraki istek yeni özet üretir. `background_daily_summary_reset()` adında fonksiyon `main.py`'e eklenir
- **Response**: `{"summary": str, "generated_at": ISO8601, "from_cache": bool}`
- **Fallback**: `gemini_service.generate()` zaten fallback döner; endpoint bunu olduğu gibi döner, 500 fırlatmaz

### Frontend: `getDailySummary()` API metodu

- `DailySummaryResponse` interface + `getDailySummary()` → `GET /intelligence/daily-summary`
- `frontend/src/lib/api.ts`'e eklenir

### Frontend: Dashboard (`/app/page.tsx`) — AI Özet Banner

- Mevcut "Piyasa Akışı" kolonu üstüne (satır ~313-324 bölgesinde) **ÖNCE** bir AI özet banner section eklenir
- Yeni section dashboard'ın en üstüne (hero chart section'ın hemen altına) eklenir — tüm satırların üstünde
- State: `const [dailySummary, setDailySummary] = useState<string | null>(null)`
- `loadData()` fonksiyonuna `api.getDailySummary()` eklenir (non-blocking, `.catch(() => null)`)
- Özet görünür olunca minimal banner olarak render olur — `aiSummaryBanner` CSS class

### Frontend: Intelligence/Haberler (`/app/intelligence/page.tsx`) — AI Özet Banner

- Feed listesinin ÜSTüne (`.feedList` öncesi) yerleştirilir
- State: `const [dailySummary, setDailySummary] = useState<string | null>(null)`
- `loadData()` içinde non-blocking: `api.getDailySummary().then(r => setDailySummary(r.summary)).catch(() => null)`
- `aiSummaryBanner` class her iki sayfada da tutarlı görünür

### CSS Stratejisi

Her sayfa kendi CSS module kullandığından, `aiSummaryBanner` CSS class'ı her iki sayfanın `.module.css` dosyasına ayrı ayrı eklenir. Tutarlı bir minimal tasarım: ince kenarlık + ikon + metin.

</decisions>

<code_context>
## Existing Code Insights

### Backend
- `backend/app/api/intelligence.py` — tek endpoint `GET /intelligence/overview` (satır 9-26). Yeni `GET /intelligence/daily-summary` endpoint buraya eklenir
- `backend/app/services/gemini_service.py` — `gemini_service.generate(prompt: str) → str` async, Phase 35'te implemente edildi
- `backend/app/main.py` — APScheduler job'ları lifespan context'te; `background_daily_summary_reset` fonksiyonu ve scheduler job'u buraya eklenir

### Frontend - Dashboard (page.tsx)
- Satır ~156-165: `loadData()` async function — BIST100, fırsat, portföy paralel fetch ediyor
- Satır ~313-324: "Piyasa Akışı" kolonu `📰 Piyasa Akışı` başlığıyla — günlük özet banner'ı bunun ÖNÜNDE, `contentGrid`'den önce eklenir (satır ~261 bölgesinde hero/BIST chart section altına)
- Satır ~327-355: Market data row (Döviz + Altın) — en sonda

### Frontend - Intelligence (page.tsx)  
- Satır ~267-328: `loadData()` — `api.getIntelligenceOverview` + `api.getKapFeed` çağırıyor
- Satır ~382-403: Feed list render bölgesi — `aiSummaryBanner` buradan önce eklenir
- Satır ~350-405: return JSX içinde; `.page` wrapper → `.pageHeader` → `.scopeRail` → content

### API.ts mevcut intelligence metodları
- `getIntelligenceOverview(limit)` satır ~500-502
- `getKapFeed(limit)` satır ~505-507

</code_context>

<specifics>
## Implementation Notes

- APScheduler job için: `scheduler.add_job(background_daily_summary_reset, "cron", hour=9, minute=5, timezone="Europe/Istanbul")` — her sabah 09:05'te cache'i sıfırla
- `background_daily_summary_reset()` sync function: `global _summary_cache; _summary_cache = {}` — basit cache invalidation
- Günlük özet prompt: `"BIST100 borsasındaki günlük piyasa koşulları hakkında yatırımcılara yönelik kısa Türkçe bir özet yaz. 3-4 cümle, anlaşılır dil, genel eğilim ve dikkat edilmesi gereken noktaları içersin."`
- Dashboard'da özet banner: hafif arka plan (var(--card-bg)), sol kenarda ince mor/accent çizgisi, ✦ ikonu + metin

</specifics>

<deferred>
## Deferred

- Günlük özet için gerçek piyasa verisi (BIST100 kapanış, fiyatlar) prompt'a ekleme — v2'ye bırakıldı; şimdilik Gemini genel bilgisine dayanıyor
- Summary refresh butonu frontend'de — kullanıcı tarafından tetikleme gereksiz (günde bir yeterli)

</deferred>
