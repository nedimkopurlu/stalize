"""BIST-specific decision guardrails.

The investment engine should not treat every green score as equally tradable.
This module turns BIST realities (data quality, liquidity, daily price limits,
sector-specific accounting caveats, and market regime) into deterministic
constraints that can be reused by APIs, UI, AI prompts, and tests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import CommodityPrice, PriceHistory
from app.models.stock import Stock


def _num(value: Any) -> Optional[float]:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _age_hours(value: Any) -> Optional[float]:
    if value is None:
        return None
    if not isinstance(value, datetime):
        return None
    now = datetime.now(timezone.utc)
    dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 3600)


def _level(score: float, high: float = 70.0, medium: float = 45.0) -> str:
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def _label(level: str) -> str:
    return {"high": "Yüksek", "medium": "Orta", "low": "Düşük"}.get(level, "Belirsiz")


@dataclass(frozen=True)
class GuardrailThresholds:
    low_liquidity_traded_value: float = 2_000_000.0
    medium_liquidity_traded_value: float = 10_000_000.0
    high_liquidity_traded_value: float = 50_000_000.0
    institutional_liquidity_traded_value: float = 250_000_000.0
    daily_limit_pct: float = 9.5


class DecisionGuardrailEngine:
    """Produces risk controls before a stock can be treated as actionable."""

    def __init__(self, thresholds: GuardrailThresholds | None = None):
        self.thresholds = thresholds or GuardrailThresholds()

    def evaluate(
        self,
        stock: Stock,
        prices: Iterable[PriceHistory],
        market_regime: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        sorted_prices = sorted(list(prices), key=lambda row: row.date)
        data_quality = self.data_quality(stock, sorted_prices)
        liquidity = self.liquidity(stock, sorted_prices)
        limit_lock = self.limit_lock(sorted_prices)
        sector_profile = self.sector_profile(stock)
        market = market_regime or {"label": "unknown", "score": 50, "detail": "BIST100 rejim verisi bağlanmadı."}
        checklist = self.pre_trade_checklist(
            data_quality=data_quality,
            liquidity=liquidity,
            limit_lock=limit_lock,
            sector_profile=sector_profile,
            market_regime=market,
        )

        action_blocks = [item["key"] for item in checklist if item["status"] == "block"]
        warnings = [item["detail"] for item in checklist if item["status"] in {"warning", "block"}]
        confidence_adjustment = 0
        if data_quality["level"] == "low":
            confidence_adjustment -= 16
        elif data_quality["level"] == "medium":
            confidence_adjustment -= 6
        if liquidity["level"] == "low":
            confidence_adjustment -= 18
        elif liquidity["level"] == "medium":
            confidence_adjustment -= 6
        if limit_lock["status"] != "clear":
            confidence_adjustment -= 14
        if market.get("label") == "risk_off":
            confidence_adjustment -= 12
        elif market.get("label") == "neutral":
            confidence_adjustment -= 4
        if sector_profile["requires_special_model"]:
            confidence_adjustment -= 6

        return {
            "data_quality": data_quality,
            "liquidity": liquidity,
            "limit_lock": limit_lock,
            "sector_profile": sector_profile,
            "market_regime": market,
            "pre_trade_checklist": checklist,
            "summary": {
                "action_blocks": action_blocks,
                "warnings": warnings,
                "confidence_adjustment": confidence_adjustment,
                "tradable": len(action_blocks) == 0,
            },
        }

    def data_quality(self, stock: Stock, prices: list[PriceHistory]) -> dict[str, Any]:
        score = 42.0
        issues: list[str] = []

        if len(prices) >= 180:
            score += 22
        elif len(prices) >= 90:
            score += 16
        elif len(prices) >= 30:
            score += 8
        else:
            issues.append("Fiyat geçmişi sınırlı; teknik sinyal güveni düşürüldü.")

        score_fields = (
            getattr(stock, "fundamental_score", None),
            getattr(stock, "technical_score", None),
            getattr(stock, "overall_score", None),
        )
        score += sum(8 for value in score_fields if _num(value) is not None)
        if _num(getattr(stock, "fundamental_score", None)) is None:
            issues.append("Temel analiz skoru eksik; yfinance/vendor verisi güvenli sayılmadı.")
        if _num(getattr(stock, "technical_score", None)) is None:
            issues.append("Teknik skor eksik; karar seviyesi izleme moduna yakın tutulmalı.")

        last_update_hours = _age_hours(getattr(stock, "last_data_update", None))
        if last_update_hours is None:
            issues.append("Son veri güncelleme zamanı bilinmiyor.")
        elif last_update_hours <= 12:
            score += 8
        elif last_update_hours > 48:
            score -= 10
            issues.append("Veri 48 saatten eski; fiyat/haber teyidi alınmadan işlem yapılmamalı.")

        if not getattr(stock, "is_bist100", False):
            score -= 5
            issues.append("BIST100 dışı hissede veri ve likidite güveni ayrıca kontrol edilmeli.")

        score = round(max(0.0, min(100.0, score)), 2)
        level = _level(score, high=75, medium=55)
        return {
            "score": score,
            "level": level,
            "label": _label(level),
            "price_history_days": len(prices),
            "last_update_age_hours": round(last_update_hours, 2) if last_update_hours is not None else None,
            "issues": issues,
            "source_caveat": "Temel veriler resmi KAP finansal tablolarıyla doğrulanmadan nihai kabul edilmez.",
        }

    def liquidity(self, stock: Stock, prices: list[PriceHistory]) -> dict[str, Any]:
        traded_values = []
        volumes = []
        for row in prices[-20:]:
            close = _num(getattr(row, "close", None))
            volume = _num(getattr(row, "volume", None))
            if close is not None and close > 0 and volume is not None and volume > 0:
                traded_values.append(close * volume)
                volumes.append(volume)

        source = "20d_avg"
        if traded_values:
            avg_traded_value = sum(traded_values) / len(traded_values)
            avg_volume = sum(volumes) / len(volumes) if volumes else None
        else:
            source = "latest_snapshot"
            price = _num(getattr(stock, "current_price", None))
            volume = _num(getattr(stock, "volume", None))
            avg_traded_value = price * volume if price and volume else None
            avg_volume = volume

        if avg_traded_value is None:
            score = 55.0
            issues = ["Hacim verisi yok; likidite güveni bilinmiyor."]
        elif avg_traded_value >= self.thresholds.institutional_liquidity_traded_value:
            score = 95.0
            issues = []
        elif avg_traded_value >= self.thresholds.high_liquidity_traded_value:
            score = 82.0
            issues = []
        elif avg_traded_value >= self.thresholds.medium_liquidity_traded_value:
            score = 63.0
            issues = ["Likidite orta; emir büyüklüğü ve spread kontrol edilmeli."]
        elif avg_traded_value >= self.thresholds.low_liquidity_traded_value:
            score = 42.0
            issues = ["Likidite sınırlı; pozisyon küçük tutulmalı ve piyasa emri kullanılmamalı."]
        else:
            score = 22.0
            issues = ["Düşük likidite; sinyal sadece izleme modunda değerlendirilmeli."]

        level = _level(score, high=70, medium=45)
        return {
            "score": round(score, 2),
            "level": level,
            "label": _label(level),
            "avg_traded_value_20d": round(avg_traded_value, 2) if avg_traded_value is not None else None,
            "avg_volume_20d": round(avg_volume, 2) if avg_volume is not None else None,
            "source": source,
            "issues": issues,
        }

    def limit_lock(self, prices: list[PriceHistory]) -> dict[str, Any]:
        events = []
        for prev, cur in zip(prices[-6:-1], prices[-5:]):
            prev_close = _num(getattr(prev, "close", None))
            close = _num(getattr(cur, "close", None))
            if prev_close is None or prev_close <= 0 or close is None:
                continue
            change_pct = ((close / prev_close) - 1.0) * 100
            if change_pct >= self.thresholds.daily_limit_pct:
                events.append({"date": cur.date.isoformat(), "direction": "up", "change_pct": round(change_pct, 2)})
            elif change_pct <= -self.thresholds.daily_limit_pct:
                events.append({"date": cur.date.isoformat(), "direction": "down", "change_pct": round(change_pct, 2)})

        latest = events[-1] if events and prices and events[-1]["date"] == prices[-1].date.isoformat() else None
        up_days = sum(1 for item in events if item["direction"] == "up")
        down_days = sum(1 for item in events if item["direction"] == "down")

        if latest and latest["direction"] == "down":
            status = "locked_down"
            stop_reliability = "poor"
            warning = "Son kapanış taban benzeri; stop emri çalışmayabilir."
        elif latest and latest["direction"] == "up":
            status = "locked_up"
            stop_reliability = "reduced"
            warning = "Son kapanış tavan benzeri; giriş fiyatı gerçekçi olmayabilir."
        elif events:
            status = "recent_limit_move"
            stop_reliability = "reduced"
            warning = "Son günlerde tavan/taban benzeri hareket var; stop ve giriş kalitesi düşer."
        else:
            status = "clear"
            stop_reliability = "normal"
            warning = None

        return {
            "status": status,
            "label": {
                "clear": "Temiz",
                "recent_limit_move": "Yakın limit hareketi",
                "locked_up": "Tavan riski",
                "locked_down": "Taban riski",
            }[status],
            "stop_reliability": stop_reliability,
            "up_days_5d": up_days,
            "down_days_5d": down_days,
            "events": events,
            "warning": warning,
        }

    def sector_profile(self, stock: Stock) -> dict[str, Any]:
        text = " ".join(
            str(getattr(stock, attr, "") or "").lower()
            for attr in ("symbol", "name", "sector", "industry")
        )
        sector_type = "standard"
        label = "Standart şirket"
        required = ["F/K", "FD/FAVÖK", "ROE", "borçluluk", "nakit akışı"]
        if any(word in text for word in ("banka", "bank", "katılım", "finansal kuruluş")):
            sector_type = "bank"
            label = "Banka/finans"
            required = ["PD/DD", "sermaye yeterliliği", "takipteki kredi oranı", "net faiz marjı"]
        elif any(word in text for word in ("gyo", "gayrimenkul yatırım", "reit")):
            sector_type = "reit"
            label = "GYO"
            required = ["NAD iskontosu", "kira geliri", "proje riski", "borç vadesi"]
        elif "holding" in text or "yatırım holding" in text:
            sector_type = "holding"
            label = "Holding"
            required = ["iştirak iskontosu", "NAD", "solo/konsolide ayrımı"]
        elif any(word in text for word in ("havayolu", "hava yolu", "airlines", "thy", "pegasus")):
            sector_type = "aviation"
            label = "Havacılık"
            required = ["yolcu trafiği", "jet yakıt", "kur duyarlılığı", "doluluk oranı"]

        requires_special_model = sector_type != "standard"
        warning = (
            f"{label} için standart F/K odaklı temel skor tek başına yeterli değildir."
            if requires_special_model
            else None
        )
        return {
            "type": sector_type,
            "label": label,
            "requires_special_model": requires_special_model,
            "required_metrics": required,
            "warning": warning,
        }

    def pre_trade_checklist(
        self,
        *,
        data_quality: dict[str, Any],
        liquidity: dict[str, Any],
        limit_lock: dict[str, Any],
        sector_profile: dict[str, Any],
        market_regime: dict[str, Any],
    ) -> list[dict[str, str]]:
        return [
            self._check(
                "data_quality",
                "Veri kalitesi",
                "pass" if data_quality["level"] == "high" else "warning" if data_quality["level"] == "medium" else "block",
                f"Veri güveni {data_quality['label']} ({data_quality['score']}/100).",
            ),
            self._check(
                "liquidity",
                "Likidite",
                "pass" if liquidity["level"] == "high" else "warning" if liquidity["level"] == "medium" else "block",
                liquidity["issues"][0] if liquidity["issues"] else f"Likidite {liquidity['label']}.",
            ),
            self._check(
                "limit_lock",
                "Tavan/taban",
                "pass" if limit_lock["status"] == "clear" else "block" if limit_lock["status"] == "locked_down" else "warning",
                limit_lock["warning"] or "Tavan/taban benzeri hareket yok.",
            ),
            self._check(
                "market_regime",
                "Piyasa rejimi",
                "pass" if market_regime.get("label") == "risk_on" else "warning" if market_regime.get("label") in {"neutral", "unknown"} else "block",
                self._market_detail(market_regime),
            ),
            self._check(
                "sector_model",
                "Sektör modeli",
                "warning" if sector_profile["requires_special_model"] else "pass",
                sector_profile["warning"] or "Standart temel analiz metrikleri bu sınıf için kullanılabilir.",
            ),
            self._check(
                "position_plan",
                "Stop ve pozisyon",
                "pass",
                "Stop, hedef, risk/ödül ve portföy yüzdesi karar kartında kontrol edilmeli.",
            ),
        ]

    def _check(self, key: str, label: str, status: str, detail: str) -> dict[str, str]:
        return {"key": key, "label": label, "status": status, "detail": detail}

    def _market_detail(self, market_regime: dict[str, Any]) -> str:
        label = market_regime.get("label", "unknown")
        if label == "risk_on":
            return "BIST100 trendi risk almaya daha uygun."
        if label == "risk_off":
            return "BIST100 riskli modda; pozitif hisse sinyalleri izlemeye düşürülmeli."
        if label == "neutral":
            return "BIST100 nötr; pozisyon boyutu kontrollü tutulmalı."
        return "BIST100 rejim verisi yetersiz; karar güveni düşürülür."

    async def market_regime(self, db: AsyncSession) -> dict[str, Any]:
        result = await db.execute(
            select(CommodityPrice)
            .where(CommodityPrice.symbol == "XU100.IS")
            .order_by(CommodityPrice.date.desc())
            .limit(220)
        )
        rows = list(reversed(result.scalars().all()))
        closes = [float(row.close) for row in rows if _num(row.close) is not None and float(row.close) > 0]
        volumes = [float(row.volume) for row in rows if _num(row.volume) is not None and float(row.volume) > 0]
        if len(closes) < 50:
            return {"label": "unknown", "score": 50, "detail": "BIST100 trend verisi yetersiz."}

        last = closes[-1]
        sma50 = sum(closes[-50:]) / 50
        sma200 = sum(closes[-200:]) / min(len(closes), 200)
        peak_120 = max(closes[-120:])
        drawdown = ((last / peak_120) - 1.0) * 100 if peak_120 > 0 else 0.0
        five_day_return = ((last / closes[-6]) - 1.0) * 100 if len(closes) >= 6 and closes[-6] > 0 else 0.0
        volume_trend = None
        if len(volumes) >= 20:
            recent = sum(volumes[-5:]) / 5
            base = sum(volumes[-20:]) / 20
            volume_trend = ((recent / base) - 1.0) * 100 if base > 0 else None

        score = 50.0
        score += 16 if last > sma50 else -16
        score += 14 if last > sma200 else -14
        score += 8 if five_day_return > 2 else -8 if five_day_return < -3 else 0
        score += 6 if drawdown > -5 else -14 if drawdown <= -15 else -6
        if volume_trend is not None:
            score += 5 if volume_trend > 15 and five_day_return > 0 else -5 if volume_trend > 15 and five_day_return < 0 else 0

        score = round(max(0.0, min(100.0, score)), 2)
        label = "risk_on" if score >= 65 else "risk_off" if score <= 35 else "neutral"
        return {
            "label": label,
            "score": score,
            "last_close": round(last, 2),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "drawdown_pct": round(drawdown, 2),
            "five_day_return_pct": round(five_day_return, 2),
            "volume_trend_pct": round(volume_trend, 2) if volume_trend is not None else None,
        }


decision_guardrail_engine = DecisionGuardrailEngine()
