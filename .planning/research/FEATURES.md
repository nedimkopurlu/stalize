# Feature Research

**Domain:** BIST-specific advanced analysis — Turkish retail investor stock assistant (v7.0)
**Researched:** 2026-05-14
**Confidence:** MEDIUM — BIST-specific standards verified via official BIST/KAP sources and academic research; NLP model performance verified on HuggingFace; some UX patterns inferred from general retail-investor research and Turkish broker practices

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users expect for a BIST analysis tool at this maturity level. These already exist in v6.0 or are obvious gaps that feel broken if absent.

| Feature | Why Expected | Complexity | Existing Hook | Notes |
|---------|--------------|------------|---------------|-------|
| Tavan/taban göstergesi | Her Türk yatırımcı bu terimleri bilir; bir hisse tavan/tabanda ise alım/satım yapılamayabilir — karar değişir | LOW | `technical.py` — price_history mevcut; önceki kapanış verisi var | BIST standart limit: önceki kapanış ±%10 (Yıldız ve Ana Pazar). Yeni halka arzlarda tavan serisi yaygın — düşük halka açıklık oranı tetikler. Gösterim: "TAVAN" kırmızı badge + kalan uzaklık yüzdesi |
| KAP duyuru türü etiketleri | Kullanıcı "bu duyuru önemli mi?" sorusunu sorar — ham KAP başlığından anlayamaz | MEDIUM | `kap_parser.py` — RSS akışı mevcut, entity linking var | 5 kritik kategori: Finansal Sonuçlar, Temettü/Sermaye, Özel Durum/M&A, Yönetim Değişikliği, Düzenleyici/Hukuki. İlk ikisi en yüksek fiyat etkisi. Kural tabanlı regex yeterli — KAP başlıkları standart formatlı |
| Portföy beta göstergesi | "Piyasa %10 düşerse portföyüm ne kadar düşer?" — temel risk sorusu | LOW | `portfolio_snapshot.py` — pozisyonlar var; `dynamic_correlation.py` — korelasyon hesaplanıyor | β_portföy = Σ(ağırlık_i × β_i). yfinance beta field kullanılır; eksikse 252 günlük regresyon (XU100.IS baz). Sözel etiket: Defansif/Piyasa Dengeli/Agresif |
| Likidite uyarısı | Düşük hacimli hissede tavan serisi, manipülasyon riski, çıkış güçlüğü yaygın — BIST'e özgü risk | MEDIUM | `scoring.py` — scoring katmanına eklenecek | Metrikler: 20 günlük ortalama hacim, hacim tutarlılığı (StdDev/Mean), spread proxy (yüksek-düşük/kapanış). "İnce Piyasa" uyarısı — skor bileşeni olarak da dahil edilebilir |

### Differentiators (Competitive Advantage)

Features that set this product apart from Fintables, StocKeys, and generic AI tools. These are BIST-specific and not available in any existing tool.

