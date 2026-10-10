# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A RAG research agent for ML-for-science literature. The spec is in `docs/SPEC.md`;
read the current milestone there before changing code. Do not build anything listed
under "Non-goals" or "Future work" unless asked.

## Layout

- `src/research_agent/models.py` — `Paper` and other shared pydantic models
- `src/research_agent/sources/` — external API clients (arXiv, Semantic Scholar)
- `src/research_agent/library.py` — local paper store (JSONL now, S3 later)
- `src/research_agent/cli.py` — `research-agent` command
- `tests/` — pytest; `tests/fixtures/` holds recorded API responses
- `eval/` — evaluation questions, harness and results

## Commands

```bash
pip install -e ".[dev]"
ruff check . && ruff format .
pytest
```

## Rules

- **Tests never touch the network.** Use `httpx.MockTransport` and fixtures in `tests/fixtures/`.
- Every API client accepts an injectable `httpx.Client` so it can be tested.
- Respect rate limits: arXiv ~3 s between requests; Semantic Scholar shared limits without a key.
- Answers must be grounded: every claim cites a retrieved chunk ID, and the system says
  "not found in library" rather than guessing.
- Any change to chunking, retrieval or prompts must be followed by an eval run, with the
  numbers recorded in `eval/results/`.
- Keep functions small and typed. Python 3.11+, line length 100, ruff for lint and format.
- Secrets come from environment variables only. Never commit keys or `data/`.
- Prefer the simplest thing that meets the milestone's acceptance criteria.
