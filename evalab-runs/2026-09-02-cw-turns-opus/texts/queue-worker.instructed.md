```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)

_SHUTDOWN = object()


class QueueWorker:
    """Runs a callback against each item pulled from a queue on a worker thread.

    The queue is bounded, so `submit` blocks once `max_in_flight` items are
    waiting on a callback that has not returned yet.
    """

    def __init__(self, handle_item, max_in_flight=100, name="queue-worker", on_error=None):
        if max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self.handle_item = handle_item
        self.on_error = on_error
        self.queue = queue.Queue(maxsize=max_in_flight)
        self.thread = threading.Thread(target=self._drain, name=name, daemon=True)
        self.started = False
        self.failure_count = 0

    def start(self):
        if self.started:
            raise RuntimeError("worker already started")
        self.started = True
        self.thread.start()

    def submit(self, item, timeout=None):
        """Block until the worker has room, then enqueue. Raises queue.Full on timeout."""
        if not self.started:
            raise RuntimeError("worker is not running")
        self.queue.put(item, timeout=timeout)

    def try_submit(self, item):
        """Enqueue only if the worker has room. Returns False when it is saturated."""
        if not self.started:
            raise RuntimeError("worker is not running")
        try:
            self.queue.put_nowait(item)
            return True
        except queue.Full:
            logger.warning("dropped %r: %d items already in flight", item, self.queue.maxsize)
            return False

    def _drain(self):
        while True:
            item = self.queue.get()
            try:
                if item is _SHUTDOWN:
                    return
                self.handle_item(item)
            except BaseException as exc:
                self.failure_count += 1
                logger.exception("handler failed for %r", item)
                if self.on_error is not None:
                    try:
                        self.on_error(item, exc)
                    except Exception:
                        logger.exception("on_error hook failed for %r", item)
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
            finally:
                self.queue.task_done()

    def join_pending(self):
        """Block until every item submitted so far has been handled."""
        self.queue.join()

    def stop(self, timeout=None):
        """Queue the sentinel so the backlog drains first, then wait for the thread."""
        if not self.started:
            return
        self.started = False
        self.queue.put(_SHUTDOWN)
        self.thread.join(timeout)
        if self.thread.is_alive():
            logger.warning("worker %s did not exit within %ss", self.thread.name, timeout)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
```

One consequence worth stating: `stop` uses a blocking `put` for the sentinel, so if the queue is full it waits for the callback to free a slot. That is what you want for a clean shutdown, but it means `stop(timeout=...)` can wait longer than `timeout` overall.
