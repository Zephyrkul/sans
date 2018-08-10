import asyncio
from functools import wraps
from time import sleep
from concurrent.futures import ThreadPoolExecutor


pool = ThreadPoolExecutor(max_workers=5)


def asink(ratelimit, semaphore):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await asyncio.wrap_future(pool.submit(semaphore.acquire))
            try:
                return await func(*args, **kwargs)
            finally:
                pool.submit(sleep, ratelimit.seconds).add_done_callback(semaphore.release)
        return wrapper
    return decorator
