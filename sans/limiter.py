import sys
from typing import AsyncGenerator, Generator

from httpx import Auth, Request, Response

from . import _state  # type: ignore
from .response import Response as NSResponse

__all__ = ["RateLimiter"]


class RateLimiter(Auth):
    """
    httpx Auth object which implements ratelimiting, User-Agent management,
    and adds XML support to the resulting Response.
    """

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        if request.url.host == "www.nationstates.net":
            request.headers["User-Agent"] = _state.agent
        response = yield request
        _state.lock.maybe_defer(response.headers)
        response.__class__ = NSResponse

    def sync_auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        url = request.url
        with _state.lock.maybe_lock(url.host, url.path):
            return (yield from super().sync_auth_flow(request))

    async def async_auth_flow(
        self, request: Request
    ) -> AsyncGenerator[Request, Response]:
        url = request.url
        async with _state.lock.maybe_lock(url.host, url.path):
            # The below is equivalent to (yield from super().async_auth_flow(request))
            # See https://peps.python.org/pep-0380/#formal-semantics for details
            super_auth_flow = super().async_auth_flow(request)
            try:
                _yield = await super_auth_flow.__anext__()
            except StopAsyncIteration:
                return
            while True:
                try:
                    _sent = yield _yield
                except GeneratorExit:
                    await super_auth_flow.aclose()
                    raise
                except BaseException:
                    try:
                        await super_auth_flow.athrow(*sys.exc_info())  # type: ignore
                    except StopAsyncIteration:
                        return
                else:
                    try:
                        _yield = await super_auth_flow.asend(_sent)
                    except StopAsyncIteration:
                        return
