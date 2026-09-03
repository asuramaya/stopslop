```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def retry(attempts=3, base_delay=0.5, backoff=2.0, jitter=0.1, exceptions=Exception):
    """Re-run the wrapped function when it raises, backing off between tries.

    The first retry waits `base_delay` seconds; each later one multiplies that
    wait by `backoff`, so the delays go 0.5s, 1s, 2s with the defaults. A random
    amount up to `jitter` seconds is added to every wait, which keeps a group of
    callers that failed at the same moment from retrying in lockstep.

    Args:
        attempts: Total calls to make, including the first. Must be at least 1.
        base_delay: Seconds to wait before the second call.
        backoff: Multiplier applied to the delay after each failure.
        jitter: Upper bound on the random padding added to each wait.
        exceptions: Exception type, or tuple of types, that triggers a retry.
            Anything else propagates immediately.

    Returns:
        A decorator that preserves the wrapped function's name and docstring.

    Raises:
        Whatever the wrapped function raised on its final attempt.
        ValueError: If `attempts` is less than 1.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")

    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == attempts:
                        raise
                    wait = delay + random.uniform(0, jitter)
                    logger.warning(
                        "%s failed on attempt %d/%d, retrying in %.2fs",
                        func.__name__, attempt, attempts, wait, exc_info=True,
                    )
                    time.sleep(wait)
                    delay *= backoff

        return wrapper

    return decorate
```
