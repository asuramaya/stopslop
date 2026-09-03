import threading
import time


class TokenBucket:
    """Token-bucket rate limiter.

    Tokens refill continuously at `rate` tokens per second, up to
    `capacity`. Each `try_acquire` call withdraws `tokens` tokens if
    enough are available.
    """

    def __init__(self, capacity: float, rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if rate <= 0:
            raise ValueError("rate must be positive")

        self._capacity = capacity
        self._rate = rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def try_acquire(self, tokens: float = 1) -> bool:
        """Attempt to withdraw `tokens` tokens.

        Returns True and deducts the tokens if enough are available,
        otherwise returns False and leaves the bucket unchanged.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
