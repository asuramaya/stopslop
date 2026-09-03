```python
import threading
import time


class TokenBucket:
    """Token-bucket rate limiter safe for use from multiple threads.

    The bucket holds up to `capacity` tokens and regains `refill_rate`
    tokens per second. A caller takes tokens with `try_acquire`, which
    never blocks: it either takes the tokens or reports failure.
    """

    def __init__(self, capacity, refill_rate, clock=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._clock = clock or time.monotonic
        self._tokens = float(capacity)
        self._updated_at = self._clock()
        self._lock = threading.Lock()

    def _refill(self):
        """Caller must hold the lock."""
        now = self._clock()
        elapsed = now - self._updated_at
        if elapsed > 0:
            self._tokens = min(
                self._capacity, self._tokens + elapsed * self._refill_rate
            )
            self._updated_at = now

    def try_acquire(self, tokens=1):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self._capacity:
            raise ValueError("tokens exceeds bucket capacity; request can never succeed")

        with self._lock:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            return True

    def wait_time(self, tokens=1):
        """Seconds until `tokens` are available. Zero means available now."""
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self._refill_rate)

    @property
    def tokens(self):
        with self._lock:
            self._refill()
            return self._tokens
```
