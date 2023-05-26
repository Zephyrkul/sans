from __future__ import annotations

from functools import wraps
from operator import methodcaller
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

import httpx

from .limiter import RateLimiter

__all__ = [
    "Client",
    "ClientType",
    "AsyncClient",
    "AsyncClientType",
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


def _ensure_auth(
    wrapped: Callable[_P, _R], *, force_auth: bool = False
) -> Callable[_P, _R]:
    setter = methodcaller(
        "__setitem__" if force_auth else "setdefault", "auth", _limiter
    )

    @wraps(wrapped)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        setter(kwargs)
        return wrapped(*args, **kwargs)

    return inner


class Client(httpx.Client):
    __doc__ = httpx.Client.__doc__
    __init__ = _ensure_auth(httpx.Client.__init__, force_auth=True)


class AsyncClient(httpx.AsyncClient):
    __doc__ = httpx.AsyncClient.__doc__
    __init__ = _ensure_auth(httpx.AsyncClient.__init__, force_auth=True)


# backwards compatibility
ClientType = Client
AsyncClientType = AsyncClient

request = _ensure_auth(httpx.request)
delete = _ensure_auth(httpx.delete)
get = _ensure_auth(httpx.get)
head = _ensure_auth(httpx.head)
options = _ensure_auth(httpx.options)
patch = _ensure_auth(httpx.patch)
post = _ensure_auth(httpx.post)
put = _ensure_auth(httpx.put)
stream = _ensure_auth(httpx.stream)
