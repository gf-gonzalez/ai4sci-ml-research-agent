"""Semantic Scholar Graph API client, used to enrich arXiv papers.

Docs: https://api.semanticscholar.org/api-docs/graph
Works without a key at a low shared rate limit; set SEMANTIC_SCHOLAR_API_KEY for more.
"""

from __future__ import annotations

import os

import httpx

from research_agent.models import Paper

API_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "citationCount,venue,tldr"


class SemanticScholarClient:
    def __init__(self, client: httpx.Client | None = None, api_key: str | None = None):
        key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        headers = {"x-api-key": key} if key else {}
        self._client = client or httpx.Client(timeout=30.0, headers=headers)

    def enrich(self, paper: Paper) -> Paper:
        """Return a copy of `paper` with citation count, venue and TL;DR when available."""
        response = self._client.get(
            f"{API_URL}/paper/arXiv:{paper.arxiv_id}", params={"fields": FIELDS}
        )
        if response.status_code == 404:
            return paper
        response.raise_for_status()
        data = response.json()
        tldr = (data.get("tldr") or {}).get("text")
        return paper.model_copy(
            update={
                "citation_count": data.get("citationCount"),
                "venue": data.get("venue") or None,
                "tldr": tldr,
            }
        )
