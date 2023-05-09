from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Iterator, Mapping, overload

from httpx import (
    AsyncClient as _XAsyncClient,
    BaseTransport,
    Client as _XClient,
    Limits,
    Response as _Response,
)
from httpx._types import *

from .limiter import RateLimiter
from .response import Response

__all__ = [
    "Client",
    "AsyncClient",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "stream",
]

class _ClientMixin:
    @property
    def auth(self) -> RateLimiter: ...
    @auth.setter
    def auth(self, auth: RateLimiter) -> None: ...

class ClientType(_ClientMixin, _XClient):
    @overload
    def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def send(
        self,
        request: Request,
        *,
        stream: bool = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
    ) -> _Response: ...
    @overload
    def send(
        self,
        request: Request,
        *,
        stream: bool = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
    ) -> Response: ...
    @overload
    def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    @contextmanager
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Iterator[_Response]: ...
    @overload
    @contextmanager
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Iterator[Response]: ...

class AsyncClientType(_ClientMixin, _XAsyncClient):
    @overload
    async def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def send(
        self,
        request: Request,
        *,
        stream: bool = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
    ) -> _Response: ...
    @overload
    async def send(
        self,
        request: Request,
        *,
        stream: bool = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
    ) -> Response: ...
    @overload
    async def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    async def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> _Response: ...
    @overload
    async def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> Response: ...
    @overload
    @asynccontextmanager
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> AsyncIterator[_Response]: ...
    @overload
    @asynccontextmanager
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData[Any, Any] = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> AsyncIterator[Response]: ...

def Client(
    *,
    auth: RateLimiter = ...,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    http1: bool = ...,
    http2: bool = ...,
    proxies: ProxiesTypes = ...,
    mounts: Mapping[str, BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: Limits = ...,
    max_redirects: int = ...,
    event_hooks: Mapping[str, List[Callable[..., Any]]] = ...,
    base_url: URLTypes = ...,
    transport: BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> ClientType: ...
def AsyncClient(
    *,
    auth: RateLimiter = ...,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    http1: bool = ...,
    http2: bool = ...,
    proxies: ProxiesTypes = ...,
    mounts: Mapping[str, BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: Limits = ...,
    max_redirects: int = ...,
    event_hooks: Mapping[str, List[Callable[..., Any]]] = ...,
    base_url: URLTypes = ...,
    transport: BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> AsyncClientType: ...
def request(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData[Any, Any] = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
@contextmanager
def stream(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData[Any, Any] = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> Iterator[Response]: ...
def get(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def options(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def head(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def post(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData[Any, Any] = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def put(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData[Any, Any] = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def patch(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData[Any, Any] = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
def delete(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: RateLimiter = ...,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> Response: ...
