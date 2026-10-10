from pathlib import Path

import pytest

from research_agent import cli
from research_agent.sources import arxiv

FIXTURE = (Path(__file__).parent / "fixtures" / "arxiv_sample.xml").read_text()


@pytest.fixture
def offline_arxiv(monkeypatch):
    monkeypatch.setattr(
        arxiv.ArxivClient, "search", lambda self, query, max_results=25: arxiv.parse_feed(FIXTURE)
    )


def test_fetch_then_list_shows_papers(tmp_path, offline_arxiv, capsys):
    library = tmp_path / "library.jsonl"
    cli.main(["--library", str(library), "fetch", "all:crystal"])
    cli.main(["--library", str(library), "list"])

    out = capsys.readouterr().out
    assert "2 papers in" in out
    assert "[2501.01234] A Flow Matching Model" in out
    assert "[2412.09999] Peptide Function Prediction" in out


def test_list_without_library_explains_why(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--library", str(tmp_path / "missing.jsonl"), "list"])
    assert "No library found at" in str(exc.value)
