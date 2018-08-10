import six
from threading import Timer


def sink(ratelimit, semaphore):
    def decorator(func):
        @six.wraps(func)
        def wrapper(*args, **kwargs):
            semaphore.acquire(True)
            try:
                return func(*args, **kwargs)
            finally:
                Timer(ratelimit.seconds, semaphore.release).start()
        return wrapper
    return decorator
