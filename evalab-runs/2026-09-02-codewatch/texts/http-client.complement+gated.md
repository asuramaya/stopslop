```python
"""Minimal JSON-over-HTTP GET helper built on urllib."""

import json
import time
import urllib.error
import urllib.request


class HTTPError(Exception):
    """Raised when the server answers with a status we will not parse."""


def get_json(url, timeout=10.0, headers=None, retry_delay=0.5):
    """GET *url* and return the decoded JSON body.

    One retry is attempted if the first response is a 5xx, since those are
    usually transient. A 4xx is raised immediately.
    """
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    last_error = None
    for attempt in range(2):
        request = urllib.request.Request(url, headers=request_headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                raise HTTPError(f"{url} returned {exc.code}") from exc
            last_error = exc
        except urllib.error.URLError as exc:
            raise HTTPError(f"{url} unreachable: {exc.reason}") from exc

        if attempt == 0:
            time.sleep(retry_delay)

    raise HTTPError(f"{url} returned {last_error.code} twice") from last_error


if __name__ == "__main__":
    import sys

    print(json.dumps(get_json(sys.argv[1]), indent=2))
```
