"""Physical metal tickers classify as gold/silver and price per gram."""

from decimal import Decimal

from app.services.asset_type import (
    TROY_OUNCE_GRAMS,
    default_metal_ticker,
    holding_unit_price,
    honors_holding_currency,
    normalize_gold_karat,
    type_from_quote,
)


def test_gc_futures_maps_to_gold():
    assert type_from_quote("FUTURE", "GC=F") == "gold"


def test_si_futures_maps_to_silver():
    assert type_from_quote("FUTURE", "SI=F") == "silver"


def test_spot_fx_metals_map_by_ticker():
    assert type_from_quote("CURRENCY", "XAUUSD=X") == "gold"
    assert type_from_quote("CURRENCY", "XAGUSD=X") == "silver"


def test_other_futures_stay_investment():
    assert type_from_quote("FUTURE", "CL=F") == "investment"


def test_equity_mapping_is_unchanged():
    assert type_from_quote("EQUITY", "AAPL") == "stock"
    assert type_from_quote("ETF", "GLD") == "etf"


def test_ounce_gold_quote_converts_to_per_gram():
    ounce_price = TROY_OUNCE_GRAMS * Decimal("100")
    assert holding_unit_price("GC=F", ounce_price) == Decimal("100")


def test_equity_quote_is_not_converted():
    assert holding_unit_price("AAPL", Decimal("180.25")) == Decimal("180.25")


def test_default_tickers_are_spot_symbols():
    assert default_metal_ticker("gold") == "GOLD"
    assert default_metal_ticker("silver") == "SILVER"


def test_goldpricez_spot_symbols_map_to_metal_types():
    assert type_from_quote("METAL", "GOLD") == "gold"
    assert type_from_quote("METAL", "SILVER") == "silver"


def test_spot_gram_quote_is_not_ounce_converted():
    assert holding_unit_price("GOLD", Decimal("7080")) == Decimal("7080")


def test_gold_karat_scales_the_gram_price():
    assert holding_unit_price("GOLD", Decimal("2400"), karat=24) == Decimal("2400")
    assert holding_unit_price("GOLD", Decimal("2400"), karat=22) == Decimal("2200")
    assert holding_unit_price("GOLD", Decimal("2400"), karat=18) == Decimal("1800")


def test_silver_ignores_gold_karat():
    assert holding_unit_price("SILVER", Decimal("100"), karat=22) == Decimal("100")


def test_normalize_gold_karat_defaults_and_rejects_other_types():
    assert normalize_gold_karat(None, "gold") == 24
    assert normalize_gold_karat(22, "gold") == 22
    assert normalize_gold_karat(22, "silver") is None
    assert normalize_gold_karat(9, "gold") == 24


def test_gold_and_silver_honor_the_holding_currency():
    assert honors_holding_currency("gold", "GC=F") is True
    assert honors_holding_currency("silver", None) is True
    assert honors_holding_currency("investment", "GC=F") is True
    assert honors_holding_currency(None, "GOLD") is True
    assert honors_holding_currency("stock", "AAPL") is False
