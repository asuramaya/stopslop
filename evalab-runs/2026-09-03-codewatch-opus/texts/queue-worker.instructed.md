```python
import logging
import queue
import threading

logger = logging.getLogger(__name__)


class Shutdown:
    """Sentinel pushed onto the queue to tell the worker to stop."""

    def __repr__(self):
        return "<shutdown>"


SHUTDOWN = Shutdown()


class QueueWorker:
    """Consumes items from a queue on a background thread, passing each to a callback.

    A callback that raises is logged and counted; the thread keeps consuming. Pass
    `on_error` to route failures somewhere useful (a dead-letter queue, metrics, a retry).

    `max_in_flight` caps how many unfinished items may sit in the queue. Once the cap is
    reached, `submit` blocks (or raises, with `timeout`) so producers feel the backpressure
    instead of letting an unbounded backlog grow behind a slow callback.
    """

    def __init__(
        self,
        work_queue,
        handle_item,
        on_error=None,
        max_in_flight=100,
        name="queue-worker",
    ):
        if max_in_flight is not None and max_in_flight < 1:
            raise ValueError("max_in_flight must be at least 1")
        self.work_queue = work_queue
        self.handle_item = handle_item
        self.on_error = on_error
        self.max_in_flight = max_in_flight
        self.capacity = threading.BoundedSemaphore(max_in_flight) if max_in_flight else None
        self.thread = threading.Thread(target=self._consume, name=name, daemon=True)
        self.processed_count = 0
        self.error_count = 0
        self.rejected_count = 0

    def start(self):
        self.thread.start()
        return self

    def _consume(self):
        while True:
            item = self.work_queue.get()
            try:
                if item is SHUTDOWN:
                    logger.debug(
                        "shutting down after %d items (%d errors, %d rejected)",
                        self.processed_count,
                        self.error_count,
                        self.rejected_count,
                    )
                    return
                self.handle_item(item)
                self.processed_count += 1
            except BaseException as exc:
                self.error_count += 1
                logger.exception("worker callback failed for item %r", item)
                self._report_error(item, exc)
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
            finally:
                self.work_queue.task_done()
                if self.capacity is not None and item is not SHUTDOWN:
                    self.capacity.release()

    def _report_error(self, item, exc):
        if self.on_error is None:
            return
        try:
            self.on_error(item, exc)
        except Exception:
            logger.exception("on_error handler failed for item %r", item)

    def submit(self, item, timeout=None):
        """Queue an item, waiting for a free slot. Returns False if `timeout` expires."""
        if item is SHUTDOWN:
            raise ValueError("use stop() to shut the worker down")
        if self.capacity is not None and not self.capacity.acquire(timeout=timeout):
            self.rejected_count += 1
            logger.warning("dropped %r: %d items already in flight", item, self.max_in_flight)
            return False
        self.work_queue.put(item)
        return True

    def drain(self):
        """Block until every item queued so far has been handled."""
        self.work_queue.join()

    def stop(self, timeout=None):
        """Queue the sentinel so the thread finishes pending items, then exits.

        The sentinel bypasses the in-flight cap so shutdown never deadlocks behind a
        full queue.
        """
        if not self.thread.is_alive():
            return True
        self.work_queue.put(SHUTDOWN)
        self.thread.join(timeout)
        if self.thread.is_alive():
            logger.warning("worker %s did not exit within %s s", self.thread.name, timeout)
            return False
        return True

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO)

    failed = queue.Queue()

    def fetch(url):
        if url.endswith("/3"):
            raise ConnectionError(url)
        time.sleep(0.05)
        logger.info("fetching %s", url)

    worker = QueueWorker(
        queue.Queue(),
        fetch,
        on_error=lambda item, exc: failed.put(item),
        max_in_flight=4,
    )
    with worker:
        for page in range(20):
            worker.submit(f"https://example.com/page/{page}", timeout=1.0)
        worker.drain()

    logger.info("%d items failed, %d rejected", failed.qsize(), worker.rejected_count)
```
