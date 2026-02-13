from __future__ import annotations

from pathlib import Path

from . import graph


def generate_architecture_doc(db_path: Path, out_path: Path) -> Path:
    conn = graph.connect(db_path)
    stats = graph.summary_stats(conn)
    top = list(graph.top_symbols(conn, limit=20))

    lines = [
        "# Generated Architecture Overview",
        "",
        f"- Files indexed: **{stats['files']}**",
        f"- Symbols indexed: **{stats['symbols']}**",
        f"- Relations indexed: **{stats['relations']}**",
        "",
        "## Most referenced symbols",
        "",
    ]

    if not top:
        lines.append("No symbols indexed yet.")
    else:
        for row in top:
            lines.append(
                f"- `{row['name']}` ({row['kind']}) — inbound refs: {row['inbound_refs']}"
            )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.close()
    return out_path
