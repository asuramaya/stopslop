```python
import json
import time
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 10.0
RETRY_DELAY = 0.5


class HTTPError(Exception):
    """Raised when the server answers with a status we will not retry past."""

    def __init__(self, status, body):
        super().__init__(f"server returned {status}")
        self.status = status
        self.body = body


def _fetch(url, headers, timeout):
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def get_json(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """GET `url` and decode the body as JSON.

    One retry on a 5xx, then the error propagates. 4xx never retries --
    a bad request stays bad.
    """
    headers = headers or {"Accept": "application/json"}

    for attempt in range(2):
        try:
            status, body = _fetch(url, headers, timeout)
        except urllib.error.HTTPError as err:
            status, body = err.code, err.read()
            if status >= 500 and attempt == 0:
                time.sleep(RETRY_DELAY)
                continue
            raise HTTPError(status, body) from err

        return json.loads(body.decode("utf-8"))

    raise AssertionError("unreachable: the loop either returns or raises")
```
