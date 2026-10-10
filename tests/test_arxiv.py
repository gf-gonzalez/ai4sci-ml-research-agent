from datetime import date
from pathlib import Path

import httpx

from research_agent.sources.arxiv import ArxivClient, parse_feed

FIXTURE = (Path(__file__).parent / "fixtures" / "arxiv_sample.xml").read_text()


def test_parse_feed_normalises_fields():
    papers = parse_feed(FIXTURE)
    assert len(papers) == 2

    p = papers[0]
    assert p.arxiv_id == "2501.01234"  # version suffix stripped
    assert (
        p.title == "A Flow Matching Model for Crystal Structure Prediction"
    )  # whitespace collapsed
    assert p.abstract.startswith("We propose an equivariant")
    assert p.authors == ["Ada Lovelace", "Alan Turing"]
    assert p.published == date(2025, 1, 3)
    assert p.categories == ["cs.LG", "cond-mat.mtrl-sci"]
    assert p.pdf_url == "http://arxiv.org/pdf/2501.01234v2"
    assert p.short_citation == "Lovelace et al. (2025), arXiv:2501.01234"


def test_parse_feed_handles_missing_pdf_link_and_single_author():
    p = parse_feed(FIXTURE)[1]
    assert p.pdf_url is None
    assert p.short_citation == "Franklin (2024), arXiv:2412.09999"


def test_search_sends_expected_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, text=FIXTURE)

    client = ArxivClient(client=httpx.Client(transport=httpx.MockTransport(handler)), delay_s=0)
    papers = client.search('all:"crystal structure"', max_results=2)

    assert len(papers) == 2
    assert seen["search_query"] == 'all:"crystal structure"'
    assert seen["max_results"] == "2"
    assert seen["sortBy"] == "submittedDate"
