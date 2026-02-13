from __future__ import annotations

import subprocess
from pathlib import Path

from . import graph


def _git_changed_files(repo_path: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--name-only", f"{base}..{head}"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def summarize_pr_impact(repo_path: Path, db_path: Path, base: str, head: str) -> str:
    changed = _git_changed_files(repo_path, base, head)
    if not changed:
        return "No file changes found between refs."

    conn = graph.connect(db_path)
    impacted = conn.execute(
        """
        SELECT DISTINCT r.dst_symbol_name as symbol
        FROM files f
        JOIN relations r ON r.file_id = f.id
        WHERE f.path IN ({})
        ORDER BY symbol
        LIMIT 200
        """.format(",".join("?" for _ in changed)),
        changed,
    ).fetchall()
    conn.close()

    lines = ["# PR Impact Summary", "", "## Changed files"]
    lines.extend([f"- `{p}`" for p in changed])
    lines.extend(["", "## Potentially impacted symbols"])

    if not impacted:
        lines.append("- No impacted symbols found in index for changed files.")
    else:
        lines.extend([f"- `{row['symbol']}`" for row in impacted])

    return "\n".join(lines)
