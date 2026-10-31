from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.associations import role_menus, user_roles
from app.models.menu import Menu
from app.models.role import Role
from app.models.user import User
from app.schemas.bodies import MenuWrite, RoleWrite
from app.services.logs import write_log


def menu_dict(menu: Menu, children: list[dict] | None = None) -> dict:
    return {
        "id": menu.id,
        "parent_id": menu.parent_id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "path": menu.path,
        "component": menu.component,
        "permission": menu.permission,
        "icon": menu.icon,
        "sort": menu.sort,
        "visible": menu.visible,
        "status": menu.status,
        "children": children if children is not None else [],
    }


def role_dict(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "remark": role.remark,
        "status": role.status,
        "menu_ids": [menu.id for menu in role.menus],
    }


def all_menus(db: Session) -> list[Menu]:
    return list(db.scalars(select(Menu).order_by(Menu.sort, Menu.id)).all())


def build_tree(menus: list[Menu]) -> list[dict]:
    nodes = {menu.id: menu_dict(menu) for menu in menus}
    roots: list[dict] = []
    for menu in menus:
        node = nodes[menu.id]
        parent = nodes.get(menu.parent_id) if menu.parent_id is not None else None
        if parent is None:
            roots.append(node)
        else:
            parent["children"].append(node)
    return roots


def permission_codes_for(user, db: Session) -> set[str]:
    if user.is_superuser:
        rows = db.scalars(select(Menu.permission).where(Menu.permission != "")).all()
        return set(rows)
    codes: set[str] = set()
    for role in user.roles:
        if role.status != "active":
            continue
        for menu in role.menus:
            if menu.status == "active" and menu.permission:
                codes.add(menu.permission)
    return codes


def navigation_for(user, db: Session) -> dict:
    menus = all_menus(db)
    by_id = {menu.id: menu for menu in menus}
    if user.is_superuser:
        allowed_ids = {menu.id for menu in menus if menu.status == "active"}
        permissions = sorted(menu.permission for menu in menus if menu.permission and menu.status == "active")
    else:
        allowed_ids = set()
        permissions_set: set[str] = set()
        for role in user.roles:
            if role.status != "active":
                continue
            for menu in role.menus:
                if menu.status != "active":
                    continue
                allowed_ids.add(menu.id)
                if menu.permission:
                    permissions_set.add(menu.permission)
        for menu_id in list(allowed_ids):
            parent_id = by_id[menu_id].parent_id if menu_id in by_id else None
            while parent_id is not None and parent_id in by_id:
                allowed_ids.add(parent_id)
                parent_id = by_id[parent_id].parent_id
        permissions = sorted(permissions_set)

    visible = [
        menu
        for menu in menus
        if menu.id in allowed_ids and menu.status == "active" and menu.visible and menu.menu_type != "button"
    ]
    return {"menus": _prune_empty_directories(build_tree(visible)), "permissions": permissions}


def _prune_empty_directories(nodes: list[dict]) -> list[dict]:
    pruned: list[dict] = []
    for node in nodes:
        node["children"] = _prune_empty_directories(node["children"])
        if node["menu_type"] == "directory" and not node["children"]:
            continue
        pruned.append(node)
    return pruned


def list_roles(db: Session, page: int, page_size: int) -> tuple[list[Role], int]:
    total = db.scalar(select(func.count()).select_from(Role)) or 0
    stmt = select(Role).order_by(Role.id).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt).all()), total


def get_role(db: Session, role_id: int) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise AppError(404, "角色不存在")
    return role


def _menus_by_ids(db: Session, menu_ids: list[int]) -> list[Menu]:
    if not menu_ids:
        return []
    unique_ids = list(dict.fromkeys(menu_ids))
    menus = list(db.scalars(select(Menu).where(Menu.id.in_(unique_ids))).all())
    if len(menus) != len(unique_ids):
        raise AppError(400, "菜单不存在")
    return menus


def save_role(db: Session, payload: RoleWrite, role: Role | None = None, *, actor: User) -> Role:
    existing = db.scalar(select(Role).where(Role.code == payload.code))
    if existing is not None and (role is None or existing.id != role.id):
        raise AppError(409, "角色编码已存在")
    created = role is None
    if role is None:
        role = Role(name=payload.name, code=payload.code)
        db.add(role)
    elif role.code == "super_admin" and payload.code != role.code:
        raise AppError(400, "不能修改超级管理员角色编码")
    role.name = payload.name
    role.code = payload.code
    role.remark = payload.remark
    role.status = payload.status
    role.menus = _menus_by_ids(db, payload.menu_ids)
    write_log(db, actor, "新增角色" if created else "编辑角色", payload.name)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int, actor: User) -> None:
    role = get_role(db, role_id)
    if role.code == "super_admin":
        raise AppError(400, "不能删除超级管理员角色")
    name = role.name
    db.execute(delete(role_menus).where(role_menus.c.role_id == role.id))
    db.execute(delete(user_roles).where(user_roles.c.role_id == role.id))
    db.delete(role)
    write_log(db, actor, "删除角色", name)
    db.commit()


def _validate_menu(db: Session, payload: MenuWrite, menu_id: int | None = None) -> None:
    if payload.menu_type == "menu" and (not payload.path or not payload.component):
        raise AppError(400, "页面需要路径和组件")
    if payload.menu_type == "button" and not payload.permission:
        raise AppError(400, "按钮需要权限标识")
    if payload.menu_type == "button" and payload.parent_id is None:
        raise AppError(400, "按钮需要上级页面")
    if payload.parent_id is not None:
        parent = db.get(Menu, payload.parent_id)
        if parent is None:
            raise AppError(400, "上级菜单不存在")
        if payload.menu_type == "button" and parent.menu_type != "menu":
            raise AppError(400, "按钮只能挂在页面下")
        if payload.menu_type in {"menu", "directory"} and parent.menu_type != "directory":
            raise AppError(400, "只能挂在目录下")
    if payload.permission:
        existing = db.scalar(select(Menu).where(Menu.permission == payload.permission))
        if existing is not None and existing.id != menu_id:
            raise AppError(409, "权限标识已存在")


def save_menu(db: Session, payload: MenuWrite, menu: Menu | None = None, *, actor: User) -> Menu:
    _validate_menu(db, payload, None if menu is None else menu.id)
    created = menu is None
    if menu is None:
        menu = Menu(name=payload.name, menu_type=payload.menu_type)
        db.add(menu)
    menu.parent_id = payload.parent_id
    menu.name = payload.name
    menu.menu_type = payload.menu_type
    menu.path = payload.path
    menu.component = payload.component
    menu.permission = payload.permission
    menu.icon = payload.icon
    menu.sort = payload.sort
    menu.visible = payload.visible
    menu.status = payload.status
    write_log(db, actor, "新增菜单" if created else "编辑菜单", payload.name)
    db.commit()
    db.refresh(menu)
    return menu


def delete_menu(db: Session, menu_id: int, actor: User) -> None:
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise AppError(404, "菜单不存在")
    child_count = db.scalar(select(func.count()).select_from(Menu).where(Menu.parent_id == menu_id)) or 0
    if child_count:
        raise AppError(400, "请先删除子菜单")
    name = menu.name
    db.execute(delete(role_menus).where(role_menus.c.menu_id == menu.id))
    db.delete(menu)
    write_log(db, actor, "删除菜单", name)
    db.commit()
