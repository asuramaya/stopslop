import functools
import random
import time


def retry(max_attempts=3, base_delay=1.0, max_delay=30.0, exceptions=(Exception,), jitter=True):
    """Retry a function on exception with exponential backoff.

    Waits base_delay * 2**attempt seconds between attempts, capped at
    max_delay, with optional random jitter to avoid thundering herds.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise

                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)

                    time.sleep(delay)

        return wrapper

    return decorator
