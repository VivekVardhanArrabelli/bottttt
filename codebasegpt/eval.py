from __future__ import annotations

import json
from pathlib import Path

from .ai import answer_question_with_metadata


def run_eval_suite(db_path: Path, dataset_path: Path, use_llm: bool = False, model: str | None = None) -> dict[str, object]:
    cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        return {"cases": 0, "avg_confidence": 0.0, "contains_rate": 0.0, "needs_human_rate": 0.0}

    contains_hits = 0
    confidence_sum = 0.0
    needs_human = 0

    for case in cases:
        question = case["question"]
        expected = [s.lower() for s in case.get("must_include", [])]
        out = answer_question_with_metadata(db_path, question, use_llm=use_llm, model=model)
        answer = str(out["answer"]).lower()

        if all(token in answer for token in expected):
            contains_hits += 1
        confidence_sum += float(out["confidence"])
        needs_human += int(bool(out["needs_human"]))

    n = len(cases)
    return {
        "cases": n,
        "avg_confidence": round(confidence_sum / n, 3),
        "contains_rate": round(contains_hits / n, 3),
        "needs_human_rate": round(needs_human / n, 3),
    }
