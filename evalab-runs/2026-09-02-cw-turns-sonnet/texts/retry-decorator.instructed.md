```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def with_retries(max_attempts=3, base_delay=1.0, max_delay=60.0, exceptions=(Exception,)):
    """Re-run the decorated function on exception, with a maximum attempt
    count and jittered exponential backoff between attempts."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    if attempt >= max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, attempt, exc,
                        )
                        raise
                    delay = min(base_delay * 2 ** (attempt - 1), max_delay)
                    delay = random.uniform(0, delay)
                    logger.warning(
                        "%s failed on attempt %d/%d (%s), retrying in %.2fs",
                        func.__name__, attempt, max_attempts, exc, delay,
                    )
                    time.sleep(delay)
        return wrapper
    return decorator
```
