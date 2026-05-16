"""Strategy backtesting for BIST signals.

The engine is deliberately deterministic: it simulates rule-based entries,
stops, targets and trailing stops from stored daily OHLCV data, then compares
the result with BIST100. This makes the signal system auditable before an LLM
adds narrative.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import sqrt
from statistics import mean, pstdev
from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import CommodityPrice, PriceHistory
from app.models.stock import Stock


BENCHMARK_SYMBOL = "XU100.IS"


@dataclass(frozen=True)
class StrategySpec:
    key: str
    label: str
    description: str
    max_hold_days: int
    stop_atr: float
    target_r: float
    trailing_atr: Optional[float] = None


STRATEGIES: dict[str, StrategySpec] = {
    "trend_quality": StrategySpec(
        key="trend_quality",
        label="Trend + Kalite",
        description="Fiyat 50/200 gunluk ortalamalar ustunde, RSI asiri sisik degil ve hacim destekli.",
        max_hold_days=30,
        stop_atr=2.0,
        target_r=2.2,
        trailing_atr=2.4,
    ),
    "breakout": StrategySpec(
        key="breakout",
        label="Hacimli Kirilim",
        description="20 gunluk zirve kirilimi ve hacim genislemesi yakalar.",
        max_hold_days=20,
        stop_atr=1.8,
        target_r=2.0,
        trailing_atr=2.0,
    ),
    "mean_reversion": StrategySpec(
        key="mean_reversion",
        label="Asiri Satim Tepkisi",
        description="RSI dusuk ve fiyat Bollinger alt bandina yakin oldugunda tepki arar.",
        max_hold_days=12,
        stop_atr=1.5,
        target_r=1.4,
        trailing_atr=None,
    ),
    "composite_signal": StrategySpec(
        key="composite_signal",
        label="Kompozit Sinyal",
        description="Trend, hacim, RSI ve genel skorun ayni anda makul oldugu daha secici sinyal.",
        max_hold_days=25,
        stop_atr=2.0,
        target_r=2.4,
        trailing_atr=2.2,
    ),
}


class BacktestService:
    """Runs strategy simulations over the local price history."""

    async def run(
        self,
        db: AsyncSession,
        strategy: str = "composite_signal",
        years: int = 1,
        symbols: Optional[list[str]] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        spec = STRATEGIES.get(strategy)
        if spec is None:
            raise ValueError(f"Bilinmeyen strateji: {strategy}")

        end_date = await self._latest_price_date(db)
        if end_date is None:
            return self._empty_response(spec, years, "Fiyat gecmisi bulunamadi.")
        start_date = end_date - timedelta(days=365 * years + 260)
        evaluation_start = end_date - timedelta(days=365 * years)

        stocks = await self._load_stocks(db, symbols=symbols, limit=limit)
        price_map = await self._load_prices(db, [stock.id for stock in stocks], start_date)
        benchmark = await self._benchmark_return(db, evaluation_start, end_date)

        stock_results = []
        all_trades = []
        for stock in stocks:
            rows = price_map.get(stock.id, [])
            trades = self._simulate_stock(stock, rows, spec, evaluation_start)
            metrics = self._metrics(trades, benchmark)
            stock_results.append(
                {
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "sector": stock.sector,
                    **metrics,
                    "trades": trades[-10:],
                }
            )
            all_trades.extend(trades)

        portfolio_metrics = self._metrics(all_trades, benchmark)
        verdict = self._verdict(portfolio_metrics)
        return {
            "strategy": {
                "key": spec.key,
                "label": spec.label,
                "description": spec.description,
            },
            "period": {
                "years": years,
                "start": evaluation_start.isoformat(),
                "end": end_date.isoformat(),
            },
            "benchmark": benchmark,
            "portfolio": portfolio_metrics,
            "verdict": verdict,
            "stocks": sorted(
                stock_results,
                key=lambda item: (
                    item["total_return_pct"] if item["total_return_pct"] is not None else -999,
                    item["win_rate_pct"] if item["win_rate_pct"] is not None else -999,
                ),
                reverse=True,
            )[:30],
            "trade_count": len(all_trades),
        }

    async def compare_all(self, db: AsyncSession, years: int = 1, limit: int = 100) -> dict[str, Any]:
        results = []
        for key in STRATEGIES:
            results.append(await self.run(db, strategy=key, years=years, limit=limit))
        return {
            "years": years,
            "benchmark_symbol": BENCHMARK_SYMBOL,
            "strategies": [
                {
                    "strategy": result["strategy"],
                    "period": result["period"],
                    "benchmark": result["benchmark"],
                    "portfolio": result["portfolio"],
                    "verdict": result["verdict"],
                    "trade_count": result["trade_count"],
                }
                for result in results
            ],
        }

    async def _latest_price_date(self, db: AsyncSession) -> Optional[date]:
        result = await db.execute(select(PriceHistory.date).order_by(PriceHistory.date.desc()).limit(1))
        return result.scalar_one_or_none()

    async def _load_stocks(
        self,
        db: AsyncSession,
        symbols: Optional[list[str]],
        limit: int,
    ) -> list[Stock]:
        query = select(Stock).where(Stock.is_active, Stock.current_price.isnot(None))
        if symbols:
            query = query.where(Stock.symbol.in_([symbol.upper().removesuffix(".IS") for symbol in symbols]))
        query = query.order_by(Stock.overall_score.desc().nullslast()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def _load_prices(
        self,
        db: AsyncSession,
        stock_ids: list[int],
        start_date: date,
    ) -> dict[int, list[PriceHistory]]:
        if not stock_ids:
            return {}
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.stock_id.in_(stock_ids), PriceHistory.date >= start_date)
            .order_by(PriceHistory.stock_id.asc(), PriceHistory.date.asc())
        )
        output: dict[int, list[PriceHistory]] = {stock_id: [] for stock_id in stock_ids}
        for row in result.scalars().all():
            output.setdefault(row.stock_id, []).append(row)
        return output

    async def _benchmark_return(self, db: AsyncSession, start: date, end: date) -> dict[str, Any]:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == BENCHMARK_SYMBOL, CommodityPrice.date >= start, CommodityPrice.date <= end)
            .order_by(CommodityPrice.date.asc())
        )
        rows = [row for row in result.scalars().all() if row.close and row.close > 0]
        if len(rows) < 2:
            return {
                "symbol": BENCHMARK_SYMBOL,
                "return_pct": None,
                "start_close": None,
                "end_close": None,
            }
        return {
            "symbol": BENCHMARK_SYMBOL,
            "return_pct": round(((rows[-1].close / rows[0].close) - 1.0) * 100, 2),
            "start_close": round(float(rows[0].close), 2),
            "end_close": round(float(rows[-1].close), 2),
        }

    def _simulate_stock(
        self,
        stock: Stock,
        prices: list[PriceHistory],
        spec: StrategySpec,
        evaluation_start: date,
    ) -> list[dict[str, Any]]:
        trades = []
        in_trade: Optional[dict[str, Any]] = None
        for idx, row in enumerate(prices):
            if row.close <= 0:
                continue

            if in_trade is not None:
                exit_trade = self._maybe_exit(row, in_trade, spec)
                if exit_trade:
                    trades.append(exit_trade)
                    in_trade = None
                continue

            if row.date < evaluation_start or idx < 30:
                continue
            if self._entry_signal(prices, idx, spec, stock):
                entry = float(row.close)
                atr = self._atr(row, entry)
                stop = max(0.01, entry - spec.stop_atr * atr)
                risk = max(entry - stop, entry * 0.005)
                in_trade = {
                    "symbol": stock.symbol,
                    "entry_date": row.date,
                    "entry_price": entry,
                    "stop": stop,
                    "highest_close": entry,
                    "target": entry + spec.target_r * risk,
                    "holding_days": 0,
                }

        if in_trade is not None and prices:
            last = prices[-1]
            trades.append(self._close_trade(last, in_trade, "period_end"))
        return trades

    def _entry_signal(self, prices: list[PriceHistory], idx: int, spec: StrategySpec, stock: Stock) -> bool:
        row = prices[idx]
        prev = prices[idx - 1]
        close = float(row.close)
        avg_volume = self._avg([p.volume for p in prices[max(0, idx - 20):idx] if p.volume])
        volume_ratio = (float(row.volume) / avg_volume) if avg_volume and row.volume else 1.0
        recent_high = max(float(p.high or p.close) for p in prices[max(0, idx - 20):idx])
        rsi = row.rsi_14
        score = float(stock.overall_score or 50)

        if spec.key == "trend_quality":
            return bool(row.sma_50 and row.sma_200 and close > row.sma_50 > row.sma_200 and (rsi is None or 45 <= rsi <= 72))
        if spec.key == "breakout":
            return close > recent_high and volume_ratio >= 1.25
        if spec.key == "mean_reversion":
            lower_band_ok = row.bb_lower is not None and close <= row.bb_lower * 1.03
            return bool((rsi is not None and rsi <= 35) or lower_band_ok)
        if spec.key == "composite_signal":
            trend_ok = bool(row.sma_50 and close > row.sma_50 and (row.sma_200 is None or close > row.sma_200))
            momentum_ok = bool(prev.macd is not None and prev.macd_signal is not None and row.macd is not None and row.macd_signal is not None and prev.macd <= prev.macd_signal and row.macd > row.macd_signal)
            volume_ok = volume_ratio >= 1.1
            rsi_ok = rsi is None or 42 <= rsi <= 70
            return trend_ok and rsi_ok and (momentum_ok or volume_ok) and score >= 58
        return False

    def _maybe_exit(self, row: PriceHistory, trade: dict[str, Any], spec: StrategySpec) -> Optional[dict[str, Any]]:
        close = float(row.close)
        trade["holding_days"] += 1
        trade["highest_close"] = max(trade["highest_close"], close)
        if spec.trailing_atr:
            atr = self._atr(row, close)
            trade["stop"] = max(trade["stop"], trade["highest_close"] - spec.trailing_atr * atr)
        if close <= trade["stop"]:
            return self._close_trade(row, trade, "stop")
        if close >= trade["target"]:
            return self._close_trade(row, trade, "target")
        if trade["holding_days"] >= spec.max_hold_days:
            return self._close_trade(row, trade, "time_exit")
        return None

    def _close_trade(self, row: PriceHistory, trade: dict[str, Any], reason: str) -> dict[str, Any]:
        exit_price = float(row.close)
        return_pct = ((exit_price / trade["entry_price"]) - 1.0) * 100
        return {
            "symbol": trade["symbol"],
            "entry_date": trade["entry_date"].isoformat(),
            "exit_date": row.date.isoformat(),
            "entry_price": round(trade["entry_price"], 2),
            "exit_price": round(exit_price, 2),
            "return_pct": round(return_pct, 2),
            "holding_days": trade["holding_days"],
            "exit_reason": reason,
        }

    def _metrics(self, trades: list[dict[str, Any]], benchmark: dict[str, Any]) -> dict[str, Any]:
        sorted_trades = sorted(trades, key=lambda trade: (trade["exit_date"], trade["symbol"]))
        returns = [float(trade["return_pct"]) for trade in sorted_trades]
        wins = [value for value in returns if value > 0]
        losses = [value for value in returns if value <= 0]
        equity = 100.0
        equity_curve = []
        for value in returns:
            equity *= 1.0 + (value / 100.0 * 0.10)
            equity_curve.append(equity)
        total_return = round(equity - 100.0, 2) if returns else None
        benchmark_return = benchmark.get("return_pct")
        return {
            "trades": len(returns),
            "total_return_pct": total_return,
            "benchmark_return_pct": benchmark_return,
            "excess_return_pct": round(total_return - benchmark_return, 2) if total_return is not None and benchmark_return is not None else None,
            "max_drawdown_pct": self._max_drawdown(equity_curve),
            "win_rate_pct": round(len(wins) / len(returns) * 100, 1) if returns else None,
            "avg_gain_pct": round(mean(wins), 2) if wins else None,
            "avg_loss_pct": round(mean(losses), 2) if losses else None,
            "avg_trade_pct": round(mean(returns), 2) if returns else None,
            "profit_factor": self._profit_factor(wins, losses),
            "volatility_pct": round(pstdev(returns) * sqrt(max(len(returns), 1)), 2) if len(returns) > 1 else None,
        }

    def _verdict(self, metrics: dict[str, Any]) -> dict[str, str]:
        trades = metrics.get("trades") or 0
        total = metrics.get("total_return_pct")
        excess = metrics.get("excess_return_pct")
        drawdown = metrics.get("max_drawdown_pct")
        win_rate = metrics.get("win_rate_pct")
        if trades < 10:
            return {"status": "insufficient_data", "label": "Veri yetersiz", "reason": "Strateji bu donemde yeterli sayida islem uretmedi."}
        if total is not None and excess is not None and total > 0 and excess > 0 and (drawdown is None or drawdown > -18) and (win_rate or 0) >= 45:
            return {"status": "passed", "label": "Calismis", "reason": "Getiri pozitif, BIST100 uzeri ve dusus kontrol edilebilir seviyede."}
        if total is not None and total > 0 and (drawdown is None or drawdown > -25):
            return {"status": "mixed", "label": "Secici kullan", "reason": "Pozitif getiri var ancak benchmark veya risk metrikleri tam ikna edici degil."}
        if total is not None and total > 0:
            return {"status": "mixed", "label": "Riskli calismis", "reason": "Getiri pozitif fakat maksimum dusus yuksek; pozisyon boyutu ve stop disiplini zorunlu."}
        return {"status": "failed", "label": "Calismamis", "reason": "Getiri veya risk profili stratejiyi savunmak icin yetersiz."}

    def _max_drawdown(self, equity_curve: list[float]) -> Optional[float]:
        if not equity_curve:
            return None
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            drawdown = (value / peak - 1.0) * 100
            max_dd = min(max_dd, drawdown)
        return round(max_dd, 2)

    def _profit_factor(self, wins: list[float], losses: list[float]) -> Optional[float]:
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        if gross_loss == 0:
            return round(gross_profit, 2) if gross_profit else None
        return round(gross_profit / gross_loss, 2)

    def _atr(self, row: PriceHistory, fallback_price: float) -> float:
        if row.atr_14 and row.atr_14 > 0:
            return float(row.atr_14)
        if row.high and row.low and row.high > row.low:
            return max(float(row.high - row.low), fallback_price * 0.015)
        return fallback_price * 0.025

    def _avg(self, values: Iterable[float]) -> Optional[float]:
        items = [float(value) for value in values if value is not None]
        return sum(items) / len(items) if items else None

    def _empty_response(self, spec: StrategySpec, years: int, reason: str) -> dict[str, Any]:
        return {
            "strategy": {"key": spec.key, "label": spec.label, "description": spec.description},
            "period": {"years": years, "start": None, "end": None},
            "benchmark": {"symbol": BENCHMARK_SYMBOL, "return_pct": None},
            "portfolio": self._metrics([], {"return_pct": None}),
            "verdict": {"status": "insufficient_data", "label": "Veri yetersiz", "reason": reason},
            "stocks": [],
            "trade_count": 0,
        }


backtest_service = BacktestService()
