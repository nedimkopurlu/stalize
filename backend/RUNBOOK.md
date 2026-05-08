# Stalize Runbook

## Amaç

Bu runbook, Stalize'in yerel ya da tek node üretim benzeri ortamda ayağa kaldırılması, doğrulanması ve arıza anında hızlı toparlanması için kullanılır.

## Başlatma

Backend:

```bash
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/backend
./.venv_repaired/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend
npm run dev
```

## Temel Doğrulama

```bash
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize
./backend/.venv_repaired/bin/python3 backend/scripts/smoke_test.py
```

Beklenen kritik yüzeyler:

- `/api/health`
- `/api/dashboard`
- `/api/intelligence/overview`
- `/api/stocks/THYAO/score-breakdown`
- `/api/model-portfolio/current`
- `/api/model-portfolio/history?limit=4`
- `/api/sources/catalog`
- `/api/sources/health/history?limit=5`
- `/`
- `/model-portfolio`

## Operasyon Notları

- KAP birinci kaynak olduğu için `kap` durumu `fresh` değilse önce o toparlanmalıdır.
- `portfolio_snapshot` aktif pozisyon yoksa `idle` görünebilir; bu arıza değildir.
- `bist_datastore` dosya uçları zaman zaman upstream `500` dönebilir; bu durumda metadata snapshot akışı yine izlenmelidir.
- Haber/skor yüzeyleri çalışıyor ama veri yoksa boş dönebilir; bu kırık sayılmaz.

## Manuel Toparlama

Belirli bir kaynağı elle tetiklemek için:

```bash
curl -X POST -H "X-API-Key: <API_KEY>" http://localhost:8000/api/sources/scan/kap
curl -X POST -H "X-API-Key: <API_KEY>" http://localhost:8000/api/sources/scan/tcmb
curl -X POST -H "X-API-Key: <API_KEY>" http://localhost:8000/api/sources/scan/tuik
curl -X POST -H "X-API-Key: <API_KEY>" http://localhost:8000/api/sources/scan/hmb
```

Model portföyü elle güncellemek için:

```bash
curl -X POST -H "X-API-Key: <API_KEY>" "http://localhost:8000/api/model-portfolio/generate?force=true"
```

## Sertleştirme Standardı

- Şema yönetimi: Alembic dosyaları repoda tutulur, ama uygulama başlangıcında `create_all` da koruma sağlar.
- Cache katmanı: tek kullanıcı/tek node çalışmada mevcut `diskcache` üretim cache katmanıdır.
- Smoke test geçmeden “çalışıyor” denmez.
- Health ekranında `failing` ya da `missing` kalan tier1 kaynakla deploy tamamlandı sayılmaz.
- Yeni fazlar bittiğinde planning, smoke ve canlı endpoint doğrulaması birlikte güncellenir.
