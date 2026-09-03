```python
import time
import random
import functools


def with_retries(max_attempts=3, base_delay=1.0, exceptions=(Exception,)):
    """Retry the decorated function on exception, backing off exponentially with jitter.

    Stop after max_attempts tries and re-raise the last exception. Never
    intercept KeyboardInterrupt or SystemExit.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(random.uniform(0, delay))
                    delay *= 2
        return wrapper
    return decorator
```
