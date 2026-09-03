```python
import threading
import time


class TokenBucket:
    """Token-bucket rate limiter, safe to share across threads.

    Tokens refill continuously at `rate` per second up to `capacity`,
    which is also the largest burst a caller can take at once.
    """

    def __init__(self, capacity, rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if rate <= 0:
            raise ValueError("rate must be positive")
        self.capacity = float(capacity)
        self.rate = float(rate)
        self._clock = clock
        self._tokens = float(capacity)
        self._updated = clock()
        self._lock = threading.Lock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._updated = now

    def try_acquire(self, tokens=1):
        """Take `tokens` if available. Return True on success, False otherwise."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are taken, or until timeout. Returns bool."""
        deadline = None if timeout is None else self._clock() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                wait = (tokens - self._tokens) / self.rate
            if deadline is not None:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    return False
                wait = min(wait, remaining)
            time.sleep(wait)

    @property
    def tokens(self):
        with self._lock:
            self._refill()
            return self._tokens
```

Notes on the design:

- `time.monotonic` rather than `time.time`, so a clock adjustment can't hand out free tokens or stall the bucket. It's injectable so tests can drive time directly.
- Refill is lazy — computed from elapsed time on each call — so there's no background thread and an idle bucket costs nothing.
- The lock covers refill and deduction together; without that, two threads can both read the same token count and both spend it.
- `acquire` computes its sleep from the deficit instead of polling, and it re-checks the balance after waking since another thread may have drained the bucket in the meantime.

I threw in the blocking `acquire` and the `tokens` property beyond what you asked for; drop them if you only want the non-blocking path.

I ran it rather than eyeballing it: a burst of 6 against a capacity-5 bucket granted exactly 5, a 0.35s pause at rate 10 restored 3.5 tokens, 100 threads racing for a 50-token bucket got exactly 50 grants, and `acquire(timeout=0.1)` on the drained bucket returned `False`. The scratch copy is at `/tmp/tb.py` — you named no destination, so I left nothing in the repo. Say the word and I'll drop it wherever it belongs.
