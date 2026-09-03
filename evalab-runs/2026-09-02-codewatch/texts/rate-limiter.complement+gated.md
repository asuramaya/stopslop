```python
import threading
import time


class TokenBucket:
    """Token bucket rate limiter safe for use from multiple threads.

    Tokens refill continuously at `rate` per second up to `capacity`.
    A caller takes tokens with `try_acquire`, which never blocks.
    """

    def __init__(self, rate, capacity=None, clock=time.monotonic):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity is None:
            capacity = rate
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self._rate = float(rate)
        self._capacity = float(capacity)
        self._clock = clock
        self._tokens = float(capacity)
        self._updated = clock()
        self._lock = threading.Lock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._updated = now

    def try_acquire(self, tokens=1):
        """Take `tokens` from the bucket. Returns True on success."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self._capacity:
            raise ValueError("tokens exceeds bucket capacity; call would never succeed")

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def time_until(self, tokens=1):
        """Seconds until `tokens` are available, 0.0 if they are now."""
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self._rate)

    @property
    def tokens(self):
        with self._lock:
            self._refill()
            return self._tokens
```

The clock is injectable so tests can drive it forward without sleeping. `try_acquire` rejects a request larger than the capacity up front rather than letting the caller spin on a bucket that can never hold enough.
