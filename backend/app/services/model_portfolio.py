"""Haftalık otomatik model portföy servisi."""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional, Tuple

from sqlalchemy import delete, desc, select

from app.core.database import AsyncSessionLocal
from app.models.model_portfolio import ModelPortfolioDailySnapshot, ModelPortfolioHolding, ModelPortfolioWeek
from app.models.stock import Stock
from app.services.gemini_service import gemini_service, FALLBACK_MESSAGE
from app.services.portfolio_snapshot import _fetch_close_price

logger = logging.getLogger(__name__)

MAX_HOLDINGS = 8
DEFAULT_SECTOR_CAP = 2
MODEL_STRATEGY_VERSION = "weekly-v1"


def _week_bounds(target_date: Optional[date] = None) -> Tuple[date, date]:
    target_date = target_date or datetime.now(timezone.utc).date()
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=4)
    return week_start, week_end


def _holding_rationale(stock: Stock) -> str:
    reasons: list[str] = []
    if (stock.fundamental_score or 0) >= 65:
        reasons.append("temel kalite güçlü")
    if (stock.technical_score or 0) >= 60:
        reasons.append("teknik yapı destekli")
    if (stock.sentiment_score or 0) >= 55:
        reasons.append("haber/KAP akışı destekleyici")
    if not reasons:
        reasons.append("genel skor evren ortalamasının üzerinde")
    return ", ".join(reasons).capitalize() + "."


def _classify_holding_failure(holding: ModelPortfolioHolding, weekly_return: float) -> list[str]:
    reasons: list[str] = []
    if (holding.technical_score or 0) < 50:
        reasons.append("technical_breakdown")
    if (holding.fundamental_score or 0) < 55:
        reasons.append("fundamental_weakness")
    if (holding.sentiment_score or 0) < 50:
        reasons.append("negative_news_flow")
    if (holding.overall_score or 0) < 60:
        reasons.append("low_conviction")
    if weekly_return <= -7:
        reasons.append("deep_drawdown")
    if not reasons:
        reasons.append("market_relative_weakness")
    return reasons


def _factor_label(key: str) -> str:
    return {
        "technical_breakdown": "teknik kırılım",
        "fundamental_weakness": "temel zayıflık",
        "negative_news_flow": "negatif haber/KAP akışı",
        "low_conviction": "düşük genel kalite",
        "deep_drawdown": "derin değer kaybı",
        "market_relative_weakness": "göreli zayıflık",
    }.get(key, key)


def _build_next_week_adjustments(
    poor_performers: list[dict[str, Any]],
    sector_drag: dict[str, float],
    factor_drag: dict[str, float],
) -> dict[str, Any]:
    penalized_symbols = sorted(
        item["symbol"]
        for item in poor_performers
        if item.get("return_pct", 0) <= -5 or "deep_drawdown" in item.get("failure_tags", [])
    )

    sector_caps: dict[str, int] = {}
    for sector, drag in sector_drag.items():
        if drag < -1:
            sector_caps[sector] = 1

    factor_penalties: dict[str, int] = {}
    for key, drag in factor_drag.items():
        if drag >= 1:
            factor_penalties[key] = 6

    review_mode = "balanced"
    if len(penalized_symbols) >= 3 or len(sector_caps) >= 2:
        review_mode = "defensive"
    elif not penalized_symbols and not sector_caps and not factor_penalties:
        review_mode = "offensive"

    return {
        "penalized_symbols": penalized_symbols,
        "sector_caps": sector_caps,
        "factor_penalties": factor_penalties,
        "review_mode": review_mode,
    }


def _build_review_summary(
    *,
    portfolio_return: float,
    top_drags: list[Tuple[str, float]],
    factor_drag: dict[str, float],
    adjustments: dict[str, Any],
) -> str:
    if portfolio_return >= 0:
        return "Bu hafta anlamlı bir zayıflık oluşmadı; mevcut seçim çerçevesi korunabilir."

    drag_text = ", ".join(f"{sector} ({value:.2f} puan)" for sector, value in top_drags) or "tekil hisseler"
    top_factors = sorted(factor_drag.items(), key=lambda item: item[1], reverse=True)[:2]
    factor_text = ", ".join(_factor_label(key) for key, _ in top_factors) if top_factors else "tekil zayıflıklar"
    penalized = adjustments.get("penalized_symbols") or []
    if penalized:
        penalize_text = ", ".join(penalized[:4])
        return (
            f"Haftalık zarar ana olarak {drag_text} kaynaklı oluştu. "
            f"Öne çıkan zayıflıklar {factor_text}; gelecek hafta {penalize_text} için ek ceza uygulanacak."
        )
    return (
        f"Haftalık zarar ana olarak {drag_text} kaynaklı oluştu. "
        f"Öne çıkan zayıflıklar {factor_text}; gelecek hafta seçim motoru bu alanları daha sıkı filtreleyecek."
    )


