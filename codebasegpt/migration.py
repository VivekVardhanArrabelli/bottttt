from __future__ import annotations

import subprocess
from pathlib import Path


def generate_migration_guide(repo_path: Path, from_ref: str, to_ref: str) -> str:
    summary = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--stat", f"{from_ref}..{to_ref}"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()

    changed_files = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--name-status", f"{from_ref}..{to_ref}"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()

    return "\n".join(
        [
            f"# Migration Guide: {from_ref} -> {to_ref}",
            "",
            "## Diff Summary",
            summary or "No changes.",
            "",
            "## Changed Files",
            "```",
            changed_files or "No changed files.",
            "```",
            "",
            "## Suggested Upgrade Steps",
            "1. Review breaking API or schema changes in modified modules.",
            "2. Re-run indexing and inspect impacted symbols.",
            "3. Run targeted tests around changed files first, then full suite.",
        ]
    )
