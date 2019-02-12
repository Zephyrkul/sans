import aiohttp
import asyncio
import collections
import contextlib
import functools
import sys
import zlib
from collections.abc import Iterable, Mapping
from enum import Enum
from lxml import etree
from types import MappingProxyType
from typing import (
    Any as _Any,
    AsyncGenerator as _AsyncGenerator,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
)
from urllib.parse import parse_qs, quote_plus, unquote_plus, urlencode, urlparse, urlunparse

from .errors import HTTPException, BadRequest
from .info import API_URL, __version__
from .objects import Threadsafe, NSElement, NSResponse
from .utils import get_running_loop
from ._lock import ResetLock


__all__ = ["Api", "Dumps"]
AGENT_FMT = f"{{}} Python/{sys.version_info[0]}.{sys.version_info[1]} aiohttp/{aiohttp.__version__} sans/{__version__}".format
API_VERSION = "9"


# Set of keys that should be added to rather than overwritten
class _Adds:
    @staticmethod
    def q(x: str, y: str):
        return " ".join((x, y))

    scale, mode, filter, tags = q, q, q, q

    @staticmethod
    def view(x, y):
        xs, ys = x.split("."), y.split(".")
        if len(xs) != 1:
            raise ValueError()
        if len(ys) != 1:
            raise ValueError()
        if xs[0] != ys[0] or len(xs) != 1 or len(ys) != 1:
            # overwrite
            return y
        return "{}.{},{}".format(xs[0], xs[1], ys[1])


def _normalize_dicts(*dicts: _Mapping[str, _Iterable[str]]):
    final = {}
    for d in dicts:
        for k, v in d.items():
            if not all((k, v)):
                continue
            if not isinstance(v, str) and isinstance(v, Iterable):
                v = " ".join(map(str, v))
            v = unquote_plus(str(v)).strip().strip("_")
            if not v:
                continue
            if k in final:
                with contextlib.suppress(AttributeError, TypeError):
                    final[k] = getattr(_Adds, k)(final[k], v)
                    continue
            final[k] = v
    final.setdefault("v", API_VERSION)
    return final


class ApiMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._agent = None
        cls._lock = None
        cls._loop = None
        cls._session = None

    @property
    def agent(cls) -> _Optional[str]:
        """The API wrapper's set user agent."""
        return cls._agent

    @agent.setter
    def agent(cls, value: str) -> None:
        if value:
            cls._agent = AGENT_FMT(value)

    @property
    def loop(cls) -> asyncio.AbstractEventLoop:
        """The API wrapper's event loop.

        Cannot be changed once it has been set or referenced."""
        if not cls._loop:
            cls._loop = asyncio.get_event_loop()
        return cls._loop

    @loop.setter
    def loop(cls, loop: asyncio.AbstractEventLoop) -> None:
        if cls._loop and cls._loop != loop:
            raise asyncio.InvalidStateError("Cannot change loop when it's already set!")
        cls._loop = loop

    @property
    def lock(cls) -> ResetLock:
        """The API wrapper's rate-limiting lock."""
        if not cls._lock:
            cls._lock = ResetLock(loop=cls.loop)
        return cls._lock

    @property
    def session(cls) -> aiohttp.ClientSession:
        """The API wrapper's HTTP client session."""
        if not cls._session or cls._session.closed:
            cls._session = aiohttp.ClientSession(
                loop=cls.loop, raise_for_status=True, response_class=NSResponse
            )
        return cls._session


