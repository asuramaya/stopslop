"""GET a URL and return the parsed JSON body, retrying once on a 5xx."""

import json
import time
import urllib.error
import urllib.request
from typing import Any


def get_json(
    url: str,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
    retry_delay: float = 0.5,
) -> Any:
    """Fetch `url` and decode the response body as JSON.

    The request is made at most twice: a 5xx status or a connection-level
    failure triggers one retry after `retry_delay` seconds. A 4xx status is
    not retried, since repeating the same request will not change it. The
    error from the final attempt propagates to the caller.

    Args:
        url: Absolute http or https URL.
        timeout: Seconds allowed for each individual attempt.
        headers: Extra request headers, merged over the default Accept.
        retry_delay: Seconds to wait before the second attempt.

    Raises:
        urllib.error.HTTPError: The server answered with an error status.
        urllib.error.URLError: The connection failed or timed out.
        json.JSONDecodeError: The body was not valid JSON.
    """
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers, method="GET")

    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except urllib.error.HTTPError as exc:
            # 4xx means the request itself is wrong; only 5xx is worth a retry.
            if attempt == 1 or exc.code < 500:
                raise
        except urllib.error.URLError:
            if attempt == 1:
                raise
        time.sleep(retry_delay)
