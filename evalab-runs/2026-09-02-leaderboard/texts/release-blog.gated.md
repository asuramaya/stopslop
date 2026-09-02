# hitch 2.0

Two years and 340 issues later, hitch 2.0 is out.

The headline change is that retries are no longer a footgun. In 1.x, `retry=True` meant "try three times, 200 ms apart, forever, on every status code," which cost one of our users about $4,000 in duplicate charges against a payments API. 2.0 ships a `RetryPolicy` object instead. You state which methods are idempotent, which status codes are worth another attempt, and a budget. Nothing retries by default.

Connection handling was rewritten on top of a shared pool. A 200-request benchmark against a local echo server went from 3.1 s to 0.9 s, mostly because 1.x opened a fresh TLS session per call. Memory under sustained load is flat now; it used to climb about 8 MB a minute. The async and sync clients finally share one code path too — `Client` and `AsyncClient` have identical method signatures, generated from the same source, so the docs stop lying about one of them.

Some things break, and I won't dress it up. `Client(url, **kwargs)` no longer swallows unknown keyword arguments — it raises. `response.json` is a method again, not a property. Python 3.8 is gone. Full list in [MIGRATION.md](./MIGRATION.md), and `hitch-migrate` will rewrite most call sites for you. Middleware is the thing we left on the floor: people asked, we prototyped it twice, and both versions made stack traces unreadable. It stays out until someone finds a design that doesn't.

```
pip install hitch==2.0.0
```

Bugs to the tracker. 1.x gets security fixes through March 2027.