| Feature | Value Proposition | Complexity | Existing Hook | Notes |
|---------|-------------------|------------|---------------|-------|
| Market Regime Engine | Sinyal bağlamı olmadan yanıltıcı. Boğa rejiminde AL sinyali güvenilir; ayı rejiminde aynı sinyal tuzak. Hiçbir Türk perakende aracında yok | MEDIUM | `technical.py` — ADX, EMA200, ATR zaten hesaplanıyor | 4 rejim: Boğa (EMA200 üstü + ADX>25 + pozitif momentum), Ayı (EMA200 altı + ADX>25 + negatif momentum), Yatay (ADX<20), Volatil (ATR/fiyat>%3). XU100.IS endeksine uygulanır. Badge her analiz sayfasında görünür |
| Türkçe NLP sentiment (BERTurk) | VADER İngilizce tabanlı — Türkçe haberlerde yanlış polarite üretir. BERTurk F1: .86 (genel), finansal alana yakın bağlam için doğru model seçimi kritik | HIGH | `sentiment.py` — VADER mevcut; `external_news_rss.py` ve `kap_parser.py` — Türkçe metin var; Transformers zaten requirements.txt'de | `savasy/bert-base-turkish-sentiment-cased` film+ürün yorumu+tweet üzerinde eğitildi — finansal fine-tune yok. Pragmatik: önce KAP keyword sınıflandırması, sonra BERTurk inference sadece KAP duyuruları için. Lazy loading şart (~440MB model) |
| Sektör-spesifik scoring | Banka için genel F/K anlamsız. GYO için net kar değil NAV iskonto kritik. Holding için iştiraklerin toplamı esas | HIGH | `scoring.py` — uniform scoring; `fundamental.py` — sektör yok | 3 adapter: Banka (NIM, NPL, F/DD, sermaye yeterlilik), GYO (NAD iskonto, kira getirisi — yfinance'de yok, quarterly KAP raporu gerekir), Holding (iştirak market cap toplamı vs piyasa değeri). Veri erişilebilirliği önce doğrulanmalı |
| KAP duyuru öncelik sınıflandırması | KAP günde 200+ duyuru — hangisi önemli belirsiz. Renk kodlu öncelik sistemi hiçbir rakipte yok | MEDIUM | `kap_parser.py` — başlık parsing ve impact_score altyapısı var | Kategori + renk (kırmızı/turuncu/gri). Kural tabanlı regex %80+ doğruluk sağlar — KAP başlıkları standart. BERTurk ile desteklenebilir ama gerekli değil |
| Pozisyon büyüklüğü rehberi | "Ne kadar almalıyım?" — çoğu uygulamada hiç yok. Disiplinli risk yönetimi öğretir | MEDIUM | ATR mevcut (`technical.py`); portföy değeri mevcut; v6.0 stop-loss alanı mevcut | Volatilite-ayarlı %1-2 risk kuralı: Pozisyon = (Portföy × Risk%) / (ATR × 2). 3 senaryo: muhafazakar/dengeli/agresif. Full Kelly değil — win-rate tahmini belirsizliği ile retail için aşırı agresif |
| Ön-işlem checklist | İşlem disiplinini pekiştiriyor. v6.0 exit/invalidation altyapısının doğal önceki adımı | LOW* | v6.0 exit_reason ve invalidation_condition zaten var; tüm diğer v7.0 özellikleri bağımlılık | 7 madde: trend, rejim, KAP duyurusu, stop-loss, pozisyon boyutu, sektör yoğunluğu, likidite. Son faza bırakılmalı — tüm alt sistemler gerektirir |

*Checklist UI basit ama tüm v7.0 bağımlılıklarını bekler

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full Kelly criterion otomasyonu | Matematiksel olarak "optimal" görünüyor | Win-rate tahmini %5 hata bile sonucu dramatik değiştirir; full Kelly ile %50+ drawdown olası; retail için psikolojik dayanılmaz | Volatilite-ayarlı %1-2 risk kuralı — daha sağlam, daha anlaşılır, retail'e uygun |
| BERTurk inference her RSS haberi için | Kapsamlı sentiment coverage görünüyor | Transformers CPU inference ~100ms/metin × 200+ günlük haber = 20+ saniye batch; startup maliyeti yüksek | Sadece şirkete linked KAP duyuruları; genel haber makro seviyede keyword-based kalır |
| GYO NAD tam otomasyonu | "Otomatik hesapla" mantıklı | GYO NAD verisi yfinance'de yok; SPK/KAP'tan quarterly rapor scraping ayrı bağımlılık; v7.0 kapsamı dışında | Uniform scoring + "GYO: NAD verisi manuel girilmeli" uyarısı — v7.0'da geçici çözüm |
| Holding tam NAD otomasyonu | Logik bir beklenti | İştirak oranı yıllık rapordan çekilmeli — yfinance'de yok; halka kapalı iştiraklerin değeri tahmin gerektirir | Sadece halka açık iştiraklerin market cap toplamı; holding iskonto kabaca hesaplanır |
| Gerçek zamanlı fiyat akışı | Kullanıcı "anlık fiyat" ister | yfinance BIST için 15 dk gecikme; gerçek zamanlı lisans maliyetli; kişisel araç için gereksiz | Veri tazeliği badge (mevcut v6.0) + "15 dk gecikmeli" notu açık gösterilir |
| Sektör karşılaştırma endeksi oluşturma | "Sektör ortalaması nedir?" sorusu makul | BIST sektör alt endeksleri veri çekimi ayrı bağımlılık; yfinance güvenilirliği düşük | Mevcut BIST100 hisseleri üzerinden peer median hesapla — yeterince yakın |

---

## Feature Dependencies

```
[Tavan/Taban Tespiti]
    └──gerektirir──> [PriceHistory.close önceki gün] (MEVCUT)
    └──besler──> [Ön-işlem Checklist] (alım/satım yapılabilir mi maddesi)
    └──besler──> [Likidite Uyarısı] (tavan serisi + ince piyasa ilişkisi)

[KAP Duyuru Sınıflandırması]
    └──gerektirir──> [kap_parser.py RSS çekimi] (MEVCUT)
    └──güçlendirir──> [Türkçe NLP Sentiment] (sınıflandırma sonucu polariteyi yönlendirir)
    └──besler──> [Ön-işlem Checklist] (olumsuz duyuru filtresi)

[Türkçe NLP Sentiment]
    └──gerektirir──> [Türkçe haber metni] (MEVCUT — external_news_rss.py, kap_parser.py)
    └──gerektirir──> [savasy/bert-base-turkish-sentiment-cased model yükleme]
    └──günceller──> [sentiment_score] → ScoringEngine ağırlıklı hesap

[Market Regime Engine]
    └──gerektirir──> [ADX, EMA200, ATR] (MEVCUT — technical.py)
    └──gerektirir──> [XU100.IS fiyat geçmişi] (yfinance — erişilebilir)
    └──besler──> [Ön-işlem Checklist] (rejim kontrol maddesi)
    └──besler──> [Sinyal Backtest Rejim Analizi] (v7.0 backtest kalitesi)
    └──bağlamlandırır──> [ScoringEngine önerileri]

[Sektör-Spesifik Scoring]
    └──gerektirir──> [Stock.sector etiketi] (MEVCUT)
    └──gerektirir──> [NIM, NPL, sermaye yeterlilik — bankalar] (fundamental.py GENİŞLEME gerekli — veri riski)
    └──gerektirir──> [NAD verisi — GYO] (yfinance'de YOK — quarterly KAP raporu scraping)
    └──gerektirir──> [İştirak oranları — holding] (KAP yıllık rapor — kısmen manuel)
    └──günceller──> [fundamental_score]

[Portföy Beta]
    └──gerektirir──> [Hisse bazlı beta] (yfinance info['beta'] — MEDIUM confidence)
    └──gerektirir──> [Pozisyon ağırlıkları] (MEVCUT — portfolio_snapshot.py)
    └──fallback──> [252 günlük regresyon XU100.IS] (technical.py genişlemesi)

[Likidite Skoru]
    └──gerektirir──> [PriceHistory volume 20 gün] (MEVCUT)
    └──besler──> [Ön-işlem Checklist] (hacim yeterli mi maddesi)
    └──besler──> [ScoringEngine risk overlay]

[Pozisyon Büyüklüğü Rehberi]
    └──gerektirir──> [ATR] (MEVCUT — technical.py)
    └──gerektirir──> [Portföy değeri] (MEVCUT — portfolio_snapshot.py)
    └──gerektirir──> [stop-loss seviyesi] (v6.0 invalidation_condition MEVCUT)
    └──besler──> [Ön-işlem Checklist] (pozisyon boyutu hesaplama maddesi)

[Ön-işlem Checklist]
    └──gerektirir──> [Market Regime Engine] (YENI)
    └──gerektirir──> [Tavan/Taban Tespiti] (YENI)
    └──gerektirir──> [KAP Duyuru Sınıflandırması] (YENI)
    └──gerektirir──> [Likidite Skoru] (YENI)
    └──gerektirir──> [Pozisyon Büyüklüğü Rehberi] (YENI)
    └──gerektirir──> [Sektör Konsantrasyon Uyarısı] (MEVCUT — v6.0)
    └──gerektirir──> [Stop-loss alanı] (MEVCUT — v6.0)
```

### Dependency Notes

- **Sektör-spesifik scoring veri riski taşıyor:** Banka için NIM/NPL yfinance'de tutarsız. GYO NAD scraping ayrı iş. Holding iştirak oranı manuel. Bu özelliğin kapsamı veri erişilebilirliğine göre daraltılabilir — banka F/DD + ROE adaptasyonu minimum uygulanabilir kapsam.
- **Türkçe NLP lazy loading zorunlu:** bert-base model ~440MB. Startup'ta değil, ilk inference isteğinde yükle. CPU-only ortamda ~100ms/metin inference — KAP duyuruları için kabul edilebilir (günlük 20-50 duyuru), genel haber için değil.
- **Market Regime tüm yorum bağlamını sağlar:** Backtest rejim analizi, ön-işlem checklist, scoring önerileri hepsi bu katmandan beslenir. En erken fazda uygulanmalı.
- **Ön-işlem checklist bağımlılık zincirinin sonundadır:** Tüm alt sistemler çalışıyorsa anlam taşır — son faza bırakılmalı.

---

## MVP Definition (v7.0 Scope)

### Faz 1: Altyapı (Hızlı Kazanımlar)

Minimum bağımlılık, yüksek değer, mevcut altyapıya doğrudan hook.

- [ ] Tavan/taban tespiti ve badge — `PriceHistory` + önceki kapanış; dış API gerektirmez
- [ ] KAP duyuru sınıflandırması — `kap_parser.py` üzerine kural tabanlı regex; Transformers gerektirmez
- [ ] Market Regime Engine — `technical.py` ADX/EMA200/ATR üzerine yeni hesaplama katmanı; XU100.IS fiyat çekimi
- [ ] Portföy beta — `portfolio_snapshot.py` + yfinance beta; görece basit; fallback regresyon

### Faz 2: Analiz Kalitesi

Daha yüksek maliyet, veri erişilebilirliği riski olan özellikler.

- [ ] Türkçe NLP sentiment — VADER'dan kademeli geçiş; önce KAP duyuruları için lazy BERTurk
- [ ] Sektör-spesifik scoring (banka minimum: F/DD, ROE adaptasyonu) — veri doğrulaması önce
- [ ] Sektör-spesifik scoring (GYO: uniform + NAD uyarısı) — tam otomasyon v8.0'a ertele
- [ ] Likidite skoru — 20 günlük hacim tutarlılık hesabı; scoring katmanına entegre

### Faz 3: Kullanıcı Arayüzü

Tüm alt sistemler hazır olduğunda anlamlı.

- [ ] Pozisyon büyüklüğü rehberi — portföy + ATR + risk yüzdesi; frontend hesaplaması; 3 senaryo
- [ ] Ön-işlem checklist — interaktif modal; 7 madde; tüm v7.0 alt sistemlerini entegre

### v8.0'a Ertele

- [ ] Holding NAD iskonto tam otomasyonu — iştirak verisi çekimi karmaşık; v7.0'da halka açık iştiraklerin hesabı ile sınırlı
- [ ] BERTurk finansal fine-tune — TurSentiFin corpus mevcut ama eğitim pipeline ayrı iş
- [ ] Sinyal backtest rejim bazlı analiz — backtest motoru yeniden yapılandırma gerektirebilir
- [ ] GYO NAD quarterly scraping — SPK/KAP PDF parse ayrı bağımlılık

---

## Feature Prioritization Matrix

| Feature | Kullanıcı Değeri | Uygulama Maliyeti | Öncelik |
|---------|-----------------|-------------------|---------|
| Tavan/taban tespiti | HIGH | LOW | P1 |
| Market Regime Engine | HIGH | MEDIUM | P1 |
| KAP duyuru sınıflandırması | HIGH | MEDIUM | P1 |
| Portföy beta | MEDIUM | LOW | P1 |
| Likidite skoru | MEDIUM | MEDIUM | P2 |
| Türkçe NLP sentiment (KAP bazlı) | HIGH | HIGH | P2 |
| Sektör-spesifik scoring — banka | MEDIUM | HIGH | P2 |
| Pozisyon büyüklüğü rehberi | HIGH | MEDIUM | P2 |
| Sektör-spesifik scoring — GYO (kısmi) | MEDIUM | HIGH | P2 |
| Ön-işlem checklist | HIGH | LOW* | P3 |
| Holding NAD iskonto (kısmi) | LOW | HIGH | P3 |
| BERTurk finansal fine-tune | MEDIUM | VERY HIGH | P3 |

*Checklist UI basit ama tüm v7.0 bağımlılıklarını bekler

---

## BIST-Specific Standards: Teknik Referans

### Tavan/Taban Sistemi (2025 itibarıyla)

**Güncel kurallar:**
- Standart fiyat limiti: Önceki kapanış ±%10 (Yıldız Pazar, Ana Pazar)
- Yakın İzleme Pazarı: Farklı marjlar uygulanabilir
- Endekse bağlı devre kesici (EBDKS): BIST100 %6 düşüşünde tüm piyasa durur (2025 güncelleme — önceki: %5+%7 iki aşamalı)
- Hisse bazlı devre kesici: Tek emirde %5 hareket → işlem 10 dakika durur (2025 güncelleme — önceden 20-30 dk)
- Yeni halka arzlar: İlk seanslarda tavan serisi yaygın; düşük halka açıklık oranı hızlandırır

**Hesaplama:** `tavan = onceki_kapanis * 1.10` / `taban = onceki_kapanis * 0.90`

**UI:** Badge rengi kırmızı/mavi, kalan yüzde mesafesi gösterilir, "emir karşılanmayabilir" uyarısı.

### KAP Duyuru Sınıflandırma Şeması

| Kategori | Türkçe Anahtar Kelimeler | Önem | Badge Rengi |
|----------|--------------------------|------|-------------|
| Finansal Sonuçlar | "finansal sonuçlar", "net kâr", "bilanço", "denetim raporu" | YÜKSEK | Kırmızı |
| Temettü / Sermaye | "kâr payı dağıtımı", "bedelsiz sermaye", "bedelli artırım", "rüçhan hakkı" | YÜKSEK | Kırmızı |
| Özel Durum / M&A | "birleşme", "devralma", "büyük sözleşme", "stratejik ortaklık" | YÜKSEK | Kırmızı |
| Yönetim Değişikliği | "genel müdür", "yönetim kurulu", "CEO", "istifa", "atama" | ORTA | Turuncu |
| Düzenleyici/Hukuki | "SPK", "BDDK", "mahkeme", "ceza", "soruşturma" | ORTA | Turuncu |
| Genel Kurul | "olağan genel kurul", "çağrı", "gündem" | DÜŞÜK | Gri |
| Diğer | (eşleşme yok) | DÜŞÜK | Gri |

Kural tabanlı regex — KAP başlıkları standart formatlı, %80+ doğruluk beklenir.

### Market Regime: 4 Rejim Tanımı

| Rejim | Koşullar (XU100.IS üzerinde) | Kullanıcı Mesajı | Sinyal Güvenilirliği |
|-------|------------------------------|------------------|---------------------|
| Boğa | Kapanış > EMA200 VE ADX > 25 VE 20g getiri > 0 | "Piyasa yükseliş trendinde" | AL sinyalleri daha güvenilir |
| Ayı | Kapanış < EMA200 VE ADX > 25 VE 20g getiri < 0 | "Piyasa düşüş trendinde" | AL sinyallerine temkinli yaklaşın |
| Yatay | ADX < 20 | "Piyasa yatay hareket ediyor" | Trend sinyalleri zayıf |
| Volatil | 20g ATR/fiyat > %3 | "Piyasa aşırı oynak" | Pozisyon boyutlarını küçültün |

Önemli not: Türkiye emerging market karakteri — kur şokları, TCMB faiz kararları, jeopolitik gelişmeler teknik rejimi override edebilir. Mevcut `macro_news.py` bu boşluğu kısmen kapatır.

### Sektör-Spesifik Scoring

**Bankalar (GARAN, AKBNK, ISCTR, VAKBN, vb.):**
- Standart F/K: Döngüsel faiz marjı etkisi nedeniyle yanıltıcı
- Kritik metrikler: F/DD (P/TBV) < 1 = cazip, ROE (yfinance'de mevcut), sermaye yeterlilik rasyosu (%8 Basel III minimum; Türk bankalar genelde %15+)
- NIM ve NPL yfinance'de tutarsız — BDDK aylık bülteninden çekilebilir (scraping) ama v7.0 kapsamı dışında
- Minimum v7.0 uygulaması: F/DD ağırlık artırımı + ROE odaklı banka adaptörü

**GYO (ISGYO, EKGYO, TOASO, vb.):**
- Kritik metrik: NAD iskonto = (Piyasa Değeri / Net Aktif Değer) - 1; negatif = cazip
- GYO'lar SPK zorunluluğuyla 6 iş günü içinde quarterly portföy tablosu BIST'e gönderir — scraping mümkün ama maliyetli
- Pragmatik v7.0: Uniform scoring + "GYO: NAD verisi otomatik çekilemiyor" uyarısı
- Tam NAD otomasyonu: v8.0

**Holdinglar (KCHOL, SAHOL, TKFEN, vb.):**
- NAD iskonto = (Holdingin Piyasa Değeri / İştirak Paylarının Toplam Market Cap) - 1
- Halka açık iştiraklerin değeri yfinance ile günlük hesaplanabilir
- İştirak oranları yıllık rapor/KAP'tan — kısmen manual, kısmen scraping
- v7.0: Sadece halka açık iştiraklerin payı hesaplanır; sonuç "yaklaşık iskonto"

### Portföy Beta: Hesaplama ve Gösterim

**Yöntem 1 (tercih):** yfinance `info['beta']` → ağırlıklı ortalama  
**Yöntem 2 (fallback):** 252 günlük günlük getiri regresyonu (hisse vs XU100.IS)  
**Gösterim:**
```
Portföy Beta: 1.34
[AGRESİF] Piyasa %10 düşerse portföyünüz yaklaşık %13.4 düşebilir.
```
Sözel etiketler: β < 0.8 = Defansif, β 0.8–1.2 = Piyasa Dengeli, β > 1.2 = Agresif  
Uyarı notu: "Beta geçmiş veriye dayanır; gelecek için garanti vermez."

### Pozisyon Büyüklüğü: Formül ve Senaryo Gösterimi

**Yöntem:** Volatilite-ayarlı sabit risk kuralı (Full Kelly değil)  
**Neden Full Kelly değil:** Win-rate tahmini %5 hatalı bile olsa sonuç dramatik değişir; full Kelly %50+ drawdown üretebilir; retail için psikolojik dayanılmaz; half-Kelly bile belirsizlikte agresif.

**Formül:**
```
Pozisyon = (Portföy Değeri × Risk%) / (ATR × 2)
Stop-loss = Giriş Fiyatı - (ATR × 2)
```

**3 senaryo gösterimi:**
| Senaryo | Risk % | Pozisyon (adet) | Toplam Değer |
|---------|--------|-----------------|-------------|
| Muhafazakar | %1 | X | Y TL |
| Dengeli | %2 | X | Y TL |
| Agresif | %3 | X | Y TL |

Sorumluluk notu: "Bu yalnızca bir rehberdir. Risk yönetimi kişisel finansal durumunuza bağlıdır."

### Ön-İşlem Checklist: 7 Madde

1. **Teknik trend** — "Hisse EMA50 üzerinde mi?" → Otomatik (technical.py)
2. **Piyasa rejimi** — "Boğa veya yatay mı?" → Otomatik (Market Regime Engine)
3. **KAP duyurusu** — "Son 48 saatte olumsuz duyuru var mı?" → Otomatik (KAP sınıflandırması)
4. **Stop-loss** — "Çıkış noktası belirlendi mi?" → Kullanıcı girer (invalidation_condition v6.0)
5. **Pozisyon büyüklüğü** — "Hesaplandı mı?" → Pozisyon rehberine link
6. **Sektör yoğunluğu** — "Bu sektör portföyün %35'ini geçiyor mu?" → Otomatik (v6.0 sektör risk modülü)
7. **Likidite** — "20g ortalama hacim yeterli mi?" → Otomatik (Likidite skoru)

**UX:** Modal veya sidebar bileşen. Her madde: tik/çarpı/uyarı ikonu. Maddeler 1-3 ve 6-7 otomatik; 4-5 kullanıcı onayı gerektirir. "İşleme Devam Et" butonu kritik maddeler temizlenince aktif.

### Türkçe NLP Sentiment: Pragmatik Geçiş Planı

**Aşama 1 (v7.0 başlangıç):** KAP duyuru sınıflandırması sonucundan keyword polarite skoru. Hız: anında. Doğruluk: kategori bazlı yüksek.

**Aşama 2 (v7.0 orta):** `savasy/bert-base-turkish-sentiment-cased` — sadece KAP duyuruları için lazy inference. Kısa metin (~50-150 karakter başlık), CPU ~100ms, günlük 20-50 duyuru = 2-5 saniye batch. Kabul edilebilir.

**Aşama 3 (v8.0+):** TurSentiFin corpus ile finansal alana fine-tune. Akademik veri kümesi mevcut — eğitim pipeline ayrı iş.

**Genel Türkçe haberler** (external_news_rss.py): BERTurk inference değil — makro seviyede keyword-based polarite yeterli. Maliyet çok yüksek.

---

## Competitor Feature Analysis

| Feature | İş Yatırım / Garanti Yatırım | Fintables | StocKeys | Bizim Yaklaşım |
|---------|------------------------------|-----------|----------|----------------|
| Tavan/taban göstergesi | Gerçek zamanlı, renk kodlu | Var (fiyat akışında) | Var | Gecikmeli ama etiketli; ±%10 mantığı kullanıcıya açıklanır |
| KAP duyuruları | Ham liste | Filtrelenmiş feed | Yok | Öncelik kategorisi + renk badge — differentiator |
| Market Regime | Analist raporunda (manuel) | Yok | Yok | 4 rejim otomatik — differentiator |
| Sektör-spesifik scoring | Analist tarafından manuel | Karne sistemi (uniform) | Uniform | Sector adapter — differentiator |
| Portföy beta | Var (platforma ait portföy) | Yok | Yok | Ağırlıklı beta + sözel yorum |
| Pozisyon rehberi | Yok | Yok | Yok | Volatilite-ayarlı 3 senaryo — differentiator |
| Ön-işlem checklist | Yok | Yok | Yok | 7 madde disiplin aracı — differentiator |
| Türkçe NLP | Manuel analiz | Yok | Yok | BERTurk hedef; şimdilik keyword-based |

---

## Sources

- [Borsa İstanbul devre kesici 2025 değişiklikleri — Bloomberg HT](https://www.bloomberght.com/borsa-istanbul-devre-kesici-sisteminde-degisiklige-gitti-3756014)
- [Tavan taban uygulama mekanizması — HangiKredi](https://www.hangikredi.com/bilgi-merkezi/borsada-tavan-taban-uygulamasi-nedir/)
- [KAP bildirim türleri kategorileri — Borsa Atlas](https://borsaatlas.com/akademi/kap-bildirim-turleri/)
- [savasy/bert-base-turkish-sentiment-cased — HuggingFace](https://huggingface.co/savasy/bert-base-turkish-sentiment-cased)
- [Turkish Sentiment Analysis Cross-Validation Study 2025 — Springer](https://link.springer.com/article/10.1007/s10579-025-09869-6)
- [BIST Banking Stock Prediction with Turkish Sentiment — ResearchGate](https://www.researchgate.net/publication/390581991_Predicting_Borsa_Istanbul_Banking_and_Finance_Stocks_Using_Turkish_Social_Media_Sentiment_with_Machine_and_Deep_Learning)
- [Market Regime Detection — LuxAlgo](https://www.luxalgo.com/blog/market-regimes-explained-build-winning-trading-strategies/)
- [BIST Trend Strategy ADX/EMA200 — TradingView](https://www.tradingview.com/script/MvU41Wwc/)
- [Volatility-Based Position Sizing — QuantifiedStrategies](https://www.quantifiedstrategies.com/volatility-based-position-sizing/)
- [Kelly Criterion retail investor risks — Deriv Experts](https://experts.deriv.com/insights/kelly-criterion-position-sizing)
- [GYO NAD iskonto değerleme — PhillipCapital TR (2024 Raporu)](https://www.phillipcapital.com.tr/Files/IndustryReport/1991b54a-1f28-4e68-abf0-78f907e6870a.pdf)
- [Portfolio Beta — Wall Street Prep](https://www.wallstreetprep.com/knowledge/portfolio-beta/)
- [Pre-Trade Checklist best practices — Earn2Trade](https://www.earn2trade.com/blog/building-robust-pre-trade-checklist-for-funded-traders/)

---
*Feature research for: BIST v7.0 — Analiz Kalitesi & Sistem Bütünlüğü*
*Researched: 2026-05-14*