class Api(metaclass=ApiMeta):
    r"""
    Construct and send an NS API request.
    NS API docs can be found here: https://www.nationstates.net/pages/api.html

    This is a low-level API wrapper. Some attempts will be made to prevent bad requests,
    but it will not check shards against a verified list.

    Api objects may be awaited or asynchronously iterated.
    To perform operations from another thread, use the :attr:`threadsafe` property.
    The Api object itself supports all :class:`collections.abc.Mapping` methods.

    ================ ============================================================================
    Operation        Description
    ================ ============================================================================
    await x          Make a request to the NS API and returns the root XML element.
    async for y in x Make a request to the NS API and return each shard element as it is parsed.
                     Useful for larger requests.
    x + y            Combines two :class:`Api` objects together into a new one.
                     Shard keywords that can't be combined will be overwritten with y's data.
    bool(x)          Naïvely check if this :class:`Api` object would result in a 400 Bad Request.
                     Truthy :class:`Api` objects may still result in a 400 Bad Request.
                     Use `len(x)` to check for containment.
    str(x)           Return the URL this :class:`Api` object will make a request to.
    Other            All other :class:`collections.abc.Mapping` methods, except x == y,
                     are also supported.
    ================ ============================================================================

    Parameters
    ----------
    \*shards: str
        Shards to request from the API.
    \*\*parameters: str
        Query parameters to append to the request, e.g. nation, scale.

    Examples
    --------

    Usage::

        darc = await Api(nation="darcania")
        async for shard in Api(nation="testlandia"):
           print(shard.to_pretty_string())

        tnp = Api(region="the_north_pacific").threadsafe()
        for shard in Api(region="testregionia").threadsafe:
            print(shard.to_pretty_string())
    """

    __slots__ = ("__proxy",)

    def __new__(cls, *shards: _Iterable[str], **parameters: _Iterable[str]):
        if len(shards) == 1 and not parameters:
            if isinstance(shards[0], cls):
                return shards[0]
            with contextlib.suppress(Exception):
                return cls.from_url(shards[0])
        dicts = [parameters] if parameters else []
        for shard in filter(bool, shards):
            if isinstance(shard, Mapping):
                dicts.append(shard)
            else:
                dicts.append({"q": shard})
        self = super().__new__(cls)
        self.__proxy = MappingProxyType(_normalize_dicts(*dicts))
        return self

    async def __await(self):
        # pylint: disable=E1133
        async for element in self.__aiter__(no_clear=True):
            pass
        return element

    def __await__(self):
        return self.__await().__await__()

    async def __aiter__(self, *, no_clear: bool = False) -> _AsyncGenerator[NSElement, None]:
        if not self.agent:
            raise RuntimeError("The API's user agent is not yet set.")
        if "a" in self and self["a"].lower() == "sendtg":
            raise RuntimeError("This API wrapper does not support API telegrams.")
        if not self:
            # Preempt the request to conserve ratelimit
            raise BadRequest()
        url = str(self)

        parser = etree.XMLPullParser(["end"], base_url=url, remove_blank_text=True)
        parser.set_element_class_lookup(etree.ElementDefaultClassLookup(element=NSElement))
        events = parser.read_events()

        async with self.session.request(
            "GET", url, headers={"User-Agent": self.agent}
        ) as response:
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

    def __contains__(self, key: str) -> bool:
        return key in self.__proxy

    def __dir__(self):
        return set(super().__dir__()).union(
            dir(self.__proxy), (a for a in dir(type(self)) if not hasattr(type, a))
        )

    __eq__ = None

    def __getattr__(self, name: str):
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
    def threadsafe(self) -> Threadsafe:
        """
        Returns a threadsafe wrapper around this object.

        The returned wrapper may be called, awaited, or iterated over.
        Both standard and async iteration are supported.
        """
        return Threadsafe(self)

    @classmethod
    def from_url(cls, url: str, *shards: _Iterable[str], **parameters: _Iterable[str]) -> "Api":
        """
        Constructs an Api object from a provided URL.

        The Api object may be further modified with shards and parameters,
        as per the :class:`Api` constructor.
        """
        parsed_url = urlparse(str(url))
        url = parsed_url[: len(API_URL)]
        if any(url) and url != API_URL:
            raise ValueError("URL must be solely query parameters or an API url")
        return cls(*shards, parse_qs(parsed_url.query), parameters)


class Dumps(Enum):
    """
    Request the daily data dumps.
    Dumps docs can be found here: https://www.nationstates.net/pages/api.html#dumps

    Dumps objects support asynchronous iteration, which returns each nation / region's XML.
    To perform operations from another thread, use the :attr:`threadsafe` property.
    """

    __slots__ = ()

    NATIONS = urlunparse((*API_URL[:2], "/pages/nations.xml.gz", None, None, None))
    NATION = NATIONS
    REGIONS = urlunparse((*API_URL[:2], "/pages/regions.xml.gz", None, None, None))
    REGION = REGIONS

    async def __aiter__(self) -> _AsyncGenerator[NSElement, None]:
        if not Api.agent:
            raise RuntimeError("The API's user agent is not yet set.")

        url = self.value
        # pylint: disable=E1101
        tag = self.name.upper().rstrip("S")

        parser = etree.XMLPullParser(["end"], base_url=url, remove_blank_text=True, tag=tag)
        parser.set_element_class_lookup(etree.ElementDefaultClassLookup(element=NSElement))
        events = parser.read_events()
        dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)

        async with Api.session.request("GET", url, headers={"User-Agent": Api.agent}) as response:
            async for data, _ in response.content.iter_chunks():
                parser.feed(dobj.decompress(data))
                for _, element in events:
                    yield element
                    element.clear()
                    while element.getparent() is not None and element.getprevious() is not None:
                        del element.getparent()[0]

    @property
    def threadsafe(self) -> Threadsafe:
        """
        Returns a threadsafe wrapper around this object.

        The returned wrapper may be iterated over.
        Both standard and async iteration are supported.
        """
        return Threadsafe(self)
