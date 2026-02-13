#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from codebasegpt.ai import answer_question
from codebasegpt.docs import generate_architecture_doc
from codebasegpt.graph import callers_of, connect, impacts_of
from codebasegpt.indexer import index_repository
from codebasegpt.migration import generate_migration_guide
from codebasegpt.pr_review import summarize_pr_impact


def default_db(repo: Path) -> Path:
    return repo / ".codebasegpt.sqlite"


def cmd_index(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    db = Path(args.db).resolve() if args.db else default_db(repo)
    stats = index_repository(repo, db, reset=not args.incremental)
    print(f"Indexed repo: {repo}")
    print(f"DB: {db}")
    print(f"Files={stats['files']} Symbols={stats['symbols']} Relations={stats['relations']}")
    return 0


def cmd_callers(args: argparse.Namespace) -> int:
    conn = connect(Path(args.db).resolve())
    rows = callers_of(conn, args.symbol)
    for row in rows:
        print(f"{row['path']}:{row['lineno']} caller={row['caller']}")
    if not rows:
        print("No callers found.")
    conn.close()
    return 0


def cmd_impacts(args: argparse.Namespace) -> int:
    conn = connect(Path(args.db).resolve())
    rows = impacts_of(conn, args.symbol)
    for row in rows:
        print(f"{row['path']}:{row['lineno']} type={row['relation_type']} dependent={row['dependent']}")
    if not rows:
        print("No impacts found.")
    conn.close()
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    print(answer_question(Path(args.db).resolve(), args.question))
    return 0


def cmd_docs(args: argparse.Namespace) -> int:
    out = generate_architecture_doc(Path(args.db).resolve(), Path(args.out).resolve())
    print(f"Wrote: {out}")
    return 0


def cmd_pr_impact(args: argparse.Namespace) -> int:
    text = summarize_pr_impact(Path(args.repo).resolve(), Path(args.db).resolve(), args.base, args.head)
    print(text)
    return 0


def cmd_migration(args: argparse.Namespace) -> int:
    text = generate_migration_guide(Path(args.repo).resolve(), args.from_ref, args.to_ref)
    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cbg", description="CodebaseGPT CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("index", help="Index repository")
    p.add_argument("repo")
    p.add_argument("--db")
    p.add_argument("--incremental", action="store_true")
    p.set_defaults(func=cmd_index)

    q = sub.add_parser("query-callers", help="Find callers of symbol")
    q.add_argument("symbol")
    q.add_argument("--db", required=True)
    q.set_defaults(func=cmd_callers)

    q2 = sub.add_parser("query-impacts", help="Find impacts of symbol")
    q2.add_argument("symbol")
    q2.add_argument("--db", required=True)
    q2.set_defaults(func=cmd_impacts)

    ask = sub.add_parser("ask", help="Ask a natural-language question")
    ask.add_argument("question")
    ask.add_argument("--db", required=True)
    ask.set_defaults(func=cmd_ask)

    docs = sub.add_parser("generate-docs", help="Generate architecture docs")
    docs.add_argument("--db", required=True)
    docs.add_argument("--out", default="ARCHITECTURE.generated.md")
    docs.set_defaults(func=cmd_docs)

    pr = sub.add_parser("pr-impact", help="Summarize PR impact between refs")
    pr.add_argument("repo")
    pr.add_argument("--db", required=True)
    pr.add_argument("--base", required=True)
    pr.add_argument("--head", required=True)
    pr.set_defaults(func=cmd_pr_impact)

    mig = sub.add_parser("migration-guide", help="Generate migration guide between refs")
    mig.add_argument("repo")
    mig.add_argument("from_ref")
    mig.add_argument("to_ref")
    mig.set_defaults(func=cmd_migration)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
