```python
import threading
import time


class TokenBucket:
    """Rate limiter that refills tokens at a steady rate up to a fixed ceiling.

    Callers spend tokens with try_acquire; when the bucket is empty the call
    fails rather than blocking, so the caller decides whether to drop, queue,
    or retry.
    """

    def __init__(self, capacity, refill_per_second, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_second <= 0:
            raise ValueError("refill_per_second must be positive")

        self.capacity = float(capacity)
        self.refill_per_second = float(refill_per_second)
        self._clock = clock
        self._tokens = float(capacity)
        self._last_refill = clock()
        self._lock = threading.Lock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(
                self.capacity, self._tokens + elapsed * self.refill_per_second
            )
            self._last_refill = now

    def try_acquire(self, tokens=1):
        """Spend tokens if the bucket holds enough. Returns True on success."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def time_until_available(self, tokens=1):
        """Seconds until the bucket holds `tokens`. Zero if it already does."""
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self.refill_per_second)

    @property
    def tokens(self):
        with self._lock:
            self._refill()
            return self._tokens
```
