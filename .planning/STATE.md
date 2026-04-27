---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Gerçek Veri Çekirdeği
status: audit_complete
last_updated: "2026-04-27T00:00:00.000Z"
progress:
  total_phases: 16
  completed_phases: 16
  total_plans: 42
  completed_plans: 42
---

# Project State

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** Gerçek ve denetlenebilir veriyle çalışan BIST100 analiz ve portföy işletim sistemi kur.
**Current focus:** 10 fazlık çekirdek tamamlandı — bundan sonrası kalibrasyon, veri kapsamı ve yeni milestone genişlemeleri

## Current Position

Phase: 16/16 — TÜM FAZLAR TAMAMLANDI
Status: v2.0 milestone audit complete — milestone kapanış için hazır

Plan 14-02 tamamlandi:

- df["ema_200"] calculate_indicators()'a eklendi (EMA 200 hesabı)
- _build_ema_series() inner function analyze_stock() içinde; DataFrame EMA sütununu [{date, value}] listesine çevirir, NaN atlanır
- analyze_stock() dönüş dict'ine "ema_50" ve "ema_200" key'leri eklendi; yetersiz veri durumunda [] döner
- TechnicalResult interface'e ema_50? ve ema_200? optional alanları eklendi
- CandlestickEMAPanel.tsx oluşturuldu: candlestick + turuncu EMA50 + mavi EMA200 overlay + hacim histogram (ortalamanın üstü vurgulu) + mor RSI çizgisi (70/30 referans çizgileriyle)
- page.tsx'te CandlestickPanel → CandlestickEMAPanel ile değiştirildi; ema50 ve ema200 props bağlandı
- TypeScript sıfır yeni hata (causal page stale .next artifact önceden mevcuttu, kapsam dışı)

Plan 14-01 tamamlandi:

- Tab sistemi kaldırıldı: activeTab state, tab-bar, chart/technical tab switching
- Causal/Nedensellik referansı yok (zaten temiz, doğrulandı)
- Yeni dikey glassmorphism layout: chart üst → metrik kartlar orta → sinyaller+KAP alt
- glassCard, metricsRow, bottomGrid CSS class'ları stock.module.css'e eklendi
- sectionTitle uppercase label stiline güncellendi
- CandlestickPanel tab olmadan tam genişlikte render ediliyor
- Plan 03 için Temel Metrikler placeholder metricsRow[0]'da
- Plan 03 için KAP Bildirimleri stockNews boşsa placeholder, doluysa gerçek veri gösteriyor
- TypeScript derleme temiz (sıfır yeni hata)

Phase: 13 (Dashboard Hisse Listesi Glassmorphism) — COMPLETE (Plan 03/3 tamamlandı)

Plan 13-03 tamamlandi:

- GET /stocks/sectors backend endpoint eklendi (distinct sektör listesi, /stocks/{symbol} path conflict yok)
- api.getStockSectors() fonksiyonu ve StockSectorsResponse tipi api.ts'e eklendi
- StockSummary'ye stop_loss ve target_price optional alanları eklendi
- Stocks sayfasında sektör dropdown'u API'dan dinamik çekiyor
- filterSector server-side filtreleme ile api.getStocks() çağrısına taşındı
- P.Degeri, Sektor, Nedensellik sütunları tablodan kaldırıldı (CLEN-03)
- Stop-Loss ve Hedef sütunları eklendi; değer yoksa — gösteriliyor
- Tablo container .glass-card sınıfına geçirildi (GLUI-03)
- next build sıfır hata, TypeScript sıfır yeni hata

Plan 13-01 tamamlandi:

- glassmorphism CSS token sistemi GLUI-01 spec'e göre güncellendi
- --bg-primary: #0a0f1e, --bg-secondary: #131929
- --glass-bg, --glass-border, --glass-blur GLUI-01 spec değerleriyle yenilendi
- --text-primary, --text-secondary rgba değerlerine geçirildi
- --accent-green: #10b981, --accent-blue: #3b82f6 spec değerleri uygulandı
- Inter font next/font/google üzerinden layout.tsx'e eklendi
- npx next build sıfır hata ile tamamlandı

