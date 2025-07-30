# https://html.spec.whatwg.org/multipage/server-sent-events.html
from __future__ import annotations

import sys
import time
from email.message import Message
from functools import wraps
from io import StringIO
from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Generic,
    NamedTuple,
    TypeVar,
)
from weakref import proxy

import anyio
import httpx

if TYPE_CHECKING:
    from typing import TypedDict
    from typing_extensions import Never, Required, Unpack

    from httpx._types import (
        AuthTypes,
        CookieTypes,
        HeaderTypes,
        QueryParamTypes,
        TimeoutTypes,
        URLTypes,
    )

    class _RequestKwargs(TypedDict, total=False):
        url: Required[URLTypes]
        params: QueryParamTypes
        headers: HeaderTypes
        cookies: CookieTypes
        auth: AuthTypes
        follow_redirects: bool
        timeout: TimeoutTypes
        extensions: dict


_ClientT = TypeVar("_ClientT", httpx.Client, httpx.AsyncClient)

if sys.version_info < (3, 9):

    def _removeprefix(__string: str, __prefix: str) -> str:
        if __string.startswith(__prefix):
            return __string[len(__prefix) :]
        return __string
else:
    _removeprefix = str.removeprefix


def _pass_by_proxy(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        self = proxy(self)
        return func(self, *args, **kwargs)

    return inner


def _is_event_stream(response: httpx.Response):
    message = Message()
    content_type = response.headers.get("Content-Type")
    if content_type:
        message["Content-Type"] = content_type
    return message.get_content_type() == "text/event-stream"


class InvalidStateError(Exception):
    pass


class _InvalidState:
    def __bool__(self):
        return False


InvalidState: Any = _InvalidState()


class Event(NamedTuple):
    type: str
    data: str
    origin: httpx.URL
    last_event_id: str


class EventSource(Generic[_ClientT]):
    __slots__ = (
        "_client",
        "_request",
        "_origin",
        "_last_event_id",
        "_reconnect",
        "_inner",
        "__weakref__",
    )

    def __init__(self, client: _ClientT, **request: Unpack[_RequestKwargs]) -> None:
        self._client = client
        self._request = request
        timeout = request.pop("timeout", client.timeout)
        try:
            timeout = request["extensions"].pop("timeout")  # type: ignore (reportTypedDictNotRequiredAccess)
        except KeyError:
            pass
        timeout = httpx.Timeout(timeout)
        timeout.read = None
        request["timeout"] = timeout
        self._last_event_id = ""
        self._reconnect = 0
        self._inner = self.__inner()

    @property
    def last_event_id(self):
        return self._last_event_id

    @_pass_by_proxy
    def __inner(self) -> Generator[Event | None, str, Never]:
        event: Event | None = None
        last_event_id = ""
        event_type = ""

        with StringIO() as data_buffer:
            while True:
                line, event = (yield event), None
                if line is None:
                    event = InvalidState
                    continue
                field, colon, value = line.partition(":")
                del line
                value = _removeprefix(value, " ")

                if (field, colon) == ("", ""):
                    self._last_event_id = last_event_id
                    data = data_buffer.getvalue()
                    if not data:
                        event_type = ""
                        continue
                    event = Event(
                        type=event_type or "message",
                        data=data[:-1],
                        origin=self._origin,
                        last_event_id=last_event_id,
                    )
                    del data
                    data_buffer.seek(0)
                    data_buffer.truncate(0)
                    event_type = ""

                elif (field, colon) == ("", ":"):
                    continue

                elif field == "event":
                    event_type = value

                elif field == "data":
                    print(value, file=data_buffer)

                elif field == "id":
                    if value != "\x00":
                        last_event_id = value

                elif field == "retry":
                    try:
                        self._reconnect = int(value)
                    except ValueError:
                        pass

    def __iter__(self: EventSource[httpx.Client]):
        client = self._client
        request_args = self._request
        send_args = {
            "auth": request_args.pop("auth", httpx.USE_CLIENT_DEFAULT),
            "follow_redirects": request_args.pop(
                "follow_redirects", httpx.USE_CLIENT_DEFAULT
            ),
            "stream": True,
        }
        driver = self._inner
        try:
            if next(driver) is InvalidState:
                raise InvalidStateError(
                    f"{self.__class__.__name__} is already running!"
                )
        except StopIteration:
            raise InvalidStateError(
                f"{self.__class__.__name__} was already closed!"
            ) from None
        try:
            while True:
                request: httpx.Request = client.build_request("GET", **request_args)  # type: ignore (reportCallIssue)
                if self._last_event_id:
                    request.headers["Last-Event-ID"] = self._last_event_id

                time.sleep(self._reconnect)

                response = client.send(request, **send_args)
                try:
                    self._origin = response.url
                    if response.status_code == 204:
                        return
                    response.raise_for_status()
                    assert _is_event_stream(response)

                    yield from filter(None, map(driver.send, response.iter_lines()))

                except httpx.RemoteProtocolError:
                    continue
                finally:
                    response.close()
        finally:
            driver.close()

    async def __aiter__(self: EventSource[httpx.AsyncClient]):
        client = self._client
        request_args = self._request
        send_args = {
            "auth": request_args.pop("auth", httpx.USE_CLIENT_DEFAULT),
            "follow_redirects": request_args.pop(
                "follow_redirects", httpx.USE_CLIENT_DEFAULT
            ),
            "stream": True,
        }
        driver = self._inner
        try:
            if next(driver) is InvalidState:
                raise InvalidStateError(
                    f"{self.__class__.__name__} is already running!"
                )
        except StopIteration:
            raise InvalidStateError(
                f"{self.__class__.__name__} was already closed!"
            ) from None
        try:
            while True:
                request: httpx.Request = client.build_request("GET", **request_args)  # type: ignore (reportCallIssue)
                if self._last_event_id:
                    request.headers["Last-Event-ID"] = self._last_event_id

                await anyio.sleep(self._reconnect)

                response = await client.send(request, **send_args)
                try:
                    self._origin = response.url
                    if response.status_code == 204:
                        return
                    response.raise_for_status()
                    assert _is_event_stream(response)

                    async for line in response.aiter_lines():
                        event = driver.send(line)
                        if event:
                            yield event

                except StopIteration as exc:
                    raise RuntimeError(
                        f"{self.__class__.__name__} was already closed!"
                    ) from exc
                except httpx.RemoteProtocolError:
                    continue
                except Exception as exc:
                    driver.throw(exc)
                    return
                finally:
                    await response.aclose()
        finally:
            driver.close()

    def close(self):
        self._inner.close()
