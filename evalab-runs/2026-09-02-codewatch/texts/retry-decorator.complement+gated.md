```python
import functools
import logging
import time

logger = logging.getLogger(__name__)


def retry(attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """Re-run a function when it raises, with exponential backoff.

    The wrapped function is called up to `attempts` times. After a failed
    call the wrapper sleeps `delay` seconds, then multiplies the wait by
    `backoff` before the next one, so with the defaults the pauses are
    1s, 2s, 4s, and so on. Only exceptions listed in `exceptions` trigger
    a retry; anything else propagates immediately, since retrying a
    TypeError or a KeyError just wastes wall-clock time.

    If the last attempt also fails, its exception is re-raised unchanged,
    so the caller sees the real traceback rather than a wrapper's.

    Args:
        attempts: Total number of calls, including the first. Must be >= 1.
        delay: Seconds to wait after the first failure.
        backoff: Multiplier applied to the delay after each failure.
        exceptions: Exception type or tuple of types that count as retryable.

    Raises:
        ValueError: If `attempts` is less than 1.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == attempts:
                        raise
                    logger.warning(
                        "%s failed on attempt %d/%d, retrying in %.1fs",
                        func.__name__, attempt, attempts, wait,
                        exc_info=True,
                    )
                    time.sleep(wait)
                    wait *= backoff

        return wrapper

    return decorator
```
