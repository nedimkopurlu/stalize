"""MarketRegimeEngine — günlük BIST100 piyasa rejimi tespiti (ADX+EMA200+ATR, USD-düzeltmeli)"""
import logging
from datetime import date

import pandas as pd
import yfinance as yf
import ta
from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.models.market_regime import MarketRegime

logger = logging.getLogger(__name__)


class MarketRegimeEngine:
    """Günlük BIST100 piyasa rejimi tespiti."""

    def _classify_regime(
        self,
        adx: float,
        ema200: float,
        usd_close: float,
        atr: float,
    ) -> str:
        """Kural tabanlı rejim sınıflandırması (öncelik sırası önemli).

        Öncelik:
        1. Volatil  — ATR/kapanış >= %2 (en yüksek öncelik)
        2. Ayı      — kapanış < EMA200 VE ADX > 25
        3. Boğa     — kapanış > EMA200 VE ADX > 25
        4. Yatay    — varsayılan (ADX zayıf veya EMA200 üstü yok)
        """
        atr_ratio = atr / usd_close if usd_close > 0 else 0
        if atr_ratio >= 0.02:
            return "Volatil"
        if usd_close < ema200 and adx > 25:
            return "Ayı"
        if usd_close > ema200 and adx > 25:
            return "Boğa"
        return "Yatay"

    def detect_regime(self) -> dict:
        """XU100.IS verisini çek, USD düzeltmesi yap, rejimi hesapla.

        Returns dict with keys: regime, adx, ema200, atr, usd_close, date
        Raises ValueError if insufficient data.
        """
        xu100 = yf.download("XU100.IS", period="300d", interval="1d", progress=False)
        usdtry = yf.download("USDTRY=X", period="300d", interval="1d", progress=False)
        if xu100.empty or usdtry.empty:
            raise ValueError("XU100.IS veya USDTRY verisi alınamadı")

        # Handle MultiIndex columns from yfinance
        if isinstance(xu100.columns, pd.MultiIndex):
            xu100.columns = xu100.columns.droplevel(1)
        if isinstance(usdtry.columns, pd.MultiIndex):
            usdtry.columns = usdtry.columns.droplevel(1)

        # Align on date index
        aligned = xu100[["Open", "High", "Low", "Close"]].join(
            usdtry[["Close"]].rename(columns={"Close": "USDTRY"}),
            how="inner",
        )
        if len(aligned) < 210:
            raise ValueError(f"Yetersiz veri: {len(aligned)} gün (210 gerekli)")

        usd_close = aligned["Close"] / aligned["USDTRY"]
        usd_high = aligned["High"] / aligned["USDTRY"]
        usd_low = aligned["Low"] / aligned["USDTRY"]

        adx_ind = ta.trend.ADXIndicator(high=usd_high, low=usd_low, close=usd_close, window=14)
        ema_ind = ta.trend.EMAIndicator(close=usd_close, window=200)
        atr_ind = ta.volatility.AverageTrueRange(high=usd_high, low=usd_low, close=usd_close, window=14)

        adx_val = float(adx_ind.adx().dropna().iloc[-1])
        ema200_val = float(ema_ind.ema_indicator().dropna().iloc[-1])
        atr_val = float(atr_ind.average_true_range().dropna().iloc[-1])
        close_val = float(usd_close.iloc[-1])

        regime = self._classify_regime(adx_val, ema200_val, close_val, atr_val)
        return {
            "regime": regime,
            "adx": round(adx_val, 4),
            "ema200": round(ema200_val, 6),
            "atr": round(atr_val, 6),
            "usd_close": round(close_val, 6),
            "date": date.today(),
        }

    async def update_regime(self) -> dict:
        """Bugünkü rejimi hesapla ve DB'ye kaydet (upsert). Returns regime dict."""
        result = self.detect_regime()
        async with AsyncSessionLocal() as db:
            # Delete today's row if exists (upsert pattern)
            await db.execute(
                delete(MarketRegime).where(MarketRegime.date == result["date"])
            )
            row = MarketRegime(
                date=result["date"],
                regime=result["regime"],
                adx=result["adx"],
                ema200=result["ema200"],
                atr=result["atr"],
            )
            db.add(row)
            await db.commit()
        logger.info(
            "MARKET_REGIME_UPDATED regime=%s adx=%.2f", result["regime"], result["adx"]
        )
        return result


market_regime_engine = MarketRegimeEngine()
