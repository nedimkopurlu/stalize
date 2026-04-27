# Stalize BIST100 Finansal Zeka Terminali
## Kapsamli Sistem Denetimi ve Faz 9 Yol Haritasi

---

## 1. Nelere Eklenmeli?

### A. Veri ve Kaynak Derinligi

- **KAP (Kamuyu Aydinlatma Platformu) Entegrasyonu**: 1. oncelik. Sirket bildirimleri anlik parse edilmeli. Bedelli, bedelsiz, kar aciklamasi, birlesme ve benzeri kritik olaylar ML katmanina dogrudan beslenmeli.
- **TCMB EDDS Senkronizasyonu**: Faiz kararlari, enflasyon verileri, swap ve benzeri makro gostergeler dogrudan resmi kanaldan alinmali.
- **Dinamik Korelasyon Matrisi**: THYAO yukselirken PGSUS'un eslik etme olasiligi gibi matematiksel korelasyonlar model skorlamasina dahil edilmeli.

### B. AI ve Analiz Gucu

- **LLM Tabanli Duygu Analizi**: VaderSentiment yerine Turkce finansal terimleri anlayan bir LLM ile JSON ciktili sentiment ve etki analizi yapilmali.
- **Teknik Formasyon Tanima**: OBO, TOBO, Fincan-Kulp gibi formasyonlar otomatik taranip isaretlenmeli.
- **Alternatif Model Destegi**: XGBoost yanina LSTM veya Transformer tabanli zaman serisi tahmin bloklari eklenmeli.

### C. UX ve Gorsel Deneyim

- **TradingView Widget Entegrasyonu**: Hisse detay ekranlarinda profesyonel grafik araclari ve daha gelismis teknik inceleme deneyimi sunulmali.

---

## 2. Neler Cikarilmali?

- **VaderSentiment**: Turkce finans dilinin baglamini ve ironisini yeterli anlamadigi icin LLM sentiment devreye girince kaldirilacak.
- **Statik Bilgi Grafigi**: `knowledge_graph.py` icindeki elle yazilan kural setleri zamanla self-learning graph yapisina evrilecek.
- **Listenin Disina Cikan Eski Hisseler**: KOZAL, KOZAA, IPEKE ve benzeri audit disi kalan hisseler cekirdek BIST100 evreninden temizlenmis kabul edilecek.

---

## 3. Neler Optimize Edilmeli?

- **Kriz Modu (Black Swan)**: Normal kosullarda haber agirligi dusuk kalirken, deprem, buyuk iflas, savas gibi senaryolarda otomatik olarak yuksek agirlikli moda gecilmeli.
- **Veritabani Hizi (Redis)**: PostgreSQL yanina hizli cache katmani eklenerek yuksek frekansli veri akisinda terminal tepki suresi dusurulmeli.
- **Explainable AI**: "Neden AL dedi?" sorusuna gerekceli, izlenebilir ve veri baglamli yanit uretilmeli.

---

## Resmi Kaynaklar

| Kaynak | URL | Notlar |
|--------|-----|--------|
| **KAP** | https://www.kap.org.tr | Sirket bildirimleri, en kritik kaynak |
| Borsa Istanbul | https://www.borsaistanbul.com | Endeks ve resmi veriler |
| TCMB | https://www.tcmb.gov.tr | Faiz, enflasyon, swap |
| TUIK | https://www.tuik.gov.tr | Makro istatistikler |
| Hazine ve Maliye Bakanligi | https://www.hmb.gov.tr | Butce ve borc yonetimi |
| Borsa Istanbul Veri Store | https://datastore.borsaistanbul.com | Ham veri |
| MKK | https://www.mkk.com.tr | Merkezi kayit |
| Takasbank | https://www.takasbank.com.tr | Takas ve netlestirme |
| TEFAS | https://www.tefas.gov.tr | Fon verileri |

## Global Finans

Etki buyuklugune gore degerlendirilir. Turkiye veya yabanci ayrimi tek basina oncelik belirlemez.

| Kaynak | URL |
|--------|-----|
| Bloomberg | https://www.bloomberg.com |
| Reuters | https://www.reuters.com |
| Financial Times | https://www.ft.com |
| CNBC | https://www.cnbc.com |
| MarketWatch | https://www.marketwatch.com |
| Yahoo Finance | https://finance.yahoo.com |

