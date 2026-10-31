from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response import ok
from app.db.session import get_db
from app.models.user import User
from app.schemas.bodies import ScheduledJobCreate, ScheduledJobUpdate
from app.services.logs import write_log
from app.services.scheduled_jobs import (
    available_handlers,
    create_job,
    delete_job,
    get_job,
    job_dict,
    list_job_logs,
    list_jobs,
    log_dict,
    run_job,
    update_job,
)

router = APIRouter(prefix="/scheduled-jobs", tags=["scheduled-jobs"])


@router.get("")
def get_scheduled_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:job:list")),
):
    items, total = list_jobs(db, page, page_size)
    return ok({"items": [job_dict(item) for item in items], "total": total, "page": page, "page_size": page_size})


@router.get("/handlers")
def get_job_handlers(_user=Depends(require_permission("system:job:list"))):
    return ok(available_handlers())


@router.post("")
def post_scheduled_job(
    body: ScheduledJobCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("system:job:create")),
):
    row = create_job(
        db,
        body.name,
        body.job_key,
        body.trigger_type,
        body.trigger_config,
        body.params,
        body.enabled,
        body.remark,
    )
    write_log(db, actor, "新增定时任务", row.name)
    db.commit()
    return ok(job_dict(row))


@router.put("/{job_id}")
def put_scheduled_job(
    job_id: int,
    body: ScheduledJobUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("system:job:update")),
):
    row = update_job(
        db,
        job_id,
        body.name,
        body.trigger_type,
        body.trigger_config,
        body.params,
        body.enabled,
        body.remark,
    )
    write_log(db, actor, "编辑定时任务", row.name)
    db.commit()
    return ok(job_dict(row))


@router.delete("/{job_id}")
def remove_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("system:job:delete")),
):
    row = get_job(db, job_id)
    name = row.name
    delete_job(db, job_id)
    write_log(db, actor, "删除定时任务", name)
    db.commit()
    return ok(None)


@router.post("/{job_id}/run")
def trigger_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("system:job:run")),
):
    row = get_job(db, job_id)
    log = run_job(db, job_id)
    write_log(db, actor, "执行定时任务", row.name)
    db.commit()
    return ok(log_dict(log))


@router.get("/{job_id}/logs")
def get_scheduled_job_logs(
    job_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:job:list")),
):
    items, total = list_job_logs(db, job_id, page, page_size)
    return ok({"items": [log_dict(item) for item in items], "total": total, "page": page, "page_size": page_size})
