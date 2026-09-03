```python
import time
import threading


class TokenBucketRateLimiter:
    """Limits throughput to a steady rate with short bursts allowed."""

    def __init__(self, rate: float, capacity: float):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def try_acquire(self, tokens: float = 1) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                self._cond.notify_all()
                return True
            return False

    def acquire(self, tokens: float = 1, timeout: float = None) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens cannot exceed bucket capacity")
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._cond.notify_all()
                    return True
                shortfall = tokens - self._tokens
                wait_for = shortfall / self.rate
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_for = min(wait_for, remaining)
                self._cond.wait(wait_for)

    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
```

The code already uses `time.monotonic()`, not `time.time()`, in every timing call (`_refill`, `acquire`'s deadline and remaining-time checks). `time.monotonic()` is immune to wall-clock adjustments (NTP sync, DST, manual clock changes) that cause `time.time()` to jump backward or forward, so there's no drift source here to fix.