def _selection_score(stock: Stock) -> float:
    overall = stock.overall_score or 0
    fundamental = stock.fundamental_score or 0
    technical = stock.technical_score or 0
    sentiment = stock.sentiment_score or 0
    return (
        overall * 0.4
        + fundamental * 0.3
        + technical * 0.2
        + sentiment * 0.1
    )


async def _fetch_benchmark_close(symbol: str = "XU100.IS") -> Optional[float]:
    price = await _fetch_close_price(symbol)
    return round(float(price), 2) if price is not None else None


def _summarize_week_changes(
    current_holdings: list[ModelPortfolioHolding],
    previous_holdings: list[ModelPortfolioHolding],
) -> dict[str, Any]:
    previous_map = {holding.symbol: holding for holding in previous_holdings}
    current_map = {holding.symbol: holding for holding in current_holdings}

    added = sorted(symbol for symbol in current_map if symbol not in previous_map)
    removed = sorted(symbol for symbol in previous_map if symbol not in current_map)

    increased: list[dict[str, Any]] = []
    decreased: list[dict[str, Any]] = []
    unchanged: list[str] = []

    for symbol in sorted(set(current_map) & set(previous_map)):
        current_weight = round(current_map[symbol].allocation_pct or 0, 2)
        previous_weight = round(previous_map[symbol].allocation_pct or 0, 2)
        delta = round(current_weight - previous_weight, 2)
        if abs(delta) < 0.1:
            unchanged.append(symbol)
            continue
        item = {
            "symbol": symbol,
            "previous_allocation_pct": previous_weight,
            "current_allocation_pct": current_weight,
            "delta_pct": delta,
        }
        if delta > 0:
            increased.append(item)
        else:
            decreased.append(item)

    summary_parts: list[str] = []
    if added:
        summary_parts.append(f"eklenen: {', '.join(added[:4])}")
    if removed:
        summary_parts.append(f"çıkarılan: {', '.join(removed[:4])}")
    if increased:
        summary_parts.append(
            "ağırlığı artırılan: "
            + ", ".join(f"{item['symbol']} (+%{item['delta_pct']:.2f})" for item in increased[:3])
        )
    if decreased:
        summary_parts.append(
            "ağırlığı azaltılan: "
            + ", ".join(f"{item['symbol']} ({item['delta_pct']:.2f} puan)" for item in decreased[:3])
        )

    return {
        "added": added,
        "removed": removed,
        "increased": increased,
        "decreased": decreased,
        "unchanged": unchanged,
        "summary": "; ".join(summary_parts) if summary_parts else "Geçen haftaya göre anlamlı bir kompozisyon değişikliği yok.",
    }


