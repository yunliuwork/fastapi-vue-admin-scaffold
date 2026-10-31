from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.access import permission_codes_for

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError(401, "未登录或登录已过期")
    payload = decode_token(credentials.credentials, settings.jwt_secret)
    if payload.get("type") != "access":
        raise AppError(401, "未登录或登录已过期")
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id is not None else None
    if user is None or user.status != "active":
        raise AppError(401, "未登录或登录已过期")
    if int(payload.get("ver", -1)) != user.token_version:
        raise AppError(401, "未登录或登录已过期")
    return user


def require_permission(code: str):
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.is_superuser or code in permission_codes_for(user, db):
            return user
        raise AppError(403, "没有权限")

    return checker
