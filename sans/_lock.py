import aiohttp
import asyncio
import collections
import time


RATE = collections.namedtuple(
    "RateLimit", ("requests", "block", "rpad", "bpad", "retry")
)(50, 30, 2, 0.1, 900)


class ResetLock(asyncio.Lock):
    __slots__ = "__xrlrs", "__xra", "__deferred"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__xrlrs = 0
        self.__xra = None
        self.__deferred = False

    def __aexit__(self, exc_type, exc, tb):
        if isinstance(exc, aiohttp.ClientResponseError):
            if exc.status == 429:
                self._xra(exc.headers["X-Retry-After"])
            elif "X-ratelimit-requests-seen" in exc.headers:
                self._xrlrs(exc.headers["X-ratelimit-requests-seen"])

        # returns a coroutine
        return super().__aexit__(exc_type, exc, tb)

    # Prevent deprecated lock usage
    __await__, __enter__, __iter__ = None, None, None

    def _defer(self):
        self.__deferred = True
        self._loop.call_later(self.__xra - time.time(), self._release)

    def release(self):
        if not self.__deferred:
            super().release()

    def _release(self):
        self.__deferred = False
        super().release()

    def _xra(self, xra: int):
        xra = int(xra)
        self.__xrlrs = 0
        self.__xra = time.time() + xra + RATE.bpad
        self._defer()

    def _xrlrs(self, xrlrs: int):
        now = time.time()
        xrlrs = int(xrlrs)
        if self.__xra is None or xrlrs < self.__xrlrs or self.__xra <= now:
            self.__xra = now + RATE.block + RATE.bpad
        self.__xrlrs = xrlrs
        if xrlrs >= RATE.requests - RATE.rpad:
            self._defer()

    @property
    def xra(self):
        if self.__deferred:
            return self.__xra
        return None

    @property
    def xrlrs(self):
        return self.__xrlrs
