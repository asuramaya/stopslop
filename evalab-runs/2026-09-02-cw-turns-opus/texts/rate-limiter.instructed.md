`time.time()` isn't in this code — the default clock has been `time.monotonic` since the first version, and `_refill` measures elapsed time between calls rather than counting ticks. If a call site is passing `clock=time.time` explicitly, drop that argument and the wall-clock problem goes away.

There is a real drift under load, though, and it's a rounding one. `_refill` advances `_last_refill = now` unconditionally. When calls arrive faster than a token's worth of time accrues, `elapsed * refill_per_second` is small enough that adding it to `_tokens` rounds to no change, but the timestamp still moves forward — so that slice of time is charged and never credited. A hot loop of `try_acquire` calls throws away a slow bucket's refill almost entirely. The fix is to only consume time you actually credited:

```python
    def _refill(self):
        """Caller must hold self._lock."""
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return

        refilled = self._tokens + elapsed * self.refill_per_second
        if refilled >= self.capacity:
            self._tokens = self.capacity
            self._last_refill = now
        elif refilled > self._tokens:
            self._tokens = refilled
            self._last_refill = now
        # Otherwise the gain rounded away entirely; leave _last_refill alone so
        # the elapsed time accumulates into a later call instead of vanishing.
```

The full class with that change:

```python
import threading
import time


class TokenBucket:
    """Rate limiter that refills tokens at a steady rate up to a burst cap.

    Tokens accrue continuously at `refill_per_second`. A caller may take up
    to `capacity` tokens at once if the bucket has been idle long enough.
    All bucket state is guarded by an internal lock, so a single instance is
    safe to share across threads.
    """

    def __init__(self, capacity, refill_per_second, clock=time.monotonic, sleep=time.sleep):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_second <= 0:
            raise ValueError("refill_per_second must be positive")

        self.capacity = float(capacity)
        self.refill_per_second = float(refill_per_second)
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(capacity)
        self._last_refill = clock()
        self._lock = threading.Lock()

    def try_acquire(self, tokens=1):
        """Take `tokens` from the bucket. Returns True if they were available."""
        self._check(tokens)
        with self._lock:
            self._refill()
            return self._take(tokens)

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are taken, or until `timeout` seconds elapse.

        Returns True on success, False if the timeout expired first. A timeout
        of None waits indefinitely; a timeout of 0 is one non-blocking attempt.
        Waiters are not queued, so a steady stream of contenders can starve a
        thread asking for a large `tokens` count until its timeout runs out.
        """
        self._check(tokens)
        deadline = None if timeout is None else self._clock() + timeout

        while True:
            with self._lock:
                self._refill()
                if self._take(tokens):
                    return True
                nap = (tokens - self._tokens) / self.refill_per_second

            if deadline is not None:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    return False
                nap = min(nap, remaining)
            self._sleep(nap)

    def wait_time(self, tokens=1):
        """Seconds until `tokens` become available. Zero if they already are.

        Advisory only: another thread can drain the bucket before the caller
        wakes, so treat the result as a sleep hint and re-check try_acquire.
        """
        self._check(tokens)
        with self._lock:
            self._refill()
            return max(0.0, (tokens - self._tokens) / self.refill_per_second)

    @property
    def available(self):
        with self._lock:
            self._refill()
            return self._tokens

    def _check(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError(
                f"cannot acquire {tokens} tokens from a bucket of capacity {self.capacity}"
            )

    def _take(self, tokens):
        """Caller must hold self._lock and have just refilled."""
        if self._tokens < tokens:
            return False
        self._tokens -= tokens
        return True

    def _refill(self):
        """Caller must hold self._lock."""
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return

        refilled = self._tokens + elapsed * self.refill_per_second
        if refilled >= self.capacity:
            self._tokens = self.capacity
            self._last_refill = now
        elif refilled > self._tokens:
            self._tokens = refilled
            self._last_refill = now
        # Otherwise the gain rounded away entirely; leave _last_refill alone so
        # the elapsed time accumulates into a later call instead of vanishing.
```

A test that pins this: capacity 10, refill 1/sec, drain the bucket, then advance a fake clock by 1e-9 seconds ten million times. The old code ends near zero tokens; this one ends at 0.01.