def _build_decision_band(
    review_notes: Optional[dict[str, Any]],
    review_summary: Optional[str],
    changes: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if not review_notes and not changes and not review_summary:
        return None

    focus = review_summary or "Bu hafta model portföy mevcut seçim çerçevesini koruyor."
    action_items: list[str] = []

    if changes:
        if changes.get("added"):
            action_items.append(f"Eklenen hisseler: {', '.join(changes['added'][:4])}")
        if changes.get("removed"):
            action_items.append(f"Çıkarılan hisseler: {', '.join(changes['removed'][:4])}")

    next_week_adjustments = (review_notes or {}).get("next_week_adjustments", {})
    penalized_symbols = next_week_adjustments.get("penalized_symbols", [])
    if penalized_symbols:
        action_items.append(f"Sıkı izleme: {', '.join(penalized_symbols[:4])}")

    factor_drag = (review_notes or {}).get("factor_drag", [])
    if factor_drag:
        top_labels = ", ".join(item["label"] for item in factor_drag[:2])
        action_items.append(f"Zayıf alanlar: {top_labels}")

    if not action_items and changes and changes.get("summary"):
        action_items.append(changes["summary"])

    return {
        "headline": "Bu haftaki model portföy kararı",
        "focus": focus,
        "actions": action_items[:4],
    }


async def _generate_gemini_rationale(
    changes: dict,
    holdings_count: int,
    selected_stocks: list | None = None,
) -> str:
    """LLM ile haftalık model portföy kararlarını derinlemesine Türkçe açıkla."""
    added = changes.get("added", [])
    removed = changes.get("removed", [])
    increased = changes.get("increased", [])
    decreased = changes.get("decreased", [])

    # Seçili hisselerin skor ve sektör özeti
    holdings_context = ""
    if selected_stocks:
        top = sorted(selected_stocks, key=lambda s: s.overall_score or 0, reverse=True)[:5]
        lines = [f"  - {s.symbol} ({s.sector or 'Sektör?'}): skor {s.overall_score:.0f}/100, öneri {s.recommendation or '?'}"
                 for s in top]
        holdings_context = "\n## En Yüksek Skorlu Hisseler (Top 5)\n" + "\n".join(lines)

    # Değişiklik özeti
    change_lines = []
    if added:
        change_lines.append(f"  - Eklenenler: {', '.join(added[:6])}")
    if removed:
        change_lines.append(f"  - Çıkarılanlar: {', '.join(removed[:6])}")
    if increased:
        syms = [f"{x['symbol']} ({x['previous_allocation_pct']:.0f}→{x['current_allocation_pct']:.0f}%)" for x in increased[:3]]
        change_lines.append(f"  - Ağırlığı arttırılanlar: {', '.join(syms)}")
    if decreased:
        syms = [f"{x['symbol']} ({x['previous_allocation_pct']:.0f}→{x['current_allocation_pct']:.0f}%)" for x in decreased[:3]]
        change_lines.append(f"  - Ağırlığı azaltılanlar: {', '.join(syms)}")
    if not change_lines:
        change_lines.append("  - Bu hafta portföy bileşiminde önemli bir değişiklik yapılmadı.")

    change_section = "\n".join(change_lines)

    prompt = f"""Haftalık BIST100 model portföyü AI tarafından güncellendi. Yatırımcılara bu kararları açıkla.

## Portföy Özeti
- Toplam hisse sayısı: {holdings_count}

## Bu Haftaki Değişiklikler
{change_section}
{holdings_context}

## Açıklama Talimatları
1. Bu haftaki portföy kararlarını bütünsel bir strateji çerçevesinde değerlendir
2. Önemli ekleme/çıkarma varsa genel gerekçeyi belirt (örn. momentum, değerleme, risk azaltma)
3. Değişiklik yoksa portföyün neden korunduğunu açıkla
4. Yatırımcıya "bu hafta ne beklenmeli?" sorusunu yanıtla

Yanıtı 3-5 cümlelik akıcı Türkçe paragraf olarak yaz. Madde listesi kullanma. Yasal uyarı ekleme."""

    return await gemini_service.generate(prompt)


async def _load_candidate_stocks() -> list[Stock]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Stock)
            .where(
                Stock.is_active,
                Stock.current_price.is_not(None),
                Stock.overall_score.is_not(None),
            )
            .order_by(desc(Stock.overall_score))
            .limit(80)
        )
        return list(result.scalars().all())


