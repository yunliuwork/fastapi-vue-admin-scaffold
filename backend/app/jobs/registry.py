from collections.abc import Callable
from typing import Any

JobHandler = Callable[..., None]

_HANDLERS: dict[str, JobHandler] = {}
_LABELS: dict[str, str] = {}


def job(key: str, *, label: str):
    def decorator(func: JobHandler) -> JobHandler:
        _HANDLERS[key] = func
        _LABELS[key] = label
        return func

    return decorator


def get_handler(key: str) -> JobHandler | None:
    return _HANDLERS.get(key)


def handler_options() -> list[dict[str, str]]:
    return [{"key": key, "label": _LABELS.get(key, key)} for key in sorted(_HANDLERS)]


def call_handler(key: str, params: dict[str, Any]) -> None:
    handler = get_handler(key)
    if handler is None:
        raise ValueError(f"未知任务：{key}")
    handler(**params)
