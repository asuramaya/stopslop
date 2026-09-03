```python
import random
import time
from functools import wraps


def with_retries(max_attempts=3, base_delay=1.0, exceptions=(Exception,)):
    """Retry the decorated function on exception, with exponential backoff and jitter."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    delay = random.uniform(0, delay)
                    time.sleep(delay)
        return wrapper
    return decorator


if __name__ == "__main__":
    calls = {"count": 0}

    @with_retries(max_attempts=4, base_delay=0.5)
    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionError(f"attempt {calls['count']} failed")
        return "ok"

    print(flaky())
    print(calls["count"])
```
