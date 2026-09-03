```python
import time
import threading


class TokenBucketRateLimiter:
    def __init__(self, capacity, refill_rate):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def _refill_locked(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_acquire(self, tokens=1):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self.lock:
            self._refill_locked()
            if tokens > self.tokens:
                return False
            self.tokens -= tokens
            return True

    def acquire(self, tokens=1, timeout=None):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens cannot exceed capacity")
        deadline = None if timeout is None else time.monotonic() + timeout
        with self.condition:
            while True:
                self._refill_locked()
                if tokens <= self.tokens:
                    self.tokens -= tokens
                    return True
                shortfall = tokens - self.tokens
                wait_for = shortfall / self.refill_rate
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_for = min(wait_for, remaining)
                self.condition.wait(timeout=wait_for)

    def available_tokens(self):
        with self.lock:
            self._refill_locked()
            return self.tokens
```
