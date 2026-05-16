"""
Fundamental Analysis Service
Fetches and calculates fundamental data using yfinance.
"""
import logging
import math
from typing import Dict, Any, Optional
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.models.stock import Stock
from app.models.fundamental import Fundamental

logger = logging.getLogger(__name__)

class FundamentalAnalysisEngine:
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            val = float(value)
            if val != val or not math.isfinite(val):  # check for NaN/inf
                return None
            return val
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _calculate_score(metrics: Dict[str, Optional[float]]) -> float:
        """
        Calculates a fundamental score (0-100) based on value and profitability metrics.
        """
        score = 50.0  # Base score
        
        pe = metrics.get('pe_ratio')
        pb = metrics.get('pb_ratio')
        roe = metrics.get('roe')
        debt_to_equity = metrics.get('debt_to_equity')
        net_margin = metrics.get('net_margin')
        
        # Valuation (PE Ratio)
        if pe is not None and pe > 0:
            if pe < 10:
                score += 15
            elif pe < 20:
                score += 5
            elif pe > 30:
                score -= 10
                
        # Valuation (PB Ratio)
        if pb is not None and pb > 0:
            if pb < 1.5:
                score += 10
            elif pb < 3:
                score += 5
            elif pb > 5:
                score -= 5
                
        # Profitability (ROE) - note: yfinance ROE is often in decimal (e.g. 0.15 = 15%)
        if roe is not None:
            if roe > 0.15:
                score += 15
            elif roe > 0.05:
                score += 5
            elif roe < 0:
                score -= 15
                
        # Profitability (Net Margin)
        if net_margin is not None:
            if net_margin > 0.15:
                score += 10
            elif net_margin > 0.05:
                score += 5
            elif net_margin < 0:
                score -= 10
                
        # Financial Health (Debt to Equity)
        if debt_to_equity is not None:
            if debt_to_equity < 50:  # yfinance returns this as %, so 50 = 50%
                score += 10
            elif debt_to_equity > 150:
                score -= 10

        return max(0.0, min(100.0, score))

    async def analyze_stock(self, db: AsyncSession, stock: Stock) -> Optional[Fundamental]:
        """
        Fetches fundamental data for a specific stock, calculates the score
        and saves it to the database.
        """
        try:
            ticker = yf.Ticker(stock.yahoo_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info and 'previousClose' not in info and 'trailingPE' not in info:
                logger.warning(f"No valid fundamental info found for {stock.symbol}")
                return None
            
            # Extract metrics
            metrics = {
                'pe_ratio': self._safe_float(info.get('trailingPE') or info.get('forwardPE')),
                'pb_ratio': self._safe_float(info.get('priceToBook')),
                'ev_ebitda': self._safe_float(info.get('enterpriseToEbitda')),
                'eps': self._safe_float(info.get('trailingEps')),
                'market_cap': self._safe_float(info.get('marketCap')),
                
                'roe': self._safe_float(info.get('returnOnEquity')),
                'roa': self._safe_float(info.get('returnOnAssets')),
                'net_margin': self._safe_float(info.get('profitMargins')),
                'gross_margin': self._safe_float(info.get('grossMargins')),
                'ebitda_margin': self._safe_float(info.get('ebitdaMargins')),
                'operating_margin': self._safe_float(info.get('operatingMargins')),
                
                'current_ratio': self._safe_float(info.get('currentRatio')),
                'quick_ratio': self._safe_float(info.get('quickRatio')),
                'debt_to_equity': self._safe_float(info.get('debtToEquity')),
                'free_cash_flow': self._safe_float(info.get('freeCashflow')),
                
                'revenue': self._safe_float(info.get('totalRevenue')),
                'revenue_growth_yoy': self._safe_float(info.get('revenueGrowth')),
                'earnings_growth_yoy': self._safe_float(info.get('earningsGrowth')),
                'net_income': self._safe_float(info.get('netIncomeToCommon')),
                
                'dividend_yield': self._safe_float(info.get('dividendYield')),
                'dividend_payout_ratio': self._safe_float(info.get('payoutRatio')),
            }
            
            score = self._calculate_score(metrics)
            
            # Use current year as period (simplified for initial implementation)
            current_year = str(datetime.now(timezone.utc).year)
            period = f"{current_year}-Current"
            
            # Upsert fundamental record
            query = select(Fundamental).where(
                Fundamental.stock_id == stock.id,
                Fundamental.period == period,
                Fundamental.period_type == "ttm"
            )
            result = await db.execute(query)
            fundamental = result.scalars().first()
            
            if not fundamental:
                fundamental = Fundamental(
                    stock_id=stock.id,
                    period=period,
                    period_type="ttm"
                )
                db.add(fundamental)
            
            # Update fields
            for key, value in metrics.items():
                if hasattr(fundamental, key):
                    setattr(fundamental, key, value)
            
            fundamental.fundamental_score = score
            
            # Also update the stock's cached fundamental score
            stock.fundamental_score = score
            
            await db.commit()
            
            logger.info(f"Fundamental analysis completed for {stock.symbol} (Score: {score:.1f})")
            return fundamental
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis for {stock.symbol}: {e}")
            await db.rollback()
            return None
