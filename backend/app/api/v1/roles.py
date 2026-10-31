from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response import ok
from app.db.session import get_db
from app.schemas.bodies import RoleWrite
from app.services.access import delete_role, get_role, list_roles, role_dict, save_role

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:role:list")),
):
    items, total = list_roles(db, page, page_size)
    return ok(
        {
            "items": [role_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("")
def post_role(
    body: RoleWrite,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:role:create")),
):
    return ok(role_dict(save_role(db, body, actor=_user)))


@router.get("/{role_id}")
def get_role_detail(
    role_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:role:list")),
):
    return ok(role_dict(get_role(db, role_id)))


@router.put("/{role_id}")
def put_role(
    role_id: int,
    body: RoleWrite,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:role:update")),
):
    role = get_role(db, role_id)
    return ok(role_dict(save_role(db, body, role, actor=_user)))


@router.delete("/{role_id}")
def remove_role(
    role_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:role:delete")),
):
    delete_role(db, role_id, _user)
    return ok(None)
