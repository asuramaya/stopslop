```python
"""Minimal JSON GET helper built on urllib."""

import json
import logging
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0


class HttpError(Exception):
    """A non-2xx response that we did not recover from."""

    def __init__(self, status, url, body):
        super().__init__(f"GET {url} failed with {status}")
        self.status = status
        self.url = url
        self.body = body


def _attempt(request, timeout):
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def get_json(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """GET `url` and return the decoded JSON body.

    A 5xx response is retried once; 4xx and transport errors are raised
    immediately as HttpError and URLError respectively.
    """
    request = urllib.request.Request(url, headers=headers or {}, method="GET")

    for remaining_retries in (1, 0):
        try:
            return _attempt(request, timeout)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            if error.code < 500 or not remaining_retries:
                raise HttpError(error.code, url, body) from error
            log.warning("GET %s returned %s, retrying once", url, error.code)
```
