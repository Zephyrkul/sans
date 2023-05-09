from __future__ import annotations

import sys
import types
from functools import partial
from typing import Callable

import httpx

from .lock import ResetLock

__all__ = []
lock = ResetLock()
agent: str
set_agent: Callable[[str], None]


class _State(types.ModuleType):
    # write-once, read-any property
    @partial(property, None)
    def agent(self, value: str):
        from . import __version__

        assert value and isinstance(value, str)
        value = (
            f"{value} Python/{sys.version_info[0]}.{sys.version_info[1]}"
            f" httpx/{httpx.__version__} sans/{__version__}"
        )
        type(self).agent = property(lambda _: value)

    def set_agent(self, value: str) -> None:
        self.agent = value


sys.modules[__name__].__class__ = _State
