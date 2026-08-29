# Kite Connect portfolio sync

Date: 2026-09-06

## Problem

Securo users with Zerodha accounts must manually enter Indian equity and mutual fund holdings. Kite Connect exposes authenticated portfolio APIs that report current quantities, cost basis, and market/NAV values.

## Decision

Add Kite as a user-scoped bank provider that syncs **equity holdings** and **mutual fund holdings** into Securo Assets via the existing `BankProvider.get_holdings()` → `_sync_holdings()` pipeline.

- One Zerodha connection per user (OAuth login flow).
- Two Kite API calls per sync: `GET /portfolio/holdings` and `GET /mf/holdings`.
- Two asset wallets: **Zerodha Stocks** and **Zerodha Mutual Funds**.
- Values refreshed on connect and on the normal connection sync schedule.
- Daily token expiry handled with **reconnect on the Assets page** (Kite tokens expire at 6 AM IST). Users should not need to visit Accounts to re-authenticate.

## Out of scope

- F&O / intraday positions (`GET /portfolio/positions`)
- SIP list, MF orders, order placement
- Cash and margin balances (`GET /user/margins`)
- Holdings authorisation (CDSL sell flow)
- Live WebSocket quotes
- Transaction ledger import from Kite order history
- Dividend reinvestment MF schemes (unsupported by Kite API)

## Operator setup

