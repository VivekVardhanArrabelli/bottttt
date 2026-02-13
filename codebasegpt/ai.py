from __future__ import annotations

from pathlib import Path

from . import graph


QUESTION_PATTERNS = {
    "authentication": ["auth", "login", "token", "oauth", "jwt"],
    "checkout": ["checkout", "cart", "payment", "order"],
}


def answer_question(db_path: Path, question: str) -> str:
    conn = graph.connect(db_path)
    q = question.lower()

    best_topic = None
    for topic, keywords in QUESTION_PATTERNS.items():
        if any(kw in q for kw in keywords):
            best_topic = topic
            break

    if best_topic is None:
        rows = list(graph.top_symbols(conn, limit=5))
        conn.close()
        if not rows:
            return "No indexed symbols found yet. Run indexing first."
        top = ", ".join(f"{r['name']} ({r['kind']})" for r in rows)
        return f"I could not map the question to a known topic yet. Top referenced symbols: {top}."

    rows = conn.execute(
        """
        SELECT f.path, s.name, s.kind
        FROM symbols s
        JOIN files f ON f.id = s.file_id
        WHERE lower(s.name) LIKE ?
        ORDER BY f.path
        LIMIT 20
        """,
        (f"%{best_topic}%",),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No direct symbols matched topic '{best_topic}'. Try refining your question."

    bullets = "\n".join(f"- `{r['name']}` ({r['kind']}) in `{r['path']}`" for r in rows)
    return f"Likely relevant code for **{best_topic}**:\n{bullets}"
