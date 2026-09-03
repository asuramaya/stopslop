import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def retry(attempts=3, delay=1.0, backoff=2.0, max_delay=None, jitter=False,
          exceptions=(Exception,)):
    """Re-run a function when it raises, with exponential backoff.

    The wrapped function is called up to `attempts` times. After a failed
    call the wrapper sleeps `delay` seconds, then multiplies the delay by
    `backoff` before the next wait. The exception from the final attempt
    propagates to the caller.

    Args:
        attempts: Total number of calls, including the first. Must be >= 1.
        delay: Seconds to wait after the first failure.
        backoff: Multiplier applied to the delay after each failure.
        max_delay: Upper bound on a single wait, or None for no bound.
        jitter: If true, each wait is scaled by a random factor in [0.5, 1.0]
            so that concurrent callers do not retry in lockstep.
        exceptions: Exception type or tuple of types that trigger a retry.
            Anything else propagates immediately.

    Returns:
        A decorator that wraps the target function.

    Raises:
        ValueError: If `attempts` is less than 1.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == attempts:
                        raise
                    sleep_for = wait
                    if max_delay is not None:
                        sleep_for = min(sleep_for, max_delay)
                    if jitter:
                        sleep_for *= random.uniform(0.5, 1.0)
                    logger.warning(
                        "%s failed on attempt %d/%d, retrying in %.2fs",
                        func.__name__, attempt, attempts, sleep_for,
                        exc_info=True,
                    )
                    time.sleep(sleep_for)
                    wait *= backoff
        return wrapper
    return decorator
