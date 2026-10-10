"""Command-line entry point.

research-agent fetch 'all:"crystal structure prediction"' --max 20 --enrich
research-agent list
"""

from __future__ import annotations

import argparse

from research_agent.library import Library
from research_agent.sources.arxiv import ArxivClient
from research_agent.sources.semantic_scholar import SemanticScholarClient


def cmd_fetch(args: argparse.Namespace) -> None:
    library = Library(args.library)
    papers = ArxivClient().search(args.query, max_results=args.max)
    if args.enrich:
        s2 = SemanticScholarClient()
        papers = [s2.enrich(p) for p in papers]
    new = library.add(papers)
    print(f"Fetched {len(papers)} papers ({new} new). Library now has {len(library)} papers.")


def cmd_list(args: argparse.Namespace) -> None:
    for paper in Library(args.library).all()[: args.limit]:
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
