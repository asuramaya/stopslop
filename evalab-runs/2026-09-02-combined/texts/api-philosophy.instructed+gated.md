# Design philosophy

This API is built around a small number of nouns and a fixed set of verbs. If you know what a `Job` is, you can guess what `GET /jobs/{id}` returns, and you will be right. We would rather add a field to an existing resource than invent a new endpoint, so the surface you learn on day one is close to the surface you are still using a year later.

Everything is explicit. There are no defaults that change based on your account tier, no fields that appear only under certain conditions, and no responses that alter shape depending on how much data matched. An empty result is an empty array, not a null and not a 404.

Writes are idempotent. Every mutating call accepts an `Idempotency-Key` header, and we store the result for 24 hours, so a retry after a timeout returns the original response rather than creating a second charge.

We version at the URL root. Old versions keep running for 18 months after a successor ships, and deprecations reach you three times before anything breaks: a `Sunset` header on live responses, then email, then removal.

Errors carry a machine-readable `code`, a human-readable `message`, and, where a specific field caused the failure, a `path` pointing at it. The message text may change between releases. The code will not.
