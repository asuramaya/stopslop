The bucket already defaulted to `time.monotonic`; the drift path was that a caller-supplied `clock` (or a wall clock) could jump backwards or forwards and corrupt `_last_refill`, and that `deadline`/`wait` mixed clock sources. This version pins the internal clock to `time.monotonic`, rejects backwards jumps, and keeps the fractional remainder so repeated small refills don't truncate away tokens.

```python
import threading
import time


class RateLimitExceeded(Exception):
    """Raised when a caller opts into strict acquisition and no tokens remain."""


class TokenBucket:
    """Thread-safe token bucket.

    Tokens refill continuously at `refill_rate` per second up to `capacity`.
    A burst of up to `capacity` requests can pass instantly; the sustained
    rate settles to `refill_rate`.

    Timing comes from `time.monotonic`, never the wall clock: NTP steps, DST
    transitions and manual clock changes must not create or destroy tokens.
    A `clock` may be injected for tests, but it is required to be monotonic —
    a backwards reading is treated as zero elapsed time rather than as a
    negative refill.

    Every read of the token count happens under `_refilled`, since refilling
    is a read-modify-write of both `_tokens` and `_last_refill`. Blocked
    waiters sleep on the condition and are woken when tokens are returned or
    their wait interval expires, so they never spin.
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
        self._last_refill = clock()
        self._refilled = threading.Condition(threading.Lock())

    def try_acquire(self, tokens=1, raise_on_empty=False):
        """Take `tokens` from the bucket. Returns True if they were available."""
        self._check_request(tokens)

        with self._refilled:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            remaining = self._tokens

        if raise_on_empty:
            raise RateLimitExceeded(f"need {tokens} tokens, {remaining:.2f} available")
        return False

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are taken.

        Returns True on success, False if `timeout` seconds elapse first. The
        deadline is computed from the same monotonic source as the refill, so
        a long wait cannot be cut short or extended by a clock adjustment.
        """
        self._check_request(tokens)

        with self._refilled:
            deadline = None if timeout is None else self._now() + timeout
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                delay = (tokens - self._tokens) / self.refill_rate
                if deadline is not None:
                    remaining = deadline - self._now()
                    if remaining <= 0:
                        return False
                    delay = min(delay, remaining)
                self._refilled.wait(delay)

    def release(self, tokens=1):
        """Return unused tokens to the bucket and wake anyone waiting on them."""
        with self._refilled:
            self._refill()
            self._tokens = min(self.capacity, self._tokens + tokens)
            self._refilled.notify_all()

    def wait_time(self, tokens=1):
        """Seconds until `tokens` would be available, 0.0 if they already are."""
        with self._refilled:
            self._refill()
            return max(0.0, (tokens - self._tokens) / self.refill_rate)

    @property
    def available(self):
        with self._refilled:
            self._refill()
            return self._tokens

    def _now(self):
        """Monotonic reading, clamped so a backwards clock never rewinds state."""
        return max(self._clock(), self._last_refill)

    def _check_request(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError(f"cannot acquire {tokens} from a bucket of {self.capacity}")

    def _refill(self):
        """Caller must hold `_refilled`."""
        now = self._now()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return

        earned = elapsed * self.refill_rate
        if self._tokens + earned >= self.capacity:
            self._tokens = self.capacity
            self._last_refill = now
            return

        # Advance the mark only by the time actually converted into tokens, so
        # the sub-token remainder of a short interval carries into the next one
        # instead of being rounded away under a high call rate.
        self._tokens += earned
        self._last_refill += earned / self.refill_rate
```
