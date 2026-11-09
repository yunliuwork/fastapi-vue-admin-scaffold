from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.services.logs import write_log
from app.models.role import Role
from app.core.time import now_ms
from app.models.user import User


def user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "roles": [{"id": role.id, "name": role.name, "code": role.code} for role in user.roles],
        "created_at": user.created_at,
        "totp_required": user.totp_required,
        "totp_enabled": user.totp_enabled,
    }


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "用户不存在")
    return user


def load_roles(db: Session, role_ids: list[int]) -> list[Role]:
    if not role_ids:
        return []
    unique_ids = list(dict.fromkeys(role_ids))
    roles = list(db.scalars(select(Role).where(Role.id.in_(unique_ids))).all())
    if len(roles) != len(unique_ids):
        raise AppError(400, "角色不存在")
    return roles


def list_users(
    db: Session,
    username: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    filters = []
    if username:
        filters.append(User.username.contains(username))
    if status:
        filters.append(User.status == status)
    total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    stmt = select(User).where(*filters).order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt).all()), total


def _apply_totp_required(user: User, totp_required: bool) -> None:
    user.totp_required = totp_required
    if not totp_required:
        user.totp_secret = None
        user.totp_enabled = False


def create_user(
    db: Session,
    username: str,
    password: str,
    nickname: str,
    role_ids: list[int],
    totp_required: bool,
    actor: User,
) -> User:
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise AppError(409, "用户名已存在")
    now = now_ms()
    user = User(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname,
        status="active",
        is_superuser=False,
        totp_required=totp_required,
        created_at=now,
        updated_at=now,
        roles=load_roles(db, role_ids),
    )
    db.add(user)
    db.flush()
    write_log(db, actor, "新增用户", username)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: int,
    nickname: str,
    status: str,
    role_ids: list[int],
    totp_required: bool,
    actor: User,
) -> User:
    user = get_user(db, user_id)
    _guard_superuser(actor, user)
    if user.is_superuser and status == "disabled":
        raise AppError(400, "不能停用超级管理员")
    user.nickname = nickname
    user.status = status
    user.roles = load_roles(db, role_ids)
    _apply_totp_required(user, totp_required)
    user.updated_at = now_ms()
    write_log(db, actor, "编辑用户", user.username)
    db.commit()
    db.refresh(user)
    return user


def update_status(db: Session, user_id: int, status: str, actor: User) -> User:
    user = get_user(db, user_id)
    _guard_superuser(actor, user)
    if user.is_superuser and status == "disabled":
        raise AppError(400, "不能停用超级管理员")
    user.status = status
    user.updated_at = now_ms()
    write_log(db, actor, "启用用户" if status == "active" else "停用用户", user.username)
    db.commit()
    db.refresh(user)
    return user


def reset_password(db: Session, user_id: int, password: str, actor: User) -> None:
    user = get_user(db, user_id)
    _guard_superuser(actor, user)
    user.password_hash = hash_password(password)
    user.token_version += 1
    user.failed_login_count = 0
    user.locked_until = None
    user.totp_secret = None
    user.totp_enabled = False
    user.updated_at = now_ms()
    write_log(db, actor, "重置密码", user.username)
    db.commit()


def reset_totp_binding(db: Session, user_id: int, actor: User) -> User:
    user = get_user(db, user_id)
    _guard_superuser(actor, user)
    if not user.totp_required:
        raise AppError(400, "该用户未启用谷歌验证")
    user.totp_secret = None
    user.totp_enabled = False
    user.token_version += 1
    user.updated_at = now_ms()
    write_log(db, actor, "重置谷歌验证器", user.username)
    db.commit()
    db.refresh(user)
    return user


def _guard_superuser(actor: User, target: User) -> None:
    if target.is_superuser and not actor.is_superuser:
        raise AppError(403, "不能修改超级管理员")
