from __future__ import annotations

import asyncio
import threading
import time
import weakref
from collections import deque
from contextvars import Context, copy_context
from functools import partial
from operator import add
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import anyio
import sniffio
from anyio.lowlevel import cancel_shielded_checkpoint, checkpoint_if_cancelled

if TYPE_CHECKING:
    from typing_extensions import TypeVarTuple, Unpack

    _Ts = TypeVarTuple("_Ts")

__all__ = ["ResetLock"]


def _threading_sleep_forever(callback_deque: deque[Callable[[], Any]]):
    lock = threading.Lock()
    with lock:
        callback_deque.append(lock.release)
        try:
            lock.acquire()
        finally:
            callback_deque.remove(lock.release)


async def _asyncio_sleep_forever(callback_deque: deque[Callable[[], Any]]) -> None:
    future = asyncio.get_running_loop().create_future()
    release = partial(future.get_loop().call_soon_threadsafe, future.set_result, None)
    callback_deque.append(release)  # type: ignore
    try:
        await future
    finally:
        callback_deque.remove(release)  # type: ignore


try:
    import trio
except ImportError:
    pass
else:

    @trio.lowlevel.enable_ki_protection
    async def _trio_sleep_forever(
        callback_deque: deque[Callable[[], Any]],
    ) -> Awaitable[None]:
        task = trio.lowlevel.current_task()
        release = partial(
            trio.lowlevel.current_trio_token().run_sync_soon,
            trio.lowlevel.reschedule,
            task,
        )
        callback_deque.append(release)  # type: ignore

        try:
            return await trio.lowlevel.wait_task_rescheduled(
                lambda _: trio.lowlevel.Abort.SUCCEEDED
            )
        finally:
            callback_deque.remove(release)  # type: ignore


class _ThreadTimer(threading.Timer):
    def __init__(
        self,
        delay: float,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: Unpack[_Ts],
        context: Context | None = None,
    ) -> None:
        if not context:
            context = copy_context()
        super().__init__(delay, context.run, (callback, *args))

    def when(self) -> float:
        # when the timer completes if started at this very moment
        return self.interval + time.monotonic()

    def run(self) -> None:
        # freeze .when() at the current time
        self.when = partial(add, self.interval, time.monotonic())
        try:
            return super().run()
        finally:
            self.when = time.monotonic
            del self.function, self.args, self.kwargs


# I would love to make this utilize a semaphore instead
# However, since multiple clients can exist on one machine,
# locking and checking the headers sequentially is a requirement
class ResetLock:
    """
    Combination :class:`asyncio.Lock`, :class:`trio.Lock`, and :class:`threading.Lock`
    for ratelimiting purposes. Works based on a FIFO queue.

    Usage::

        lock = ResetLock()
        [async] with lock.maybe_lock(url):
            response = ...
            lock.maybe_defer(response.headers)

    Note that, when using :mod:`httpx`,
    using :class:`RateLimiter` will manage a global lock for you.
    """

    __deferred: _ThreadTimer | None = None

    def __finalizer(self) -> None:
        pass

    def __init__(self):
        self._lock = threading.Lock()
        self._waiters: deque[Callable[[], Any]] = deque()

    def _wake_up_next(self):
        try:
            release = next(iter(self._waiters))
        except StopIteration:
            return
        else:
            release()

    async def __aenter__(self) -> None:
        acquire = self._lock.acquire
        waiters = self._waiters
        sleep_forever: Callable[[deque[Callable[[], Any]]], Awaitable[None]] = (
            globals()[f"_{sniffio.current_async_library()}_sleep_forever"]
        )
        await checkpoint_if_cancelled()
        if not waiters:
            if acquire(False):
                await cancel_shielded_checkpoint()
                return
        try:
            await sleep_forever(waiters)
        except anyio.get_cancelled_exc_class():
            if not self._lock.locked():
                self._wake_up_next()
            raise
        else:
            # We were just rescheduled, so the lock is about to be released
            acquire()

    async def __aexit__(self, *_):
        self.release()

    def __enter__(self) -> bool:
        acquire = self._lock.acquire
        waiters = self._waiters
        if not waiters:
            if acquire(False):
                return True
        _threading_sleep_forever(waiters)
        return acquire()

    def __exit__(self, *_):
        self.release()

    @property
    def deferred(self) -> float | None:
        if self.__deferred:
            return time.monotonic() - self.__deferred.when()
        # return None

    _deferred = property(deferred.fget)

    @_deferred.setter
    def _deferred(self, value: _ThreadTimer):
        assert self.locked()
        self.__finalizer()
        value.start()
        self.__deferred = value
        self.__finalizer = weakref.finalize(self, value.finished.set)

    @_deferred.deleter
    def _deferred(self) -> None:
        assert self.locked()
        self.__finalizer()
        del self.__deferred

    def defer(self, delay: float) -> None:
        if not self.locked():
            return
        self._deferred = _ThreadTimer(delay, self._release)

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


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor

    from anyio.lowlevel import checkpoint

    async def main():
        lock = ResetLock()

        def target(lock=lock):
            print("before threading lock")
            with lock:
                print("during threading lock")
                lock.defer(1)
            print("after threading lock")

        async def async_target(lock=lock):
            lib = sniffio.current_async_library()
            print(f"before {lib} lock")
            async with lock:
                print(f"during {lib} lock")
                lock.defer(1)
                await checkpoint()
            print(f"after {lib} lock")

        with ThreadPoolExecutor() as pool:
            async with anyio.create_task_group() as group:
                for _ in range(5):
                    group.start_soon(async_target)
                    pool.submit(target)
                    await checkpoint()

    anyio.run(main, backend="asyncio")
    anyio.run(main, backend="trio")
