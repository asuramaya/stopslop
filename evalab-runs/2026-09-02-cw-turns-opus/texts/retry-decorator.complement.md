```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)

NO_RETRY = (KeyboardInterrupt, SystemExit)


def with_retries(attempts=3, delay=0.5, backoff=2.0, jitter=0.25, exceptions=(Exception,)):
    """Decorate a function so it is re-run on exception, with exponential backoff.

    Returns a decorator. The wrapped function is called up to `attempts` times;
    the first call that returns normally wins. A call is retried only if it
    raises something in `exceptions`; anything else propagates immediately.

    The base delay after failure n is delay * backoff ** n. Each sleep is drawn
    uniformly from +/- `jitter` of that base (jitter=0.25 means +/-25%), so
    callers that fail at the same instant spread out instead of retrying in
    lockstep and hammering a recovering service. The last attempt's exception
    propagates unchanged.

    KeyboardInterrupt and SystemExit always propagate on the first attempt, even
    if `exceptions` is widened to BaseException: a Ctrl-C or an interpreter
    shutdown is an instruction to stop, not a failure to paper over.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if not 0.0 <= jitter < 1.0:
        raise ValueError("jitter must be in [0.0, 1.0)")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NO_RETRY:
                    raise
                except exceptions as exc:
                    if attempt == attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            attempts,
                            exc,
                        )
                        raise
                    sleep_for = wait * random.uniform(1.0 - jitter, 1.0 + jitter)
                    logger.warning(
                        "%s attempt %d/%d failed (%s); retrying in %.2fs",
                        func.__name__,
                        attempt,
                        attempts,
                        exc,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    wait *= backoff

        return wrapper

    return decorator
```

Call sites change from `@retry(...)` to `@with_retries(...)`; the signature and behaviour are unchanged. If the old name is public API, `retry = with_retries` alongside the definition keeps it working, though that leaves both names in the namespace to be cleaned up later.
