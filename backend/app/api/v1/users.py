from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response import ok
from app.db.session import get_db
from app.schemas.bodies import ResetPassword, StatusUpdate, UserCreate, UserUpdate
from app.services.users import (
    create_user,
    get_user,
    list_users,
    reset_password,
    reset_totp_binding,
    update_status,
    update_user,
    user_dict,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(
    username: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:user:list")),
):
    items, total = list_users(db, username, status, page, page_size)
    return ok(
        {
            "items": [user_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("")
def post_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:user:create")),
):
    user = create_user(
        db,
        body.username,
        body.password,
        body.nickname,
        body.role_ids,
        body.totp_required,
        _user,
    )
    return ok(user_dict(user))


@router.get("/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:user:list")),
):
    return ok(user_dict(get_user(db, user_id)))


@router.put("/{user_id}")
def put_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("system:user:update")),
):
    user = update_user(
        db,
        user_id,
        body.nickname,
        body.status,
        body.role_ids,
        body.totp_required,
        actor,
    )
    return ok(user_dict(user))


@router.patch("/{user_id}/status")
def patch_status(
    user_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("system:user:disable")),
):
    user = update_status(db, user_id, body.status, actor)
    return ok(user_dict(user))


@router.post("/{user_id}/reset-password")
def post_reset_password(
    user_id: int,
    body: ResetPassword,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("system:user:reset-password")),
):
    reset_password(db, user_id, body.password, actor)
    return ok(None)


@router.post("/{user_id}/reset-totp")
def post_reset_totp(
    user_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("system:user:update")),
):
    user = reset_totp_binding(db, user_id, actor)
    return ok(user_dict(user))
