# Version 2.0 of the client library is out

The rewrite took eight months. The headline is that the client no longer holds a thread while it waits on the network. Every method has an async variant, and the sync methods are now thin wrappers over the same transport rather than a separate code path that drifted out of sync with it. If you were pinning to 1.x because the async support in 1.7 was bolted on, this is the release to move to.

Retries changed shape. The old client retried on any 5xx with a fixed 200ms backoff, which was a reliable way to make an outage worse. 2.0 uses exponential backoff with jitter, respects `Retry-After` when the server sends it, and refuses to retry non-idempotent requests unless you pass an idempotency key. Defaults are 3 attempts, capped at 30 seconds total. That cap is configurable per client, and per request when you need to override it for a slow endpoint.

Pagination is now an iterator. `client.users.list()` returns something you can loop over directly, and it fetches the next page when you reach the end of the current one.

Three things break. The `timeout` argument is now a struct with separate connect and read fields. Error types moved out of the top-level namespace into `errors`. And we dropped Python 3.8, which went end-of-life in October 2024. The migration guide covers each one with before-and-after code, and most projects we tested against needed under twenty lines of changes.

Install with `pip install apiclient==2.0.0`. 1.x gets security fixes through March 2027.
