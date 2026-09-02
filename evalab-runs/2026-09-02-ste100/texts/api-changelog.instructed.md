# Version 3.0

## Removed: `/v1/users/{id}/friends`

We deleted this endpoint. It is gone, not deprecated. Calls to it now return 410 Gone with a pointer to the replacement. The old endpoint returned every friend in one array, which broke for accounts past a few thousand records, and we could not fix that without changing the response shape anyway.

## Added: `/v2/users/{id}/connections`

The replacement returns a page at a time. Each response carries a `data` array, a `next_cursor` string, and a `has_more` boolean. Pass `next_cursor` back as the `cursor` query parameter to fetch the following page. Default page size is 50, and the maximum is 200 through the `limit` parameter.

The record shape changed too. What v1 called a friend, v2 calls a connection, and a connection now carries a `status` field with the values `pending`, `accepted`, or `blocked`. The v1 endpoint only ever returned accepted friendships. If you want the old behavior, filter on `status=accepted`.

## Dates are now ISO 8601

Every date field across the API returns an ISO 8601 string in UTC, for example `2026-09-02T14:30:00Z`. Unix timestamps are no longer returned anywhere. If your client does arithmetic on the raw integer, parse the string first.
