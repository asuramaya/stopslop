```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def with_retries(
    max_attempts=3,
    base_delay=0.5,
    backoff_factor=2.0,
    max_delay=30.0,
    jitter=True,
    exceptions=(Exception,),
):
    """Decorate a function so it is re-run when it raises, with exponential backoff.

    The delay before try N is base_delay * backoff_factor ** (N - 1), capped at
    max_delay. With jitter on, each delay is scaled by a random factor in
    [0.5, 1.0) so concurrent callers don't retry in lockstep. The exception from
    the final attempt propagates.

    KeyboardInterrupt and SystemExit are never retried: they signal that the
    process is being torn down, not that the call failed. They inherit from
    BaseException, so a default `exceptions` of (Exception,) already excludes
    them, but they are re-raised explicitly in case a caller passes a wider
    tuple such as (BaseException,).
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.warning(
                            "%s failed after %d attempts: %s",
                            func.__name__, attempt, exc,
                        )
                        raise
                    sleep_for = min(delay, max_delay)
                    if jitter:
                        sleep_for *= random.uniform(0.5, 1.0)
                    logger.info(
                        "%s attempt %d/%d failed (%s); retrying in %.2fs",
                        func.__name__, attempt, max_attempts, exc, sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay *= backoff_factor

        return wrapper

    return decorate
```
