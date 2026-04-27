"""
Stalize Configuration
Central configuration management using pydantic-settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict
import os

from app.data.bist100_universe import (
    BIST100_UNIVERSE,
    get_bist100_company_map,
    get_bist100_sector_map,
    get_bist100_symbols,
    get_bist30_symbols,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Stalize"
    APP_VERSION: str = "1.4.0"  # Teknik + temel + haber/olay analizi
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/stockanalist"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://localhost:5432/stockanalist"

    # API Settings
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Data Collection
    YFINANCE_CACHE_TTL: int = 3600  # 1 hour cache
    DATA_UPDATE_INTERVAL_HOURS: int = 6  # Update every 6 hours
    NEWS_UPDATE_INTERVAL_HOURS: int = 2  # Update news every 2 hours

    # KAP (Kamuyu Aydınlatma Platformu) — 1. Öncelikli Kaynak
    KAP_RSS_URL: str = "https://www.kap.org.tr/tr/rss/bildirimler"
    KAP_ALT_RSS_URL: str = "https://www.kap.org.tr/en/rss"  # Yedek
    KAP_SCAN_INTERVAL_MIN: int = 5  # Her 5 dakikada bir tara
    KAP_MAX_AGE_HOURS: int = 48    # 48 saatten eski haberleri atla

    # Ensemble Weights — Orta vadeli yatirimci odagi (MIDT-02)
    WEIGHT_FUNDAMENTAL: float = 0.45  # Temel analiz: F/K, PD/DD, ROE, marj
    WEIGHT_TECHNICAL: float = 0.40    # Teknik analiz: EMA, ATR, RSI, hacim, divergence
    WEIGHT_NEWS: float = 0.15         # Haber etkisi: KAP, TCMB, TUIK duygu

    # Source Strategy
    PRIMARY_DISCLOSURE_SOURCE: str = "KAP"
    NEWS_PRIORITIZATION_MODE: str = "impact_first"

    # Official / Market Data Sources
    SOURCE_CATALOG: Dict[str, str] = {
        "Borsa Istanbul": "https://www.borsaistanbul.com",
        "KAP": "https://www.kap.org.tr",
        "TCMB": "https://www.tcmb.gov.tr",
        "TUIK": "https://www.tuik.gov.tr",
        "Hazine ve Maliye Bakanligi": "https://www.hmb.gov.tr",
        "Bloomberg": "https://www.bloomberg.com",
        "Reuters": "https://www.reuters.com",
        "Yahoo Finance": "https://finance.yahoo.com",
        "MarketWatch": "https://www.marketwatch.com",
        "Financial Times": "https://www.ft.com",
        "CNBC": "https://www.cnbc.com",
        "Investing": "https://tr.investing.com",
        "TradingView": "https://www.tradingview.com",
        "Midas": "https://www.getmidas.com",
        "Matriks": "https://www.matriksdata.com",
        "Ideal Data": "https://www.idealdata.com.tr",
        "Bloomberg HT": "https://www.bloomberght.com",
        "Ekonomim": "https://www.ekonomim.com",
        "Dunya Gazetesi": "https://www.dunya.com",
        "CNBC-e": "https://www.cnbce.com",
        "Bigpara": "https://bigpara.hurriyet.com.tr",
        "Mynet Finans": "https://finans.mynet.com",
        "A Para": "https://www.apara.com.tr",
        "Para Analiz": "https://www.paraanaliz.com",
        "InvestAZ Arastirma": "https://www.investaz.com.tr",
        "Foreks": "https://www.foreks.com",
        "Borsa Gundem": "https://www.borsagundem.com.tr",
        "Finans Gundem": "https://www.finansingundemi.com",
        "Borsanin Gundemi": "https://www.borsaningundemi.com",
        "Fintables": "https://fintables.com",
        "Finnet": "https://www.finnet.com.tr",
        "TEFAS": "https://www.tefas.gov.tr",
        "Takasbank": "https://www.takasbank.com.tr",
        "Borsa Istanbul Veri Store": "https://datastore.borsaistanbul.com",
        "MKK": "https://www.mkk.com.tr",
    }

    SOURCE_PRIORITY: List[str] = [
        "KAP",
        "Borsa Istanbul",
        "TCMB",
        "TUIK",
        "Hazine ve Maliye Bakanligi",
        "Reuters",
        "Bloomberg",
        "Financial Times",
        "CNBC",
        "Yahoo Finance",
        "MarketWatch",
        "Investing",
        "TradingView",
        "Bloomberg HT",
        "Ekonomim",
        "Dunya Gazetesi",
        "CNBC-e",
        "Foreks",
        "Fintables",
        "Finnet",
        "Takasbank",
        "TEFAS",
        "MKK",
    ]

    BIST100_UNIVERSE: List[Dict[str, object]] = BIST100_UNIVERSE
    BIST100_COMPANIES: Dict[str, str] = get_bist100_company_map()
    BIST100_SECTORS: Dict[str, str] = get_bist100_sector_map()
    BIST100_SYMBOLS: List[str] = get_bist100_symbols()
    BIST30_SYMBOLS: List[str] = get_bist30_symbols()

    # Commodity Symbols (Yahoo Finance)
    COMMODITY_SYMBOLS: Dict[str, str] = {
        "brent_oil": "BZ=F",
        "wti_oil": "CL=F",
        "gold": "GC=F",
        "silver": "SI=F",
        "platinum": "PL=F",
        "natural_gas": "NG=F",
        "copper": "HG=F",
        "wheat": "ZW=F",
        "corn": "ZC=F",
        "cotton": "CT=F",
        "sugar": "SB=F",
    }

    # Global Index Symbols
    INDEX_SYMBOLS: Dict[str, str] = {
        "bist100": "XU100.IS",
        "bist30": "XU030.IS",
        "sp500": "^GSPC",
        "nasdaq": "^IXIC",
        "dowjones": "^DJI",
        "dax": "^GDAXI",
        "ftse": "^FTSE",
        "shanghai": "000001.SS",
        "nikkei": "^N225",
        "vix": "^VIX",
        "msci_em": "EEM",
    }

    # Currency Pairs
    CURRENCY_PAIRS: Dict[str, str] = {
        "usd_try": "USDTRY=X",
        "eur_try": "EURTRY=X",
        "gbp_try": "GBPTRY=X",
        "cny_try": "CNYTRY=X",
        "dxy": "DX-Y.NYB",
    }

    # Bond Yields
    BOND_SYMBOLS: Dict[str, str] = {
        "us_10y": "^TNX",
        "us_2y": "^IRX",
    }

    def model_post_init(self, __context) -> None:
        # Railway provides postgresql:// — convert to driver-specific URLs
        raw = self.DATABASE_URL
        if raw.startswith("postgresql://") or raw.startswith("postgres://"):
            base = raw.replace("postgres://", "postgresql://", 1)
            object.__setattr__(self, "DATABASE_URL", base.replace("postgresql://", "postgresql+asyncpg://", 1))
            object.__setattr__(self, "DATABASE_SYNC_URL", base.replace("postgresql://", "postgresql+psycopg2://", 1))

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore unknown/legacy env vars.


settings = Settings()
