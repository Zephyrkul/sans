from __future__ import annotations

from typing import overload

import httpx

from .limiter import RateLimiter
from .url import API_URL

try:
    # guard against reloading
    _PINS  # type: ignore  # noqa: B018
except NameError:
    _PINS: dict[str, str] = {}


__all__ = ["NSAuth"]


class NSAuth(RateLimiter):
    @overload
    def __init__(self, *, password: str) -> None: ...

    @overload
    def __init__(self, *, autologin: str) -> None: ...

    def __init__(
        self, *, password: str | None = None, autologin: str | None = None
    ) -> None:
        self._password = password
        self.autologin = autologin

    @property
    def password(self) -> str | None:
        return self._password

    @password.setter
    def password(self, value: str | None) -> None:
        if value:
            self._autologin = None  # likely out of date
        self._password = value

    @property
    def autologin(self) -> str | None:
        return self._autologin

    @autologin.setter
    def autologin(self, value: str | None) -> None:
        if value:
            self._password = None  # no longer needed
        self._autologin = value

    def _request_hook(self, request: httpx.Request) -> httpx.Request:
        params = request.url.params
        nation = params.get("nation")
        if not nation:
            return request
        headers = request.headers
        if self._autologin:
            headers["X-Autologin"] = self._autologin
            pin = _PINS.get(self._autologin)
            if pin:
                headers["X-Pin"] = pin
        elif self._password:
            headers["X-Password"] = self._password
        try:
            is_empty = not request.content
        except httpx.RequestNotRead:
            pass  # don't override content
        else:
            if is_empty and ("c" in params or request.method == "POST"):
                # coerce a POST request
                headers.pop("Content-Type", None)
                headers.pop("Content-Length", None)
                request = httpx.Request("POST", API_URL, headers=headers, data=params)
        return super()._request_hook(request)

    def _response_hook(self, response: httpx.Response) -> None:
        autologin: str | None = response.headers.get("X-Autologin")
        if autologin:
            self.autologin = autologin
            pin = response.headers.get("X-Pin")
            if pin:
                _PINS[autologin] = pin
        return super()._response_hook(response)
