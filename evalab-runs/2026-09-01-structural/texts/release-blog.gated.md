# Norn 2.0 is out

Two years ago Norn was a thin wrapper over `requests` with retry logic bolted on. It worked. It also made you write `client.get("/v1/users", params={...})` and hope the response shape hadn't drifted since the last deploy.

2.0 changes the middle layer.

Endpoints are now generated from your OpenAPI spec at install time, so `client.users.list(status="active")` is a real method with a real signature, and your editor knows what comes back. Mistype a filter and you find out before the request leaves the machine. The other big change is async, and every method now has an `await`-able twin under `norn.aio`, sharing the same connection pool and the same retry policy, so there's no second client to configure.

Smaller things worth knowing:

- Retries respect `Retry-After` instead of guessing with exponential backoff.
- Pagination is an iterator. `for user in client.users.list():` walks every page.
- Errors carry the response body. `err.body` is parsed JSON, not a truncated string in the message.
- Median request overhead dropped from 4.1 ms to 1.3 ms, mostly by not re-parsing the spec per call.

Two things break. Python 3.8 support is gone, and the `Client(base_url=...)` positional argument is now keyword-only. Anything under `norn.legacy` was removed rather than deprecated, because nobody in the download stats appeared to be importing it. The migration guide covers the rest, including a `norn migrate` command that rewrites the common call patterns for you.

1.x gets security fixes through June 2027.

`pip install --upgrade norn`
