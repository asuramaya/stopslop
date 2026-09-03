```python
import asyncio
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)

#: Never retried, even if the caller's `exceptions` would match them. These
#: signal "stop what you are doing", not "the operation failed" — swallowing
#: one turns Ctrl-C into a several-second hang, or an interpreter shutdown /
#: task cancellation into a silent retry storm.
NEVER_RETRY = (KeyboardInterrupt, SystemExit, GeneratorExit, asyncio.CancelledError)


def with_retries(
    attempts=3,
    exceptions=Exception,
    delay=0.5,
    backoff=2.0,
    max_delay=30.0,
    jitter=0.25,
):
    """Decorate a function so it is re-run when it raises, with exponential backoff.

    attempts:   total number of calls, including the first one (must be >= 1)
    exceptions: exception type or tuple of types that trigger another attempt
    delay:      base seconds to wait before the second attempt
    backoff:    multiplier applied to the base delay after each failure
    max_delay:  ceiling on the base delay before jitter is applied
    jitter:     fraction of the wait to randomise, in [0, 1]. Each wait is
                drawn uniformly from [w * (1 - jitter), w * (1 + jitter)], so
                many clients failing on the same outage do not retry in
                lockstep and re-hammer the service.

    Anything in NEVER_RETRY propagates immediately, as does the exception from
    the final attempt.

        @with_retries(attempts=5, exceptions=(ConnectionError, TimeoutError))
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
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NEVER_RETRY:
                    raise
                except exceptions:
                    if attempt == attempts:
                        raise
                    sleep_for = wait * random.uniform(1 - jitter, 1 + jitter)
                    logger.warning(
                        "%s failed on attempt %d/%d, retrying in %.2fs",
                        func.__name__, attempt, attempts, sleep_for,
                        exc_info=True,
                    )
                    time.sleep(sleep_for)
                    wait = min(wait * backoff, max_delay)

        return wrapper

    return decorator
```

Usage:

```python
@with_retries(attempts=5, exceptions=(ConnectionError, TimeoutError), delay=0.2, jitter=0.5)
def fetch(url):
    ...
```

The name appears in three places — the `def`, the docstring example, and the usage snippet — and all three now read `with_retries`; nothing else in the body referenced the old name, since the inner closures are `decorator` and `wrapper`. If you have existing call sites, `retry = with_retries` at module level keeps them working during a migration.
