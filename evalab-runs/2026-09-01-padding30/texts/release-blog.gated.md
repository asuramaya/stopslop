Here's the post. I used **Halyard** as a stand-in name and invented the version specifics — swap in your real numbers and API names.

---

# Halyard 2.0

Halyard started as a thin wrapper one of us wrote on a Friday afternoon. Then it turned up in other people's production code, which was flattering right up until the Friday-afternoon decisions started to hurt. 2.0 pays that debt off.

**Async is native.** No more `run_in_executor` gymnastics. `AsyncHalyard` shares the same method signatures as the sync client, so porting is mostly a matter of adding `await` and changing one import. Both clients now pool connections by default; a tight loop of 500 calls against our staging API dropped from 41 seconds to 6.

**Retries got opinions.** The old `retry=True` flag retried everything, including the 400s that were never going to succeed. Now retries are idempotency-aware and back off with jitter, and you can pass a policy object if ours annoys you.

**Errors carry the response.** `HalyardError` exposes `.status`, `.body`, and `.request_id` instead of collapsing everything into a string. Small thing. It'll save you an afternoon eventually.

Some breaking changes were unavoidable. `Client.call()` is gone in favor of the per-resource methods, config moved from keyword soup to a `Config` dataclass, and Python 3.8 is no longer supported. The migration guide covers all of it, and `halyard migrate` will rewrite the mechanical parts of your codebase for you.

1.x gets security fixes through next June. After that, it's on its own.

```
pip install --upgrade halyard
```

Bug reports welcome. Complaints about the retry defaults, especially.
