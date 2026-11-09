from sqlalchemy import delete, update

from app.core.config import Settings
from app.db import session as db_session
from app.jobs.registry import job
from app.models.operation_log import OperationLog
from app.core.time import MS_PER_DAY, now_ms
from app.models.user import User


@job("clear_expired_login_locks", label="清理过期登录锁定")
def clear_expired_login_locks() -> None:
    factory = db_session.session_factory
    if factory is None:
        return
    db = factory()
    try:
        now = now_ms()
        db.execute(
            update(User)
            .where(User.locked_until.is_not(None))
            .where(User.locked_until < now)
            .values(failed_login_count=0, locked_until=None)
        )
        db.commit()
    finally:
        db.close()


@job("purge_old_operation_logs", label="清理操作日志")
def purge_old_operation_logs(retention_days: int | None = None) -> None:
    days = retention_days if retention_days is not None else _default_retention_days()
    if days <= 0:
        return
    factory = db_session.session_factory
    if factory is None:
        return
    db = factory()
    try:
        cutoff = now_ms() - days * MS_PER_DAY
        db.execute(delete(OperationLog).where(OperationLog.created_at < cutoff))
        db.commit()
    finally:
        db.close()


def _default_retention_days() -> int:
    return Settings().operation_log_retention_days
