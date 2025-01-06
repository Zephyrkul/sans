from __future__ import annotations

import httpx

try:
    from orjson import loads
except ModuleNotFoundError:
    from json import loads

from contextlib import AsyncExitStack, ExitStack
from datetime import datetime, timezone
from typing import AsyncIterator, Generic, Iterator, TypedDict, TypeVar
from urllib.parse import quote

from .client import AsyncClient, Client
from .url import API_URL

__all__ = ["serversent_events"]
_ClientT = TypeVar("_ClientT", Client, AsyncClient, None)


class _SSEvent(TypedDict):
    str: str
    id: int
    time: datetime


def _decode_event(line: str) -> _SSEvent:
    assert line.startswith("data: ")
    data = loads(line[6:])
    data["id"] = int(data["id"])
    data["time"] = datetime.fromtimestamp(data["time"], tz=timezone.utc)
    return data


class _SSIter(Generic[_ClientT]):
    __slots__ = ("_client", "_url")

    def __init__(self, client: _ClientT, url: httpx.URL):
        self._client = client
        self._url = url

    def __iter__(self: _SSIter[Client] | _SSIter[None]) -> Iterator[_SSEvent]:
        client, url = self._client, self._url
        with ExitStack() as stack:
            if client is None:
                client = stack.enter_context(Client())
            response = stack.enter_context(client.stream("GET", url, timeout=None))
            response.raise_for_status()
            yield from map(
                _decode_event,
                filter(lambda line: line.startswith("data: "), response.iter_lines()),
            )

    async def __aiter__(
        self: _SSIter[AsyncClient] | _SSIter[None],
    ) -> AsyncIterator[_SSEvent]:
        client, url = self._client, self._url
        async with AsyncExitStack() as stack:
            if client is None:
                client = await stack.enter_async_context(AsyncClient())
            response = await stack.enter_async_context(
                client.stream("GET", url, timeout=None)
            )
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield _decode_event(line)

    def __repr__(self):
        return f"<{self.__class__.__name__} client={self._client!r} url={self._url!r}"


def serversent_events(client: _ClientT, *filters: str) -> _SSIter[_ClientT]:
    if not filters:
        raise TypeError("At least one filter is required.")
    # use raw_path or httpx will do its own standards-compliant encoding
    url = API_URL.copy_with(
        raw_path=b"/api/"
        + quote("+".join(filters), safe="+: ").encode("ascii").replace(b" ", b"_")
    )
    return _SSIter(client, url)
