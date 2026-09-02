# Client 2.0 is out

Version 2.0 is on PyPI this morning. It replaces the transport layer, and it will break code written against 1.x.

Every method is now async. The old version opened a fresh connection per call, which was fine for scripts and terrible for anything serving traffic. The new client holds a pooled session, so a hundred concurrent calls share about eight sockets instead of a hundred. In our benchmark against a local mock server, throughput went from 240 requests per second to roughly 3,100.

Responses come back as typed objects rather than dictionaries. If your editor knows about the library, it now knows that a customer record has an `email` field and a `created` field that is a datetime, not a string you have to parse yourself. We generate these from the OpenAPI spec, so they track the API.

Retries are built in. Pass `max_retries` to the constructor and the client backs off exponentially on 429 and 5xx, honoring the `Retry-After` header when the server sends one. Previously you wrote that loop.

Three things break. The synchronous `Client` class is gone, replaced by `AsyncClient`. Pagination returns an async iterator instead of a list, so `for page in results` becomes `async for page in results`. The `timeout` argument now takes seconds as a float rather than milliseconds as an integer, which we regret changing but could not leave inconsistent with the rest of the ecosystem.

We wrote a migration guide covering each of these with before-and-after code. Version 1.x gets security fixes through March 2027.
