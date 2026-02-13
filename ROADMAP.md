# Production-Grade Support Agent Roadmap (3 Phases)

## Phase 1 — Retrieval and answer quality hardening

### Implemented in this repo
- Multi-term extraction (topic + token parsing).
- Lightweight evidence ranking with flow-edge boosting.
- Structured answer format with direct answer, components, and uncertainty.
- Evaluation harness via JSONL dataset (`cbg.py evaluate`).

### Remaining
- Add call-path retrieval beyond single-hop relations.
- Expand parser parity across non-Python languages.

## Phase 2 — Reliability, guardrails, and ops integration

### Implemented in this repo
- Confidence scoring + `needs_human` abstain signal.
- Policy flag detection for sensitive questions.
- PII redaction (emails/cards) in generated responses.
- Query telemetry logging to `.codebasegpt/queries.jsonl`.

### Remaining
- Full policy engine and configurable thresholds.
- Latency/error dashboards and SLA tracking.

## Phase 3 — Autonomous support + dev-assist workflow

### Implemented in this repo
- Owner suggestions based on CODEOWNERS + retrieved evidence paths.
- Next-action recommendations in structured response metadata.

### Remaining
- Automatic task creation and code-owner routing integrations.
- Closed-loop feedback/retraining from production outcomes.
