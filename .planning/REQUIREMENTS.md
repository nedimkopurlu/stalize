# Requirements: Stalize v3.1 — Audit Düzeltmeleri

**Tanımlandı:** 2026-04-28
**Core Value:** Gerçek ve denetlenebilir veriyle çalışan, tüm Borsa İstanbul'u kapsayan yatırım araştırma ve portföy takip platformu.

## v3.1 Gereksinimleri

### ASYNC — Async & Concurrency

- [ ] **ASYNC-01**: `time.sleep()` → `await asyncio.sleep()` — yfinance retry sırasında event loop donmuyor, diğer request'ler etkilenmiyor
- [ ] **ASYNC-02**: Tüm API route'ları `Depends(get_db)` kullanıyor; `AsyncSessionLocal()` doğrudan çağırılmıyor — bağlantı havuzu yönetiliyor
- [ ] **ASYNC-03**: 14 scheduler job 5dk aralıklarla staggered; hiçbiri eş zamanlı thundering herd oluşturmuyor
- [ ] **ASYNC-04**: Startup `asyncio.create_task()` hataları uygulamayı sessizce kırık başlatmıyor; hata loglanıp servis health durumunu etkiliyor

### SEC — Güvenlik

- [ ] **SEC-01**: Tüm POST/DELETE endpoint'leri API key dependency gerektiriyor; kimlik doğrulamasız mutasyon mümkün değil
- [ ] **SEC-02**: CORS `allow_origins` kısıtlı (wildcard yok); `allow_credentials` ile birlikte CSRF vektörü kapalı
- [ ] **SEC-03**: API response'ları ham `str(e)` döndürmüyor; istemciye generic hata mesajı, detay server log'a yazılıyor
- [ ] **SEC-04**: `DEBUG=False` varsayılan; SQL echo production'da kapalı; env var override mümkün

### DATA — Veri Güvenilirliği

- [ ] **DATA-01**: KAP symbol extraction `BIST_FULL_SYMBOLS` kullanıyor — BIST250+ şirket haberleri sisteme giriyor
- [ ] **DATA-02**: `datetime.now(timezone.utc)` data_collector'da zorunlu; naive datetime UTC karşılaştırmayı kırmıyor
- [ ] **DATA-03**: yfinance empty dönüş ile ağ hatası ayırt ediliyor; başarısız semboller `SourceHealthRun` tablosuna yazılıyor
- [ ] **DATA-04**: Diskcache dizin boyutu sınırlı; Railway ortamında unbounded büyüme önleniyor
- [ ] **DATA-05**: `NewsItem(source, url)` unique constraint DB seviyesinde; duplicate KAP bildirimleri sessizce çoğalmıyor

### LOGIC — İş Mantığı Doğruluğu

- [ ] **LOGIC-01**: `calculate_overall_score()` ve `get_contextual_score_breakdown()` aynı ağırlıkları kullanıyor; API aynı hisse için çelişkili öneri dönmüyor
- [ ] **LOGIC-02**: Screener `pe_ratio_min > pe_ratio_max` gibi geçersiz aralıkları HTTP 400 ile reddediyor; sessiz boş sonuç yok
- [ ] **LOGIC-03**: ATR volatilite teknik skorda bileşen olarak entegre; yüksek volatiliteli hisse düşük volatiliteli hisseyle eşit skor almıyor
- [ ] **LOGIC-04**: Portfolio P&L response, yfinance'tan fiyat alınamayan pozisyonları `partial: true` flag ile işaretliyor

### FE — Frontend Kalitesi

- [ ] **FE-01**: Tüm sayfalarda boş `catch(() => {})` kaldırıldı; hata durumunda kullanıcı hata UI'ı görüyor
- [ ] **FE-02**: `MacroPanel` unsafe type assertion düzeltildi; `asOfKey` casting güvenli
- [ ] **FE-03**: Screener sayfası ham `fetch()` yerine `api.ts` helper kullanıyor; hata durumu gösteriliyor
- [ ] **FE-04**: Portfolio formu client-side validation yapıyor (`entry_price > 0`, `quantity > 0`)
- [ ] **FE-05**: Yıkıcı aksiyonlar (pozisyon kapat, watchlist'ten çıkar) onay dialogu gösteriyor

### INFRA — Altyapı

- [ ] **INFRA-01**: Python 3.9 (EOL) → 3.12 yükseltmesi; tüm bağımlılıklar 3.12-compatible
- [ ] **INFRA-02**: `/health` endpoint DB bağlantısını test ediyor; DB düşükse healthcheck başarısız dönüyor
- [ ] **INFRA-03**: Emoji'siz, parse edilebilir structured logging; kritik job hataları log'da izlenebilir

## Kapsam Dışı

| Özellik | Neden |
|---------|-------|
| OAuth / kullanıcı sistemi | Kişisel kullanım; API key yeterli |
| Glassmorphism CSS kaldırma | Kullanıcı mevcut tasarımı onayladı |
| Watchlist backend persistence | localStorage v3.1 için yeterli |
| Otomatik BIST universe güncelleme | Statik liste yılda 1-2 güncelleme yeterli |
| Test coverage arttırma | Mevcut test suite korunuyor; yeni test eklenmeyecek |

## Traceability

| Gereksinim | Faz | Durum |
|------------|-----|-------|
| ASYNC-01 | Phase 22 | Bekliyor |
| ASYNC-02 | Phase 22 | Bekliyor |
| ASYNC-03 | Phase 22 | Bekliyor |
| ASYNC-04 | Phase 22 | Bekliyor |
| SEC-01 | Phase 23 | Bekliyor |
| SEC-02 | Phase 23 | Bekliyor |
| SEC-03 | Phase 23 | Bekliyor |
| SEC-04 | Phase 23 | Bekliyor |
| DATA-01 | Phase 24 | Bekliyor |
| DATA-02 | Phase 24 | Bekliyor |
| DATA-03 | Phase 24 | Bekliyor |
| DATA-04 | Phase 24 | Bekliyor |
| DATA-05 | Phase 24 | Bekliyor |
| LOGIC-01 | Phase 25 | Bekliyor |
| LOGIC-02 | Phase 25 | Bekliyor |
| LOGIC-03 | Phase 25 | Bekliyor |
| LOGIC-04 | Phase 25 | Bekliyor |
| FE-01 | Phase 26 | Bekliyor |
| FE-02 | Phase 26 | Bekliyor |
| FE-03 | Phase 26 | Bekliyor |
| FE-04 | Phase 26 | Bekliyor |
| FE-05 | Phase 26 | Bekliyor |
| INFRA-01 | Phase 27 | Bekliyor |
| INFRA-02 | Phase 27 | Bekliyor |
| INFRA-03 | Phase 27 | Bekliyor |

**Kapsam:**
- v3.1 gereksinimleri: 25 toplam
- Faza atanan: 25
- Atamasız: 0 ✓

---
*Gereksinimler tanımlandı: 2026-04-28*
*Son güncelleme: 2026-04-28 — v3.1 Audit Düzeltmeleri milestone başlatıldı*
