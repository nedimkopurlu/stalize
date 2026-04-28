# Phase 22: Async Infrastructure - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Bu faz, backend'in async güvenliğini ve veritabanı bağlantı havuzu yönetimini düzeltir. Kapsam: `time.sleep()` → `await asyncio.sleep()` geçişi, tüm route handler'larının `Depends(get_db)` pattern'ine alınması, APScheduler job'larının staggered başlatılması ve startup task hatalarının sessizce yutulmaması. Kullanıcıya görünen herhangi bir UI değişikliği içermez.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
Pure infrastructure phase — tüm implementasyon kararları Claude'un takdirine bırakılmıştır.

- `time.sleep()` → `await asyncio.sleep()`: data_collector.py ve macro_news.py içindeki tüm sync sleep'ler değiştirilir
- `AsyncSessionLocal()` doğrudan çağrısı: tüm API route handler'larında `Depends(get_db)` ile değiştirilir
- Scheduler staggering: `start_date` parametresi ile her job farklı zaman diliminde başlatılır (örn. dakika offset'leri)
- Startup task tracking: `asyncio.create_task()` sonuçları yakalanır, hata durumunda loglama yapılır

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/core/database.py` — `AsyncSessionLocal`, `get_db()` dependency mevcut
- `backend/app/main.py` — APScheduler job tanımları, startup event handler'ları
- `backend/app/services/data_collector.py` — yfinance retry loop, `time.sleep()` kullanımı
- `backend/app/services/macro_news.py` — async context içinde `time.sleep()` kullanımı

### Established Patterns
- FastAPI `Depends()` pattern zaten config.py, database.py'de kullanılıyor
- APScheduler `add_job()` ile `start_date` destekliyor
- Python `asyncio.sleep()` drop-in replacement for `time.sleep()` in async context

### Integration Points
- Tüm `backend/app/api/*.py` route dosyaları DB session yönetimini değiştirecek
- `backend/app/main.py` scheduler konfigürasyonu ve lifespan event'leri
- `backend/app/services/` — async context'teki tüm sleep çağrıları

</code_context>

<specifics>
## Specific Ideas

- ASYNC-01: `data_collector.py:59` ve `macro_news.py:77` — `time.sleep()` → `await asyncio.sleep()`
- ASYNC-02: `backend/app/api/` altındaki tüm dosyalarda `async with AsyncSessionLocal() as db:` → `db: AsyncSession = Depends(get_db)` olarak route signature'a taşınacak
- ASYNC-03: APScheduler'da her job için `start_date` ile minute-level offset eklenir (örn. job 1: +0dk, job 2: +1dk, ... 14 job'a dağıtılır)
- ASYNC-04: `asyncio.create_task()` çağrıları `.add_done_callback()` veya try/except içinde wrap edilir; hata durumunda `logger.error()` çağrılır

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
