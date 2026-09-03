"""Single-threaded queue consumer with a sentinel-based shutdown."""

import queue
import threading


_SENTINEL = object()


class QueueWorker:
    """Runs `callback(item)` on a background thread for each queued item.

    Exceptions raised by the callback are passed to `on_error` (default:
    swallowed) so one bad item cannot kill the thread.
    """

    def __init__(self, callback, on_error=None, maxsize=0, name="queue-worker"):
        self.callback = callback
        self.on_error = on_error
        self.queue = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._started = False
        self._dropping = False

    def start(self):
        if self._started:
            raise RuntimeError("worker already started")
        self._started = True
        self._thread.start()
        return self

    def put(self, item, block=True, timeout=None):
        self.queue.put(item, block, timeout)

    def _run(self):
        while True:
            item = self.queue.get()
            try:
                if item is _SENTINEL:
                    return
                if self._dropping:
                    continue
                self.callback(item)
            except Exception as exc:  # noqa: BLE001 - one item must not kill the thread
                if self.on_error is not None:
                    self.on_error(item, exc)
            finally:
                self.queue.task_done()

    def stop(self, drain=True, timeout=None):
        """Shut the thread down. With drain=False, items still queued are dropped."""
        if not self._started:
            return
        if not drain:
            self._dropping = True
        self.queue.put(_SENTINEL)
        self._thread.join(timeout)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc_info):
        self.stop()
        return False
