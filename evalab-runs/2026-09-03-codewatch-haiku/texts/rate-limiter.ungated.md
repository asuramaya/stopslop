```python
import time
import threading

class TokenBucketRateLimiter:
    """A thread-safe token bucket rate limiter with blocking acquire."""
    
    def __init__(self, capacity: float, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens the bucket can hold
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.monotonic()
        self._condition = threading.Condition()
    
    def try_acquire(self, tokens: float = 1) -> bool:
        """Try to acquire tokens without blocking."""
        with self._condition:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens: float = 1, timeout: float = None) -> bool:
        """
        Acquire tokens, blocking until available or timeout.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum seconds to wait (None for infinite)
        
        Returns:
            True if successful, False on timeout
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        
        with self._condition:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                
                if deadline is not None and time.monotonic() >= deadline:
                    return False
                
                wait_timeout = 0.1 if deadline is None else min(0.1, max(0, deadline - time.monotonic()))
                self._condition.wait(timeout=wait_timeout)
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_time = now
```
