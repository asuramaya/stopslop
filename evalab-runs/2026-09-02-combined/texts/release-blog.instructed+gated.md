# Apiary 2.0 is out

Apiary 2.0 drops today. The headline change is that request retries are now configurable per endpoint instead of per client, which is what most of the GitHub issues on the 1.x tracker were actually asking for.

In 1.x, you set a retry policy once at construction and every call inherited it. That worked until you had one endpoint that tolerated three retries and another that was a payment write and tolerated zero. People worked around it by building two clients. Now you pass a policy to the call itself, and the client-level setting is the default when you don't.

The other significant change is that responses stream by default. A 400 MB export used to sit in memory until it finished; now you iterate over chunks and peak memory stays flat. Existing code that reads `response.body` still works, though it buffers, so the old behavior is one property access away if you want it.

Two things broke. `Client(timeout=)` now takes seconds as a float rather than milliseconds as an int, because half the bug reports we got were people passing 30 and waiting 30 milliseconds. And the deprecated `.request_raw()` method is gone; use `.request(parse=False)`.

Migration for a typical codebase is under an hour. The upgrade guide lists every rename, and `apiary-migrate` rewrites the timeout calls for you.

Python 3.9 support ends with this release. 1.x keeps getting security patches through June 2027, so there's no rush if you're pinned.

Install with `pip install apiary==2.0.0`. Changelog and upgrade guide are in the docs.
