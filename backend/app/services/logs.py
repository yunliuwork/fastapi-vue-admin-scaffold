import json
from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.context import client_ip, remember_log_id, request_params
from app.models.operation_log import OperationLog
from app.models.user import User, utcnow

_LIMIT = 4000


def write_log(db: Session, user: User | None, action: str, target: str) -> None:
    row = OperationLog(
        user_id=None if user is None else user.id,
        username="" if user is None else user.username,
        action=action,
        target=target[:255],
        ip=client_ip.get()[:64],
        params=request_params.get()[:_LIMIT],
        response_body="",
        status_code=None,
        created_at=utcnow(),
    )
    db.add(row)
    db.flush()
    remember_log_id(row.id)


def finish_logs(db: Session, log_ids: list[int], status_code: int, response: str) -> None:
    if not log_ids:
        return
    rows = list(db.scalars(select(OperationLog).where(OperationLog.id.in_(log_ids))).all())
    for row in rows:
        row.status_code = status_code
        row.response_body = response[:_LIMIT]
    db.commit()


def write_failure(
    db: Session,
    user_id: int | None,
    username: str,
    action: str,
    target: str,
    status_code: int,
    response: str,
) -> None:
    db.add(
        OperationLog(
            user_id=user_id,
            username=username[:64],
            action=action[:32],
            target=target[:255],
            ip=client_ip.get()[:64],
            params=request_params.get()[:_LIMIT],
            response_body=response[:_LIMIT],
            status_code=status_code,
            created_at=utcnow(),
        )
    )
    db.commit()


def failure_action(method: str, path: str, body: object) -> tuple[str, str]:
    name = ""
    status = ""
    if isinstance(body, dict):
        name = str(body.get("username") or body.get("name") or "")
        status = str(body.get("status") or "")
    if path == "/api/v1/auth/login":
        return "登录", name
    if path == "/api/v1/auth/logout":
        return "退出", name
    if path == "/api/v1/auth/password":
        return "修改密码", name
    if path == "/api/v1/users" and method == "POST":
        return "新增用户", name
    if path.startswith("/api/v1/users/") and path.endswith("/status"):
        return ("启用用户" if status == "active" else "停用用户"), ""
    if path.startswith("/api/v1/users/") and path.endswith("/reset-password"):
        return "重置密码", ""
    if path.startswith("/api/v1/users/") and method == "PUT":
        return "编辑用户", ""
    if path == "/api/v1/roles" and method == "POST":
        return "新增角色", name
    if path.startswith("/api/v1/roles/") and method == "PUT":
        return "编辑角色", name
    if path.startswith("/api/v1/roles/") and method == "DELETE":
        return "删除角色", ""
    if path == "/api/v1/menus" and method == "POST":
        return "新增菜单", name
    if path.startswith("/api/v1/menus/") and method == "PUT":
        return "编辑菜单", name
    if path.startswith("/api/v1/menus/") and method == "DELETE":
        return "删除菜单", ""
    return f"{method} {path}"[:32], ""


def list_logs(
    db: Session,
    username: str | None,
    action: str | None,
    outcome: str | None,
    page: int,
    page_size: int,
) -> tuple[list[OperationLog], int]:
    filters = []
    if username:
        filters.append(OperationLog.username.contains(username))
    if action:
        filters.append(OperationLog.action.contains(action))
    if outcome == "success":
        filters.append(OperationLog.status_code.is_not(None))
        filters.append(OperationLog.status_code < 400)
    elif outcome == "failure":
        filters.append(OperationLog.status_code >= 400)
    total = db.scalar(select(func.count()).select_from(OperationLog).where(*filters)) or 0
    stmt = (
        select(OperationLog)
        .where(*filters)
        .order_by(OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt).all()), total


def log_dict(row: OperationLog) -> dict:
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return {
        "id": row.id,
        "username": row.username,
        "action": row.action,
        "target": row.target,
        "ip": row.ip,
        "params": row.params,
        "response": row.response_body,
        "status_code": row.status_code,
        "created_at": created.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    }


def redact(value: object) -> object:
    if isinstance(value, dict):
        return {key: "***" if _secret(str(key)) else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def dump_redacted(value: object) -> str:
    try:
        text = json.dumps(redact(value), ensure_ascii=False)
    except TypeError:
        text = str(value)
    return text[:_LIMIT]


def _secret(key: str) -> bool:
    lowered = key.lower()
    return "password" in lowered or lowered in {"access_token", "refresh_token", "token", "authorization"}
