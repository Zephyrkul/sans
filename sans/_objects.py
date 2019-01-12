import aiohttp
import asyncio
import collections
import contextlib
from concurrent.futures import Future
from lxml import etree
from urllib.parse import urlparse

from .info import API_URL
from .utils import get_running_loop


class Threadsafe:
    __slots__ = ("api",)

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
        self.api = api

    def __await__(self):
        return asyncio.wrap_future(self._run_coro_ts(self._wrapper(self.api))).__await__()

    async def __aiter__(self):
        aiter = self.api.__aiter__()
        while True:
            yield (await asyncio.wrap_future(self._run_coro_ts(aiter.__anext__())))

    def __call__(self):
        return self._run_coro_ts(self._wrapper(self.api)).result()

    def __iter__(self):
        aiter = self.api.__aiter__()
        with contextlib.suppress(StopAsyncIteration):
            while True:
                yield self._run_coro_ts(aiter.__anext__()).result()


class NSElement(etree.ElementBase, collections.abc.MutableMapping):
    __slots__ = ()

    def __delitem__(self, key):
        element = self[key]
        element.getparent().remove(element)

    def __getitem__(self, key):
        with contextlib.suppress(TypeError):
            return super().__getitem__(key)
        e = self.find(key)
        if e is None:
            raise KeyError(key)
        if e.attrib or len(e):
            return e
        return e.text

    def __iter__(self):
        return (e.tag for e in self.iterchildren())

    # __len__ implemented by ElementBase

    def __setitem__(self, key, value):
        with contextlib.suppress(TypeError):
            return super().__setitem__(key, value)
        e = self.find(key)
        if e is None:
            raise KeyError(key)
        if isinstance(value, collections.abc.Mapping):
            e.attrib = value
        else:
            e.text = str(value)

    def to_pretty_string(self):
        return etree.tostring(self, encoding=str, pretty_print=True)


class NSResponse(aiohttp.ClientResponse):
    __slots__ = ()

    async def start(self, conn):
        from .api import Api

        if urlparse(str(self.real_url))[: len(API_URL)] != API_URL:
            # don't use the lock
            lock = _NullACM()
        else:
            # pylint: disable=E1701
            lock = Api.lock
        async with lock:
            for tries in range(5):
                response = await super().start(conn)
                with contextlib.suppress(KeyError):
                    lock.xrlrs(response.headers["X-ratelimit-requests-seen"])
                if response.status == 429:
                    lock.xra(response.headers["X-Retry-After"])
                    break
                elif response.status >= 500:
                    await asyncio.sleep(1 + tries * 2)  # keep the lock
                else:
                    break
            return response


class _NullACM:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: self
