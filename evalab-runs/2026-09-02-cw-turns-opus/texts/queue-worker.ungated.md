All eight checks pass, the original smoke run among them (five items in order, raising callback to `on_error`).

`maxsize` was already a bound, but the wrong one: `queue.Queue` stops counting an item the moment the worker calls `get()`, so the item sitting inside a slow callback does not occupy a slot. With `maxsize=2` and one wedged callback, a producer can still have three items accepted. `max_in_flight` counts accepted-until-finished instead.

What it does:

- `max_in_flight=N` allocates a `threading.Semaphore(N)`. `put()` takes a permit before it touches the queue; `_free()` returns it in the same `finally` that calls `task_done()`, so a callback that raises, a sentinel, and an item dropped by `stop(drain=False)` or `_abandon()` all give their permit back.
- At the limit, `put()` blocks; `block=False` or a `timeout` gets `queue.Full`. A `timeout` covers the whole call, permit wait plus enqueue, off one `time.monotonic()` deadline, rather than being spent twice.
- `stop()` puts `_STOP` past the semaphore deliberately, and `_free()` skips `_STOP` for the same reason. Shutdown must not queue behind the backlog it is ending.
- `put()` re-checks `self.error` after the permit wait, since that wait can outlast the thread, and releases the permit on any failure out of the enqueue.

Two things worth knowing:

A producer already blocked waiting for a permit is not covered by the `WorkerDead` check — it passed that check before it blocked. If the thread then dies, `_abandon()` releases the backlog's permits, the producer wakes and puts into a queue nobody drains. Its *next* `put()` raises. Same shape as the window `_abandon()` already had, one step earlier in the call.

`stop(drain=True)` has the same edge for a different reason: the backlog ahead of `_STOP` is processed, permits come back, and a producer waiting on one wakes up after the thread has already exited. If you stop from one thread while another is still producing, expect that last item to be silently orphaned. `join()` before `stop()` avoids it.

`max_in_flight` and `maxsize` compose but overlap — `max_in_flight <= maxsize` makes `maxsize` unreachable, since a permit is always the scarcer resource.
