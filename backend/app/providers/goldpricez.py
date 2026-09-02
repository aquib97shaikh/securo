"""GoldPriceZ live gold and silver prices (per gram, multi-currency).

Yahoo futures quote metals in USD per troy ounce. Physical holdings in Securo
are grams in the user's currency, so this provider calls GoldPriceZ:

    GET /api/rates/currency/{ccy}/measure/gram/metal/all
    Header: X-API-KEY

and reads ``gram_in_{ccy}`` / ``silver_gram_in_{ccy}``. One request covers
both metals; responses are cached briefly to stay under the free-tier
30–60 req/hour cap.
"""

from __future__ import annotations

import json
import logging
import time
from decimal import Decimal, InvalidOperation
from typing import Optional

import httpx

from app.providers.market_price import (
    MarketPriceProvider,
    MarketPriceRateLimitedError,
)
from app.schemas.asset import MarketSymbolMatch, MarketSymbolQuote

logger = logging.getLogger(__name__)

BASE_URL = "https://goldpricez.com/api/rates"
CACHE_TTL_SECONDS = 90.0

GOLD_SYMBOLS = frozenset({"GOLD", "XAU"})
SILVER_SYMBOLS = frozenset({"SILVER", "XAG"})

_GOLD_MATCH = MarketSymbolMatch(
    symbol="GOLD",
    name="Gold (spot, per gram)",
    exchange="GoldPriceZ",
    quote_type="METAL",
)
_SILVER_MATCH = MarketSymbolMatch(
    symbol="SILVER",
    name="Silver (spot, per gram)",
    exchange="GoldPriceZ",
    quote_type="METAL",
)


def is_goldpricez_symbol(symbol: Optional[str]) -> bool:
    key = (symbol or "").strip().upper()
    return key in GOLD_SYMBOLS or key in SILVER_SYMBOLS


def metal_kind(symbol: Optional[str]) -> Optional[str]:
    key = (symbol or "").strip().upper()
    if key in GOLD_SYMBOLS:
        return "gold"
    if key in SILVER_SYMBOLS:
        return "silver"
    return None


def extract_gram_price(
    payload: dict, metal: str, currency: str
) -> tuple[Optional[Decimal], str]:
    """Return (per-gram price, currency actually found)."""
    ccy = (currency or "USD").strip().lower()
    if metal == "silver":
        keys = ((f"silver_gram_in_{ccy}", currency), ("silver_gram_in_usd", "USD"))
    else:
        keys = ((f"gram_in_{ccy}", currency), ("gram_in_usd", "USD"))
    for field, found_ccy in keys:
        raw = payload.get(field)
        if raw is None or raw == "":
            continue
        try:
            return Decimal(str(raw)), found_ccy.upper()
        except (InvalidOperation, ValueError):
            continue
    return None, currency.upper()


class GoldpricezProvider(MarketPriceProvider):
    name = "goldpricez"

    def __init__(
        self,
        api_key: str,
        *,
        http: Optional[httpx.AsyncClient] = None,
        cache_ttl: float = CACHE_TTL_SECONDS,
    ) -> None:
        self.api_key = api_key
        self._http = http
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, dict]] = {}

    async def search(self, query: str, limit: int = 20) -> list[MarketSymbolMatch]:
        q = (query or "").strip().casefold()
        out: list[MarketSymbolMatch] = []
        gold_hit = not q or any(tok in q for tok in ("gold", "xau", "metal", "jewellery", "jewelry"))
        silver_hit = not q or any(tok in q for tok in ("silver", "xag", "metal"))
        if gold_hit:
            out.append(_GOLD_MATCH)
        if silver_hit:
            out.append(_SILVER_MATCH)
        return out[:limit]

    async def get_quote(
        self, symbol: str, currency: Optional[str] = None
    ) -> Optional[MarketSymbolQuote]:
        kind = metal_kind(symbol)
        if kind is None:
            return None
        ccy = (currency or "USD").strip().upper() or "USD"
        payload = await self._fetch_rates(ccy)
        if payload is None:
            return None
        price, found_ccy = extract_gram_price(payload, kind, ccy)
        if price is None:
            return None
        canonical = "GOLD" if kind == "gold" else "SILVER"
        name = "Gold" if kind == "gold" else "Silver"
        return MarketSymbolQuote(
            symbol=canonical,
            name=f"{name} (spot, per gram)",
            exchange="GoldPriceZ",
            currency=found_ccy,
            price=float(price),
            quote_type="METAL",
        )

    async def get_latest_prices(
        self, symbols: list[str]
    ) -> dict[str, Optional[Decimal]]:
        # Currency is per holding, not per ticker — callers should quote
        # each metal asset individually via get_quote.
        return {s.strip().upper(): None for s in symbols if s}

    async def _fetch_rates(self, currency: str) -> Optional[dict]:
        cache_key = currency.upper()
        now = time.monotonic()
        cached = self._cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        url = (
            f"{BASE_URL}/currency/{cache_key.lower()}/measure/gram/metal/all"
        )
        try:
            client = self._http
            if client is None:
                async with httpx.AsyncClient(timeout=15) as owned:
                    payload = await self._get_json(owned, url)
            else:
                payload = await self._get_json(client, url)
        except MarketPriceRateLimitedError:
            raise
        except Exception:
            logger.warning("GoldPriceZ fetch failed for %s", cache_key, exc_info=True)
            return None

        if payload is None:
            return None
        self._cache[cache_key] = (now + self._cache_ttl, payload)
        return payload

    async def _get_json(self, client: httpx.AsyncClient, url: str) -> Optional[dict]:
        response = await client.get(url, headers={"X-API-KEY": self.api_key})
        if response.status_code == 429:
            raise MarketPriceRateLimitedError("GoldPriceZ rate-limited this key")
        if response.status_code in (401, 403):
            logger.warning("GoldPriceZ rejected the API key (%s)", response.status_code)
            return None
        if response.status_code >= 400:
            logger.warning("GoldPriceZ HTTP %s for %s", response.status_code, url)
            return None
        data = response.json()
        if isinstance(data, (bytes, str)):
            try:
                data = json.loads(data)
            except (TypeError, ValueError, json.JSONDecodeError):
                logger.warning("GoldPriceZ returned a non-JSON body")
                return None
        if isinstance(data, dict) and data.get("error"):
            if int(data.get("code") or 0) == 429:
                raise MarketPriceRateLimitedError(str(data.get("message") or "rate limited"))
            logger.warning("GoldPriceZ error payload: %s", data.get("message"))
            return None
        if not isinstance(data, dict):
            return None
        return data


_goldpricez_singleton: Optional[GoldpricezProvider] = None


def get_goldpricez_provider() -> Optional[GoldpricezProvider]:
    global _goldpricez_singleton
    from app.core.config import get_settings

    key = get_settings().goldpricez_api_key.get_secret_value().strip()
    if not key:
        _goldpricez_singleton = None
        return None
    if _goldpricez_singleton is None or _goldpricez_singleton.api_key != key:
        _goldpricez_singleton = GoldpricezProvider(key)
    return _goldpricez_singleton
