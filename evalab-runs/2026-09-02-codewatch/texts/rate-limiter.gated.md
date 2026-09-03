`rate_limiter.py` already exists in your working tree (untracked, ~63 lines) and is exactly this — a thread-safe `TokenBucket` with `try_acquire`. Note there's another live agent on this repo, so it may not be yours.

I ran it rather than rewriting it. It passes: burst up to capacity, refusal when empty, continuous (not tick-based) refill, cap at capacity, and 200 threads racing for 100 tokens yield exactly 100 winners.

What's there:

- `TokenBucket(rate, capacity=None, clock=time.monotonic)` — injectable clock, so tests don't sleep
- `try_acquire(tokens=1)` → bool, all work under one `threading.Lock`
- `wait_time(tokens=1)` → seconds until the request would succeed
- `tokens` property, refilled as of the call

Two things I'd flag if you want changes:

- `try_acquire` raises on `tokens > capacity` instead of returning `False`. That's the right call (an unsatisfiable request is a bug, not backpressure), but `wait_time` doesn't do the same check — it returns a finite number for a request that can never succeed. Worth making consistent.
- `_refill` guards on `elapsed > 0`, so a non-monotonic injected clock going backwards freezes `_updated` rather than corrupting the count. Fine, just deliberate.

Say the word and I'll overwrite it with a fresh implementation, or patch the `wait_time` inconsistency.
