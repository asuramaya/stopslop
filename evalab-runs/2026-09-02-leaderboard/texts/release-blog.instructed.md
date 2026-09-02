# Announcing 2.0

The client library is at 2.0 today. The headline change is that every method now returns a typed response object instead of a raw dictionary, so a typo in a field name fails at import time rather than three hours into a batch job.

Retries are the other big shift. The 1.x client retried on any non-2xx status with a fixed 500ms delay, which turned a brief rate limit into a thundering herd. 2.0 respects the `Retry-After` header, backs off exponentially with jitter, and by default gives up after four attempts. You can swap in your own policy by passing a `RetryPolicy` to the constructor.

Connection pooling moved from a per-call session to a shared pool held by the client. In our benchmark of 10,000 sequential GETs against a local server, median latency dropped from 4.1ms to 1.3ms. Most of that was TLS handshakes we were paying for over and over.

Breaking changes, in short:

1. `Client.request()` returns `Response`, not `dict`. Call `.data` for the old behavior.
2. `timeout` is now a float in seconds everywhere. It used to be milliseconds in three methods and seconds in the rest.
3. Python 3.8 support is dropped. The typing features 2.0 relies on landed in 3.9.
4. The `verbose` flag is gone. Configure the `apiclient` logger instead.

A migration script that handles the first two mechanically ships in `tools/migrate_v2.py`. It covers the common call shapes and leaves a comment where it isn't sure.

Install with `pip install apiclient==2.0.0`. The 1.x branch gets security fixes through March 2027.
