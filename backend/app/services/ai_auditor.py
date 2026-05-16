"""AI auditor role for investment decisions.

The deterministic audit is always returned. OpenAI is used only to explain the
same evidence in a stricter "risk committee" voice when available.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsItem
from app.models.price import PriceHistory
from app.models.stock import Stock
from app.services.gemini_service import FALLBACK_MESSAGE, gemini_service
from app.services.investment_decision import DecisionInput, investment_decision_engine


AUDITOR_SYSTEM_PROMPT = """Sen bir yatirim komitesi risk denetcisisin.
Gorevin hisseyi pazarlamak degil; sinyalin nerede kirilabilecegini bulmak.
Turkce yaz. Net, sert ve kanita bagli ol. Yatirim tavsiyesi uyarisi ekleme.
Mutlaka su basliklari kullan: Karar, Gerekce, Celiskiler, KAP/Haber Etkisi, Ters Senaryo, Denetci Notu."""


class AIAuditorService:
    """Builds contradiction and downside-risk reports for a stock signal."""

    async def audit_stock(
        self,
        db: AsyncSession,
        symbol: str,
        portfolio_value: float = 100_000.0,
        risk_per_trade_pct: float = 1.0,
        include_llm: bool = False,
    ) -> dict[str, Any]:
        stock = await self._stock(db, symbol)
        prices = await self._prices(db, stock.id)
        news = await self._recent_news(db, stock.id)
        decision = investment_decision_engine.build_decision(
            DecisionInput(
                stock=stock,
                prices=prices,
                portfolio_value=portfolio_value,
                risk_per_trade_pct=risk_per_trade_pct,
            )
        )
        deterministic = self._deterministic_audit(stock, decision, news)
        narrative = (
            await self._llm_narrative(stock, decision, deterministic, news)
            if include_llm
            else "Deterministik denetim tamamlandı. OpenAI anlatımı bu hızlı kontrolde kapalı."
        )
        return {
            "symbol": stock.symbol,
            "decision": decision,
            "audit": deterministic,
            "narrative": narrative,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _stock(self, db: AsyncSession, symbol: str) -> Stock:
        result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper().removesuffix(".IS")))
        stock = result.scalar_one_or_none()
        if stock is None:
            raise ValueError(f"Hisse bulunamadi: {symbol}")
        return stock

    async def _prices(self, db: AsyncSession, stock_id: int) -> list[PriceHistory]:
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.stock_id == stock_id)
            .order_by(PriceHistory.date.desc())
            .limit(260)
        )
        return list(reversed(result.scalars().all()))

    async def _recent_news(self, db: AsyncSession, stock_id: int) -> list[NewsItem]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        result = await db.execute(
            select(NewsItem)
            .where(NewsItem.stock_id == stock_id, NewsItem.published_at >= cutoff)
            .order_by(NewsItem.published_at.desc())
            .limit(12)
        )
        return list(result.scalars().all())

    def _deterministic_audit(self, stock: Stock, decision: dict[str, Any], news: list[NewsItem]) -> dict[str, Any]:
        contradictions = []
        risks = []
        positives = []

        technical = stock.technical_score or 0
        fundamental = stock.fundamental_score or 0
        sentiment = stock.sentiment_score or 0
        risk_reward = decision.get("risk_reward") or 0
        risk_level = decision.get("risk_level")
        trend = decision.get("signals", {}).get("trend")
        drawdown = decision.get("signals", {}).get("drawdown_pct")

        if technical >= 65 and fundamental < 50:
            contradictions.append("Teknik yapi guclu gorunuyor ama temel skor zayif.")
        if fundamental >= 65 and technical < 50:
            contradictions.append("Bilanco/temel kalite iyi ama fiyat davranisi bunu henuz onaylamiyor.")
        if sentiment < 45 and decision["action"] in {"strong_buy", "buy"}:
            contradictions.append("AL sinyali haber/KAP duyarliligi ile tam desteklenmiyor.")
        if risk_reward < 1.5 and decision["action"] in {"strong_buy", "buy"}:
            contradictions.append("AL sinyaline ragmen risk/odul orani dusuk.")

        if risk_level == "high":
            risks.append("Volatilite veya drawdown nedeniyle pozisyon boyutu agresif olmamali.")
        if trend in {"bearish", "weak"}:
            risks.append("Trend zayif; stop calismadan pozisyonda israr etmek zarari buyutebilir.")
        if drawdown is not None and drawdown <= -20:
            risks.append(f"Hisse son zirvesinden %{abs(drawdown):.1f} uzakta; tepki alimi tuzagi riski var.")
        if not news:
            risks.append("Son 14 gunde karar kalitesini destekleyecek hisse ozel haber/KAP baglami yok.")

        negative_news = [item for item in news if (item.sentiment_score or 0) < -0.2]
        if negative_news:
            risks.append(f"Son haber akisi icinde {len(negative_news)} negatif/uyari niteliginde madde var.")

        if technical >= 60:
            positives.append("Teknik skor esik ustunde.")
        if fundamental >= 60:
            positives.append("Temel skor esik ustunde.")
        if risk_reward >= 2:
            positives.append("Risk/odul orani guclu.")

        severity = "high" if len(risks) >= 3 or len(contradictions) >= 2 else "medium" if risks or contradictions else "low"
        veto = decision["action"] in {"strong_buy", "buy"} and severity == "high"

        return {
            "auditor_action": "veto" if veto else "approve_with_conditions" if severity != "low" else "approve",
            "severity": severity,
            "contradictions": contradictions,
            "risk_report": risks,
            "positive_evidence": positives,
            "kap_news_summary": [
                {
                    "title": item.title,
                    "source": item.source,
                    "sentiment_score": item.sentiment_score,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                }
                for item in news[:5]
            ],
            "failure_scenario": self._failure_scenario(decision, risks),
        }

    def _failure_scenario(self, decision: dict[str, Any], risks: list[str]) -> str:
        stop = decision.get("stop_loss")
        if risks:
            return f"Fiyat {stop} TL altinda kapanir veya model skoru bozulursa islem tezi gecersizlesir; ana risk: {risks[0]}"
        return f"Ana ters senaryo fiyat {stop} TL altinda kapanis yapmasi ve beklenen hedefe gitmeden momentum kaybetmesi."

    async def _llm_narrative(
        self,
        stock: Stock,
        decision: dict[str, Any],
        audit: dict[str, Any],
        news: list[NewsItem],
    ) -> str:
        prompt = {
            "stock": {"symbol": stock.symbol, "name": stock.name, "sector": stock.sector},
            "decision": decision,
            "audit": audit,
            "recent_news": [
                {
                    "title": item.title,
                    "source": item.source,
                    "sentiment_score": item.sentiment_score,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                }
                for item in news[:8]
            ],
        }
        text = await gemini_service.generate(str(prompt), system_prompt=AUDITOR_SYSTEM_PROMPT)
        if text == FALLBACK_MESSAGE:
            return "AI denetci anlatimi su an kullanilamiyor; deterministik denetim raporu gecerli."
        return text


ai_auditor_service = AIAuditorService()
