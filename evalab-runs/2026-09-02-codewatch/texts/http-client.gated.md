This already exists in your working tree: `json_get.py` (untracked, 51 lines) is exactly that wrapper — `get_json(url, timeout=10.0, headers=None, retry_delay=0.5)` over `urllib.request`, one retry on 5xx or a connection failure, no retry on 4xx, body decoded with the response's charset and parsed as JSON.

I ran it against a throwaway local server rather than write a duplicate:

- plain 200 → parsed dict
- 503 then 200 → returns on the second attempt
- 404 → raises `HTTPError` after exactly one request

Want me to change anything about it — e.g. retry on 429 too, honor `Retry-After`, or cap the response size — or add a test file for it? Note `retry.py` in the same directory is a general backoff decorator; `json_get.py` deliberately does its own two-attempt loop instead of using it, since it needs to inspect the status code.
