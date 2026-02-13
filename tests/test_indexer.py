import tempfile
import unittest
from pathlib import Path

from codebasegpt.graph import callers_of, connect, impacts_of
from codebasegpt.indexer import index_repository


class IndexerTests(unittest.TestCase):
    def test_index_and_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / "app.py").write_text(
                """
import os

def helper():
    return 1

def checkout():
    return helper()
""".strip(),
                encoding="utf-8",
            )

            db = tmp_path / "graph.sqlite"
            stats = index_repository(repo, db)
            self.assertEqual(stats["files"], 1)
            self.assertGreaterEqual(stats["symbols"], 2)

            conn = connect(db)
            rows = callers_of(conn, "helper")
            self.assertTrue(any(r["caller"] == "checkout" for r in rows))

            imports = impacts_of(conn, "os")
            self.assertEqual(len(imports), 1)
            conn.close()


if __name__ == "__main__":
    unittest.main()
