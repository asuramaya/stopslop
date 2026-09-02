# Version 2.0 is out

We rewrote the client from the request layer up. The old version wrapped `requests` and blocked on every call. The new one runs on `httpx` and gives you both a sync and an async client from the same interface.

Retries now happen inside the client, which is the first thing you will notice. You configure them once when you build the client, and the client honors `Retry-After` headers on 429 and 503 responses. Version 1.x left that to you.

Pagination returns an iterator, so instead of pulling a `next_cursor` out of the response and passing it back yourself, you write `for record in client.orders.list()` and the client fetches pages as you consume them. Every response object is typed. We generate the models from our OpenAPI spec, so your editor autocompletes field names and mypy catches typos before you ship them.

Two breaking changes. `Client(api_key=...)` no longer accepts a positional key, and the `timeout` argument moved from per-method to the constructor. Both raise clear errors rather than failing at runtime, and the migration guide covers the rest. We kept 1.x on the release branch and will patch security issues there through March 2027, so nothing forces you to move today.

Install it:

```
pip install apiclient==2.0.0
```

Kavi and Dorotea did most of the async work over the past four months. About thirty people on the beta filed issues that shaped the final API. If something breaks for you, open an issue with the traceback and we will look at it.
