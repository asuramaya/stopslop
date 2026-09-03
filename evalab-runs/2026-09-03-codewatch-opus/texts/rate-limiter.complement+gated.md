```python
import threading
import time


class TokenBucket:
    """Rate limiter allowing bursts up to `capacity`, refilling at `rate` tokens/sec.

    Thread-safe: one lock guards the token count and the refill clock together,
    so two callers can never both spend the same token. Every public entry point
    takes the lock; `_refill` never does, since it is only ever reached from
    inside a held lock. Waiters sleep on a condition variable rather than the
    wall clock, so a returning token wakes them immediately.

    The clock must be monotonic. `time.time()` is subject to NTP steps, leap
    second smearing, and manual clock changes: a backwards step stalls every
    refill until the wall clock catches up, and a forwards step hands out a
    burst the rate limit never authorized. `time.monotonic()` measures only
    elapsed time and cannot be adjusted.
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
        self._updated_at = clock()
        self._not_empty = threading.Condition()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._updated_at
        if elapsed <= 0:
            return

        earned = elapsed * self.rate
        if self._tokens + earned >= self.capacity:
            self._tokens = self.capacity
            self._updated_at = now
            return

        self._tokens += earned
        # Advance the mark by the time actually converted into tokens, not to
        # `now`. Under load these calls land far more often than one token
        # period, and rounding the leftover away each time is what makes a
        # bucket deliver measurably under its rate over a long run.
        self._updated_at += earned / self.rate

    def try_acquire(self, tokens=1):
        """Spend `tokens` if available. Returns True on success, False otherwise."""
        self._validate(tokens)
        with self._not_empty:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            return True

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are spent. Returns False if `timeout` expires first.

        A caller that gives up releases the condition without touching the
        bucket, so nothing is consumed on the timeout path.
        """
        self._validate(tokens)
        deadline = None if timeout is None else self._clock() + timeout

        with self._not_empty:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                delay = (tokens - self._tokens) / self.rate
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    delay = min(delay, remaining)
                # Timing out here is expected, not an error: the loop re-checks
                # the deadline and the refilled balance on the next pass.
                self._not_empty.wait(delay)

    def release(self, tokens=1):
        """Return unused tokens to the bucket and wake anyone waiting on them."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._not_empty:
            self._refill()
            self._tokens = min(self.capacity, self._tokens + tokens)
            self._not_empty.notify_all()

    def wait_time(self, tokens=1):
        """Seconds until `tokens` would be available. 0.0 if they already are."""
        self._validate(tokens)
        with self._not_empty:
            self._refill()
            return max(0.0, (tokens - self._tokens) / self.rate)

    @property
    def tokens(self):
        with self._not_empty:
            self._refill()
            return self._tokens

    def _validate(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError(
                f"cannot acquire {tokens} tokens from a bucket of capacity {self.capacity}"
            )
```
