```python
import functools
import logging
import time

log = logging.getLogger(__name__)


def retry(attempts=3, base_delay=0.5, backoff=2.0, exceptions=(Exception,)):
    """Re-run the wrapped function when it raises, with exponential backoff.

    The function is called up to `attempts` times. After a failed call the
    wrapper sleeps `base_delay * backoff ** (n - 1)` seconds, where n is the
    number of calls made so far, then tries again. If the last attempt also
    raises, that exception propagates unchanged.

    Args:
        attempts: Total number of calls to make. Must be at least 1.
        base_delay: Seconds to wait after the first failure.
        backoff: Multiplier applied to the delay after each failure.
        exceptions: Exception types that count as a retryable failure.
            Anything else propagates immediately.

    Raises:
        ValueError: If attempts is less than 1.
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
                    log.warning(
                        "%s failed on attempt %d/%d, retrying in %.2fs",
                        func.__name__, attempt, attempts, delay,
                        exc_info=True,
                    )
                    time.sleep(delay)
                    delay *= backoff

        return wrapper

    return decorate
```
