# MIT License

# Copyright (c) 2018 - 2023

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal

from .auth import *
from .client import *
from .errors import *
from .limiter import RateLimiter as RateLimiter, TelegramLimiter as TelegramLimiter
from .response import *
from .sse import *
from .url import *
from .utils import *

if _sys.version_info < (3, 8):
    from importlib_metadata import metadata as _metadata
else:
    from importlib.metadata import metadata as _metadata

__copyright__ = "Copyright 2019-2023 Zephyrkul"

_meta = _metadata(__name__)
__title__ = _meta["Name"]
__author__ = _meta["Author"]
__license__ = _meta["License"]
__version__ = _meta["Version"]


del annotations, _sys, TYPE_CHECKING, _metadata, _meta  # not for export


def set_agent(new_agent: str, *, _force: Literal[False] = False) -> str:
    """
    Sets sans' User-Agent header.

    Parameters
    ----------
    agent: str
        The User-Agent header to use.
        Your nation name and a method of contact, like an email address, are recommended.
        Some script info will be appended automatically.
    _force: bool
        Forcibly override the User-Agent header even after it's already been set.
        Not recommended: https://www.nationstates.net/pages/api.html#terms

    Returns
    -------
    The actual newly set agent, including attached additional script information.
    """

    if RateLimiter._agent and not _force:
        raise RuntimeError("Agent cannot be re-set")
    if not new_agent:
        RateLimiter._agent = ""
    else:
        import sys

        import httpx

        RateLimiter._agent = (
            f"{new_agent} Python/{sys.version_info[0]}.{sys.version_info[1]} "
            f"httpx/{httpx.__version__} sans/{__version__}"
        )
    return RateLimiter._agent


def deferred() -> float | None:
    """
    Returns when the internal ratelimiting lock is scheduled to be
    released in seconds from now, or None if the lock isn't deferred.

    Note that this is only the *schedule* - the value could be
    0.0 or even negative if the deferring thread falls behind.
    """
    return RateLimiter._lock.deferred


def locked() -> bool:
    """
    Returns when the internal ratelimiting lock is locked.
    """
    return RateLimiter._lock.locked()


for obj in list(globals().values()):
    if getattr(obj, "__module__", "").startswith(__name__):
        obj.__module__ = __name__
del obj  # type: ignore
