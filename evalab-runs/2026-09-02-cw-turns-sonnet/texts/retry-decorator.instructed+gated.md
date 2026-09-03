```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def with_retries(max_attempts=3, base_delay=1.0, backoff_factor=2.0, jitter=0.5, exceptions=(Exception,)):
    """Retry a function on exception, with exponential backoff plus jitter, until max_attempts is reached."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    sleep_for = delay + random.uniform(0, jitter * delay)
                    logger.warning(
                        "%s failed on attempt %d/%d: %s. Retrying in %.1fs.",
                        func.__name__,
                        attempt,
                        max_attempts,
                        exc,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay *= backoff_factor
            raise last_exc

        return wrapper

    return decorator
```
