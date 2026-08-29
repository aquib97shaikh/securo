# Google Drive workspace backup

Date: 2026-08-31

## Problem

Backup today only downloads a zip of the current workspace. There is no way to keep a copy on Google Drive, on a schedule or when the user clicks Backup.

## Decision

Instance-wide Google Drive backup, configured by an admin.

- Admin connects one Google account (OAuth) and sets schedule (daily or weekly) plus an optional zip password.
- Each run writes files named after the workspace into a `Securo Backups` folder.
- Retention per workspace: `{Name}-latest.zip` (overwritten) plus the last 3 dated `{Name}-YYYY-MM-DD.zip` files. Same-day dated file is overwritten. Latest does not count toward the 3.
- Manual Backup still downloads the current workspace zip. If Drive is connected, that run also refreshes that workspace’s Drive files. Drive encryption uses the stored optional password; the dialog password still applies only to the local download.
- Scheduled Celery job backs up every non-archived workspace when the cadence is due.

## Out of scope

- Per-workspace Drive accounts or folders
- Other destinations (S3, local Drive folder, Dropbox)
- Restoring from a Drive backup inside Securo
- Google Drive version-history UI

## Operator setup

`GOOGLE_DRIVE_CLIENT_ID` and `GOOGLE_DRIVE_CLIENT_SECRET` from a Google Cloud OAuth client with the Drive File and userinfo.email scopes. Redirect URI: `{FRONTEND_URL}/admin/drive-backup/callback`. Without those env vars the admin card explains they are missing and Backup stays download-only.

## Errors

Manual download always proceeds even if Drive upload fails. Last-run status records success or a short error. A revoked token asks the admin to reconnect. A failed scheduled run stays due so the next hourly tick retries; `last_scheduled_at` is stored only after every workspace succeeds.
