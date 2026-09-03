Orbit 1.0 shipped three years ago as a thin wrapper around requests. It worked, but every new endpoint meant hand-written methods, and pagination bugs kept coming back in different forms.

Version 2.0 replaces that wrapper with a client generated from our OpenAPI spec, so the library and the API stay in sync automatically. Orbit now ships both `Client` and `AsyncClient` classes with matching method signatures, and switching between sync and async code means changing an import, not rewriting call sites. Under the hood we moved from requests to httpx, cutting median request latency by 40ms in our benchmarks.

Pagination is automatic now. Calling `client.list_users()` returns an iterator that fetches subsequent pages as you consume it, instead of returning a single page and leaving cursor handling to the caller. This was the single most common bug report against 1.x.

Error handling changed too. Every non-2xx response raises a typed exception (`NotFoundError`, `RateLimitError`, `ValidationError`) instead of a generic `HTTPError`, so callers catch specific failure modes without parsing status codes.

This is a breaking release. The old synchronous-only `Client.request()` method is gone. Retry configuration moved from environment variables to constructor arguments. The minimum supported Python version is now 3.9. A migration guide with a working diff for the most common usage patterns is in the docs.

Install with `pip install orbit-client==2.0.0`. Version 1.x gets security patches until March 2027.
