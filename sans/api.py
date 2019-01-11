import aiohttp
import asyncio
import collections
import contextlib
import functools
import zlib
from collections.abc import Iterable, Mapping
from enum import Enum
from lxml import etree
from types import MappingProxyType
from typing import Any as _Any, Iterable as _Iterable, Mapping as _Mapping
from urllib.parse import parse_qs, unquote_plus, urlencode, urlparse, urlunparse

from .info import API_URL, AGENT_FMT
from .lock import ResetLock
from .objects import Threadsafe, NSElement, NSResponse
from .utils import get_running_loop


__all__ = ["Api", "Dumps"]


def _maybe_threadsafe(func):
    if not hasattr(Threadsafe, func.__name__):
        raise RuntimeError("This method cannot be made threadsafe")

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if get_running_loop() == Api.loop:
            return func(*args, **kwargs)
        return getattr(Threadsafe(args[0]), func.__name__)(*args[1:], **kwargs)

    return decorator


def _normalize_dicts(*dicts: _Mapping[str, _Iterable]):
    final = {}
    for d in dicts:
        for k, v in d.items():
            if not all((k, v)):
                continue
            if not isinstance(v, str):
                v = " ".join(map(str, v))
            v = unquote_plus(str(v).strip())
            if not v:
                continue
            if k in final:
                final[k] += " {}".format(v)
            else:
                final[k] = v
    # make read-only
    return MappingProxyType(final)


class ApiMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._agent = None
        cls._lock = None
        cls._loop = None
        cls._session = None

    @property
    def agent(cls):
        return cls._agent

    @agent.setter
    def agent(cls, value: str):
        if value:
            cls._agent = AGENT_FMT(value)

    @property
    def loop(cls):
        if not cls._loop:
            cls._loop = asyncio.get_event_loop()
        return cls._loop

    @loop.setter
    def loop(cls, loop: asyncio.AbstractEventLoop):
        if cls._loop and cls._loop != loop:
            raise asyncio.InvalidStateError("Cannot change loop when it's already set!")
        cls._loop = loop

    @property
    def lock(cls):
        if not cls._lock:
            cls._lock = ResetLock(loop=cls.loop)
        return cls._lock

    @property
    def session(cls):
        if not cls._session:
            cls._session = aiohttp.ClientSession(
                loop=cls.loop, raise_for_status=True, response_class=NSResponse
            )
        return cls._session


class Api(metaclass=ApiMeta):
    __slots__ = ("__proxy",)

    def __new__(cls, *shards: _Any, **kwargs: str):
        if len(shards) == 1 and not kwargs:
            if isinstance(shards[0], cls):
                return shards[0]
            with contextlib.suppress(Exception):
                return cls.from_url(shards[0])
        dicts = [kwargs] if kwargs else []
        for shard in filter(bool, shards):
            if isinstance(shard, Mapping):
                dicts.append(shard)
            else:
                dicts.append({"q": shard})
        self = super().__new__(cls)
        self.__proxy = _normalize_dicts(*dicts)
        return self

    async def __await(self):
        # pylint: disable=E1133
        async for element in self.__aiter__(no_clear=True):
            pass
        return element

    @_maybe_threadsafe
    def __await__(self):
        return self.__await().__await__()

    @_maybe_threadsafe
    async def __aiter__(self, *, no_clear: bool = False):
        if not self.agent:
            raise RuntimeError("The API's user agent is not yet set.")
        if not self:
            # Preempt the request to conserve ratelimit
            raise ValueError("Bad request")
        url = str(self)

        parser = etree.XMLPullParser(["end"], base_url=url, remove_blank_text=True)
        parser.set_element_class_lookup(etree.ElementDefaultClassLookup(element=NSElement))
        events = parser.read_events()

        async with self.session.request(
            "GET", url, headers={"User-Agent": self.agent}
        ) as response:
            yield parser.makeelement("HEADERS", attrib=response.headers)
            encoding = response.headers["Content-Type"].split("charset=")[1].split(",")[0]
            async for data, _ in response.content.iter_chunks():
                parser.feed(data.decode(encoding))
                for _, element in events:
                    if not no_clear and (
                        element.getparent() is None or element.getparent().getparent() is not None
                    ):
                        continue
                    yield element
                    if no_clear:
                        continue
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]

    def __add__(self, other: _Any) -> "Api":
        if isinstance(other, str):
            with contextlib.suppress(Exception):
                other = type(self).from_url(other)
        with contextlib.suppress(Exception):
            return type(self)(self, other)
        return NotImplemented

    def __bool__(self):
        if any(a in self for a in ("nation", "region")):
            return True
        if "a" in self:
            if self["a"] == "verify" and all(a in self for a in ("nation", "checksum")):
                return True
            if self["a"] == "sendtg" and all(a in self for a in ("client", "tgid", "key", "to")):
                return True
        return "q" in self

    def __contains__(self, key):
        return key in self.__proxy

    def __dir__(self):
        return set(super().__dir__()).union(
            dir(self.__proxy), (a for a in dir(type(self)) if not hasattr(type, a))
        )

    def __getattr__(self, name):
        with contextlib.suppress(AttributeError):
            return getattr(self.__proxy, name)
        if not hasattr(type, name):
            return getattr(type(self), name)
        raise AttributeError

    def __getitem__(self, key):
        return self.__proxy[str(key).lower()]

    def __iter__(self):
        return iter(self.__proxy)

    def __len__(self):
        return len(self.__proxy)

    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__, ", ".join("{}={!r}".format(*t) for t in self.__proxy.items())
        )

    def __str__(self) -> str:
        params = [(k, v if isinstance(v, str) else " ".join(v)) for k, v in self.items()]
        return urlunparse((*API_URL, None, urlencode(params, safe="+"), None))

    @property
    def threadsafe(self):
        return Threadsafe(self)

    @classmethod
    def from_url(cls, url: str, *args, **kwargs):
        parsed_url = urlparse(str(url))
        url = parsed_url[: len(API_URL)]
        if any(url) and url != API_URL:
            raise ValueError("URL must be solely query parameters or an API url")
        return cls(*args, parse_qs(parsed_url.query), kwargs)


class Dumps(Enum):
    NATIONS = urlunparse((*API_URL[:2], "/pages/nations.xml.gz", None, None, None))
    NATION = NATIONS
    REGIONS = urlunparse((*API_URL[:2], "/pages/regions.xml.gz", None, None, None))
    REGION = REGIONS

    @_maybe_threadsafe
    async def __aiter__(self):
        url = self.value
        # pylint: disable=E1101
        tag = self.name.lower().rstrip("s")

        parser = etree.XMLPullParser(["end"], base_url=url, remove_blank_text=True, tag=tag)
        parser.set_element_class_lookup(etree.ElementDefaultClassLookup(element=NSElement))
        events = parser.read_events()
        dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)

        async with Api.session.request("GET", url, headers={"User-Agent": Api.agent}) as response:
            yield parser.makeelement("HEADERS", attrib=response.headers)
            async for data, _ in response.content.iter_chunks():
                parser.feed(dobj.decompress(data))
                for _, element in events:
                    yield element
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]

    @property
    def threadsafe(self):
        return Threadsafe(self)
