# bottttt (CodebaseGPT)

CodebaseGPT is a local-first codebase understanding engine for high-quality, evidence-grounded answers over source code.

## What is implemented

- Repository indexing into SQLite (`files`, `symbols`, `relations`)
- Python semantic extraction (functions, classes, imports, calls, inheritance)
- Query commands for callers and impact
- Hybrid Q&A (graph retrieval + optional LLM synthesis)
- Policy flags + PII redaction + abstain/escalation signal (`needs_human`)
- Observability telemetry (`.codebasegpt/queries.jsonl`)
- Evaluation harness (`evaluate` command with JSONL datasets)
- Owner suggestions via CODEOWNERS matching

## Quickstart

### 1) Index a repository
```bash
python cbg.py index /path/to/repo
```

### 2) Ask questions (text)
```bash
python cbg.py ask "How does checkout work?" --db /path/to/repo/.codebasegpt.sqlite
```

### 3) Ask questions (structured JSON)
```bash
python cbg.py ask "Where does authentication happen?" \
  --db /path/to/repo/.codebasegpt.sqlite \
  --repo /path/to/repo \
  --json
```

### 4) Use LLM synthesis
```bash
export CBG_LLM_API_KEY=...
export CBG_LLM_API_URL=https://api.openai.com/v1/chat/completions
export CBG_LLM_MODEL=gpt-4o-mini
python cbg.py ask "Explain auth flow" --db /path/to/repo/.codebasegpt.sqlite --llm --json
```

### 5) Run evaluation suite
```bash
python cbg.py evaluate \
  --db /path/to/repo/.codebasegpt.sqlite \
  --dataset tests/fixtures/eval_dataset.jsonl
```

## Roadmap execution status

See `ROADMAP.md` for the 3-phase plan and what has now been implemented from each phase.
