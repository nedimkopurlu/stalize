"""
Technical Analysis Service — Teknik Analiz Motoru

Tüm teknik indikatörleri hesaplar ve skor üretir.
Kullanılan kütüphane: ta (Technical Analysis Library)
"""
import pandas as pd
import ta
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, Optional, Tuple, List
import logging

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.price import PriceHistory

logger = logging.getLogger(__name__)


class TechnicalAnalysisEngine:
    """Comprehensive technical analysis engine for BIST stocks."""

    # ─── CALCULATE ALL INDICATORS ────────────────────────────────────────

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators on price DataFrame."""
        if len(df) < 50:
            logger.warning("Yetersiz veri, minimum 50 gün gerekli")
            return df

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # ── TREND INDICATORS ──
        # SMA
        df["sma_20"] = ta.trend.sma_indicator(close, window=20)
        df["sma_50"] = ta.trend.sma_indicator(close, window=50)
        df["sma_100"] = ta.trend.sma_indicator(close, window=100)
        df["sma_200"] = ta.trend.sma_indicator(close, window=200)

        # EMA
        df["ema_12"] = ta.trend.ema_indicator(close, window=12)
        df["ema_26"] = ta.trend.ema_indicator(close, window=26)
        df["ema_50"] = ta.trend.ema_indicator(close, window=50)
        df["ema_200"] = ta.trend.ema_indicator(close, window=200)

        # MACD
        macd = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_histogram"] = macd.macd_diff()

        # ADX
        adx = ta.trend.ADXIndicator(high, low, close, window=14)
        df["adx"] = adx.adx()
        df["adx_pos"] = adx.adx_pos()
        df["adx_neg"] = adx.adx_neg()

        # Ichimoku
        ichimoku = ta.trend.IchimokuIndicator(high, low, window1=9, window2=26, window3=52)
        df["ichimoku_a"] = ichimoku.ichimoku_a()
        df["ichimoku_b"] = ichimoku.ichimoku_b()
        df["ichimoku_base"] = ichimoku.ichimoku_base_line()
        df["ichimoku_conv"] = ichimoku.ichimoku_conversion_line()

        # ── MOMENTUM INDICATORS ──
        # RSI
        df["rsi_14"] = ta.momentum.rsi(close, window=14)

        # Stochastic RSI
        stoch_rsi = ta.momentum.StochRSIIndicator(close, window=14, smooth1=3, smooth2=3)
        df["stoch_rsi_k"] = stoch_rsi.stochrsi_k()
        df["stoch_rsi_d"] = stoch_rsi.stochrsi_d()

        # Williams %R
        df["williams_r"] = ta.momentum.williams_r(high, low, close, lbp=14)

        # CCI
        df["cci"] = ta.trend.cci(high, low, close, window=20)

        # MFI
        df["mfi"] = ta.volume.money_flow_index(high, low, close, volume, window=14)

        # ── VOLATILITY INDICATORS ──
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()
        df["bb_width"] = bb.bollinger_wband()
        df["bb_pband"] = bb.bollinger_pband()

        # ATR
        df["atr_14"] = ta.volatility.average_true_range(high, low, close, window=14)

        # Keltner Channel
        kc = ta.volatility.KeltnerChannel(high, low, close, window=20, window_atr=10)
        df["kc_upper"] = kc.keltner_channel_hband()
        df["kc_lower"] = kc.keltner_channel_lband()

        # ── VOLUME INDICATORS ──
        # OBV
        df["obv"] = ta.volume.on_balance_volume(close, volume)

        # VWAP (approximation using cumulative)
        df["vwap"] = (volume * (high + low + close) / 3).cumsum() / volume.cumsum()

        # A/D Line
        df["ad_line"] = ta.volume.acc_dist_index(high, low, close, volume)

        return df

    # ─── PATTERN RECOGNITION (FORMASYON AVCISI) ──────────────────────────
    
    def _detect_geometric_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """
        Geçmiş 60 gün içerisindeki lokal tepe ve dipleri scipy.signal ile bularak
        OBO, TOBO, İkili Tepe, İkili Dip gibi popüler formasyonları saptar.
        """
        patterns = []
        if len(df) < 60:
            return patterns

        # Son 60 günlük veriyi al
        recent_df = df.tail(60).copy()
        closes = recent_df['close'].values
        
        # Tepe ve Dipleri bul
        # Dipleri bulmak için veriyi ters çevirip find_peaks kullanıyoruz
        peaks, _ = find_peaks(closes, distance=10, prominence=0.05 * np.mean(closes))
        dips, _ = find_peaks(-closes, distance=10, prominence=0.05 * np.mean(closes))
        
        peak_prices = closes[peaks]
        dip_prices = closes[dips]
        
        # 1. İKİLİ DİP (Double Bottom) - W Formasyonu
        if len(dip_prices) >= 2:
            last_dip = dip_prices[-1]
            prev_dip = dip_prices[-2]
            # Son iki dip arasında %2'den az fark varsa ve şu anki fiyat bu diplerin üzerindeyse
            if abs(last_dip - prev_dip) / prev_dip < 0.02 and closes[-1] > last_dip * 1.03:
                patterns.append({
                    "type": "pattern",
                    "name": "İkili Dip (Double Bottom)",
                    "direction": "bullish",
                    "strength": 1.5  # Çok güçlü sinyal
                })

        # 2. İKİLİ TEPE (Double Top) - M Formasyonu
        if len(peak_prices) >= 2:
            last_peak = peak_prices[-1]
            prev_peak = peak_prices[-2]
            if abs(last_peak - prev_peak) / prev_peak < 0.02 and closes[-1] < last_peak * 0.97:
                patterns.append({
                    "type": "pattern",
                    "name": "İkili Tepe (Double Top)",
                    "direction": "bearish",
                    "strength": 1.5  # Çok güçlü düşüş sinyali
                })

        # 3. TOBO (Ters Omuz Baş Omuz) - Yükseliş
        if len(dip_prices) >= 3:
            d1, d2, d3 = dip_prices[-3], dip_prices[-2], dip_prices[-1]
            # Baş (Ortadaki) dip en derin olmalı, omuzlar nispeten benzer seviyede olmalı
            if d2 < d1 and d2 < d3 and abs(d1 - d3) / d1 < 0.04:
                patterns.append({
                    "type": "pattern",
                    "name": "TOBO Formasyonu",
                    "direction": "bullish",
                    "strength": 1.8  # Kritik yükseliş sinyali
                })

        # 4. OBO (Omuz Baş Omuz) - Düşüş
        if len(peak_prices) >= 3:
            p1, p2, p3 = peak_prices[-3], peak_prices[-2], peak_prices[-1]
            if p2 > p1 and p2 > p3 and abs(p1 - p3) / p1 < 0.04:
                patterns.append({
                    "type": "pattern",
                    "name": "OBO Formasyonu",
                    "direction": "bearish",
                    "strength": 1.8  # Kritik düşüş sinyali
                })

        return patterns

    # ─── SIGNAL DETECTION ────────────────────────────────────────────────

    def detect_signals(self, df: pd.DataFrame) -> Dict:
        """Detect trading signals from calculated indicators."""
        if len(df) < 5:
            return {"signals": [], "score": 50}

        signals = []
        
        # Geometrik Formasyon Taraması (Faz 10: Pattern Recognition)
        patterns = self._detect_geometric_patterns(df)
        signals.extend(patterns)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # ── RSI SIGNALS ──
        rsi = last.get("rsi_14")
        if rsi is not None:
            if rsi < 30:
                signals.append({"type": "momentum", "name": "RSI Aşırı Satım", "direction": "bullish", "strength": 0.8})
            elif rsi < 40:
                signals.append({"type": "momentum", "name": "RSI Düşük Bölge", "direction": "bullish", "strength": 0.4})
            elif rsi > 70:
                signals.append({"type": "momentum", "name": "RSI Aşırı Alım", "direction": "bearish", "strength": 0.8})
            elif rsi > 60:
                signals.append({"type": "momentum", "name": "RSI Yüksek Bölge", "direction": "bearish", "strength": 0.3})

        # ── MACD SIGNALS ──
        macd = last.get("macd")
        macd_sig = last.get("macd_signal")
        prev_macd = prev.get("macd")
        prev_macd_sig = prev.get("macd_signal")

        if all(v is not None for v in [macd, macd_sig, prev_macd, prev_macd_sig]):
            if prev_macd < prev_macd_sig and macd > macd_sig:
                signals.append({"type": "trend", "name": "MACD Bullish Crossover", "direction": "bullish", "strength": 0.7})
            elif prev_macd > prev_macd_sig and macd < macd_sig:
                signals.append({"type": "trend", "name": "MACD Bearish Crossover", "direction": "bearish", "strength": 0.7})

        # ── GOLDEN / DEATH CROSS ──
        sma50 = last.get("sma_50")
        sma200 = last.get("sma_200")
        prev_sma50 = prev.get("sma_50")
        prev_sma200 = prev.get("sma_200")

        if all(v is not None for v in [sma50, sma200, prev_sma50, prev_sma200]):
            if prev_sma50 < prev_sma200 and sma50 > sma200:
                signals.append({"type": "trend", "name": "Golden Cross (SMA50 > SMA200)", "direction": "bullish", "strength": 0.9})
            elif prev_sma50 > prev_sma200 and sma50 < sma200:
                signals.append({"type": "trend", "name": "Death Cross (SMA50 < SMA200)", "direction": "bearish", "strength": 0.9})

        # ── BOLLINGER BAND SIGNALS ──
        close = last.get("close")
        bb_lower = last.get("bb_lower")
        bb_upper = last.get("bb_upper")
        bb_width = last.get("bb_width")

        if all(v is not None for v in [close, bb_lower, bb_upper]):
            if close < bb_lower:
                signals.append({"type": "volatility", "name": "Fiyat Bollinger Alt Bandı Altında", "direction": "bullish", "strength": 0.6})
            elif close > bb_upper:
                signals.append({"type": "volatility", "name": "Fiyat Bollinger Üst Bandı Üstünde", "direction": "bearish", "strength": 0.6})

        # Bollinger Squeeze
        if bb_width is not None:
            bb_width_20 = df["bb_width"].tail(20)
            if bb_width < bb_width_20.quantile(0.1):
                signals.append({"type": "volatility", "name": "Bollinger Squeeze (Sıkışma)", "direction": "neutral", "strength": 0.5})

        # ── TREND POSITION ──
        if all(v is not None for v in [close, sma50, sma200]):
            if close > sma50 > sma200:
                signals.append({"type": "trend", "name": "Güçlü Yükseliş Trendi (Fiyat > SMA50 > SMA200)", "direction": "bullish", "strength": 0.7})
            elif close < sma50 < sma200:
                signals.append({"type": "trend", "name": "Güçlü Düşüş Trendi (Fiyat < SMA50 < SMA200)", "direction": "bearish", "strength": 0.7})

        # ── ADX TREND STRENGTH ──
        adx = last.get("adx")
        if adx is not None:
            if adx > 25:
                signals.append({"type": "trend", "name": f"Güçlü Trend (ADX={adx:.1f})", "direction": "neutral", "strength": 0.5})

        # ── SUPPORT / RESISTANCE ──
        recent_20 = df.tail(20)
        support = recent_20["low"].min()
        resistance = recent_20["high"].max()
        if close is not None:
            dist_to_support = ((close - support) / close) * 100
            dist_to_resistance = ((resistance - close) / close) * 100

            if dist_to_support < 2:
                signals.append({"type": "support_resistance", "name": f"Destek Yakın ({support:.2f})", "direction": "bullish", "strength": 0.5})
            if dist_to_resistance < 2:
                signals.append({"type": "support_resistance", "name": f"Direnç Yakın ({resistance:.2f})", "direction": "bearish", "strength": 0.5})

        div = self._detect_rsi_divergence(df)
        if div is not None:
            signals.append(div)

        return {
            "signals": signals,
            "support": float(support) if support is not None else None,
            "resistance": float(resistance) if resistance is not None else None,
        }

    # ─── EMA TREND SCORE (MIDT-01) ──────────────────────────────────────────

    def _compute_ema_trend_score(self, df: pd.DataFrame) -> float:
        """EMA 50/200 trend skoru hesapla (MIDT-01). 0-50 arası float döner.

        Puanlama kuralları:
        - close > ema_200:   +20 taban puan
        - ema_50 > ema_200:  +15 ek puan (golden cross zonu)
        - momentum bonus:    ((close - ema_200) / ema_200).clip(0, 0.10) * 150 → 0-15 puan
        - toplam aralık:    0-50 puan
        - ema_200 veya ema_50 NaN ise 0.0 döner (yetersiz veri)
        """
        if "ema_200" not in df.columns or "ema_50" not in df.columns:
            return 0.0

        last = df.iloc[-1]
        ema_200 = last.get("ema_200")
        ema_50 = last.get("ema_50")
        close = last.get("close")

        # NaN kontrolü
        if ema_200 is None or ema_50 is None or close is None:
            return 0.0
        try:
            ema_200 = float(ema_200)
            ema_50 = float(ema_50)
            close = float(close)
        except (TypeError, ValueError):
            return 0.0
        if pd.isna(ema_200) or pd.isna(ema_50) or pd.isna(close):
            return 0.0

        score = 0.0

        if close > ema_200:
            score += 20.0  # taban: fiyat uzun vadeli trendin üstünde

            if ema_50 > ema_200:
                score += 15.0  # golden cross zonu

            # Momentum bonus: (close - ema_200) / ema_200, [0, 0.10] aralığına sınırlandırılır
            momentum_ratio = (close - ema_200) / ema_200
            momentum_ratio = max(0.0, min(0.10, momentum_ratio))
            score += momentum_ratio * 150.0  # 0-15 puan arası

        return round(score, 4)

    # ─── SCORE CALCULATION ────────────────────────────────────────────

    def calculate_score(self, df: pd.DataFrame, signals: Dict) -> Tuple[float, str]:
        """Teknik analiz skoru hesapla (0-100) ve öneriyi belirle.

        Sinyal bazlı skor ile EMA trend skorunu harmanlar:
        - signal_score:      sinyal dengesinden 0-100 arası
        - ema_component:     _compute_ema_trend_score() dan 0-50 arası
        - ema_normalized:    ema_component * 2  → 0-100 arası
        - blended:           signal_score * 0.6 + ema_normalized * 0.4, [0, 100]'e sınırlandırılır
        """
        if not signals.get("signals"):
            return 50.0, "TUT"

        bullish_score = 0
        bearish_score = 0
        total_weight = 0

        for sig in signals["signals"]:
            strength = sig["strength"]
            if sig["direction"] == "bullish":
                bullish_score += strength
            elif sig["direction"] == "bearish":
                bearish_score += strength
            total_weight += strength

        if total_weight == 0:
            return 50.0, "TUT"

        # Sinyal bazlı 0-100 skoru
        net_score = (bullish_score - bearish_score) / total_weight
        signal_score = 50 + (net_score * 50)
        signal_score = max(0.0, min(100.0, signal_score))

        # EMA trend bileşeni (0-50) → normalize edilmiş 0-100
        ema_component = self._compute_ema_trend_score(df)
        ema_normalized = ema_component * 2.0  # 0-100'e normalize

        # ATR volatilite düzeltmesi: yüksek volatilite riski artırır → skoru düşürür
        atr_adjustment = 0.0
        if "atr_14" in df.columns and "close" in df.columns:
            last_atr = df["atr_14"].iloc[-1]
            last_close = df["close"].iloc[-1]
            if not pd.isna(last_atr) and not pd.isna(last_close) and last_close > 0:
                atr_pct = float(last_atr) / float(last_close)  # ATR as % of price
                # Penalty for high volatility: >5% ATR pulls score toward neutral
                if atr_pct > 0.05:
                    atr_adjustment = -min((atr_pct - 0.05) * 100, 10.0)

        # Harmanlama: sinyal %60 + EMA %40 + ATR ayarlaması
        blended = signal_score * 0.6 + ema_normalized * 0.4 + atr_adjustment
        score = round(max(0.0, min(100.0, blended)), 2)

        # Öneri belirleme
        if score >= 80:
            rec = "GÜÇLÜ AL"
        elif score >= 65:
            rec = "AL"
        elif score >= 40:
            rec = "TUT"
        elif score >= 20:
            rec = "SAT"
        else:
            rec = "GÜÇLÜ SAT"

        return score, rec

    # ─── RISK LEVELS (SGNL-01) ───────────────────────────────────────────

    def _compute_stop_loss(self, df: pd.DataFrame) -> Optional[float]:
        """ATR bazlı stop-loss (SGNL-01): close - (2 * ATR14)."""
        if len(df) < 1:
            return None
        last_close = df["close"].iloc[-1]
        atr = df["atr_14"].iloc[-1] if "atr_14" in df.columns else None
        if pd.isna(last_close) or atr is None or pd.isna(atr):
            return None
        return round(float(last_close) - 2 * float(atr), 2)

    def _compute_target_price(self, df: pd.DataFrame) -> Optional[float]:
        """İlk direnç (SGNL-01): son 20 bar içindeki last_close üstündeki en yüksek high."""
        if len(df) < 1:
            return None
        last_close = df["close"].iloc[-1]
        if pd.isna(last_close):
            return None
        window = df["high"].tail(20)
        above = window[window > float(last_close)]
        if len(above) == 0:
            return None
        return round(float(above.max()), 2)

    # ─── RSI DIVERGENCE (SGNL-03) ────────────────────────────────────────

    def _detect_rsi_divergence(self, df: pd.DataFrame) -> Optional[Dict]:
        """RSI-fiyat divergence tespiti (SGNL-03).

        Son 20 barda iki lokal extrema karşılaştırılır:
          - Bullish: fiyat lower-low yaparken RSI higher-low → reversal yukarı
          - Bearish: fiyat higher-high yaparken RSI lower-high → reversal aşağı
        Eğer yalnızca bir formel dip/tepe varsa, son nokta da karşılaştırma noktası
        olarak kullanılır (trending seriler için).
        Yoksa None döner.
        """
        window = df.tail(20)
        if len(window) < 6 or "rsi_14" not in window.columns:
            return None
        closes = window["close"].dropna().values
        rsis = window["rsi_14"].dropna().values
        if len(closes) < 6 or len(rsis) < 6 or len(closes) != len(rsis):
            return None

        # Son 2 lokal minimum (dip) ve maksimum (tepe) indislerini bul.
        dips_idx, _ = find_peaks(-closes, distance=2)
        peaks_idx, _ = find_peaks(closes, distance=2)

        last_idx = len(closes) - 1

        # Bullish divergence: iki dip — fiyat daha düşük, RSI daha yüksek
        # İki formel dip varsa onları kullan; yalnızca bir dip varsa son noktayı da dip olarak değerlendir.
        bullish_pairs = []
        if len(dips_idx) >= 2:
            bullish_pairs.append((dips_idx[-2], dips_idx[-1]))
        if len(dips_idx) >= 1 and dips_idx[-1] != last_idx:
            bullish_pairs.append((dips_idx[-1], last_idx))

        for d1, d2 in bullish_pairs:
            if closes[d2] < closes[d1] and rsis[d2] > rsis[d1]:
                return {
                    "type": "divergence",
                    "name": "RSI Bullish Divergence",
                    "direction": "bullish",
                    "strength": 0.6,
                }

        # Bearish divergence: iki tepe — fiyat daha yüksek, RSI daha düşük
        bearish_pairs = []
        if len(peaks_idx) >= 2:
            bearish_pairs.append((peaks_idx[-2], peaks_idx[-1]))
        if len(peaks_idx) >= 1 and peaks_idx[-1] != last_idx:
            bearish_pairs.append((peaks_idx[-1], last_idx))

        for p1, p2 in bearish_pairs:
            if closes[p2] > closes[p1] and rsis[p2] < rsis[p1]:
                return {
                    "type": "divergence",
                    "name": "RSI Bearish Divergence",
                    "direction": "bearish",
                    "strength": 0.6,
                }

        return None

    # ─── ANALYZE SINGLE STOCK ────────────────────────────────────────────

    async def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """Run full technical analysis for a single stock."""
        async with AsyncSessionLocal() as db:
            # Get stock
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            if not stock:
                logger.warning(f"Hisse bulunamadı: {symbol}")
                return None

            # Get price data
            prices_result = await db.execute(
                select(PriceHistory)
                .where(PriceHistory.stock_id == stock.id)
                .order_by(PriceHistory.date.asc())
            )
            prices = prices_result.scalars().all()

            if len(prices) < 50:
                logger.warning(f"{symbol}: Yetersiz fiyat verisi ({len(prices)} gün)")
                return None

            # Build DataFrame
            data = {
                "date": [p.date for p in prices],
                "open": [p.open for p in prices],
                "high": [p.high for p in prices],
                "low": [p.low for p in prices],
                "close": [p.close for p in prices],
                "volume": [p.volume or 0 for p in prices],
            }
            df = pd.DataFrame(data)

            # Calculate indicators
            df = self.calculate_indicators(df)

            # Detect signals
            signals = self.detect_signals(df)

            # Calculate score
            score, recommendation = self.calculate_score(df, signals)

            # Update stock with technical score
            stock.technical_score = score

            # Update last N price records with indicator values
            for i, price in enumerate(prices[-min(30, len(prices)):]):
                idx = len(df) - min(30, len(prices)) + i
                if idx >= 0 and idx < len(df):
                    row = df.iloc[idx]
                    price.sma_20 = float(row["sma_20"]) if pd.notna(row.get("sma_20")) else None
                    price.sma_50 = float(row["sma_50"]) if pd.notna(row.get("sma_50")) else None
                    price.sma_200 = float(row["sma_200"]) if pd.notna(row.get("sma_200")) else None
                    price.ema_12 = float(row["ema_12"]) if pd.notna(row.get("ema_12")) else None
                    price.ema_26 = float(row["ema_26"]) if pd.notna(row.get("ema_26")) else None
                    price.rsi_14 = float(row["rsi_14"]) if pd.notna(row.get("rsi_14")) else None
                    price.macd = float(row["macd"]) if pd.notna(row.get("macd")) else None
                    price.macd_signal = float(row["macd_signal"]) if pd.notna(row.get("macd_signal")) else None
                    price.macd_histogram = float(row["macd_histogram"]) if pd.notna(row.get("macd_histogram")) else None
                    price.bb_upper = float(row["bb_upper"]) if pd.notna(row.get("bb_upper")) else None
                    price.bb_middle = float(row["bb_middle"]) if pd.notna(row.get("bb_middle")) else None
                    price.bb_lower = float(row["bb_lower"]) if pd.notna(row.get("bb_lower")) else None
                    price.atr_14 = float(row["atr_14"]) if pd.notna(row.get("atr_14")) else None
                    price.obv = float(row["obv"]) if pd.notna(row.get("obv")) else None

            await db.commit()

            stop_loss = self._compute_stop_loss(df)
            target_price = self._compute_target_price(df)

            def _build_ema_series(column: str) -> list:
                """Convert an EMA column to [{date, value}] list, dropping NaN rows."""
                result = []
                for _, row in df.iterrows():
                    val = row.get(column)
                    if val is not None and not pd.isna(val):
                        date_val = row["date"]
                        result.append({
                            "date": date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val),
                            "value": round(float(val), 4),
                        })
                return result

            last = df.iloc[-1]
            return {
                "symbol": symbol,
                "score": score,
                "recommendation": recommendation,
                "signals": signals["signals"],
                "support": signals.get("support"),
                "resistance": signals.get("resistance"),
                "stop_loss": stop_loss,
                "target_price": target_price,
                "indicators": {
                    "last_close": float(last["close"]) if pd.notna(last.get("close")) else None,
                    "rsi_14": float(last["rsi_14"]) if pd.notna(last.get("rsi_14")) else None,
                    "macd": float(last["macd"]) if pd.notna(last.get("macd")) else None,
                    "macd_signal": float(last["macd_signal"]) if pd.notna(last.get("macd_signal")) else None,
                    "adx": float(last["adx"]) if pd.notna(last.get("adx")) else None,
                    "bb_width": float(last["bb_width"]) if pd.notna(last.get("bb_width")) else None,
                    "sma_50": float(last["sma_50"]) if pd.notna(last.get("sma_50")) else None,
                    "sma_200": float(last["sma_200"]) if pd.notna(last.get("sma_200")) else None,
                    "ema_trend_score": self._compute_ema_trend_score(df),
                },
                "ema_50": _build_ema_series("ema_50"),
                "ema_200": _build_ema_series("ema_200"),
            }

    # ─── ANALYZE ALL STOCKS ──────────────────────────────────────────────

    async def analyze_all(self):
        """Run technical analysis for all BIST100 stocks."""
        logger.info("📊 Teknik analiz başlıyor (tüm BIST100)...")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock.symbol).where(Stock.is_active))
            symbols = [row[0] for row in result.fetchall()]

        results = []
        for symbol in symbols:
            try:
                result = await self.analyze_stock(symbol)
                if result:
                    results.append(result)
                    logger.info(f"  📊 {symbol}: Skor={result['score']}, Sinyal={result['recommendation']}")
            except Exception as e:
                logger.error(f"  ❌ {symbol} teknik analiz hatası: {e}")

        logger.info(f"✅ Teknik analiz tamamlandı ({len(results)}/{len(symbols)} hisse)")
        return results


# Singleton
technical_engine = TechnicalAnalysisEngine()


# ─── SGNL-02: VOLUME RATIO HELPER ─────────────────────────────────────

def compute_volume_ratio(current: Optional[int], avg_20d: Optional[float]) -> Optional[float]:
    """20-günlük ortalama hacme göre normalize edilmiş oran.

    Args:
        current: Bugünkü (son) hacim
        avg_20d: Son 20 günün ortalama hacmi

    Returns:
        Oran (2.4 → "2.4x"); current veya avg_20d eksikse/sıfırsa None.
    """
    if current is None or avg_20d is None:
        return None
    try:
        avg_f = float(avg_20d)
    except (TypeError, ValueError):
        return None
    if avg_f <= 0:
        return None
    return round(float(current) / avg_f, 2)
