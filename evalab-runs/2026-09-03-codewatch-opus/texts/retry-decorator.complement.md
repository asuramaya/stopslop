```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def with_retries(
    attempts=3,
    base_delay=0.5,
    factor=2.0,
    max_delay=30.0,
    jitter=True,
    exceptions=(Exception,),
):
    """Re-run the wrapped function on failure with exponential backoff.

    The delay before retry n (1-based) is base_delay * factor ** (n - 1),
    capped at max_delay. With jitter on, each delay is drawn uniformly from
    [0, capped_delay] so callers that failed together do not retry together.

    KeyboardInterrupt and SystemExit are never retried: they signal that the
    caller wants to stop, not that the call failed. Both derive from
    BaseException, so a custom `exceptions` tuple can only reintroduce them
    by naming them explicitly, which this guard still overrides.

    Raises the last exception once `attempts` calls have all failed.

    Usage:

        @with_retries(attempts=5, base_delay=0.2, exceptions=(IOError,))
        def fetch(url):
            ...
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    if attempt == attempts:
                        logger.warning(
                            "%s failed after %d attempts", func.__name__, attempts
                        )
                        raise
                    capped = min(delay, max_delay)
                    sleep_for = random.uniform(0, capped) if jitter else capped
                    logger.info(
                        "%s failed (attempt %d/%d): %s; retrying in %.2fs",
                        func.__name__,
                        attempt,
                        attempts,
                        exc,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay *= factor

        return wrapper

    return decorator
```
