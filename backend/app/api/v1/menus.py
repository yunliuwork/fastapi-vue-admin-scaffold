from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.errors import AppError
from app.core.response import ok
from app.db.session import get_db
from app.models.menu import Menu
from app.schemas.bodies import MenuWrite
from app.services.access import all_menus, build_tree, delete_menu, menu_dict, save_menu

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("")
def get_menus(
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:menu:list")),
):
    return ok(build_tree(all_menus(db)))


@router.post("")
def post_menu(
    body: MenuWrite,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:menu:create")),
):
    return ok(menu_dict(save_menu(db, body, actor=_user)))


@router.put("/{menu_id}")
def put_menu(
    menu_id: int,
    body: MenuWrite,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:menu:update")),
):
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise AppError(404, "菜单不存在")
    return ok(menu_dict(save_menu(db, body, menu, actor=_user)))


@router.delete("/{menu_id}")
def remove_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("system:menu:delete")),
):
    delete_menu(db, menu_id, _user)
    return ok(None)
