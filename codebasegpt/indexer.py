from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from . import graph


SUPPORTED_SUFFIXES = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".rs": "rust",
    ".go": "go",
}


@dataclass
class Symbol:
    name: str
    kind: str
    lineno: int | None


@dataclass
class Relation:
    dst_symbol_name: str
    relation_type: str
    lineno: int | None
    src_symbol_name: str | None = None


@dataclass
class FileIndexResult:
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


class PythonAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: list[Symbol] = []
        self.relations: list[Relation] = []
        self._stack: list[str] = []

    def _current_symbol(self) -> str | None:
        return self._stack[-1] if self._stack else None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.symbols.append(Symbol(name=node.name, kind="function", lineno=node.lineno))
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(Symbol(name=node.name, kind="class", lineno=node.lineno))
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.relations.append(
                    Relation(
                        dst_symbol_name=base.id,
                        relation_type="inherits",
                        lineno=node.lineno,
                        src_symbol_name=node.name,
                    )
                )
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.relations.append(
                Relation(
                    dst_symbol_name=alias.name,
                    relation_type="imports",
                    lineno=node.lineno,
                    src_symbol_name=self._current_symbol(),
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full = f"{module}.{alias.name}" if module else alias.name
            self.relations.append(
                Relation(
                    dst_symbol_name=full,
                    relation_type="imports",
                    lineno=node.lineno,
                    src_symbol_name=self._current_symbol(),
                )
            )

    def visit_Call(self, node: ast.Call) -> None:
        called_name = None
        if isinstance(node.func, ast.Name):
            called_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr

        if called_name:
            self.relations.append(
                Relation(
                    dst_symbol_name=called_name,
                    relation_type="calls",
                    lineno=node.lineno,
                    src_symbol_name=self._current_symbol(),
                )
            )
        self.generic_visit(node)


def iter_source_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") and part not in {".", ".."} for part in path.parts):
            continue
        if "node_modules" in path.parts or "target" in path.parts or "dist" in path.parts:
            continue
        if path.suffix in SUPPORTED_SUFFIXES:
            yield path


def analyze_file(path: Path) -> FileIndexResult:
    lang = SUPPORTED_SUFFIXES[path.suffix]
    result = FileIndexResult(language=lang)

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return result

    if lang == "python":
        try:
            tree = ast.parse(content)
            analyzer = PythonAnalyzer()
            analyzer.visit(tree)
            result.symbols.extend(analyzer.symbols)
            result.relations.extend(analyzer.relations)
        except Exception:
            # Keep indexing resilient: even unreadable files are tracked.
            pass
        return result

    # Lightweight cross-language extraction for Phase 1 parity improvements.
    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if lang in {"javascript", "typescript"}:
            m = re.match(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="function", lineno=lineno))
            m = re.match(r"(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="class", lineno=lineno))
            imp = re.search(r"from\s+[\"']([^\"']+)[\"']", stripped)
            if imp:
                result.relations.append(Relation(dst_symbol_name=imp.group(1), relation_type="imports", lineno=lineno))

        elif lang == "go":
            m = re.match(r"func\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="function", lineno=lineno))
            m = re.match(r"type\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="class", lineno=lineno))

        elif lang == "rust":
            m = re.match(r"(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="function", lineno=lineno))
            m = re.match(r"(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if m:
                result.symbols.append(Symbol(name=m.group(1), kind="class", lineno=lineno))

    return result


def index_repository(repo_path: Path, db_path: Path, reset: bool = True) -> dict[str, int]:
    conn = graph.connect(db_path)
    graph.init_db(conn)
    if reset:
        graph.reset_repository(conn)

    for file_path in iter_source_files(repo_path):
        relative = str(file_path.relative_to(repo_path))
        analysis = analyze_file(file_path)
        file_id = graph.upsert_file(conn, relative, analysis.language)

        symbol_map: dict[str, int] = {}
        for symbol in analysis.symbols:
            symbol_id = graph.insert_symbol(conn, file_id, symbol.name, symbol.kind, symbol.lineno)
            symbol_map[symbol.name] = symbol_id

        for relation in analysis.relations:
            graph.insert_relation(
                conn=conn,
                file_id=file_id,
                dst_symbol_name=relation.dst_symbol_name,
                relation_type=relation.relation_type,
                lineno=relation.lineno,
                src_symbol_id=symbol_map.get(relation.src_symbol_name or ""),
            )

    conn.commit()
    stats = graph.summary_stats(conn)
    conn.close()
    return stats
