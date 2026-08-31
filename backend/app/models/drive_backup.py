"""Singleton row holding the instance Google Drive backup connection."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DriveBackupConfig(Base):
    __tablename__ = "drive_backup_config"

    # One row for the install. Id is always 1.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    folder_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    google_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    schedule: Mapped[str] = mapped_column(String(16), default="daily", server_default="daily")
    password_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latest_file_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_run_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
