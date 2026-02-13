import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codebasegpt.ai import answer_question
from codebasegpt.indexer import index_repository


class AITests(unittest.TestCase):
    def test_heuristic_answer_contains_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / "auth_flow.py").write_text(
                """

def authenticate_user(token):
    return token is not None
""".strip(),
                encoding="utf-8",
            )
            db = tmp_path / "graph.sqlite"
            index_repository(repo, db)

            text = answer_question(db, "Where does authentication happen?")
            self.assertIn("Relevant components", text)
            self.assertIn("authenticate_user", text)

    def test_llm_failure_falls_back_to_heuristic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / "checkout.py").write_text(
                """

def checkout():
    return True
""".strip(),
                encoding="utf-8",
            )
            db = tmp_path / "graph.sqlite"
            index_repository(repo, db)

            with mock.patch("codebasegpt.ai._llm_answer", side_effect=RuntimeError("boom")):
                text = answer_question(db, "How does checkout work?", use_llm=True)

            self.assertIn("LLM call failed", text)
            self.assertIn("Relevant components", text)


if __name__ == "__main__":
    unittest.main()
