```python
import functools
import random
import time


class RetryError(Exception):
    """Raised when every attempt failed; the last failure is the __cause__."""


def with_retries(attempts=3, base_delay=0.1, factor=2.0, max_delay=30.0,
                 exceptions=(Exception,), jitter=True, sleep=time.sleep):
    """Re-run the wrapped function until it returns or the attempts run out.

    Without jitter, the delay before attempt n (1-indexed) is
    base_delay * factor ** (n - 1), capped at max_delay. With jitter, each
    delay is drawn uniformly from [base_delay, previous_delay * factor), so
    two callers that fail at the same instant diverge instead of retrying in
    lockstep on every attempt.

    KeyboardInterrupt and SystemExit always propagate, even if `exceptions`
    is wide enough to match them: a retry loop that swallows Ctrl-C or
    sys.exit() cannot be stopped.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        break
                    if jitter:
                        delay = random.uniform(base_delay, delay * factor)
                    else:
                        delay *= factor if attempt > 1 else 1.0
                    delay = min(delay, max_delay)
                    sleep(delay)
            raise RetryError(
                f"{func.__name__} failed after {attempts} attempts"
            ) from last_exc

        return wrapper

    return decorator
```
