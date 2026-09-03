We shipped version 2.0 of the client library today. It's on npm now as `@company/api-client@2.0.0`.

The rewrite started because the 1.x request pipeline built a new HTTP connection for every call. Under load, that meant socket exhaustion and retries that made things worse. Version 2.0 pools connections by default and reuses them across requests, which cut median latency by about 40% in our own load tests.

We also changed how errors surface. Previously, a failed request threw a generic `APIError` regardless of cause, and you had to inspect the message string to figure out what went wrong. Errors now carry a specific type. A `RateLimitError` includes `retryAfter`. An `AuthenticationError` fires on bad or expired credentials. A `ValidationError` includes the field-level messages the server returned. A `NetworkError` covers connection failures. Each type carries the fields relevant to handling it.

Pagination is automatic. Call `client.list()` and iterate with a `for await` loop; the library fetches the next page when you cross the boundary, instead of you managing cursor tokens by hand.

This is a breaking release, and the constructor signature changed as part of it: `new Client(apiKey, options)` replaces the old options-object-only form. Retry configuration moved from `options.retry` to `options.retryPolicy`, and the shape changed to match the new typed errors. The migration guide in the repo walks through both changes with before-and-after examples. Budget real time for this migration if you have retry logic that inspects error messages directly, since that logic will need to switch to checking error types instead.

1.x will get security patches through the end of the year, then it's done. If you're on 1.x, start the migration now rather than waiting for the deprecation window to close.
