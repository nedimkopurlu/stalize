---
phase: 10-temizlik-skor
verified: 2026-04-20T00:00:00Z
status: gaps_found
score: 9/12 must-haves verified
gaps:
  - truth: "Backend python -c 'from app.main import app' hatasiz basliyor"
    status: failed
    reason: "sentiment.py, kap_parser.py, tcmb_adapter.py, tuik_adapter.py dosyalari top-level olarak silinen llm_sentiment modulunu import ediyor — ModuleNotFoundError firlatir"
    artifacts:
      - path: "backend/app/services/sentiment.py"
        issue: "Line 11: 'from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict' — top-level import, modul silindi"
      - path: "backend/app/services/kap_parser.py"
        issue: "Line 23: 'from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict' — top-level import, modul silindi"
      - path: "backend/app/services/tcmb_adapter.py"
        issue: "Line 25: 'from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict' — top-level import, modul silindi"
      - path: "backend/app/services/tuik_adapter.py"
        issue: "Line 28: 'from app.services.llm_sentiment import llm_sentiment_service, _to_legacy_dict' — top-level import, modul silindi"
    missing:
      - "llm_sentiment import satirlari sentiment.py, kap_parser.py, tcmb_adapter.py, tuik_adapter.py dosyalarindan kaldirilmali"
      - "Bu dosyalardaki llm_sentiment_service.analyze() cagrilari kaldirılmali veya kural tabanli yedek ile degistirilmeli"
  - truth: "GET /api/briefing/* ve /api/causal/* endpoint'leri 404 donuyor — router kaydi main.py'de yok"
    status: partial
    reason: "main.py'den causal ve briefing router kayitlari kaldirildi (VERIFIED). Ancak intelligence.py icinde iki endpoint event_fusion modulunu lazy import ediyor; cagirildiginda runtime ModuleNotFoundError firlatir"
    artifacts:
      - path: "backend/app/api/intelligence.py"
        issue: "Line 33 ve 59: 'from app.services.event_fusion import event_fusion' — lazy import, modul silindi; /intelligence/fusion ve /intelligence/impact-ranking endpointleri cagrildiginda patlar"
    missing:
      - "intelligence.py'deki /intelligence/fusion ve /intelligence/impact-ranking endpoint'leri ya kaldirilmali ya da event_fusion olmadan yeniden yazilmali"
  - truth: "pip install -r requirements.txt sonrasi xgboost, instructor paketleri yuklu degil (CLEN-04)"
    status: partial
    reason: "xgboost ve instructor basariyla kaldirildi. Ancak 'diskcache==5.6.3' hala requirements.txt'te mevcut. Plan 10-03 bunu kaldirmasi gerekiyordu ama data_collector.py hala aktif olarak kullandigini kontrol etti; kaldirilmamasi dogru karar olabilir. Ancak Plan 10-03 bunu kaldirilacak paket olarak listelemeliydi."
    artifacts:
      - path: "backend/requirements.txt"
        issue: "diskcache==5.6.3 mevcut — Plan 10-03 bunu silmek veya korumak icin acikca karar vermeli; data_collector.py hala kullaniyor (doğru sekilde tutuldu)"
    missing: []
---

# Phase 10: Temizlik & Skor Yeniden Yapilandirma — Dogrulama Raporu

**Phase Hedefi:** AI/LLM kaldır, scoring ağırlıklarını orta vadeye göre yeniden yaz, bağımlılıkları temizle
**Dogrulama Tarihi:** 2026-04-20
**Durum:** gaps_found
**Re-verification:** No — initial verification

---

## Hedef Basarisi

### Gozlemlenebilir Dogrular

| # | Dogru | Durum | Kanit |
|---|-------|-------|-------|
| 1 | llm_sentiment.py, briefing_generator.py, knowledge_graph.py, causal.py, event_fusion.py silinmis | VERIFIED | Filesystem kontrolu: hicbiri mevcut degil |
| 2 | ml.py, performance_monitor.py, portfolio_optimizer.py silinmis | VERIFIED | Filesystem kontrolu: hicbiri mevcut degil |
| 3 | api/portfolio.py silinmis, api/briefing.py silinmis, api/causal.py silinmis | VERIFIED | Filesystem kontrolu: hicbiri mevcut degil |
| 4 | main.py yalnizca stocks, macro, intelligence, admin router'larini kayit ediyor | VERIFIED | main.py Line 14: `from app.api import stocks, macro, intelligence, admin`; portfolio/briefing/causal referansi yok |
| 5 | Backend hatasiz basliyor | FAILED | sentiment.py, kap_parser.py, tcmb_adapter.py, tuik_adapter.py top-level olarak silinen llm_sentiment'i import ediyor — ModuleNotFoundError |
| 6 | /intelligence/fusion ve /intelligence/impact-ranking endpointleri cagrildiginda calisiyor | FAILED | intelligence.py lazy import ile event_fusion kullanıyor (silindi) — runtime hatasi firlatir |
| 7 | config.py: WEIGHT_FUNDAMENTAL=0.45, WEIGHT_TECHNICAL=0.40, WEIGHT_NEWS=0.15 | VERIFIED | config.py Lines 38-40: degerler dogru; WEIGHT_ML/CAUSAL/MACRO yok |
| 8 | scoring.py sadece uc agirlik kullaniyor, ml_score/causal_score yoksayiliyor | VERIFIED | scoring.py tamamen yeniden yazilmis; sadece fundamental/technical/sentiment_score referanslari var |
| 9 | scoring.py -> config.py key link calisiyor | VERIFIED | settings.WEIGHT_FUNDAMENTAL, settings.WEIGHT_TECHNICAL, settings.WEIGHT_NEWS kullaniyor |
| 10 | scoring.py -> stock model key link calisiyor | VERIFIED | stock.fundamental_score, stock.technical_score, stock.sentiment_score kullaniyor |
| 11 | requirements.txt: xgboost ve instructor kaldirildi | VERIFIED | grep kontrolu: hicbiri mevcut degil |
| 12 | diskcache kaldirilmasi veya korunmasi karari | PARTIAL | diskcache==5.6.3 mevcut; data_collector.py aktif kullaniyor (dogru sekilde tutuldu); Plan 10-03 acik karar vermemisti |

