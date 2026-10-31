from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response import ok
from app.db.session import get_db
from app.services.logs import list_logs, log_dict

router = APIRouter(prefix="/operation-logs", tags=["operation-logs"])


@router.get("")
def get_operation_logs(
    username: str | None = None,
    action: str | None = None,
    outcome: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:log:list")),
):
    items, total = list_logs(db, username, action, outcome, page, page_size)
    return ok(
        {
            "items": [log_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )
