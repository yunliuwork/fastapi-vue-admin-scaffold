from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.menu import Menu
from app.models.role import Role
from app.core.time import now_ms
from app.models.user import User


SEED_MENUS = [
    {
        "name": "工作台",
        "menu_type": "menu",
        "path": "/dashboard",
        "component": "dashboard/index",
        "icon": "DashboardOutlined",
        "sort": 0,
        "permission": "",
    },
    {
        "name": "系统管理",
        "menu_type": "directory",
        "path": "/system",
        "icon": "SettingOutlined",
        "sort": 10,
        "permission": "",
        "children": [
            {
                "name": "用户管理",
                "menu_type": "menu",
                "path": "/system/users",
                "component": "system/user/index",
                "icon": "TeamOutlined",
                "sort": 0,
                "permission": "system:user:list",
                "children": [
                    {"name": "新增用户", "menu_type": "button", "permission": "system:user:create", "sort": 0},
                    {"name": "编辑用户", "menu_type": "button", "permission": "system:user:update", "sort": 1},
                    {"name": "停用用户", "menu_type": "button", "permission": "system:user:disable", "sort": 2},
                    {"name": "重置密码", "menu_type": "button", "permission": "system:user:reset-password", "sort": 3},
                ],
            },
            {
                "name": "角色管理",
                "menu_type": "menu",
                "path": "/system/roles",
                "component": "system/role/index",
                "icon": "SafetyCertificateOutlined",
                "sort": 1,
                "permission": "system:role:list",
                "children": [
                    {"name": "新增角色", "menu_type": "button", "permission": "system:role:create", "sort": 0},
                    {"name": "编辑角色", "menu_type": "button", "permission": "system:role:update", "sort": 1},
                    {"name": "删除角色", "menu_type": "button", "permission": "system:role:delete", "sort": 2},
                ],
            },
            {
                "name": "菜单管理",
                "menu_type": "menu",
                "path": "/system/menus",
                "component": "system/menu/index",
                "icon": "MenuOutlined",
                "sort": 2,
                "permission": "system:menu:list",
                "children": [
                    {"name": "新增菜单", "menu_type": "button", "permission": "system:menu:create", "sort": 0},
                    {"name": "编辑菜单", "menu_type": "button", "permission": "system:menu:update", "sort": 1},
                    {"name": "删除菜单", "menu_type": "button", "permission": "system:menu:delete", "sort": 2},
                ],
            },
            {
                "name": "操作日志",
                "menu_type": "menu",
                "path": "/system/logs",
                "component": "system/log/index",
                "icon": "FileSearchOutlined",
                "sort": 3,
                "permission": "system:log:list",
            },
            {
                "name": "定时任务",
                "menu_type": "menu",
                "path": "/system/tasks",
                "component": "system/task/index",
                "icon": "ClockCircleOutlined",
                "sort": 4,
                "permission": "system:job:list",
                "children": [
                    {"name": "新增任务", "menu_type": "button", "permission": "system:job:create", "sort": 0},
                    {"name": "编辑任务", "menu_type": "button", "permission": "system:job:update", "sort": 1},
                    {"name": "删除任务", "menu_type": "button", "permission": "system:job:delete", "sort": 2},
                    {"name": "执行任务", "menu_type": "button", "permission": "system:job:run", "sort": 3},
                ],
            },
        ],
    },
]


def _add_menu(db: Session, payload: dict, parent_id: int | None = None) -> Menu:
    menu = Menu(
        parent_id=parent_id,
        name=payload["name"],
        menu_type=payload["menu_type"],
        path=payload.get("path", ""),
        component=payload.get("component", ""),
        permission=payload.get("permission", ""),
        icon=payload.get("icon", ""),
        sort=payload.get("sort", 0),
        visible=True,
        status="active",
    )
    db.add(menu)
    db.flush()
    for child in payload.get("children", []):
        _add_menu(db, child, menu.id)
    return menu


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(User)) or 0
    if count:
        return
    for payload in SEED_MENUS:
        _add_menu(db, payload)
    menus = list(db.scalars(select(Menu)).all())
    now = now_ms()
    role = Role(name="超级管理员", code="super_admin", remark="拥有全部菜单", status="active", menus=menus)
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        nickname="超级管理员",
        status="active",
        is_superuser=True,
        created_at=now,
        updated_at=now,
        roles=[role],
    )
    db.add(admin)
    db.commit()


def ensure_operation_log_menu(db: Session) -> None:
    existing = db.scalar(select(Menu).where(Menu.permission == "system:log:list"))
    parent = db.scalar(select(Menu).where(Menu.path == "/system", Menu.menu_type == "directory"))
    if parent is None:
        return
    if existing is None:
        existing = Menu(
            parent_id=parent.id,
            name="操作日志",
            menu_type="menu",
            path="/system/logs",
            component="system/log/index",
            permission="system:log:list",
            icon="FileSearchOutlined",
            sort=3,
            visible=True,
            status="active",
        )
        db.add(existing)
        db.flush()
    role = db.scalar(select(Role).where(Role.code == "super_admin"))
    if role is not None and all(item.id != existing.id for item in role.menus):
        role.menus.append(existing)
    db.commit()


def ensure_scheduled_task_menu(db: Session) -> None:
    parent = db.scalar(select(Menu).where(Menu.path == "/system", Menu.menu_type == "directory"))
    if parent is None:
        return
    existing = db.scalar(select(Menu).where(Menu.permission == "system:job:list"))
    if existing is None:
        existing = Menu(
            parent_id=parent.id,
            name="定时任务",
            menu_type="menu",
            path="/system/tasks",
            component="system/task/index",
            permission="system:job:list",
            icon="ClockCircleOutlined",
            sort=4,
            visible=True,
            status="active",
        )
        db.add(existing)
        db.flush()
        buttons = [
            ("新增任务", "system:job:create", 0),
            ("编辑任务", "system:job:update", 1),
            ("删除任务", "system:job:delete", 2),
            ("执行任务", "system:job:run", 3),
        ]
        for name, permission, sort in buttons:
            db.add(
                Menu(
                    parent_id=existing.id,
                    name=name,
                    menu_type="button",
                    permission=permission,
                    sort=sort,
                    visible=True,
                    status="active",
                )
            )
    role = db.scalar(select(Role).where(Role.code == "super_admin"))
    if role is not None:
        menu_ids = {item.id for item in role.menus}
        to_add = [existing]
        if existing.id:
            for child in db.scalars(select(Menu).where(Menu.parent_id == existing.id)).all():
                if child.id not in menu_ids:
                    to_add.append(child)
        for menu in to_add:
            if menu.id not in menu_ids:
                role.menus.append(menu)
    db.commit()
