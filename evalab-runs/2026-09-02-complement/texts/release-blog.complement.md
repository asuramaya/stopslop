# Relay 2.0

Relay 2.0 is out today. The headline change: the transport layer is now async-first, and the synchronous client is a thin wrapper over it rather than a separate code path. One implementation to fix bugs in, one set of semantics for timeouts and retries.

Typed responses come next. If you point Relay at an OpenAPI document, `relay generate` writes dataclasses for every schema in it, and the client returns those instead of raw dictionaries. Your editor knows the shape of a response, and a renamed field breaks at import time instead of three calls later in production.

Retries got rebuilt. In 1.x, retry behavior lived in three places and disagreed with itself. Now there is one policy object you pass to the client, with per-status backoff, a jitter setting, and a hard ceiling on total elapsed time. Idempotency keys are attached automatically for POST requests when the server advertises support.

Connection pooling now defaults to per-host limits rather than a single global pool, which fixed the head-of-line blocking a few of you reported when talking to slow and fast hosts from the same process.

Two things break. Python 3.8 is no longer supported; the minimum is 3.10. And `Client.request()` returns a `Response` object rather than a parsed body, so calls that indexed the return value directly need a `.json()` added. The migration guide covers both, with a codemod for the second.

Install with `pip install relay==2.0.0`. The 1.x branch gets security fixes through June 2027. Bug reports and questions go to the issue tracker as usual.