async def review_model_portfolio_week(week_id: int) -> Optional[dict[str, Any]]:
    async with AsyncSessionLocal() as db:
        week = await db.get(ModelPortfolioWeek, week_id)
        if week is None:
            return None

        holdings_result = await db.execute(
            select(ModelPortfolioHolding).where(ModelPortfolioHolding.week_id == week.id).order_by(ModelPortfolioHolding.rank.asc())
        )
        holdings = list(holdings_result.scalars().all())
        if not holdings:
            return None

        benchmark_last = await _fetch_benchmark_close(week.benchmark_symbol)
        portfolio_return = 0.0
        sector_drag: dict[str, float] = defaultdict(float)
        factor_drag: dict[str, float] = defaultdict(float)
        poor_performers: list[dict[str, Any]] = []

        for holding in holdings:
            current_price = await _fetch_close_price(f"{holding.symbol}.IS")
            if current_price is None or holding.entry_price in (None, 0):
                continue

            weekly_return = ((current_price - holding.entry_price) / holding.entry_price) * 100
            weighted_return = weekly_return * (holding.allocation_pct / 100)
            portfolio_return += weighted_return
            holding.current_price = round(float(current_price), 2)
            holding.weekly_return_pct = round(weekly_return, 4)

            if weekly_return < 0:
                sector_drag[holding.sector or "Bilinmeyen"] += weighted_return
                failure_tags = _classify_holding_failure(holding, weekly_return)
                for tag in failure_tags:
                    factor_drag[tag] += abs(weighted_return)
                poor_performers.append(
                    {
                        "symbol": holding.symbol,
                        "sector": holding.sector,
                        "return_pct": round(weekly_return, 2),
                        "overall_score": holding.overall_score,
                        "technical_score": holding.technical_score,
                        "fundamental_score": holding.fundamental_score,
                        "sentiment_score": holding.sentiment_score,
                        "failure_tags": failure_tags,
                        "primary_reason": _factor_label(failure_tags[0]),
                    }
                )

        benchmark_return = None
        if week.benchmark_entry in (None, 0) and benchmark_last is not None:
            week.benchmark_entry = benchmark_last
        if week.benchmark_entry not in (None, 0) and benchmark_last is not None:
            benchmark_return = ((benchmark_last - week.benchmark_entry) / week.benchmark_entry) * 100

        poor_performers.sort(key=lambda item: item["return_pct"])
        top_drags = sorted(sector_drag.items(), key=lambda item: item[1])[:3]
        top_factors = sorted(factor_drag.items(), key=lambda item: item[1], reverse=True)[:4]
        weakest_dimension = _factor_label(top_factors[0][0]) if top_factors else "belirgin zayıflık yok"
        adjustments = _build_next_week_adjustments(poor_performers, sector_drag, factor_drag)
        summary = _build_review_summary(
            portfolio_return=portfolio_return,
            top_drags=top_drags,
            factor_drag=factor_drag,
            adjustments=adjustments,
        )

        week.benchmark_last = benchmark_last
        week.portfolio_return_pct = round(portfolio_return, 4)
        week.benchmark_return_pct = round(benchmark_return, 4) if benchmark_return is not None else None
        week.active_return_spread = (
            round(week.portfolio_return_pct - week.benchmark_return_pct, 4)
            if week.portfolio_return_pct is not None and week.benchmark_return_pct is not None
            else None
        )
        week.review_summary = summary
        week.reviewed_at = datetime.now(timezone.utc)
        week.review_notes = {
            "poor_performers": poor_performers[:5],
            "sector_drag": [
                {"sector": sector, "weighted_drag": round(value, 4)}
                for sector, value in top_drags
            ],
            "weakest_dimension": weakest_dimension,
            "factor_drag": [
                {"factor": key, "label": _factor_label(key), "weighted_drag": round(value, 4)}
                for key, value in top_factors
            ],
            "next_week_adjustments": adjustments,
        }
        week.status = "reviewed"
        await db.commit()

        return {
            "portfolio_return_pct": week.portfolio_return_pct,
            "benchmark_return_pct": week.benchmark_return_pct,
            "active_return_spread": week.active_return_spread,
            "review_summary": week.review_summary,
            "review_notes": week.review_notes,
        }


