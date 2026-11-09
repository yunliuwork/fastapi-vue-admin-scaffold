from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_settings
from app.core.config import Settings
from app.core.errors import AppError
from app.core.response import ok
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.core.totp import new_secret, provisioning_uri, verify_code
from app.db.session import get_db
from app.core.time import MS_PER_MINUTE, now_ms
from app.models.user import User
from app.schemas.bodies import (
    LoginRequest,
    LoginTotpConfirm,
    PasswordChange,
    RefreshRequest,
    TotpDisableRequest,
)
from app.services.access import navigation_for
from app.services.logs import write_log
from app.services.users import user_dict

router = APIRouter(prefix="/auth", tags=["auth"])

LOGIN_FAILURE_LIMIT = 5
LOGIN_LOCK_MINUTES = 15
PRE_AUTH_MINUTES = 10


def _session_tokens(user: User, settings: Settings) -> dict:
    access = create_token(
        user.id,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        settings.jwt_secret,
        user.token_version,
    )
    refresh = create_token(
        user.id,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        settings.jwt_secret,
        user.token_version,
    )
    return {
        "login_step": "complete",
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


def _pre_auth_token(user: User, settings: Settings) -> str:
    return create_token(
        user.id,
        "pre_auth",
        timedelta(minutes=PRE_AUTH_MINUTES),
        settings.jwt_secret,
        user.token_version,
    )


def _user_from_pre_auth(db: Session, token: str, settings: Settings) -> User:
    payload = decode_token(token, settings.jwt_secret)
    if payload.get("type") != "pre_auth":
        raise AppError(401, "登录步骤已过期，请重新输入账号密码")
    user = db.get(User, int(payload["sub"]))
    if user is None or user.status != "active" or int(payload.get("ver", -1)) != user.token_version:
        raise AppError(401, "登录步骤已过期，请重新输入账号密码")
    if not user.totp_required:
        raise AppError(400, "该账号未启用谷歌验证")
    return user


def _locked(user: User) -> bool:
    return user.locked_until is not None and user.locked_until > now_ms()


def _register_login_failure(db: Session, user: User | None) -> None:
    if user is None:
        return
    if user.locked_until is not None and not _locked(user):
        user.failed_login_count = 0
        user.locked_until = None
    user.failed_login_count += 1
    if user.failed_login_count >= LOGIN_FAILURE_LIMIT:
        user.locked_until = now_ms() + LOGIN_LOCK_MINUTES * MS_PER_MINUTE
    db.commit()


def _clear_login_failures(user: User) -> None:
    user.failed_login_count = 0
    user.locked_until = None


def _authenticate_password(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is not None and _locked(user):
        raise AppError(429, "尝试次数过多，请稍后再试")
    if user is None or not verify_password(password, user.password_hash):
        _register_login_failure(db, user)
        raise AppError(401, "用户名或密码错误")
    if user.status != "active":
        raise AppError(403, "账号已停用")
    return user


def _finish_login(db: Session, user: User, settings: Settings) -> dict:
    _clear_login_failures(user)
    write_log(db, user, "登录", user.username)
    db.commit()
    return _session_tokens(user, settings)


def _prepare_bind_material(user: User, settings: Settings) -> dict:
    secret = new_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    user.updated_at = now_ms()
    return {
        "secret": secret,
        "otpauth_url": provisioning_uri(secret, username=user.username, issuer=settings.app_name),
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    user = _authenticate_password(db, body.username, body.password)
    if not user.totp_required:
        return ok(_finish_login(db, user, settings))
    if user.totp_enabled and user.totp_secret:
        return ok(
            {
                "login_step": "totp_verify",
                "pre_auth_token": _pre_auth_token(user, settings),
            }
        )
    bind = _prepare_bind_material(user, settings)
    db.commit()
    return ok(
        {
            "login_step": "totp_bind",
            "pre_auth_token": _pre_auth_token(user, settings),
            **bind,
        }
    )


@router.post("/login/totp-verify")
def login_totp_verify(
    body: LoginTotpConfirm,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = _user_from_pre_auth(db, body.pre_auth_token, settings)
    if not user.totp_enabled or not user.totp_secret:
        raise AppError(400, "请先完成谷歌验证器绑定")
    if not verify_code(user.totp_secret, body.totp_code):
        _register_login_failure(db, user)
        raise AppError(401, "谷歌验证码不正确")
    return ok(_finish_login(db, user, settings))


@router.post("/login/totp-bind")
def login_totp_bind(
    body: LoginTotpConfirm,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = _user_from_pre_auth(db, body.pre_auth_token, settings)
    if user.totp_enabled:
        raise AppError(400, "已绑定谷歌验证器，请直接输入验证码")
    if not user.totp_secret:
        raise AppError(400, "绑定信息已失效，请重新输入账号密码")
    if not verify_code(user.totp_secret, body.totp_code):
        raise AppError(401, "验证码不正确，请核对 Google Authenticator 中的 6 位数字")
    user.totp_enabled = True
    user.updated_at = now_ms()
    write_log(db, user, "绑定谷歌验证器", user.username)
    return ok(_finish_login(db, user, settings))


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    payload = decode_token(body.refresh_token, settings.jwt_secret)
    if payload.get("type") != "refresh":
        raise AppError(401, "未登录或登录已过期")
    user = db.get(User, int(payload["sub"]))
    if user is None or user.status != "active" or int(payload.get("ver", -1)) != user.token_version:
        raise AppError(401, "未登录或登录已过期")
    tokens = _session_tokens(user, settings)
    tokens.pop("login_step", None)
    return ok(tokens)


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    write_log(db, user, "退出", user.username)
    user.token_version += 1
    user.updated_at = now_ms()
    db.commit()
    return ok(None)


@router.put("/password")
def change_password(
    body: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not verify_password(body.old_password, user.password_hash):
        raise AppError(400, "原密码不正确")
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    _clear_login_failures(user)
    user.updated_at = now_ms()
    write_log(db, user, "修改密码", user.username)
    db.commit()
    tokens = _session_tokens(user, settings)
    tokens.pop("login_step", None)
    return ok(tokens)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(user_dict(user))


@router.get("/menus")
def menus(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(navigation_for(user, db))


@router.post("/totp/disable")
def totp_disable(
    body: TotpDisableRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.totp_required:
        raise AppError(400, "管理员已要求使用谷歌验证，请在用户管理中关闭后再解绑")
    if not user.totp_enabled or not user.totp_secret:
        raise AppError(400, "尚未绑定谷歌验证器")
    if not verify_password(body.password, user.password_hash):
        raise AppError(400, "登录密码不正确")
    if not verify_code(user.totp_secret, body.totp_code):
        raise AppError(400, "谷歌验证码不正确")
    user.totp_secret = None
    user.totp_enabled = False
    user.updated_at = now_ms()
    write_log(db, user, "解绑谷歌验证器", user.username)
    db.commit()
    return ok(None)
