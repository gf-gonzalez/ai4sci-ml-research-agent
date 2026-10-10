"""arXiv API client.

Docs: https://info.arxiv.org/help/api/user-manual.html
arXiv asks clients to wait ~3 seconds between consecutive requests.
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from research_agent.models import Paper

API_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
REQUEST_DELAY_S = 3.0
_VERSION_RE = re.compile(r"v\d+$")


def _clean(text: str | None) -> str:
    return " ".join((text or "").split())


def parse_feed(xml_text: str) -> list[Paper]:
    """Parse an arXiv Atom feed into Paper objects."""
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []
    for entry in root.findall("atom:entry", NS):
        raw_id = _clean(entry.findtext("atom:id", namespaces=NS))
        arxiv_id = _VERSION_RE.sub("", raw_id.rsplit("/abs/", 1)[-1])

        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")

        published = datetime.fromisoformat(
            _clean(entry.findtext("atom:published", namespaces=NS)).replace("Z", "+00:00")
        ).date()

        papers.append(
            Paper(
                arxiv_id=arxiv_id,
                title=_clean(entry.findtext("atom:title", namespaces=NS)),
                authors=[
                    _clean(a.findtext("atom:name", namespaces=NS))
                    for a in entry.findall("atom:author", NS)
                ],
                abstract=_clean(entry.findtext("atom:summary", namespaces=NS)),
                published=published,
                categories=[c.get("term", "") for c in entry.findall("atom:category", NS)],
                pdf_url=pdf_url,
                html_url=f"https://arxiv.org/html/{arxiv_id}",
            )
        )
    return papers


class ArxivClient:
    def __init__(self, client: httpx.Client | None = None, delay_s: float = REQUEST_DELAY_S):
        self._client = client or httpx.Client(timeout=30.0)
        self._delay_s = delay_s
        self._last_request = 0.0

    def _get(self, params: dict) -> str:
        wait = self._delay_s - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        response = self._client.get(API_URL, params=params)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return response.text

    def search(self, query: str, max_results: int = 25, newest_first: bool = True) -> list[Paper]:
        """Search arXiv. `query` uses arXiv syntax, e.g. 'all:"crystal structure prediction"'."""
        params = {"search_query": query, "start": 0, "max_results": max_results}
        if newest_first:
            params |= {"sortBy": "submittedDate", "sortOrder": "descending"}
        return parse_feed(self._get(params))

    def get(self, arxiv_ids: list[str]) -> list[Paper]:
        """Fetch specific papers by arXiv ID."""
        if not arxiv_ids:
            return []
        return parse_feed(
            self._get({"id_list": ",".join(arxiv_ids), "max_results": len(arxiv_ids)})
        )
