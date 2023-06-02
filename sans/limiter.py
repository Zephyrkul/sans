from __future__ import annotations

import logging
import time
from contextlib import AsyncExitStack, ExitStack
from itertools import count, repeat, starmap
from math import ldexp
from random import random
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    ClassVar,
    Generator,
    Iterator,
    Mapping,
    TypeVar,
)

import anyio
import httpx

# from . import _state
from .errors import AgentNotSetError
from .lock import ResetLock
from .response import Response
from .url import API_URL

if TYPE_CHECKING:
    pass

__all__ = ["RateLimiter", "TelegramLimiter"]
LOG = logging.getLogger(__name__)
_KT = TypeVar("_KT")
_T = TypeVar("_T")


def _get_as_int(mapping: Mapping[_KT, Any], key: _KT, default: _T) -> int | _T:
    try:
        return int(mapping[key])
    except (KeyError, ValueError):
        return default


class _Backoff:
    def __getitem__(self, item: slice) -> Iterator[float]:
        if item.stop is None or item.step == 0:
            indices = count(item.start, item.step)
        else:
            indices = range(item.start or 0, item.stop, item.step or 1)

        # Yields random numbers in the range of [0, 2**index)
        return map(ldexp, starmap(random, repeat(())), indices)


_backoff = _Backoff()


