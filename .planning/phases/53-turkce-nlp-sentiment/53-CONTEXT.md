# Phase 53 — Türkçe NLP & Sentiment — Context

## Goal

VADER kaldırılır; KAP duyuruları OpenAI GPT-4o-mini ile Türkçe sentiment analizine tabi
tutulur; RSS haber akışları Türkçe kural setiyle sınıflandırılır.

## Problem Statement

`vaderSentiment` İngilizce için tasarlanmış bir kural tabanlı NLP kütüphanesidir. BIST haberleri
çoğunlukla Türkçe olduğundan VADER anlamlı sonuçlar üretemiyor. `requirements.txt` içinde hâlâ
`vaderSentiment` bağımlılığı göründüğü tespit edildi (inceleme sonucu: `macro_news.py` içinde
VADER doğrudan import edilmiyor — keyword-based `_score_headline()` zaten kullanılıyor; ancak
yine de paketi temizlemek ve Türkçe anahtar kelime setini genişletmek gerekiyor).

KAP duyuruları için mevcut `_analyze_announcement()` kural tabanlıdır ve yalnızca event type'a
göre statik skor atar. OpenAI GPT-4o-mini entegrasyonu (`gemini_service.py`) Phase 35'te yapıldı
ve batch çağrı için hazır; bu altyapıyı KAP sentiment için de kullanmak mantıklı.

## Current State

- `macro_news.py`: VADER import yok, `_score_headline()` keyword-based. `requirements.txt`'de
  `vaderSentiment` paketi YOK (önceden temizlenmiş). Türkçe ve İngilizce keyword'ler karma.
- `kap_parser.py`: `_analyze_announcement()` event_type → static score mapping kullanıyor.
  `sentiment_label` değerleri İngilizce: `"positive"`, `"negative"`, `"neutral"`.
- `gemini_service.py` (`OpenAIService`): `AsyncOpenAI` istemcisi, `gpt-4o-mini` modeli,
  `settings.OPENAI_API_KEY` — batch sentiment için kullanıma hazır.
- `NewsItem` ORM: `sentiment_label VARCHAR(20)` alanı mevcut — migration gerekmez.
- Frontend `stocks/[symbol]/page.tsx`: `sentimentLabel()` fonksiyonu `"positive"` → `"Olumlu"`,
  `"negative"` → `"Olumsuz"`, `"neutral"` → `"Nötr"` çevirisi yapıyor. CSS
  `data-sentiment="positive"` / `"negative"` değerlerine göre renklendiriyor.

## Key Decisions

**NLP-01 — KAP OpenAI Batch Sentiment:**
- `kap_parser.py` içine `analyze_kap_sentiment_batch()` async metod eklenecek.
- `KAPParser.store_announcements()` kaydedilen item'ların `sentiment_label`'ını
  `"positive"/"negative"/"neutral"` (İngilizce) olarak saklayacak — frontend'deki
  `sentimentLabel()` köprü fonksiyonu zaten Türkçe çeviriyi hallediyor.
- Batch size: 20 item. JSON array response parse. Hata durumunda kural tabanlı fallback.
- APScheduler: KAP scan'den sonra (`background_kap_scan`) çağrılacak.

**NLP-02 — RSS Türkçe Keyword Classifier:**
- `macro_news.py` içindeki İngilizce-ağırlıklı keyword listelerini Türkçe-öncelikli hale getir.
- `_score_headline()` yerine `classify_turkish_sentiment() -> "pozitif"/"negatif"/"nötr"` ekle
  (ancak bu servis DB'ye yazmıyor — sadece event dict içindeki `sentiment_score` hesaplıyor).
- `requirements.txt`'deki `vaderSentiment` yoksa da kontrol et; kesinlikle bulunmamasını doğrula.

**Frontend (Plan 53-02):**
- `data-sentiment` attribute'u `"positive"/"negative"/"neutral"` değerlerini kullanıyor.
- KAP batch analizi sonucu DB'de İngilizce label'la saklandığında frontend değişikliğe gerek yok.
- Ancak CSS'te `data-sentiment="pozitif"` gibi Türkçe değerlere karşı kural yoksa, doğrulama
  yapılacak ve gerekirse `sentimentLabel()` fonksiyonu + CSS güncelleneceK.

## Requirements

- NLP-01: KAP duyuruları GPT-4o-mini batch sentiment ile işlenir.
- NLP-02: RSS haber sınıflandırması Türkçe keyword seti ile yapılır; vaderSentiment tamamen kaldırılır.

## Out of Scope

- Gerçek zamanlı (per-request) LLM sentiment — yalnızca APScheduler batch.
- Türkçe transformer modeli entegrasyonu (v2'ye bırakıldı).
- KAP dışı kaynaklar için LLM kullanımı.
