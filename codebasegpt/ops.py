from __future__ import annotations

import json
import re
from pathlib import Path

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

SENSITIVE_PATTERNS = {
    "security": ["breach", "exploit", "vulnerability", "token leak"],
    "legal": ["lawsuit", "legal", "gdpr", "compliance"],
    "payments": ["chargeback", "refund dispute", "stolen card"],
}


def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = CARD_RE.sub("[REDACTED_CARD]", text)
    return text


def detect_policy_flags(question: str) -> list[str]:
    q = question.lower()
    flags: list[str] = []
    for key, patterns in SENSITIVE_PATTERNS.items():
        if any(p in q for p in patterns):
            flags.append(key)
    return flags


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_codeowners(repo_path: Path) -> list[tuple[str, list[str]]]:
    candidates = [repo_path / "CODEOWNERS", repo_path / ".github" / "CODEOWNERS", repo_path / "docs" / "CODEOWNERS"]
    file = next((p for p in candidates if p.exists()), None)
    if not file:
        return []

    rules: list[tuple[str, list[str]]] = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rules.append((parts[0], parts[1:]))
    return rules


def suggest_owners(paths: list[str], codeowners_rules: list[tuple[str, list[str]]]) -> list[str]:
    owners: set[str] = set()
    for path in paths:
        for pattern, people in codeowners_rules:
            normalized = pattern.lstrip("/")
            if normalized == "*" or path.startswith(normalized.rstrip("*")):
                owners.update(people)
    return sorted(owners)
