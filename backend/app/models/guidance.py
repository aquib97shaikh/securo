import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GuidanceFeedback(Base):
    """User feedback, snooze, dismissal, and action records for guidance insights."""

    __tablename__ = "guidance_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    insight_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # active, snoozed, dismissed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # True = helpful, False = not helpful, None = not rated
    is_helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
