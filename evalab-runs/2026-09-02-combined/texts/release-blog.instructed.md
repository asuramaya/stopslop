# Fetchling 2.0

Fetchling 2.0 is out on PyPI today. The headline change is that retries, timeouts, and rate limiting now live in a single middleware stack instead of being scattered across constructor keyword arguments.

In 1.x, a client with retry logic and a custom auth refresh took about forty lines of subclassing, and the ordering between the two was undefined. You can now write it as a list:

```python
client = Fetchling(
    base_url="https://api.example.com",
    middleware=[BearerAuth(refresh=get_token), RetryAfter(max_attempts=4), Timeout(10)],
)
```

Middleware runs outer to inner on the request and inner to outer on the response, so auth refresh sees the 401 before the retry layer decides whether to try again. That was the ordering most people wanted in 1.x and could not express.

Async support is no longer a separate package. `fetchling.AsyncFetchling` shares the middleware types with the sync client; only the transport differs. If you were on `fetchling-aio`, the migration is an import change plus removing the dependency.

Two breaking changes. `Client.request()` no longer accepts `retries=`, `backoff=`, or `timeout=` directly, and response bodies are now lazily decoded, so `resp.json()` raises at call time rather than at request time. The migration guide covers both, and `fetchling migrate` rewrites the common constructor patterns for you.

Python 3.9 support is dropped. The minimum is 3.10.

Install with `pip install -U fetchling`. Changelog and migration guide are in the docs. Issues and regressions go to the tracker.
