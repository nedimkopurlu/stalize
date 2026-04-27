"""
Günlük portföy snapshot servisi — MPRT-02

Her hafta içi 18:30 İstanbul'da APScheduler tarafından tetiklenir.
Gerçek yfinance kapanış fiyatlarını çeker, günlük P&L hesaplar,
portfolio_daily_snapshots tablosuna upsert yapar.
Mock fiyat veya simülasyon yoktur.
"""
import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Optional

import yfinance as yf
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.portfolio_v2 import PortfolioPosition, PortfolioDailySnapshot
from app.services.source_health import record_source_failure, record_source_success

logger = logging.getLogger(__name__)


async def _fetch_close_price(yahoo_symbol: str) -> Optional[float]:
    """yfinance'den son kapanış fiyatını çek — async (run_in_executor)."""
    loop = asyncio.get_event_loop()

    def _sync_fetch():
        try:
            data = yf.download(yahoo_symbol, period="5d", interval="1d", progress=False)
            if data is None or data.empty:
                return None
            # Son satır bugünkü veya en son işlem günü kapanışı
            close = data["Close"]
            if hasattr(close, "iloc"):
                return float(close.iloc[-1])
            return None
        except Exception as exc:
            logger.warning(f"yfinance fiyat çekme hatası [{yahoo_symbol}]: {exc}")
            return None

    return await loop.run_in_executor(None, _sync_fetch)


async def take_daily_snapshot() -> None:
    """
    Aktif pozisyonların gerçek kapanış fiyatlarını çek,
    günlük P&L hesapla ve portfolio_daily_snapshots'a upsert yap.

    APScheduler tarafından çağrılır — hafta içi 18:30 İstanbul.
    Aktif pozisyon yoksa sessizce çıkar.
    """
    today = date.today()
    logger.info(f"[portfolio_snapshot] {today} snapshot başlıyor...")

    try:
        async with AsyncSessionLocal() as db:
            # Aktif pozisyonları çek
            result = await db.execute(
                select(PortfolioPosition).where(PortfolioPosition.is_active == True)  # noqa: E712
            )
            positions = result.scalars().all()

            if not positions:
                logger.info("[portfolio_snapshot] Aktif pozisyon yok — snapshot atlandı.")
                record_source_success(
                    "portfolio_snapshot",
                    detail={"positions": 0, "reason": "no_active_positions"},
                )
                return

            # Her pozisyon için gerçek fiyat çek
            total_value = 0.0
            total_cost = 0.0
            positions_detail = []
            skipped_symbols = []

            for pos in positions:
                yahoo_symbol = f"{pos.symbol}.IS"
                current_price = await _fetch_close_price(yahoo_symbol)

                if current_price is None:
                    logger.warning(f"[portfolio_snapshot] {pos.symbol} fiyatı alınamadı — atlanıyor.")
                    skipped_symbols.append(pos.symbol)
                    continue

                position_value = current_price * pos.quantity
                position_cost = pos.entry_price * pos.quantity
                pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100

                total_value += position_value
                total_cost += position_cost

                positions_detail.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": current_price,
                    "position_value": round(position_value, 2),
                    "pnl_pct": round(pnl_pct, 4),
                    "stop_loss": pos.stop_loss,
                    "target_price": pos.target_price,
                })

            if total_cost > 0:
                daily_pnl_pct = ((total_value - total_cost) / total_cost) * 100
            else:
                daily_pnl_pct = 0.0

            if not positions_detail:
                error = "No close prices fetched for active portfolio positions"
                detail = {
                    "active_positions": len(positions),
                    "priced_positions": 0,
                    "skipped_symbols": skipped_symbols,
                }
                logger.error("[portfolio_snapshot] %s", error)
                record_source_failure("portfolio_snapshot", error, detail=detail)
                return

            existing_snapshot = (
                await db.execute(
                    select(PortfolioDailySnapshot).where(PortfolioDailySnapshot.date == today)
                )
            ).scalar_one_or_none()

            if existing_snapshot is None:
                db.add(
                    PortfolioDailySnapshot(
                        date=today,
                        total_value=round(total_value, 2),
                        daily_pnl_pct=round(daily_pnl_pct, 4),
                        positions_json=positions_detail,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            else:
                existing_snapshot.total_value = round(total_value, 2)
                existing_snapshot.daily_pnl_pct = round(daily_pnl_pct, 4)
                existing_snapshot.positions_json = positions_detail

            await db.commit()

            detail = {
                "active_positions": len(positions),
                "priced_positions": len(positions_detail),
                "skipped_symbols": skipped_symbols,
                "total_value": round(total_value, 2),
                "daily_pnl_pct": round(daily_pnl_pct, 4),
            }

            record_source_success(
                "portfolio_snapshot",
                detail=detail,
            )

            logger.info(
                f"[portfolio_snapshot] {today} snapshot kaydedildi — "
                f"toplam değer: {total_value:.2f} TRY, günlük P&L: {daily_pnl_pct:.2f}%, "
                f"{len(positions_detail)} pozisyon, {len(skipped_symbols)} atlanan sembol."
            )
    except Exception as exc:
        record_source_failure("portfolio_snapshot", str(exc))
        raise
