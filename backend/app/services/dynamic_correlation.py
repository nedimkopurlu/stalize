"""
Dinamik Korelasyon Matrisi & Kriz Modu (Faz 9.6)

Hisse senedi fiyat korelasyonlarını dinamik olarak hesapla:
1. Rolling window (30/60/90 gün) korelasyon matrisi
2. Volatilite artışında "Kriz Modu" tetikle
3. Portföy çeşitlendirme tavsiyesi

Örnek:
- Normal: THYAO ve PGSUS korelasyon 0.35 (düşük)
- Kriz: THYAO ve PGSUS korelasyon 0.85 (yüksek - tüm hisseler aynı yönde hareket)
- Tavsiye: Kriz döneminde daha fazla çeşitlendirme yapın
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, desc

from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.price import PriceHistory

logger = logging.getLogger(__name__)


class DynamicCorrelationMatrix:
    """
    Runtime Korelasyon Matrisi ve Kriz Modu Motoru

    Görevler:
    1. Hisse fiyatları → korelasyon matrisi hesapla
    2. Volatilite takibi
    3. Kriz modu tespiti (volatilite spike)
    4. Portföy diversifikasyon tavsiyesi
    """

    def __init__(
        self,
        windows_days: List[int] = [30, 60, 90],
        volatility_threshold: float = 3.0,  # Standart sapmanın 3 katı
        correlation_threshold_crisis: float = 0.75,  # Kriz: korelasyon > 0.75
    ):
        self.windows_days = windows_days
        self.volatility_threshold = volatility_threshold
        self.correlation_threshold_crisis = correlation_threshold_crisis
        self.last_computed = None
        self.crisis_mode = False

    async def compute_correlation_matrix(
        self, window_days: int = 30, symbols: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Belirtilen gün sayısı için korelasyon matrisini hesapla.

        Args:
            window_days: 30, 60, veya 90
            symbols: BIST100 sembolleri (None = tüm 100)

        Returns:
            {
                "window_days": 30,
                "computed_at": "2026-04-15T...",
                "correlation_matrix": {
                    "THYAO": {"PGSUS": 0.35, "EREGL": 0.42, ...},
                    "PGSUS": {...},
                    ...
                },
                "statistics": {
                    "mean_correlation": 0.45,
                    "max_correlation": 0.92,
                    "min_correlation": -0.15,
                    "crisis_detected": False,
                    "avg_volatility_pct": 2.3
                }
            }
        """
        try:
            async with AsyncSessionLocal() as db:
                # Semboller
                if symbols is None:
                    stock_result = await db.execute(select(Stock))
                    stocks = stock_result.scalars().all()
                    symbols = [s.symbol for s in stocks]

                logger.info(f"📊 {window_days}-gün korelasyon matrisi hesaplanıyor ({len(symbols)} hisse)...")

                # Fiyat geçmişi çek
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=window_days)

                price_result = await db.execute(
                    select(PriceHistory)
                    .filter(PriceHistory.date >= cutoff_date)
                    .order_by(desc(PriceHistory.date))
                )

                all_prices = price_result.scalars().all()

                if not all_prices:
                    logger.warning("Fiyat verisi bulunamadı")
                    return None

                # DataFrame'e dönüştür
                df = pd.DataFrame([
                    {
                        "symbol": p.stock.symbol,
                        "date": p.date,
                        "close": p.close
                    }
                    for p in all_prices
                    if p.stock and p.stock.symbol in symbols
                ])

                if df.empty:
                    logger.warning("DataFrame boş")
                    return None

                # Pivot: Her hisse için ayrı sütun
                df_pivot = df.pivot(index="date", columns="symbol", values="close")

                # NaN değerleri doldur (forward fill)
                df_pivot = df_pivot.ffill().dropna()

                if df_pivot.empty or len(df_pivot) < 10:
                    logger.warning("Yeterli veri yok")
                    return None

                # Returns hesapla (log returns)
                returns = np.log(df_pivot / df_pivot.shift(1)).dropna()

                # Korelasyon matrisi
                corr_matrix = returns.corr()

                # İstatistikler
                stats = self._compute_statistics(returns, corr_matrix)

                # Kriz modu tespiti
                crisis = await self._detect_crisis(stats)

                if crisis:
                    logger.warning("⚠️ KRİZ MODU TETİKLENDİ!")
                    self.crisis_mode = True
                else:
                    self.crisis_mode = False

                # Korelasyon matrisini dict'e çevir
                corr_dict = {
                    symbol: {
                        other: round(float(corr_matrix.loc[symbol, other]), 3)
                        for other in corr_matrix.columns
                    }
                    for symbol in corr_matrix.columns
                }

                self.last_computed = datetime.now(timezone.utc)

                return {
                    "window_days": window_days,
                    "computed_at": datetime.now(timezone.utc).isoformat(),
                    "correlation_matrix": corr_dict,
                    "statistics": stats,
                    "crisis_mode": crisis,
                }

        except Exception as e:
            logger.error(f"Korelasyon matrisi hesaplama hatası: {e}")
            return None

    def _compute_statistics(self, returns: pd.DataFrame, corr_matrix: pd.DataFrame) -> Dict:
        """Korelasyon ve volatilite istatistikleri hesapla."""
        try:
            # Korelasyon istatistikleri
            corr_values = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]

            mean_corr = float(np.mean(corr_values))
            max_corr = float(np.max(corr_values))
            min_corr = float(np.min(corr_values))

            # Volatilite (standart sapma × 100)
            volatilities = returns.std() * 100
            mean_volatility = float(volatilities.mean())
            max_volatility = float(volatilities.max())

            return {
                "mean_correlation": round(mean_corr, 3),
                "max_correlation": round(max_corr, 3),
                "min_correlation": round(min_corr, 3),
                "mean_volatility_pct": round(mean_volatility, 2),
                "max_volatility_pct": round(max_volatility, 2),
                "num_stocks": len(returns.columns),
                "num_observations": len(returns),
            }

        except Exception as e:
            logger.error(f"İstatistik hesaplama hatası: {e}")
            return {}

    async def _detect_crisis(self, stats: Dict) -> bool:
        """
        Kriz modu tespiti.

        Kurallar:
        - Volatilite > 4% ve artan trend
        - Ortalama korelasyon > 0.75
        """
        try:
            mean_vol = stats.get("mean_volatility_pct", 0)
            max_vol = stats.get("max_volatility_pct", 0)
            mean_corr = stats.get("mean_correlation", 0)

            # Basit kriz kuralları
            high_volatility = mean_vol > 4.0
            high_correlation = mean_corr > self.correlation_threshold_crisis
            volatility_spike = max_vol > mean_vol * 1.5

            crisis = high_volatility and (high_correlation or volatility_spike)

            logger.info(
                f"🔍 Kriz Tespiti: vol={mean_vol:.1f}%, corr={mean_corr:.2f}, crisis={crisis}"
            )

            return crisis

        except Exception as e:
            logger.error(f"Kriz tespiti hatası: {e}")
            return False

    async def get_diversification_recommendations(self) -> Dict:
        """
        Portföy çeşitlendirme tavsiyesi.

        Kriz modunda:
        - Yüksek korelasyonlu hisseleri azalt
        - Düşük/negatif korelasyonlu hisseleri ekle

        Normal modunda:
        - Standart modern portföy teorisi
        """
        try:
            corr_matrix = await self.compute_correlation_matrix(window_days=30)

            if not corr_matrix:
                return {}

            stats = corr_matrix.get("statistics", {})
            crisis = corr_matrix.get("crisis_mode", False)

            recommendations = {
                "mode": "crisis" if crisis else "normal",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "statistics": stats,
            }

            if crisis:
                recommendations["actions"] = [
                    "⚠️ Kriz Modu Aktif: Tüm hisseler aynı yönde hareket ediyor",
                    "🔄 Yüksek korelasyonlu hisse çiftlerini azalt",
                    "📍 Düşük korelasyonlu sektörlere yatırım yap (örn. savunma, kamu)",
                    "💰 Nakit oranını %20'ye çıkar",
                ]
            else:
                recommendations["actions"] = [
                    "✅ Normal Pazar Koşulları",
                    "📊 Klasik Markowitz portföy optimizasyonu kullan",
                    "🎯 Beklenen getiri ve risk dengesini sağla",
                    "📈 Sektör çeşitlendirmesi yap (BIST30 ve küçük caplar)",
                ]

            return recommendations

        except Exception as e:
            logger.error(f"Diversifikasyon tavsiyesi hatası: {e}")
            return {}

    async def find_low_correlation_pairs(self, correlation_threshold: float = 0.3) -> List[Tuple[str, str, float]]:
        """
        Düşük korelasyonlu hisse çiftlerini bul (çeşitlendirme için).

        Returns:
            [
                ("THYAO", "PGSUS", 0.15),  # Düşük korelasyon = iyi çeşitlendirme
                ("EREGL", "MAVI", 0.22),
                ...
            ]
        """
        try:
            corr_matrix = await self.compute_correlation_matrix(window_days=60)

            if not corr_matrix:
                return []

            corr_dict = corr_matrix.get("correlation_matrix", {})

            pairs = []

            for stock1 in corr_dict:
                for stock2, correlation in corr_dict[stock1].items():
                    if stock1 < stock2:  # Duplikasyon önle
                        if abs(correlation) < correlation_threshold:
                            pairs.append((stock1, stock2, correlation))

            # Korelasyona göre sırala (en düşük önce)
            pairs.sort(key=lambda x: abs(x[2]))

            logger.info(f"✅ {len(pairs)} düşük korelasyonlu çift bulundu (< {correlation_threshold})")

            return pairs[:20]  # İlk 20'yi döndür

        except Exception as e:
            logger.error(f"Düşük korelasyon çiftleri hatası: {e}")
            return []


