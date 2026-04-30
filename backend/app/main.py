from typing import Optional
"""
Stalize Backend — FastAPI Ana Uygulama

"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models as _models  # noqa: F401
from app.core.config import settings
from app.core import database
from app.api import stocks, macro, intelligence, admin, portfolio_v2, model_portfolio
from app.services.portfolio_snapshot import take_daily_snapshot
from app.services.data_collector import data_collector

# Structured logging — machine-parseable format, no emoji
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
# SQLAlchemy log seviyesi — üretimde WARNING'e çekilmeli
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler()


def _log_task_error(task: asyncio.Task) -> None:
    """Done-callback for startup asyncio tasks. Logs exceptions so failures are visible."""
    if task.cancelled():
        logging.warning("STARTUP_TASK_CANCELLED [%s]", task.get_name())
        return
    exc = task.exception()
    if exc is not None:
        logging.error(
            "STARTUP_TASK_ERROR [%s]: %s",
            task.get_name(),
            exc,
            exc_info=exc,
        )


def _parse_runtime_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _startup_refresh_due_hours(source_key: str) -> int:
    return {
        "kap": 6,
        "tcmb": 24,
        "tuik": 48,
        "borsa_istanbul": 24,
        "bist_datastore": 24,
        "hmb": 24,
        "takasbank": 24,
        "mkk": 168,
    }.get(source_key, 24)


def _should_run_startup_refresh(source_key: str, runtime: dict) -> bool:
    last_success = _parse_runtime_ts(runtime.get("last_successful_fetch"))
    if last_success is None:
        return True
    age_hours = (datetime.now(timezone.utc) - last_success).total_seconds() / 3600
    return age_hours >= _startup_refresh_due_hours(source_key)

async def background_kap_scan():
    from app.services.kap_parser import run_kap_scan
    from app.services.scoring import scoring_engine
    logging.info("JOB_START source=kap")
    try:
        stored = await run_kap_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"KAP Tarama Hatası: {e}")

async def background_tcmb_scan():
    from app.services.tcmb_adapter import run_tcmb_scan
    from app.services.scoring import scoring_engine
    logging.info("JOB_START source=tcmb")
    try:
        stored = await run_tcmb_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"TCMB Tarama Hatası: {e}")

async def background_tuik_scan():
    from app.services.tuik_adapter import run_tuik_scan
    from app.services.scoring import scoring_engine
    logging.info("JOB_START source=tuik")
    try:
        stored = await run_tuik_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"TUIK Tarama Hatası: {e}")

async def background_borsa_istanbul_scan():
    from app.services.official_news_ingest import run_borsa_istanbul_scan
    logging.info("JOB_START source=borsa_istanbul")
    try:
        await run_borsa_istanbul_scan()
    except Exception as e:
        logging.error(f"Borsa İstanbul tarama hatası: {e}")

async def background_bist_datastore_scan():
    from app.services.official_news_ingest import run_bist_datastore_scan
    logging.info("JOB_START source=bist_datastore")
    try:
        await run_bist_datastore_scan()
    except Exception as e:
        logging.error(f"BIST datastore tarama hatası: {e}")

async def background_mkk_scan():
    from app.services.official_news_ingest import run_mkk_scan
    logging.info("JOB_START source=mkk")
    try:
        await run_mkk_scan()
    except Exception as e:
        logging.error(f"MKK tarama hatası: {e}")


async def background_hmb_scan():
    from app.services.official_news_ingest import run_hmb_scan

    logging.info("JOB_START source=hmb")
    try:
        await run_hmb_scan()
    except Exception as e:
        logging.error(f"HMB tarama hatası: {e}")

async def background_takasbank_scan():
    from app.services.official_news_ingest import run_takasbank_scan
    logging.info("JOB_START source=takasbank")
    try:
        await run_takasbank_scan()
    except Exception as e:
        logging.error(f"Takasbank tarama hatası: {e}")


async def background_tefas_scan():
    from app.services.official_ingest import get_source_runner

    logging.info("JOB_START source=tefas")
    try:
        runner = get_source_runner("tefas")
        if runner is None:
            logging.warning("TEFAS runner bulunamadı, tarama atlandı.")
            return
        await runner()
    except Exception as e:
        logging.error(f"TEFAS tarama hatası: {e}")

async def background_dynamic_correlation():
    from app.services.dynamic_correlation import run_dynamic_correlation_scan
    logging.info("JOB_START source=dynamic_correlation")
    try:
        result = await run_dynamic_correlation_scan()
        if result.get("crisis_mode"):
            logging.warning("CRISIS_MODE_TRIGGERED source=dynamic_correlation")
    except Exception as e:
        logging.error(f"Dinamik Korelasyon Hatası: {e}")


async def background_model_portfolio_generate():
    from app.services.model_portfolio import generate_weekly_model_portfolio

    logging.info("JOB_START source=model_portfolio_generate")
    try:
        await generate_weekly_model_portfolio(force=False)
    except Exception as e:
        logging.error(f"Model portföy üretim hatası: {e}")


async def background_model_portfolio_snapshot():
    from app.services.model_portfolio import take_model_portfolio_snapshot

    logging.info("JOB_START source=model_portfolio_snapshot")
    try:
        await take_model_portfolio_snapshot()
    except Exception as e:
        logging.error(f"Model portföy snapshot hatası: {e}")


async def background_data_update():
    logging.info("JOB_START source=data_update")
    try:
        await data_collector.daily_update()
    except Exception as e:
        logging.error(f"DataCollector güncelleme hatası: {e}")


async def background_fundamentals_update():
    """Temel finansal verileri haftalık güncelle (F/K, PD/DD, ROE vb.)."""
    logging.info("JOB_START source=fundamentals")
    try:
        await data_collector.collect_fundamentals()
    except Exception as e:
        logging.error(f"Temel veri güncelleme hatası: {e}", exc_info=True)


async def startup_seed_stock_universe():
    """Fast startup seed: keep BIST100 metadata canonical without triggering heavy backfills."""
    await data_collector.initialize_stocks()
    if await data_collector.live_price_refresh_needed(max_age_minutes=60):
        await data_collector.collect_live_bist_quotes()


async def startup_refresh_sources():
    from app.services.official_ingest import get_source_runner
    from app.services.source_health import get_all_source_health

    source_order = [
        "kap",
        "tcmb",
        "tuik",
        "borsa_istanbul",
        "bist_datastore",
        "hmb",
        "takasbank",
        "mkk",
    ]
    runtime = get_all_source_health()

    for source_key in source_order:
        runner = get_source_runner(source_key)
        if runner is None:
            continue

        if not _should_run_startup_refresh(source_key, runtime.get(source_key, {})):
            continue

        logging.info("STARTUP_CATCHUP source=%s", source_key)
        try:
            await runner()
        except Exception as exc:
            logging.error("Startup catch-up hatası [%s]: %s", source_key, exc)
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç & kapanış."""
    logging.info("Stalize API başlıyor...")

    # Runtime dizinlerini oluştur (Railway'de yoksa)
    for d in ["runtime", "cache", "cache/llm", "cache/yfinance", "models"]:
        os.makedirs(d, exist_ok=True)

    # Tablo oluştur (eğer yoksa)
    async with database.async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    # Feedparser startup validation (FOND-01)
    try:
        import feedparser  # noqa: F401
    except ModuleNotFoundError:
        raise RuntimeError("feedparser is not installed. Install it with: pip install feedparser==6.0.11")

    _now = datetime.now(timezone.utc)

    # KAP taraması
    scheduler.add_job(background_kap_scan, "interval", minutes=settings.KAP_SCAN_INTERVAL_MIN, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=0))

    # TCMB Makro Veri taraması
    scheduler.add_job(background_tcmb_scan, "interval", minutes=60, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=30))

    # TUIK Ekonomik Veri taraması
    scheduler.add_job(background_tuik_scan, "interval", minutes=180, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=60))

    # Borsa İstanbul duyuru taraması
    scheduler.add_job(background_borsa_istanbul_scan, "interval", minutes=30, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=90))

    # BIST datastore konsolide veri katalog taraması
    scheduler.add_job(background_bist_datastore_scan, "interval", minutes=120, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=120))

    # HMB resmi yayın taraması
    scheduler.add_job(background_hmb_scan, "interval", minutes=60, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=150))

    # Takasbank duyuru taraması
    scheduler.add_job(background_takasbank_scan, "interval", minutes=60, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=180))

    # MKK aylık bülten kontrolü
    scheduler.add_job(background_mkk_scan, "interval", minutes=360, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=210))

    # Dinamik Korelasyon Matrisi
    scheduler.add_job(background_dynamic_correlation, "interval", minutes=60, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(seconds=240))

    # Model Portföy Günlük Snapshot
    scheduler.add_job(take_daily_snapshot, "interval", hours=24, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(minutes=15))

    # Haftalık model portföy üretimi
    scheduler.add_job(background_model_portfolio_generate, "interval", hours=6, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(minutes=5))

    # Model portföy günlük izleme snapshot'ı
    scheduler.add_job(background_model_portfolio_snapshot, "interval", hours=1, max_instances=1, misfire_grace_time=300, start_date=_now + timedelta(minutes=6))

    # Hisse fiyat + teknik veri güncelleme (yfinance)
    scheduler.add_job(
        background_data_update,
        "interval",
        hours=settings.DATA_UPDATE_INTERVAL_HOURS,
        max_instances=1,
        misfire_grace_time=300,
        start_date=_now + timedelta(minutes=10),
    )

    # Temel finansal veri güncelleme — haftalık (F/K, PD/DD, ROE)
    scheduler.add_job(
        background_fundamentals_update,
        "interval",
        hours=168,  # 7 gün
        max_instances=1,
        misfire_grace_time=3600,
        start_date=_now + timedelta(minutes=25),
    )

    scheduler.start()
    _task_startup_refresh = asyncio.create_task(
        startup_refresh_sources(), name="startup_refresh_sources"
    )
    _task_startup_refresh.add_done_callback(_log_task_error)

    initial_load_coro = (
        data_collector.full_initial_load()
        if settings.RUN_FULL_INITIAL_LOAD_ON_STARTUP
        else startup_seed_stock_universe()
    )
    _task_initial_load = asyncio.create_task(
        initial_load_coro,
        name="full_initial_load" if settings.RUN_FULL_INITIAL_LOAD_ON_STARTUP else "startup_seed_stock_universe",
    )
    _task_initial_load.add_done_callback(_log_task_error)
    logging.info(
        "Zamanlanmış veri tarama görevleri başlatıldı "
        "(KAP hızlı, resmi kaynaklar ölçülü, model portföy haftalık mantıkla güncellenecek)."
    )

    yield

    logging.info("APP_SHUTDOWN")
    scheduler.shutdown()
    await database.async_engine.dispose()


app = FastAPI(
    title="Stalize — BIST100 Analiz API",
    description="Teknik + Temel + Haber Analizi ile BIST100 hisse analizi",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow_origins env var ile override edilebilir; yoksa localhost'a kısıtlı
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
if "*" in _origins:
    logging.warning(
        "CORS_ORIGINS wildcard (*) is not allowed; falling back to localhost-only."
    )
    _origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API rotaları
app.include_router(stocks.router, prefix="/api")
app.include_router(macro.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(portfolio_v2.router, prefix="/api")
app.include_router(model_portfolio.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Stalize",
        "description": "BIST100 Hisse Analiz Platformu",
        "version": "1.0.0",
        "api_docs": "/docs",
    }
