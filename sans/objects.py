import aiohttp
import asyncio
import collections
import contextlib
from collections.abc import MutableMapping, MutableSequence
from lxml import etree
from typing import Any, Union
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


class NSElement(etree.ElementBase, MutableMapping, MutableSequence):
    """
    LXML Element class that supports MutableMapping and MutableSequence methods.

    Because backwards compatibility with my old pynationstates code is too hard otherwise.

    Item access gets the nth subelement if an `int` is passed, or an element with the specified
    tag if a `str` is passed. XPATH is also supported.
    The subelement will be converted to common data types if they can be:

    ========================================================================== ==================
    Element                                                                    Return Type
    ========================================================================== ==================
    Element does not exist.                                                    `IndexError` or
                                                                               `KeyError`
    <ELEMENT />                                                                `NoneType`
    <ELEMENT attrs="attr" />                                                   `dict`
    <ELEMENT>#</ELEMENT> (# is a number)                                       `int` or `float`
    <ELEMENT>data</ELEMENT>                                                    `str`
    <ELEMENT><ANY_SUBELEMENT /></ELEMENT>                                      :class:`NSElement`
    <ELEMENT attrs="attr">data</ELEMENT>                                       :class:`NSElement`
    ========================================================================== ==================

    :meth:`get_element` may be used to get subelements without autoconverting to common data types.
    """

    __slots__ = ()

    def __delitem__(self, key):
        element = self.get_element(key)
        element.getparent().remove(element)

    def __getitem__(self, key):
        e = self.get_element(key)
        if len(e):
            return e
        if e.attrib and e.text:
            return e
        if e.attrib:
            return e.attrib
        if not e.text:
            return None
        for t in (int, float):
            with contextlib.suppress(ValueError):
                return t(e.text)
        return e.text

    def __iter__(self):
        for e in self.iterchildren():
            yield e.tag

    # __len__ implemented by ElementBase

    def __setitem__(self, key, value):
        with contextlib.suppress(TypeError):
            return super().__setitem__(key, value)
        e = self.get_element(key)
        if isinstance(value, collections.abc.Mapping):
            e.attrib = value
        else:
            e.text = str(value)

    def __str__(self):
        return etree.tostring(self, encoding=str)

    def __contains__(self, element):
        return any(
            super(clz, self).__contains__(element) for clz in type(self).__bases__
        )

    # insert implemented by ElementBase

    def get_element(self, key: Union[int, str]) -> "NSElement":
        """
        Gets a subelement as :meth:`__getitem__`, but without autoconverting it into other data types.
        """
        try:
            e = super().__getitem__(key)
        except TypeError:
            try:
                e = self.find(key)
            except SyntaxError as se:
                raise KeyError(key) from se
        if e is None:
            raise KeyError(key)
        return e

    def pop(self, key: Union[int, str] = -1, default: Any = NotImplemented) -> Any:
        """
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError or IndexError is raised.
        """
        try:
            val = self[key]
        except (KeyError, IndexError):
            if default is NotImplemented:
                raise
            return default
        else:
            del self[key]
            return val

    def to_pretty_string(self) -> str:
        """
        Returns the base XML as a formatted and indented string.
        """
        return etree.tostring(self, encoding=str, pretty_print=True)


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
