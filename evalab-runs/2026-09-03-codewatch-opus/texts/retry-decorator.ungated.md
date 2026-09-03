```python
import functools
import itertools
import logging
import random
import time

logger = logging.getLogger(__name__)

# Control-flow signals that must never be swallowed by a retry loop: a Ctrl-C
# or an interpreter shutdown means "stop now", not "the call failed".
NEVER_RETRY = (KeyboardInterrupt, SystemExit, GeneratorExit)


def with_retries(
    attempts=3,
    exceptions=Exception,
    delay=0.5,
    backoff=2.0,
    max_delay=30.0,
    jitter=0.5,
    never_retry=NEVER_RETRY,
):
    """Decorate a function so it is re-run when it raises, with exponential backoff.

    attempts    -- total number of calls, including the first one (must be >= 1)
    exceptions  -- exception type or tuple of types that trigger a retry
    delay       -- seconds to wait before the second attempt
    backoff     -- multiplier applied to the delay after each failure
    max_delay   -- ceiling on any single sleep
    jitter      -- fraction of randomness around each sleep, in [0, 1]. Each wait
                   is scaled by uniform(1 - jitter, 1 + jitter) so that clients
                   which failed together do not all retry at the same instant.
    never_retry -- types that always propagate immediately, checked before
                   `exceptions`, so passing exceptions=BaseException still lets
                   Ctrl-C and interpreter shutdown through.

    The exception from the final attempt propagates unchanged.

    Example:
        @with_retries(attempts=5, exceptions=(IOError, TimeoutError), delay=1)
        def fetch(url):
            ...
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError("jitter must be between 0 and 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in itertools.count(1):
                try:
                    return func(*args, **kwargs)
                except never_retry:
                    raise
                except exceptions:
                    if attempt >= attempts:
                        raise
                    sleep_for = min(wait, max_delay)
                    if jitter:
                        sleep_for *= random.uniform(1 - jitter, 1 + jitter)
                    logger.warning(
                        "%s failed (attempt %d/%d), retrying in %.2fs",
                        func.__name__, attempt, attempts, sleep_for,
                        exc_info=True,
                    )
                    time.sleep(sleep_for)
                    wait *= backoff

        return wrapper

    return decorator
```

Usage: `@with_retries(attempts=5, exceptions=(IOError, TimeoutError), delay=1)`. Nominal waits are 1s, 2s, 4s, 8s (capped at `max_delay`), each drawn from a ±50% window, so callers that failed together fan out instead of retrying in lockstep. Pass `jitter=0` for deterministic timing in tests.

The `except never_retry: raise` clause still sits first, so it wins even when `exceptions` is broad, and the cap still applies before jitter — a jittered sleep can exceed `max_delay` by up to `jitter`.

If the old name is already imported elsewhere, `retry = with_retries` keeps those call sites working during the transition.