# Singleton instance
correlation_engine = DynamicCorrelationMatrix()


async def run_dynamic_correlation_scan() -> Dict:
    """
    Dinamik korelasyon analizi (arka plan görevi).
    APScheduler tarafından pazartesi saat 9'da çağrılır.
    """
    logger.info("📊 Dinamik Korelasyon Matrisi Taraması Başlıyor...")

    try:
        # 30-gün korelasyon
        corr_30 = await correlation_engine.compute_correlation_matrix(window_days=30)

        # 60-gün korelasyon
        corr_60 = await correlation_engine.compute_correlation_matrix(window_days=60)

        # Çeşitlendirme önerileri
        recommendations = await correlation_engine.get_diversification_recommendations()

        # Düşük korelasyon çiftleri
        low_corr_pairs = await correlation_engine.find_low_correlation_pairs(correlation_threshold=0.3)

        logger.info(f"✅ Korelasyon Taraması Tamamlandı")
        logger.info(f"🔗 {len(low_corr_pairs)} düşük korelasyon çifti önerilendi")

        if correlation_engine.crisis_mode:
            logger.warning("⚠️⚠️⚠️ KRİZ MODU UYARISI ⚠️⚠️⚠️")
            logger.warning(f"Mean Korelasyon: {corr_30.get('statistics', {}).get('mean_correlation', 'N/A')}")

        return {
            "corr_30": corr_30,
            "corr_60": corr_60,
            "recommendations": recommendations,
            "low_correlation_pairs": low_corr_pairs,
            "crisis_mode": correlation_engine.crisis_mode,
        }

    except Exception as e:
        logger.error(f"Korelasyon taraması başarısız: {e}")
        return {}
