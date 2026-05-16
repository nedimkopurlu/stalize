from app.core.config import settings
from app.data.bist_full_universe import BIST_FULL_UNIVERSE, get_bist_full_symbols
from app.services.data_collector import DataCollector


def test_bist_full_universe_is_larger_than_bist100():
    assert len(get_bist_full_symbols()) >= 350
    assert len(get_bist_full_symbols()) > len(settings.BIST100_SYMBOLS)


def test_bist_full_universe_symbols_are_unique():
    symbols = get_bist_full_symbols()

    assert len(symbols) == len(set(symbols))


def test_settings_are_derived_from_full_canonical_universe():
    canonical_symbols = [item["symbol"] for item in BIST_FULL_UNIVERSE]

    assert settings.BIST_FULL_SYMBOLS == canonical_symbols


def test_data_collector_defaults_to_full_bist_universe():
    collector = DataCollector()

    assert collector.symbols == settings.BIST_FULL_SYMBOLS
