`json_get.py` — 51 lines:

- `get_json(url, timeout=10.0, headers=None, retry_delay=0.5)` builds a `Request` with `Accept: application/json`, opens it with a per-attempt timeout, and decodes the body using the charset from the response headers (falling back to utf-8).
- Two attempts max. A `HTTPError` with `code >= 500` or a connection-level `URLError` (which is also what a timeout surfaces as) sleeps `retry_delay` and tries again; 4xx raises immediately since repeating it won't help. The second attempt's error propagates.

Smoke-tested against a throwaway local server: a 503-then-200 endpoint returned the parsed dict after 2 hits, and a 404 raised after a single hit.