## Canli Veri ve Grafik

| Kaynak | URL |
|--------|-----|
| Investing.com (TR) | https://tr.investing.com |
| TradingView | https://www.tradingview.com |
| Midas | https://www.getmidas.com |
| Matriks | https://www.matriksdata.com |
| Ideal Data | https://www.idealdata.com.tr |

## Turkiye Ekonomi ve Finans Haberleri

| Kaynak | URL |
|--------|-----|
| Bloomberg HT | https://www.bloomberght.com |
| Ekonomim | https://www.ekonomim.com |
| Dunya Gazetesi | https://www.dunya.com |
| CNBC-e | https://www.cnbce.com |
| Bigpara | https://bigpara.hurriyet.com.tr |
| Mynet Finans | https://finans.mynet.com |
| A Para | https://www.apara.com.tr |
| Para Analiz | https://www.paraanaliz.com |
| InvestAZ Arastirma | https://www.investaz.com.tr |

## Borsa Odakli

| Kaynak | URL |
|--------|-----|
| Foreks | https://www.foreks.com |
| Borsa Gundem | https://www.borsagundem.com.tr |
| Finans Gundem | https://www.finansingundemi.com |
| Borsanin Gundemi | https://www.borsaningundemi.com |

## Veri ve Analiz Platformlari

| Kaynak | URL |
|--------|-----|
| Fintables | https://fintables.com |
| Finnet | https://www.finnet.com.tr |

---

## Faz 9 Milestone: Yerli Bloomberg Terminali

Faz 9'un en kritik adimi:

- **KAP Anlik Bildirim Okuyucu**
- **LLM Tabanli Turkce Duygu Analizi**

Bu ikili birlikte calismadan Stalize'in BIST uzerindeki sirket-temelli etkiyi dogru okuma kapasitesi ust lige cikmaz.

### Veritabani Durumu (Nisan 2026 Auditi)

- 39 eski veya yanlis hisse cekirdek evrenden cikarildi
- 40 yeni hisse cekirdek evrene dahil edildi
- 60 hisse adi guncellendi
- Toplam 100 dogru BIST100 hissesi aktif evren olarak tanimlandi

### Haber Stratejisi

1. KAP bildirimleri
2. Buyuk kuresel kaynaklar
3. Yerel Turkiye finansal medyasi

Onceliklendirme ilkesi:

- Turkiye vs. yabanci ayrimi yok
- Siralama tamamen BIST uzerindeki tahmini etki buyuklugune gore yapilir
- Sirket odakli disclosure verisi genel medya haberinden daha yuksek guven puani alir

### Faz 9 Yol Haritasi

- `Faz 9.1` KAP canli bildirim ingest katmanini haber motoruna bagla
- `Faz 9.2` TCMB, TUIK ve HMB makro adapter'larini ekle
- `Faz 9.3` Cok kaynakli event birlestirme ve deduplikasyon katmani kur
- `Faz 9.4` KAP + haber + makro etki skoru ile unified impact rank uret
- `Faz 9.5` LLM tabanli Turkce finansal sentiment ve aciklanabilir neden uretimi
- `Faz 9.6` Dinamik korelasyon matrisi ve kriz modu

---

## Bu Milestone ile Islenen Teknik Kararlar

- KAP, cekirdek konfigurasayonda birincil disclosure kaynagi olarak tanimlandi
- Haber oncelikleme mantigi `impact_first` olarak isaretlendi
- Kaynak katalogu resmi, global, yerel ve analiz platformlari olarak merkezi hale getirildi
- BIST100 sembol ve sirket adi eslesmeleri dogrulandi
- Hisse bootstrap asamasinda canonical sirket adlari kullanilmaya baslandi

---

## Not

Bu dokuman Faz 9'un urun ve veri stratejisi referansidir. Bir sonraki dogal implementasyon adimi:

1. KAP bildirimlerini canli pipeline'a almak
2. LLM sentiment katmanini mevcut sentiment motorunun yerine koymak
3. Kaynak guven skoru ve event fusion mantigini devreye almak
