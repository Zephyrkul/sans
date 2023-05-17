from __future__ import annotations

from typing import (
    Any,
    AsyncContextManager,
    Callable,
    Collection,
    ContextManager,
    Mapping,
    NewType,
    overload,
)
from typing_extensions import TypedDict

import httpx
from httpx._types import (
    AuthTypes,
    CertTypes,
    CookieTypes,
    HeaderTypes,
    ProxiesTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
    VerifyTypes,
)

from .limiter import RateLimiter
from .response import Response

__all__ = [
    "Client",
    "ClientType",
    "AsyncClient",
    "AsyncClientType",
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

class _EventHooks(TypedDict):
    request: list[Callable[[httpx.Request], None]]
    response: list[Callable[[httpx.Response], None]]

class _EventHooksParam(TypedDict):
    request: Collection[Callable[[httpx.Request], None]]
    response: Collection[Callable[[httpx.Response], None]]

class _ClientMixin:
    @property
    def auth(self) -> RateLimiter: ...
    @auth.setter
    def auth(self, auth: RateLimiter) -> None: ...
    @property
    def event_hooks(self) -> _EventHooks: ...
    @event_hooks.setter
    def event_hooks(self, value: _EventHooksParam) -> None: ...

class _ClientType(_ClientMixin, httpx.Client):
    @overload
    def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
    def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
    ) -> Response: ...
    @overload
    def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
    ) -> httpx.Response: ...
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
    def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
    def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> ContextManager[Response]: ...
    @overload
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> ContextManager[httpx.Response]: ...

class _AsyncClientType(_ClientMixin, httpx.AsyncClient):
    @overload
    async def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
    async def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
    ) -> Response: ...
    @overload
    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
    ) -> httpx.Response: ...
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
    async def get(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    async def options(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    async def head(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    async def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
    async def post(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    async def put(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    async def patch(
        self,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
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
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
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
    async def delete(
        self,
        url: URLTypes,
        *,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> httpx.Response: ...
    @overload
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: RateLimiter = ...,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> AsyncContextManager[Response]: ...
    @overload
    def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = ...,
        data: RequestData = ...,
        files: RequestFiles = ...,
        json: Any = ...,
        params: QueryParamTypes = ...,
        headers: HeaderTypes = ...,
        cookies: CookieTypes = ...,
        auth: AuthTypes | None,
        follow_redirects: bool = ...,
        timeout: TimeoutTypes = ...,
        extensions: dict[Any, Any] = ...,
    ) -> AsyncContextManager[httpx.Response]: ...

ClientType = NewType("ClientType", _ClientType)
AsyncClientType = NewType("AsyncClientType", _AsyncClientType)

@overload
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
    mounts: Mapping[str, httpx.BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: httpx.Limits = ...,
    max_redirects: int = ...,
    event_hooks: _EventHooksParam = ...,
    base_url: URLTypes = ...,
    transport: httpx.BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> ClientType: ...
@overload
def Client(
    *,
    auth: AuthTypes | None,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    http1: bool = ...,
    http2: bool = ...,
    proxies: ProxiesTypes = ...,
    mounts: Mapping[str, httpx.BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: httpx.Limits = ...,
    max_redirects: int = ...,
    event_hooks: Mapping[str, list[Callable[..., Any]]] = ...,
    base_url: URLTypes = ...,
    transport: httpx.BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> httpx.Client: ...
@overload
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
    mounts: Mapping[str, httpx.BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: httpx.Limits = ...,
    max_redirects: int = ...,
    event_hooks: Mapping[str, Collection[Callable[..., Any]]] = ...,
    base_url: URLTypes = ...,
    transport: httpx.BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> AsyncClientType: ...
@overload
def AsyncClient(
    *,
    auth: AuthTypes | None,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    http1: bool = ...,
    http2: bool = ...,
    proxies: ProxiesTypes = ...,
    mounts: Mapping[str, httpx.BaseTransport] = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    limits: httpx.Limits = ...,
    max_redirects: int = ...,
    event_hooks: _EventHooksParam = ...,
    base_url: URLTypes = ...,
    transport: httpx.BaseTransport = ...,
    app: Callable[..., Any] = ...,
    trust_env: bool = ...,
) -> httpx.AsyncClient: ...
@overload
def request(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
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
@overload
def request(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
def stream(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
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
) -> ContextManager[Response]: ...
@overload
def stream(
    method: str,
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> ContextManager[httpx.Response]: ...
@overload
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
@overload
def get(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
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
@overload
def options(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
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
@overload
def head(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
def post(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
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
@overload
def post(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
def put(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
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
@overload
def put(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
def patch(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
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
@overload
def patch(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    content: RequestContent = ...,
    data: RequestData = ...,
    files: RequestFiles = ...,
    json: Any = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    timeout: TimeoutTypes = ...,
    follow_redirects: bool = ...,
    verify: VerifyTypes = ...,
    cert: CertTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
@overload
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
@overload
def delete(
    url: URLTypes,
    *,
    params: QueryParamTypes = ...,
    headers: HeaderTypes = ...,
    cookies: CookieTypes = ...,
    auth: AuthTypes | None,
    proxies: ProxiesTypes = ...,
    follow_redirects: bool = ...,
    cert: CertTypes = ...,
    verify: VerifyTypes = ...,
    timeout: TimeoutTypes = ...,
    trust_env: bool = ...,
) -> httpx.Response: ...
