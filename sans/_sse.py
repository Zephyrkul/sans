from __future__ import annotations

from datetime import datetime, timezone
from itertools import chain
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Generic,
    Iterable,
    Iterator,
    TypedDict,
    TypeVar,
)
from urllib.parse import quote

import httpx

from ._client import AsyncClient, Client
from ._eventsource import Event, EventSource
from ._url import API_URL

if TYPE_CHECKING:
    from json import loads
else:
    try:
        from orjson import loads
    except ModuleNotFoundError:
        from json import loads

__all__ = ["serversent_events"]
_T = TypeVar("_T")
_ClientT = TypeVar("_ClientT", Client, AsyncClient)
_OptionalClientT = TypeVar("_OptionalClientT", Client, AsyncClient, None)


# backport of 3.10's contextlib.nullcontext
class _nullcontext(Generic[_T]):
    __slots__ = ("enter_result",)

    def __init__(self, enter_result: _T):
        self.enter_result = enter_result

    def __enter__(self) -> _T:
        return self.enter_result

    def __exit__(self, *_):
        pass

    async def __aenter__(self) -> _T:
        return self.enter_result

    async def __aexit__(self, *_):
        pass


class _SSEvent(TypedDict):
    str: str
    htmlStr: str
    id: int
    time: datetime


def _decode_event_data(event: Event) -> _SSEvent:
    data = loads(event.data)
    data["id"] = int(data["id"])
    data["time"] = datetime.fromtimestamp(data["time"], tz=timezone.utc)
    return data


def _wrap_client(client: _ClientT | None) -> _nullcontext[_ClientT] | None:
    if client is None:
        return None
    return _nullcontext(client)


def _quote_parameters(
    buckets: Iterable[str], nations: Iterable[str], regions: Iterable[str]
) -> str:
    return quote(
        "+".join(
            chain(
                buckets,
                nations
                and map(
                    "nation:%s".__mod__,
                    (nations,) if isinstance(nations, str) else nations,
                ),
                regions
                and map(
                    "region:%s".__mod__,
                    (regions,) if isinstance(regions, str) else regions,
                ),
            )
        ),
        safe="+: ",
    ).replace(" ", "_")


class _SSViewIter(Generic[_OptionalClientT]):
    __slots__ = ("_client", "_url")

    def __init__(self, client: _OptionalClientT, url: httpx.URL):
        self._client = client
        self._url = url

    def __iter__(self: _SSViewIter[Client] | _SSViewIter[None]) -> Iterator[_SSEvent]:
        url = self._url
        with _wrap_client(self._client) or Client() as client:
            del self
            yield from map(_decode_event_data, EventSource(client, url=url))

    async def __aiter__(
        self: _SSViewIter[AsyncClient] | _SSViewIter[None],
    ) -> AsyncIterator[_SSEvent]:
        url = self._url
        async with _wrap_client(self._client) or AsyncClient() as client:
            del self
            async for event in EventSource(client, url=url):
                yield _decode_event_data(event)

    def __repr__(self):
        return f"<{self.__class__.__name__} client={self._client!r} url={self._url!r}"


class _SSIter(_SSViewIter[_OptionalClientT]):
    __slots__ = ()

    def view(
        self, *views: str, nations: Iterable[str] = (), regions: Iterable[str] = ()
    ) -> _SSViewIter[_OptionalClientT]:
        """
        Subscribe only to events that also match at least one of the provided buckets.

        Parameters
        ----------
        views: *str
            The different buckets to filter with.
        nations: Iterable[str]
            The different nation-based buckets to also filter with.
        regions: Iterable[str]
            The different region-based buckets to also filter with.

        Returns
        -------
        An optionally asynchronous iterable which, when iterated,
        yields events as they occur in the form of a dict.
        """
        quoted = _quote_parameters(views, nations, regions)
        if not quoted:
            raise TypeError("At least one view is required.")
        url = API_URL.copy_with(
            raw_path=b"/".join((self._url.raw_path, quoted.encode("ascii")))
        )
        return _SSViewIter(self._client, url)


def serversent_events(
    client: _OptionalClientT,
    *buckets: str,
    nations: Iterable[str] = (),
    regions: Iterable[str] = (),
) -> _SSIter[_OptionalClientT]:
    """
    Subscribe to and iterate over server-sent events.

    Parameters
    ----------
    client: Client | AsyncClient | None
        The client to use. If not supplied,
        one will be opened for the lifetime of the iterator.
    buckets: *str
        The different buckets to subscribe to.
    nations: Iterable[str]
        The different nation-based buckets to also subscribe to.
    regions: Iterable[str]
        The different region-based buckets to also subscribe to.

    Returns
    -------
    An optionally asynchronous iterable which, when iterated,
    yields events as they occur in the form of a dict.
    """
    quoted = _quote_parameters(buckets, nations, regions)
    if not quoted:
        raise ValueError("At least one bucket is required.")
    # use raw_path or httpx will do its own standards-compliant encoding
    url = API_URL.copy_with(raw_path=b"/api/" + quoted.encode("ascii"))
    return _SSIter(client, url)
