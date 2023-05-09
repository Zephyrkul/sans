from functools import partial
from typing import Any, ContextManager

from .limiter import RateLimiter
from .response import Response

from httpx import (  # isort: skip
    AsyncClient as AsyncClientType,
    Client as ClientType,
    request as _request,  # type: ignore
    stream as _stream,  # type: ignore
)


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


def Client(*, auth: Any = None, **kwargs: Any):
    if auth is None or not isinstance(auth, RateLimiter):
        auth = RateLimiter()
    return ClientType(auth=auth, **kwargs)


def AsyncClient(*, auth: Any = None, **kwargs: Any):
    if auth is None or not isinstance(auth, RateLimiter):
        auth = RateLimiter()
    return AsyncClientType(auth=auth, **kwargs)


def request(*args: Any, auth: Any = None, **kwargs: Any) -> Response:
    if auth is None or not isinstance(auth, RateLimiter):
        auth = RateLimiter()
    return _request(*args, auth=auth, **kwargs)  # type: ignore


delete = partial(request, "DELETE")
get = partial(request, "GET")
head = partial(request, "HEAD")
options = partial(request, "OPTIONS")
patch = partial(request, "PATCH")
post = partial(request, "POST")
put = partial(request, "PUT")


def stream(*args: Any, auth: Any = None, **kwargs: Any) -> ContextManager[Response]:
    if auth is None or not isinstance(auth, RateLimiter):
        auth = RateLimiter()
    return _stream(*args, auth=auth, **kwargs)  # type: ignore
