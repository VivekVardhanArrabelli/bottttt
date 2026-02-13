import tempfile
import unittest
from pathlib import Path

from codebasegpt.eval import run_eval_suite
from codebasegpt.indexer import index_repository


class EvalTests(unittest.TestCase):
    def test_eval_suite_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / "auth_flow.py").write_text("def authenticate_user(token):\n    return token\n", encoding="utf-8")
            db = tmp_path / "graph.sqlite"
            index_repository(repo, db)

            dataset = Path("tests/fixtures/eval_dataset.jsonl").resolve()
            result = run_eval_suite(db, dataset)
            self.assertEqual(result["cases"], 2)
            self.assertIn("policy_precision", result)
            self.assertEqual(len(result["per_case"]), 2)


if __name__ == "__main__":
    unittest.main()
