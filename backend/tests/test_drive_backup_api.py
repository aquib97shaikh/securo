"""Admin Drive backup status and settings, plus the download-dialog flag."""
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from pydantic import SecretStr

from app.core.config import get_settings


@pytest.fixture
def drive_oauth_env(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_drive_client_id", "drive-client")
    monkeypatch.setattr(settings, "google_drive_client_secret", SecretStr("drive-secret"))
    return settings


@pytest.mark.asyncio
async def test_drive_status_requires_admin(client: AsyncClient, auth_headers):
    resp = await client.get("/api/admin/drive-backup", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_drive_status_unconfigured(client: AsyncClient, admin_auth_headers, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_drive_client_id", "")
    monkeypatch.setattr(settings, "google_drive_client_secret", SecretStr(""))
    resp = await client.get("/api/admin/drive-backup", headers=admin_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["connected"] is False
    assert body["folder_name"] == "Securo Backups"
    assert body["schedule"] == "daily"
    assert body["has_password"] is False


@pytest.mark.asyncio
async def test_drive_status_available_when_env_is_set(
    client: AsyncClient, admin_auth_headers, drive_oauth_env
):
    resp = await client.get("/api/admin/drive-backup", headers=admin_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["available"] is True
    assert resp.json()["connected"] is False


@pytest.mark.asyncio
async def test_update_schedule_and_password(client: AsyncClient, admin_auth_headers):
    resp = await client.patch(
        "/api/admin/drive-backup",
        json={"schedule": "weekly", "password": "correct horse"},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["schedule"] == "weekly"
    assert resp.json()["has_password"] is True

    cleared = await client.patch(
        "/api/admin/drive-backup",
        json={"clear_password": True},
        headers=admin_auth_headers,
    )
    assert cleared.status_code == 200
    assert cleared.json()["has_password"] is False
    assert cleared.json()["schedule"] == "weekly"


@pytest.mark.asyncio
async def test_oauth_url_refuses_when_env_missing(client: AsyncClient, admin_auth_headers, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_drive_client_id", "")
    monkeypatch.setattr(settings, "google_drive_client_secret", SecretStr(""))
    resp = await client.get("/api/admin/drive-backup/oauth-url", headers=admin_auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_oauth_url_returns_google_authorize_link(
    client: AsyncClient, admin_auth_headers, drive_oauth_env, monkeypatch
):
    monkeypatch.setattr(
        "app.api.drive_backup.oauth_state.store_state",
        AsyncMock(return_value="opaque-state"),
    )
    resp = await client.get("/api/admin/drive-backup/oauth-url", headers=admin_auth_headers)
    assert resp.status_code == 200
    url = resp.json()["url"]
    assert "accounts.google.com" in url
    assert "opaque-state" in url
    assert "access_type=offline" in url


@pytest.mark.asyncio
async def test_export_drive_status_is_false_when_disconnected(
    client: AsyncClient, auth_headers
):
    resp = await client.get("/api/export/drive-status", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"connected": False}


@pytest.mark.asyncio
async def test_backup_still_downloads_when_drive_upload_would_apply(
    client: AsyncClient, auth_headers
):
    resp = await client.post("/api/export/backup", json={}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
