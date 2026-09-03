```python
import time
import threading


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

    def try_acquire(self, tokens: float = 1) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._lock:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            self._cv.notify_all()
            return True

    def acquire(self, tokens: float = 1, timeout: float = None) -> bool:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._cv:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._cv.notify_all()
                    return True
                deficit = tokens - self._tokens
                wait_for = deficit / self._refill_rate
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_for = min(wait_for, remaining)
                self._cv.wait(timeout=wait_for)

    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens

    def wait_time(self, tokens: float = 1) -> float:
        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            if deficit <= 0:
                return 0.0
            return deficit / self._refill_rate
```
