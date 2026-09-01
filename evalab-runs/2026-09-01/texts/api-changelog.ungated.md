## v3.0.0

**Breaking changes.** Read this before you upgrade.

### Removed

`GET /v1/users/{id}/friends` is gone. It returned the entire friend list in one unbounded array, which meant a 40-second response for accounts past about 50,000 friends. There is no deprecation window; v1 of this endpoint stopped serving on release day.

### Added

`GET /v2/users/{id}/connections` replaces it. The response is paginated: pass `?limit=` (default 50, max 500) and `?cursor=`, and read the next cursor from `page.next_cursor` in the body. When `page.next_cursor` is `null`, you have the last page. The old top-level array is now nested under `data`.

The rename is not cosmetic. A connection carries a `status` field (`accepted`, `pending`, `blocked`), so what used to be an implicit "these are friends" list now tells you what kind of relationship each row represents. Filter with `?status=accepted` to get the old semantics.

### Changed

Every date field across the API is now an ISO 8601 string in UTC — `"2026-03-14T09:21:00Z"` instead of `1773479660`. This affects `created_at`, `updated_at`, and `last_seen_at` on all resources, not only the connections endpoints. If you were doing arithmetic on raw integers, parse first.

### Migration

Point clients at `/v2`, loop on the cursor, and swap your timestamp parser.
