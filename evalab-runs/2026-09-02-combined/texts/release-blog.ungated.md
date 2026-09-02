247 words, passes the slopwatch gate clean. I invented a library name (Ackerman) and the specifics since you didn't name one — swap them for the real ones.

---

# Ackerman 2.0 is out

Ackerman started as a thin wrapper over `requests` with a retry loop bolted on. That held up until people used it for things we had not planned for: hour-long uploads, streamed responses, three different services authenticated separately inside one process. Version 2.0 is the rewrite those users argued us into.

The headline change is async. The client now sits on `httpx`, and every method exists in both a blocking and an awaitable form, generated from the same schema so they cannot drift apart. If you are already using `asyncio`, you no longer need a thread pool to keep Ackerman from blocking your loop.

Retries moved out of the request path and into a policy object you pass to the constructor. The old behaviour retried any 5xx three times with a fixed delay, which was wrong for idempotent writes and too timid for rate limits. Now you say what you want, per status class, and the default respects `Retry-After`.

Pagination is an iterator instead of a callback. Errors carry the parsed response body rather than just a status code. Type hints cover the whole public surface, checked in CI against mypy strict.

Breaking changes are real. `Client(token=...)` becomes `Client(auth=BearerAuth(...))`, the `raw` keyword is gone, and Python 3.8 is no longer supported. The migration guide walks through each one, and `ackerman-migrate` rewrites the common call sites for you.

1.x gets security fixes through March 2027. Issues and questions go on the tracker as usual.
