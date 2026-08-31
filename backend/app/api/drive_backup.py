"""Admin Google Drive backup: connect, schedule, optional password."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_superuser
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.drive_backup import (
    DriveBackupSettingsUpdate,
    DriveBackupStatus,
    DriveOAuthCallbackRequest,
    DriveOAuthUrlResponse,
)
from app.services import drive_backup_service, oauth_state
from app.services.google_drive_client import (
    DriveApiError,
    GoogleDriveClient,
    authorization_url,
    exchange_code,
    oauth_configured,
)

router = APIRouter(prefix="/api/admin/drive-backup", tags=["admin"])


@router.get("", response_model=DriveBackupStatus)
async def get_drive_backup_status(
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(current_superuser),
):
    config = await drive_backup_service.get_or_create_config(session)
    return DriveBackupStatus.model_validate(drive_backup_service.status_payload(config))


@router.patch("", response_model=DriveBackupStatus)
async def update_drive_backup_settings(
    body: DriveBackupSettingsUpdate,
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(current_superuser),
):
    password = body.password.get_secret_value() if body.password else None
    config = await drive_backup_service.update_settings(
        session, body.schedule, password, body.clear_password
    )
    return DriveBackupStatus.model_validate(drive_backup_service.status_payload(config))


@router.get("/oauth-url", response_model=DriveOAuthUrlResponse)
async def get_drive_oauth_url(
    user: User = Depends(current_superuser),
):
    if not oauth_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET are not set",
        )
    state = await oauth_state.store_state(
        {"purpose": "drive_backup", "user_id": str(user.id)}
    )
    return DriveOAuthUrlResponse(url=authorization_url(state))


@router.post("/oauth/callback", response_model=DriveBackupStatus)
async def drive_oauth_callback(
    body: DriveOAuthCallbackRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_superuser),
):
    consumed = await oauth_state.consume_state(body.state)
    if not consumed or consumed.get("purpose") != "drive_backup":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    if consumed.get("user_id") != str(user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    try:
        tokens = await exchange_code(body.code)
        refresh = tokens.get("refresh_token")
        if not refresh:
            raise DriveApiError(
                "Google did not return a refresh token. Reconnect and grant offline access."
            )
        access = tokens.get("access_token") or ""
        email = None
        if access:
            client = GoogleDriveClient(access)
            try:
                email = await client.user_email()
            finally:
                await client.aclose()
        config = await drive_backup_service.finish_oauth(session, refresh, email)
    except DriveApiError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DriveBackupStatus.model_validate(drive_backup_service.status_payload(config))


@router.post("/disconnect", response_model=DriveBackupStatus)
async def disconnect_drive(
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(current_superuser),
):
    config = await drive_backup_service.disconnect(session)
    return DriveBackupStatus.model_validate(drive_backup_service.status_payload(config))