class RateLimiter(httpx.Auth):
    """
    httpx Auth utility object which implements ratelimiting, User-Agent management,
    and exponential backoff, while adding XML support to the resulting Response.
    """

    _agent: ClassVar = ""
    _lock: ClassVar = ResetLock()

    def _request_hook(self, request: httpx.Request) -> httpx.Request:
        agent = RateLimiter._agent
        if not agent:
            raise AgentNotSetError("sans has no set agent")
        request.headers["User-Agent"] = agent
        return request

    def _response_hook(self, response: httpx.Response) -> None:
        response_headers = response.headers
        # Retry-After is handled before this point
        xrlr = _get_as_int(response_headers, "RateLimit-Remaining", 1)
        if xrlr:
            return
        xrlr = _get_as_int(response_headers, "RateLimit-Reset", 0)
        RateLimiter._lock.defer(xrlr)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        if request.url.host == API_URL.host:
            request = self._request_hook(request)
        response = yield request
        response.__class__ = Response
        if response.url.host == API_URL.host:
            self._response_hook(response)

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        recruitment_delay: int = 0
        is_telegram_limiter = isinstance(self, TelegramLimiter)
        with ExitStack() as stack:
            if request.url.copy_with(query=None) == API_URL:
                if is_telegram_limiter:
                    stack.enter_context(TelegramLimiter._lock)
                    if TelegramLimiter._last_request is not None:
                        time.sleep(
                            max(
                                TelegramLimiter._last_request
                                + self._recruitment_delay
                                - time.monotonic(),
                                0,
                            )
                        )
                stack.enter_context(RateLimiter._lock)
            # The below is equivalent to: return (yield from self.auth_flow(request))
            # but with exponential backoff, locking, and ratelimit retry added.
            # See https://peps.python.org/pep-0380/#formal-semantics for details
            flow = self.auth_flow(request)
            try:
                _yield = next(flow)
            except StopIteration as exc:
                assert exc.value is None
                return
            backoff = _backoff[:6]
            while True:
                try:
                    _sent = yield _yield
                except GeneratorExit:
                    flow.close()
                    raise
                except BaseException as exc:
                    try:
                        _yield = flow.throw(exc)
                    except StopIteration as exc:
                        assert exc.value is None
                        return
                else:
                    status = _sent.status_code
                    if status == 429:
                        retry = _get_as_int(_sent.headers, "Retry-After", 0)
                        if retry:
                            LOG.info("Ratelimit hit, retrying in %s seconds.", retry)
                            remaining = _get_as_int(
                                _sent.headers, "Ratelimit-Remaining", 0
                            )
                            with ExitStack() as unlock_stack:
                                if remaining and not is_telegram_limiter:
                                    # Unmarked Telegram API
                                    LOG.warning(
                                        "Telegram API was used without using sans.TelegramLimiter.",
                                        stack_info=True,
                                    )
                                    is_telegram_limiter = True
                                    # infer the recruitment delay from the headers
                                    assert TelegramLimiter._last_request is not None
                                    if (
                                        time.monotonic() + retry
                                        > TelegramLimiter._last_request + 105
                                    ):
                                        recruitment_delay = 180
                                    else:
                                        recruitment_delay = 30
                                    unlock_stack.enter_context(
                                        RateLimiter._lock.unlock
                                    )  # let other requests go through
                                    stack.enter_context(
                                        TelegramLimiter._lock
                                    )  # while acquiring the telegram lock in the outer stack
                                    retry = max(
                                        TelegramLimiter._last_request
                                        + recruitment_delay
                                        - time.monotonic(),
                                        0,
                                    )
                                time.sleep(retry)
                            # fall out of RL._lock.unlock scope
                            backoff = _backoff[:6]
                            continue
                    elif status in [500, 502]:
                        try:
                            retry = next(backoff)
                        except StopIteration:
                            pass  # out of retries
                        else:
                            LOG.debug(
                                "Status %s received, retrying in %.0f seconds.",
                                status,
                                retry,
                            )
                            time.sleep(retry)
                            continue  # retry with the same request
                    try:
                        _yield = flow.send(_sent)
                    except StopIteration as exc:
                        if is_telegram_limiter:
                            TelegramLimiter._last_request = time.monotonic()
                        assert exc.value is None
                        return
                    backoff = _backoff[:6]

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        recruitment_delay: int = 0
        is_telegram_limiter = isinstance(self, TelegramLimiter)
        async with AsyncExitStack() as stack:
            if request.url.copy_with(query=None) == API_URL:
                if is_telegram_limiter:
                    await stack.enter_async_context(TelegramLimiter._lock)
                    if TelegramLimiter._last_request is not None:
                        await anyio.sleep(
                            max(
                                TelegramLimiter._last_request
                                + self._recruitment_delay
                                - time.monotonic(),
                                0,
                            )
                        )
                await stack.enter_async_context(RateLimiter._lock)
            # The below is equivalent to: return (yield from self.auth_flow(request))
            # but with exponential backoff, locking, and ratelimit retry added.
            # See https://peps.python.org/pep-0380/#formal-semantics for details
            flow = self.auth_flow(request)
            try:
                _yield = next(flow)
            except StopIteration as exc:
                assert exc.value is None
                return
            backoff = _backoff[:6]
            while True:
                try:
                    _sent = yield _yield
                except GeneratorExit:
                    flow.close()
                    raise
                except BaseException as exc:
                    try:
                        _yield = flow.throw(exc)
                    except StopIteration as exc:
                        assert exc.value is None
                        return
                else:
                    status = _sent.status_code
                    if status == 429:
                        retry = _get_as_int(_sent.headers, "Retry-After", 0)
                        if retry:
                            LOG.info("Ratelimit hit, retrying in %s seconds.", retry)
                            remaining = _get_as_int(
                                _sent.headers, "Ratelimit-Remaining", 0
                            )
                            async with AsyncExitStack() as unlock_stack:
                                if remaining and not is_telegram_limiter:
                                    # Unmarked Telegram API
                                    LOG.warning(
                                        "Telegram API was used without using sans.TelegramLimiter.",
                                        stack_info=True,
                                    )
                                    is_telegram_limiter = True
                                    # infer the recruitment delay from the headers
                                    assert TelegramLimiter._last_request is not None
                                    if (
                                        time.monotonic() + retry
                                        > TelegramLimiter._last_request + 105
                                    ):
                                        recruitment_delay = 180
                                    else:
                                        recruitment_delay = 30
                                    await unlock_stack.enter_async_context(
                                        RateLimiter._lock.unlock
                                    )  # let other requests go through
                                    await stack.enter_async_context(
                                        TelegramLimiter._lock
                                    )  # while acquiring the telegram lock in the outer stack
                                    retry = max(
                                        TelegramLimiter._last_request
                                        + recruitment_delay
                                        - time.monotonic(),
                                        0,
                                    )
                                await anyio.sleep(retry)
                            # fall out of RL._lock.unlock scope
                            backoff = _backoff[:6]
                            continue
                    elif status in [500, 502]:
                        try:
                            retry = next(backoff)
                        except StopIteration:
                            pass  # out of retries
                        else:
                            LOG.debug(
                                "Status %s received, retrying in %.0f seconds.",
                                status,
                                retry,
                            )
                            await anyio.sleep(retry)
                            continue  # retry with the same request
                    try:
                        _yield = flow.send(_sent)
                    except StopIteration as exc:
                        if is_telegram_limiter:
                            TelegramLimiter._last_request = time.monotonic()
                        assert exc.value is None
                        return
                    backoff = _backoff[:6]


class TelegramLimiter(RateLimiter):
    _lock: ClassVar = ResetLock()
    _last_request: ClassVar[float | None] = None

    def __init__(self, *, recruitment: bool) -> None:
        super().__init__()
        self._recruitment_delay = 180 if recruitment else 30
