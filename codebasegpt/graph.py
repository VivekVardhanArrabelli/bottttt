from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    language TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    lineno INTEGER,
    UNIQUE(file_id, name, kind, lineno),
    FOREIGN KEY(file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    src_symbol_id INTEGER,
    dst_symbol_name TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    lineno INTEGER,
    FOREIGN KEY(src_symbol_id) REFERENCES symbols(id),
    FOREIGN KEY(file_id) REFERENCES files(id)
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_relations_dst ON relations(dst_symbol_name);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def reset_repository(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM relations")
    conn.execute("DELETE FROM symbols")
    conn.execute("DELETE FROM files")
    conn.commit()


def upsert_file(conn: sqlite3.Connection, path: str, language: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO files(path, language) VALUES (?, ?)",
        (path, language),
    )
    row = conn.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
    assert row is not None
    return int(row["id"])


def insert_symbol(
    conn: sqlite3.Connection,
    file_id: int,
    name: str,
    kind: str,
    lineno: Optional[int],
) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO symbols(file_id, name, kind, lineno) VALUES (?, ?, ?, ?)",
        (file_id, name, kind, lineno),
    )
    row = conn.execute(
        "SELECT id FROM symbols WHERE file_id=? AND name=? AND kind=? AND lineno IS ?",
        (file_id, name, kind, lineno),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def insert_relation(
    conn: sqlite3.Connection,
    file_id: int,
    dst_symbol_name: str,
    relation_type: str,
    lineno: Optional[int] = None,
    src_symbol_id: Optional[int] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO relations(src_symbol_id, dst_symbol_name, relation_type, file_id, lineno)
        VALUES (?, ?, ?, ?, ?)
        """,
        (src_symbol_id, dst_symbol_name, relation_type, file_id, lineno),
    )


def callers_of(conn: sqlite3.Connection, symbol_name: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.path, s.name as caller, r.lineno
        FROM relations r
        LEFT JOIN symbols s ON s.id = r.src_symbol_id
        JOIN files f ON f.id = r.file_id
        WHERE r.relation_type = 'calls' AND r.dst_symbol_name = ?
        ORDER BY f.path, r.lineno
        """,
        (symbol_name,),
    ).fetchall()


def impacts_of(conn: sqlite3.Connection, symbol_name: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.path, s.name as dependent, r.relation_type, r.lineno
        FROM relations r
        LEFT JOIN symbols s ON s.id = r.src_symbol_id
        JOIN files f ON f.id = r.file_id
        WHERE r.dst_symbol_name = ?
        ORDER BY r.relation_type, f.path
        """,
        (symbol_name,),
    ).fetchall()


def summary_stats(conn: sqlite3.Connection) -> dict[str, int]:
    files = conn.execute("SELECT COUNT(*) c FROM files").fetchone()["c"]
    symbols = conn.execute("SELECT COUNT(*) c FROM symbols").fetchone()["c"]
    relations = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]
    return {"files": files, "symbols": symbols, "relations": relations}


def top_symbols(conn: sqlite3.Connection, limit: int = 20) -> Iterable[sqlite3.Row]:
    return conn.execute(
        """
        SELECT s.name, s.kind, COUNT(r.id) AS inbound_refs
        FROM symbols s
        LEFT JOIN relations r ON r.dst_symbol_name = s.name
        GROUP BY s.id
        ORDER BY inbound_refs DESC, s.name ASC
        LIMIT ?
        """,
        (limit,),
    )
