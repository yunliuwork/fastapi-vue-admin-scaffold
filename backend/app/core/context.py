from contextvars import ContextVar

client_ip: ContextVar[str] = ContextVar("client_ip", default="")
request_params: ContextVar[str] = ContextVar("request_params", default="")
pending_log_ids: ContextVar[list[int] | None] = ContextVar("pending_log_ids", default=None)


def remember_log_id(log_id: int) -> None:
    pending = pending_log_ids.get()
    if pending is not None:
        pending.append(log_id)
