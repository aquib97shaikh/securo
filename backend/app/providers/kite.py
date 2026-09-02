"""Zerodha Kite Connect provider — Indian equity and mutual fund holdings.

Auth is a custom login flow (not OAuth 2.0): the user logs in at Kite,
returns a short-lived ``request_token``, which we exchange server-side for
an ``access_token``. Tokens expire daily at 6 AM IST; there is no refresh
token for standard apps, so users must re-login.
"""
from __future__ import annotations

import hashlib
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.agents.services.crypto import decrypt, encrypt
from app.core.config import get_settings
from app.providers.base import (
    AccountData,
    BankProvider,
    ConnectionData,
    HoldingData,
    SessionExpiredError,
    TransactionData,
    default_oauth_redirect_uri,
)

logger = logging.getLogger(__name__)

KITE_API_BASE = "https://api.kite.trade"
KITE_LOGIN_BASE = "https://kite.zerodha.com/connect/login"
KITE_VERSION = "3"
INSTITUTION_NAME = "Zerodha"


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _checksum(api_key: str, request_token: str, api_secret: str) -> str:
    payload = f"{api_key}{request_token}{api_secret}"
    return hashlib.sha256(payload.encode()).hexdigest()


class KiteProvider(BankProvider):
    @property
    def name(self) -> str:
        return "kite"

    @property
    def flow_type(self) -> str:
        return "oauth"

    @property
    def redirect_uri(self) -> str:
        settings = get_settings()
        return settings.kite_oauth_redirect_uri or default_oauth_redirect_uri()

    def _api_key(self) -> str:
        key = get_settings().kite_api_key
        if not key:
            raise RuntimeError("KITE_API_KEY is not configured")
        return key

    def _api_secret(self) -> str:
        secret = get_settings().kite_api_secret.get_secret_value()
        if not secret:
            raise RuntimeError("KITE_API_SECRET is not configured")
        return secret

    def _access_token(self, credentials: dict) -> str:
        raw = credentials.get("access_token_enc") or credentials.get("access_token")
        if not raw:
            raise SessionExpiredError("Kite access token missing — reconnect Zerodha")
        token = decrypt(raw) if credentials.get("access_token_enc") else raw
        if not token:
            raise SessionExpiredError("Kite access token missing — reconnect Zerodha")
        return token

    def _auth_headers(self, credentials: dict) -> dict[str, str]:
        api_key = self._api_key()
        access_token = self._access_token(credentials)
        return {
            "X-Kite-Version": KITE_VERSION,
            "Authorization": f"token {api_key}:{access_token}",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        credentials: Optional[dict] = None,
        data: Optional[dict] = None,
        unauthenticated: bool = False,
    ) -> Any:
        headers: dict[str, str] = {"X-Kite-Version": KITE_VERSION}
        if not unauthenticated:
            if credentials is None:
                raise ValueError("credentials required for authenticated Kite request")
            headers.update(self._auth_headers(credentials))

        url = f"{KITE_API_BASE}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, data=data)

        if response.status_code in (401, 403):
            raise SessionExpiredError("Kite session expired — reconnect Zerodha")

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Kite returned non-JSON response for {path}") from exc

        if payload.get("status") != "success":
            error_type = (payload.get("error_type") or "").lower()
            message = payload.get("message") or f"Kite API error on {path}"
            if error_type in {"tokenexception", "inputexception"} and "token" in message.lower():
                raise SessionExpiredError("Kite session expired — reconnect Zerodha")
            raise RuntimeError(message)

        return payload.get("data")

    async def get_oauth_url(
        self,
        redirect_uri: str,
        state: str,
        flow_params: Optional[dict] = None,
    ) -> str:
        api_key = self._api_key()
        params = {
            "v": KITE_VERSION,
            "api_key": api_key,
            "redirect_params": urlencode({"state": state}),
        }
        return f"{KITE_LOGIN_BASE}?{urlencode(params)}"

    async def reauth_url(
        self,
        credentials: dict,
        settings: dict,
        redirect_uri: str,
        state: str,
    ) -> str:
        return await self.get_oauth_url(redirect_uri, state)

    async def handle_oauth_callback(self, code: str) -> ConnectionData:
        request_token = (code or "").strip()
        if not request_token:
            raise ValueError("Kite login did not return a request_token")

        api_key = self._api_key()
        api_secret = self._api_secret()
        data = await self._request(
            "POST",
            "/session/token",
            data={
                "api_key": api_key,
                "request_token": request_token,
                "checksum": _checksum(api_key, request_token, api_secret),
            },
            unauthenticated=True,
        )
        if not isinstance(data, dict):
            raise RuntimeError("Kite token exchange returned unexpected payload")

        access_token = data.get("access_token")
        user_id = data.get("user_id")
        if not access_token or not user_id:
            raise RuntimeError("Kite token exchange missing access_token or user_id")

        encrypted_token = encrypt(access_token) or access_token
        credentials = {
            "access_token_enc": encrypted_token,
            "user_id": user_id,
            "login_time": data.get("login_time"),
            "api_key": api_key,
        }
        return ConnectionData(
            external_id=str(user_id),
            institution_name=INSTITUTION_NAME,
            credentials=credentials,
            accounts=[],
        )

    async def get_accounts(self, credentials: dict) -> list[AccountData]:
        return []

    async def get_transactions(
        self,
        credentials: dict,
        account_external_id: str,
        since=None,
        payee_source: str = "auto",
    ) -> list[TransactionData]:
        return []

    async def refresh_credentials(self, credentials: dict) -> dict:
        # Probe the session; Kite has no refresh token for standard apps.
        await self._request("GET", "/user/profile", credentials=credentials)
        return credentials

    def _map_equity_holding(self, raw: dict) -> Optional[HoldingData]:
        exchange = (raw.get("exchange") or "").strip()
        symbol = (raw.get("tradingsymbol") or "").strip()
        if not exchange or not symbol:
            return None

        quantity = _to_decimal(raw.get("quantity"))
        last_price = _to_decimal(raw.get("last_price"))
        if quantity is None or last_price is None:
            return None

        current_value = quantity * last_price
        isin = (raw.get("isin") or "").strip() or None
        average_price = _to_decimal(raw.get("average_price"))
        total_cost = (
            average_price * quantity
            if average_price is not None and quantity is not None
            else None
        )

        return HoldingData(
            external_id=f"{exchange}:{symbol}",
            name=symbol,
            currency="INR",
            ticker=symbol,
            isin=isin,
            quantity=quantity,
            unit_price=last_price,
            current_value=current_value,
            purchase_price=total_cost,
            account_external_id="equity",
            account_name="Zerodha Stocks",
            metadata={
                "kite_kind": "equity",
                "average_price": str(average_price)
                if average_price is not None
                else None,
                "exchange": exchange,
                "product": raw.get("product"),
                "instrument_token": raw.get("instrument_token"),
                "pnl": str(raw.get("pnl")) if raw.get("pnl") is not None else None,
                "day_change": str(raw.get("day_change"))
                if raw.get("day_change") is not None
                else None,
                "day_change_percentage": str(raw.get("day_change_percentage"))
                if raw.get("day_change_percentage") is not None
                else None,
                "close_price": str(raw.get("close_price"))
                if raw.get("close_price") is not None
                else None,
            },
        )

    def _map_mf_holding(self, raw: dict) -> Optional[HoldingData]:
        isin = (raw.get("tradingsymbol") or "").strip()
        folio = (raw.get("folio") or "").strip()
        fund_name = (raw.get("fund") or "").strip()
        if not isin or not folio:
            return None

        quantity = _to_decimal(raw.get("quantity"))
        last_price = _to_decimal(raw.get("last_price"))
        if quantity is None or last_price is None:
            return None

        average_price = _to_decimal(raw.get("average_price"))
        total_cost = (
            average_price * quantity
            if average_price is not None and quantity is not None
            else None
        )

        return HoldingData(
            external_id=f"mf:{isin}:{folio}",
            name=fund_name or isin,
            currency="INR",
            isin=isin,
            quantity=quantity,
            unit_price=last_price,
            current_value=quantity * last_price,
            purchase_price=total_cost,
            account_external_id="mf",
            account_name="Zerodha Mutual Funds",
            metadata={
                "kite_kind": "mutual_fund",
                "average_price": str(average_price)
                if average_price is not None
                else None,
                "folio": folio,
                "pnl": str(raw.get("pnl")) if raw.get("pnl") is not None else None,
                "last_price_date": raw.get("last_price_date"),
                "pledged_quantity": str(raw.get("pledged_quantity"))
                if raw.get("pledged_quantity") is not None
                else None,
            },
        )

    async def get_holdings(self, credentials: dict) -> list[HoldingData]:
        holdings: list[HoldingData] = []

        try:
            equity_raw = await self._request(
                "GET", "/portfolio/holdings", credentials=credentials
            )
            if isinstance(equity_raw, list):
                for item in equity_raw:
                    if isinstance(item, dict):
                        mapped = self._map_equity_holding(item)
                        if mapped is not None:
                            holdings.append(mapped)
        except SessionExpiredError:
            raise
        except Exception:
            logger.exception("Failed to fetch Kite equity holdings")

        try:
            mf_raw = await self._request("GET", "/mf/holdings", credentials=credentials)
            if isinstance(mf_raw, list):
                for item in mf_raw:
                    if isinstance(item, dict):
                        mapped = self._map_mf_holding(item)
                        if mapped is not None:
                            holdings.append(mapped)
        except SessionExpiredError:
            raise
        except Exception:
            logger.exception("Failed to fetch Kite mutual fund holdings")

        return holdings
