The class never used `time.time()` — the default clock has been `time.monotonic` since the first version, and refill is computed from absolute elapsed time (`now - _updated_at`) rather than accumulated per-tick increments, so it doesn't drift under load either.

There is a real drift hazard adjacent to what you're describing, though: if a caller passes a wall clock as `clock` (or the injected clock ever steps backwards), `elapsed` goes negative and the bucket silently freezes its timestamp in the future, stalling refill for the length of the step. The version below clamps backwards jumps, and fixes the one genuine time-source mismatch I flagged earlier — `Condition.wait` counted in real seconds while token math counted in injected-clock seconds.

```python
import threading
import time


class RateLimitExceeded(Exception):
    """Raised by acquire() when tokens cannot be obtained in time."""


class TokenBucket:
    """Thread-safe token bucket rate limiter.

    The bucket holds at most `capacity` tokens and refills continuously at
    `refill_rate` tokens per second. Each call consumes tokens; when the
    bucket is empty, calls are refused (`try_acquire`) or wait (`acquire`).

    `clock` must be monotonic. Refill is derived from absolute elapsed time,
    not accumulated per-call increments, so it does not drift no matter how
    often or how irregularly the bucket is touched.

    All mutable state is guarded by `_cond`'s lock. `_refill` and
    `_try_locked` assume the caller already holds it.
    """

    def __init__(self, capacity, refill_rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._clock = clock
        self._tokens = float(capacity)
        self._updated_at = clock()
        self._cond = threading.Condition()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._updated_at
        if elapsed < 0:
            # Clock stepped backwards (a wall clock was injected, or NTP
            # slewed). Re-anchor rather than banking a negative debt that
            # would stall refill until real time caught back up.
            self._updated_at = now
        elif elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._updated_at = now

    def _check(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens exceeds bucket capacity")

    def _try_locked(self, tokens):
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    @property
    def tokens(self):
        """Currently available tokens, refilled to the present moment."""
        with self._cond:
            self._refill()
            return self._tokens

    def try_acquire(self, tokens=1):
        """Consume `tokens` if available. Returns True on success, else False."""
        self._check(tokens)
        with self._cond:
            return self._try_locked(tokens)

    def time_until(self, tokens=1):
        """Seconds until `tokens` are available; 0.0 if available now."""
        self._check(tokens)
        with self._cond:
            self._refill()
            return max(0.0, (tokens - self._tokens) / self.refill_rate)

    def acquire(self, tokens=1, timeout=None, blocking=True):
        """Block until `tokens` are acquired.

        `timeout` is a deadline in seconds; None waits indefinitely and 0 (or
        blocking=False) makes a single attempt. Raises RateLimitExceeded if the
        deadline passes first; the bucket is left untouched in that case.
        """
        self._check(tokens)
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative")
        if not blocking:
            timeout = 0.0
        with self._cond:
            deadline = None if timeout is None else self._clock() + timeout
            while not self._try_locked(tokens):
                wait = (tokens - self._tokens) / self.refill_rate
                if deadline is not None:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        # A peer may be blocked behind a wake we will never use.
                        self._cond.notify_all()
                        raise RateLimitExceeded(
                            f"could not acquire {tokens} token(s) within {timeout}s"
                        )
                    wait = min(wait, remaining)
                # Wall-clock deadline for wait(); the loop re-derives the true
                # deficit from `clock` on every wake, so an early or late wake
                # costs one cheap re-check and never a lost or duplicated token.
                self._cond.wait(max(wait, 0.001))
            return True

    def release(self, tokens=1):
        """Return unused tokens to the bucket and wake any waiters."""
        with self._cond:
            self._refill()
            self._tokens = min(self.capacity, self._tokens + tokens)
            self._cond.notify_all()
```

If what you're actually seeing is a rate that comes out lower than `refill_rate` under load, the cause is more likely one of these than the clock:

- **Saturation clamping.** Time that elapses while the bucket is full is discarded by design. A bursty workload that idles at capacity, then drains, gets `refill_rate` sustained but no credit for the idle stretch beyond `capacity`.
- **`acquire`'s 1 ms floor.** With a high `refill_rate`, many waiters wake, take one token, and re-block; the floor caps the achievable throughput per waiting thread at roughly 1000 acquisitions/sec. Raise `capacity` so callers take bursts instead of single tokens.
- **No fairness.** Waiters are woken as a herd, so a hot thread can repeatedly beat a starved one. That shows up as per-caller drift, not aggregate drift. Fixing it needs a FIFO ticket queue rather than a bare condition variable — worth adding if you need per-client fairness.
