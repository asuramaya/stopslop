```python
import functools
import logging
import random
import time

logger = logging.getLogger(__name__)


def with_retries(
    attempts=3,
    initial_delay=0.5,
    backoff=2.0,
    max_delay=30.0,
    jitter=0.5,
    exceptions=(Exception,),
):
    """Re-run the wrapped function on failure with jittered exponential backoff.

    The nominal delay before retry n is initial_delay * backoff ** (n - 1),
    capped at max_delay. `jitter` is the fraction of that delay left to chance:
    0.0 sleeps the full nominal delay, 1.0 draws uniformly from [0, delay), and
    the default 0.5 keeps half as a floor and randomises the rest. Randomising
    spreads out callers that failed on the same downstream outage, so they do
    not all retry in lockstep and re-create the thundering herd.

    KeyboardInterrupt and SystemExit are never retried even when `exceptions`
    would cover them: they signal that the process is being torn down, not that
    the call failed, and sleeping through a Ctrl-C makes the program feel hung.
    They derive from BaseException, so a default of (Exception,) already misses
    them, but callers passing BaseException get the same guarantee. The
    exception from the final attempt propagates.

    Usage:

        @with_retries(attempts=5, exceptions=(ConnectionError,))
        def fetch_manifest(url):
            ...
    """
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError(f"jitter must be between 0.0 and 1.0, got {jitter}")

    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    if attempt == attempts:
                        logger.warning(
                            "%s failed after %d attempts", func.__name__, attempts
                        )
                        raise
                    nominal = min(delay, max_delay)
                    sleep_for = nominal * (1.0 - jitter) + random.uniform(
                        0.0, nominal * jitter
                    )
                    logger.info(
                        "%s raised %r on attempt %d/%d; retrying in %.2fs",
                        func.__name__,
                        exc,
                        attempt,
                        attempts,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay *= backoff

        return wrapper

    return decorate
```
