```python
import threading
import time


class TokenBucket:
    """Rate limiter that refills `rate` tokens per second up to `capacity`.

    Bursts are allowed up to `capacity`; sustained throughput settles at `rate`.
    Every method that touches token state holds `_lock`, so instances can be
    shared across threads without external synchronization.

    Timing uses `time.monotonic`, which is unaffected by wall-clock adjustments.
    """

    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.rate = rate
        self.capacity = capacity
        self._clock = clock
        self._tokens = float(capacity)
        self._last_refill = clock()
        self._lock = threading.Lock()
        self._refilled = threading.Condition(self._lock)

    def _refill(self):
        """Caller must hold `_lock`."""
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return

        earned = elapsed * self.rate
        if self._tokens + earned >= self.capacity:
            self._tokens = float(self.capacity)
            self._last_refill = now
            return

        # Advance the clock only by the time actually converted into tokens, so
        # the sub-token remainder is credited on the next refill instead of
        # being truncated away.
        whole = earned // 1 if self.rate >= 1 else earned
        self._tokens += whole
        self._last_refill += whole / self.rate

    def _check_request(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")

    def try_acquire(self, tokens=1):
        """Take `tokens` from the bucket. Returns False without waiting if short."""
        self._check_request(tokens)

        with self._lock:
            self._refill()
            if self._tokens < tokens:
                return False
            self._tokens -= tokens
            return True

    def acquire(self, tokens=1, timeout=None):
        """Wait for `tokens` and take them. Returns False if `timeout` expires first.

        `timeout=None` waits indefinitely. The deadline is measured on `_clock`,
        so an injected clock controls both refill and expiry.
        """
        self._check_request(tokens)
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative")

        with self._refilled:
            deadline = None if timeout is None else self._clock() + timeout
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                wait_for = (tokens - self._tokens) / self.rate
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    wait_for = min(wait_for, remaining)
                self._refilled.wait(wait_for)

    def release(self, tokens=1):
        """Return unused tokens to the bucket and wake anyone waiting on them."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        with self._refilled:
            self._tokens = min(self.capacity, self._tokens + tokens)
            self._refilled.notify_all()

    def time_until_available(self, tokens=1):
        """Seconds until `tokens` can be acquired; 0.0 if they are available now."""
        self._check_request(tokens)

        with self._lock:
            self._refill()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self.rate)

    @property
    def available(self):
        with self._lock:
            self._refill()
            return self._tokens
```

The clock was already `time.monotonic`, so drift under load is not coming from the clock source — `time.time()` would give you jumps on an NTP step, not a steady undercount. What does drift is the refill bookkeeping: the old `_refill` set `_last_refill = now` on every call, which discards the fraction of elapsed time that had not yet added up to a usable token. Under load, `try_acquire` is called far more often than a token period, so nearly every call throws away a slice of time and the bucket refills measurably slower than `rate`.

The fix advances `_last_refill` by the time actually converted into tokens, leaving the remainder to accumulate. At `rate >= 1` the credit is truncated to whole tokens; below that, tokens are inherently fractional and the whole elapsed span is credited. The saturated case still snaps `_last_refill` to `now`, since time spent at full capacity is genuinely lost.

One consequence to know about: `available` and `time_until_available` now report on whole-token boundaries at `rate >= 1`, so a bucket that is 40% of the way to its next token still reads as the lower integer. That is the honest answer to "what can I take right now."
