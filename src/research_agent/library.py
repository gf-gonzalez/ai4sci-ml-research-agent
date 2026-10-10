"""A local paper library stored as JSON Lines.

Deliberately simple for week 1: one JSON object per paper, keyed by arXiv ID.
Later this becomes the source of truth that the chunker and vector index read from,
and it moves to S3 in week 4.
"""

from __future__ import annotations

import json
from pathlib import Path

from research_agent.models import Paper


class Library:
    def __init__(self, path: Path | str = "data/library.jsonl"):
        self.path = Path(path)
        self._papers: dict[str, Paper] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    paper = Paper.model_validate_json(line)
                    self._papers[paper.arxiv_id] = paper

    def __len__(self) -> int:
        return len(self._papers)

    def __contains__(self, arxiv_id: str) -> bool:
        return arxiv_id in self._papers

    def get(self, arxiv_id: str) -> Paper | None:
        return self._papers.get(arxiv_id)

    def all(self) -> list[Paper]:
        return sorted(self._papers.values(), key=lambda p: p.published, reverse=True)

    def add(self, papers: list[Paper]) -> int:
        """Add or update papers. Returns how many were new."""
        new = sum(p.arxiv_id not in self._papers for p in papers)
        for p in papers:
            self._papers[p.arxiv_id] = p
        self.save()
        return new

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for paper in self.all():
                f.write(json.dumps(paper.model_dump(mode="json")) + "\n")
        tmp.replace(self.path)
