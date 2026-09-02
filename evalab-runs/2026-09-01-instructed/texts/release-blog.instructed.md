# Version 2.0 of the client library

Version 2.0 is out. The change that drove the release: every call now returns a typed result object instead of a raw dictionary, so a typo in a field name fails at type-check time rather than three functions later in production.

The retry logic was rewritten. In 1.x, retries were configured globally and applied to every request, including non-idempotent ones. That was a mistake we heard about from users who saw duplicate POSTs. Retries are now per-method, default to idempotent verbs only, and honor `Retry-After` headers instead of ignoring them.

Connection pooling moved to a single shared pool with a configurable ceiling. Under the old per-client pools, an application that created a client per request could exhaust file descriptors within an hour. The new default caps at 100 connections and raises a clear error when the pool is saturated, rather than blocking forever.

Async support is no longer a separate package. `AsyncClient` lives alongside `Client` and shares the same method signatures, so porting a synchronous call site means changing the constructor and adding `await`.

Breaking changes: Python 3.9 is the minimum version, `client.request()` no longer accepts positional arguments after the URL, and the `verbose` flag is replaced by standard `logging` configuration. The migration guide covers each one with before-and-after code.

Two deprecated modules from 1.4 have been removed: `compat` and `legacy_auth`. If you still import either, pin to 1.x until you can move off them.

Install with `pip install apiclient==2.0.0`. Issues and questions go to the tracker.
