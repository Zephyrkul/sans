from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal

from .lock import ResetLock

__all__ = []
lock = ResetLock()
agent: str = ""


def set_agent(new_agent: str, *, _force: Literal[False] = False) -> None:
    """
    Sets sans' User-Agent header.

    Parameters
    ----------
    agent: str
        The User-Agent header to use.
        Your nation name and a method of contact, like an email address, are recommended.
    _force: bool
        Forcibly override the User-Agent header even after it's already been set.
        Not recommended: https://www.nationstates.net/pages/api.html#terms
    """
    global agent
    if agent and not _force:
        raise RuntimeError("Agent cannot be re-set")
    agent = new_agent
