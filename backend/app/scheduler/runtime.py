import json
import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.jobs.registry import call_handler
from app.models.scheduled_job import ScheduledJob, ScheduledJobLog
from app.core.time import now_ms

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_settings: Settings | None = None


def bind_scheduler(scheduler: BackgroundScheduler | None, settings: Settings) -> None:
    global _scheduler, _settings
    _scheduler = scheduler
    _settings = settings


def scheduler_instance() -> BackgroundScheduler | None:
    return _scheduler


def job_scheduler_id(job_id: int) -> str:
    return f"scheduled-job-{job_id}"


def build_trigger(job: ScheduledJob, timezone: str):
    config = json.loads(job.trigger_config or "{}")
    if job.trigger_type == "interval":
        return IntervalTrigger(timezone=timezone, **config)
    if job.trigger_type == "cron":
        expr = config.get("expr")
        if expr:
            return CronTrigger.from_crontab(str(expr), timezone=timezone)
        return CronTrigger(timezone=timezone, **{k: v for k, v in config.items() if k != "expr"})
    raise ValueError("不支持的触发类型")


def parse_params(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def trigger_label(job: ScheduledJob) -> str:
    config = json.loads(job.trigger_config or "{}")
    if job.trigger_type == "interval":
        hours = config.get("hours")
        minutes = config.get("minutes")
        if hours:
            return f"每 {hours} 小时"
        if minutes:
            return f"每 {minutes} 分钟"
        return "间隔执行"
    if job.trigger_type == "cron":
        expr = config.get("expr")
        if expr:
            return f"Cron {expr}"
        hour = config.get("hour")
        minute = config.get("minute", 0)
        if hour is not None:
            return f"每天 {int(hour):02d}:{int(minute):02d}"
    return job.trigger_config


def execute_job(job_id: int, *, trigger_mode: str = "scheduled", force: bool = False) -> None:
    from app.db import session as db_session

    factory = db_session.session_factory
    if factory is None:
        return
    db = factory()
    try:
        row = db.get(ScheduledJob, job_id)
        # 定时触发尊重启停；手动执行（force）在停用状态下也要能跑
        if row is None or (not row.enabled and not force):
            return
        job_key = row.job_key
        job_name = row.name
        params_raw = row.params
    finally:
        db.close()

    started = now_ms()
    status = "success"
    message = "执行完成"
    try:
        call_handler(job_key, parse_params(params_raw))
    except Exception as exc:
        status = "failure"
        message = str(exc)[:2000]
        logger.exception("scheduled job %s failed", job_key)

    finished = now_ms()
    db = factory()
    try:
        row = db.get(ScheduledJob, job_id)
        if row is None:
            return
        db.add(
            ScheduledJobLog(
                job_id=job_id,
                job_name=job_name,
                status=status,
                message=message,
                trigger_mode=trigger_mode,
                started_at=started,
                finished_at=finished,
            )
        )
        row.last_run_at = finished
        row.last_status = status
        row.updated_at = finished
        db.commit()
    finally:
        db.close()


def sync_job(job: ScheduledJob) -> None:
    scheduler = _scheduler
    settings = _settings
    if scheduler is None or settings is None:
        return
    job_id = job_scheduler_id(job.id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    if not job.enabled:
        return
    scheduler.add_job(
        execute_job,
        build_trigger(job, settings.scheduler_timezone),
        id=job_id,
        kwargs={"job_id": job.id, "trigger_mode": "scheduled"},
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def reload_all(db: Session) -> None:
    rows = list(db.scalars(select(ScheduledJob).order_by(ScheduledJob.id)).all())
    for row in rows:
        sync_job(row)


def run_job_now(db: Session, job_id: int) -> ScheduledJobLog:
    row = db.get(ScheduledJob, job_id)
    if row is None:
        raise ValueError("任务不存在")
    execute_job(job_id, trigger_mode="manual", force=True)
    db.refresh(row)
    log = db.scalar(
        select(ScheduledJobLog)
        .where(ScheduledJobLog.job_id == job_id)
        .order_by(ScheduledJobLog.id.desc())
        .limit(1)
    )
    if log is None:
        raise RuntimeError("未找到执行记录")
    return log
