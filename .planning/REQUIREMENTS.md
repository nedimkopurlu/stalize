# Requirements: Stalize — BIST 100 Kişisel Yatırım Analiz Platformu

**Defined:** 2026-04-16
**Updated:** 2026-04-20 — v1.2 milestone started, AI/LLM kaldırıldı, model portföy + glassmorphism eklendi
**Core Value:** BIST 100'deki 1-2 aylık orta vadeli fırsatları, gerçek temel ve teknik verilerle tespit et — model portföyde tut, günlük performansını takip et.

## v1.0 Requirements (Historical — All Complete)

### Foundation

- [x] **FOND-01**: KAP parser mock fallback kaldırılsın; feedparser yoksa startup'ta hata fırlatsın
- [x] **FOND-02**: Scoring ağırlıkları tek yerden yönetilsin — config.py değerleri scoring.py BASE_WEIGHTS'e aktarılsın
- [x] **FOND-03**: tensorflow, torch, transformers, sentencepiece kaldırılsın (kullanılmıyor, 3-4GB boşa)
- [x] **FOND-04**: endpoints.py domain router'lara bölünsün (stocks, macro, briefing, portfolio vb. ayrı dosyalar)
- [x] **FOND-05**: UTC/naive datetime karışıklığı giderilsin — tüm DB kayıtları UTC timezone-aware

### ML & Caching

- [x] **MLCA-01**: XGBoost modelleri disk'e kaydedilsin (.ubj formatı); startup'ta yüklensin; haftalık APScheduler job ile retrain
- [x] **MLCA-02**: yfinance HTTP katmanı requests-cache ile cache'lensin (fiyat 5dk TTL, temel veri 24s TTL)
- [x] **MLCA-03**: LLM analiz sonuçları diskcache ile cache'lensin (30dk TTL, hisse bazında key)

### LLM Altyapı

- [x] **LLMI-01**: instructor kütüphanesi entegre edilsin; StockAnalysis Pydantic modeli tanımlansin
- [x] **LLMI-02**: DeepSeek çağrıları asyncio.Semaphore(5) + günlük token cap ile rate limit'e bağlansın
- [x] **LLMI-03**: LLM prompt assembly'de as_of timestamp zorunlu olsun; bayat veri (>15dk) işaretlensin

### AI Brifing

- [x] **BREF-01**: APScheduler cron (hafta içi 06:30) ile günlük brifing otomatik üretilsin
- [x] **BREF-02**: DailyBriefing ORM modeli eklensin — günde 1 satır, upsert-safe
- [x] **BREF-03**: Brifing içeriği: gece gelen KAP bildirimleri + kapanış fiyat hareketleri + makro göstergeler sentezi
- [x] **BREF-04**: Dikkat çeken hisseler bölümü — hacim anomalileri, sert fiyat hareketleri, anormal sinyal kombinasyonları
- [x] **BREF-05**: Net AI yorumu — bugünkü risk ortamı, potansiyel fırsatlar, dikkat edilecekler

### UI

- [x] **UIUX-01**: Dashboard ana ekranı sabah brifing card'ı olarak yeniden tasarlansın
- [x] **UIUX-02**: Hisse detay sayfası — candlestick fiyat grafiği, 3 katman skor (temel/teknik/algı), AI gerekçesi
- [x] **UIUX-03**: Skor tablosu — tüm BIST100 hisseleri, overall_score'a göre sıralı, skor filtresi ve öneri filtresi
- [x] **UIUX-04**: Makro gösterge panosu — USD/TRY, faiz oranı, enflasyon, altın, BIST100 endeksi tek bakışta

## v1.1 Requirements (Historical — All Complete)

### Teknik Düzeltmeler (TECH)

- [x] **TECH-01**: APScheduler job'larında overlap olmadan çalışır — tüm job tanımlarına max_instances=1 ve misfire_grace_time=300 eklenmiştir
- [x] **TECH-02**: Backend yfinance verisi çekerken event loop'u bloke etmez — run_in_executor ile wrap edilmiştir
- [x] **TECH-03**: dynamic_correlation.py'deki deprecated fillna(method="ffill") pandas yeni API'ye (ffill()) güncellendi
- [x] **TECH-04**: overall_score hesabında ML ve causal skor çift sayımı kaldırıldı

### Sinyal Kalitesi (SGNL)

