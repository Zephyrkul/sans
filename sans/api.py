import aiohttp
import asyncio
import contextlib
import functools
import sys
import zlib
from collections.abc import Iterable, Mapping
from datetime import date as Date
from lxml import etree, objectify
from types import MappingProxyType
from typing import (
    Any as _Any,
    AsyncGenerator as _AsyncGenerator,
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)
from urllib.parse import parse_qs, unquote_plus, urlencode, urlparse, urlunparse

from .errors import BadRequest
from .info import API_URL, __version__
from .objects import Threadsafe, NSResponse
from .utils import get_running_loop
from ._lock import ResetLock


__all__ = ["Api", "Dumps", "Archives"]


AGENT_FMT = f"{{}} Python/{sys.version_info[0]}.{sys.version_info[1]} aiohttp/{aiohttp.__version__} sans/{__version__}"
API_VERSION = "9"
PINS: dict = {}


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
    final: dict = {}
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
    """
    The :class:`Api`'s metaclass.

    Lazily loads and controls access and settings to various global states,
    accessible by attribute access from the :class:`Api` class.
    """

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._agent = None
        cls.__lock = None
        cls._loop = None
        cls._session = None

    @property
    def agent(cls) -> _Optional[str]:
        """The API wrapper's set user agent."""
        return cls._agent

    @agent.setter
    def agent(cls, value: str) -> None:
        if value:
            cls._agent = AGENT_FMT.format(value)

    @property
    def loop(cls) -> _Optional[asyncio.AbstractEventLoop]:
        """The API wrapper's event loop.

        Cannot be changed once it has been set or referenced."""
        if not cls._loop:
            cls._loop = get_running_loop()
        return cls._loop

    @loop.setter
    def loop(cls, loop: asyncio.AbstractEventLoop) -> None:
        if cls._loop and cls._loop != loop:
            raise asyncio.InvalidStateError("Cannot change loop when it's already set!")
        cls._loop = loop

    @property
    def session(cls) -> aiohttp.ClientSession:
        """The API wrapper's HTTP client session."""
        if not cls._session or cls._session.closed:
            loop = cls.loop
            if not loop:
                cls.loop = asyncio.get_event_loop()
            cls._session = aiohttp.ClientSession(loop=loop, response_class=NSResponse)
        return cls._session

    @property
    def _lock(cls) -> ResetLock:
        if not cls.__lock:
            loop = cls.loop
            if not loop:
                cls.loop = asyncio.get_event_loop()
            cls.__lock = ResetLock(loop=loop)
        return cls.__lock

    @property
    def locked(cls) -> _Optional[bool]:
        """
        Whether or not the API's lock is currently locked.

        As every request acquires the lock, use :attr:`xra` to check if the rate limit is saturated instead.
        """
        if cls.__lock:
            return cls.__lock.locked()
        return None

    @property
    def xra(cls) -> _Optional[float]:
        """
        If the rate limit is currently saturated,
        returns when another API call can be made in the form of a Unix timestamp.
        Otherwise, returns `None`.
        """
        if cls.__lock:
            return cls.__lock.xra
        return None


