import threading
import time


class TokenBucket:
    """Token-bucket rate limiter.

    Tokens refill continuously at `rate` per second, up to `capacity`.
    """

    def __init__(self, capacity: float, rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if rate <= 0:
            raise ValueError("rate must be positive")
        self.capacity = capacity
        self.rate = rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def try_acquire(self, tokens: float = 1) -> bool:
        """Attempt to consume `tokens`. Return True if granted, False otherwise."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire(self, tokens: float = 1, timeout: float = None) -> bool:
        """Block until `tokens` are granted or `timeout` seconds elapse.

        `timeout=None` waits indefinitely. Returns True if granted, False on timeout.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self.try_acquire(tokens):
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(min(0.01, tokens / self.rate))


if __name__ == "__main__":
    bucket = TokenBucket(capacity=5, rate=1)
    for i in range(7):
        granted = bucket.try_acquire()
        print(f"request {i}: {'granted' if granted else 'denied'}")