async def generate_weekly_model_portfolio(force: bool = False, target_date: Optional[date] = None) -> dict[str, Any]:
    week_start, week_end = _week_bounds(target_date)
    candidates = await _load_candidate_stocks()

    async with AsyncSessionLocal() as db:
        existing_result = await db.execute(
            select(ModelPortfolioWeek).where(ModelPortfolioWeek.week_start == week_start)
        )
        existing = existing_result.scalar_one_or_none()
        if existing and not force:
            return await get_current_model_portfolio()

        latest_result = await db.execute(
            select(ModelPortfolioWeek).order_by(ModelPortfolioWeek.week_start.desc()).limit(1)
        )
        previous_week = latest_result.scalar_one_or_none()
        previous_review = None
        penalized_symbols: set[str] = set()
        sector_caps: dict[str, int] = defaultdict(lambda: DEFAULT_SECTOR_CAP)
        factor_penalties: dict[str, int] = {}

        if previous_week is not None and previous_week.week_start != week_start:
            previous_review = await review_model_portfolio_week(previous_week.id)
            adjustment_plan = (previous_review or {}).get("review_notes", {}).get("next_week_adjustments", {})
            penalized_symbols.update(adjustment_plan.get("penalized_symbols", []))
            for sector, cap in adjustment_plan.get("sector_caps", {}).items():
                sector_caps[sector] = cap
            factor_penalties = {
                str(key): int(value)
                for key, value in adjustment_plan.get("factor_penalties", {}).items()
            }

        if existing:
            await db.execute(delete(ModelPortfolioHolding).where(ModelPortfolioHolding.week_id == existing.id))
            await db.execute(delete(ModelPortfolioDailySnapshot).where(ModelPortfolioDailySnapshot.week_id == existing.id))
            await db.delete(existing)
            await db.flush()

        ranked = []
        for stock in candidates:
            if stock.recommendation not in {"GÜÇLÜ AL", "AL", "TUT"}:
                continue
            penalty = 8 if stock.symbol in penalized_symbols else 0
            if factor_penalties.get("technical_breakdown") and (stock.technical_score or 0) < 60:
                penalty += factor_penalties["technical_breakdown"]
            if factor_penalties.get("fundamental_weakness") and (stock.fundamental_score or 0) < 60:
                penalty += factor_penalties["fundamental_weakness"]
            if factor_penalties.get("negative_news_flow") and (stock.sentiment_score or 0) < 50:
                penalty += factor_penalties["negative_news_flow"]
            if factor_penalties.get("low_conviction") and (stock.overall_score or 0) < 65:
                penalty += factor_penalties["low_conviction"]
            ranked.append((_selection_score(stock) - penalty, stock))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected: list[Stock] = []
        sector_counts: dict[str, int] = defaultdict(int)

        for _, stock in ranked:
            sector = stock.sector or "Bilinmeyen"
            sector_cap = sector_caps[sector]
            if sector_counts[sector] >= sector_cap:
                continue
            selected.append(stock)
            sector_counts[sector] += 1
            if len(selected) >= MAX_HOLDINGS:
                break

        if not selected:
            raise RuntimeError("Model portföy için uygun hisse bulunamadı.")

        allocation_base = sum(max((stock.overall_score or 0), 1) for stock in selected)
        benchmark_entry = await _fetch_benchmark_close()

        week = ModelPortfolioWeek(
            week_start=week_start,
            week_end=week_end,
            strategy_version=MODEL_STRATEGY_VERSION,
            status="active",
            benchmark_entry=benchmark_entry,
            generation_notes={
                "selection_rule": "overall/fundamental ağırlıklı, sektör dağıtılmış haftalık seçim",
                "penalized_symbols": sorted(penalized_symbols),
                "sector_caps": dict(sector_caps),
                "factor_penalties": factor_penalties,
                "previous_adjustment_mode": (previous_review or {}).get("review_notes", {}).get("next_week_adjustments", {}).get("review_mode"),
                "previous_review_summary": previous_review["review_summary"] if previous_review else None,
            },
        )
        db.add(week)
        await db.flush()

        holdings_payload = []
        for index, stock in enumerate(selected, start=1):
            allocation_pct = round((max((stock.overall_score or 0), 1) / allocation_base) * 100, 2)
            holding = ModelPortfolioHolding(
                week_id=week.id,
                symbol=stock.symbol,
                name=stock.name,
                sector=stock.sector,
                allocation_pct=allocation_pct,
                entry_price=stock.current_price,
                current_price=stock.current_price,
                daily_change_pct=stock.daily_change_pct,
                technical_score=stock.technical_score,
                fundamental_score=stock.fundamental_score,
                sentiment_score=stock.sentiment_score,
                overall_score=stock.overall_score,
                recommendation=stock.recommendation,
                rank=index,
                rationale=_holding_rationale(stock),
            )
            db.add(holding)
            holdings_payload.append(
                {
                    "symbol": stock.symbol,
                    "allocation_pct": allocation_pct,
                    "sector": stock.sector,
                    "overall_score": stock.overall_score,
                    "recommendation": stock.recommendation,
                }
            )

        await db.commit()

    # ── Gemini haftalık gerekçe (LLM-04) ──────────────────────────────────
    try:
        # Önceki haftayla karşılaştırarak değişiklikleri hesapla
        previous_week_holdings: list[ModelPortfolioHolding] = []
        if previous_week is not None and previous_week.week_start != week_start:
            async with AsyncSessionLocal() as _db:
                prev_h_result = await _db.execute(
                    select(ModelPortfolioHolding).where(ModelPortfolioHolding.week_id == previous_week.id)
                )
                previous_week_holdings = list(prev_h_result.scalars().all())

        # Seçilen hisseleri mock ModelPortfolioHolding nesneleri gibi temsil et
        class _FakeHolding:
            def __init__(self, sym: str):
                self.symbol = sym
                self.allocation_pct = 0

        current_fakes = [_FakeHolding(s.symbol) for s in selected]
        changes_for_gemini = _summarize_week_changes(current_fakes, previous_week_holdings)  # type: ignore[arg-type]

        gemini_text = await _generate_gemini_rationale(changes_for_gemini, len(selected), selected_stocks=selected)

        if gemini_text and FALLBACK_MESSAGE not in gemini_text:
            async with AsyncSessionLocal() as update_db:
                upd_result = await update_db.execute(
                    select(ModelPortfolioWeek).where(ModelPortfolioWeek.id == week.id)
                )
                w = upd_result.scalar_one_or_none()
                if w:
                    w.review_summary = gemini_text
                    await update_db.commit()
            logger.info(f"MODEL_PORTFOLIO Gemini gerekçe yazıldı (week_id={week.id})")
    except Exception as _e:
        logger.warning(f"Gemini haftalık gerekçe üretilemedi — deterministik fallback korunuyor: {_e}")

    await take_model_portfolio_snapshot(for_week_start=week_start)
    payload = await get_current_model_portfolio()
    payload["generated"] = True
    payload["generation_notes"] = {
        "selected_count": len(selected),
        "penalized_symbols": sorted(penalized_symbols),
        "sector_caps": dict(sector_caps),
        "factor_penalties": factor_penalties,
        "holdings": holdings_payload,
    }
    return payload


