from datetime import timezone

import pytest

from app.services.data_collector import (
    _detail_slug_from_bloomberght_url,
    _parse_bloomberght_quote_items,
    _parse_tr_number,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("73,70", 73.70),
        ("6.087.286.875,35", 6087286875.35),
        ("0.07", 0.07),
        ("-1,32", -1.32),
        ("-", None),
    ],
)
def test_parse_tr_number(raw, expected):
    assert _parse_tr_number(raw) == expected


def test_detail_slug_from_bloomberght_url():
    assert (
        _detail_slug_from_bloomberght_url("/borsa/hisse/akbnk-akbank-detay")
        == "akbnk-akbank-detay"
    )


def test_parse_bloomberght_quote_items():
    quote = _parse_bloomberght_quote_items(
        {
            "ibsSymbol": "AKBNK",
            "lastPrice": "73,70",
            "prevPrice": "73,70",
            "percentChange": "0,00",
            "priceHigh": "74,05",
            "priceLow": "72,85",
            "volume": "6.087.286.875,35",
            "volumeLot": "82.800.089,00",
            "lastUpdateTime": "30/04/2026 16:11:31",
        }
    )

    assert quote is not None
    assert quote.symbol == "AKBNK"
    assert quote.last_price == 73.70
    assert quote.daily_change_pct == 0.0
    assert quote.high == 74.05
    assert quote.low == 72.85
    assert quote.volume_lot == 82800089.0
    assert quote.as_of.tzinfo is not None
    assert quote.as_of.astimezone(timezone.utc).isoformat() == "2026-04-30T13:11:31+00:00"
