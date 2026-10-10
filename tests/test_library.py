from pathlib import Path

from research_agent.library import Library
from research_agent.sources.arxiv import parse_feed

FIXTURE = (Path(__file__).parent / "fixtures" / "arxiv_sample.xml").read_text()


def test_add_persists_and_deduplicates(tmp_path):
    path = tmp_path / "library.jsonl"
    papers = parse_feed(FIXTURE)

    lib = Library(path)
    assert lib.add(papers) == 2
    assert lib.add(papers) == 0  # same papers again: nothing new
    assert len(lib) == 2

    reloaded = Library(path)
    assert len(reloaded) == 2
    assert "2501.01234" in reloaded
    assert reloaded.get("2501.01234").title.startswith("A Flow Matching")


def test_all_is_sorted_newest_first(tmp_path):
    lib = Library(tmp_path / "library.jsonl")
    lib.add(parse_feed(FIXTURE))
    dates = [p.published for p in lib.all()]
    assert dates == sorted(dates, reverse=True)
