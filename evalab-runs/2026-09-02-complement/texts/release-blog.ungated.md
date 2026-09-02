You didn't name a library, so I invented one — Skiff, a Python client — with concrete version details. Swap the names and numbers for your real ones. 241 words, and it passes this project's own slopwatch gate clean.

---

# Skiff 2.0 is out

Skiff 2.0 landed on PyPI this morning. It rewrites the transport layer, and it breaks two things on purpose.

The big change is async. Version 1.x wrapped a thread pool and called it concurrency. 2.0 sits on httpx, so `await client.users.list()` does what you expect, and the synchronous client is a thin shim over the same code. Both share a connection pool. On 500 sequential calls against a local mock server, wall time went from 11.4s to 2.1s.

Responses are typed now. Every endpoint returns a dataclass generated from the OpenAPI spec instead of a dict. Your editor autocompletes field names and mypy catches the ones you got wrong. If you liked dicts, call `.to_dict()`.

The breaking changes are small but real. `Client(token=...)` becomes `Client(auth=BearerAuth(...))`, because three auth schemes shipped in the last year and one keyword argument could not hold them. Retries moved from a global setting to a per-request `retry=` parameter, which defaults to three attempts on 429 and 5xx. The old names raise a `DeprecationWarning` through the 2.x line and go away in 3.0.

To migrate, install version 2.0 and run `skiff-migrate` over your tree. It rewrites the constructor calls and flags the retry settings it cannot translate. For most projects that is the whole job.

Thanks to the thirty-odd people who filed issues against the 2.0 betas, and to whoever reported the connection leak on the second day. That one was ugly.

---

Draft is at `/tmp/skiff2.md` if you want to edit it in place. Tell me the real library and I'll refit the specifics.
