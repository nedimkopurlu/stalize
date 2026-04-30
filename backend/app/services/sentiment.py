"""
Sentiment Analysis Service
Fetches related news and calculates sentiment scores.
"""
import logging
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.stock import Stock

logger = logging.getLogger(__name__)

class SentimentAnalysisEngine:
    def __init__(self):
        pass

    async def analyze_stock(self, db: AsyncSession, stock: Stock) -> float:
        """
        Fetches latest news for a stock, calculates average sentiment,
        updates the stock and saves to db.
        Returns the sentiment score (0-100).
        """
        try:
            ticker = yf.Ticker(stock.yahoo_symbol)
            news_items = ticker.news
            
            if not news_items:
                # If no news recently, default to neutral sentiment
                default_score = 50.0
                if stock.sentiment_score is None:
                    stock.sentiment_score = default_score
                    await db.commit()
                return default_score
                
            total_score = 0.0
            total_weight = 0.0
            count = 0
            
            for item in news_items[:10]: # Analyze up to top 10 latest news
                content = item.get('content', {})
                title = content.get('title', '')
                summary = content.get('summary', '')
                
                text_to_analyze = f"{title}. {summary}"
                if text_to_analyze.strip() == ".":
                    continue

                # Kural tabanlı varsayılan duygu skoru.
                # Pozitif/negatif anahtar kelime tespiti ile basit kural tabanlı skor
                text_lower = (title + " " + summary).lower()
                pos_words = ["artış", "yükseliş", "kar", "büyüme", "güçlü", "rekor", "olumlu"]
                neg_words = ["düşüş", "kayıp", "zarar", "zayıf", "risk", "olumsuz", "daralma"]
                pos_count = sum(1 for w in pos_words if w in text_lower)
                neg_count = sum(1 for w in neg_words if w in text_lower)
                raw_score = 0.0 + (pos_count * 0.2) - (neg_count * 0.2)
                raw_score = max(-1.0, min(1.0, raw_score))
                analysis = {"sentiment_score": raw_score, "importance_score": 1.0}
                normalized_score = (analysis["sentiment_score"] + 1.0) / 2.0 * 100.0
                weight = max(0.1, float(analysis["importance_score"]))

                total_score += normalized_score * weight
                total_weight += weight
                count += 1
                
            if count == 0:
                return 50.0
                
            average_sentiment = total_score / total_weight if total_weight > 0 else 50.0
            
            # Apply a smoothing factor so sudden news doesn't swing score violently
            # if we already have a previous score.
            current_score = stock.sentiment_score or 50.0
            smoothed_score = (average_sentiment * 0.6) + (current_score * 0.4)
            
            stock.sentiment_score = smoothed_score
            stock.last_data_update = datetime.now(timezone.utc)
            
            await db.commit()
            
            logger.info(f"Sentiment analysis completed for {stock.symbol} (Score: {smoothed_score:.1f} from {count} news)")
            return smoothed_score
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {stock.symbol}: {e}")
            return 50.0
