## 3.0

This release breaks clients. Plan for code changes before you upgrade.

### Removed: /v1/users/{id}/friends

The endpoint is gone rather than deprecated. Nothing answers at that path anymore, so a client that still calls it fails on its first request after the upgrade. The change leaves the rest of the /v1 tree alone. This path will not come back.

### Added: /v2/users/{id}/connections

The replacement covers the same ground, one user's connections, but it pages the results instead of returning the whole set at once. A response carries a page of connections plus what a client needs to ask for the page after it. Code that read the old response as one flat array of friends has to be rewritten around the envelope, and around a loop that walks pages until they run out.

### Dates are now ISO 8601

Timestamps in v2 responses are ISO 8601 strings, not integer Unix seconds. Anything that did arithmetic on the old numbers, or passed them straight to a date constructor, needs a parser now. Check log lines and cached records too: values your earlier code stored remain there in the old form.
