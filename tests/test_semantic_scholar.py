from datetime import date

import httpx

from research_agent.models import Paper
from research_agent.sources.semantic_scholar import SemanticScholarClient

PAPER = Paper(
    arxiv_id="2501.01234",
    title="T",
    authors=["A B"],
    abstract="x",
    published=date(2025, 1, 1),
)


def _client(status: int, payload: dict | None = None) -> SemanticScholarClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/paper/arXiv:2501.01234")
        return httpx.Response(status, json=payload or {})

    return SemanticScholarClient(client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_enrich_adds_metadata():
    enriched = _client(
        200, {"citationCount": 42, "venue": "NeurIPS", "tldr": {"text": "Short summary."}}
    ).enrich(PAPER)
    assert enriched.citation_count == 42
    assert enriched.venue == "NeurIPS"
    assert enriched.tldr == "Short summary."
    assert PAPER.citation_count is None  # original untouched


def test_enrich_returns_paper_unchanged_when_not_found():
    assert _client(404).enrich(PAPER) == PAPER
