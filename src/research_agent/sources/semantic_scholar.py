"""Semantic Scholar Graph API client, used to enrich arXiv papers.

Docs: https://api.semanticscholar.org/api-docs/graph
Works without a key at a low shared rate limit; set SEMANTIC_SCHOLAR_API_KEY for more.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

import httpx

from research_agent.models import Paper
from research_agent.sources.http import DEFAULT_TIMEOUT, get_with_retries

API_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "citationCount,venue,tldr"


class SemanticScholarClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
        retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ):
        key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        headers = {"x-api-key": key} if key else {}
        self._client = client or httpx.Client(timeout=DEFAULT_TIMEOUT, headers=headers)
        self._retries = retries
        self._sleep = sleep

    def enrich(self, paper: Paper) -> Paper:
        """Return a copy of `paper` with citation count, venue and TL;DR when available."""
        response = get_with_retries(
            self._client,
            f"{API_URL}/paper/arXiv:{paper.arxiv_id}",
            params={"fields": FIELDS},
            retries=self._retries,
            sleep=self._sleep,
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
