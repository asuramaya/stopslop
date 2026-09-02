# Design Philosophy

This API moves records between your system and ours without surprising you.

Every endpoint returns the same envelope. A `data` field holds the result, a `meta` field holds pagination and rate-limit state, and an `errors` array is either absent or populated. You can write one response handler and reuse it everywhere.

Errors carry a stable machine-readable code alongside human-readable text, so you can branch on the code and log the text.

We version at the URL path. Old versions stay live for eighteen months after a successor ships. Within a version, we add fields but never remove or retype them. Treat unknown fields as ignorable and your client will survive our release cycle.

Writes are idempotent when you send an idempotency key. Retry a timed-out request with the same key and you get the original response, not a duplicate record. We keep keys for twenty-four hours.

We chose predictability over cleverness in a few places you may notice. Pagination is cursor-based, so page three stays stable while rows are inserted underneath it. Timestamps are always UTC with an offset, and money is an integer of minor units plus a currency code, never a float. These are the choices most likely to bite you late, so we made them boring on purpose.

When we get something wrong, the changelog says so and names the fix.
