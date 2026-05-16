"""Portfolio risk guard and actionable alert generation."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsItem
from app.models.portfolio_v2 import PortfolioPosition
from app.models.price import CommodityPrice, PriceHistory
from app.models.signal import SignalDecisionSnapshot
from app.models.stock import Stock


class RiskGuardService:
    """Computes risk controls and alerts from the current portfolio state."""

    async def portfolio_risk(
        self,
        db: AsyncSession,
        portfolio_value: float = 100_000.0,
    ) -> dict[str, Any]:
        positions = await self._active_positions(db)
        stocks = await self._stocks_by_symbol(db, [position.symbol for position in positions])
        latest_prices = await self._latest_prices(db, list(stocks.values()))
        market = await self._market_regime(db)

        position_items = []
        sector_exposure: dict[str, float] = defaultdict(float)
        total_exposure = 0.0
        risk_amount = 0.0

        for position in positions:
            stock = stocks.get(position.symbol)
            latest = latest_prices.get(position.symbol)
            current_price = latest or position.entry_price
            exposure = current_price * position.quantity
            total_exposure += exposure
            sector = stock.sector if stock and stock.sector else "Bilinmeyen"
            sector_exposure[sector] += exposure
            stop_gap_pct = None
            at_risk = False
            if position.stop_loss:
                stop_gap_pct = round(((current_price / position.stop_loss) - 1.0) * 100, 2)
                at_risk = stop_gap_pct <= 3
                risk_amount += max(0.0, (current_price - position.stop_loss) * position.quantity)
            target_gap_pct = None
            if position.target_price:
                target_gap_pct = round(((position.target_price / current_price) - 1.0) * 100, 2)

            position_items.append(
                {
                    "symbol": position.symbol,
                    "sector": sector,
                    "entry_price": position.entry_price,
                    "current_price": round(current_price, 2),
                    "quantity": position.quantity,
                    "exposure": round(exposure, 2),
                    "exposure_pct": round(exposure / portfolio_value * 100, 2) if portfolio_value > 0 else 0.0,
                    "stop_loss": position.stop_loss,
                    "target_price": position.target_price,
                    "stop_gap_pct": stop_gap_pct,
                    "target_gap_pct": target_gap_pct,
                    "at_risk": at_risk,
                    "score": stock.overall_score if stock else None,
                }
            )

        sector_rows = [
            {
                "sector": sector,
                "exposure": round(value, 2),
                "exposure_pct": round(value / portfolio_value * 100, 2) if portfolio_value > 0 else 0.0,
                "limit_pct": 25.0,
                "status": "over_limit" if portfolio_value > 0 and value / portfolio_value * 100 > 25 else "ok",
            }
            for sector, value in sorted(sector_exposure.items(), key=lambda item: item[1], reverse=True)
        ]

        invested_pct = round(total_exposure / portfolio_value * 100, 2) if portfolio_value > 0 else 0.0
        cash_pct = max(0.0, round(100.0 - invested_pct, 2))
        recommended_cash = self._recommended_cash_pct(market)
        risk_score = self._risk_score(position_items, sector_rows, invested_pct, market)

        return {
            "portfolio_value": portfolio_value,
            "invested_pct": invested_pct,
            "cash_pct": cash_pct,
            "recommended_cash_pct": recommended_cash,
            "cash_action": self._cash_action(cash_pct, recommended_cash),
            "risk_score": risk_score,
            "risk_level": self._risk_level(risk_score),
            "estimated_capital_at_risk": round(risk_amount, 2),
            "market_regime": market,
            "sector_exposure": sector_rows,
            "positions": position_items,
            "rules": {
                "max_single_position_pct": 12.0,
                "max_sector_exposure_pct": 25.0,
                "default_risk_per_trade_pct": 1.0,
                "stop_alert_distance_pct": 3.0,
            },
        }

    async def alerts(self, db: AsyncSession, portfolio_value: float = 100_000.0) -> dict[str, Any]:
        risk = await self.portfolio_risk(db, portfolio_value=portfolio_value)
        alerts: list[dict[str, Any]] = []
        alerts.extend(self._position_alerts(risk))
        alerts.extend(self._sector_alerts(risk))
        alerts.extend(await self._score_deterioration_alerts(db))
        alerts.extend(await self._kap_alerts(db))
        alerts.extend(await self._new_signal_alerts(db))
        alerts.extend(self._cash_alerts(risk))

        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts = sorted(alerts, key=lambda item: (severity_order.get(item["severity"], 9), item["symbol"] or ""))
        return {
            "status": "critical" if any(a["severity"] == "critical" for a in alerts) else "warning" if any(a["severity"] == "warning" for a in alerts) else "ok",
            "summary": {
                "critical": sum(1 for item in alerts if item["severity"] == "critical"),
                "warning": sum(1 for item in alerts if item["severity"] == "warning"),
                "info": sum(1 for item in alerts if item["severity"] == "info"),
                "total": len(alerts),
            },
            "alerts": alerts[:80],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _active_positions(self, db: AsyncSession) -> list[PortfolioPosition]:
        result = await db.execute(select(PortfolioPosition).where(PortfolioPosition.is_active == True))  # noqa: E712
        return list(result.scalars().all())

    async def _stocks_by_symbol(self, db: AsyncSession, symbols: list[str]) -> dict[str, Stock]:
        if not symbols:
            return {}
        result = await db.execute(select(Stock).where(Stock.symbol.in_(symbols)))
        return {stock.symbol: stock for stock in result.scalars().all()}

    async def _latest_prices(self, db: AsyncSession, stocks: list[Stock]) -> dict[str, float]:
        output: dict[str, float] = {}
        for stock in stocks:
            result = await db.execute(
                select(PriceHistory)
                .where(PriceHistory.stock_id == stock.id)
                .order_by(PriceHistory.date.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row and row.close:
                output[stock.symbol] = float(row.close)
        return output

    async def _market_regime(self, db: AsyncSession) -> dict[str, Any]:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == "XU100.IS")
            .order_by(CommodityPrice.date.desc())
            .limit(220)
        )
        rows = list(reversed(result.scalars().all()))
        closes = [float(row.close) for row in rows if row.close]
        if len(closes) < 50:
            return {"label": "unknown", "score": 50, "detail": "BIST100 trend verisi yetersiz."}
        last = closes[-1]
        sma50 = sum(closes[-50:]) / 50
        sma200 = sum(closes[-200:]) / min(len(closes), 200)
        drawdown = ((last / max(closes[-120:])) - 1.0) * 100
        score = 50
        if last > sma50:
            score += 15
        else:
            score -= 15
        if last > sma200:
            score += 15
        else:
            score -= 15
        if drawdown <= -15:
            score -= 15
        elif drawdown >= -5:
            score += 5
        label = "risk_on" if score >= 65 else "risk_off" if score <= 35 else "neutral"
        return {
            "label": label,
            "score": max(0, min(100, score)),
            "last_close": round(last, 2),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "drawdown_pct": round(drawdown, 2),
        }

    async def _score_deterioration_alerts(self, db: AsyncSession) -> list[dict[str, Any]]:
        result = await db.execute(
            select(SignalDecisionSnapshot)
            .order_by(SignalDecisionSnapshot.symbol.asc(), SignalDecisionSnapshot.decision_date.desc())
            .limit(400)
        )
        by_symbol: dict[str, list[SignalDecisionSnapshot]] = defaultdict(list)
        for row in result.scalars().all():
            by_symbol[row.symbol].append(row)

        alerts = []
        for symbol, rows in by_symbol.items():
            if len(rows) < 2:
                continue
            latest, previous = rows[0], rows[1]
            score_drop = (previous.overall_score or 0) - (latest.overall_score or 0)
            if score_drop >= 8 or latest.action in {"reduce", "exit"} and previous.action in {"strong_buy", "buy", "watch"}:
                alerts.append(
                    self._alert(
                        "model_score_deteriorated",
                        "warning",
                        symbol,
                        f"Model skoru {score_drop:.1f} puan zayifladi veya aksiyon dusuruldu.",
                        "Pozisyon varsa stop ve pozisyon buyuklugu yeniden kontrol edilmeli.",
                    )
                )
        return alerts

    async def _kap_alerts(self, db: AsyncSession) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
        result = await db.execute(
            select(NewsItem, Stock.symbol)
            .join(Stock, NewsItem.stock_id == Stock.id, isouter=True)
            .where(NewsItem.source == "KAP", NewsItem.published_at >= cutoff)
            .order_by(NewsItem.published_at.desc())
            .limit(30)
        )
        alerts = []
        for item, symbol in result.fetchall():
            alerts.append(
                self._alert(
                    "kap_news",
                    "info" if (item.sentiment_score or 0) >= -0.2 else "warning",
                    symbol or "",
                    item.title,
                    "KAP etkisi sinyal gerekcesi ve risk raporunda incelenmeli.",
                    metadata={"url": item.url, "published_at": item.published_at.isoformat() if item.published_at else None},
                )
            )
        return alerts

    async def _new_signal_alerts(self, db: AsyncSession) -> list[dict[str, Any]]:
        result = await db.execute(
            select(SignalDecisionSnapshot)
            .where(SignalDecisionSnapshot.action.in_(["strong_buy", "buy"]))
            .order_by(SignalDecisionSnapshot.decision_date.desc(), SignalDecisionSnapshot.confidence.desc())
            .limit(10)
        )
        alerts = []
        for row in result.scalars().all():
            if row.confidence >= 75 and (row.risk_reward or 0) >= 1.5:
                alerts.append(
                    self._alert(
                        "new_strong_signal",
                        "info",
                        row.symbol,
                        f"{row.action_label} sinyali: guven {row.confidence}, R/O {row.risk_reward}.",
                        "Backtest ve portfoy sektor yogunlugu uygun degilse islem acma.",
                    )
                )
        return alerts

    def _position_alerts(self, risk: dict[str, Any]) -> list[dict[str, Any]]:
        alerts = []
        for pos in risk["positions"]:
            if pos["stop_gap_pct"] is not None and pos["stop_gap_pct"] <= 0:
                alerts.append(self._alert("stop_breached", "critical", pos["symbol"], "Fiyat stop seviyesinin altinda veya uzerinde kapandi.", "Pozisyon kapatma/azaltma plani hemen kontrol edilmeli."))
            elif pos["stop_gap_pct"] is not None and pos["stop_gap_pct"] <= 3:
                alerts.append(self._alert("stop_near", "warning", pos["symbol"], f"Stop mesafesi %{pos['stop_gap_pct']:.2f}.", "Stop emri ve pozisyon buyuklugu guncellenmeli."))
            if pos["target_gap_pct"] is not None and pos["target_gap_pct"] <= 3:
                alerts.append(self._alert("target_near", "info", pos["symbol"], f"Hedefe kalan mesafe %{pos['target_gap_pct']:.2f}.", "Kar alma veya trailing stop planlanmali."))
        return alerts

    def _sector_alerts(self, risk: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            self._alert("sector_overload", "warning", None, f"{row['sector']} sektor maruziyeti %{row['exposure_pct']:.2f}.", "Yeni islemlerde bu sektore ek alimi durdur.")
            for row in risk["sector_exposure"]
            if row["status"] == "over_limit"
        ]

    def _cash_alerts(self, risk: dict[str, Any]) -> list[dict[str, Any]]:
        action = risk["cash_action"]
        if action["status"] == "ok":
            return []
        severity = "warning" if action["status"] == "raise_cash" else "info"
        return [self._alert("cash_ratio", severity, None, action["detail"], action["remediation"])]

    def _recommended_cash_pct(self, market: dict[str, Any]) -> float:
        label = market.get("label")
        if label == "risk_off":
            return 35.0
        if label == "neutral":
            return 20.0
        return 10.0

    def _cash_action(self, current_cash_pct: float, recommended_cash_pct: float) -> dict[str, str]:
        if current_cash_pct + 5 < recommended_cash_pct:
            return {
                "status": "raise_cash",
                "detail": f"Nakit orani %{current_cash_pct:.1f}; onerilen seviye %{recommended_cash_pct:.1f}.",
                "remediation": "Zayif sinyallerde pozisyon azaltarak nakit tamponu yukselt.",
            }
        if current_cash_pct > recommended_cash_pct + 20:
            return {
                "status": "deploy_selectively",
                "detail": f"Nakit orani %{current_cash_pct:.1f}; piyasa rejimine gore fazla temkinli olabilir.",
                "remediation": "Sadece backtest'i gecen ve sektor limiti uygun AL sinyallerini degerlendir.",
            }
        return {"status": "ok", "detail": "Nakit orani rejime uygun.", "remediation": "Aksiyon gerekmiyor."}

    def _risk_score(self, positions: list[dict[str, Any]], sectors: list[dict[str, Any]], invested_pct: float, market: dict[str, Any]) -> int:
        score = 20
        score += sum(18 for pos in positions if pos["at_risk"])
        score += sum(12 for row in sectors if row["status"] == "over_limit")
        if invested_pct > 90:
            score += 15
        elif invested_pct > 75:
            score += 8
        if market.get("label") == "risk_off":
            score += 20
        elif market.get("label") == "neutral":
            score += 8
        return max(0, min(100, score))

    def _risk_level(self, score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    def _alert(
        self,
        kind: str,
        severity: str,
        symbol: Optional[str],
        detail: str,
        remediation: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "severity": severity,
            "symbol": symbol,
            "detail": detail,
            "remediation": remediation,
            "metadata": metadata or {},
        }


risk_guard_service = RiskGuardService()
