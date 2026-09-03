```python
import time
import threading


class TokenBucketRateLimiter:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be positive")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_acquire(self, tokens: float = 1) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def acquire(self, tokens: float = 1, timeout: float = None) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens must not exceed capacity")
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                shortfall = tokens - self.tokens
                wait_time = shortfall / self.refill_rate
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_time = min(wait_time, remaining)
                self._condition.wait(wait_time)

    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self.tokens
```

`_refill` already uses `time.monotonic()`, not `time.time()`. `time.monotonic()` cannot go backward or jump under load, adjtime, or NTP correction, so there is no drift to fix here; switching to `time.time()` would introduce the exact bug you are describing.
