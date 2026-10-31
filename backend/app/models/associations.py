from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base

user_roles = Table(
    "sys_user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
)

role_menus = Table(
    "sys_role_menus",
    Base.metadata,
    Column("role_id", ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_id", ForeignKey("sys_menus.id", ondelete="CASCADE"), primary_key=True),
)
