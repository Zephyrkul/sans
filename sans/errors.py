from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ClassVar, Collection

# as ... to mark for re-export
from httpx import HTTPStatusError as HTTPStatusError

if TYPE_CHECKING:

    class _HTTPStatusError(HTTPStatusError):
        _codes: ClassVar[Collection[int]]

else:
    _HTTPStatusError = HTTPStatusError


__all__ = [
    "AgentNotSetError",
    "HTTPStatusError",  # re-export
    "ClientError",
    "BadRequest",
    "Forbidden",
    "NotFound",
    "Conflict",
    "Teapot",
    "TooManyRequests",
    "ServerError",
]


class AgentNotSetError(RuntimeError):
    pass


def narrow(original: HTTPStatusError) -> HTTPStatusError:
    code = original.response.status_code
    match = (sys.maxsize, HTTPStatusError)
    for exc in globals().values():
        if exc is HTTPStatusError:
            continue
        if not isinstance(exc, type) or not issubclass(exc, _HTTPStatusError):
            continue
        codes = exc._codes
        if code in codes:
            match = min(match, (len(codes), exc))
    _, best = match
    if best is type(original):
        return original
    # bypass __init__
    _new = best.__new__(best)
    _new.__dict__.update(original.__dict__)
    _new.args = original.args
    return _new.with_traceback(original.__traceback__)


class ClientError(_HTTPStatusError):
    """
    :exc:`httpx.HTTPStatusError` for 4XX: Client Error status codes.
    """

    _codes = range(400, 500)


class BadRequest(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 400: Bad Request status codes.
    """

    _codes = (400,)


class Forbidden(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 403: Forbidden status codes.
    """

    _codes = (403,)


class NotFound(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 404: Not Found status codes.
    """

    _codes = (404,)


class Conflict(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 409: Conflict status codes.
    """

    _codes = (409,)


class Teapot(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 418: I'm a Teapot status codes.
    """

    _codes = (418,)


class TooManyRequests(ClientError):
    """
    :exc:`httpx.HTTPStatusError` for 429: Too Many Requests status codes.
    """

    _codes = (429,)


class ServerError(_HTTPStatusError):
    """
    :exc:`httpx.HTTPStatusError` for 5XX: Server Error status codes.
    """

    _codes = range(500, 600)
