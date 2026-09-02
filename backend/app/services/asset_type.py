"""Asset type helpers shared by holdings created from market quotes.

Physical gold and silver are priced from COMEX/spot tickers that quote in
USD per troy ounce. Holdings store quantity in grams, so quotes are converted
to a per-gram unit price before they land on `last_price`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

TROY_OUNCE_GRAMS = Decimal("31.1034768")

GOLD_OZ_TICKERS = frozenset({"GC=F", "MGC=F", "XAUUSD=X", "XAU=X"})
SILVER_OZ_TICKERS = frozenset({"SI=F", "SIL=F", "XAGUSD=X", "XAG=X"})
GOLD_GRAM_TICKERS = frozenset({"GOLD", "XAU"})
SILVER_GRAM_TICKERS = frozenset({"SILVER", "XAG"})
GOLD_KARATS = (24, 22, 21, 18, 16, 14, 10)
DEFAULT_GOLD_KARAT = 24

_QUOTE_TYPE_TO_ASSET = {
    "EQUITY": "stock",
    "ETF": "etf",
    "CRYPTOCURRENCY": "crypto",
    "MUTUALFUND": "fund",
    "INDEX": "fund",
}


def is_physical_metal_oz_ticker(ticker: Optional[str]) -> bool:
    key = (ticker or "").strip().upper()
    return key in GOLD_OZ_TICKERS or key in SILVER_OZ_TICKERS


def is_physical_metal_gram_ticker(ticker: Optional[str]) -> bool:
    key = (ticker or "").strip().upper()
    return key in GOLD_GRAM_TICKERS or key in SILVER_GRAM_TICKERS


def is_gold_ticker(ticker: Optional[str]) -> bool:
    key = (ticker or "").strip().upper()
    return key in GOLD_OZ_TICKERS or key in GOLD_GRAM_TICKERS


def normalize_gold_karat(karat: Optional[int], asset_type: Optional[str] = None) -> Optional[int]:
    """Gold stores purity as an integer karat. Anything else is unset."""
    kind = (asset_type or "").strip().lower()
    if kind != "gold":
        return None
    if karat in GOLD_KARATS:
        return karat
    return DEFAULT_GOLD_KARAT


def gold_karat_factor(karat: Optional[int]) -> Decimal:
    normalized = karat if karat in GOLD_KARATS else DEFAULT_GOLD_KARAT
    return Decimal(normalized) / Decimal(DEFAULT_GOLD_KARAT)


def type_from_quote(quote_type: Optional[str], symbol: Optional[str] = None) -> str:
    """Map a provider quote to Securo's asset type.

    Metal futures/spot symbols win over quoteType so GC=F is gold even when
    Yahoo labels it FUTURE (which would otherwise fall through to investment).
    """
    ticker = (symbol or "").strip().upper()
    if ticker in GOLD_OZ_TICKERS or ticker in GOLD_GRAM_TICKERS:
        return "gold"
    if ticker in SILVER_OZ_TICKERS or ticker in SILVER_GRAM_TICKERS:
        return "silver"
    return _QUOTE_TYPE_TO_ASSET.get((quote_type or "").upper(), "investment")


def holding_unit_price(
    ticker: Optional[str],
    quote_price: Decimal,
    karat: Optional[int] = None,
) -> Decimal:
    """Price per holding unit. Metal ounce quotes become a per-gram price.

    Gold karats scale the 24K spot: 22K is 22/24 of the live gram price.
    Silver has no karat and is left unchanged.
    """
    unit = quote_price / TROY_OUNCE_GRAMS if is_physical_metal_oz_ticker(ticker) else quote_price
    if is_gold_ticker(ticker) and karat is not None:
        unit = unit * gold_karat_factor(karat)
    return unit


def honors_holding_currency(asset_type: Optional[str], ticker: Optional[str] = None) -> bool:
    """Gold/silver (and metal ounce/spot tickers) keep the user's chosen currency."""
    kind = (asset_type or "").strip().lower()
    return (
        kind in {"gold", "silver"}
        or is_physical_metal_oz_ticker(ticker)
        or is_physical_metal_gram_ticker(ticker)
    )


def default_metal_ticker(asset_type: str) -> str:
    if asset_type == "gold":
        return "GOLD"
    if asset_type == "silver":
        return "SILVER"
    raise ValueError(f"not a physical metal type: {asset_type}")
