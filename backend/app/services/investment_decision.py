"""Investment decision engine.

Turns existing scores and price history into an actionable, risk-aware plan.
The output is deterministic so it can be tested, compared, and audited before
an LLM explains it in prose.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import pstdev
from typing import Any, Iterable, Optional

from app.models.price import PriceHistory
from app.models.stock import Stock
from app.services.decision_guardrails import decision_guardrail_engine


@dataclass(frozen=True)
class DecisionInput:
    stock: Stock
    prices: list[PriceHistory]
    portfolio_value: float = 100_000.0
    risk_per_trade_pct: float = 1.0
    policy: Optional["DecisionPolicy"] = None
    market_regime: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class DecisionPolicy:
    """Optional calibration policy for stricter decision gating."""

    mode: str = "observation"
    min_buy_confidence: int = 0
    min_buy_risk_reward: float = 0.0
    block_high_risk_buys: bool = False


class InvestmentDecisionEngine:
    """Builds a concrete trading decision from scores, trend, and risk."""

    def build_decision(self, data: DecisionInput) -> dict[str, Any]:
        stock = data.stock
        prices = sorted(data.prices, key=lambda p: p.date)
        latest = prices[-1] if prices else None
        current_price = self._current_price(stock, latest)

        atr = self._atr(latest, prices, current_price)
        stop_loss = round(max(0.01, current_price - (2.0 * atr)), 2)
        target_price = round(self._target_price(prices, current_price, stop_loss), 2)
        risk_per_share = max(current_price - stop_loss, 0.01)
        reward_per_share = max(target_price - current_price, 0.0)
        risk_reward = round(reward_per_share / risk_per_share, 2)

        trend = self._trend(latest, current_price)
        annualized_volatility = self._annualized_volatility(prices)
        drawdown_pct = self._drawdown_pct(prices, current_price)
        guardrails = decision_guardrail_engine.evaluate(
            stock=stock,
            prices=prices,
            market_regime=data.market_regime,
        )
        risk_level = self._risk_level(annualized_volatility, drawdown_pct, stock, guardrails)
        confidence = self._confidence(stock, trend, risk_reward, risk_level, guardrails)
        action, action_label = self._action(stock, trend, risk_reward, risk_level, drawdown_pct)
        action, action_label, guardrail_notes = self._apply_guardrails(
            action=action,
            action_label=action_label,
            guardrails=guardrails,
        )
        action, action_label, policy_notes = self._apply_policy(
            action=action,
            action_label=action_label,
            confidence=confidence,
            risk_reward=risk_reward,
            risk_level=risk_level,
            policy=data.policy,
        )
        position = self._position_size(
            portfolio_value=data.portfolio_value,
            risk_per_trade_pct=data.risk_per_trade_pct,
            current_price=current_price,
            risk_per_share=risk_per_share,
            risk_level=risk_level,
        )

        thesis = self._thesis(stock, trend, risk_reward, risk_level, drawdown_pct, guardrails)
        invalidation = (
            f"{stop_loss:.2f} TL altında kapanış veya skorun 45 altına inmesi bu planı geçersiz kılar."
        )

        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "action": action,
            "action_label": action_label,
            "confidence": confidence,
            "risk_level": risk_level,
            "time_horizon": "swing_2_8_weeks",
            "current_price": round(current_price, 2),
            "entry_zone": {
                "low": round(current_price * 0.985, 2),
                "high": round(current_price * 1.015, 2),
            },
            "stop_loss": stop_loss,
            "target_price": target_price,
            "risk_reward": risk_reward,
            "position_size": position,
            "signals": {
                "overall_score": stock.overall_score,
                "technical_score": stock.technical_score,
                "fundamental_score": stock.fundamental_score,
                "sentiment_score": stock.sentiment_score,
                "recommendation": stock.recommendation,
                "trend": trend,
                "drawdown_pct": drawdown_pct,
                "annualized_volatility_pct": annualized_volatility,
                "data_quality_score": guardrails["data_quality"]["score"],
                "liquidity_score": guardrails["liquidity"]["score"],
                "limit_lock_status": guardrails["limit_lock"]["status"],
                "market_regime_label": guardrails["market_regime"].get("label"),
                "sector_profile": guardrails["sector_profile"]["type"],
            },
            "guardrails": guardrails,
            "policy": {
                "mode": data.policy.mode if data.policy else "default",
                "notes": guardrail_notes + policy_notes,
            },
            "thesis": thesis,
            "invalidation": invalidation,
            "watch_items": self._watch_items(stock, trend, risk_level, guardrails),
        }

    def _current_price(self, stock: Stock, latest: Optional[PriceHistory]) -> float:
        if stock.current_price and stock.current_price > 0:
            return float(stock.current_price)
        if latest is not None and latest.close > 0:
            return float(latest.close)
        raise ValueError(f"{stock.symbol} için fiyat verisi yok.")

    def _atr(self, latest: Optional[PriceHistory], prices: list[PriceHistory], current_price: float) -> float:
        if latest is not None and latest.atr_14 and latest.atr_14 > 0:
            return float(latest.atr_14)
        ranges = [
            float(p.high - p.low)
            for p in prices[-14:]
            if p.high is not None and p.low is not None and p.high > p.low
        ]
        if ranges:
            return max(sum(ranges) / len(ranges), current_price * 0.015)
        return current_price * 0.03

    def _target_price(self, prices: list[PriceHistory], current_price: float, stop_loss: float) -> float:
        risk = max(current_price - stop_loss, 0.01)
        resistance = None
        for p in prices[-40:]:
            if p.high is not None and p.high > current_price:
                resistance = max(resistance or 0.0, float(p.high))
        if resistance and resistance >= current_price + (1.4 * risk):
            return resistance
        return current_price + (2.0 * risk)

    def _trend(self, latest: Optional[PriceHistory], current_price: float) -> str:
        if latest is None:
            return "unknown"
        sma50 = latest.sma_50
        sma200 = latest.sma_200
        if sma50 is not None and sma200 is not None:
            if current_price > sma50 > sma200:
                return "bullish"
            if current_price < sma50 < sma200:
                return "bearish"
        if sma50 is not None:
            if current_price > sma50:
                return "constructive"
            if current_price < sma50:
                return "weak"
        return "neutral"

    def _annualized_volatility(self, prices: list[PriceHistory]) -> Optional[float]:
        closes = [float(p.close) for p in prices[-61:] if p.close and p.close > 0]
        if len(closes) < 10:
            return None
        returns = [(closes[i] / closes[i - 1]) - 1.0 for i in range(1, len(closes))]
        return round(pstdev(returns) * sqrt(252) * 100, 2)

    def _drawdown_pct(self, prices: list[PriceHistory], current_price: float) -> Optional[float]:
        highs = [float(p.high) for p in prices[-60:] if p.high and p.high > 0]
        if not highs:
            return None
        peak = max(highs)
        if peak <= 0:
            return None
        return round(((current_price / peak) - 1.0) * 100, 2)

    def _risk_level(
        self,
        volatility: Optional[float],
        drawdown_pct: Optional[float],
        stock: Stock,
        guardrails: dict[str, Any],
    ) -> str:
        score = 0
        if volatility is not None:
            if volatility >= 55:
                score += 2
            elif volatility >= 35:
                score += 1
        if drawdown_pct is not None:
            if drawdown_pct <= -25:
                score += 2
            elif drawdown_pct <= -12:
                score += 1
        if abs(float(stock.daily_change_pct or 0.0)) >= 5:
            score += 1
        if guardrails["liquidity"]["level"] == "low":
            score += 2
        elif guardrails["liquidity"]["level"] == "medium":
            score += 1
        if guardrails["limit_lock"]["status"] != "clear":
            score += 1
        if guardrails["market_regime"].get("label") == "risk_off":
            score += 1
        if getattr(stock, "is_bist30", False):
            score -= 1
        if score >= 3:
            return "high"
        if score >= 1:
            return "medium"
        return "low"

    def _action(
        self,
        stock: Stock,
        trend: str,
        risk_reward: float,
        risk_level: str,
        drawdown_pct: Optional[float],
    ) -> tuple[str, str]:
        overall = float(stock.overall_score or 50.0)
        technical = float(stock.technical_score or 50.0)
        fundamental = float(stock.fundamental_score or 50.0)
        broken = trend in {"bearish", "weak"} or (drawdown_pct is not None and drawdown_pct <= -30)

        if overall >= 82 and technical >= 70 and fundamental >= 60 and risk_reward >= 1.8 and risk_level != "high":
            return "strong_buy", "Güçlü Al"
        if overall >= 70 and technical >= 58 and risk_reward >= 1.5 and not broken:
            return "buy", "Al"
        if overall >= 58 and risk_reward >= 1.2 and trend not in {"bearish"}:
            return "watch", "İzle"
        if overall >= 45 and not broken:
            return "hold", "Tut"
        if overall >= 35:
            return "reduce", "Azalt"
        return "exit", "Çık"

    def _apply_guardrails(
        self,
        action: str,
        action_label: str,
        guardrails: dict[str, Any],
    ) -> tuple[str, str, list[str]]:
        buy_actions = {"strong_buy", "buy"}
        notes: list[str] = []

        if action not in buy_actions:
            return action, action_label, notes

        summary = guardrails.get("summary", {})
        blocks = summary.get("action_blocks", [])
        if blocks:
            notes.append("guardrail_block:" + ",".join(blocks))
            return "watch", "İzle", notes

        if guardrails["market_regime"].get("label") == "risk_off":
            notes.append("market_regime_risk_off")
            return "watch", "İzle", notes

        if guardrails["limit_lock"]["status"] != "clear":
            notes.append(f"limit_lock:{guardrails['limit_lock']['status']}")
            return "watch", "İzle", notes

        if guardrails["data_quality"]["level"] == "medium" or guardrails["liquidity"]["level"] == "medium":
            notes.append("guardrail_caution:data_or_liquidity_medium")
            if action == "strong_buy":
                return "buy", "Al", notes

        return action, action_label, notes

    def _apply_policy(
        self,
        action: str,
        action_label: str,
        confidence: int,
        risk_reward: float,
        risk_level: str,
        policy: Optional[DecisionPolicy],
    ) -> tuple[str, str, list[str]]:
        if policy is None or policy.mode != "enforced":
            return action, action_label, []

        buy_actions = {"strong_buy", "buy"}
        notes = []
        if action in buy_actions and confidence < policy.min_buy_confidence:
            notes.append(f"confidence<{policy.min_buy_confidence}")
        if action in buy_actions and risk_reward < policy.min_buy_risk_reward:
            notes.append(f"risk_reward<{policy.min_buy_risk_reward}")
        if action in buy_actions and policy.block_high_risk_buys and risk_level == "high":
            notes.append("high_risk_buy_blocked")

        if notes:
            return "watch", "İzle", notes
        return action, action_label, []

    def _confidence(
        self,
        stock: Stock,
        trend: str,
        risk_reward: float,
        risk_level: str,
        guardrails: dict[str, Any],
    ) -> int:
        confidence = 35
        available_scores = [
            stock.fundamental_score,
            stock.technical_score,
            stock.sentiment_score,
            stock.overall_score,
        ]
        confidence += sum(8 for value in available_scores if value is not None)
        if trend in {"bullish", "constructive"}:
            confidence += 10
        elif trend in {"bearish", "weak"}:
            confidence -= 8
        if risk_reward >= 2:
            confidence += 10
        elif risk_reward < 1.2:
            confidence -= 8
        if risk_level == "high":
            confidence -= 12
        elif risk_level == "low":
            confidence += 5
        confidence += int(guardrails.get("summary", {}).get("confidence_adjustment", 0))
        return max(0, min(100, confidence))

    def _position_size(
        self,
        portfolio_value: float,
        risk_per_trade_pct: float,
        current_price: float,
        risk_per_share: float,
        risk_level: str,
    ) -> dict[str, Any]:
        risk_budget = max(0.0, portfolio_value) * max(0.0, risk_per_trade_pct) / 100.0
        raw_shares = int(risk_budget // risk_per_share) if risk_per_share > 0 else 0
        max_exposure_pct = {"low": 12.0, "medium": 8.0, "high": 5.0}[risk_level]
        max_shares = int((portfolio_value * max_exposure_pct / 100.0) // current_price) if current_price > 0 else 0
        shares = max(0, min(raw_shares, max_shares))
        exposure = shares * current_price
        return {
            "risk_budget": round(risk_budget, 2),
            "shares": shares,
            "estimated_exposure": round(exposure, 2),
            "estimated_exposure_pct": round((exposure / portfolio_value) * 100, 2) if portfolio_value > 0 else 0.0,
            "max_exposure_pct": max_exposure_pct,
        }

    def _thesis(
        self,
        stock: Stock,
        trend: str,
        risk_reward: float,
        risk_level: str,
        drawdown_pct: Optional[float],
        guardrails: dict[str, Any],
    ) -> list[str]:
        market = guardrails["market_regime"].get("label", "unknown")
        liquidity = guardrails["liquidity"]
        data_quality = guardrails["data_quality"]
        thesis = [
            f"Model skoru {stock.overall_score if stock.overall_score is not None else 'bilinmiyor'} ve mevcut öneri {stock.recommendation or 'yok'}.",
            f"Trend görünümü {trend}; risk/ödül oranı {risk_reward}.",
            f"Risk seviyesi {risk_level} olarak sınıflandı.",
            f"Piyasa rejimi {market}; veri güveni {data_quality['label']} ve likidite {liquidity['label']}.",
        ]
        if drawdown_pct is not None:
            thesis.append(f"Son 60 günlük zirveye göre uzaklık {drawdown_pct}%.")
        if guardrails["sector_profile"]["warning"]:
            thesis.append(guardrails["sector_profile"]["warning"])
        if guardrails["limit_lock"]["warning"]:
            thesis.append(guardrails["limit_lock"]["warning"])
        return thesis

    def _watch_items(self, stock: Stock, trend: str, risk_level: str, guardrails: dict[str, Any]) -> list[str]:
        items = ["KAP haber akışı", "BIST100 genel trendi", "hacim değişimi"]
        if risk_level == "high":
            items.append("gün içi volatilite ve gap riski")
        if trend in {"bearish", "weak"}:
            items.append("50 günlük ortalama üzerine geri dönüş")
        if (stock.fundamental_score or 0) < 50:
            items.append("temel skorun iyileşmesi")
        if guardrails["liquidity"]["level"] != "high":
            items.append("likidite/spread kontrolü")
        if guardrails["limit_lock"]["status"] != "clear":
            items.append("tavan/taban sonrası emir gerçekleşme riski")
        if guardrails["market_regime"].get("label") != "risk_on":
            items.append("piyasa rejimi iyileşmeden pozisyon büyütmeme")
        return items

    def rank_decisions(self, decisions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        action_rank = {
            "strong_buy": 5,
            "buy": 4,
            "watch": 3,
            "hold": 2,
            "reduce": 1,
            "exit": 0,
        }
        return sorted(
            decisions,
            key=lambda d: (
                action_rank.get(d["action"], 0),
                d["confidence"],
                d["risk_reward"],
                d["signals"].get("overall_score") or 0,
            ),
            reverse=True,
        )


investment_decision_engine = InvestmentDecisionEngine()
