import json

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.time import MS_PER_DAY, now_ms
from app.core.errors import AppError
from app.jobs.registry import get_handler, handler_options
from app.models.scheduled_job import ScheduledJob, ScheduledJobLog
from app.models.user import User
from app.scheduler import runtime


def ensure_default_jobs(db: Session, settings: Settings) -> None:
    defaults = [
        {
            "name": "清理过期登录锁定",
            "job_key": "clear_expired_login_locks",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"hours": 1}, ensure_ascii=False),
            "params": "{}",
            "builtin": True,
            "remark": "锁定时间已过的账号恢复可登录",
        },
    ]
    if settings.operation_log_retention_days > 0:
        defaults.append(
            {
                "name": "清理操作日志",
                "job_key": "purge_old_operation_logs",
                "trigger_type": "cron",
                "trigger_config": json.dumps({"expr": "0 3 * * *"}, ensure_ascii=False),
                "params": json.dumps({"retention_days": settings.operation_log_retention_days}, ensure_ascii=False),
                "builtin": True,
                "remark": "删除超过保留天数的操作日志",
            }
        )
    for item in defaults:
        existing = db.scalar(select(ScheduledJob).where(ScheduledJob.job_key == item["job_key"]))
        if existing is not None:
            continue
        db.add(ScheduledJob(enabled=True, **item))
    db.commit()


def job_dict(row: ScheduledJob) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "job_key": row.job_key,
        "trigger_type": row.trigger_type,
        "trigger_config": row.trigger_config,
        "params": row.params,
        "enabled": row.enabled,
        "builtin": row.builtin,
        "remark": row.remark,
        "trigger_label": runtime.trigger_label(row),
        "last_run_at": row.last_run_at,
        "last_status": row.last_status or "",
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def log_dict(row: ScheduledJobLog) -> dict:
    return {
        "id": row.id,
        "job_id": row.job_id,
        "job_name": row.job_name,
        "status": row.status,
        "message": row.message,
        "trigger_mode": row.trigger_mode,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


def list_jobs(db: Session, page: int, page_size: int) -> tuple[list[ScheduledJob], int]:
    total = db.scalar(select(func.count()).select_from(ScheduledJob)) or 0
    rows = list(
        db.scalars(
            select(ScheduledJob)
            .order_by(ScheduledJob.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def get_job(db: Session, job_id: int) -> ScheduledJob:
    row = db.get(ScheduledJob, job_id)
    if row is None:
        raise AppError(404, "任务不存在")
    return row


def create_job(
    db: Session,
    name: str,
    job_key: str,
    trigger_type: str,
    trigger_config: str,
    params: str,
    enabled: bool,
    remark: str,
) -> ScheduledJob:
    if get_handler(job_key) is None:
        raise AppError(400, "任务处理器不存在")
    exists = db.scalar(select(ScheduledJob).where(ScheduledJob.job_key == job_key))
    if exists is not None:
        raise AppError(400, "该任务已存在")
    _validate_trigger(trigger_type, trigger_config)
    row = ScheduledJob(
        name=name,
        job_key=job_key,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        params=params or "{}",
        enabled=enabled,
        builtin=False,
        remark=remark,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    runtime.sync_job(row)
    return row


def update_job(
    db: Session,
    job_id: int,
    name: str,
    trigger_type: str,
    trigger_config: str,
    params: str,
    enabled: bool,
    remark: str,
) -> ScheduledJob:
    row = get_job(db, job_id)
    _validate_trigger(trigger_type, trigger_config)
    row.name = name
    row.trigger_type = trigger_type
    row.trigger_config = trigger_config
    row.params = params or "{}"
    row.enabled = enabled
    row.remark = remark
    row.updated_at = now_ms()
    db.commit()
    db.refresh(row)
    runtime.sync_job(row)
    return row


def set_job_enabled(db: Session, job_id: int, enabled: bool) -> ScheduledJob:
    row = get_job(db, job_id)
    row.enabled = enabled
    row.updated_at = now_ms()
    db.commit()
    db.refresh(row)
    runtime.sync_job(row)
    return row


def delete_job(db: Session, job_id: int) -> None:
    row = get_job(db, job_id)
    if row.builtin:
        raise AppError(400, "内置任务不能删除")
    scheduler = runtime.scheduler_instance()
    if scheduler is not None:
        job_id_str = runtime.job_scheduler_id(row.id)
        if scheduler.get_job(job_id_str):
            scheduler.remove_job(job_id_str)
    db.delete(row)
    db.commit()


def list_job_logs(db: Session, job_id: int, page: int, page_size: int) -> tuple[list[ScheduledJobLog], int]:
    get_job(db, job_id)
    filters = [ScheduledJobLog.job_id == job_id]
    total = db.scalar(select(func.count()).select_from(ScheduledJobLog).where(*filters)) or 0
    rows = list(
        db.scalars(
            select(ScheduledJobLog)
            .where(*filters)
            .order_by(ScheduledJobLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def job_log_stats(db: Session) -> dict:
    now = now_ms()

    def older_than(days: int) -> int:
        stmt = (
            select(func.count())
            .select_from(ScheduledJobLog)
            .where(ScheduledJobLog.started_at < now - days * MS_PER_DAY)
        )
        return db.scalar(stmt) or 0

    return {
        "total": db.scalar(select(func.count()).select_from(ScheduledJobLog)) or 0,
        "older_than_7d": older_than(7),
        "older_than_30d": older_than(30),
    }


def cleanup_job_logs(db: Session, days: int | None) -> int:
    stmt = delete(ScheduledJobLog)
    if days is not None:
        stmt = stmt.where(ScheduledJobLog.started_at < now_ms() - days * MS_PER_DAY)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


def run_job(db: Session, job_id: int) -> ScheduledJobLog:
    try:
        return runtime.run_job_now(db, job_id)
    except ValueError as exc:
        raise AppError(400, str(exc)) from exc


def available_handlers() -> list[dict[str, str]]:
    return handler_options()


def _validate_trigger(trigger_type: str, trigger_config: str) -> None:
    if trigger_type not in {"interval", "cron"}:
        raise AppError(400, "触发类型无效")
    try:
        config = json.loads(trigger_config or "{}")
    except json.JSONDecodeError as exc:
        raise AppError(400, "触发配置必须是 JSON") from exc
    if not isinstance(config, dict):
        raise AppError(400, "触发配置必须是 JSON 对象")
    dummy = ScheduledJob(
        id=0,
        name="",
        job_key="",
        trigger_type=trigger_type,
        trigger_config=json.dumps(config, ensure_ascii=False),
    )
    try:
        runtime.build_trigger(dummy, Settings().scheduler_timezone)
    except Exception as exc:
        raise AppError(400, "触发配置无效") from exc


