Passes slopwatch clean, 184 words.

## 3.0.0

### Breaking changes

**Removed `GET /v1/users/{id}/friends`.** The route is gone, not deprecated. Requests to it return `410 Gone` with a `Link` header pointing at the replacement. The rest of `/v1` stays up; only this route was cut.

**Added `GET /v2/users/{id}/connections`.** The replacement returns a paginated envelope instead of a bare array:

```json
{
  "data": [ ... ],
  "page": { "next_cursor": "c2Vjb25k", "has_more": true }
}
```

Page size defaults to 50 and caps at 200 through `?limit=`. Pass `?cursor=` to walk forward. Clients that read the old top-level array must read `data` instead.

**All dates are now ISO 8601.** Every field that carried a Unix timestamp — `created_at`, `updated_at`, `last_seen_at`, and their equivalents on every other resource — now carries a string like `2026-09-01T14:32:07Z`, always UTC, always with the `Z` suffix. Integer timestamps are rejected on write too: send ISO 8601 or get a `400`.

### Migration

Swap the URL, read `data` rather than the array root, and parse dates with your language's ISO 8601 parser instead of a seconds-to-date conversion. Cursors are opaque; do not decode them or build them yourself.

The cursor value, limit cap, and `410`-vs-`404` choice are placeholders — swap in whatever your implementation actually does.
