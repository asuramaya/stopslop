```python
import threading
import time


class TokenBucket:
    """Token bucket rate limiter safe for use from multiple threads.

    Tokens refill continuously at `refill_rate` per second up to `capacity`.
    A caller that finds too few tokens is rejected rather than blocked.
    """

    def __init__(self, capacity, refill_rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._clock = clock
        self._tokens = float(capacity)
        self._last_refill = clock()
        self._lock = threading.Lock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

    def try_acquire(self, tokens=1):
        """Take `tokens` from the bucket. Returns False if not enough are available."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity; request can never succeed")

        with self._lock:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            return True

    def time_until_available(self, tokens=1):
        """Seconds until `tokens` can be acquired, assuming no competing callers."""
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self.refill_rate)

    @property
    def available(self):
        with self._lock:
            self._refill()
            return self._tokens
```
