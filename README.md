# bottttt (CodebaseGPT)

CodebaseGPT is a local-first codebase understanding tool that indexes repositories into a graph and exposes CLI workflows for:

- symbol/call impact analysis,
- natural-language repo questions,
- generated architecture docs,
- PR impact summaries,
- migration guides between git refs.

## Implemented Features

- ✅ Repository indexing into SQLite (`files`, `symbols`, `relations`)
- ✅ Python semantic extraction (functions, classes, imports, calls, inheritance)
- ✅ Query commands for callers and impact
- ✅ Natural-language Q&A (graph-grounded heuristic responder)
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
- `codebasegpt/ai.py`: question answering using indexed graph context
- `codebasegpt/docs.py`: architecture report generation
- `codebasegpt/pr_review.py`: PR blast-radius summary from git diff
- `codebasegpt/migration.py`: migration guide generation from git refs
- `cbg.py`: unified CLI entrypoint

## Notes

- Language extraction is currently deepest for **Python**.
- Other file types (`.js`, `.ts`, `.rs`, `.go`) are indexed at file-level and are ready for deeper parser adapters.
- This implementation is intentionally local-first and dependency-light (Python stdlib).
CodebaseGPT is an open-source engine for understanding large codebases.

It indexes repositories into a queryable graph, then uses that context to answer engineering questions, generate docs, and explain pull-request impact.

---

## TL;DR

- Parse source code into structured symbols + relationships.
- Store the graph locally (SQLite) or at scale (Neo4j).
- Expose CLI/API queries for architecture and impact analysis.
- Generate docs and PR summaries using graph-grounded LLM prompts.

If you want to contribute, start in **[Implementation Plan](#implementation-plan-mvp-first)** and pick an unchecked task.

---

## Problem

Teams spend too much time trying to answer questions like:

- Where does auth actually happen?
- What breaks if I change this model?
- What services are touched by this endpoint?
- Which tests should run for this PR?

Raw code search helps, but it does not provide system-level understanding.

## Goal

Build a local-first, open-source “code understanding layer” that turns repositories into:

1. a **semantic graph** (symbols, calls, imports, ownership, flows), and
2. a **developer-facing interface** (CLI/UI/Q&A) for reasoning over that graph.

---

## Core Features

### 1) Repository indexing

- Multi-language parsing via tree-sitter.
- Symbol extraction (files, classes, functions, methods, modules).
- Relationship extraction (imports, calls, inheritance, references).
- Incremental re-indexing when files change.

### 2) Query + analysis

- Structural queries ("show callers of X", "find all auth entrypoints").
- Impact queries ("what depends on this function/schema/type?").
- Path exploration ("from API handler to DB write").

### 3) AI-assisted understanding

- Natural-language Q&A grounded in graph context.
- Architecture and onboarding doc generation.
- PR blast-radius summaries + likely regression areas.

### 4) Integrations

- CLI for local workflows.
- Optional web UI for graph browsing and docs.
- GitHub App mode for continuous PR analysis.

---

## Tech Stack

- **CLI / core indexing:** Rust
- **Parsing:** tree-sitter
- **Storage:** SQLite (default), Neo4j (optional scale mode)
- **LLM provider (initial):** Claude API
- **Frontend (planned):** Next.js

---

## Repository Status

This repo is currently in the **project-definition stage**.

There is no production implementation yet. The next milestone is to land an MVP CLI that can:

1. index one repository,
2. write a graph to SQLite,
3. answer at least 3 structural queries from the CLI.

---

## Implementation Plan (MVP first)

### Phase 0 — Scaffolding

- [ ] Create Rust workspace layout (`crates/indexer`, `crates/graph`, `crates/cli`).
- [ ] Add config loading (`codebasegpt.toml`).
- [ ] Add logging + error conventions.

### Phase 1 — Parser + graph ingest

- [ ] Parse repository files with tree-sitter.
- [ ] Normalize symbols to stable IDs.
- [ ] Store nodes/edges in SQLite schema.
- [ ] Add basic integrity tests for graph writes.

### Phase 2 — CLI queries

- [ ] `cbg index <repo-path>`
- [ ] `cbg query callers <symbol>`
- [ ] `cbg query impacts <symbol>`
- [ ] `cbg query path <from> <to>`

### Phase 3 — AI layer

- [ ] Build retrieval of relevant subgraph context.
- [ ] Add prompt templates for Q&A and PR summaries.
- [ ] Return cited answers (graph evidence IDs).

### Phase 4 — Product surface

- [ ] Minimal web UI for graph + answer views.
- [ ] GitHub PR comment prototype.
- [ ] Caching + incremental update performance pass.

---

## Contribution Guide (Current)

Until full contributor docs are added, use this lightweight workflow:

1. Open an issue with your proposed task.
2. Keep PRs focused on one milestone item.
3. Include tests or validation commands in your PR description.
4. Update this README checklist when completing milestone work.

### Good first contributions

- Define initial SQLite schema (`symbols`, `relations`, `files`).
- Add CLI command scaffolding + argument parsing.
- Add fixture repos for parser tests.
- Add benchmark script for indexing speed.

---

## Non-goals (for MVP)

- Perfect interprocedural analysis across every language.
- Fully autonomous code modification agents.
- Replacing static analyzers or test frameworks.

MVP focuses on practical, trustworthy code understanding.

---

## Vision

CodebaseGPT should become the open standard for codebase intelligence:

- Local-first and self-hostable.
- Transparent graph model (inspectable, extensible).
- Useful for individuals, teams, maintainers, and researchers.

