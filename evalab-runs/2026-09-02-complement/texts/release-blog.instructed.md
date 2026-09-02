# Version 2.0 of the client library

Version 2.0 is out. The headline change is that every request now returns a typed response object instead of a raw dictionary, so a typo in a field name fails at type-check time rather than three functions later in production.

We also rewrote the retry layer. In 1.x, retries were controlled by two flags that interacted in ways nobody could predict from reading the docs. There is now one `RetryPolicy` object you pass to the client, and the default policy retries on 429 and 5xx with exponential backoff capped at 30 seconds.

Pagination changed shape. `list_items()` returns an iterator that fetches pages lazily; you can loop over it without holding the whole result set in memory. If you want the old behaviour, `list(client.list_items())` does the same thing 1.x did.

Async support is no longer a separate package. `AsyncClient` lives in the main library and shares the same method signatures as the sync client, which means the two implementations can no longer drift apart the way they did between 1.4 and 1.7.

Breaking changes, in short: dict responses are gone, the `retry_count` and `backoff` arguments are gone, and Python 3.8 is no longer supported. The migration guide walks through each one with before-and-after code, and a codemod handles the response-access rewrites for most codebases.

Install with `pip install apiclient==2.0.0`. The 1.x line gets security fixes for six months.
