from __future__ import annotations

import asyncio
import threading
from collections import deque
from contextvars import Context, copy_context
from functools import partial
from operator import add
from time import monotonic
from typing import TYPE_CHECKING, Any, Callable, Mapping, TypeVar
from urllib.parse import urlparse

if TYPE_CHECKING:
    from typing_extensions import Literal, Self

__all__ = ["ResetLock"]


_KT = TypeVar("_KT")


def _get_as_int(mapping: Mapping[_KT, Any], key: _KT, default: int) -> int:
    try:
        return int(mapping[key])
    except (KeyError, ValueError):
        return default


class _Timer(threading.Timer):
    def when(self) -> float:
        # when the timer completes if started at this very moment
        return monotonic() + self.interval

    def run(self) -> None:
        # freeze .when() at the current time
        self.when = partial(add, monotonic(), self.interval)
        return super().run()


class _NullContext:
    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass

    async def __aenter__(self):
        pass

    async def __aexit__(self, *_):
        pass


# I would love to make this utilize a semaphore instead
# However, since multiple clients can exist on one machine,
# locking and checking the headers sequentially is a requirement
class ResetLock:
    """
    Combination :class:`asyncio.Lock` and :class:`threading.Lock`
    for ratelimiting purposes.

    Usage::

        lock = ResetLock()
        [async] with lock.maybe_lock(url):
            response = ...
            lock.maybe_defer(response.headers)

    Note that, when using :module:`httpx`,
    using :class:`RateLimiter` will manage a global lock for you.
    """

    def __init__(self):
        self.__deferred: asyncio.TimerHandle | _Timer | None = None
        self._lock = threading.Lock()
        self._waiters: deque[asyncio.Future[Literal[True]]] = deque()

    def _wake_up_next(self):
        try:
            next_fut = next(iter(self._waiters))
        except StopIteration:
            return
        if next_fut.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        next_loop = next_fut.get_loop()
        if next_loop == loop:
            next_fut.set_result(True)
        else:
            next_loop.call_soon_threadsafe(next_fut.set_result, True)

    async def __aenter__(self) -> None:
        acquire = self._lock.acquire
        future_factory = asyncio.get_running_loop().create_future
        waiters_append = self._waiters.append
        waiters_remove = self._waiters.remove
        while not acquire(False):
            fut = future_factory()
            waiters_append(fut)
            try:
                try:
                    await fut
                finally:
                    waiters_remove(fut)
            except asyncio.CancelledError:
                self._wake_up_next()
                raise

    async def __aexit__(self, *_):
        self.release()

    def __enter__(self) -> bool:
        return self._lock.acquire()

    def __exit__(self, *_):
        self.release()

    @property
    def deferred(self) -> float | None:
        """
        Returns when the lock is scheduled to be released according to internal monotonic clocks,
        or None if the lock isn't deferred.
        """
        if self.__deferred:
            return self.__deferred.when()
        # return None

    # write-only property
    @partial(property, None)
    def _deferred(self, value: asyncio.TimerHandle | _Timer | None):
        assert self.locked()
        if self.__deferred:
            self.__deferred.cancel()
        self.__deferred = value

    @_deferred.deleter
    def _deferred(self) -> None:
        assert self.locked()
        if self.__deferred:
            self.__deferred.cancel()
        self.__deferred = None

    def maybe_defer(self, response_headers: Mapping[str, str]) -> None:
        if not self.locked():
            return
        try:
            call_later = asyncio.get_running_loop().call_later  # type: ignore
        except RuntimeError:

            def call_later(
                delay: float,
                callback: Callable[..., Any],
                *args: Any,
                context: Context | None = None,
            ) -> _Timer | asyncio.TimerHandle:
                if not context:
                    context = copy_context()
                timer = _Timer(delay, context.run, (callback, *args))
                timer.start()
                return timer

        xra = _get_as_int(response_headers, "Retry-After", 0)
        if xra:
            self._deferred = call_later(xra, self._release)
            return
        xrlr = _get_as_int(response_headers, "RateLimit-Remaining", 1)
        if xrlr:
            return
        xrlr = _get_as_int(response_headers, "RateLimit-Reset", 0)
        self._deferred = call_later(xrlr, self._release)

    def maybe_lock(self, hostname: str, path: str | None = None) -> Self | _NullContext:
        if not path:
            url = urlparse(hostname)
            hostname = url.hostname or ""
            path = url.path
        if hostname == "www.nationstates.net" and path == "/cgi-bin/api.cgi":
            return self
        return _NullContext()

    def locked(self):
        return self._lock.locked()

    def release(self):
        if self.deferred is not None:
            return
        self._wake_up_next()
        self._lock.release()

    def _release(self):
        del self._deferred
        self._wake_up_next()
        self._lock.release()
