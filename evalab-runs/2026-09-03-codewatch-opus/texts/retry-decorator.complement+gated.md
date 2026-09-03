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
    """Wrap a function so it is re-run when it raises, with exponential backoff.

    The delay before try N is base_delay * factor ** (N - 2), clamped to
    max_delay. With jitter on, each delay is scaled by a random factor in
    [0.5, 1.0) so that concurrent callers do not retry in lockstep.

    KeyboardInterrupt and SystemExit always propagate immediately: they signal
    that the process is going away, not that the call failed.

    Raises the exception from the final attempt if every attempt fails.
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
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions:
                    if attempt == attempts:
                        raise
                    wait = min(delay, max_delay)
                    if jitter:
                        wait *= 0.5 + random.random() * 0.5
                    logger.warning(
                        "%s failed on attempt %d/%d, retrying in %.2fs",
                        func.__name__,
                        attempt,
                        attempts,
                        wait,
                        exc_info=True,
                    )
                    time.sleep(wait)
                    delay *= factor

        return wrapper

    return decorate
```