async def take_model_portfolio_snapshot(for_week_start: Optional[date] = None) -> Optional[dict[str, Any]]:
    today = datetime.now(timezone.utc).date()

    async with AsyncSessionLocal() as db:
        week_query = select(ModelPortfolioWeek).order_by(ModelPortfolioWeek.week_start.desc())
        if for_week_start is not None:
            week_query = week_query.where(ModelPortfolioWeek.week_start == for_week_start)
        week_result = await db.execute(week_query.limit(1))
        week = week_result.scalar_one_or_none()
        if week is None:
            return None

        holdings_result = await db.execute(
            select(ModelPortfolioHolding).where(ModelPortfolioHolding.week_id == week.id).order_by(ModelPortfolioHolding.rank.asc())
        )
        holdings = list(holdings_result.scalars().all())
        if not holdings:
            return None

        total_return = 0.0
        daily_return = 0.0
        positions_json = []

        for holding in holdings:
            async with AsyncSessionLocal() as price_db:
                stock_result = await price_db.execute(select(Stock).where(Stock.symbol == holding.symbol))
                stock = stock_result.scalar_one_or_none()
            if stock is None or holding.entry_price in (None, 0):
                continue

            current_price = stock.current_price or holding.entry_price
            weekly_return = ((current_price - holding.entry_price) / holding.entry_price) * 100
            weighted_return = weekly_return * (holding.allocation_pct / 100)
            total_return += weighted_return
            weighted_daily = (stock.daily_change_pct or 0) * (holding.allocation_pct / 100)
            daily_return += weighted_daily

            holding.current_price = current_price
            holding.weekly_return_pct = round(weekly_return, 4)
            holding.daily_change_pct = stock.daily_change_pct

            positions_json.append(
                {
                    "symbol": holding.symbol,
                    "allocation_pct": holding.allocation_pct,
                    "weekly_return_pct": holding.weekly_return_pct,
                    "daily_change_pct": holding.daily_change_pct,
                }
            )

        benchmark_last = await _fetch_benchmark_close(week.benchmark_symbol)
        if week.benchmark_entry in (None, 0) and benchmark_last is not None:
            week.benchmark_entry = benchmark_last
        benchmark_return = None
        if week.benchmark_entry not in (None, 0) and benchmark_last is not None:
            benchmark_return = ((benchmark_last - week.benchmark_entry) / week.benchmark_entry) * 100
        active_spread = round(total_return - benchmark_return, 4) if benchmark_return is not None else None

        week.portfolio_return_pct = round(total_return, 4)
        week.daily_return_pct = round(daily_return, 4)
        week.benchmark_last = benchmark_last
        week.benchmark_return_pct = round(benchmark_return, 4) if benchmark_return is not None else None
        week.active_return_spread = active_spread

        existing_result = await db.execute(
            select(ModelPortfolioDailySnapshot).where(
                ModelPortfolioDailySnapshot.week_id == week.id,
                ModelPortfolioDailySnapshot.date == today,
            )
        )
        snapshot = existing_result.scalar_one_or_none()
        if snapshot is None:
            snapshot = ModelPortfolioDailySnapshot(
                week_id=week.id,
                date=today,
                total_return_pct=round(total_return, 4),
                daily_return_pct=round(daily_return, 4),
                benchmark_return_pct=round(benchmark_return, 4) if benchmark_return is not None else None,
                active_return_spread=active_spread,
                positions_json=positions_json,
            )
            db.add(snapshot)
        else:
            snapshot.total_return_pct = round(total_return, 4)
            snapshot.daily_return_pct = round(daily_return, 4)
            snapshot.benchmark_return_pct = round(benchmark_return, 4) if benchmark_return is not None else None
            snapshot.active_return_spread = active_spread
            snapshot.positions_json = positions_json

        await db.commit()
        return {
            "week_id": week.id,
            "date": today.isoformat(),
            "total_return_pct": round(total_return, 4),
            "daily_return_pct": round(daily_return, 4),
            "benchmark_return_pct": round(benchmark_return, 4) if benchmark_return is not None else None,
            "active_return_spread": active_spread,
        }


