`worker.py`, 110 lines. All three cases above pass.

What changed:

- `Worker(callback, max_pending=N)` builds a bounded `queue.Queue(maxsize=N)`. `0` (the default) stays unbounded, matching `Queue`'s own convention. Passing both `q` and `max_pending` raises — the bound belongs to whichever queue object you own.
- `put(item, block=True, timeout=None)` now forwards those args, so a producer can block, time out, or fail fast. `try_put(item)` returns `False` instead of raising `queue.Full`.
- `pending` exposes `qsize()`.
- `stop()` routes the sentinel through `_send_stop`, which retries in 50ms slices while the thread is alive rather than issuing one blocking `put`. Without that, a bounded queue turns `stop()` into a deadlock in exactly the case case 3 covers: the thread has already exited on a producer-sent `STOP`, the queue is full, and nothing will ever free a slot.

The limit is on queued items, not concurrency: one thread means one callback at a time, so `max_pending=N` caps the backlog at N, with the in-flight item counted until `task_done()`. In case 1, six items through a 2-slot queue held the producer for 0.15s instead of returning immediately.

Two things this does not do. Backpressure is only as good as the producer — `put()` blocking means the producer's thread stalls, which is the point, but if that thread also serves something latency-sensitive you want `put(block=False)` and a drop policy instead. And `_send_stop` can still spin for the full `timeout` if the thread is alive and wedged inside a callback that never returns; the sentinel goes in as soon as a slot frees, but nothing preempts a hung callback. A hard cancel that drops the backlog remains unbuilt — still available if you want it.
