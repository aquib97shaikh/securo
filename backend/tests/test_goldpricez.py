"""GoldPriceZ metal quotes — per-gram prices in the requested currency."""

import json
from decimal import Decimal

import httpx
import pytest

from app.providers.goldpricez import (
    GoldpricezProvider,
    extract_gram_price,
    is_goldpricez_symbol,
)
from app.providers.market_price import MarketPriceRateLimitedError


SAMPLE_INR = {
    "ounce_price_usd": "2650.00",
    "gram_in_usd": "85.20",
    "gram_in_inr": "7080.00",
    "silver_gram_in_usd": "1.05",
    "silver_gram_in_inr": "87.15",
}


def test_gold_and_silver_spot_symbols_are_goldpricez():
    assert is_goldpricez_symbol("GOLD") is True
    assert is_goldpricez_symbol("SILVER") is True
    assert is_goldpricez_symbol("GC=F") is False
    assert is_goldpricez_symbol("AAPL") is False


def test_extract_gram_price_prefers_requested_currency():
    gold, ccy = extract_gram_price(SAMPLE_INR, "gold", "INR")
    assert gold == Decimal("7080.00")
    assert ccy == "INR"
    silver, sccy = extract_gram_price(SAMPLE_INR, "silver", "INR")
    assert silver == Decimal("87.15")
    assert sccy == "INR"


def test_extract_gram_price_falls_back_to_usd_field():
    payload = {"gram_in_usd": "85.20"}
    price, ccy = extract_gram_price(payload, "gold", "INR")
    assert price == Decimal("85.20")
    assert ccy == "USD"


@pytest.mark.asyncio
async def test_provider_quotes_gold_per_gram_in_holding_currency():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-api-key") == "test-key"
        assert "/currency/inr/" in str(request.url)
        assert "/measure/gram/" in str(request.url)
        assert "/metal/all" in str(request.url)
        return httpx.Response(200, json=SAMPLE_INR)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        provider = GoldpricezProvider("test-key", http=http)
        quote = await provider.get_quote("GOLD", currency="INR")

    assert quote is not None
    assert quote.symbol == "GOLD"
    assert quote.currency == "INR"
    assert quote.price == pytest.approx(7080.0)
    assert quote.quote_type == "METAL"
    assert quote.exchange == "GoldPriceZ"


@pytest.mark.asyncio
async def test_provider_quotes_silver_from_the_same_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SAMPLE_INR)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        provider = GoldpricezProvider("test-key", http=http)
        quote = await provider.get_quote("SILVER", currency="INR")

    assert quote is not None
    assert quote.symbol == "SILVER"
    assert quote.price == pytest.approx(87.15)


@pytest.mark.asyncio
async def test_provider_search_returns_spot_metals():
    provider = GoldpricezProvider("test-key")
    gold = await provider.search("gold")
    assert [m.symbol for m in gold] == ["GOLD"]
    both = await provider.search("metal")
    assert {m.symbol for m in both} == {"GOLD", "SILVER"}


@pytest.mark.asyncio
async def test_provider_unwraps_json_encoded_string_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=json.dumps(SAMPLE_INR))

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        provider = GoldpricezProvider("test-key", http=http)
        quote = await provider.get_quote("GOLD", currency="INR")

    assert quote is not None
    assert quote.price == pytest.approx(7080.0)


@pytest.mark.asyncio
async def test_provider_429_is_rate_limited():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": True, "code": 429, "message": "Too Many Requests"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        provider = GoldpricezProvider("test-key", http=http)
        with pytest.raises(MarketPriceRateLimitedError):
            await provider.get_quote("GOLD", currency="USD")
