```python
import functools
import random
import time


def retry(attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,), jitter=0.0):
    """Re-run the wrapped function when it raises, with exponential backoff.

    The function is called up to `attempts` times. After a failed call the
    wrapper sleeps, then tries again; each sleep is the previous one times
    `backoff`. If the last attempt also raises, that exception propagates.

    Args:
        attempts: Total number of calls, including the first one. Must be >= 1.
        delay: Seconds to sleep after the first failure.
        backoff: Multiplier applied to the delay after each failure.
        exceptions: Exception type or tuple of types that trigger a retry.
            Anything else propagates immediately.
        jitter: Upper bound of a random extra sleep, in seconds, added to each
            wait to spread out retries from concurrent callers.

    Returns:
        A decorator that wraps a callable with the retry behaviour.

    Raises:
        ValueError: If `attempts` is less than 1.

    Example:
        @retry(attempts=5, delay=0.5, exceptions=(ConnectionError,))
        def fetch(url):
            ...
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for remaining in range(attempts - 1, -1, -1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if remaining == 0:
                        raise
                    time.sleep(wait + random.uniform(0, jitter))
                    wait *= backoff
        return wrapper
    return decorator
```

A few things worth knowing:

- `exceptions` defaults to `Exception`, not `BaseException`, so `KeyboardInterrupt` and `SystemExit` still interrupt the loop.
- The loop counts down `remaining`, so the final attempt re-raises the original exception with its traceback intact rather than wrapping it.
- `jitter` defaults to 0, which keeps the timing deterministic for tests; set it when several clients retry against the same service.
