from __future__ import annotations

from httpx import Request, Response

from .limiter import RateLimiter

try:
    # guard against reloading
    _PINS  # type: ignore  # noqa: B018
except NameError:
    _PINS: dict[str, str] = {}


__all__ = ["NSAuth"]


class NSAuth(RateLimiter):
    def __init__(self, *, password: str | None = None, autologin: str | None = None):
        self._password = password
        self.autologin = autologin

    @property
    def autologin(self) -> str | None:
        return self._autologin

    @autologin.setter
    def autologin(self, value: str | None) -> None:
        if value:
            self._password = None  # no longer needed
        self._autologin = value

    def _request_hook(self, request: Request) -> Request:
        nation = request.url.params.get("nation")
        if not nation:
            return request
        auth = {}
        if self._password:
            auth["X-Password"] = self._password
        elif self._autologin:
            auth["X-Autologin"] = self._autologin
        pin = _PINS.get(nation)
        if pin:
            auth["X-Pin"] = pin
        request.method = "POST"
        return super()._request_hook(request)

    def _response_hook(self, response: Response) -> None:
        autologin = response.headers.get("X-Autologin")
        if autologin:
            self.autologin = autologin
        return super()._response_hook(response)
