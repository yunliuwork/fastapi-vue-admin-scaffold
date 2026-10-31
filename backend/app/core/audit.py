import json
from urllib.parse import parse_qsl

from sqlalchemy import select

from app.core.context import client_ip, pending_log_ids, request_params
from app.core.errors import AppError
from app.core.security import decode_token
from app.db import session as db_session
from app.models.user import User
from app.services.logs import dump_redacted, failure_action, finish_logs, write_failure

_SKIPPED = {"GET", "HEAD", "OPTIONS"}
_BODY_LIMIT = 16_000


class RequestAuditMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        body, replay = await _buffer(receive)
        parsed = _parse_body(body)
        params = _params(scope.get("query_string", b""), parsed, body)
        client = scope.get("client")
        ip_token = client_ip.set(client[0] if client else "")
        params_token = request_params.set(params)
        pending: list[int] = []
        pending_token = pending_log_ids.set(pending)
        status_code = 500
        chunks: list[bytes] = []

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                chunk = message.get("body") or b""
                if sum(len(item) for item in chunks) < _BODY_LIMIT:
                    chunks.append(chunk)
            await send(message)

        try:
            await self.app(scope, replay, send_wrapper)
        finally:
            try:
                _persist(scope, pending, status_code, b"".join(chunks), parsed)
            finally:
                client_ip.reset(ip_token)
                request_params.reset(params_token)
                pending_log_ids.reset(pending_token)


def _persist(scope, pending: list[int], status_code: int, raw: bytes, body: object) -> None:
    factory = db_session.session_factory
    if factory is None:
        return
    record_failure = not pending and _should_record_failure(scope, status_code)
    if not pending and not record_failure:
        return
    response = _response_text(raw)
    db = factory()
    try:
        if pending:
            finish_logs(db, list(pending), status_code, response)
            return
        if not record_failure:
            return
        user_id, username = _actor(scope, db, body)
        action, target = failure_action(scope.get("method", ""), scope.get("path", ""), body)
        if not username and isinstance(body, dict):
            username = str(body.get("username") or "")
        write_failure(db, user_id, username, action, target, status_code, response)
    finally:
        db.close()


def _should_record_failure(scope, status_code: int) -> bool:
    method = scope.get("method", "")
    path = scope.get("path", "")
    if method in _SKIPPED or status_code < 400:
        return False
    if path == "/api/v1/auth/refresh":
        return False
    return path.startswith("/api/")


def _actor(scope, db, body: object) -> tuple[int | None, str]:
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    raw = headers.get(b"authorization", b"").decode()
    if raw.lower().startswith("bearer "):
        token = raw.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token, scope["app"].state.settings.jwt_secret)
            user = db.get(User, int(payload["sub"]))
        except (AppError, KeyError, TypeError, ValueError):
            user = None
        if user is not None:
            return user.id, user.username
    if isinstance(body, dict):
        name = str(body.get("username") or "")
        if name:
            user = db.scalar(select(User).where(User.username == name))
            return (None if user is None else user.id), name
    return None, ""


async def _buffer(receive):
    buffered = []
    while True:
        message = await receive()
        buffered.append(message)
        if message["type"] != "http.request" or not message.get("more_body", False):
            break
    index = 0

    async def replay():
        nonlocal index
        if index < len(buffered):
            message = buffered[index]
            index += 1
            return message
        return await receive()

    body = b"".join(message.get("body", b"") for message in buffered if message["type"] == "http.request")
    return body[:_BODY_LIMIT], replay


def _parse_body(body: bytes) -> object:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _params(query: bytes, parsed: object, body: bytes) -> str:
    pairs = dict(parse_qsl(query.decode("utf-8", errors="replace")))
    if pairs and parsed is not None:
        return dump_redacted({"query": pairs, "body": parsed})
    if pairs:
        return dump_redacted(pairs)
    if parsed is not None:
        return dump_redacted(parsed)
    if body:
        return body.decode("utf-8", errors="replace")[:4000]
    return ""


def _response_text(raw: bytes) -> str:
    if not raw:
        return ""
    text = raw[:_BODY_LIMIT].decode("utf-8", errors="replace")
    try:
        return dump_redacted(json.loads(text))
    except json.JSONDecodeError:
        return text[:4000]
