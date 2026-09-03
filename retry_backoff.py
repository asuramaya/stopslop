import functools
import random
import time


def with_retries(max_attempts=3, base_delay=1.0, max_delay=30.0, exceptions=(Exception,), jitter=True):
    """Re-run the decorated function on exception, with exponential backoff between attempts."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as exc:
                    if attempt >= max_attempts:
                        raise

                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)

                    time.sleep(delay)

        return wrapper

    return decorator


if __name__ == "__main__":
    calls = {"count": 0}

    @with_retries(max_attempts=3, base_delay=0.1)
    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionError("temporary failure")
        return "ok"

    print(flaky(), calls["count"])