- [x] **SGNL-01**: Hisse detay sayfası, ATR bazlı stop-loss seviyesi ve hedef fiyatı gösterir; GET /api/stocks/{symbol}/technical endpoint'inde döner
- [x] **SGNL-02**: Hisse listesindeki hacim sütunu 20 günlük ortalama hacme göre normalize edilmiş rölatif değeri gösterir (örn. "2.4x")
- [x] **SGNL-03**: Teknik analiz motoru RSI-fiyat bullish/bearish divergence tespit eder ve top_signals listesine ekler

### v1.1 Backlog — Superseded by v1.2

- [~] **UICL-01**: ~~Nedensellik tab'ı causal engine verisini gösterir~~ — CANCELLED: causal engine v1.2'de kaldırılıyor (AIRF-02)
- [~] **UICL-02**: Hisse detay sayfasında Temel Metrik kartı — ABSORBED into CLEN-02 (glassmorphism redesign)
- [~] **UICL-03**: Hisse listesine sektör dropdown filtresi — ABSORBED into CLEN-03 (glassmorphism redesign)
- [~] **UICL-04**: /portfolio sayfası ve mock backend kaldırılır — ABSORBED into AIRF-04
- [~] **UICL-05**: Dashboard intelligence bölümü empty state — ABSORBED into CLEN-01 (KAP feed replaces AI intelligence)
- [~] **DATA-01**: Signal history tablosu — CANCELLED: XGBoost ML kaldırılıyor (AIRF-03)
- [~] **DATA-02**: ML walk-forward validation — CANCELLED: XGBoost ML kaldırılıyor (AIRF-03)
- [~] **DATA-03**: Fundamental skor sektör medyanına göre normalize — ABSORBED into MIDT-02 (scoring rebalance)

## v1.2 Requirements (v2.0 Milestone — All Complete)

### AI/LLM Kaldırma (AIRF)

