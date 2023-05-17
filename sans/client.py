from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

import httpx
from httpx import AsyncClient as AsyncClientType, Client as ClientType

from .limiter import RateLimiter

__all__ = [
    "Client",
    "AsyncClient",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]
_limiter = RateLimiter()


def _ensure_auth(wrapped: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(wrapped)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        if "auth" not in kwargs:
            kwargs["auth"] = _limiter
        return wrapped(*args, **kwargs)

    return inner


Client = _ensure_auth(ClientType)
AsyncClient = _ensure_auth(AsyncClientType)

request = _ensure_auth(httpx.request)
delete = _ensure_auth(httpx.delete)
get = _ensure_auth(httpx.get)
head = _ensure_auth(httpx.head)
options = _ensure_auth(httpx.options)
patch = _ensure_auth(httpx.patch)
post = _ensure_auth(httpx.post)
put = _ensure_auth(httpx.put)
stream = _ensure_auth(httpx.stream)
