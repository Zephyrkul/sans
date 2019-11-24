import asyncio
import contextlib
from lxml import etree
from threading import Thread
from typing import Optional


def pretty_string(element_or_tree: etree.ElementBase) -> str:
    """
    Returns the base XML as a formatted and indented string.
    """
    return etree.tostring(element_or_tree, encoding=str, pretty_print=True)


_get_running_loop = getattr(
    asyncio,
    "get_running_loop",
    getattr(asyncio, "_get_running_loop", asyncio.get_event_loop),
)


def get_running_loop() -> Optional[asyncio.AbstractEventLoop]:
    """
    Gets the running event loop without creating a new one.

    Backport of :func:`asyncio.get_running_loop` which doesn't raise.
    """
    with contextlib.suppress(RuntimeError):
        return _get_running_loop()
    return None


def run_in_thread() -> None:
    """
    Runs the API event loop in its own thread.

    Required in order to make synchronous requests.
    """
    from .api import Api

    if Api._loop:
        raise RuntimeError("API event loop is already set.")

    def run(loop):
        try:
            loop.run_forever()
        finally:
            asyncio.gather(
                *asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True
            ).cancel()
            loop.run_until_complete(Api.session.close())
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    loop = asyncio.new_event_loop()
    Api.loop = loop
    Thread(target=run, args=(loop,), name="NS API Event Loop", daemon=True).start()
