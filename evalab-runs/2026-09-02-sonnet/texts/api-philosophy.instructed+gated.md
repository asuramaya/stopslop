Every endpoint returns the same shape whether it succeeds or fails: a `data` field or an `error` field, never both, never neither. Client code checks one thing.

Resources map to nouns, actions map to HTTP verbs. There is no `/getUser` or `/createOrder`. There is `GET /users/{id}` and `POST /orders`. If an operation cannot be expressed this way, the resource model needs rethinking.

Versioning lives in the URL path (`/v1/`, `/v2/`), not in headers or query params. A version is visible in every log line and every curl command without extra flags.

We add optional fields to responses without bumping the version. We never remove or repurpose a field without one. Old integrations keep working after we ship new ones.

Pagination uses cursors, not page numbers. Page numbers break when rows are inserted or deleted between requests.

Rate limits are enforced per API key and reported in response headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`) on every call, not just the ones that get throttled. Callers can back off before they hit the limit.

Each documentation page starts with a working request and its exact response, not a schema definition.
