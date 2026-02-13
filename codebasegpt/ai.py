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
}


@dataclass
class EvidenceItem:
    path: str
    symbol: str
    kind: str
    relation_type: str
    lineno: int | None


def _topic_from_question(question: str) -> str | None:
    q = question.lower()
    for topic, keywords in QUESTION_PATTERNS.items():
        if any(kw in q for kw in keywords):
            return topic

    tokens = [t for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", q) if t not in {"where", "what", "does", "happen", "when"}]
    if tokens:
        return tokens[0]
    return None


def _collect_evidence(db_path: Path, question: str, limit: int = 30) -> list[EvidenceItem]:
    conn = graph.connect(db_path)
    topic = _topic_from_question(question)
    if topic is None:
        rows = conn.execute(
            """
            SELECT f.path, s.name AS symbol, s.kind, 'top' AS relation_type, NULL AS lineno
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            ORDER BY s.name
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    else:
        terms = [topic]
        terms.extend(QUESTION_PATTERNS.get(topic, []))

        clauses = " OR ".join(
            ["lower(s.name) LIKE ? OR lower(f.path) LIKE ? OR lower(COALESCE(r.dst_symbol_name, '')) LIKE ?" for _ in terms]
        )
        params: list[str | int] = []
        for term in terms:
            like = f"%{term.lower()}%"
            params.extend([like, like, like])
        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT f.path, s.name AS symbol, s.kind, COALESCE(r.relation_type, 'declares') AS relation_type, COALESCE(r.lineno, s.lineno) AS lineno
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            LEFT JOIN relations r ON r.dst_symbol_name = s.name
            WHERE {clauses}
            ORDER BY f.path
            LIMIT ?
            """,
            tuple(params),
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

    lines = [f"Question: {question}", "", "Most relevant indexed evidence:"]
    for item in evidence[:15]:
        location = f"{item.path}:{item.lineno}" if item.lineno else item.path
        lines.append(f"- `{item.symbol}` ({item.kind}) via `{item.relation_type}` in `{location}`")

    lines.append("")
    lines.append("This is a graph-grounded heuristic answer. Enable --llm for richer synthesis.")
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

    system_prompt = (
        "You are a codebase analysis assistant. Answer only from provided evidence. "
        "If evidence is weak, explicitly say uncertainty and what to inspect next."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Indexed evidence:\n{evidence_text}\n\n"
        "Return a concise natural-language explanation with:\n"
        "1) direct answer\n2) key code components\n3) uncertainty notes"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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

    try:
        return raw["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # parsing external API response
        raise RuntimeError(f"Unexpected LLM response shape: {raw}") from exc


def answer_question(db_path: Path, question: str, use_llm: bool = False, model: str | None = None) -> str:
    evidence = _collect_evidence(db_path, question)

    if use_llm:
        try:
            return _llm_answer(question, evidence, model=model)
        except Exception as exc:
            fallback = _heuristic_answer(question, evidence)
            return f"LLM call failed ({exc}).\n\n{fallback}"

    return _heuristic_answer(question, evidence)
