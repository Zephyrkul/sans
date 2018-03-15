import asyncio
import inspect
import functools


__all__ = []


class RateLimit:

    def __init__(self, loop: asyncio.AbstractEventLoop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._block = (
            50, # requests per
            30  # seconds
        )
        self._semaphore = asyncio.BoundedSemaphore(self._block[0], loop=self._loop)

    def __call__(self, function):
        @functools.wraps(function)
        async def _wrapper(*args, **kwargs):
            await self._semaphore.acquire()
            try:
                return await function(*args, **kwargs)
            finally:
                self._loop.call_later(self._block[1], self._semaphore.release)
        return _wrapper

    @property
    def loop(self):
        return self._loop


def ratelimited(function):
    try:
        return ratelimited.ratelimit(function)
    except AttributeError:
        ratelimited.ratelimit = RateLimit()
        return ratelimited.ratelimit(function)
