import httpx
import pytest

from research_agent.sources.http import get_with_retries


def _client(responses):
    """Mock client that returns (or raises) each item of `responses` in turn."""
    calls = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return item

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_retries_timeout_then_succeeds():
    sleeps = []
    client = _client([httpx.ReadTimeout("slow"), httpx.Response(200, text="ok")])
    response = get_with_retries(client, "https://x.test", sleep=sleeps.append, backoff_s=1)
    assert response.text == "ok"
    assert sleeps == [1]


def test_retries_503_and_honours_retry_after():
    sleeps = []
    client = _client(
        [httpx.Response(503, headers={"Retry-After": "7"}), httpx.Response(200, text="ok")]
    )
    assert get_with_retries(client, "https://x.test", sleep=sleeps.append).text == "ok"
    assert sleeps == [7.0]


def test_backoff_is_exponential_and_gives_up():
    sleeps = []
    client = _client([httpx.ReadTimeout("slow")] * 3)
    with pytest.raises(httpx.ReadTimeout):
        get_with_retries(client, "https://x.test", retries=2, backoff_s=2, sleep=sleeps.append)
    assert sleeps == [2, 4]


def test_does_not_retry_404():
    sleeps = []
    client = _client([httpx.Response(404)])
    assert get_with_retries(client, "https://x.test", sleep=sleeps.append).status_code == 404
    assert sleeps == []
