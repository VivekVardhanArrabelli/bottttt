# Production-Grade Support Agent Roadmap (3 Phases)

## Phase 1 — Retrieval and answer quality hardening (now -> near term)

**Goal:** Make answers consistently evidence-backed and higher precision.

- Multi-query retrieval strategy (symbol, file, relation, and call-path views).
- Better ranking features (term overlap, relation weights, recency, file importance).
- Response schema with explicit sections: direct answer, evidence, uncertainty, next checks.
- Evaluation harness with golden Q&A set and precision/recall tracking.
- Language parser expansion beyond Python with parity targets.

**Exit criteria**
- >=85% answer usefulness on curated internal benchmark.
- <=5% unsupported assertions on audited sample.

## Phase 2 — Reliability, guardrails, and ops integration

**Goal:** Safe operation for support workflows.

- Confidence calibration and abstain/escalation thresholds.
- Policy and safety filters (PII, legal/security-sensitive handling).
- Observability: request traces, evidence logs, latency/error dashboards.
- Deterministic fallback paths when LLM unavailable.
- Queue/webhook integration for external ticket systems.

**Exit criteria**
- SLA-backed latency p95 defined and met.
- Escalation precision validated against reviewed ticket set.

## Phase 3 — Autonomous support + dev-assist workflow

**Goal:** Close the loop from customer question to engineering action.

- Automatic conversion of high-confidence root causes into engineering tasks.
- Suggested code-owner routing from graph dependencies and ownership maps.
- PR/change recommendations generated from validated evidence context.
- Continuous evaluation in production with feedback loops and retraining data.

**Exit criteria**
- Measurable MTTR reduction in pilot.
- Increased first-response quality and reduced manual triage load.
