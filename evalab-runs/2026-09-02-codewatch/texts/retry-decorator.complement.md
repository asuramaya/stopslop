```python
import functools
import random
import time


def retry(attempts=3, base_delay=0.5, backoff=2.0, jitter=0.0, exceptions=(Exception,)):
    """Re-run a function when it raises, with exponential backoff between tries.

    The wrapped function is called up to `attempts` times. After a failed
    call number n (1-indexed), the wrapper sleeps for
    `base_delay * backoff ** (n - 1)` seconds, plus a random amount in
    [0, jitter) if jitter is set, then tries again. If the last attempt
    also raises, that exception propagates to the caller unchanged.

    Only exceptions listed in `exceptions` trigger a retry; anything else
    propagates immediately, so a programming error is not mistaken for a
    transient failure.

    Args:
        attempts: Total number of calls to make. Must be at least 1.
        base_delay: Seconds to sleep after the first failure.
        backoff: Multiplier applied to the delay after each failure.
        jitter: Upper bound on a random extra delay, to spread out
            clients that failed at the same moment.
        exceptions: Exception type or tuple of types that count as
            retryable.

    Raises:
        ValueError: If attempts is less than 1.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be >= 1, got {attempts}")

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
                    time.sleep(delay + random.uniform(0, jitter))
                    delay *= backoff

        return wrapper

    return decorate
```
