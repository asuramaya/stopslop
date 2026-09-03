import functools
import random
import time


def retry(attempts=3, delay=1.0, backoff=2.0, max_delay=60.0, jitter=0.1,
          exceptions=(Exception,)):
    """Re-run a function when it raises, waiting longer after each failure.

        @retry(attempts=5, delay=0.5, exceptions=(ConnectionError,))
        def fetch(url):
            ...

    The function runs up to `attempts` times. After a failed call the
    wrapper sleeps `delay`, then multiplies that wait by `backoff` for the
    next round, up to `max_delay`. Each sleep is scaled by a random factor
    in [1 - jitter, 1 + jitter], so several clients that fail at the same
    moment do not retry in lockstep. The exception from the last attempt
    reaches the caller.

    KeyboardInterrupt and SystemExit always propagate, even when
    `exceptions` is broad enough to match them.

    Raises:
        ValueError: If `attempts` is less than 1, or `jitter` is outside
            the range 0 to 1.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError("jitter must be between 0 and 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions:
                    if attempt == attempts:
                        raise
                    capped = min(wait, max_delay)
                    time.sleep(capped * random.uniform(1.0 - jitter, 1.0 + jitter))
                    wait *= backoff
        return wrapper
    return decorator
