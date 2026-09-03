Design philosophy

Every endpoint maps to one resource and one HTTP verb combination. If you can guess the URL before reading the docs, we did our job.

We chose synchronous responses over webhooks wherever the operation completes in under a second. Webhooks add a second system to monitor and a retry policy to get wrong. We only use them for operations that take minutes, like batch exports.

Errors return the field that failed and the constraint it violated, not a generic 400. A client parsing `error.field` and `error.constraint` can build its own validation without querying us first.

We version the API by date, not by number. `2026-03-01` tells you what the API looked like on that day; `v3` tells you nothing without a changelog open in another tab. Old date versions stay live for at least eighteen months after a newer one ships.

Pagination uses cursors, not page numbers. Page numbers break the moment a row is inserted between two requests; cursors don't.

Rate limits are per API key, not per IP, because IPs move behind shared NATs and proxies. The limit and remaining count ride in response headers on every call, not just the one that gets throttled, so you can back off before you hit the wall.
