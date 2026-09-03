```python
import threading
import time


class RateLimitExceeded(Exception):
    """Raised when a caller asks for more tokens than the bucket can ever hold."""


class TokenBucket:
    """Thread-safe token bucket.

    The bucket holds at most `capacity` tokens and refills continuously at
    `refill_rate` tokens per second. Tokens are computed lazily under the
    lock on each call, so there is no background timer thread and every
    mutable field (`_tokens`, `_last_refill`) is only ever touched by a
    thread holding the condition's lock. `capacity` and `refill_rate` are
    fixed at construction and safe to read unguarded.

    All timing uses `time.monotonic`, which is unaffected by wall-clock
    adjustments (NTP steps, DST, manual clock changes). `time.time` would
    let a backwards step stall refills for the length of the correction and
    a forwards step hand out a windfall of tokens. Fractional elapsed time
    is never discarded: `_last_refill` advances to the observed `now` on
    every refill, so repeated sub-tick calls under load accumulate rather
    than truncating toward zero. A custom `clock` may be injected for tests
    but must be monotonic and expressed in seconds.
    """

    def __init__(self, capacity, refill_rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._clock = clock
        self._tokens = float(capacity)
        self._last_refill = clock()
        self._condition = threading.Condition()

    @property
    def capacity(self):
        return self._capacity

    @property
    def refill_rate(self):
        return self._refill_rate

    def _refill_locked(self):
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            # A monotonic clock never runs backwards, but an injected one might;
            # resynchronize instead of crediting or debiting tokens.
            self._last_refill = now
            return
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

    def _check_request(self, tokens):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self._capacity:
            raise RateLimitExceeded(
                f"request of {tokens} exceeds bucket capacity {self._capacity}"
            )

    def _take_locked(self, tokens):
        self._refill_locked()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def try_acquire(self, tokens=1):
        """Consume `tokens` if available. Returns True on success, False otherwise."""
        self._check_request(tokens)
        with self._condition:
            return self._take_locked(tokens)

    def acquire(self, tokens=1, timeout=None):
        """Block until `tokens` are consumed, or until `timeout` seconds elapse.

        Returns True if the tokens were consumed, False if the timeout expired
        first. `timeout=None` waits indefinitely. The deadline is measured on
        the same monotonic clock as the refill, so a wall-clock jump can neither
        cut a wait short nor extend it. Waiters sleep on the refill deadline
        rather than polling, and wake each other on release so a cancelled or
        partially served waiter does not strand the queue.
        """
        self._check_request(tokens)
        deadline = None if timeout is None else self._clock() + timeout

        with self._condition:
            while True:
                if self._take_locked(tokens):
                    return True

                needed = (tokens - self._tokens) / self._refill_rate
                if deadline is None:
                    wait = needed
                else:
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    wait = min(needed, remaining)

                self._condition.wait(wait)

    def release(self, tokens=1):
        """Return unused tokens to the bucket and wake any waiters."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._condition:
            self._refill_locked()
            self._tokens = min(self._capacity, self._tokens + tokens)
            self._condition.notify_all()

    def wait_time(self, tokens=1):
        """Seconds until `tokens` become available; 0.0 if they already are."""
        with self._condition:
            self._refill_locked()
            deficit = tokens - self._tokens
            return max(0.0, deficit / self._refill_rate)

    @property
    def available(self):
        with self._condition:
            self._refill_locked()
            return self._tokens
```
