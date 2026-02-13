# Production-Grade Support Agent Roadmap (3 Phases)

## Phase 1 — Retrieval and answer quality hardening

### Implemented in this repo
- Multi-term extraction (topic + token parsing).
- Lightweight evidence ranking with flow-edge boosting.
- Multi-hop call-path retrieval over `calls` edges.
- Expanded language indexing for JS/TS/Go/Rust (lightweight symbol extraction).
- Structured answer format with direct answer, components, and uncertainty.
- Evaluation harness via JSONL dataset (`cbg.py evaluate`).

## Phase 2 — Reliability, guardrails, and ops integration

### Implemented in this repo
- Confidence scoring + `needs_human` abstain signal.
- Configurable guardrail thresholds (`CBG_MIN_CONFIDENCE`, `CBG_FLAGGED_MAX_CONFIDENCE`).
- Policy flag detection for sensitive questions.
- PII redaction (emails/cards) in generated responses.
- Query telemetry logging to `.codebasegpt/queries.jsonl`.

## Phase 3 — Autonomous support + dev-assist workflow foundations

### Implemented in this repo
- Owner suggestions based on CODEOWNERS + retrieved evidence paths.
- Call-path metadata and next-action recommendations in structured response output.
- Richer evaluation output with per-case diagnostics and policy precision.

### Remaining (explicitly out of current scope)
- Automatic ticket/task creation integrations.
- Closed-loop feedback and retraining from production outcomes.
