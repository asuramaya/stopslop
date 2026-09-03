```python
import logging
import random
import time
from functools import wraps

log = logging.getLogger(__name__)

NEVER_RETRIED = (KeyboardInterrupt, SystemExit)


def with_retries(attempts=3, base_delay=0.5, backoff=2.0, max_delay=30.0, jitter=0.5,
                 exceptions=(Exception,)):
    """Re-run the wrapped function when it raises, with exponential backoff.

    The delay before attempt n is base_delay * backoff ** (n - 1), capped at
    max_delay, then multiplied by a random factor drawn uniformly from
    [1 - jitter, 1 + jitter] so concurrent callers spread out instead of
    retrying in lockstep. Set jitter to 0 for deterministic delays. The
    exception from the final attempt propagates to the caller.

    KeyboardInterrupt and SystemExit always propagate on the first raise, even
    if `exceptions` is wide enough to cover them: a Ctrl-C must interrupt, and
    a requested exit must exit.

    Usage:

        @with_retries(attempts=5, exceptions=(ConnectionError,))
        def fetch(url):
            ...
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError("jitter must be between 0.0 and 1.0")

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NEVER_RETRIED:
                    raise
                except exceptions as exc:
                    if attempt == attempts:
                        log.warning(
                            "%s failed on final attempt %d/%d: %s",
                            func.__name__, attempt, attempts, exc,
                        )
                        raise
                    sleep_for = delay * random.uniform(1.0 - jitter, 1.0 + jitter)
                    log.info(
                        "%s failed on attempt %d/%d (%s); retrying in %.2fs",
                        func.__name__, attempt, attempts, exc, sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay = min(delay * backoff, max_delay)

        return wrapper

    return decorate
```
