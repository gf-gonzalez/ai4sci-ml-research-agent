"""Shared HTTP helper: GET with retries and backoff for flaky public APIs.

arXiv and Semantic Scholar both time out or rate-limit (429/503) under load.
Retry those cases; fail fast on everything else.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = httpx.Timeout(90.0, connect=15.0)


def get_with_retries(
    client: httpx.Client,
    url: str,
    params: dict | None = None,
    retries: int = 3,
    backoff_s: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """GET `url`, retrying timeouts, connection errors and 429/5xx with exponential backoff.

    Returns the final response (which may still be an error status for the caller to handle,
    e.g. 404). Raises the last transport error if every attempt failed to connect.
    """
    for attempt in range(retries + 1):
        last = attempt == retries
        try:
            response = client.get(url, params=params)
        except (httpx.TimeoutException, httpx.TransportError):
            if last:
                raise
            sleep(backoff_s * 2**attempt)
            continue

        if response.status_code in RETRY_STATUS and not last:
            retry_after = response.headers.get("Retry-After", "")
            wait = float(retry_after) if retry_after.isdigit() else backoff_s * 2**attempt
            sleep(wait)
            continue
        return response

    raise AssertionError("unreachable")
