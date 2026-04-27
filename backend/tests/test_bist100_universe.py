from app.core.config import settings
from app.data.bist100_universe import BIST100_UNIVERSE, get_bist30_symbols


def test_bist100_universe_has_exactly_100_symbols():
    assert len(BIST100_UNIVERSE) == 100


def test_bist100_universe_symbols_are_unique():
    symbols = [item["symbol"] for item in BIST100_UNIVERSE]
    assert len(symbols) == len(set(symbols))


def test_settings_are_derived_from_canonical_universe():
    canonical_symbols = [item["symbol"] for item in BIST100_UNIVERSE]
    canonical_names = {item["symbol"]: item["name"] for item in BIST100_UNIVERSE}

    assert settings.BIST100_SYMBOLS == canonical_symbols
    assert settings.BIST100_COMPANIES == canonical_names


def test_bist30_subset_is_inside_bist100_universe():
    canonical_symbols = {item["symbol"] for item in BIST100_UNIVERSE}
    bist30_symbols = set(get_bist30_symbols())

    assert len(bist30_symbols) == 30
    assert bist30_symbols.issubset(canonical_symbols)
