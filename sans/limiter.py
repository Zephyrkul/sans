from __future__ import annotations

import logging
import sys
import time
from itertools import count
from math import ldexp
from random import random
from typing import AsyncGenerator, Generator, Iterator

import anyio
import httpx

from . import _state
from .errors import AgentNotSetError
from .response import Response
from .url import API_URL

__all__ = ["RateLimiter"]
LOG = logging.getLogger(__name__)


class _Backoff:
    def __getitem__(self, item: slice) -> Iterator[float]:
        def _next(index: int) -> float:
            # Random number in the range of [0, 2**index)
            return ldexp(random(), index)

        if item.stop is None or item.step == 0:
            return map(_next, count(item.start, item.step))

        return map(_next, range(item.start or 0, item.stop, item.step or 1))


class _NullContext:
    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass

    async def __aenter__(self):
        pass

    async def __aexit__(self, *_):
        pass


_backoff = _Backoff()
_nullctx = _NullContext()


class RateLimiter(httpx.Auth):
    """
    httpx Auth utility object which implements ratelimiting, User-Agent management,
    and exponential backoff, while adding XML support to the resulting Response.
    """

    def _request_hook(self, request: httpx.Request) -> httpx.Request:
        agent = _state.agent
        if not agent:
            raise AgentNotSetError("sans has no set agent")
        request.headers["User-Agent"] = agent
        return request

    def _response_hook(self, response: httpx.Response) -> None:
        _state.lock.maybe_defer(response.headers)

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
        if request.url.copy_with(query=None) == API_URL:
            ctx = _state.lock
        else:
            ctx = _nullctx
        with ctx:
            # The below is equivalent to: return (yield from self.auth_flow(request))
            # but with exponential backoff, locking, and ratelimit retry added.
            # See https://peps.python.org/pep-0380/#formal-semantics for details
            flow = self.auth_flow(request)
            try:
                _yield = next(flow)
            except StopIteration as exc:
                return exc.value
            backoff = _backoff[:5]
            while True:
                try:
                    _sent = yield _yield
                except GeneratorExit:
                    flow.close()
                    raise
                except BaseException:
                    try:
                        flow.throw(*sys.exc_info())  # type: ignore
                    except StopIteration as exc:
                        return exc.value
                else:
                    status = _sent.status_code
                    if status == 429:
                        retry = int(_sent.headers.get("Retry-After", 0))
                        if retry:
                            LOG.info("Ratelimit hit, retrying in %s seconds.", retry)
                            time.sleep(retry)
                            continue
                    elif status in [500, 502]:
                        try:
                            retry = next(backoff)
                        except StopIteration:
                            pass  # out of retries
                        else:
                            LOG.debug(
                                "Status %s received, retrying in %.1f seconds.",
                                status,
                                retry,
                            )
                            time.sleep(retry)
                            continue  # retry with the same request
                    try:
                        _yield = flow.send(_sent)
                    except StopIteration as exc:
                        return exc.value
                    backoff = _backoff[:5]

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if request.url.copy_with(query=None) == API_URL:
            ctx = _state.lock
        else:
            ctx = _nullctx
        async with ctx:
            # The below is equivalent to: return (yield from self.auth_flow(request))
            # but with exponential backoff, locking, and ratelimit retry added.
            # See https://peps.python.org/pep-0380/#formal-semantics for details
            flow = self.auth_flow(request)
            try:
                _yield = next(flow)
            except StopIteration as exc:
                assert exc.value is None
                return
            backoff = _backoff[:5]
            while True:
                try:
                    _sent = yield _yield
                except GeneratorExit:
                    flow.close()
                    raise
                except BaseException:
                    try:
                        flow.throw(*sys.exc_info())  # type: ignore
                    except StopIteration as exc:
                        assert exc.value is None
                        return
                else:
                    status = _sent.status_code
                    if status == 429:
                        retry = int(_sent.headers.get("Retry-After", 0))
                        if retry:
                            await anyio.sleep(retry)
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
                        assert exc.value is None
                        return
                    backoff = _backoff[:5]