Register a Kite Connect app at [developers.kite.trade](https://developers.kite.trade/) and set:

| Env var | Purpose |
|---------|---------|
| `KITE_API_KEY` | Public API key |
| `KITE_API_SECRET` | Server-side secret (never exposed to frontend) |
| `KITE_OAUTH_REDIRECT_URI` | Optional; defaults to `{FRONTEND_URL}/oauth/callback` |

Redirect URL registered in Kite developer console must match the frontend callback. Provider auto-registers when both key and secret are set.

## Authentication

Kite uses a custom login flow, not OAuth 2.0:

1. Redirect user to `https://kite.zerodha.com/connect/login?v=3&api_key=...` with `state` passed via `redirect_params`.
2. Kite redirects back with `request_token` (not `code`).
3. Backend exchanges token: `POST /session/token` with `checksum = SHA256(api_key + request_token + api_secret)`.
4. Store encrypted `access_token` and `user_id` on `BankConnection.credentials`.
5. Sign subsequent requests: `Authorization: token api_key:access_token`.

Frontend change: `oauth-callback.tsx` accepts `request_token` as fallback when `code` is absent, and posts it to the existing `/connections/oauth/callback` endpoint.

Token expires daily at 6 AM IST with no refresh token for standard apps. On expiry, provider raises `SessionExpiredError`; connection is marked for reconnection.

## Sync behaviour

`KiteProvider.get_holdings(credentials)` fetches both endpoints, normalizes to `HoldingData`, and returns a combined list.

Failures on one endpoint should not block the other (equity error still syncs MF, and vice versa). Log and return partial results.

Archived assets: holdings absent from the latest response are archived (existing `_sync_holdings` behaviour), not deleted.

Respects `connection.settings.sync_assets` (default `true`).

## Wallet layout

Use `HoldingData.account_external_id` to split wallets (same pattern as SimpleFIN per-account wallets):

| `account_external_id` | Wallet name | Source API |
|----------------------|-------------|------------|
| `equity` | Zerodha Stocks | `/portfolio/holdings` |
| `mf` | Zerodha Mutual Funds | `/mf/holdings` |

## Equity holdings mapping

Source: `GET /portfolio/holdings`

| Kite field | `HoldingData` |
|------------|---------------|
| `{exchange}:{tradingsymbol}` | `external_id` |
| `tradingsymbol` | `name` |
| `tradingsymbol` | `ticker` |
| `isin` | `isin` |
| `INR` | `currency` |
| `quantity` | `quantity` |
| `last_price` | `unit_price` |
| `quantity * last_price` | `current_value` |
| `average_price` | `purchase_price` |
| `equity` | `account_external_id` |
| `Zerodha Stocks` | `account_name` |
| `pnl`, `day_change`, `day_change_percentage`, `exchange`, `product`, `instrument_token`, `close_price` | `metadata` |

Securo asset: `source=kite`, `type=investment`, `valuation_method=manual`. Metadata includes `kite_kind: "equity"`.

## Mutual fund holdings mapping

Source: `GET /mf/holdings`

MF `tradingsymbol` is the fund ISIN. The same ISIN can appear under multiple folios, so `external_id` must include folio:

| Kite field | `HoldingData` |
|------------|---------------|
| `mf:{tradingsymbol}:{folio}` | `external_id` |
| `fund` | `name` |
| `tradingsymbol` | `isin` |
| `INR` | `currency` |
| `quantity` | `quantity` |
| `last_price` | `unit_price` |
| `quantity * last_price` | `current_value` |
| `average_price` | `purchase_price` |
| `mf` | `account_external_id` |
| `Zerodha Mutual Funds` | `account_name` |
| `folio`, `pnl`, `last_price_date`, `pledged_quantity` | `metadata` |

Securo asset: `source=kite`, `type=investment`, `valuation_method=manual`. Metadata includes `kite_kind: "mutual_fund"`.

Do not set `ticker` for MF rows (ISIN is not a market ticker; avoids confusion with Yahoo lookup).

## Backend components

| File | Change |
|------|--------|
| `backend/app/providers/kite.py` | New `KiteProvider` |
| `backend/app/providers/__init__.py` | Register provider, add to `KNOWN_PROVIDERS` |
| `backend/app/core/config.py` | `kite_api_key`, `kite_api_secret`, `kite_oauth_redirect_uri` |
| `backend/.env.example` | Document env vars |

`KiteProvider` implements:

- `get_oauth_url()` — Kite login URL with Redis-backed `state`
- `handle_oauth_callback(request_token)` — token exchange, return `ConnectionData` with `external_id=user_id`, `institution_name=Zerodha`, empty `accounts`
- `get_holdings()` — equity + MF fetch and map
- `reauth_url()` — same as login URL
- `refresh_credentials()` — raise `SessionExpiredError` when token invalid

HTTP client: thin wrapper around `httpx` with `X-Kite-Version: 3` header. Map Kite error responses to `SessionExpiredError` when appropriate.

Credentials stored encrypted (`access_token_enc`) following Enable Banking pattern.

## Frontend components

| File | Change |
|------|--------|
| `frontend/src/pages/oauth-callback.tsx` | Accept `request_token` query param |
| `frontend/src/pages/assets.tsx` | Re-auth banner + actions on synced wallets (required) |
| Locales | Reconnect copy for Assets page |

Kite appears in the connect-provider list when configured. Synced assets show existing "Synced" badge; edit/delete disabled for provider-owned assets.

### Assets page re-auth (required)

Kite tokens expire every morning, so reconnection must be reachable where users view holdings — on the Assets page — not only on Accounts.

**Data:** Assets page loads `connections.list()` alongside wallets. Each synced wallet already carries `connection_id`; join to `BankConnection.status` (`active`, `error`, `expired`).

**When `connection.status` is `error` or `expired`:**

1. **Page banner** — If any synced wallet’s connection needs reconnection, show a dismissible amber alert at the top of Assets:
   - Message: holdings may be stale; log in again to refresh (e.g. “Your Zerodha session expired. Reconnect to update holdings.”)
   - Primary action: **Reconnect** → `connections.getReauthUrl(connectionId)` → redirect to Kite login
   - If multiple connections need reconnection, one banner per institution (or a single banner listing each with its own button)

2. **Per-wallet row** — On each affected synced wallet header (Zerodha Stocks / Zerodha Mutual Funds):
   - Amber warning icon (same visual language as Accounts)
   - **Reconnect** button next to wallet actions (alongside edit wallet)
   - Subtitle under wallet name: “Session expired — reconnect to sync” (reuse/adapt `accounts.connectionExpired`)

3. **Sync while healthy** — When connection is `active`, show a sync icon on synced wallet headers that calls `connections.sync(connectionId)` (same as Accounts refresh). Hidden or disabled when reconnection is required.

**Implementation:** Reuse existing APIs — no new backend endpoints:

- OAuth re-auth: `POST /connections/{id}/oauth/reauth-url` (Kite `flow_type: oauth`)
- After callback, redirect user back to `/assets` (store `return_to=assets` in OAuth state or default post-callback redirect for Kite connections)

Extract shared reconnect helper from `accounts.tsx` (`handleReconnectClick` + provider flow lookup) into a small hook or util so Accounts and Assets stay consistent.

**Connect (first time):** Optional v1 shortcut — “Connect Zerodha” button on Assets when Kite is configured and user has no Kite connection yet. Opens the same OAuth connect flow as Accounts.

## Errors

| Situation | Behaviour |
|-----------|-----------|
| Token expired | Connection status `expired`; Assets page banner + per-wallet Reconnect button; OAuth re-auth via existing `/oauth/reauth-url` |
| One API fails | Sync partial holdings; log error |
| User has no MF on Coin | `/mf/holdings` returns `[]`; equity still syncs |
| Kite not configured | Provider hidden from list (`configured: false`) |

Manual asset edits remain available for non-synced assets only (existing rule).

## Testing

| Test | Coverage |
|------|----------|
| `backend/tests/test_kite_provider.py` | Checksum, token exchange, equity/MF parsing, partial failure |
| `backend/tests/test_sync_holdings.py` | Mock Kite provider; wallet split, upsert, archive |
| `backend/tests/test_connections_api.py` | Kite in provider list when env set |
| Frontend (manual / component) | Expired Kite connection shows Reconnect on Assets wallet row and page banner |

Use recorded JSON fixtures from Kite docs for response parsing tests.

## Security

- `api_secret` and `access_token` never sent to frontend.
- Tokens encrypted at rest.
- OAuth `state` single-use via Redis (existing `oauth_state.py`).

## Future extensions (not in v1)

- Positions sync for active traders
- MF SIP metadata linked to Securo recurring transactions
- Margin/cash as a linked account for net-worth completeness
- Map equity tickers to NSE Yahoo symbols (`.NS`) for live quotes independent of sync
