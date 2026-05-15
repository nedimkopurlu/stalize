"""
Scoring Service — Genel Skor Hesaplama Motoru.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.fundamental import Fundamental
from app.models.news import NewsItem
from app.models.price import PriceHistory
from app.models.stock import Stock

logger = logging.getLogger(__name__)


def calculate_data_quality_score(fundamental) -> float:
    """0-100 veri kalite skoru. Fundamental satırı temel alınır.

    Başlangıç: 100. Her USD-şüpheli alan için -30, her None alan için -10.
    Minimum 0'a sabitlenir.

    USD-şüpheli eşikler (BIST değerleri USD'ye dönüştürülünce gerçekçi olmayan
    küçük değerler gösterir):
      - pe_ratio: değer mevcut ve pe < 2 (0 < pe < 2 veya pe < 0.5 içerir)
      - pb_ratio: değer mevcut ve pb < 0.05
    Null ceza alanları: pe_ratio, pb_ratio, ev_ebitda, net_income, revenue
    """
    if fundamental is None:
        return 0.0
    score = 100.0
    pe = getattr(fundamental, "pe_ratio", None)
    pb = getattr(fundamental, "pb_ratio", None)
    ev_eb = getattr(fundamental, "ev_ebitda", None)
    net_income = getattr(fundamental, "net_income", None)
    revenue = getattr(fundamental, "revenue", None)

    # USD-şüpheli tespit (yalnızca değer mevcut olduğunda)
    if pe is not None and pe < 2:
        score -= 30
    if pb is not None and pb < 0.05:
        score -= 30

    # Null cezası
    for field_val in (pe, pb, ev_eb, net_income, revenue):
        if field_val is None:
            score -= 10

    return max(0.0, score)


async def calculate_amihud_liquidity(stock_id: int, db) -> tuple:
    """Compute 30-day Amihud illiquidity ratio for a stock.

    Returns:
        (amihud_ratio: float | None, liquidity_score: str | None)
        liquidity_score: "yüksek" (ratio < 0.001), "orta" (0.001-0.01), "düşük" (> 0.01)
        Returns (None, None) if fewer than 5 price rows or all volumes zero.
    """
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock_id)
        .order_by(PriceHistory.date.desc())
        .limit(31)
    )
    rows = result.scalars().all()
    # Need at least 5 to compute at least 4 returns (more robust signal)
    if len(rows) < 5:
        return (None, None)
    # Order ascending for return computation (oldest first)
    rows = list(reversed(rows))
    amihud_values = []
    for i in range(1, len(rows)):
        prev_close = rows[i - 1].close
        curr_close = rows[i].close
        vol = rows[i].volume
        if not prev_close or not vol or vol == 0:
            continue
        ret = abs((curr_close - prev_close) / prev_close)
        amihud_values.append(ret / vol)
    if not amihud_values:
        return (None, None)
    ratio = sum(amihud_values) / len(amihud_values)
    ratio = min(ratio, 1.0)  # cap at 1.0 for display sanity
    if ratio < 0.001:
        score = "yüksek"
    elif ratio <= 0.01:
        score = "orta"
    else:
        score = "düşük"
    return (ratio, score)


class ScoringEngine:
    """Temel, teknik ve haber skorlarini agirliklandirarak birlestirir."""

    DEFAULT_SCORE = 50.0
    CONTEXTUAL_WEIGHTS = {
        "fundamental_score": settings.WEIGHT_FUNDAMENTAL,
        "technical_score": settings.WEIGHT_TECHNICAL,
        "sentiment_score": settings.WEIGHT_NEWS,
        "company_event_score": 0.15,
        "macro_regime_score": 0.10,
        "risk_overlay_score": 0.05,
    }

    def _resolve_weights(self) -> Dict[str, float]:
        """
        CONTEXTUAL_WEIGHTS'teki 3 çekirdek bileşenin göreli oranlarını 1.0'a
        normalize eder; böylece calculate_overall_score ve get_contextual_score_breakdown
        aynı ağırlık oranlarını kullanır.
        """
        core_keys = ("fundamental_score", "technical_score", "sentiment_score")
        core = {k: self.CONTEXTUAL_WEIGHTS[k] for k in core_keys}
        total = sum(core.values())
        return {k: v / total for k, v in core.items()}

    def calculate_overall_score(self, stock: Stock) -> tuple:
        """
        Agirlikli ortalama ile genel skor hesapla.
        Eksik skorlar icin agirlik kalan skorlara normalize edilir.

        Returns:
            (overall_score, recommendation)
        """
        scores = {
            "fundamental_score": stock.fundamental_score,
            "technical_score": stock.technical_score,
            "sentiment_score": stock.sentiment_score,
        }
        weights = self._resolve_weights()

        total_weight = 0.0
        weighted_sum = 0.0

        for score_name, weight in weights.items():
            value = scores.get(score_name)
            if value is not None:
                weighted_sum += value * weight
                total_weight += weight

        if total_weight == 0:
            return self.DEFAULT_SCORE, "TUT"

        # Normalize (eksik skorlar icin agirlik yeniden dagitilir)
        overall = weighted_sum / total_weight
        overall = round(max(0.0, min(100.0, overall)), 2)

        if overall >= 80:
            recommendation = "GÜÇLÜ AL"
        elif overall >= 65:
            recommendation = "AL"
        elif overall >= 45:
            recommendation = "TUT"
        elif overall >= 25:
            recommendation = "SAT"
        else:
            recommendation = "GÜÇLÜ SAT"

        return overall, recommendation

    def get_score_breakdown(self, stock: Stock) -> Dict:
        """Alt skor katkılarını ve normalize ağırlıkları açıkla."""
        weights = self._resolve_weights()
        component_labels = {
            "fundamental_score": "Temel",
            "technical_score": "Teknik",
            "sentiment_score": "Haber/Olay",
        }
        component_reasons = {
            "fundamental_score": "Şirket kârlılığı, çarpanlar, büyüme ve bilanço kalitesi",
            "technical_score": "Trend, momentum, hacim ve volatilite yapısı",
            "sentiment_score": "KAP, makro ve haber akışının fiyatlama üzerindeki etkisi",
        }

        available_components = []
        missing_components = []
        total_weight = 0.0

        for score_name, base_weight in weights.items():
            value = getattr(stock, score_name, None)
            if value is None:
                missing_components.append({
                    "key": score_name,
                    "label": component_labels[score_name],
                    "reason": component_reasons[score_name],
                })
                continue

            total_weight += base_weight
            available_components.append(
                {
                    "key": score_name,
                    "label": component_labels[score_name],
                    "raw_score": round(float(value), 2),
                    "base_weight": round(base_weight, 4),
                    "reason": component_reasons[score_name],
                }
            )

        overall, recommendation = self.calculate_overall_score(stock)

        for component in available_components:
            normalized_weight = component["base_weight"] / total_weight if total_weight > 0 else 0.0
            contribution = component["raw_score"] * normalized_weight
            component["normalized_weight"] = round(normalized_weight, 4)
            component["contribution"] = round(contribution, 2)

        summary = {
            "available_component_count": len(available_components),
            "missing_component_count": len(missing_components),
            "normalization_applied": total_weight > 0 and total_weight < 1.0,
            "weight_coverage": round(total_weight, 4),
        }

        return {
            "overall_score": overall,
            "recommendation": recommendation,
            "components": available_components,
            "missing_components": missing_components,
            "summary": summary,
        }

    def _recommendation_for_score(self, overall: float) -> str:
        if overall >= 80:
            return "GÜÇLÜ AL"
        if overall >= 65:
            return "AL"
        if overall >= 45:
            return "TUT"
        if overall >= 25:
            return "SAT"
        return "GÜÇLÜ SAT"

    def _score_company_event_news(self, items: List[NewsItem]) -> Dict[str, Union[float, str]]:
        if not items:
            return {"score": 50.0, "reason": "Son 30 gunde tez degistiren sirket olayi bulunmadi."}

        weights = []
        weighted_sum = 0.0
        for item in items[:6]:
            base = ((item.sentiment_score or 0.0) + 1.0) / 2.0 * 100.0
            category_bonus = 8.0 if item.category in {"earnings", "investment", "merger", "dividend"} else 0.0
            category_penalty = -10.0 if item.category in {"legal", "share_sale", "rights_issue", "restructuring"} else 0.0
            score = max(0.0, min(100.0, base + category_bonus + category_penalty))
            weight = max(0.2, float(item.importance_score or 0.5))
            weighted_sum += score * weight
            weights.append(weight)

        final_score = round(weighted_sum / sum(weights), 2) if weights else 50.0
        dominant = items[0]
        return {
            "score": final_score,
            "reason": f"Son sirket olayi odagi: {dominant.title[:120]}",
        }

    def _score_macro_regime(self, items: List[NewsItem]) -> Dict[str, Union[float, str]]:
        if not items:
            return {"score": 50.0, "reason": "Son resmi makro akista tez degistiren sinyal bulunmadi."}

        source_weights = {"TCMB": 1.0, "TUIK": 0.95, "HMB": 0.8, "Borsa İstanbul": 0.75}
        weighted_sum = 0.0
        weights = []
        for item in items[:8]:
            base = ((item.sentiment_score or 0.0) + 1.0) / 2.0 * 100.0
            weight = max(0.25, float(item.importance_score or 0.5)) * source_weights.get(item.source or "", 0.7)
            weighted_sum += base * weight
            weights.append(weight)

        score = round(weighted_sum / sum(weights), 2) if weights else 50.0
        return {
            "score": score,
            "reason": f"Makro rejim son resmi akista {items[0].source or 'resmi kaynak'} odakli okunuyor.",
        }

    def _score_risk_overlay(self, stock: Stock, crisis_mode: bool) -> Dict[str, Union[float, str]]:
        score = 50.0
        reasons = []
        daily_move = abs(float(stock.daily_change_pct or 0.0))
        if daily_move >= 5:
            score -= 15
            reasons.append("gunluk oynaklik yuksek")
        elif daily_move >= 3:
            score -= 8
            reasons.append("gunluk oynaklik artmis")

        if crisis_mode:
            score -= 8
            reasons.append("korelasyon rejimi savunmaci")

        if (stock.technical_score or 0) >= 65 and daily_move < 3:
            score += 10
            reasons.append("teknik yapi daha kontrollu")

        if stock.is_bist30:
            score += 4
            reasons.append("likidite avantajı")

        return {
            "score": round(max(0.0, min(100.0, score)), 2),
            "reason": ", ".join(reasons) if reasons else "risk gorunumu dengeli",
        }

    async def get_contextual_score_breakdown(self, stock: Stock, db=None, crisis_mode: bool = False) -> Dict:
        owns_session = db is None
        if owns_session:
            db = AsyncSessionLocal()

        try:
            since_company = datetime.now(timezone.utc) - timedelta(days=30)
            since_macro = datetime.now(timezone.utc) - timedelta(days=21)
            company_items_result = await db.execute(
                select(NewsItem)
                .where(
                    NewsItem.stock_id == stock.id,
                    NewsItem.source == "KAP",
                    NewsItem.published_at >= since_company,
                )
                .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
                .limit(8)
            )
            macro_items_result = await db.execute(
                select(NewsItem)
                .where(
                    NewsItem.stock_id.is_(None),
                    NewsItem.source.in_(["TCMB", "TUIK", "HMB", "Borsa İstanbul"]),
                    NewsItem.published_at >= since_macro,
                )
                .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
                .limit(8)
            )
            company_items = list(company_items_result.scalars().all())
            macro_items = list(macro_items_result.scalars().all())
        finally:
            if owns_session:
                await db.close()

        contextual_components = [
            {
                "key": "fundamental_score",
                "label": "Temel",
                "raw_score": round(float(stock.fundamental_score), 2) if stock.fundamental_score is not None else None,
                "base_weight": self.CONTEXTUAL_WEIGHTS["fundamental_score"],
                "reason": "Sirket kalitesi ve carpansal dayaniklilik",
            },
            {
                "key": "technical_score",
                "label": "Teknik",
                "raw_score": round(float(stock.technical_score), 2) if stock.technical_score is not None else None,
                "base_weight": self.CONTEXTUAL_WEIGHTS["technical_score"],
                "reason": "Trend ve momentum kalitesi",
            },
            {
                "key": "sentiment_score",
                "label": "Haber",
                "raw_score": round(float(stock.sentiment_score), 2) if stock.sentiment_score is not None else None,
                "base_weight": self.CONTEXTUAL_WEIGHTS["sentiment_score"],
                "reason": "Anlik haber ve KAP akisindan gelen taban algi",
            },
        ]
        company_event = self._score_company_event_news(company_items)
        macro_regime = self._score_macro_regime(macro_items)
        risk_overlay = self._score_risk_overlay(stock, crisis_mode)

        contextual_components.extend([
            {
                "key": "company_event_score",
                "label": "Sirket Olayi",
                "raw_score": company_event["score"],
                "base_weight": self.CONTEXTUAL_WEIGHTS["company_event_score"],
                "reason": company_event["reason"],
            },
            {
                "key": "macro_regime_score",
                "label": "Makro Rejim",
                "raw_score": macro_regime["score"],
                "base_weight": self.CONTEXTUAL_WEIGHTS["macro_regime_score"],
                "reason": macro_regime["reason"],
            },
            {
                "key": "risk_overlay_score",
                "label": "Risk Katmani",
                "raw_score": risk_overlay["score"],
                "base_weight": self.CONTEXTUAL_WEIGHTS["risk_overlay_score"],
                "reason": risk_overlay["reason"],
            },
        ])

        # NULL bileşenleri ağırlıklandırmadan çıkar (50.0 doldurmak yerine)
        available = [c for c in contextual_components if c["raw_score"] is not None]
        missing = [c for c in contextual_components if c["raw_score"] is None]

        total_weight = sum(c["base_weight"] for c in available)
        weighted_sum = 0.0
        for component in contextual_components:
            if component["raw_score"] is None:
                component["normalized_weight"] = 0.0
                component["contribution"] = 0.0
                continue
            normalized_weight = component["base_weight"] / total_weight if total_weight else 0.0
            component["normalized_weight"] = round(normalized_weight, 4)
            component["contribution"] = round(component["raw_score"] * normalized_weight, 2)
            weighted_sum += component["raw_score"] * normalized_weight

        overall = round(max(0.0, min(100.0, weighted_sum)), 2)
        recommendation = self._recommendation_for_score(overall)
        return {
            "overall_score": overall,
            "recommendation": recommendation,
            "components": contextual_components,
            "missing_components": [c["key"] for c in missing],
            "summary": {
                "available_component_count": len(available),
                "missing_component_count": len(missing),
                "normalization_applied": len(missing) > 0,
                "weight_coverage": round(total_weight / sum(c["base_weight"] for c in contextual_components), 4) if contextual_components else 1.0,
                "crisis_mode": crisis_mode,
            },
        }

    async def update_all_scores(self):
        """Tum hisseler icin genel skoru guncelle."""
        logger.info("Genel skor hesaplamasi basliyor...")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock).where(Stock.is_active))
            stocks = result.scalars().all()

            updated = 0
            for stock in stocks:
                contextual = await self.get_contextual_score_breakdown(stock, db=db, crisis_mode=False)
                overall = contextual["overall_score"]
                recommendation = contextual["recommendation"]
                stock.overall_score = overall
                stock.recommendation = recommendation

                # En güncel fundamental kaydını çek ve veri kalite skorunu hesapla
                fund_result = await db.execute(
                    select(Fundamental)
                    .where(Fundamental.stock_id == stock.id)
                    .order_by(Fundamental.updated_at.desc())
                    .limit(1)
                )
                fundamental = fund_result.scalar_one_or_none()
                if fundamental is not None:
                    stock.data_quality_score = calculate_data_quality_score(fundamental)
                else:
                    stock.data_quality_score = None

                amihud_ratio, liquidity_score = await calculate_amihud_liquidity(stock.id, db)
                stock.amihud_ratio = amihud_ratio
                stock.liquidity_score = liquidity_score

                updated += 1

            await db.commit()

        logger.info(f"{updated} hisse skoru guncellendi")
        return updated

    async def get_rankings(
        self,
        sort_by: str = "overall_score",
        limit: int = 30,
        sector: Optional[str] = None,
        bist30_only: bool = False,
    ) -> List[Dict]:
        """Hisseleri skorlarina gore sirala."""
        async with AsyncSessionLocal() as db:
            query = select(Stock).where(Stock.is_active)

            if bist30_only:
                query = query.where(Stock.is_bist30)
            if sector:
                query = query.where(Stock.sector == sector)

            sort_column = getattr(Stock, sort_by, Stock.overall_score)
            query = query.order_by(sort_column.desc().nullslast()).limit(limit)

            result = await db.execute(query)
            stocks = result.scalars().all()

            return [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "sector": s.sector,
                    "current_price": s.current_price,
                    "daily_change_pct": s.daily_change_pct,
                    "volume": s.volume,
                    "market_cap": s.market_cap,
                    "is_bist30": s.is_bist30,
                    "technical_score": s.technical_score,
                    "fundamental_score": s.fundamental_score,
                    "sentiment_score": s.sentiment_score,
                    "overall_score": s.overall_score,
                    "recommendation": s.recommendation,
                }
                for s in stocks
            ]


# Singleton
scoring_engine = ScoringEngine()