async def get_current_model_portfolio() -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        week_result = await db.execute(
            select(ModelPortfolioWeek).order_by(ModelPortfolioWeek.week_start.desc()).limit(1)
        )
        week = week_result.scalar_one_or_none()
        if week is None:
            return {
                "week": None,
                "holdings": [],
                "snapshots": [],
                "summary": None,
            }

        holdings_result = await db.execute(
            select(ModelPortfolioHolding).where(ModelPortfolioHolding.week_id == week.id).order_by(ModelPortfolioHolding.rank.asc())
        )
        holdings = list(holdings_result.scalars().all())
        previous_week_result = await db.execute(
            select(ModelPortfolioWeek)
            .where(ModelPortfolioWeek.week_start < week.week_start)
            .order_by(ModelPortfolioWeek.week_start.desc())
            .limit(1)
        )
        previous_week = previous_week_result.scalar_one_or_none()
        previous_holdings: list[ModelPortfolioHolding] = []
        if previous_week is not None:
            previous_holdings_result = await db.execute(
                select(ModelPortfolioHolding)
                .where(ModelPortfolioHolding.week_id == previous_week.id)
                .order_by(ModelPortfolioHolding.rank.asc())
            )
            previous_holdings = list(previous_holdings_result.scalars().all())
        snapshots_result = await db.execute(
            select(ModelPortfolioDailySnapshot)
            .where(ModelPortfolioDailySnapshot.week_id == week.id)
            .order_by(ModelPortfolioDailySnapshot.date.asc())
        )
        snapshots = list(snapshots_result.scalars().all())

    changes = _summarize_week_changes(holdings, previous_holdings) if previous_holdings else None

    decision_band = _build_decision_band(
        week.review_notes if isinstance(week.review_notes, dict) else None,
        week.review_summary,
        changes,
    )

    return {
        "week": {
            "id": week.id,
            "week_start": week.week_start.isoformat(),
            "week_end": week.week_end.isoformat(),
            "status": week.status,
            "strategy_version": week.strategy_version,
            "portfolio_return_pct": week.portfolio_return_pct,
            "daily_return_pct": week.daily_return_pct,
            "benchmark_symbol": week.benchmark_symbol,
            "benchmark_entry": week.benchmark_entry,
            "benchmark_last": week.benchmark_last,
            "benchmark_return_pct": week.benchmark_return_pct,
            "active_return_spread": week.active_return_spread,
            "review_summary": week.review_summary,
            "review_notes": week.review_notes,
            "generation_notes": week.generation_notes,
            "reviewed_at": week.reviewed_at.isoformat() if week.reviewed_at else None,
        },
        "holdings": [
            {
                "id": holding.id,
                "symbol": holding.symbol,
                "name": holding.name,
                "sector": holding.sector,
                "allocation_pct": holding.allocation_pct,
                "entry_price": holding.entry_price,
                "current_price": holding.current_price,
                "weekly_return_pct": holding.weekly_return_pct,
                "daily_change_pct": holding.daily_change_pct,
                "technical_score": holding.technical_score,
                "fundamental_score": holding.fundamental_score,
                "sentiment_score": holding.sentiment_score,
                "overall_score": holding.overall_score,
                "recommendation": holding.recommendation,
                "rank": holding.rank,
                "rationale": holding.rationale,
            }
            for holding in holdings
        ],
        "snapshots": [
            {
                "date": snapshot.date.isoformat(),
                "total_return_pct": snapshot.total_return_pct,
                "daily_return_pct": snapshot.daily_return_pct,
                "benchmark_return_pct": snapshot.benchmark_return_pct,
                "active_return_spread": snapshot.active_return_spread,
                "positions_json": snapshot.positions_json,
            }
            for snapshot in snapshots
        ],
        "summary": {
            "holding_count": len(holdings),
            "best_holding": _extreme_holding(holdings, reverse=True),
            "worst_holding": _extreme_holding(holdings, reverse=False),
        },
        "changes": changes,
        "decision_band": decision_band,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_model_portfolio_history(limit: int = 12) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ModelPortfolioWeek).order_by(ModelPortfolioWeek.week_start.desc()).limit(limit)
        )
        weeks = list(result.scalars().all())
        holdings_result = await db.execute(
            select(ModelPortfolioHolding)
            .where(ModelPortfolioHolding.week_id.in_([week.id for week in weeks] or [-1]))
            .order_by(ModelPortfolioHolding.week_id.asc(), ModelPortfolioHolding.rank.asc())
        )
        holdings = list(holdings_result.scalars().all())

    holdings_by_week: dict[int, list[ModelPortfolioHolding]] = defaultdict(list)
    for holding in holdings:
        holdings_by_week[holding.week_id].append(holding)

    chronological_weeks = list(reversed(weeks))
    change_map: Optional[dict[int, dict[str, Any]]] = {}
    previous_week_holdings: list[ModelPortfolioHolding] = []
    for week in chronological_weeks:
        current_holdings = holdings_by_week.get(week.id, [])
        change_map[week.id] = _summarize_week_changes(current_holdings, previous_week_holdings) if previous_week_holdings else None
        previous_week_holdings = current_holdings

    return {
        "weeks": [
            {
                "id": week.id,
                "week_start": week.week_start.isoformat(),
                "week_end": week.week_end.isoformat(),
                "status": week.status,
                "portfolio_return_pct": week.portfolio_return_pct,
                "daily_return_pct": week.daily_return_pct,
                "benchmark_return_pct": week.benchmark_return_pct,
                "active_return_spread": week.active_return_spread,
                "review_summary": week.review_summary,
                "change_summary": change_map.get(week.id, {}).get("summary") if change_map.get(week.id) else None,
            }
            for week in weeks
        ],
        "count": len(weeks),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _extreme_holding(holdings: list[ModelPortfolioHolding], reverse: bool) -> Optional[dict[str, Any]]:
    valid = [holding for holding in holdings if holding.weekly_return_pct is not None]
    if not valid:
        return None
    selected = sorted(valid, key=lambda holding: holding.weekly_return_pct or 0, reverse=reverse)[0]
    return {
        "symbol": selected.symbol,
        "weekly_return_pct": selected.weekly_return_pct,
        "allocation_pct": selected.allocation_pct,
    }