**Puan:** 9/12 dogru dogrulandi

---

## Gereken Artifact'lar

| Artifact | Beklenen | Durum | Detay |
|----------|---------|-------|-------|
| `backend/app/services/llm_sentiment.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/briefing_generator.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/knowledge_graph.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/causal.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/event_fusion.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/ml.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/api/portfolio.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/api/briefing.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/api/causal.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/performance_monitor.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/portfolio_optimizer.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/models/model_daily_briefing.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/services/portfolio.py` | DELETED | VERIFIED | Mevcut degil |
| `backend/app/main.py` | Temizlenmis main | VERIFIED | Yalnizca stocks/macro/intelligence/admin; briefing/causal/portfolio/ml referansi yok |
| `backend/app/core/config.py` | WEIGHT_FUNDAMENTAL=0.45, WEIGHT_TECHNICAL=0.40, WEIGHT_NEWS=0.15 | VERIFIED | Lines 38-40 degerleri dogru; eski ML sabitleri yok |
| `backend/app/services/scoring.py` | Yeniden yazilmis, sadece uc agirlik | VERIFIED | Tam yeniden yazim; ml_score/causal_score referansi yok |
| `backend/requirements.txt` | xgboost, instructor, shap kaldirildi | VERIFIED | Hicbiri mevcut degil; diskcache tutuldu (data_collector kulaniyor) |
| `backend/app/services/sentiment.py` | LLM referanslari kaldirilmis olmali | FAILED | Line 11 top-level import; llm_sentiment silinmis — import hatasiyla patlar |
| `backend/app/services/kap_parser.py` | LLM referanslari kaldirilmis olmali | FAILED | Line 23 top-level import; llm_sentiment silinmis — import hatasiyla patlar |
| `backend/app/services/tcmb_adapter.py` | LLM referanslari kaldirilmis olmali | FAILED | Line 25 top-level import; llm_sentiment silinmis — import hatasiyla patlar |
| `backend/app/services/tuik_adapter.py` | LLM referanslari kaldirilmis olmali | FAILED | Line 28 top-level import; llm_sentiment silinmis — import hatasiyla patlar |
| `backend/app/api/intelligence.py` | event_fusion referanslari kaldirilmis olmali | FAILED | Lines 33, 59 lazy import; event_fusion silinmis — endpoint cagirildiginda patlar |

---

## Key Link Dogrulama

| From | To | Via | Durum | Detay |
|------|----|-----|-------|-------|
| scoring.py | config.py | settings.WEIGHT_FUNDAMENTAL/TECHNICAL/NEWS | VERIFIED | Lines 29-31 uc agirligi da kullaniyor |
| scoring.py | stock.py | stock.fundamental/technical/sentiment_score | VERIFIED | Lines 43-45 uc sutunu da kullaniyor |
| main.py | app.api.briefing/causal | include_router | VERIFIED (DELETED) | Hic reference yok |
| main.py | app.api.portfolio | include_router | VERIFIED (DELETED) | Hic reference yok |
| main.py | app.services.ml | ml_engine preload | VERIFIED (DELETED) | Hic reference yok |
| sentiment.py | llm_sentiment.py | top-level import | BROKEN | Modul silindi, import top-level |
| kap_parser.py | llm_sentiment.py | top-level import | BROKEN | Modul silindi, import top-level |
| tcmb_adapter.py | llm_sentiment.py | top-level import | BROKEN | Modul silindi, import top-level |
| tuik_adapter.py | llm_sentiment.py | top-level import | BROKEN | Modul silindi, import top-level |
| intelligence.py | event_fusion.py | lazy import in endpoint | BROKEN | Modul silindi; /intelligence/fusion ve /intelligence/impact-ranking patlar |

---

## Requirements Kapsami