- [x] **AIRF-01**: DeepSeek LLM entegrasyonu tamamen kaldırılır — llm_sentiment.py, daily_briefing scheduler, instructor kütüphanesi; DEEPSEEK_API_KEY artık kullanılmaz; DailyBriefing tablosu ve /api/briefing/* endpoint'leri silinir
- [x] **AIRF-02**: Causal knowledge graph tamamen kaldırılır — knowledge_graph.py, causal.py, event_fusion.py, app/api/causal.py; /api/causal/* endpoint'leri silinir; main.py'deki router kaydı silinir
- [x] **AIRF-03**: XGBoost ML tahmin motoru kaldırılır — ml.py, tests/test_ml_*.py; overall_score hesabı temel+teknik+haber ağırlıklı pure skor olarak yeniden yapılandırılır; ML bağımlılıkları requirements.txt'ten çıkarılır
- [x] **AIRF-04**: Mock/sahte portföy backend'i tamamen kaldırılır — app/api/portfolio.py, app/services/portfolio.py, app/services/performance_monitor.py; main.py'deki router kaydı silinir

### Model Portföy (MPRT)

- [x] **MPRT-01**: Model portföy veritabanı tabloları oluşturulur — portfolio_positions (symbol, entry_price, quantity, entry_date, stop_loss, target_price, rationale), portfolio_daily_snapshots (date, total_value, daily_pnl_pct, positions_json), portfolio_change_log (date, action, symbol, reason)
- [x] **MPRT-02**: Her gün Türk piyasası kapanışında (18:30 İstanbul) APScheduler otomatik snapshot alır — yfinance'den günlük kapanış fiyatı çekilir, günlük kazanç/kayıp hesaplanır, snapshot kaydedilir; simülasyon yok, asla mock fiyat
- [x] **MPRT-03**: GET /api/portfolio/positions — aktif pozisyonlar, her biri için güncel fiyat, giriş fiyatı, kazanç/kayıp (%) ve stop-loss/hedef fiyat döner; GET /api/portfolio/history?days=90 — günlük snapshot geçmişi döner
- [x] **MPRT-04**: Model portföy sayfası, portföyün geçmiş günlük performansını GitHub heatmap tarzı takvim görünümünde gösterir (yeşil=kazançlı, kırmuzı=kayıplı, gri=piyasa kapalı); kümülatif getiri BIST100 endeksiyle karşılaştırmalı çizgi grafik gösterilir
- [x] **MPRT-05**: Portföy pozisyon değişikliği POST /api/portfolio/positions endpoint'i üzerinden yapılır (ekle/çıkar); değişiklik tarihi, işlem türü ve gerekçe portfolio_change_log'a kaydedilir; sistem otomatik pozisyon değiştirmez

### Glassmorphism UI Yeniden Tasarım (GLUI)

- [x] **GLUI-01**: Tüm uygulama glassmorphism tema sistemine geçer — globals.css'te CSS değişkenleri: --bg-primary: #0a0f1e, --bg-secondary: #131929, --glass-bg: rgba(255,255,255,0.05), --glass-border: rgba(255,255,255,0.10), --glass-blur: blur(16px); Inter/Geist font; koyu mod zorunlu
- [x] **GLUI-02**: Dashboard yeniden tasarlanır — AI brifing bölümü tamamen kaldırılır; makro göstergeler üstte yatay bant, son KAP bildirimleri sağ sütun (tıklanabilir, KAP'a link), hisse skor tablosu ana alan; glassmorphism card'lar
- [x] **GLUI-03**: Hisse listesi sayfası yeniden tasarlanır — sektör filtresi dropdown, skor/öneri filtresi, kolon: hisse adı / skor / öneri / değişim% / hacim-ratio / stop-loss / hedef; glassmorphism tablo satırları
- [x] **GLUI-04**: Hisse detay sayfası yeniden tasarlanır — Nedensellik tab'ı kaldırılır; tam ekran candlestick grafik (EMA50/200 overlay, hacim alt panel), Temel Metrik kartları (F/K, PD/DD, ROE, net marj, borç/özsermaye), Teknik Sinyaller ve Son KAP Bildirimleri bölümleri
- [x] **GLUI-05**: Model portföy sayfası inşa edilir — aktif pozisyonlar kartları (hisse, giriş fiyatı, güncel fiyat, kazanç/kayıp%), performans takvimi (heatmap), BIST100 karşılaştırma grafiği; tüm bölümler glassmorphism

### Gelişmiş Görselleştirme (VIZZ)

- [x] **VIZZ-01**: Hisse detay candlestick grafiğine EMA 50 (turuncu çizgi) ve EMA 200 (mavi çizgi) overlay olarak eklenir; alt panelde hacim bar grafiği (ortalamanın üzerindeki hacimler vurgulanır) ve RSI çizgisi (70/30 referans çizgileriyle) gösterilir
- [x] **VIZZ-02**: Model portföy sayfasında kümülatif getiri çizgi grafiği (portföy vs BIST100) lightweight-charts ile gerçek günlük snapshot verilerinden üretilir; tarih aralığı seçilebilir (1H/3H/6H/YTD)
- [x] **VIZZ-03**: Dashboard'da mini chart widget'ları — BIST100 endeks sparkline (son 30 gün) ve USD/TRY sparkline; veri yfinance'den çekilir, statik görsel değil

### Orta Vadeli Analiz (MIDT)

- [x] **MIDT-01**: Teknik skor hesabına EMA 50/200 trend bileşeni eklenir — fiyat EMA200 üzerindeyse +20p, EMA50>EMA200 ise ek +15p; EMA uzaklığı (momentum) 0-15p arası dinamik; sadece günlük noise değil 1-2 aylık trend yansıtılır
- [x] **MIDT-02**: Scoring ağırlıkları orta vadeye göre yeniden yapılandırılır — Temel Analiz %45, Teknik Analiz %40, Haber Etkisi %15; ML (%25) ve Causal (%15) ağırlıkları kaldırılır; config.py güncellenir, scoring.py yeniden yazılır
- [x] **MIDT-03**: Hisse detay sayfası ve dashboard KAP haber listesi — her hisse için son 5 KAP bildirimi başlık + tarih + kategori olarak listelenir; veriler news_items tablosundan çekilir; KAP'a dışarı link içerir

### Temizlik & Backlog (CLEN)

- [x] **CLEN-01**: Dashboard AI intelligence bölümü kaldırılır; yerine gerçek KAP bildirimleri listesi (son 10 bildirim, hisse adı + başlık + tarih, tıklanabilir KAP linki) eklenir; boş geldiğinde "Henüz bildirim yok" empty state gösterilir
- [x] **CLEN-02**: Hisse detay sayfasında Temel Metrik glassmorphism kartı oluşturulur — F/K, PD/DD, ROE, net marj, borç/özsermaye; veriler stocks tablosundaki mevcut DB alanlarından (pe_ratio, pb_ratio, roe, net_margin, debt_equity) çekilir
- [x] **CLEN-03**: Hisse listesi sayfasına sektör filtresi eklenir — sector değerleri DB'den dinamik olarak çekilir (GET /api/stocks/sectors), frontend'de anlık filtreleme yapılır; "Tümü" varsayılan seçenek
- [x] **CLEN-04**: requirements.txt ve pyproject.toml temizliği — kaldırılan ML/LLM bağımlılıkları (xgboost, instructor, deepseek-sdk veya benzeri) silinir; test bağımlılıkları gözden geçirilir; pip install sonrası çalışan temiz requirements bırakılır

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user erişim | Kişisel araç, tek kullanıcı |
| OAuth / kayıt sistemi | Gerek yok |
| Mobil uygulama | Web-first |
| Gerçek zamanlı WebSocket | yfinance 15dk gecikmeli, WebSocket değer katmaz |
| Otomatik emir iletimi | Sadece analiz, emir yok |
| AI/LLM brifing | Kaldırıldı — pure veri analizi yeterli (AIRF-01) |
| Causal knowledge graph | Kaldırıldı — kullanılmıyor, karmaşıklık ekliyor (AIRF-02) |
| XGBoost ML tahmin | Kaldırıldı — veri yetersizliği, güvenilmez (AIRF-03) |
| Kısa vadeli trade sinyalleri | 1-2 ay+ odak, günlük noise değil |
| Yabancı haber kaynakları | Sadece Türk kaynaklar (KAP, TCMB, TÜİK) |
| Simülasyon/backtesting | Gerçek veri sadece — asla mock fiyat |
| Chat/soru-cevap arayüzü | v2 — önce sağlam veri analizi altyapısı |
| Event fusion indirect_impact | v2 — kaldırılan causal engine'in parçası |
| Signal history tracking | Cancelled — ML kaldırıldığından sinyal geçmişi anlamsız |
| Otomatik portföy rotasyonu | Sistem öneri sunar, karar kullanıcıya ait |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOND-01 | Phase 1 | Complete |
| FOND-02 | Phase 1 | Complete |
| FOND-03 | Phase 1 | Complete |
| FOND-04 | Phase 1 | Complete |
| FOND-05 | Phase 1 | Complete |
| MLCA-01 | Phase 2 | Complete |
| MLCA-02 | Phase 2 | Complete |
| MLCA-03 | Phase 2 | Complete |
| LLMI-01 | Phase 3 | Complete |
| LLMI-02 | Phase 3 | Complete |
| LLMI-03 | Phase 3 | Complete |
| BREF-01 | Phase 4 | Complete |
| BREF-02 | Phase 4 | Complete |
| BREF-03 | Phase 4 | Complete |
| BREF-04 | Phase 4 | Complete |
| BREF-05 | Phase 4 | Complete |
| UIUX-01 | Phase 5 | Complete |
| UIUX-02 | Phase 5 | Complete |
| UIUX-03 | Phase 5 | Complete |
| UIUX-04 | Phase 5 | Complete |
| TECH-01 | Phase 6 | Complete |
| TECH-02 | Phase 6 | Complete |
| TECH-03 | Phase 6 | Complete |
| TECH-04 | Phase 6 | Complete |
| SGNL-01 | Phase 7 | Complete |
| SGNL-02 | Phase 7 | Complete |
| SGNL-03 | Phase 7 | Complete |
| AIRF-01 | Phase 10 | Complete |
| AIRF-02 | Phase 10 | Complete |
| AIRF-03 | Phase 10 | Complete |
| AIRF-04 | Phase 10 | Complete |
| MPRT-01 | Phase 11 | Complete |
| MPRT-02 | Phase 11 | Complete |
| MPRT-03 | Phase 11 | Complete |
| MPRT-04 | Phase 12+15 | Complete |
| MPRT-05 | Phase 11 | Complete |
| GLUI-01 | Phase 13 | Complete |
| GLUI-02 | Phase 13 | Complete |
| GLUI-03 | Phase 13 | Complete |
| GLUI-04 | Phase 14 | Complete |
| GLUI-05 | Phase 15 | Complete |
| VIZZ-01 | Phase 14 | Complete |
| VIZZ-02 | Phase 15 | Complete |
| VIZZ-03 | Phase 13 | Complete |
| MIDT-01 | Phase 16 | Complete |
| MIDT-02 | Phase 10 | Complete |
| MIDT-03 | Phase 14 | Complete |
| CLEN-01 | Phase 13 | Complete |
| CLEN-02 | Phase 14 | Complete |
| CLEN-03 | Phase 13 | Complete |
| CLEN-04 | Phase 10 | Complete |

**Coverage:**
- v1.0 requirements: 20 total — all Complete ✓
- v1.1 requirements: 10 total — all Complete ✓ (8 superseded/absorbed into v1.2)
- v1.2 requirements: 24 total — all Complete ✓
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-27 — v2.0 milestone audit: tüm v1.2 gereksinimleri tamamlandı olarak işaretlendi (audit sonrası güncelleme)*
