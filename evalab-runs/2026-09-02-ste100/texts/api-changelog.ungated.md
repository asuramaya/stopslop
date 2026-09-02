Here's the entry (207 words). It passes the project's own slopwatch gate.

```markdown
## 3.0

Breaking release. Read this before you upgrade.

`GET /v1/users/{id}/friends` is gone. It returned the full friend list in
one array, which worked until accounts crossed a few thousand entries and
then stopped working in a way we could not fix without changing the shape
of the response. So we changed the shape and gave it a new name.

The replacement is `GET /v2/users/{id}/connections`. It is paginated:
pass `limit` (default 50, max 200) and `cursor`, and read the next cursor
out of `meta.next_cursor`. When `meta.next_cursor` is null you are at the
end. Records live under `data` rather than at the top level, so a client
that did `response.map(...)` now needs `response.data.map(...)`.

Every date and time field across the API is now an ISO 8601 string in
UTC, for example `2026-09-02T14:30:00Z`. Previously these were integer
Unix timestamps. This applies everywhere, including fields you did not
ask us to change: `created_at`, `updated_at`, `last_seen_at`, and the
timestamps inside webhook payloads.

v1 was switched off on release day. There is no deprecation window,
because v1 was already returning errors on the accounts that mattered.
```

Two things I invented because you didn't specify them and a changelog is useless without them: the pagination parameter names and limits, and the sunset policy for v1. Swap in your real values.
