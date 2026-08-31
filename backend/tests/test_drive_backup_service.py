"""Google Drive backup orchestration — schedule due-ness and upload retention.

Drive HTTP is replaced with an in-memory fake so these tests pin behaviour
(overwrite latest, keep 3 dated copies, skip other workspaces) without a
Google account.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drive_backup import DriveBackupConfig
from app.services.drive_backup_naming import dated_filename, latest_filename
from app.services.drive_backup_service import (
    FOLDER_NAME,
    is_schedule_due,
    upload_workspace_archive,
)


@dataclass
class FakeFile:
    id: str
    name: str
    content: bytes


class FakeDriveClient:
    def __init__(self) -> None:
        self.files: dict[str, FakeFile] = {}
        self.folder_name: str | None = None
        self._n = 0

    async def ensure_folder(self, name: str) -> str:
        self.folder_name = name
        return "folder-1"

    async def upsert_file(
        self, folder_id: str, name: str, content: bytes, file_id: str | None = None
    ) -> str:
        if file_id and file_id in self.files:
            self.files[file_id] = FakeFile(file_id, name, content)
            return file_id
        for existing in self.files.values():
            if existing.name == name:
                self.files[existing.id] = FakeFile(existing.id, name, content)
                return existing.id
        self._n += 1
        fid = f"file-{self._n}"
        self.files[fid] = FakeFile(fid, name, content)
        return fid

    async def list_files(self, folder_id: str) -> list[tuple[str, str]]:
        return [(f.id, f.name) for f in self.files.values()]

    async def delete_file(self, file_id: str) -> None:
        self.files.pop(file_id, None)


def test_daily_schedule_is_due_when_never_run():
    assert is_schedule_due("daily", last_scheduled_at=None, now=datetime.now(timezone.utc))


def test_daily_schedule_is_not_due_on_the_same_utc_day():
    now = datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc)
    last = datetime(2026, 8, 31, 1, 0, tzinfo=timezone.utc)
    assert is_schedule_due("daily", last, now) is False


def test_daily_schedule_is_due_the_next_utc_day():
    now = datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc)
    last = datetime(2026, 8, 31, 23, 0, tzinfo=timezone.utc)
    assert is_schedule_due("daily", last, now) is True


def test_weekly_schedule_is_due_after_seven_days():
    now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
    last = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    assert is_schedule_due("weekly", last, now) is True


def test_weekly_schedule_is_not_due_before_seven_days():
    now = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
    last = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    assert is_schedule_due("weekly", last, now) is False


@pytest.mark.asyncio
async def test_upload_writes_latest_and_dated_and_prunes_older_dated(
    session: AsyncSession, clean_db
):
    client = FakeDriveClient()
    config = DriveBackupConfig(id=1, folder_id="folder-1")
    session.add(config)
    await session.flush()

    archive = b"zip-bytes"
    stem = "Personal"
    for day in (date(2026, 8, 27), date(2026, 8, 28), date(2026, 8, 29), date(2026, 8, 30)):
        await client.upsert_file("folder-1", dated_filename(stem, day), b"old")
    await client.upsert_file("folder-1", "Business-2026-08-01.zip", b"other")

    await upload_workspace_archive(
        session,
        client,
        config,
        workspace_name="Personal",
        archive=archive,
        today=date(2026, 8, 31),
    )

    names = {f.name for f in client.files.values()}
    assert latest_filename(stem) in names
    assert dated_filename(stem, date(2026, 8, 31)) in names
    assert dated_filename(stem, date(2026, 8, 30)) in names
    assert dated_filename(stem, date(2026, 8, 29)) in names
    assert dated_filename(stem, date(2026, 8, 28)) not in names
    assert dated_filename(stem, date(2026, 8, 27)) not in names
    assert "Business-2026-08-01.zip" in names
    assert client.folder_name in (None, FOLDER_NAME)

    latest = next(f for f in client.files.values() if f.name == latest_filename(stem))
    assert latest.content == archive
    assert config.latest_file_ids[stem] == latest.id


@pytest.mark.asyncio
async def test_upload_overwrites_the_same_days_dated_file(
    session: AsyncSession, clean_db
):
    client = FakeDriveClient()
    config = DriveBackupConfig(id=1, folder_id="folder-1")
    session.add(config)
    await session.flush()

    await upload_workspace_archive(
        session, client, config, "Personal", b"first", today=date(2026, 8, 31)
    )
    first_ids = {f.name: f.id for f in client.files.values()}
    await upload_workspace_archive(
        session, client, config, "Personal", b"second", today=date(2026, 8, 31)
    )

    dated = next(
        f for f in client.files.values() if f.name == dated_filename("Personal", date(2026, 8, 31))
    )
    latest = next(f for f in client.files.values() if f.name == latest_filename("Personal"))
    assert dated.content == b"second"
    assert latest.content == b"second"
    assert dated.id == first_ids[dated.name]
    assert latest.id == first_ids[latest.name]
    assert len(client.files) == 2
