```python
"""A background worker pool that drains a queue.Queue, handing each item to a callback."""

import logging
import queue
import threading

log = logging.getLogger(__name__)


class _Shutdown:
    """Sentinel: put it on the queue to end one worker after the backlog drains."""

    __slots__ = ()

    def __repr__(self):
        return "SHUTDOWN"


SHUTDOWN = _Shutdown()


def _log_error(item, exc):
    log.exception("worker callback failed on %r", item, exc_info=exc)


class QueueWorker:
    """Runs `callback(item)` on up to `max_in_flight` daemon threads."""

    SHUTDOWN = SHUTDOWN

    def __init__(self, callback, q=None, name="queue-worker", on_error=None,
                 max_in_flight=1, max_pending=None, on_full="block"):
        if max_in_flight < 1:
            raise ValueError("max_in_flight must be >= 1")
        if on_full not in ("block", "drop", "error"):
            raise ValueError("on_full must be 'block', 'drop' or 'error'")
        if max_pending is None:
            max_pending = max_in_flight * 16  # 0 means explicitly unbounded
        self.callback = callback
        self.queue = q if q is not None else queue.Queue(maxsize=max_pending)
        self.on_error = on_error if on_error is not None else _log_error
        self.on_full = on_full
        self.max_in_flight = max_in_flight
        self.stopped = threading.Event()
        self.processed = self.errors = self.dropped = self.in_flight = 0
        self.crash = None  # last BaseException that ended a thread, if any
        self._lock = threading.Lock()
        self._live = max_in_flight
        self._threads = [
            threading.Thread(target=self._run, name=f"{name}-{i}", daemon=True)
            for i in range(max_in_flight)
        ]
        self._started = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        for t in self._threads:
            t.start()
        return self

    def submit(self, item, timeout=None):
        """Enqueue an item. Returns False only when on_full='drop' and it was dropped."""
        if self.stopped.is_set():
            raise RuntimeError("worker is shutting down")
        if self.on_full == "block":
            self.queue.put(item, timeout=timeout)
            return True
        try:
            self.queue.put_nowait(item)
            return True
        except queue.Full:
            with self._lock:
                self.dropped += 1
            if self.on_full == "error":
                raise
            log.warning("queue full (%d pending); dropping %r", self.queue.qsize(), item)
            return False

    def _handle_error(self, item, exc):
        with self._lock:
            self.errors += 1
        try:
            self.on_error(item, exc)
        except Exception:
            # A broken error handler must not be the thing that kills the worker.
            log.exception("worker on_error handler itself failed for %r", item)

    def _run(self):
        try:
            while True:
                item = self.queue.get()
                try:
                    if item is SHUTDOWN:
                        log.debug("worker received sentinel; shutting down")
                        return
                    with self._lock:
                        self.in_flight += 1
                    try:
                        self.callback(item)
                    finally:
                        with self._lock:
                            self.in_flight -= 1
                    with self._lock:
                        self.processed += 1
                except Exception as exc:
                    self._handle_error(item, exc)
                finally:
                    self.queue.task_done()
        except BaseException as exc:
            # KeyboardInterrupt, SystemExit, MemoryError: the thread is going
            # down regardless, but it should not go down *silently*.
            self.crash = exc
            log.critical("worker thread died: %r", exc, exc_info=exc)
            self._handle_error(None, exc)
        finally:
            with self._lock:
                self._live -= 1
                last = self._live == 0
            if last:
                self.stopped.set()
                if self.crash is not None:
                    self._drain()

    def _drain(self):
        """Unblock anyone in join_queue() after every worker has died abnormally."""
        while True:
            try:
                self.queue.get_nowait()
            except Exception:
                return
            try:
                self.queue.task_done()
            except ValueError:
                return

    def join_queue(self):
        """Block until submitted work is processed, or the workers die trying."""
        self.queue.join()
        if self.crash is not None:
            raise RuntimeError("worker died") from self.crash

    def stop(self, timeout=None):
        """Ask the workers to finish the backlog, then exit. Idempotent."""
        if not self._started:
            self.stopped.set()
            return True
        deadline = None if timeout is None else time.monotonic() + timeout
        if not self.stopped.is_set():
            for _ in self._threads:
                # Bounded queue: a sentinel may have to wait for room.
                while True:
                    left = None if deadline is None else deadline - time.monotonic()
                    if left is not None and left <= 0:
                        return False
                    try:
                        self.queue.put(SHUTDOWN, timeout=left if left is None else min(left, 0.1))
                        break
                    except queue.Full:
                        continue
        for t in self._threads:
            t.join(None if deadline is None else max(0.0, deadline - time.monotonic()))
        return not any(t.is_alive() for t in self._threads)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False
```

That needs `import time` alongside the others — `stop()` now works against a deadline.

Two separate bounds, because a slow callback backs things up in two different places:

**In-flight** is `max_in_flight`, enforced structurally by running that many worker threads rather than by a semaphore. One thread stuck in a 30-second callback leaves the other N-1 pulling items, so a single slow item stalls a slice of throughput instead of the whole pipeline. Note this is genuine concurrency only for I/O-bound or C-extension callbacks — the GIL means CPU-bound work won't speed up, though the bound still limits how much is queued *inside* the callback layer.

**Pending** is the queue's `maxsize`, defaulting to `max_in_flight * 16`. This is the one that stops unbounded memory growth when producers outrun the callback: previously the queue grew without limit and the failure showed up as an OOM far from the cause. Pass `max_pending=0` to opt back into unbounded.

`on_full` decides what happens when the bound is hit, and it's a real choice, not a default worth accepting silently:

- `"block"` (default) — backpressure: `submit()` blocks, so producers slow to the consumer's rate. Correct when items must not be lost; deadlock-prone if a callback ever submits back into the same worker.
- `"drop"` — shed load, count it in `self.dropped`, return `False`. Right for telemetry and metrics where fresh data beats complete data.
- `"error"` — raise `queue.Full` and let the producer decide.

`stop()` now puts one sentinel per thread and honours `timeout` across both the puts and the joins, returning `False` if any worker is still inside a callback when time runs out. `_drain()` only fires when the *last* worker exits after a crash, so one dying thread no longer discards work its peers are still processing. `in_flight` is readable from outside as a live gauge of how many callbacks are executing right now.
