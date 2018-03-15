import six
import sys
from abc import ABCMeta
from collections import namedtuple
from threading import BoundedSemaphore, Lock
from .sink import sink
try:
    import asyncio
    from .asink import asink
except ImportError:
    asyncio = None


__all__ = ["ratelimit", "ratelimited"]


BRL = namedtuple("BaseRateLimit", ("requests", "seconds"))


ratelimit = namedtuple("RateLimits", (
    "api", "telegram", "recruitment"
))(
    BRL(50, 30), BRL(1, 30), BRL(1, 180)
)


semaphores = namedtuple("Semaphores", ratelimit._fields)(*(
    BoundedSemaphore(brl.requests) for brl in ratelimit
))


def ratelimited(func):
    if asyncio and asyncio.iscoroutine(func):
        return asink(ratelimit, semaphores)(func)
    return sink(ratelimit, semaphores)(func)
