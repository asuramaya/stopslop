```python
import time
from threading import Condition


class TokenBucketRateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.condition = Condition()
    
    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        refilled = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + refilled)
        self.last_refill = now
    
    def try_acquire(self, tokens=1):
        """Attempt to acquire tokens. Returns True if successful."""
        with self.condition:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens=1, timeout=None):
        """
        Acquire tokens, blocking until available or timeout.
        Returns True if acquired, False if timeout expired.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        
        with self.condition:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self.condition.wait(timeout=min(remaining, 0.1))
                else:
                    self.condition.wait(timeout=0.1)
```
