```python
import time
from threading import Lock


class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self.lock = Lock()
    
    def try_acquire(self, tokens=1):
        """Attempt to acquire tokens. Returns True if successful, False if insufficient."""
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens=1, timeout=None):
        """Block until tokens are available, or timeout expires. Returns True if successful."""
        start_time = time.monotonic()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)
    
    def _refill(self):
        """Add tokens based on elapsed time, capped at capacity."""
        now = time.monotonic()
        time_passed = now - self.last_refill_time
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now
```
