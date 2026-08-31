"""Google Drive REST (OAuth + files) over httpx.

No official Google client: the surface we need is token exchange, one folder,
and zip upsert/list/delete. Tests inject a MockTransport.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_FILES = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
FOLDER_MIME = "application/vnd.google-apps.folder"
SCOPES = " ".join(
    [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/userinfo.email",
    ]
)


class DriveApiError(Exception):
    """Google Drive or OAuth returned an error we should surface to the admin."""


def oauth_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.google_drive_client_id
        and settings.google_drive_client_secret.get_secret_value()
    )


def oauth_redirect_uri() -> str:
    settings = get_settings()
    if settings.google_drive_oauth_redirect_uri:
        return settings.google_drive_oauth_redirect_uri
    return f"{settings.frontend_url.rstrip('/')}/admin/drive-backup/callback"


def authorization_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_drive_client_id,
        "redirect_uri": oauth_redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _client_auth() -> dict[str, str]:
    settings = get_settings()
    return {
        "client_id": settings.google_drive_client_id,
        "client_secret": settings.google_drive_client_secret.get_secret_value(),
    }


async def exchange_code(code: str, http: httpx.AsyncClient | None = None) -> dict:
    payload = {
        **_client_auth(),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": oauth_redirect_uri(),
    }
    return await _post_token(payload, http)


async def refresh_access_token(refresh_token: str, http: httpx.AsyncClient | None = None) -> str:
    payload = {
        **_client_auth(),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    data = await _post_token(payload, http)
    token = data.get("access_token")
    if not token:
        raise DriveApiError("Google did not return an access token")
    return token


async def _post_token(payload: dict, http: httpx.AsyncClient | None) -> dict:
    client = http or httpx.AsyncClient()
    owns = http is None
    try:
        response = await client.post(TOKEN_URL, data=payload)
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        return response.json()
    finally:
        if owns:
            await client.aclose()


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
        return str(body.get("error_description") or body.get("error") or response.text)[:500]
    except ValueError:
        return (response.text or f"HTTP {response.status_code}")[:500]


class GoogleDriveClient:
    def __init__(self, access_token: str, http: httpx.AsyncClient | None = None):
        self.access_token = access_token
        self._http = http
        self._owns_http = http is None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient()
        return self._http

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def user_email(self) -> str | None:
        client = await self._client()
        response = await client.get(USERINFO_URL, headers=self._headers())
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        return response.json().get("email")

    async def ensure_folder(self, name: str) -> str:
        existing = await self._find(name, mime=FOLDER_MIME)
        if existing:
            return existing
        client = await self._client()
        response = await client.post(
            DRIVE_FILES,
            headers=self._headers(),
            json={"name": name, "mimeType": FOLDER_MIME},
        )
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        return response.json()["id"]

    async def upsert_file(
        self, folder_id: str, name: str, content: bytes, file_id: str | None = None
    ) -> str:
        target = file_id or await self._find(name, parent=folder_id)
        client = await self._client()
        if target:
            response = await client.patch(
                f"{DRIVE_UPLOAD}/{target}",
                params={"uploadType": "media"},
                headers={**self._headers(), "Content-Type": "application/zip"},
                content=content,
            )
            if response.status_code >= 400:
                raise DriveApiError(_error_message(response))
            return target
        metadata = json.dumps({"name": name, "parents": [folder_id]})
        boundary = "securo_drive_boundary"
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{metadata}\r\n"
            f"--{boundary}\r\n"
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + content + f"\r\n--{boundary}--".encode("utf-8")
        response = await client.post(
            DRIVE_UPLOAD,
            params={"uploadType": "multipart"},
            headers={
                **self._headers(),
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            content=body,
        )
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        return response.json()["id"]

    async def list_files(self, folder_id: str) -> list[tuple[str, str]]:
        client = await self._client()
        query = f"'{folder_id}' in parents and trashed = false"
        response = await client.get(
            DRIVE_FILES,
            headers=self._headers(),
            params={"q": query, "fields": "files(id,name)", "pageSize": 1000},
        )
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        return [(f["id"], f["name"]) for f in response.json().get("files", [])]

    async def delete_file(self, file_id: str) -> None:
        client = await self._client()
        response = await client.delete(f"{DRIVE_FILES}/{file_id}", headers=self._headers())
        if response.status_code >= 400 and response.status_code != 404:
            raise DriveApiError(_error_message(response))

    async def _find(self, name: str, mime: str | None = None, parent: str | None = None) -> str | None:
        escaped = name.replace("\\", "\\\\").replace("'", r"\'")
        parts = [f"name = '{escaped}'", "trashed = false"]
        if mime:
            parts.append(f"mimeType = '{mime}'")
        if parent:
            parts.append(f"'{parent}' in parents")
        client = await self._client()
        response = await client.get(
            DRIVE_FILES,
            headers=self._headers(),
            params={"q": " and ".join(parts), "fields": "files(id)", "pageSize": 1},
        )
        if response.status_code >= 400:
            raise DriveApiError(_error_message(response))
        files = response.json().get("files") or []
        return files[0]["id"] if files else None
