# bottttt (CodebaseGPT)

CodebaseGPT is a local-first codebase understanding tool that indexes repositories into a graph and exposes CLI workflows for:

- symbol/call impact analysis,
- natural-language codebase questions,
- generated architecture docs,
- PR impact summaries,
- migration guides between git refs.

## Implemented Features

- ✅ Repository indexing into SQLite (`files`, `symbols`, `relations`)
- ✅ Python semantic extraction (functions, classes, imports, calls, inheritance)
- ✅ Query commands for callers and impact
- ✅ Natural-language Q&A (graph-grounded)
- ✅ Optional LLM API synthesis (OpenAI-compatible chat endpoint)
- ✅ Generated architecture markdown report
- ✅ PR impact summary from git diff + indexed relations
- ✅ Migration guide generation between tags/refs

## Quickstart

### 1) Index a repository

```bash
python cbg.py index /path/to/repo
```

By default this writes `/path/to/repo/.codebasegpt.sqlite`.

### 2) Query callers and impacts

```bash
python cbg.py query-callers helper --db /path/to/repo/.codebasegpt.sqlite
python cbg.py query-impacts checkout --db /path/to/repo/.codebasegpt.sqlite
```

### 3) Ask natural-language questions

```bash
python cbg.py ask "Where does authentication happen?" --db /path/to/repo/.codebasegpt.sqlite
```

Use LLM-backed synthesis (recommended for richer answers):

```bash
export CBG_LLM_API_KEY=...
# optional
export CBG_LLM_API_URL=https://api.openai.com/v1/chat/completions
export CBG_LLM_MODEL=gpt-4o-mini

python cbg.py ask "How does checkout work end-to-end?" --db /path/to/repo/.codebasegpt.sqlite --llm
```

### 4) Generate architecture docs

```bash
python cbg.py generate-docs --db /path/to/repo/.codebasegpt.sqlite --out ARCHITECTURE.generated.md
```

### 5) Summarize PR impact

```bash
python cbg.py pr-impact /path/to/repo --db /path/to/repo/.codebasegpt.sqlite --base main --head feature-branch
```

### 6) Generate migration guide

```bash
python cbg.py migration-guide /path/to/repo v2.0.0 v3.0.0
```

## Architecture

- `codebasegpt/indexer.py`: repository scanning + AST-based extraction
- `codebasegpt/graph.py`: SQLite schema + persistence + query helpers
- `codebasegpt/ai.py`: question answering + optional LLM synthesis
- `codebasegpt/docs.py`: architecture report generation
- `codebasegpt/pr_review.py`: PR blast-radius summary from git diff
- `codebasegpt/migration.py`: migration guide generation from git refs
- `cbg.py`: unified CLI entrypoint

## Response quality improvements (current)

- Expanded term extraction from questions (topic keywords + token parsing).
- Added lightweight evidence ranking for better relevance ordering.
- Kept strict evidence grounding in heuristic and LLM prompts.

## Roadmap

See `ROADMAP.md` for the 3-phase plan to move from this prototype to a production-grade support agent.
