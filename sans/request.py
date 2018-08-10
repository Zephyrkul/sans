import sys
import zlib
import aiohttp
from abc import ABC
from collections import deque
from enum import Enum, unique
from urllib.parse import urlparse, urlunparse
from inspect import isawaitable as awaitable
try:
    from lxml.etree import XMLPullParser
except ImportError:
    from xml.etree import XMLPullParser
from .api import API
from .ratelimit import ratelimited
from .sshard import SShard


__all__ = []


class Request:

    keysentinel = object()

    def __init__(self, url: str, *, session: aiohttp.ClientSession, method: str, agent: str):
        self._response, self._dobj, self._parser, self._charset, self._events = \
            (None for _ in range(5))
        self._url = url
        self._session = session if session else aiohttp
        self._method = method
        self._agent = agent

    def __iter__(self):
        return self

    __aiter__ = __iter__

    def __next__(self):
        raise NotImplementedError()

    async def __anext__(self) -> tuple:
        try:
            if self._events is None:
                return await self._aenter()
            else:
                return await self._anextiter()
        except StopAsyncIteration:
            if self._parser:
                self._parser.close()
            await self._response.release()
            raise
        except:
            if self._parser:
                self._parser.close()
            if self._response:
                self._response.close()
            raise

    @ratelimited
    async def _arequest(self) -> None:
        self._response = await self._session.request(self._method, self._url, headers={
            "User-Agent": API.agent})
        self._response.raise_for_status()

    async def _aenter(self) -> tuple:
        if not self._response:
            await self._arequest()
        self._setup()
        try:
            ret = ("headers", self._response.headers)
            if awaitable(ret):
                return await ret
            else:
                return ret
        except TypeError:
            return ("headers", self._response.headers)
        except KeyError:
            return await self._anextiter()

    async def _anextiter(self) -> tuple:
        if self._method != "GET":
            raise StopAsyncIteration()
        if not self._parser:
            self._method = None
            return ("bytes", await self._response.read())
        while True:
            try:
                event = self._nextevent()
            except StopIteration:
                break
        content = await self._response.content.readany()
        if not content:
            raise StopAsyncIteration()
        self._feed(content)
        return await self._anextiter()

    def _setup(self):
        contenttype = self._response.headers["Content-Type"].split("; ")
        self._dobj = zlib.decompressobj(16 + zlib.MAX_WBITS) if contenttype[0] == "application/x-gzip" else None
        if self._dobj or contenttype[0] == "text/xml":
            self._parser = XMLPullParser(["end"])
        elif contenttype[0] == "text/html":
            raise TypeError("This API wrapper does not support HTML calls. "
                            "Rather than attempt to scrape HTML, it is recommended that you request an "
                            "API endpoint (https://forum.nationstates.net/viewtopic.php?f=15&t=45424).")
        self._charset = contenttype[1][contenttype[1].index("=") + 1:] if len(contenttype) > 1 else "utf-8"
        self._events = False  # needs to be falsy, but not None

    def _nextevent(self):
        try:
            element = next(self._events)[1]
        except TypeError:
            raise StopIteration()
        tag = SShard.sshard(element)
        return (tag, element)

    def _feed(self, content):
        if self._dobj:
            content = self._dobj.decompress(content)
        self._parser.feed(content.decode(self._charset))
        self._events = self._parser.read_events()
