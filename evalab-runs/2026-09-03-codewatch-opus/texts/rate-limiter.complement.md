```python
import threading
import time


class RateLimitExceeded(Exception):
    """Raised by acquire() when tokens cannot be obtained within the deadline."""


class TokenBucket:
    """Classic token bucket: `capacity` tokens, refilled at `rate` tokens/second.

    Thread-safe. Refill is computed lazily from elapsed time on each call, so
    there is no background timer to manage. Waiters block on a Condition.

    The clock must be monotonic: time.time() is subject to NTP steps and manual
    resets, which either stall the bucket or hand it a windfall of tokens.
    """

    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._clock = clock
        self._tokens = float(capacity)
        self._updated_at = clock()
        self._cond = threading.Condition(threading.Lock())

    def _refill(self):
        """Caller must hold the condition's lock."""
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
        # Advance the mark only by the time actually converted into tokens.
        # Under load _refill() runs far more often than once per token period,
        # and setting _updated_at = now would discard each call's sub-token
        # remainder, so the bucket would fill measurably slower than `rate`.
        self._updated_at += earned / self.rate

    def _check_n(self, n):
        if n <= 0:
            raise ValueError("n must be positive")
        if n > self.capacity:
            raise ValueError(f"n={n} exceeds bucket capacity {self.capacity}")

    @property
    def tokens(self):
        with self._cond:
            self._refill()
            return self._tokens

    def try_acquire(self, n=1):
        """Take `n` tokens if available. Returns True on success, False otherwise."""
        self._check_n(n)
        with self._cond:
            self._refill()
            if self._tokens < n:
                return False
            self._tokens -= n
            return True

    def acquire(self, n=1, timeout=None):
        """Block until `n` tokens are taken.

        Returns True on success. With `timeout=None` this waits indefinitely;
        otherwise it raises RateLimitExceeded once `timeout` seconds have passed
        without the tokens becoming available.
        """
        self._check_n(n)
        deadline = None if timeout is None else self._clock() + timeout
        with self._cond:
            while True:
                self._refill()
                if self._tokens >= n:
                    self._tokens -= n
                    return True
                wait = (n - self._tokens) / self.rate
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        raise RateLimitExceeded(
                            f"could not acquire {n} tokens in {timeout}s"
                        )
                    wait = min(wait, remaining)
                # Timed wait rather than notify-driven: tokens accrue from the
                # clock, so no other thread is in a position to signal them.
                # Competing waiters may consume the refill first, hence the loop.
                self._cond.wait(wait)

    def release(self, n=1):
        """Return `n` unused tokens to the bucket and wake the waiters."""
        if n <= 0:
            raise ValueError("n must be positive")
        with self._cond:
            self._refill()
            self._tokens = min(self.capacity, self._tokens + n)
            self._cond.notify_all()
```
