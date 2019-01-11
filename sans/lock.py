import aiohttp
import asyncio
import collections
import time


RATE = collections.namedtuple("RateLimit", ("requests", "block", "rpad", "bpad", "retry"))(
    50, 30, 2, 0.1, 900
)


class ResetLock(asyncio.Lock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._xrlrs = 0
        self._xra = None
        self._deferred = False

    def __aexit__(self, exc_type, exc, tb):
        if isinstance(exc, aiohttp.ClientResponseError):
            if exc.status == 429:
                self._xrlrs = 0
                self._xra = time.time() + exc.headers["X-Retry-After"] + RATE.bpad
                self.defer()
            elif "X-ratelimit-requests-seen" in exc.headers:
                self.xrlrs(exc.headers["X-ratelimit-requests-seen"])

        # returns a coroutine
        return super().__aexit__(exc_type, exc, tb)

    # Prevent deprecated lock usage
    __await__, __enter__, __iter__ = None, None, None

    def defer(self):
        self._deferred = True
        self._loop.call_later(self._xra - time.time(), super().release)

    def release(self):
        if not self._deferred:
            super().release()

    def xrlrs(self, xrlrs: int):
        xrlrs = int(xrlrs)
        if not self.locked():
            raise asyncio.InvalidStateError()
        now = time.time()
        if self._xra is None or xrlrs < self._xrlrs or self._xra <= now:
            self._xra = now + RATE.block + RATE.bpad
        self._xrlrs = xrlrs
        if xrlrs >= RATE.requests - RATE.rpad:
            self.defer()
