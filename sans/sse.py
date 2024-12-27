from __future__ import annotations

try:
    from orjson import loads
except ModuleNotFoundError:
    from json import loads

from contextlib import ExitStack
from datetime import datetime, timezone
from typing import AsyncIterator, Iterable, Iterator, TypedDict, overload

from .client import AsyncClient, Client
from .url import API_URL

__all__ = ["serversent_events"]


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


@overload
def serversent_events(client: Client | None, *filters: str) -> Iterator[_SSEvent]: ...
@overload
def serversent_events(
    client: AsyncClient, *filters: str
) -> AsyncIterator[_SSEvent]: ...


def serversent_events(
    client: Client | AsyncClient | None,
    *filters: str,
) -> Iterator[_SSEvent] | AsyncIterator[_SSEvent]:
    if isinstance(client, AsyncClient):
        return _sse_async(client, filters)
    return _sse_sync(client, filters)


def _sse_sync(client: Client | None, filters: Iterable[str]) -> Iterator[_SSEvent]:
    with ExitStack() as stack:
        if client is None:
            client = stack.enter_context(Client())
        response = stack.enter_context(
            client.stream(
                "GET", API_URL.copy_with(path="/api/" + " ".join(filters)), timeout=None
            )
        )
        yield from map(
            _decode_event,
            filter(lambda line: line.startswith("data: "), response.iter_lines()),
        )


async def _sse_async(
    client: AsyncClient, filters: Iterable[str]
) -> AsyncIterator[_SSEvent]:
    async with client.stream(
        "GET", API_URL.copy_with(path="/api/" + " ".join(filters)), timeout=None
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                yield _decode_event(line)
