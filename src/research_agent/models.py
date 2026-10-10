"""Core data models shared across sources, the library and (later) the RAG pipeline."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A single paper, normalised across sources (arXiv, Semantic Scholar, ...)."""

    arxiv_id: str = Field(description="arXiv identifier without version, e.g. '2501.01234'")
    title: str
    authors: list[str]
    abstract: str
    published: date
    categories: list[str] = Field(default_factory=list)
    pdf_url: str | None = None
    html_url: str | None = None

    # Enrichment from Semantic Scholar (optional)
    citation_count: int | None = None
    venue: str | None = None
    tldr: str | None = None

    @property
    def short_citation(self) -> str:
        first = self.authors[0].split()[-1] if self.authors else "Unknown"
        etal = " et al." if len(self.authors) > 1 else ""
        return f"{first}{etal} ({self.published.year}), arXiv:{self.arxiv_id}"
