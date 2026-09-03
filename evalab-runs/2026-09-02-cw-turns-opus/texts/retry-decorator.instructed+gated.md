```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)

NEVER_RETRIED = (KeyboardInterrupt, SystemExit)


def with_retries(
    attempts=3,
    base_delay=0.5,
    max_delay=30.0,
    multiplier=2.0,
    jitter=0.5,
    exceptions=(Exception,),
):
    """Re-run the wrapped function when it raises, backing off between tries.

    Waits base_delay after the first failure and multiplies the wait by
    `multiplier` after each subsequent one, capped at max_delay. The final
    failure is re-raised rather than swallowed.

    `jitter` is the fraction of each wait that is randomised: 0 sleeps the
    full backoff every time, 1 picks uniformly from (0, backoff]. The default
    of 0.5 keeps half the wait fixed so a retry never fires immediately, and
    spreads the other half so callers that failed together do not come back
    together.

    KeyboardInterrupt and SystemExit propagate immediately even if `exceptions`
    would match them, so a Ctrl-C or a shutdown is never turned into a sleep.

    Usage::

        @with_retries(attempts=5, exceptions=(ConnectionError,))
        def fetch_quote(symbol):
            ...
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError("jitter must be between 0 and 1")

    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NEVER_RETRIED:
                    raise
                except exceptions as exc:
                    if attempt == attempts:
                        logger.warning(
                            "%s failed after %d attempts", func.__name__, attempts
                        )
                        raise
                    wait = delay * (1.0 - jitter) + random.uniform(0.0, delay * jitter)
                    logger.info(
                        "%s raised %r on attempt %d/%d; retrying in %.2fs",
                        func.__name__,
                        exc,
                        attempt,
                        attempts,
                        wait,
                    )
                    time.sleep(wait)
                    delay = min(delay * multiplier, max_delay)

        return wrapper

    return decorate
```
