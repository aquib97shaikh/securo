"""Instance-wide Google Drive backup: schedule, upload, retention.

One Google account, every workspace. Filenames carry the workspace name.
The Drive HTTP client is injected so tests can use an in-memory fake.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.services.crypto import decrypt, encrypt
from app.models.drive_backup import DriveBackupConfig
from app.models.workspace import Workspace
from app.services.backup_service import build_backup_archive
from app.services.drive_backup_naming import (
    dated_filename,
    files_to_delete,
    latest_filename,
    workspace_backup_stem,
)
from app.services.google_drive_client import (
    DriveApiError,
    GoogleDriveClient,
    oauth_configured,
    refresh_access_token,
)

logger = logging.getLogger(__name__)

FOLDER_NAME = "Securo Backups"
_WEEK = timedelta(days=7)


def is_schedule_due(
    schedule: str,
    last_scheduled_at: datetime | None,
    now: datetime,
) -> bool:
    """Whether a scheduled run should fire at `now` (UTC)."""
    if last_scheduled_at is None:
        return True
    if schedule == "weekly":
        return now - last_scheduled_at >= _WEEK
    # daily (and any unknown value treated as daily)
    return last_scheduled_at.astimezone(timezone.utc).date() < now.astimezone(timezone.utc).date()


async def upload_workspace_archive(
    session: AsyncSession,
    client,
    config: DriveBackupConfig,
    workspace_name: str,
    archive: bytes,
    today: date | None = None,
) -> None:
    """Write latest + dated zips for one workspace and prune older dated copies."""
    day = today or date.today()
    stem = workspace_backup_stem(workspace_name)
    folder_id = config.folder_id or await client.ensure_folder(FOLDER_NAME)
    config.folder_id = folder_id

    ids = dict(config.latest_file_ids or {})
    latest_id = await client.upsert_file(
        folder_id,
        latest_filename(stem),
        archive,
        ids.get(stem),
    )
    ids[stem] = latest_id
    await client.upsert_file(folder_id, dated_filename(stem, day), archive)
    config.latest_file_ids = ids

    listed = await client.list_files(folder_id)
    name_to_id = {name: file_id for file_id, name in listed}
    for doomed in files_to_delete(list(name_to_id), stem, keep=3):
        file_id = name_to_id.get(doomed)
        if file_id:
            await client.delete_file(file_id)

    await session.flush()


async def get_or_create_config(session: AsyncSession) -> DriveBackupConfig:
    row = await session.get(DriveBackupConfig, 1)
    if row is None:
        row = DriveBackupConfig(id=1, schedule="daily")
        session.add(row)
        await session.flush()
    return row


def is_connected(config: DriveBackupConfig) -> bool:
    return bool(config.refresh_token_encrypted)


def status_payload(config: DriveBackupConfig) -> dict:
    return {
        "available": oauth_configured(),
        "connected": is_connected(config),
        "google_email": config.google_email if is_connected(config) else None,
        "folder_name": FOLDER_NAME,
        "schedule": config.schedule if config.schedule in ("daily", "weekly") else "daily",
        "has_password": bool(config.password_encrypted),
        "last_run_at": config.last_run_at.isoformat() if config.last_run_at else None,
        "last_run_ok": config.last_run_ok,
        "last_run_error": config.last_run_error,
    }


def _record_run(config: DriveBackupConfig, ok: bool, error: str | None = None) -> None:
    config.last_run_at = datetime.now(timezone.utc)
    config.last_run_ok = ok
    config.last_run_error = (error or "")[:500] if not ok else None


async def finish_oauth(session: AsyncSession, refresh_token: str, email: str | None) -> DriveBackupConfig:
    config = await get_or_create_config(session)
    config.refresh_token_encrypted = encrypt(refresh_token)
    config.google_email = email
    config.folder_id = None
    config.latest_file_ids = None
    await session.commit()
    return config


async def disconnect(session: AsyncSession) -> DriveBackupConfig:
    config = await get_or_create_config(session)
    config.refresh_token_encrypted = None
    config.folder_id = None
    config.google_email = None
    config.latest_file_ids = None
    config.last_run_error = None
    await session.commit()
    return config


async def update_settings(
    session: AsyncSession,
    schedule: str | None,
    password: str | None,
    clear_password: bool,
) -> DriveBackupConfig:
    config = await get_or_create_config(session)
    if schedule in ("daily", "weekly"):
        config.schedule = schedule
    if clear_password:
        config.password_encrypted = None
    elif password:
        config.password_encrypted = encrypt(password)
    await session.commit()
    return config


async def _client_for(config: DriveBackupConfig) -> GoogleDriveClient:
    refresh = decrypt(config.refresh_token_encrypted)
    if not refresh:
        raise DriveApiError("Google Drive is not connected")
    access = await refresh_access_token(refresh)
    return GoogleDriveClient(access)


async def maybe_upload_workspace(session: AsyncSession, workspace: Workspace, files: dict) -> None:
    """Best-effort Drive upload. Failures are recorded; callers still return the zip."""
    if not oauth_configured():
        return
    config = await session.get(DriveBackupConfig, 1)
    if config is None or not is_connected(config):
        return
    try:
        password = decrypt(config.password_encrypted)
        archive = build_backup_archive(files, password)
        client = await _client_for(config)
        try:
            await upload_workspace_archive(session, client, config, workspace.name, archive)
        finally:
            await client.aclose()
        _record_run(config, True)
        await session.commit()
    except Exception as exc:
        logger.warning("Drive backup upload failed: %s", exc)
        try:
            _record_run(config, False, str(exc))
            await session.commit()
        except Exception:
            logger.exception("Failed to record Drive backup error")


async def run_scheduled_backups(session: AsyncSession, collect) -> dict:
    """Backup every non-archived workspace if the cadence is due.

    `collect` is `async (session, workspace) -> dict` of backup files, injected
    so this module does not import the export API.
    """
    if not oauth_configured():
        return {"skipped": True, "reason": "oauth_not_configured"}
    config = await get_or_create_config(session)
    if not is_connected(config):
        return {"skipped": True, "reason": "not_connected"}
    now = datetime.now(timezone.utc)
    if not is_schedule_due(config.schedule, config.last_scheduled_at, now):
        return {"skipped": True, "reason": "not_due"}

    workspaces = (
        await session.execute(select(Workspace).where(Workspace.is_archived.is_(False)))
    ).scalars().all()
    password = decrypt(config.password_encrypted)
    errors: list[str] = []
    client = await _client_for(config)
    try:
        for workspace in workspaces:
            try:
                files = await collect(session, workspace)
                archive = build_backup_archive(files, password)
                await upload_workspace_archive(session, client, config, workspace.name, archive)
            except Exception as exc:
                logger.warning("Drive backup failed for workspace %s: %s", workspace.id, exc)
                errors.append(f"{workspace.name}: {exc}")
    finally:
        await client.aclose()

    if errors:
        _record_run(config, False, "; ".join(errors)[:500])
    else:
        config.last_scheduled_at = now
        _record_run(config, True)
    await session.commit()
    return {"skipped": False, "ok": not errors, "workspaces": len(workspaces), "errors": errors}
