```python
import time
from threading import Lock


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        """
        Initialize a token bucket rate limiter.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = Lock()
    
    def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
        
        Returns:
            True if tokens were acquired, False otherwise
        """
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            # Try to acquire tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens: float = 1.0, timeout: float = None) -> bool:
        """
        Acquire tokens from the bucket, blocking until available or timeout.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum seconds to wait (None = infinite)
        
        Returns:
            True if tokens were acquired, False if timeout exceeded
        """
        start_time = time.monotonic()
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.001)  # 1ms sleep between attempts
```
