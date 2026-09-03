Version 2.0 of the client library is out. It's a rewrite of the transport layer, and it changes a few things you'll notice right away.

The old client opened a new connection for every request. That was fine at low volume and slow everywhere else. 2.0 pools connections and reuses them across calls, which cuts median latency by about 40% in our benchmarks against the same endpoints.

Retries are built in now. Requests that fail with a 429 or a 5xx back off automatically, with jitter, up to a limit you configure with `max_retries`. Previously you had to wrap every call in your own retry loop; you can delete that code.

Error handling is stricter. In 1.x, a malformed response could silently return `None`. In 2.0, it raises `ClientResponseError` with the status code and body attached, so failures show up where they happen instead of three functions later.

The biggest breaking change: `Client.request()` no longer accepts positional arguments for headers and params. Pass them as keyword arguments, or the call raises `TypeError`. The migration guide has a script that rewrites most call sites automatically.

Async support is new. `AsyncClient` mirrors the sync API method for method, so switching a project over is mostly a matter of adding `await` and running it under an event loop.

1.x is still on PyPI and will get security patches through the end of the year. After that, upgrade.

Install with `pip install --upgrade apiclient`. The migration guide is linked from the README, and it covers each breaking change with a before-and-after example.
