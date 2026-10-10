# Project spec

Written before the code. Each milestone lists its intent, constraints and acceptance
criteria; a milestone is done only when its criteria pass.

## Problem

When researching a new ML-for-science topic I need to answer questions like:

- Which models are state of the art on MP-20 for crystal structure prediction, and on which metrics?
- What alignment or matching procedure does benchmark X use?
- Which datasets exist for multilabel antimicrobial peptide classification?
- How does method A's training objective differ from method B's?

General-purpose assistants answer fluently but often invent datasets, metrics or numbers.
I want answers grounded in specific papers, with citations I can check, and a measured
error rate.

## Users

1. Me, from Claude Code or the Claude app, through an MCP server.
2. Anyone reading the repo: the eval results show how much to trust the answers.

## Non-goals (for now)

- A web chat UI. The MCP server and CLI are the interfaces.
- Full PDF parsing of equations and tables. Use arXiv HTML and abstracts first.
- Multi-agent orchestration, knowledge graphs, auto-generated surveys.

## Milestones

### M1 — Ingestion (week 1)
- **Intent:** build a local library of papers on a topic from arXiv, enriched with Semantic Scholar metadata.
- **Constraints:** respect arXiv's ~3 s delay between requests; no network calls in tests.
- **Acceptance:** `research-agent fetch` adds papers without duplicates; `list` shows them; tests and CI pass. **Done.**

### M2 — Retrieval and cited answers (week 1)
- **Intent:** ask a question over the library and get an answer citing paper and section.
- **Design:** fetch arXiv HTML full text when available, otherwise use the abstract; chunk by section with overlap; hybrid retrieval (BM25 + dense embeddings, fused with reciprocal rank fusion); optional reranking; Claude answers using only retrieved chunks and must cite chunk IDs.
- **Acceptance:** each claim in an answer maps to a chunk ID that exists; the model says "not found in library" instead of guessing when retrieval is empty.

### M3 — Evaluation (week 2)
- **Intent:** measure how often the system is right, and why it fails.
- **Data:** 50–100 questions about papers I know well (crystal structure prediction, peptide function prediction, PXRD), each with a gold answer and gold supporting passage(s). Stored in `eval/questions.jsonl`.
- **Metrics:** retrieval recall@k (gold passage retrieved); citation faithfulness (cited chunk supports the claim; LLM judge, spot-checked by hand); answer correctness (LLM judge against gold, spot-checked); cost per query (tokens × price) and p50/p95 latency.
- **Ablations:** chunk size; BM25 vs dense vs hybrid; with and without reranking; prompt variants.
- **Output:** a results table in the README and an error taxonomy (retrieval miss, wrong chunk cited, unsupported claim, outdated information, ...).

### M4 — Agent, MCP and service (week 3)
- **Tools:** `search_papers` (arXiv), `add_to_library`, `ask_library`, `compare_methods`, `find_datasets`.
- **Interfaces:** MCP server for Claude Code and the Claude app; FastAPI service exposing the same functions.
- **Packaging:** Dockerfile; GitHub Actions builds the image and runs a small eval subset in CI.
- **Acceptance:** usable from Claude Code on a real literature question; eval scores do not regress versus M3.

### M5 — AWS (week 4)
- **LLM and embeddings:** Claude and an embedding model on Amazon Bedrock.
- **Storage:** library and index in S3.
- **Compute:** container on ECS Fargate or Lambda (image pushed to ECR).
- **Scheduling:** EventBridge rule runs a weekly fetch and sends a digest of new papers on my topics.
- **Observability:** structured logs, per-query cost and latency in CloudWatch.
- **CD:** GitHub Actions deploys on merge to `main`.
- **Cost control:** billing alarm from day one; no always-on services with a minimum charge (e.g. avoid OpenSearch Serverless for this scale).

## Future work (not in scope)

- Extend the eval set into a public benchmark for research-QA in ML for science.
- Citation-graph exploration via Semantic Scholar references.
- Comparing tables of reported results across papers.