class Api(metaclass=ApiMeta):
    r"""
    Construct and send an NS API request.
    NS API docs can be found here: https://www.nationstates.net/pages/api.html

    This is a low-level API wrapper. Some attempts will be made to prevent bad requests,
    but it will not check shards against a verified list.
    Authentication may be provided for private nation shards.
    X-Pin headers are be stored internally and globally for ease of use.

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
    password: str
        X-Password authentication for private nation shards.
    autologin: str
        X-Autologin authentication for private nation shards.
    \*\*parameters: str
        Query parameters to append to the request, e.g. nation, scale.

    Examples
    --------

    Usage::

        darc = await Api(nation="darcania")
        async for shard in Api(nation="testlandia"):
           print(pretty_string(shard))

        tnp = Api(region="the_north_pacific").threadsafe()
        for shard in Api(region="testregionia").threadsafe:
            print(pretty_string(shard))
    """

    __slots__ = ("__proxy", "_password", "_str", "_hash", "_last_response")

    def __new__(
        cls,
        *shards: _Union[str, _Iterable[str]],
        password: _Optional[str] = None,
        autologin: _Optional[str] = None,
        **parameters: str,
    ):
        if len(shards) == 1 and not parameters:
            if isinstance(shards[0], cls):
                return shards[0]
            with contextlib.suppress(Exception):
                return cls.from_url(shards[0])
        return super().__new__(cls)

    def __init__(
        self,
        *shards: _Union[str, _Iterable[str]],
        password: _Optional[str] = None,
        autologin: _Optional[str] = None,
        **parameters: str,
    ):
        has_nation = "nation" in parameters
        dicts = [parameters] if parameters else []
        for shard in filter(bool, shards):
            if isinstance(shard, Mapping):
                dicts.append(shard)
                if not has_nation and "nation" in shard:
                    has_nation = True
            else:
                dicts.append({"q": shard})
        if not has_nation and (password or autologin):
            raise ValueError("Authentication may only be used with the Nation API.")
        self.__proxy = MappingProxyType(_normalize_dicts(*dicts))
        self._password = password
        self._last_response = None
        self._str = None
        self._hash = None

    async def __await(self):
        async for element in self.__aiter__(clear=False):
            pass
        return element

    def __await__(self):
        return self.__await().__await__()

    async def __aiter__(
        self, *, clear: bool = True
    ) -> _AsyncGenerator[objectify.ObjectifiedElement, None]:
        if not Api.agent:
            raise RuntimeError("The API's user agent is not yet set.")
        if "a" in self and self["a"].lower() == "sendtg":
            raise RuntimeError("This API wrapper does not support API telegrams.")
        if not self:
            # Preempt the request to conserve ratelimit
            raise BadRequest()
        url = str(self)

        headers = {"User-Agent": Api.agent}
        if self._password:
            headers["X-Password"] = self._password
        autologin = self.autologin
        if autologin:
            headers["X-Autologin"] = autologin
        if self.get("nation") in PINS:
            headers["X-Pin"] = PINS[self["nation"]]

        async with Api.session.request("GET", url, headers=headers) as response:
            self._last_response = response
            if "X-Autologin" in response.headers:
                self._password = None
            if "X-Pin" in response.headers:
                PINS[self["nation"]] = response.headers["X-Pin"]
            response.raise_for_status()

            encoding = (
                response.headers["Content-Type"].split("charset=")[1].split(",")[0]
            )
            with contextlib.suppress(etree.XMLSyntaxError), contextlib.closing(
                etree.XMLPullParser(["end"], base_url=url, remove_blank_text=True)
            ) as parser:
                parser.set_element_class_lookup(objectify.ObjectifyElementClassLookup())
                events = parser.read_events()

                async for data, _ in response.content.iter_chunks():
                    parser.feed(data.decode(encoding))
                    for _, element in events:
                        if clear and (
                            element.getparent() is None
                            or element.getparent().getparent() is not None
                        ):
                            continue
                        yield element
                        if clear:
                            element.clear(keep_tail=True)

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
            if self["a"] == "sendtg" and all(
                a in self for a in ("client", "tgid", "key", "to")
            ):
                return True
            return False
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
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __getitem__(self, key):
        return self.__proxy[str(key).lower()]

    def __hash__(self):
        if self._hash is not None:
            return self._hash
        params = sorted(
            (k, v if isinstance(v, str) else " ".join(sorted(v)))
            for k, v in self.items()
        )
        self._hash = hash(tuple(params))
        return self._hash

    def __iter__(self):
        return iter(self.__proxy)

    def __len__(self):
        return len(self.__proxy)

    def __repr__(self) -> str:
        return "{}.{}({})".format(
            type(self).__module__,
            type(self).__name__,
            ", ".join("{}={!r}".format(*t) for t in self.__proxy.items()),
        )

    def __str__(self) -> str:
        if self._str is not None:
            return self._str
        params = [
            (k, v if isinstance(v, str) else "+".join(v)) for k, v in self.items()
        ]
        self._str = urlunparse((*API_URL, None, urlencode(params, safe="+"), None))
        return self._str

    @property
    def autologin(self) -> _Optional[str]:
        """
        If a private nation shard was properly requested and returned,
        this property may be used to get the "X-Autologin" token.
        """
        if self._last_response:
            return self._last_response.headers.get("X-Autologin")
        return None

    @property
    def last_headers(self) -> _Optional[_Mapping[str, str]]:
        """
        Returns the headers returned from the last request this API object sent.
        """
        if self._last_response:
            return self._last_response.headers
        return None

    @property
    def last_response(self) -> _Optional[NSResponse]:
        """
        Returns the response object from the last request this API object sent.
        """
        return self._last_response

    @property
    def threadsafe(self) -> Threadsafe:
        """
        Returns a threadsafe wrapper around this object.

        The returned wrapper may be called, awaited, or iterated over.
        Both standard and async iteration are supported.
        """
        return Threadsafe(self)

    @classmethod
    def from_url(
        cls, url: str, *shards: _Iterable[str], **parameters: _Iterable[str]
    ) -> "Api":
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


