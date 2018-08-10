import sys
try:
    import regex as re
except ImportError:
    import re
from collections import abc
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from .request import Request
from .structs import qdict


__all__ = ["__version__", "__apiversion__", "API"]
__version__ = "0.1.0a"
__apiversion__ = "9"


AGENT_FORMAT = "{0} sans/{1} {{}} python/{2[0]}.{2[1]}.{2[2]}"
SCHEME = "https"
NETLOC = "www.zephyrkul.info"
PATH = "/mock-ns/"
SPLITTER = re.compile(r"[\d\l\u]+")


class APIMeta(type):

    def __new__(cls, name, bases, classdict):
        # create an _agent if it's not specified
        if "_agent" not in classdict:
            classdict["_agent"] = None
        return super().__new__(cls, name, bases, classdict)

    @property
    def agent(cls):
        return cls._agent

    @agent.setter
    def agent(cls, value):
        cls._agent = AGENT_FORMAT.format(
            value, __version__, sys.version_info)


class API(metaclass=APIMeta):

    def __init__(self, *shards, url: str=None, session=None, **kwargs: str):
        self._session, self._shards, self._kwargs = None, None, None
        self(*shards, url=url, session=session, clear=True, **kwargs)

    def __call__(self, *shards, url: str=None, session=None, clear=False, **kwargs: str):
        self._session = session if session else self._session
        if len(shards) == 1 and not isinstance(shards[0], str) and isinstance(shards[0], abc.Iterable):
            shards = tuple(shards[0])
        if url:
            kwargs.update(parse_qs(urlparse(url).query))
            shards += (kwargs.pop("q", ""),)
        shards = (m.group(0) for m in SPLITTER.finditer(str(shard).lower()) for shard in shards)
        kwargs = {k.lower(): str(v).lower() for k, v in kwargs.items()}
        if clear:
            self._shards = set(shards)
            self._kwargs = kwargs
        else:
            self._shards.update(shards)
            self._kwargs.update(kwargs)
        return self

    def __getattribute__(self, name):
        if name.startswith("_"):
            return super(API, self).__getattribute__(name)
        if "__" in name:
            self._kwargs.update((map(str.lower, name.split("__")),))
        else:
            self._shards.update(m.group(0) for m in SPLITTER.finditer(name.lower()))
        return self

    def __setattr__(self, name, value):
        if value:
            self._kwargs[name.lower()] = str(value).lower()
        else:
            del self._kwargs[name.lower()]
        return self

    def __delattr__(self, name):
        try:
            self._shards.remove(name)
        except KeyError:
            super(API, self).__delattr__(name)

    def __contains__(self, name):
        return str(name).lower() in self._shards

    def __getitem__(self, name):
        return self._kwargs.__getitem__(str(name).lower())

    def __setitem__(self, name, value):
        return self._kwargs.__setitem__(str(name).lower(), str(value).lower())

    def __delitem__(self, name):
        return self._kwargs.__delitem__(str(name).lower())

    def __len__(self):
        return len(self._query)

    def __repr__(self):
        return "{}.{}(url={!r})".format(self.__module__, type(self).__name__, str(self))

    def __str__(self):
        return urlunparse((SCHEME, NETLOC, PATH, "", str(self._query), ""))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._query == other._query and self._method == other._method

    def __iter__(self):
        return Request(str(self), agent=self.__class__.agent, session=self._session, method=self._method)

    __aiter__ = __iter__

    def _request(self):
        """Forms an HTTP request to the NationStates or API.

        While this method is synchronous, it returns an asynchronous iterator.
        So, while you *can* do the following::

            request = NS.Nation(...)

        You will still have to use asynchronous iteration to get the actual data::

            async for event, result in request:
                ...

        The actual request will not be opened until it is iterated over; thus you
        can prepare several requests ahead of time and space out the
        requests themselves.

        This wrapper supports the API ratelimit automatically.

        Parameters:
            *args: The arguments for the specified NationStates API.
                Any excess args are considered to be no-op shards.
                Nation: One arg. Specifies the nation to request.
                Region: One arg. Specifies the region to request.
                World: Zero args.
                WA: One arg. Specifies the council to request.
                Telegram: Four args. client, to, tgid, key.
                Verification: Two to three args. nation, checksum, token.
                Dumps: One arg. "nations" or "regions".

        Keyword Arguments:
            method: Specifies the HTTP Method. Can be either GET or HEAD.
            session:
                The `ClientSession` to use. Defaults to no session.
            **kwargs: Keyword arguments.
                If the value is a String, Integer, or Iterable,
                assume it's a shard keyword parameter.
                Otherwise, assume it's a shard / processor pair.
                In the latter case, the iterator will take any XML Elements
                matching the shard key and pass the Element object into
                the callable / awaitable and call / await it.
                If the processor isn't callable / awaitable, for example None,
                the Request object will yield the Element's text.
                If no processors are specified, all Elements' texts are yielded.

        Returns:
            An asynchronous iterator.

        Yields:
            tuple: A tuple with the event (the requested HTML / XML element or
                other events) and the processed HTML / XML element.
        """
        pass
