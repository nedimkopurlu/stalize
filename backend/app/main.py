from typing import Optional
"""
Stalize Backend — FastAPI Ana Uygulama

"""
import asyncio
import logging
import os
from datetime import datetime, timezone
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

# SQLAlchemy log seviyesi – üretimde WARNING'e çekilmeli
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler()


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
        "tefas": 36,
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
    logging.info("🔴 TETİKLENDİ: KAP anlık bildirim taraması")
    try:
        stored = await run_kap_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"KAP Tarama Hatası: {e}")

async def background_tcmb_scan():
    from app.services.tcmb_adapter import run_tcmb_scan
    from app.services.scoring import scoring_engine
    logging.info("🏦 TETİKLENDİ: TCMB Makro Veri Taraması")
    try:
        stored = await run_tcmb_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"TCMB Tarama Hatası: {e}")

async def background_tuik_scan():
    from app.services.tuik_adapter import run_tuik_scan
    from app.services.scoring import scoring_engine
    logging.info("📊 TETİKLENDİ: TUIK Ekonomik Veri Taraması")
    try:
        stored = await run_tuik_scan()
        if stored > 0:
            await scoring_engine.update_all_scores()
    except Exception as e:
        logging.error(f"TUIK Tarama Hatası: {e}")

async def background_borsa_istanbul_scan():
    from app.services.official_news_ingest import run_borsa_istanbul_scan
    logging.info("📣 TETİKLENDİ: Borsa İstanbul duyuru taraması")
    try:
        await run_borsa_istanbul_scan()
    except Exception as e:
        logging.error(f"Borsa İstanbul tarama hatası: {e}")

async def background_bist_datastore_scan():
    from app.services.official_news_ingest import run_bist_datastore_scan
    logging.info("🗂️ TETİKLENDİ: BIST datastore katalog taraması")
    try:
        await run_bist_datastore_scan()
    except Exception as e:
        logging.error(f"BIST datastore tarama hatası: {e}")

async def background_mkk_scan():
    from app.services.official_news_ingest import run_mkk_scan
    logging.info("📘 TETİKLENDİ: MKK piyasa bülteni taraması")
    try:
        await run_mkk_scan()
    except Exception as e:
        logging.error(f"MKK tarama hatası: {e}")


async def background_hmb_scan():
    from app.services.official_news_ingest import run_hmb_scan

    logging.info("💼 TETİKLENDİ: HMB resmi yayın taraması")
    try:
        await run_hmb_scan()
    except Exception as e:
        logging.error(f"HMB tarama hatası: {e}")

async def background_takasbank_scan():
    from app.services.official_news_ingest import run_takasbank_scan
    logging.info("🏦 TETİKLENDİ: Takasbank resmi duyuru taraması")
    try:
        await run_takasbank_scan()
    except Exception as e:
        logging.error(f"Takasbank tarama hatası: {e}")


async def background_tefas_scan():
    from app.services.official_ingest import get_source_runner

    logging.info("📈 TETİKLENDİ: TEFAS fon evreni taraması")
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
    logging.info("📊 TETİKLENDİ: Dinamik Korelasyon Matrisi Taraması")
    try:
        result = await run_dynamic_correlation_scan()
        if result.get("crisis_mode"):
            logging.warning("⚠️ KRİZ MODU TETİKLENDİ!")
    except Exception as e:
        logging.error(f"Dinamik Korelasyon Hatası: {e}")


async def background_model_portfolio_generate():
    from app.services.model_portfolio import generate_weekly_model_portfolio

    logging.info("🧠 TETİKLENDİ: Haftalık model portföy üretimi")
    try:
        await generate_weekly_model_portfolio(force=True)
    except Exception as e:
        logging.error(f"Model portföy üretim hatası: {e}")


async def background_model_portfolio_snapshot():
    from app.services.model_portfolio import take_model_portfolio_snapshot

    logging.info("📒 TETİKLENDİ: Model portföy günlük snapshot")
    try:
        await take_model_portfolio_snapshot()
    except Exception as e:
        logging.error(f"Model portföy snapshot hatası: {e}")


async def background_data_update():
    logging.info("📈 TETİKLENDİ: Hisse fiyat + temel veri güncelleme (yfinance)")
    try:
        await data_collector.daily_update()
    except Exception as e:
        logging.error(f"DataCollector güncelleme hatası: {e}")


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
        "tefas",
    ]
    runtime = get_all_source_health()

    for source_key in source_order:
        runner = get_source_runner(source_key)
        if runner is None:
            continue

        if not _should_run_startup_refresh(source_key, runtime.get(source_key, {})):
            continue

        logging.info("🔄 Startup catch-up: %s kaynağı tazeleniyor", source_key)
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

    # KAP taraması
    scheduler.add_job(background_kap_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # TCMB Makro Veri taraması
    scheduler.add_job(background_tcmb_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # TUIK Ekonomik Veri taraması
    scheduler.add_job(background_tuik_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Borsa İstanbul duyuru taraması
    scheduler.add_job(background_borsa_istanbul_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # BIST datastore konsolide veri katalog taraması
    scheduler.add_job(background_bist_datastore_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # HMB resmi yayın taraması
    scheduler.add_job(background_hmb_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Takasbank duyuru taraması
    scheduler.add_job(background_takasbank_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # MKK aylık bülten kontrolü
    scheduler.add_job(background_mkk_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # TEFAS fon evreni tazeleme
    scheduler.add_job(background_tefas_scan, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Dinamik Korelasyon Matrisi
    scheduler.add_job(background_dynamic_correlation, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Model Portföy Günlük Snapshot
    scheduler.add_job(take_daily_snapshot, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Haftalık model portföy üretimi
    scheduler.add_job(background_model_portfolio_generate, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Model portföy günlük izleme snapshot'ı
    scheduler.add_job(background_model_portfolio_snapshot, "interval", minutes=5, max_instances=1, misfire_grace_time=300)

    # Hisse fiyat + temel veri güncelleme (yfinance)
    scheduler.add_job(background_data_update, "interval", minutes=30, max_instances=1, misfire_grace_time=600)

    scheduler.start()
    asyncio.create_task(startup_refresh_sources())
    asyncio.create_task(data_collector.full_initial_load())
    logging.info(
        "Zamanlanmış veri tarama görevleri başlatıldı "
        "(Tüm kaynaklar 5 dakikada bir güncellenecek şekilde ayarlandı)."
    )

    yield

    logging.info("🛑 Stalize API kapatılıyor...")
    scheduler.shutdown()
    await database.async_engine.dispose()


app = FastAPI(
    title="Stalize — BIST100 Analiz API",
    description="Teknik + Temel + Haber Analizi ile BIST100 hisse analizi",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow_origins env var ile override edilebilir; yoksa her yerden açık
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _cors_origins.split(",")] if _cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
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
