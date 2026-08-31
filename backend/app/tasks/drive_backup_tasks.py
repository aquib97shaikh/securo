import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.export import _collect
from app.core.config import get_settings
from app.services.drive_backup_service import run_scheduled_backups
from app.worker import celery_app

logger = logging.getLogger(__name__)


def _make_session_maker():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run_scheduled() -> dict:
    engine, session_maker = _make_session_maker()
    try:
        async with session_maker() as session:

            async def collect(sess, workspace):
                return await _collect(workspace, sess)

            return await run_scheduled_backups(session, collect)
    finally:
        await engine.dispose()


@celery_app.task(name="app.tasks.drive_backup_tasks.run_scheduled_drive_backups")
def run_scheduled_drive_backups() -> dict:
    """Hourly tick; the service skips when the daily/weekly cadence is not due."""
    try:
        return asyncio.run(_run_scheduled())
    except Exception:
        logger.exception("Scheduled Google Drive backup failed")
        raise
