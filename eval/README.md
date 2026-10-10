# Evaluation

Planned for week 2 (see `docs/SPEC.md`, M3).

- `questions.jsonl` — expert-written questions about ML-for-science papers, each with a gold
  answer and the arXiv ID + passage that supports it.
- `run_eval.py` — runs the system on every question and computes retrieval recall@k,
  citation faithfulness, answer correctness, cost per query and latency.
- `results/` — one file per run, so every change to chunking, retrieval or prompts has numbers.

Question format:

```json
{"id": "csp-001", "question": "...", "gold_answer": "...", "gold_sources": [{"arxiv_id": "...", "passage": "..."}], "topic": "crystal-structure-prediction"}
```
