import aiohttp
import asyncio
import contextlib
from urllib.parse import urlparse

from .info import API_URL
from .utils import get_running_loop
from .errors import HTTPException


class Threadsafe:
    """
    Threadsafe wrapper for :class:`sans.api.Api` or :class:`sans.api.Dumps` objects.

    This may only be run in a seperate thread from the Api loop.
    This object may be awaited, called, or iterated over.
    Synchronous and asynchronous iteration is supported.

    ================ ============================================================================
    Operation        Description
    ================ ============================================================================
    await x          Make a request to the NS API and returns the root XML element.
    async for y in x Make a request to the NS API and return each shard element as it is parsed.
                     Useful for larger requests.
    x()              Make a request to the NS API and returns the root XML element.
    for y in x       Make a request to the NS API and return each shard element as it is parsed.
                     Useful for larger requests.
    ================ ============================================================================

    Examples
    --------

    Usage::

        sans.run_in_thread()

        darc = await Api(nation="darcania").threadsafe
        async for shard in Api(nation="testlandia").threadsafe:
           print(shard.to_pretty_string())

        tnp = Api(region="the_north_pacific").threadsafe()
        for shard in Api(region="testregionia").threadsafe:
            print(shard.to_pretty_string())
    """

    __slots__ = ("_api",)

    @staticmethod
    def _run_coro_ts(coro):
        from .api import Api

        if not Api._loop or not Api._loop.is_running():
            raise RuntimeError("The API's event loop is not running.")
        if Api._loop == get_running_loop():
            raise RuntimeError(
                "Threaded responses cannot be run in the same loop as the API's loop."
            )
        return asyncio.run_coroutine_threadsafe(coro, Api.loop)

    @staticmethod
    async def _wrapper(awaitable):
        return await awaitable

    def __init__(self, api):
        self._api = api

    def __await__(self):
        return asyncio.wrap_future(
            self._run_coro_ts(self._wrapper(self._api))
        ).__await__()

    async def __aiter__(self):
        aiter = self._api.__aiter__()
        with contextlib.suppress(StopAsyncIteration):
            while True:
                yield (await asyncio.wrap_future(self._run_coro_ts(aiter.__anext__())))

    def __call__(self):
        return self._run_coro_ts(self._wrapper(self._api)).result()

    def __iter__(self):
        aiter = self._api.__aiter__()
        with contextlib.suppress(StopAsyncIteration):
            while True:
                yield self._run_coro_ts(aiter.__anext__()).result()


class NSResponse(aiohttp.ClientResponse):
    __slots__ = ()

    async def start(self, conn):
        from .api import Api

        if urlparse(str(self.real_url))[: len(API_URL)] != API_URL:
            # don't use the lock
            lock = _NullACM()
        else:
            lock = Api._lock
        async with lock:
            for tries in range(5):
                response = await super().start(conn)
                with contextlib.suppress(KeyError):
                    lock._xrlrs(response.headers["X-ratelimit-requests-seen"])
                if response.status == 429:
                    lock._xra(response.headers["X-Retry-After"])
                    break
                elif response.status >= 500:
                    # keep the lock
                    await asyncio.sleep(1 + tries * 2)
                else:
                    break
            return response

    def raise_for_status(self, *args, **kwargs):
        try:
            return super().raise_for_status(*args, **kwargs)
        except aiohttp.ClientResponseError as cre:
            raise HTTPException(cre) from cre


class _NullACM:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return self
