No library was named, so I invented one — swap the names and specifics for yours.

---

# Halyard 2.0

Halyard 1.0 shipped in 2023 with one job: wrap a REST endpoint in something you could call without reading the docs twice. Two years and about 400 issues later, we've rewritten the core.

The big change is the transport layer. Every request now goes through one path, and that path is async underneath. Sync callers get a thin blocking shim, so `client.get("/users")` behaves exactly as it did. But if you `await` it, you get real concurrency — 200 in-flight requests sharing a connection pool instead of one thread apiece.

Retries changed too. 1.x retried on any exception, which meant a typo in your JSON body got retried five times before it failed. 2.0 retries on status codes and connection errors only, with jittered backoff, and you can hand it your own predicate.

Pagination is no longer your problem. Endpoints that return a cursor now come back as an iterator that fetches the next page when you exhaust the current one.

What broke:

- `Client(base_url=...)` is positional now.
- The `timeout` float is gone. Pass a `Timeout` with separate connect and read values.
- `response.json` is a method again, not a property. That was our mistake in 1.4 and we're taking it back.

The migration guide lives in `MIGRATING.md`, and `halyard-codemod` handles the mechanical parts — imports, the timeout change, the `.json` call sites. 1.x keeps getting security patches until March 2027.

```
pip install halyard==2.0.0
```
