"""
News & Sentiment model — Haberler ve duygu analizi
"""
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NewsItem(Base):
    """A news article with sentiment analysis results."""
    __tablename__ = "news_items"
    __table_args__ = (
        UniqueConstraint("source", "url", name="uq_news_source_url"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True, index=True)  # nullable for general market news

    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    source = Column(String(100), nullable=True)  # Reuters, Bloomberg HT, KAP, etc.
    language = Column(String(10), default="tr")  # tr, en
    category = Column(String(50), nullable=True)  # geopolitics, macro, sector, company
    kap_category = Column(String(50), nullable=True)  # Türkçe display label: "Temettü", "Finansal Sonuçlar", etc.
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Sentiment Analysis
    sentiment_score = Column(Float, nullable=True)  # -1.0 to +1.0
    sentiment_label = Column(String(20), nullable=True)  # positive, negative, neutral
    sentiment_confidence = Column(Float, nullable=True)  # 0-1
    importance_score = Column(Float, nullable=True)  # 0-1, how important is this news

    # Geopolitical classification
    is_geopolitical = Column(Boolean, default=False)
    geopolitical_category = Column(String(50), nullable=True)  # war, sanctions, trade, etc.
    geopolitical_severity = Column(Integer, nullable=True)  # 1-10

    # Processing status
    is_processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    stock = relationship("Stock", back_populates="news_items")

    def __repr__(self):
        return f"<NewsItem(title='{self.title[:50]}...', sentiment={self.sentiment_score})>"
