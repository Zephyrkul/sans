import inspect
import re
from aiohttp import ClientResponseError
from typing import Optional


_docre = re.compile(r"(?i)([\d]+):\s+([\w\s]+)\s+status\s+code")


def _find(cls, test):
    for clz in filter(test, cls.__subclasses__()):
        if clz.__subclasses__():
            return _find(clz, test)
        return clz
    return cls


class HTTPException(ClientResponseError):
    """
    Base exception for failed HTTP requests.
    """

    code = None
    codes = ()

    def __new__(cls, e: Optional[ClientResponseError] = None):
        if not e:
            return super().__new__(cls, e)
        if not isinstance(e, ClientResponseError):
            raise TypeError(type(e))

        def test(clz):
            if clz.code:
                return e.status == clz.code
            return e.status in clz.codes

        return super().__new__(_find(cls, test), e)

    def __init__(self, e: Optional[ClientResponseError] = None):
        d = {
            k: None if v.default == inspect.Parameter.empty else v.default
            for k, v in inspect.signature(ClientResponseError).parameters.items()
        }
        if e:
            d.update(e.__dict__)
        else:
            match = _docre.search(self.__class__.__doc__)
            if not match:
                raise TypeError("This class cannot be directly instantiated.")
            d.update({"status": int(match[1]), "message": match[2]})
        super().__init__(**d)


class ClientError(HTTPException):
    """
    :exc:`HTTPException` for 4XX: Client Error status codes.
    """

    codes = range(400, 500)


class BadRequest(ClientError):
    """
    :exc:`ClientError` for 400: Bad Request status codes.
    """

    code = 400


class Forbidden(ClientError):
    """
    :exc:`ClientError` for 403: Forbidden status codes.
    """

    code = 403


class NotFound(ClientError):
    """
    :exc:`ClientError` for 404: Not Found status codes.
    """

    code = 404


class Conflict(ClientError):
    """
    :exc:`ClientError` for 409: Conflict status codes.
    """

    code = 409


class Teapot(ClientError):
    """
    :exc:`ClientError` for 418: I'm a Teapot status codes.
    """

    code = 418


class TooManyRequests(ClientError):
    """
    :exc:`ClientError` for 429: Too Many Requests status codes.
    """

    code = 429


class ServerError(HTTPException):
    """
    :exc:`HTTPException` for 5XX: Server Error status codes.
    """

    codes = range(500, 600)
