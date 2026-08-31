from typing import Literal, Optional

from pydantic import BaseModel, Field, SecretStr


class DriveBackupStatus(BaseModel):
    available: bool
    connected: bool
    google_email: Optional[str] = None
    folder_name: str
    schedule: Literal["daily", "weekly"]
    has_password: bool
    last_run_at: Optional[str] = None
    last_run_ok: Optional[bool] = None
    last_run_error: Optional[str] = None


class DriveBackupSettingsUpdate(BaseModel):
    schedule: Optional[Literal["daily", "weekly"]] = None
    password: SecretStr | None = Field(default=None, min_length=8, max_length=256)
    clear_password: bool = False


class DriveOAuthUrlResponse(BaseModel):
    url: str


class DriveOAuthCallbackRequest(BaseModel):
    code: str
    state: str
