"""Command-line entry point.

research-agent fetch 'all:"crystal structure prediction"' --max 20 --enrich
research-agent list
"""

from __future__ import annotations

import argparse
import sys

import httpx

from research_agent.library import Library
from research_agent.sources.arxiv import ArxivClient
from research_agent.sources.semantic_scholar import SemanticScholarClient


def cmd_fetch(args: argparse.Namespace) -> None:
    library = Library(args.library)
    print("Searching arXiv (its API can take up to a minute)...")
    try:
        papers = ArxivClient().search(args.query, max_results=args.max)
    except httpx.HTTPError as exc:
        sys.exit(
            f"arXiv request failed after retries: {exc.__class__.__name__}: {exc}\n"
            "arXiv's API is often slow or busy. Wait a minute and try again, or lower --max."
        )

    if args.enrich:
        s2 = SemanticScholarClient()
        enriched, skipped = [], 0
        for paper in papers:
            try:
                enriched.append(s2.enrich(paper))
            except httpx.HTTPError:
                enriched.append(paper)  # keep the paper, just without enrichment
                skipped += 1
        papers = enriched
        if skipped:
            print(
                f"Semantic Scholar enrichment skipped for {skipped} papers (rate limit or "
                "network). Set SEMANTIC_SCHOLAR_API_KEY or retry later."
            )

    new = library.add(papers)
    print(f"Fetched {len(papers)} papers ({new} new). Library now has {len(library)} papers.")
    print(f"Saved to {library.path.resolve()}")


def cmd_list(args: argparse.Namespace) -> None:
    library = Library(args.library)
    location = library.path.resolve()
    if not library.path.exists():
        sys.exit(
            f"No library found at {location}\n"
            "Run `fetch` first, from the same folder (the library path is relative to it)."
        )
    if len(library) == 0:
        sys.exit(f"The library at {location} is empty.")

    print(f"{len(library)} papers in {location}\n")
    for paper in library.all()[: args.limit]:
        cites = f" · {paper.citation_count} citations" if paper.citation_count is not None else ""
        print(f"[{paper.arxiv_id}] {paper.title} — {paper.short_citation}{cites}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="research-agent")
    parser.add_argument("--library", default="data/library.jsonl")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Search arXiv and add results to the library")
    fetch.add_argument("query", help="arXiv query, e.g. 'all:\"flow matching\" AND cat:cs.LG'")
    fetch.add_argument("--max", type=int, default=25)
    fetch.add_argument("--enrich", action="store_true", help="Add Semantic Scholar metadata")
    fetch.set_defaults(func=cmd_fetch)

    lst = sub.add_parser("list", help="List papers in the library")
    lst.add_argument("--limit", type=int, default=50)
    lst.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
