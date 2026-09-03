```python
import time
from threading import Lock


class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

    def try_acquire(self, tokens=1):
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def acquire(self, tokens=1, timeout=None):
        start = time.monotonic()
        while True:
            if self.try_acquire(tokens):
                return True
            if timeout and time.monotonic() - start > timeout:
                return False
            time.sleep(0.001)

    def get_tokens(self):
        with self.lock:
            self._refill()
            return self.tokens

    def reset(self):
        with self.lock:
            self.tokens = self.capacity
            self.last_refill = time.monotonic()
```
