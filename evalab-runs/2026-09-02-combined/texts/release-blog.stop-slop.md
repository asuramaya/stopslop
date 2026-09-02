# Version 2.0 of the client is out

We rewrote the request layer. The old client held one connection per instance and serialized calls behind a lock, which meant a batch job spent most of its wall clock waiting. The new one pools connections and lets you fire concurrent requests against a single client object. In our own batch importer, a 4,000-record sync dropped from 19 minutes to 3.

Retries changed too. Version 1.x retried on any non-2xx response, which sometimes hammered a server that had already told us to stop. Now the client reads `Retry-After`, backs off exponentially with jitter, and skips retries entirely on 4xx codes other than 408 and 429. You can swap in your own policy by passing a `RetryPolicy` object to the constructor.

Two breaking changes to plan for. `Client.get()` returns a `Response` object instead of a raw dict, so `resp["items"]` becomes `resp.data["items"]`. And we dropped Python 3.8, which reached end of life last October. The migration guide lists a `codemod` script that handles the first change across a codebase in one pass.

Type hints now cover the whole public surface. If you run mypy in strict mode, the client will stop being the thing you have to ignore.

We shipped this after six months of running it inside our own services, so the rough edges you would have hit in a fresh rewrite are mostly sanded down. Install with `pip install apiclient==2.0.0`. Bugs go to the issue tracker; Marcus watches it daily and usually answers within a day.
