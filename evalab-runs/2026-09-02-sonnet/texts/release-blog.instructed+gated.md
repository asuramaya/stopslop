We shipped version 2.0 of the API client library today. The rewrite touches the transport layer, the retry logic, and the type definitions, and it breaks compatibility with 1.x in three places.

The client now uses a single HTTP connection pool instead of opening a new connection per request. On a benchmark of 10,000 sequential calls against our staging API, that cut median latency from 340ms to 190ms. Retries now use exponential backoff with jitter and respect a `Retry-After` header when the server sends one; 1.x retried on a fixed 500ms interval regardless of what the server asked for.

Three breaking changes. The `Client` constructor now takes an options object instead of positional arguments — `new Client({apiKey, timeout})` instead of `new Client(apiKey, timeout)`. Error responses are now instances of typed subclasses (`RateLimitError`, `AuthError`, `NotFoundError`) rather than a generic `ApiError` with a `.code` string. And the deprecated `client.fetch()` alias, which we kept around since 1.2, is gone; use `client.request()`.

Every public method now has a generated TypeScript signature pulled from the OpenAPI spec, so autocomplete matches the actual API surface instead of hand-maintained `.d.ts` files that drifted out of sync.

Migration guide and a codemod that handles the constructor and error-class changes are in the repo under `/migrations/v2`. The codemod covers about 90% of the diff in our own internal callers; the rest was renamed error handling we did by hand.

1.x gets security patches through March 2027 and no new features. Install with `npm install client@2.0.0`.
