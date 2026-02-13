from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import graph


QUESTION_PATTERNS = {
    "authentication": ["auth", "login", "token", "oauth", "jwt"],
    "checkout": ["checkout", "cart", "payment", "order"],
    "performance": ["slow", "latency", "timeout", "throughput"],
}

STOPWORDS = {
    "where",
    "what",
    "does",
    "happen",
    "when",
    "how",
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
}


@dataclass
class EvidenceItem:
    path: str
    symbol: str
    kind: str
    relation_type: str
    lineno: int | None


def _extract_terms(question: str) -> list[str]:
    q = question.lower()
    terms: list[str] = []

    for topic, keywords in QUESTION_PATTERNS.items():
        if any(kw in q for kw in keywords):
            terms.append(topic)
            terms.extend(keywords)

    tokens = [t for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", q) if t not in STOPWORDS]
    terms.extend(tokens)

    deduped: list[str] = []
    seen: set[str] = set()
    for t in terms:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped[:10]


def _collect_evidence(db_path: Path, question: str, limit: int = 40) -> list[EvidenceItem]:
    conn = graph.connect(db_path)
    terms = _extract_terms(question)

    if not terms:
        rows = conn.execute(
            """
            SELECT f.path, s.name AS symbol, s.kind, 'top' AS relation_type, s.lineno AS lineno
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            ORDER BY s.name
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    else:
        clauses = " OR ".join(
            ["lower(s.name) LIKE ? OR lower(f.path) LIKE ? OR lower(COALESCE(r.dst_symbol_name, '')) LIKE ?" for _ in terms]
        )
        params: list[str | int] = []
        for term in terms:
            like = f"%{term}%"
            params.extend([like, like, like])
        params.append(limit * 3)

        raw_rows = conn.execute(
            f"""
            SELECT f.path, s.name AS symbol, s.kind,
                   COALESCE(r.relation_type, 'declares') AS relation_type,
                   COALESCE(r.lineno, s.lineno) AS lineno
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            LEFT JOIN relations r ON r.dst_symbol_name = s.name
            WHERE {clauses}
            ORDER BY f.path
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

        # lightweight ranking: reward direct token overlap in symbol/path names
        scored: list[tuple[int, object]] = []
        for row in raw_rows:
            hay = f"{row['symbol']} {row['path']} {row['relation_type']}".lower()
            score = sum(2 if t in row["symbol"].lower() else 1 for t in terms if t in hay)
            scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        rows = [row for _, row in scored[:limit]]

    if not rows:
        rows = conn.execute(
            """
            SELECT f.path, s.name AS symbol, s.kind, 'fallback' AS relation_type, s.lineno AS lineno
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            ORDER BY s.name
            LIMIT ?
            """,
            (min(limit, 10),),
        ).fetchall()

    conn.close()
    return [
        EvidenceItem(
            path=row["path"],
            symbol=row["symbol"],
            kind=row["kind"],
            relation_type=row["relation_type"],
            lineno=row["lineno"],
        )
        for row in rows
    ]


def _heuristic_answer(question: str, evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "No indexed evidence found. Run indexing first or refine your question."

    lines = ["Direct answer (evidence-grounded)", f"Question: {question}", ""]
    lines.append("Relevant components:")
    for item in evidence[:12]:
        location = f"{item.path}:{item.lineno}" if item.lineno else item.path
        lines.append(f"- `{item.symbol}` ({item.kind}) via `{item.relation_type}` in `{location}`")
    lines.append("")
    lines.append("Confidence note: heuristic mode. Use --llm for higher quality synthesis.")
    return "\n".join(lines)


def _llm_answer(question: str, evidence: list[EvidenceItem], model: str | None = None) -> str:
    api_key = os.getenv("CBG_LLM_API_KEY")
    if not api_key:
        raise RuntimeError("CBG_LLM_API_KEY is not set")

    api_url = os.getenv("CBG_LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model_name = model or os.getenv("CBG_LLM_MODEL", "gpt-4o-mini")

    evidence_lines = [
        f"- symbol={e.symbol} kind={e.kind} relation={e.relation_type} file={e.path} line={e.lineno}"
        for e in evidence[:40]
    ]
    evidence_text = "\n".join(evidence_lines) if evidence_lines else "- no evidence found"

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a codebase analysis assistant. Answer strictly from provided evidence. "
                    "State uncertainty explicitly if evidence is weak."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Indexed evidence:\n{evidence_text}\n\n"
                    "Respond with:\n1) direct answer\n2) key components and flow\n3) uncertainty notes"
                ),
            },
        ],
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    return raw["choices"][0]["message"]["content"].strip()


def answer_question_with_metadata(
    db_path: Path,
    question: str,
    use_llm: bool = False,
    model: str | None = None,
) -> dict[str, object]:
    evidence = _collect_evidence(db_path, question)
    evidence_count = len(evidence)

    confidence = min(0.95, 0.25 + 0.05 * min(evidence_count, 10))
    if use_llm:
        confidence = min(0.98, confidence + 0.08)

    if use_llm:
        try:
            answer = _llm_answer(question, evidence, model=model)
        except Exception as exc:
            answer = f"LLM call failed ({exc}).\n\n" + _heuristic_answer(question, evidence)
            confidence = max(0.3, confidence - 0.2)
    else:
        answer = _heuristic_answer(question, evidence)

    return {
        "answer": answer,
        "evidence_count": evidence_count,
        "confidence": confidence,
        "needs_human": confidence < 0.45 or evidence_count == 0,
    }


def answer_question(db_path: Path, question: str, use_llm: bool = False, model: str | None = None) -> str:
    return str(answer_question_with_metadata(db_path, question, use_llm=use_llm, model=model)["answer"])
