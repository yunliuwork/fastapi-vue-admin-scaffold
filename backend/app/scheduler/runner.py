from apscheduler.schedulers.background import BackgroundScheduler

import app.jobs.tasks  # noqa: F401

from app.core.config import Settings
from app.db import session as db_session
from app.scheduler import runtime
from app.services.scheduled_jobs import ensure_default_jobs


def start_scheduler(settings: Settings) -> BackgroundScheduler | None:
    if not settings.scheduler_enabled:
        runtime.bind_scheduler(None, settings)
        return None
    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    runtime.bind_scheduler(scheduler, settings)
    db = db_session.session_factory()
    try:
        ensure_default_jobs(db, settings)
        runtime.reload_all(db)
    finally:
        db.close()
    scheduler.start()
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler | None) -> None:
    if scheduler is not None:
        scheduler.shutdown(wait=False)
    runtime.bind_scheduler(None, Settings())
