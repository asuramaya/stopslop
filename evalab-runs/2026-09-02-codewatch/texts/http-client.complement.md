```python
import json
import time
import urllib.error
import urllib.request


class HTTPStatusError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


def _attempt(url, headers, timeout):
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def get_json(url, headers=None, timeout=10.0, retry_delay=0.5):
    """GET `url` and return the decoded JSON body.

    One retry is made when the server answers 5xx or the socket times out.
    Raises HTTPStatusError on a final non-2xx response, ValueError on a body
    that is not JSON, and urllib.error.URLError on an unrecoverable transport
    failure.
    """
    headers = dict(headers or {})
    headers.setdefault("Accept", "application/json")

    for attempt in range(2):
        last_attempt = attempt == 1
        try:
            status, body = _attempt(url, headers, timeout)
        except (urllib.error.URLError, TimeoutError):
            if last_attempt:
                raise
            time.sleep(retry_delay)
            continue

        if 500 <= status < 600 and not last_attempt:
            time.sleep(retry_delay)
            continue
        if not 200 <= status < 300:
            raise HTTPStatusError(status, body)
        return json.loads(body.decode("utf-8"))
```