Phase 10 (Üretim Sertleştirme) — DONE
Plan (Phase 10):

- resmi kaynak kataloğu API yüzeyine açıldı
- KAP / TCMB / TÜİK aktif resmi kaynaklar olarak işaretlendi
- makro paneldeki sabit faiz/enflasyon değerleri kaldırıldı
- faiz ve enflasyon son resmi DB kayıtlarından okunur hale geldi
- MKK aylık piyasa bülteni adaptörü aktif edildi
- Takasbank duyuru adaptörü aktif edildi
- HMB butce/borclanma yayin adaptörü aktif edildi
- TEFAS fon evreni resmi karşılaştırma servisi üzerinden bağlandı
- TEFAS fon evreni kalıcı snapshot tablosuna yazılır hale geldi
- TEFAS snapshot endpoint'i stale ise kendini otomatik yenileyecek korumaya alındı
- startup catch-up akışı eksik ve bayat kaynakları uygulama açılışında otomatik tazeler hale geldi
- BIST Veri Store için ürün tipi dosya listesi ve indirme probe endpoint'leri açıldı
- HMB resmi yayınları WordPress JSON kaynağından okunup kalıcı ingest ve scheduler hattına taşındı
- resmi kaynak katalog summary'si artık 9 aktif, 0 planlanan kaynak gösteriyor
- kaynak sağlık runtime'ı son koşu geçmişi, başarı oranı ve ardışık hata bilgisi tutuyor
- admin health/catalog payload'ları kaynak güvenilirlik sinyalleriyle zenginleşti
- dashboard sağlık kartları son koşu kalitesini gösterecek şekilde rafine edildi
- Borsa İstanbul, MKK ve Takasbank için kalıcı `NewsItem` ingest hattı açıldı
- bu üç kaynak artık ingest registry üzerinden generic manual scan alabiliyor
- scheduler bu üç resmi kaynağı periyodik olarak tarayıp DB kayıt sayısını health ekranına taşıyor
- source health olayları artık `source_health_runs` ledger tablosuna da yazılıyor
- admin tarafında source health geçmişi sorgulanabilir endpoint ile açıldı
- source health dashboard'u artık açık incident, recovery ve en uzun hata serisi metrikleri üretiyor
- operatör terminali toparlanan kaynakları ve incident baskısını daha net gösteriyor
- KAP olay sınıflandırması dividend/bonus_issue/rights_issue/buyback/earnings/investment/tender/contract/credit_rating/financing/share_sale/merger/legal/restructuring seviyesine genişletildi
- KAP başlıklarından pozitif/negatif tetikleyicilerle daha gerçekçi önem ve yön skoru üretiliyor
- temettü ile finansal sonuç aynı başlıkta geçtiğinde olay önceliği artık temettü lehine doğru kuruluyor
- intelligence birleşik feed'i artık yalnızca KAP + yfinance makro değil; TCMB, TÜİK, HMB, Borsa İstanbul, MKK ve Takasbank `NewsItem` kayıtlarını da aynı akışta gösteriyor
- source priority sıralaması Türkçe karakter farklarını normalize ederek uygulanıyor; `Borsa İstanbul` gibi resmi kaynak adları artık doğru öncelik alıyor
- resmi akışta HMB başlıkları HTML entity'den arındırılıyor ve piyasa dışı sınav/personel duyuruları filtreleniyor
- direct RSS tabanlı global haber kolektörü eklendi; şu an MarketWatch `mw_marketpulse` ile Investing `stock/forex/economic indicators` akışlarını normalize ediyor
- kişisel finans, insider filing ve 72 saatten eski dış haberler feed'den filtreleniyor
- `intelligence/overview` artık canlı dış RSS akışını da KAP ve resmi kaynaklarla birlikte tek dedupe katmanında sıralıyor
- yeni arayüz yönü netleşti: dashboard merkezli, borsa dışı gürültüsüz, ana tema koyu, açık/koyu geçişli
- operasyonel health ve ingest ayrıntıları ana dashboard odağından çıkarılıp arka plan/ikincil yüzeye itilecek
- haftalık model portföy ekranı ürünün ana karar yüzeylerinden biri olarak öne alındı
- haftalık model portföy için günlük performans takibi ve haftalık değişim görünürlüğü Faz 7 kapsamına net olarak eklendi
- `model_portfolio_weeks`, `model_portfolio_holdings`, `model_portfolio_daily_snapshots` ile sistemin otomatik model portföyü ayrı veri hattına taşındı
- kişisel portföy için ayrı `/portfolio` ekranı açıldı; mevcut manuel pozisyon akışı bu yüzeye ayrıldı
- sistem artık haftalık model portföyü manuel tetikleme ile üretebiliyor ve günlük snapshot bırakabiliyor
- dashboard artık ana ekranda hem sistem model portföyünü hem de kişisel portföyü kısa özet kartlarla gösteriyor
- dashboard'taki operasyonel yoğunluk bir kademe daha azaltıldı; ikinci odak alanı portföy karar yüzeyine çevrildi
- roadmap, project ve state dosyalarına "faz içinde tasarım tutarlılığı zorunlu" ilkesi işlendi
- tasarım geliştirmesi artık ayrı bir yan iş değil; dokunulan her fazın teslim kriterine bağlandı
- ortak sade sayfa başlığı dili ve hero sonrası kompakt ekran hiyerarşisi ürün standardı olarak seçildi
- kalan fazların yeni öncelik sırası kullanıcı isteğine göre güncellendi: resmi kaynaklar, öğrenen model portföy, tek tasarım dili, çok kaynaklı haber, orta vadeli skor motoru
- dashboard-first, borsa dışı gürültüsüz bilgi mimarisi artık sadece tasarım hedefi değil, faz planlama kriteri olarak yazıldı
- model portföyün her hafta neden iyi/kötü gittiğini okuyup sonraki haftaya ders taşıması resmi ürün beklentisi olarak roadmap'e işlendi
- kişisel portföy ile sistem model portföyünün tamamen ayrı ama kıyaslanabilir iki yüzey olması ürün standardı olarak sabitlendi
- Borsa İstanbul Veri Store için kalıcı `bist_datastore_file_snapshots` tablosu eklendi
- Veri Store scheduler/manual hattı artık yalnızca health değil, kalıcı dosya metadata snapshot'ı da üretiyor
- `backfill` ve `latest snapshot` endpoint'leri açıldı; Veri Store health artık DB-backed kayıt sayısını gösteriyor
- Veri Store için runtime dosya arşivleme endpoint'i açıldı; upstream 500 durumları artık sistemi çökertmeden `download_failed` olarak görünür oluyor
- model portföy review motoru artık zayıf hisseleri sadece isim bazlı değil, teknik kırılım / temel zayıflık / negatif haber akışı / düşük kalite / derin düşüş gibi neden kodlarıyla sınıflandırıyor
- haftalık review çıktısı artık `factor_drag`, `next_week_adjustments`, `review_mode`, `sector_caps` ve `factor_penalties` üretiyor
- yeni hafta üretimi bu review planını gerçekten kullanıyor; cezalı semboller, sıkılaştırılmış sektör limitleri ve faktör cezaları seçim skoruna yansıyor
- model portföy ekranı artık gelecek hafta modu, cezalı hisseler ve sıkılaştırılan sektörleri kullanıcıya sade biçimde gösteriyor
- model portföy backend'i artık geçen haftaya göre eklenen/çıkarılan hisseleri ve ağırlık artış/azalışlarını `changes` ve `change_summary` alanlarıyla üretiyor
- model portföy ekranında haftalık değişim günlüğü açıldı; eklenen, çıkarılan ve ağırlığı değişen hisseler ayrı bloklarda gösteriliyor
- geçmiş haftalar tablosu artık her hafta için kısa bir `change_summary` taşıyor
- model portföy backend'i artık `decision_band` üretiyor; review özeti, cezalı hisseler, zayıf faktörler ve giren/çıkan hisseleri tek karar bloğunda birleştiriyor
- model portföy ekranında yeni karar bandı açıldı; kullanıcı artık bu hafta portföyün neden böyle kurulduğunu tek yerde okuyabiliyor
- dashboard ana ekranındaki model portföy kartı artık aynı karar bandını taşıyor; kullanıcı uygulamayı açar açmaz sistemin haftalık portföy mantığını görebiliyor
- Faz 7 hedefleri tamamlandı: otomatik model portföy, günlük snapshot, benchmark farkı, öğrenen review, değişim günlüğü, karar bandı ve kişisel portföy ayrımı birlikte çalışıyor
- Faz 9 hedefleri tamamlandı: dashboard, hisse radarı, hisse detay, piyasa akışı, sektörler, sıralama, model portföy ve kişisel portföy ekranları ortak başlık, panel, tablo ve yoğunluk diliyle hizalandı
- kalan büyük hero/vitrin blokları temizlendi; tema düğmesi sidebar altına taşındı ve ekranlar dashboard-first, borsa-odaklı bilgi mimarisine çekildi
- radar filtreleri ve kişisel portföy formu gibi yoğun yüzeylerde inline yapı azaltıldı; ortak bileşen ve modül stilleri daha baskın hale geldi
- Reuters, CNBC, Financial Times, Yahoo Finance, Bloomberg HT, Ekonomim ve Dunya kaynakları RSS tabanlı dış haber kolektörüne bağlandı
- haber akışı artık `thesis_horizon` ile short_term ve medium_term olarak ayrılıyor; overview buna göre horizon summary üretiyor
- KAP olay motoru tez ufku, tez ağırlığı ve tez nedeni üreten yapıya taşındı
- skor motoru `company_event`, `macro_regime` ve `risk_overlay` katmanlarını explainable breakdown içinde üretiyor
- `score-breakdown` endpoint'i artık contextual skor mantığını kullanıyor
- kaynak health yüzeyi cadence ve warn_after_hours temelli freshness policy döndürüyor
- `portfolio_snapshot` aktif pozisyon yoksa artık dürüst biçimde `idle` durumunda gösteriliyor
- source catalog summary artık watch durumlarını da attention sayımına katıyor
- `backend/scripts/smoke_test.py` eklendi; kritik frontend/backend yüzeyleri tek komutta doğrulanabiliyor
- `backend/RUNBOOK.md` eklendi; başlatma, smoke, manuel toparlama ve deployment standardı yazıldı

## Immediate Risks

- Makro veri parser'ları dürüst ve canlı ama bazı resmi uçlar hâlâ kırılgan; bu artık faz değil kalibrasyon işi
- Borsa İstanbul Veri Store dosya indirme başarımı upstream kararlılığına bağlı olmaya devam ediyor
- Model portföy review ve factor penalty mantığı gerçek hafta verisi biriktikçe yeniden kalibre edilmeli

## Next Step

Faz 13 tamamlandi. Bir sonraki hedef: kalibrasyon ve yeni milestone genişlemeleri.

**Kısa vade önceliği:**

1. Makro parser kalibrasyon ve KAP tez kuralları derinleştirme (Faz 14+)
2. Stop-Loss/Hedef fiyat alanlarını /api/stocks list payload'a ekle (isteğe bağlı)
3. Dashboard widget'larına glassmorphism uygula (13-02 tamamlandıysa)

---
