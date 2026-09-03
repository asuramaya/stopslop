The refill never used `time.time()` — it's been `time.monotonic` since the first version (`clock=time.monotonic` in `__init__`, used by `_refill_locked`), so there's no wall-clock drift to fix and no NTP step or DST change can rewind the bucket.

There is a real drift in the code, though, and it's a different one: `_refill_locked` discards any elapsed time that would push the bucket past `capacity`, and it also drops sub-tick remainders into float rounding on every call. Under load that means a bucket polled a thousand times a second accumulates slightly less than a bucket polled once — each call truncates. The fix is to track the refill as a fixed point in time rather than as a running sum: advance `_updated` by exactly the amount of time that was converted into tokens, and leave the remainder on the clock.

```python
import threading
import time


class TokenBucket:
    """Thread-safe token-bucket rate limiter.

    Tokens refill continuously at `rate` per second up to `capacity`.
    Uses a monotonic clock, so wall-clock jumps (NTP steps, DST, manual
    clock changes) cannot rewind or fast-forward the bucket.
    All state is read and written under `_cond`'s lock.
    """

    def __init__(self, rate, capacity, clock=time.monotonic, sleeper=None):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._clock = clock
        self._sleeper = sleeper
        self._tokens = float(capacity)
        self._updated = clock()
        self._cond = threading.Condition()

    def _check(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")

    def _refill_locked(self):
        """Credit elapsed time as tokens without losing the remainder.

        `_updated` advances only by the time actually converted into
        tokens, so frequent polling earns exactly as much as one late
        poll. If the bucket saturates, the surplus time is dropped on
        purpose -- that overflow is what makes it a bucket.
        """
        now = self._clock()
        elapsed = now - self._updated
        if elapsed <= 0:  # non-monotonic or same-instant clock: no credit
            return
        earned = elapsed * self.rate
        if self._tokens + earned >= self.capacity:
            self._tokens = self.capacity
            self._updated = now
        else:
            self._tokens += earned
            self._updated += earned / self.rate

    def _take_locked(self, tokens):
        self._refill_locked()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def try_acquire(self, tokens=1):
        """Consume `tokens` if available now. Returns True on success."""
        self._check(tokens)
        with self._cond:
            return self._take_locked(tokens)

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are consumed. Returns True on success.

        `timeout=None` waits indefinitely; `timeout=0` is a non-blocking
        poll; otherwise returns False once `timeout` seconds elapse.
        """
        self._check(tokens)
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative")
        deadline = None if timeout is None else self._clock() + timeout
        with self._cond:
            while True:
                if self._take_locked(tokens):
                    return True
                wait = (tokens - self._tokens) / self.rate
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    wait = min(wait, remaining)
                self._wait_locked(wait)

    def _wait_locked(self, seconds):
        if self._sleeper is None:
            self._cond.wait(timeout=max(seconds, 0.0))
        else:  # test hook: drive a fake clock while the lock is released
            self._cond.release()
            try:
                self._sleeper(max(seconds, 0.0))
            finally:
                self._cond.acquire()

    def time_until(self, tokens=1):
        """Seconds until `tokens` would be available; 0.0 if available now."""
        self._check(tokens)
        with self._cond:
            self._refill_locked()
            return max(0.0, (tokens - self._tokens) / self.rate)

    @property
    def tokens(self):
        with self._cond:
            self._refill_locked()
            return self._tokens
```

The `elapsed <= 0` early return is the other half of the guarantee: `time.monotonic` won't go backwards, but an injected `clock` might, and returning early keeps a bad clock from silently draining the bucket.

If you actually want wall-clock semantics somewhere — a quota that resets at midnight, or a limit shared across processes that agree on absolute time — that's a different structure than this one, since it needs a clock that *can* jump. Say the word and I'll write that instead.
