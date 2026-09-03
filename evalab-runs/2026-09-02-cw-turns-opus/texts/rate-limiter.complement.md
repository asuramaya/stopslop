`time.time()` isn't in this code — the refill has used `time.monotonic` since the first version, so wall-clock jumps and NTP steps are already out of the picture. The drift that is left is in the accumulator: `self._tokens += elapsed * self.rate` rounds on every call, and under load that is thousands of roundings per second, all biased the same way once the value gets large relative to the increment. Below, the accumulator is gone. State is a single timestamp (the GCRA / virtual-scheduling form), and the token count is derived from it, so error cannot compound across calls.

```python
import threading
import time


class TokenBucket:
    """Rate limiter allowing bursts up to `capacity` tokens, refilled at `rate` per second.

    State is one timestamp, not a running token count: `_tat` is the time at which the
    bucket would next be empty given everything granted so far. Tokens are derived from
    it on read, so no per-call rounding accumulates.

    Safe to share across threads: every read and write of `_tat` happens under `_cond`.
    The `_locked_*` helpers assume the caller already holds it.
    """

    def __init__(self, capacity, rate, clock=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if rate <= 0:
            raise ValueError("rate must be positive")

        self.capacity = float(capacity)
        self.rate = float(rate)
        self._interval = 1.0 / self.rate
        self._span = self.capacity * self._interval
        self._clock = clock or time.monotonic
        self._cond = threading.Condition()
        self._tat = self._clock()

    def _check_request(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity; request can never succeed")

    def _locked_grant(self, tokens, now):
        """Charge `tokens` if they fit, returning seconds to wait (0.0 on success)."""
        # A backwards clock jump must not let debt outlive it, hence max().
        start = max(self._tat, now)
        tat = start + tokens * self._interval
        shortfall = tat - (now + self._span)
        if shortfall > 0:
            return shortfall
        self._tat = tat
        return 0.0

    def try_acquire(self, tokens=1):
        """Take `tokens` if available. Returns True on success, False without waiting."""
        self._check_request(tokens)
        with self._cond:
            return self._locked_grant(tokens, self._clock()) == 0.0

    def acquire(self, tokens=1, timeout=None):
        """Wait for `tokens` and take them. Returns False if `timeout` seconds elapse first.

        `timeout=None` waits indefinitely; `timeout=0` is equivalent to `try_acquire`.
        """
        self._check_request(tokens)
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative or None")

        deadline = None if timeout is None else self._clock() + timeout
        with self._cond:
            while True:
                wait = self._locked_grant(tokens, self._clock())
                if wait == 0.0:
                    return True
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    wait = min(wait, remaining)
                # Nothing signals this condition; the timed wait is the refill clock.
                self._cond.wait(wait)

    def time_until_available(self, tokens=1):
        """Seconds until `tokens` can be acquired, or 0.0 if available now.

        Advisory only: another thread can drain the bucket before the caller waits.
        """
        self._check_request(tokens)
        with self._cond:
            now = self._clock()
            return max(0.0, max(self._tat, now) + tokens * self._interval - now - self._span)

    @property
    def tokens(self):
        with self._cond:
            now = self._clock()
            return min(self.capacity, max(0.0, (now - self._tat) / self._interval + self.capacity))
```

Two behaviour notes, since the internals changed and not just the clock source:

- `time_until_available` now validates its argument, so asking about more tokens than `capacity` raises instead of returning a wait that would never end.
- `_tat` is granted in arrival order, which makes concurrent `acquire` calls closer to FIFO than the old accumulator was — a thread that got in first has already moved `_tat`. It is still not a fairness guarantee; a `try_acquire` arriving in a gap can jump the line.
