"""A thread-safe token-bucket rate limiter."""

import threading
import time


class TokenBucket:
    """Allows up to `rate` operations per second, with bursts up to `capacity`.

    Tokens refill continuously rather than on a fixed tick, so a caller that
    waits 0.5s at rate=10 gets 5 tokens back, not 0.
    """

    def __init__(self, rate, capacity=None, clock=time.monotonic):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity is None:
            capacity = rate
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._clock = clock
        self._tokens = float(capacity)
        self._updated = clock()
        self._lock = threading.Lock()

    def _refill(self):
        """Credit the tokens earned since the last update. Call under the lock."""
        now = self._clock()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._updated = now

    def try_acquire(self, tokens=1):
        """Take `tokens` from the bucket. Return True if they were available."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")
        with self._lock:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            return True

    def wait_time(self, tokens=1):
        """Return the seconds until `tokens` are available, 0.0 if they are now."""
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self.rate)

    @property
    def tokens(self):
        """The current token count, refilled as of this call."""
        with self._lock:
            self._refill()
            return self._tokens

    def __repr__(self):
        return f"TokenBucket(rate={self.rate}, capacity={self.capacity})"
