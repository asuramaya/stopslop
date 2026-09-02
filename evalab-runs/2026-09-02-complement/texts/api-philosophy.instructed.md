## Design philosophy

Every endpoint returns a resource, and every resource has an identifier you can store indefinitely. We do not recycle IDs or renumber them during migrations.

Versioning lives in the URL, not a header. `/v2/orders` behaves in 2030 the way it behaves today; when behavior has to change, we ship `/v3` and keep `/v2` serving traffic for at least 24 months past the deprecation notice.

Errors carry a machine-readable code, the field that triggered them, and a link to the page that explains the code. You never need to parse an error string. If the code alone is not enough to act on, that is a defect on our side.

Writes are idempotent whenever you supply an `Idempotency-Key`. Retrying after a timeout is safe: the second call returns the first call's stored response instead of creating a duplicate order.

Defaults favor the common case over the flexible one. Pagination is on at 50 items per page, timestamps are UTC in RFC 3339, and monetary amounts are integers counting the currency's smallest unit. The page size is yours to change. The other two are fixed, because every format we allowed in v1 became a class of bug someone else had to debug.
