```python
import time
from threading import Lock, Condition


class TokenBucket:
    """Rate limiter using the token bucket algorithm.
    
    Tokens are refilled at a constant rate. Requests that exceed
    available tokens are rejected. All operations are thread-safe.
    """

    def __init__(self, capacity, refill_rate):
        """Initialize the token bucket.
        
        Args:
            capacity: Maximum number of tokens the bucket can hold
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = Lock()
        self.condition = Condition(self.lock)

    def try_acquire(self, tokens=1):
        """Attempt to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire (default 1)
            
        Returns:
            True if sufficient tokens were available and acquired,
            False otherwise.
        """
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def acquire(self, tokens=1, timeout=None):
        """Block until tokens are available or timeout occurs.
        
        Args:
            tokens: Number of tokens to acquire (default 1)
            timeout: Maximum time to wait in seconds (None = wait indefinitely)
            
        Returns:
            True if tokens were acquired, False if timeout occurred.
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
                    self.condition.wait(timeout=min(remaining, 0.01))
                else:
                    self.condition.wait(timeout=0.01)

    def _refill(self):
        """Refill tokens based on elapsed time since last refill.
        
        Must be called while holding the lock.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_available_tokens(self):
        """Return the current number of available tokens."""
        with self.lock:
            self._refill()
            return self.tokens
```
