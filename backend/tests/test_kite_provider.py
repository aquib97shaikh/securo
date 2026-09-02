"""Unit tests for the Kite Connect provider."""
from __future__ import annotations

import hashlib
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.providers.base import SessionExpiredError
from app.providers.kite import KiteProvider, _checksum


@pytest.fixture
def kite_env(monkeypatch):
    monkeypatch.setenv("KITE_API_KEY", "test-api-key")
    monkeypatch.setenv("KITE_API_SECRET", "test-api-secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_checksum_is_sha256_of_concatenated_values():
    assert _checksum("aaa", "bbb", "ccc") == hashlib.sha256(b"aaabbbccc").hexdigest()


@pytest.mark.asyncio
async def test_get_oauth_url_includes_api_key_and_state(kite_env):
    provider = KiteProvider()
    url = await provider.get_oauth_url("http://localhost:5173/oauth/callback", "state-token-123")
    assert "kite.zerodha.com/connect/login" in url
    assert "api_key=test-api-key" in url
    assert "state-token-123" in url


@pytest.mark.asyncio
async def test_handle_oauth_callback_exchanges_token(kite_env):
    provider = KiteProvider()

    async def fake_request(method, path, **kwargs):
        if path == "/session/token":
            return {
                "user_id": "AB1234",
                "access_token": "access-xyz",
                "login_time": "2026-09-06 09:00:00",
            }
        raise AssertionError(path)

    with patch.object(provider, "_request", side_effect=fake_request):
        data = await provider.handle_oauth_callback("req-abc")

    assert data.external_id == "AB1234"
    assert data.institution_name == "Zerodha"
    assert data.accounts == []
    assert data.credentials["user_id"] == "AB1234"
    assert "access_token_enc" in data.credentials


@pytest.mark.asyncio
async def test_get_holdings_maps_equity_and_mf(kite_env):
    provider = KiteProvider()
    creds = {"access_token": "token"}

    async def fake_request(method, path, *, credentials=None, **kwargs):
        if path == "/portfolio/holdings":
            return [
                {
                    "tradingsymbol": "SBIN",
                    "exchange": "NSE",
                    "isin": "INE062A01020",
                    "quantity": 16,
                    "last_price": 762.45,
                    "average_price": 801.78,
                    "pnl": -629.3,
                    "day_change": -3.95,
                    "day_change_percentage": -0.51,
                    "product": "CNC",
                    "instrument_token": 779530,
                    "close_price": 766.4,
                }
            ]
        if path == "/mf/holdings":
            return [
                {
                    "folio": "3108290884",
                    "fund": "INVESCO INDIA TAX PLAN - DIRECT PLAN",
                    "tradingsymbol": "INF205K01NT8",
                    "quantity": 382.488,
                    "last_price": 84.86,
                    "average_price": 78.43,
                    "pnl": 0,
                    "last_price_date": "2026-09-05",
                    "pledged_quantity": 0,
                }
            ]
        raise AssertionError(path)

    with patch.object(provider, "_request", side_effect=fake_request):
        holdings = await provider.get_holdings(creds)

    assert len(holdings) == 2
    equity = next(h for h in holdings if h.external_id == "NSE:SBIN")
    assert equity.name == "SBIN"
    assert equity.ticker == "SBIN"
    assert equity.currency == "INR"
    assert equity.quantity == Decimal("16")
    assert equity.current_value == Decimal("16") * Decimal("762.45")
    assert equity.purchase_price == Decimal("16") * Decimal("801.78")
    assert equity.account_external_id == "equity"
    assert equity.metadata["kite_kind"] == "equity"
    assert equity.metadata["average_price"] == "801.78"
    assert equity.unit_price == Decimal("762.45")

    mf = next(h for h in holdings if h.external_id.startswith("mf:"))
    assert mf.external_id == "mf:INF205K01NT8:3108290884"
    assert mf.name == "INVESCO INDIA TAX PLAN - DIRECT PLAN"
    assert mf.ticker is None
    assert mf.account_external_id == "mf"
    assert mf.metadata["kite_kind"] == "mutual_fund"


@pytest.mark.asyncio
async def test_get_holdings_equity_failure_still_returns_mf(kite_env):
    provider = KiteProvider()
    creds = {"access_token": "token"}

    async def fake_request(method, path, *, credentials=None, **kwargs):
        if path == "/portfolio/holdings":
            raise RuntimeError("upstream error")
        if path == "/mf/holdings":
            return [
                {
                    "folio": "1",
                    "fund": "Test Fund",
                    "tradingsymbol": "INF000",
                    "quantity": 1,
                    "last_price": 10,
                    "average_price": 9,
                    "pnl": 0,
                    "pledged_quantity": 0,
                }
            ]
        raise AssertionError(path)

    with patch.object(provider, "_request", side_effect=fake_request):
        holdings = await provider.get_holdings(creds)

    assert len(holdings) == 1
    assert holdings[0].external_id == "mf:INF000:1"


@pytest.mark.asyncio
async def test_request_maps_token_error_to_session_expired(kite_env):
    provider = KiteProvider()
    mock_response = httpx.Response(
        200,
        json={
            "status": "error",
            "message": "Invalid session token",
            "error_type": "TokenException",
        },
    )
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client
    mock_cm.__aexit__.return_value = False

    with patch("app.providers.kite.httpx.AsyncClient", return_value=mock_cm):
        with pytest.raises(SessionExpiredError):
            await provider._request(
                "GET",
                "/user/profile",
                credentials={"access_token": "bad"},
            )
