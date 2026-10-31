from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import role_menus


class Menu(Base):
    __tablename__ = "sys_menus"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sys_menus.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    menu_type: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(128), default="")
    component: Mapped[str] = mapped_column(String(128), default="")
    permission: Mapped[str] = mapped_column(String(128), default="")
    icon: Mapped[str] = mapped_column(String(64), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(16), default="active")

    roles: Mapped[list["Role"]] = relationship(secondary=role_menus, back_populates="menus")