class _DumpsType:
    __slots__ = "name"

    def __init__(self, name):
        self.name = name

    @functools.lru_cache(maxsize=2)
    def __call__(self, *date: _Union[Date, int]):
        return Dumps(self, *date)

    def __aiter__(self):
        return self().__aiter__()

    def __getattr__(self, attr):
        return getattr(self(), attr)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name
        return NotImplemented


class Dumps:
    """
    Request the daily data dumps.
    Dumps docs can be found here: https://www.nationstates.net/pages/api.html#dumps

    Dumps objects support asynchronous iteration, which returns each nation's / region's XML.
    To perform operations from another thread, use the :attr:`threadsafe` property.
    """

    __slots__ = ("url", "_category", "_last_response")

    NATIONS: _ClassVar[_DumpsType] = _DumpsType("nations")
    NATION = NATIONS
    REGIONS: _ClassVar[_DumpsType] = _DumpsType("regions")
    REGION = REGIONS

    def __init__(self, category: _DumpsType, *date: _Union[Date, int]):
        self._category = category
        self._last_response = None
        if not date:
            self.url = urlunparse(
                (*API_URL[:2], "/pages/{name}.xml.gz", None, None, None)
            ).format(name=category.name)
        else:
            if len(date) == 1 and isinstance(date, Date):
                date = date[0]
            else:
                date = Date(*date)
            self.url = urlunparse(
                (*API_URL[:2], "/archive/{name}/{date}-{name}-xml.gz", None, None, None)
            ).format(name=category.name, date=date.isoformat())

    async def __aiter__(self) -> _AsyncGenerator[objectify.ObjectifiedElement, None]:
        if not Api.agent:
            raise RuntimeError("The API's user agent is not yet set.")

        url = self.url
        tag = self._category.name.upper().rstrip("S")
        dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)

        async with Api.session.request(
            "GET", url, headers={"User-Agent": Api.agent}
        ) as response:
            self._last_response = response
            response.raise_for_status()

            with contextlib.suppress(etree.XMLSyntaxError), contextlib.closing(
                etree.XMLPullParser(
                    ["end"], base_url=url, remove_blank_text=True, tag=tag
                )
            ) as parser:
                parser.set_element_class_lookup(objectify.ObjectifyElementClassLookup())
                events = parser.read_events()

                async for data, _ in response.content.iter_chunks():
                    parser.feed(dobj.decompress(data))
                    for _, element in events:
                        yield element
                        element.clear(keep_tail=True)

    @property
    def last_headers(self) -> _Optional[_Mapping[str, str]]:
        """
        Returns the headers returned from the last request this API object sent.
        """
        if self._last_response:
            return self._last_response.headers
        return None

    @property
    def last_response(self) -> _Optional[NSResponse]:
        """
        Returns the response object from the last request this API object sent.
        """
        return self._last_response

    @property
    def threadsafe(self) -> Threadsafe:
        """
        Returns a threadsafe wrapper around this object.

        The returned wrapper may be iterated over.
        Both standard and async iteration are supported.
        """
        return Threadsafe(self)


Archives = Dumps