| Requirement | Kaynak Plan | Tanim | Durum | Kanit |
|-------------|------------|-------|-------|-------|
| AIRF-01 | 10-01 | DeepSeek LLM entegrasyonu tamamen kaldirilir | PARTIAL | llm_sentiment.py silindi, briefing silindi, main.py temiz; AMA sentiment.py/kap_parser.py/tcmb_adapter.py/tuik_adapter.py hala llm_sentiment import ediyor — backend calismaz |
| AIRF-02 | 10-01 | Causal knowledge graph tamamen kaldirilir | PARTIAL | knowledge_graph.py, causal.py, event_fusion.py, api/causal.py silindi; AMA intelligence.py /fusion ve /impact-ranking endpoint'leri event_fusion lazy import ediyor — cagirildiginda patlar |
| AIRF-03 | 10-02 | XGBoost ML tahmin motoru kaldirilir | VERIFIED | ml.py silindi; test dosyalari silindi; requirements.txt'te xgboost/shap yok; scoring.py ml_score kullaniyor |
| AIRF-04 | 10-02 | Mock/sahte portföy backend kaldirilir | VERIFIED | api/portfolio.py, services/portfolio.py, performance_monitor.py, portfolio_optimizer.py silindi; main.py'de router kaydi yok |
| MIDT-02 | 10-03 | Scoring agirliklar orta vadeye gore yeniden yapilandirilir | VERIFIED | WEIGHT_FUNDAMENTAL=0.45, WEIGHT_TECHNICAL=0.40, WEIGHT_NEWS=0.15; scoring.py tamamen yeniden yazilmis |
| CLEN-04 | 10-03 | requirements.txt ML/LLM bagimliliklari kaldirilir | VERIFIED | xgboost, instructor, shap kaldirildi; diskcache tutuldu (data_collector aktif kullaniyor) |

---

## Anti-Pattern Bulgusu

| Dosya | Satir | Pattern | Siddet | Etki |
|-------|-------|---------|--------|------|
| `backend/app/services/sentiment.py` | 11 | `from app.services.llm_sentiment import ...` (silindi) | BLOCKER | Backend'in hicbir servisi sentiment.py'yi import ettiginde cokecek |
| `backend/app/services/kap_parser.py` | 23 | `from app.services.llm_sentiment import ...` (silindi) | BLOCKER | KAP tarama scheduler job'u cokecek |
| `backend/app/services/tcmb_adapter.py` | 25 | `from app.services.llm_sentiment import ...` (silindi) | BLOCKER | TCMB tarama scheduler job'u cokecek |
| `backend/app/services/tuik_adapter.py` | 28 | `from app.services.llm_sentiment import ...` (silindi) | BLOCKER | TUIK tarama scheduler job'u cokecek |
| `backend/app/api/intelligence.py` | 33, 59 | `from app.services.event_fusion import event_fusion` (silindi) | BLOCKER | /intelligence/fusion ve /intelligence/impact-ranking endpoint'leri cagrildiginda 500 donecek |

---

## Bosluk Ozeti

Phase 10, temizlik gorevlerinin buyuk cogunlugunu tamamladi:
- 13 AI/ML/portfolio dosyasi basariyla silindi
- main.py tamamen temizlendi — hicbir eski router/scheduler/import referansi yok
- scoring.py eksiksiz yeniden yazildi, config.py agirliklar dogru
- requirements.txt xgboost/instructor/shap icermiyor

Ancak iki kritik bosluk kaliyor:

**Bosluk 1 — Kirik imports (BLOCKER):** `sentiment.py`, `kap_parser.py`, `tcmb_adapter.py`, `tuik_adapter.py` dosyalarinin hepsi top-level olarak `llm_sentiment` import ediyor. Bu modul silindi. Bu dosyalar herhangi bir backend baslangici sirasinda import edildiginde, backend `ModuleNotFoundError` ile patlar. Plan 10-01 `llm_sentiment.py`'yi sildi ama bu dosyalardaki tureve bagimliliklari temizlemeyi atladi. Her dosyadan import satiri ve `llm_sentiment_service.analyze()` cagrisi kaldirilmali; ya silinmeli ya da kural tabanli yedek ile degistirilmeli.

**Bosluk 2 — Kirik endpoint'ler (BLOCKER):** `intelligence.py`'deki iki endpoint (`/intelligence/fusion`, `/intelligence/impact-ranking`) lazy import ile silinen `event_fusion` modulunu cagiriyor. Plan 10-01 `event_fusion.py`'yi sildi ama intelligence router'inin bu module olan bagimliligini temizlemeyi atladi. Bu endpoint'ler ya kaldirilmali ya da event_fusion olmadan yeniden implement edilmeli.

Bu iki bosluk, AIRF-01 ve AIRF-02 gereksinimlerini "tam" yerine "parcali" olarak isaretliyor. Diger dort gereksinim (AIRF-03, AIRF-04, MIDT-02, CLEN-04) tamamen karsilaniyor.

---

_Dogrulayan: Claude (gsd-verifier)_
_Tarih: 2026-04-20_
