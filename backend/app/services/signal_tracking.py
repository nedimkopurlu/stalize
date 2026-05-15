"""Persist signal decisions and evaluate their realized outcomes."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_regime import MarketRegime
from app.models.price import CommodityPrice, PriceHistory
from app.models.signal import SignalDecisionSnapshot
from app.models.stock import Stock
from app.services.investment_decision import DecisionInput, DecisionPolicy, investment_decision_engine

BENCHMARK_SYMBOL = "XU100.IS"
MARKET_TZ = ZoneInfo("Europe/Istanbul")


def calculate_round_trip_cost(is_bist30: bool, liquidity_score: Optional[str]) -> float:
    """Bir işlem için iki yönlü toplam maliyet oranını döner.

    Slipaj (bps) + komisyon (%0.1) her yönde, toplam gidiş-dönüş:
      round_trip_cost = 2 × (slipaj_oranı + 0.001)

    Slipaj katmanları:
      BIST30 (is_bist30=True) veya liquidity_score='yüksek' → 10 bps = 0.001
      liquidity_score='orta' veya None → 20 bps = 0.002
      liquidity_score='düşük' → 40 bps = 0.004
    """
    if is_bist30 or liquidity_score == "yüksek":
        slippage = 0.0010
    elif liquidity_score == "düşük":
        slippage = 0.0040
    else:  # "orta" veya None → varsayılan orta
        slippage = 0.0020
    return round(2 * (slippage + 0.001), 6)


class SignalTrackingService:
    """Records decision snapshots and later scores their outcomes."""

    async def snapshot_top_signals(
        self,
        db: AsyncSession,
        limit: int = 40,
        portfolio_value: float = 100_000.0,
        risk_per_trade_pct: float = 1.0,
        decision_date: Optional[date] = None,
    ) -> dict[str, Any]:
        decision_date = decision_date or datetime.now(MARKET_TZ).date()
        stocks = await self._load_candidate_stocks(db)
        prices_by_stock = await self._load_prices_by_stock(db, [s.id for s in stocks])
        benchmark_close = await self._benchmark_close_on_or_before(db, decision_date)

        decisions = []
        for stock in stocks:
            try:
                decisions.append(
                    investment_decision_engine.build_decision(
                        DecisionInput(
                            stock=stock,
                            prices=prices_by_stock.get(stock.id, []),
                            portfolio_value=portfolio_value,
                            risk_per_trade_pct=risk_per_trade_pct,
                        )
                    )
                )
            except ValueError:
                continue

        ranked = investment_decision_engine.rank_decisions(decisions)[:limit]
        upserted = 0
        for decision in ranked:
            stock = next((s for s in stocks if s.symbol == decision["symbol"]), None)
            if stock is None:
                continue
            existing = await self._find_snapshot(db, stock.id, decision_date)
            snapshot = existing or SignalDecisionSnapshot(stock_id=stock.id, symbol=stock.symbol, decision_date=decision_date)
            snapshot.sector = stock.sector
            self._apply_decision(snapshot, decision, benchmark_close)
            db.add(snapshot)
            upserted += 1

        await db.commit()
        return {
            "decision_date": decision_date.isoformat(),
            "created_or_updated": upserted,
            "benchmark_symbol": BENCHMARK_SYMBOL,
            "benchmark_close": benchmark_close,
        }

    async def evaluate_outcomes(self, db: AsyncSession, as_of: Optional[date] = None) -> dict[str, Any]:
        as_of = as_of or datetime.now(MARKET_TZ).date()
        result = await db.execute(
            select(SignalDecisionSnapshot)
            .where(SignalDecisionSnapshot.decision_date <= as_of - timedelta(days=7))
            .order_by(SignalDecisionSnapshot.decision_date.asc(), SignalDecisionSnapshot.id.asc())
            .limit(500)
        )
        snapshots = list(result.scalars().all())

        evaluated_1w = 0
        evaluated_1m = 0
        for snapshot in snapshots:
            if snapshot.actual_return_1w_pct is None:
                evaluated_1w += await self._evaluate_horizon(db, snapshot, days=7)
            if snapshot.decision_date <= as_of - timedelta(days=30) and snapshot.actual_return_1m_pct is None:
                evaluated_1m += await self._evaluate_horizon(db, snapshot, days=30)

        await db.commit()
        return {"evaluated_1w": evaluated_1w, "evaluated_1m": evaluated_1m, "as_of": as_of.isoformat()}

    async def list_outcomes(
        self,
        db: AsyncSession,
        limit: int = 50,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        horizon: str = "1w",
    ) -> dict[str, Any]:
        query = select(SignalDecisionSnapshot)
        if action:
            query = query.where(SignalDecisionSnapshot.action == action)
        if outcome:
            outcome_col = SignalDecisionSnapshot.outcome_1m if horizon == "1m" else SignalDecisionSnapshot.outcome_1w
            query = query.where(outcome_col == outcome)
        query = query.order_by(SignalDecisionSnapshot.decision_date.desc(), SignalDecisionSnapshot.confidence.desc()).limit(limit)

        result = await db.execute(query)
        rows = list(result.scalars().all())
        return {
            "items": [self._serialize(row) for row in rows],
            "count": len(rows),
            "summary": self._summary(rows, horizon),
        }

    async def calibration_report(
        self,
        db: AsyncSession,
        horizon: str = "1w",
        min_count: int = 1,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(SignalDecisionSnapshot)
            .where(
                SignalDecisionSnapshot.actual_return_1m_pct.isnot(None)
                if horizon == "1m"
                else SignalDecisionSnapshot.actual_return_1w_pct.isnot(None)
            )
            .order_by(SignalDecisionSnapshot.decision_date.desc())
            .limit(1000)
        )
        rows = list(result.scalars().all())
        return {
            "horizon": horizon,
            "sample_size": len(rows),
            "overall": self._calibration_bucket("overall", rows, horizon),
            "by_action": self._bucket_rows(rows, horizon, "action", min_count),
            "by_risk_level": self._bucket_rows(rows, horizon, "risk_level", min_count),
            "by_sector": self._bucket_rows(rows, horizon, "sector", min_count),
            "recommendations": self._calibration_recommendations(rows, horizon),
            "suggested_policy": self.suggest_policy(rows, horizon),
        }

    def suggest_policy(self, rows: list[SignalDecisionSnapshot], horizon: str = "1w") -> dict[str, Any]:
        measured_count = len(rows)
        policy = DecisionPolicy()
        reasons = []
        if measured_count < 20:
            return {
                "mode": "observation",
                "measured_count": measured_count,
                "min_buy_confidence": policy.min_buy_confidence,
                "min_buy_risk_reward": policy.min_buy_risk_reward,
                "block_high_risk_buys": policy.block_high_risk_buys,
                "reasons": ["sample_size_below_20"],
            }

        buy_rows = [row for row in rows if row.action in {"strong_buy", "buy"}]
        high_risk_rows = [row for row in rows if row.risk_level == "high"]
        buy_bucket = self._calibration_bucket("buy_actions", buy_rows, horizon)
        high_risk_bucket = self._calibration_bucket("high", high_risk_rows, horizon)

        min_buy_confidence = 0
        min_buy_risk_reward = 0.0
        block_high_risk_buys = False

        if buy_rows and buy_bucket["success_rate"] < 45:
            min_buy_confidence = 80
            min_buy_risk_reward = 1.8
            reasons.append("buy_success_rate_below_45")
        elif buy_rows and buy_bucket["avg_excess_return_pct"] is not None and buy_bucket["avg_excess_return_pct"] < 0:
            min_buy_confidence = 75
            min_buy_risk_reward = 1.6
            reasons.append("buy_excess_return_negative")

        if high_risk_rows and high_risk_bucket["success_rate"] < 45:
            block_high_risk_buys = True
            reasons.append("high_risk_success_rate_below_45")

        return {
            "mode": "enforced" if reasons else "observation",
            "measured_count": measured_count,
            "min_buy_confidence": min_buy_confidence,
            "min_buy_risk_reward": min_buy_risk_reward,
            "block_high_risk_buys": block_high_risk_buys,
            "reasons": reasons or ["no_policy_change"],
        }

    def policy_from_report(self, report: dict[str, Any]) -> DecisionPolicy:
        suggested = report.get("suggested_policy") or {}
        return DecisionPolicy(
            mode=suggested.get("mode", "observation"),
            min_buy_confidence=int(suggested.get("min_buy_confidence") or 0),
            min_buy_risk_reward=float(suggested.get("min_buy_risk_reward") or 0.0),
            block_high_risk_buys=bool(suggested.get("block_high_risk_buys")),
        )

    async def _fetch_regime_map(self, db: AsyncSession, dates: list) -> dict:
        """date → regime string eşlemesi döner. Eşleşme yoksa 'Bilinmiyor' kullanılır."""
        if not dates:
            return {}
        try:
            result = await db.execute(
                select(MarketRegime).where(MarketRegime.date.in_(dates))
            )
            return {row.date: row.regime for row in result.scalars().all()}
        except Exception:
            return {}

    async def _load_candidate_stocks(self, db: AsyncSession) -> list[Stock]:
        result = await db.execute(
            select(Stock)
            .where(Stock.is_active, Stock.current_price.isnot(None))
            .order_by(Stock.overall_score.desc().nullslast())
            .limit(200)
        )
        return list(result.scalars().all())

    async def _load_prices_by_stock(self, db: AsyncSession, stock_ids: list[int]) -> dict[int, list[PriceHistory]]:
        if not stock_ids:
            return {}
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.stock_id.in_(stock_ids))
            .order_by(PriceHistory.stock_id.asc(), PriceHistory.date.desc())
        )
        prices_by_stock: dict[int, list[PriceHistory]] = {stock_id: [] for stock_id in stock_ids}
        for price in result.scalars().all():
            bucket = prices_by_stock.get(price.stock_id)
            if bucket is not None and len(bucket) < 260:
                bucket.append(price)
        return prices_by_stock

    async def _find_snapshot(self, db: AsyncSession, stock_id: int, decision_date: date) -> Optional[SignalDecisionSnapshot]:
        result = await db.execute(
            select(SignalDecisionSnapshot).where(
                SignalDecisionSnapshot.stock_id == stock_id,
                SignalDecisionSnapshot.decision_date == decision_date,
            )
        )
        return result.scalar_one_or_none()

    async def _benchmark_close_on_or_before(self, db: AsyncSession, target_date: date) -> Optional[float]:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == BENCHMARK_SYMBOL, CommodityPrice.date <= target_date)
            .order_by(CommodityPrice.date.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return float(row.close) if row and row.close is not None else None

    async def _benchmark_close_on_or_after(self, db: AsyncSession, target_date: date) -> Optional[float]:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == BENCHMARK_SYMBOL, CommodityPrice.date >= target_date)
            .order_by(CommodityPrice.date.asc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return float(row.close) if row and row.close is not None else None

    async def _stock_close_on_or_after(self, db: AsyncSession, stock_id: int, target_date: date) -> Optional[float]:
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.stock_id == stock_id, PriceHistory.date >= target_date)
            .order_by(PriceHistory.date.asc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return float(row.close) if row and row.close is not None else None

    async def _evaluate_horizon(self, db: AsyncSession, snapshot: SignalDecisionSnapshot, days: int) -> int:
        target_date = snapshot.decision_date + timedelta(days=days)
        actual_close = await self._stock_close_on_or_after(db, snapshot.stock_id, target_date)
        if actual_close is None or snapshot.current_price <= 0:
            return 0

        actual_return = self._pct_change(snapshot.current_price, actual_close)
        benchmark_return = None
        benchmark_close = await self._benchmark_close_on_or_after(db, target_date)
        if snapshot.benchmark_close and benchmark_close:
            benchmark_return = self._pct_change(snapshot.benchmark_close, benchmark_close)
        excess_return = round(actual_return - benchmark_return, 2) if benchmark_return is not None else None
        outcome = self.classify_outcome(snapshot.action, actual_return, excess_return)

        if days == 7:
            snapshot.actual_close_1w = actual_close
            snapshot.actual_return_1w_pct = actual_return
            snapshot.benchmark_return_1w_pct = benchmark_return
            snapshot.excess_return_1w_pct = excess_return
            snapshot.outcome_1w = outcome
        else:
            snapshot.actual_close_1m = actual_close
            snapshot.actual_return_1m_pct = actual_return
            snapshot.benchmark_return_1m_pct = benchmark_return
            snapshot.excess_return_1m_pct = excess_return
            snapshot.outcome_1m = outcome
        snapshot.evaluated_at = datetime.now(timezone.utc)
        return 1

    def classify_outcome(self, action: str, actual_return: float, excess_return: Optional[float]) -> str:
        excess = excess_return if excess_return is not None else actual_return
        if action in {"strong_buy", "buy"}:
            if actual_return > 0 and excess > 0:
                return "success"
            if actual_return > -2 and excess >= -1:
                return "partial"
            return "failure"
        if action in {"reduce", "exit"}:
            if actual_return <= 0 or excess <= 0:
                return "success"
            if actual_return <= 2:
                return "partial"
            return "failure"
        if abs(actual_return) <= 2:
            return "success"
        return "partial" if abs(actual_return) <= 5 else "failure"

    def _bucket_rows(
        self,
        rows: list[SignalDecisionSnapshot],
        horizon: str,
        field: str,
        min_count: int,
    ) -> list[dict[str, Any]]:
        buckets: dict[str, list[SignalDecisionSnapshot]] = {}
        for row in rows:
            key = getattr(row, field, None) or "unknown"
            buckets.setdefault(str(key), []).append(row)
        bucket_metrics = [
            self._calibration_bucket(key, bucket_rows, horizon)
            for key, bucket_rows in buckets.items()
            if len(bucket_rows) >= min_count
        ]
        return sorted(
            bucket_metrics,
            key=lambda item: (item["success_rate"], item["avg_excess_return_pct"], item["count"]),
            reverse=True,
        )

    def _calibration_bucket(
        self,
        key: str,
        rows: list[SignalDecisionSnapshot],
        horizon: str,
    ) -> dict[str, Any]:
        outcome_attr = "outcome_1m" if horizon == "1m" else "outcome_1w"
        return_attr = "actual_return_1m_pct" if horizon == "1m" else "actual_return_1w_pct"
        excess_attr = "excess_return_1m_pct" if horizon == "1m" else "excess_return_1w_pct"

        count = len(rows)
        successes = sum(1 for row in rows if getattr(row, outcome_attr) == "success")
        partials = sum(1 for row in rows if getattr(row, outcome_attr) == "partial")
        failures = sum(1 for row in rows if getattr(row, outcome_attr) == "failure")
        returns = [getattr(row, return_attr) for row in rows if getattr(row, return_attr) is not None]
        excess_returns = [getattr(row, excess_attr) for row in rows if getattr(row, excess_attr) is not None]

        return {
            "key": key,
            "count": count,
            "success": successes,
            "partial": partials,
            "failure": failures,
            "success_rate": round(successes / count * 100, 1) if count else 0.0,
            "non_failure_rate": round((successes + partials) / count * 100, 1) if count else 0.0,
            "avg_return_pct": round(sum(returns) / len(returns), 2) if returns else None,
            "avg_excess_return_pct": round(sum(excess_returns) / len(excess_returns), 2) if excess_returns else None,
        }

    def _calibration_recommendations(self, rows: list[SignalDecisionSnapshot], horizon: str) -> list[str]:
        if len(rows) < 20:
            return ["Örneklem henüz düşük; eşik değiştirmek için en az 20 ölçülmüş sinyal beklenmeli."]
        action_buckets = self._bucket_rows(rows, horizon, "action", min_count=3)
        risk_buckets = self._bucket_rows(rows, horizon, "risk_level", min_count=3)
        recommendations = []
        weak_actions = [b for b in action_buckets if b["success_rate"] < 40 and b["avg_excess_return_pct"] is not None and b["avg_excess_return_pct"] < 0]
        strong_actions = [b for b in action_buckets if b["success_rate"] >= 60 and b["avg_excess_return_pct"] is not None and b["avg_excess_return_pct"] > 0]
        high_risk = next((b for b in risk_buckets if b["key"] == "high"), None)
        if strong_actions:
            recommendations.append(f"En iyi çalışan aksiyon kümesi: {strong_actions[0]['key']} ({strong_actions[0]['success_rate']}% başarı).")
        if weak_actions:
            recommendations.append(f"Zayıf aksiyon kümesi sıkılaştırılmalı: {weak_actions[0]['key']} ({weak_actions[0]['avg_excess_return_pct']}% BIST farkı).")
        if high_risk and high_risk["success_rate"] < 45:
            recommendations.append("Yüksek risk sinyallerinde pozisyon limiti veya minimum risk/ödül eşiği artırılmalı.")
        return recommendations or ["Mevcut ölçümlerde belirgin bir eşik değişikliği sinyali yok."]

    def _apply_decision(
        self,
        snapshot: SignalDecisionSnapshot,
        decision: dict[str, Any],
        benchmark_close: Optional[float],
    ) -> None:
        snapshot.action = decision["action"]
        snapshot.action_label = decision["action_label"]
        snapshot.confidence = decision["confidence"]
        snapshot.risk_level = decision["risk_level"]
        snapshot.time_horizon = decision["time_horizon"]
        snapshot.current_price = decision["current_price"]
        snapshot.entry_low = decision["entry_zone"]["low"]
        snapshot.entry_high = decision["entry_zone"]["high"]
        snapshot.stop_loss = decision["stop_loss"]
        snapshot.target_price = decision["target_price"]
        snapshot.risk_reward = decision["risk_reward"]
        snapshot.suggested_shares = decision["position_size"]["shares"]
        snapshot.estimated_exposure = decision["position_size"]["estimated_exposure"]
        snapshot.estimated_exposure_pct = decision["position_size"]["estimated_exposure_pct"]
        snapshot.overall_score = decision["signals"].get("overall_score")
        snapshot.technical_score = decision["signals"].get("technical_score")
        snapshot.fundamental_score = decision["signals"].get("fundamental_score")
        snapshot.sentiment_score = decision["signals"].get("sentiment_score")
        snapshot.recommendation = decision["signals"].get("recommendation")
        snapshot.trend = decision["signals"].get("trend")
        snapshot.drawdown_pct = decision["signals"].get("drawdown_pct")
        snapshot.annualized_volatility_pct = decision["signals"].get("annualized_volatility_pct")
        snapshot.benchmark_symbol = BENCHMARK_SYMBOL
        snapshot.benchmark_close = benchmark_close
        snapshot.thesis_json = decision.get("thesis")
        snapshot.invalidation = decision.get("invalidation")
        snapshot.watch_items_json = decision.get("watch_items")
        snapshot.generated_at = datetime.now(timezone.utc)

    def _pct_change(self, start: float, end: float) -> float:
        return round(((end / start) - 1.0) * 100.0, 2)

    def _summary(self, rows: list[SignalDecisionSnapshot], horizon: str) -> dict[str, Any]:
        outcome_attr = "outcome_1m" if horizon == "1m" else "outcome_1w"
        return {
            "success": sum(1 for row in rows if getattr(row, outcome_attr) == "success"),
            "partial": sum(1 for row in rows if getattr(row, outcome_attr) == "partial"),
            "failure": sum(1 for row in rows if getattr(row, outcome_attr) == "failure"),
            "pending": sum(1 for row in rows if getattr(row, outcome_attr) is None),
        }

    def _serialize(self, row: SignalDecisionSnapshot) -> dict[str, Any]:
        return {
            "id": row.id,
            "symbol": row.symbol,
            "sector": row.sector,
            "decision_date": row.decision_date.isoformat(),
            "action": row.action,
            "action_label": row.action_label,
            "confidence": row.confidence,
            "risk_level": row.risk_level,
            "current_price": row.current_price,
            "stop_loss": row.stop_loss,
            "target_price": row.target_price,
            "risk_reward": row.risk_reward,
            "suggested_shares": row.suggested_shares,
            "estimated_exposure_pct": row.estimated_exposure_pct,
            "overall_score": row.overall_score,
            "trend": row.trend,
            "actual_return_1w_pct": row.actual_return_1w_pct,
            "benchmark_return_1w_pct": row.benchmark_return_1w_pct,
            "excess_return_1w_pct": row.excess_return_1w_pct,
            "outcome_1w": row.outcome_1w,
            "actual_return_1m_pct": row.actual_return_1m_pct,
            "benchmark_return_1m_pct": row.benchmark_return_1m_pct,
            "excess_return_1m_pct": row.excess_return_1m_pct,
            "outcome_1m": row.outcome_1m,
            "generated_at": row.generated_at.isoformat() if row.generated_at else None,
            "evaluated_at": row.evaluated_at.isoformat() if row.evaluated_at else None,
        }


signal_tracking_service = SignalTrackingService()
