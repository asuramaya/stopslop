# Version 2.0 of the client library

We shipped 2.0 this morning. If you use the 1.x client, read this before you upgrade, because we broke things.

The biggest change: every method returns a typed response object instead of a raw dictionary. In 1.x you wrote `resp["data"]["items"]` and found out at runtime that the shape had changed. Now you write `resp.data.items` and your editor tells you when a field disappears. We generate these types from the API schema, so they track the server on each release.

Retries used to happen inside every method with a fixed three-attempt limit. Sarah on our team pulled that logic into a `RetryPolicy` you pass to the constructor once. You set the backoff, the jitter, and which status codes count as retryable. If you liked the old behavior, `RetryPolicy.legacy()` reproduces it.

Async support no longer lives in a separate package. `AsyncClient` sits next to `Client` in the same module and shares the transport layer, so a bug fix in one lands in both.

We dropped Python 3.8. The type work depends on features that arrived in 3.9.

The migration guide walks through each break with a before-and-after snippet. Most of our beta testers finished the upgrade in under an hour; the ones with heavy retry customization took longer.

1.x gets security patches through March 2027. After that we archive it.

Install with `pip install apiclient==2.0.0`. File issues on GitHub, and tell us if the migration guide misses a case you hit.
